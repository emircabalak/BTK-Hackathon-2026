"""Scout agent — parse query, filter seed candidates, rank top-N.

Real-mode pipeline:
1. Parse natural-language query into a structured ParsedQuery (Gemini)
2. Filter seed products by category + budget
3. If more than `max_candidates`, ask Gemini to rank by fit
4. Return top-N as candidates

Mock-mode fallback: regex/keyword heuristics produce a sensible parse + rank.
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable

from app.llm import Message, chat_json
from app.models import ParsedQuery, Product, ScoutOutput
from app.prompts.scout import QUERY_PARSE_SYSTEM, RANK_SYSTEM
from seed.products import ALL_PRODUCTS, KNOWN_CATEGORIES, products_in_category

log = logging.getLogger(__name__)


# --- Mock parse: simple keyword heuristics ---

_CATEGORY_KEYWORDS = {
    "kulaklik": ["kulaklık", "kulaklik", "headphone", "anc", "bluetooth kulak"],
    "olta": ["olta", "balık", "balikci", "balıkçı", "balıkçılık"],
    "klavye": ["klavye", "keyboard", "mekanik klavye"],
    "anne_hediye": [
        "anne",
        "hediye",
        "doğum günü",
        "dogum gunu",
        "hediyelik",
        "kalp kolye",
    ],
}


def _mock_parse_query(query: str) -> ParsedQuery:
    q = query.lower()
    category = ""
    for cat, kws in _CATEGORY_KEYWORDS.items():
        if any(kw in q for kw in kws):
            category = cat
            break

    # Budget: look for "<n> TL" or "<n> tl altı"
    budget_max = None
    m = re.search(r"(\d{2,5})\s*(?:tl|₺|lira)", q)
    if m:
        budget_max = float(m.group(1))

    must_have = []
    for kw in ["kaliteli", "premium", "mekanik", "bluetooth", "anc", "deri", "gümüş"]:
        if kw in q:
            must_have.append(kw)

    persona = ""
    if "baba" in q or "babam" in q:
        persona = "baba (hediye)"
    elif "anne" in q or "annem" in q:
        persona = "anne (hediye)"
    elif "oyuncu" in q or "gaming" in q:
        persona = "oyuncu"

    return ParsedQuery(
        category=category,
        budget_max=budget_max,
        must_have=must_have,
        nice_to_have=[],
        persona=persona,
    )


def _build_parse_mock(query: str) -> Callable:
    def mock(system: str, messages: list[Message]) -> dict:
        parsed = _mock_parse_query(query)
        return parsed.model_dump()
    return mock


def _build_rank_mock(candidates: list[Product], parsed: ParsedQuery) -> Callable:
    def mock(system: str, messages: list[Message]) -> dict:
        # Simple scoring: rating + (1 - review_suspicion) + budget_fit
        scores: dict[str, float] = {}
        for p in candidates:
            score = p.rating * 12  # 0..60 range
            if parsed.budget_max and p.price <= parsed.budget_max:
                score += 20
            # Penalize suspicious products
            if p.rating >= 4.85 and p.review_count < 100:
                score -= 25
            if any(w in p.title for w in ["LÜX", "LÜKS", "ULTRA", "PRO MAX+", "SÜPER"]):
                score -= 15
            scores[p.product_id] = max(0, min(100, score))

        ranked_ids = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)
        return {
            "ranked_ids": ranked_ids,
            "scores": scores,
            "reasoning": (
                f"Bütçe uyumu ve yorum güvenilirliği esas alındı. "
                f"Şüpheli başlık/yorumlu adaylar düşürüldü."
            ),
        }
    return mock


def _filter_seed(parsed: ParsedQuery) -> list[Product]:
    if not parsed.category:
        # No category match → cross-category fallback by budget
        pool = list(ALL_PRODUCTS)
    else:
        pool = products_in_category(parsed.category)
    if parsed.budget_max:
        # Allow 10% over-budget tolerance — Gemini can decide
        ceiling = parsed.budget_max * 1.1
        pool = [p for p in pool if p.price <= ceiling]
    return pool


def _summarize_candidate(p: Product) -> dict:
    return {
        "id": p.product_id,
        "title": p.title,
        "price": p.price,
        "rating": p.rating,
        "review_count": p.review_count,
        "tags": p.tags,
        "seller": {
            "name": p.seller.name,
            "rating": p.seller.rating,
            "sales": p.seller.total_sales,
        },
    }


def _live_search(parsed: ParsedQuery, max_candidates: int, log_lines: list[str]) -> list[Product]:
    """Try Trendyol live scrape. On failure, returns []. Top N finalists also get reviews scraped."""
    from concurrent.futures import ThreadPoolExecutor

    from app.scrapers import trendyol

    # Build a clean search string — dedupe terms case-insensitively
    cat_term = {
        "kulaklik": "bluetooth kulaklık",
        "olta": "olta seti",
        "klavye": "mekanik klavye",
        "anne_hediye": "anne hediye",
    }.get(parsed.category, parsed.category or "")
    seen: set[str] = set()
    search_tokens: list[str] = []
    for raw in [cat_term, *parsed.must_have[:3]]:
        if not raw:
            continue
        for tok in raw.lower().split():
            if tok and tok not in seen:
                seen.add(tok)
                search_tokens.append(tok)
    search_q = " ".join(search_tokens) if search_tokens else "ürün"

    log_lines.append(f"Trendyol canlı arama: '{search_q}' (bütçe {parsed.budget_max})")
    try:
        products = trendyol.search(
            search_q,
            max_price=parsed.budget_max,
            category=parsed.category or "",
            max_results=max_candidates,
            use_cache=True,
        )
        log_lines.append(f"Trendyol'dan {len(products)} ürün geldi.")
    except trendyol.ScrapeError as e:
        log_lines.append(f"⚠ Trendyol scrape başarısız: {e}. Seed'e dönülüyor.")
        return []
    except Exception as e:  # noqa: BLE001
        log_lines.append(f"⚠ Beklenmeyen scrape hatası: {e}. Seed'e dönülüyor.")
        return []

    if not products:
        return []

    # Sort by review_count (proxy for popularity) and fetch reviews for top N
    review_top_n = min(len(products), 4)
    by_popularity = sorted(products, key=lambda p: (p.review_count, p.rating), reverse=True)
    top_for_reviews = by_popularity[:review_top_n]

    # Sequential — Playwright sync_api conflicts with ThreadPoolExecutor.
    # Cache makes repeat calls instant, so first-time pain only.
    log_lines.append(f"En popüler {review_top_n} ürün için yorumlar çekiliyor...")
    review_map: dict[str, list] = {}
    for p in top_for_reviews:
        try:
            reviews = trendyol.fetch_reviews(p.url, max_reviews=15, use_cache=True)
            review_map[p.product_id] = reviews
        except Exception as e:  # noqa: BLE001
            log_lines.append(f"⚠ '{p.title[:30]}' yorumları alınamadı: {e}")
            review_map[p.product_id] = []

    total_reviews = sum(len(rs) for rs in review_map.values())
    log_lines.append(f"Yorumlar geldi: toplam {total_reviews} yorum {review_top_n} üründen.")

    # Inject reviews into matching products
    for p in products:
        if p.product_id in review_map:
            p.reviews = review_map[p.product_id]

    return products


def run_scout(
    query: str,
    *,
    max_candidates: int = 8,
    source: str = "seed",
) -> ScoutOutput:
    """Scout pipeline.

    source:
      - "seed": always use bundled seed/products.py
      - "live": try Trendyol scrape; fall back to seed on failure
    """
    log_lines: list[str] = []

    # Step 1: parse
    parse_data = chat_json(
        system=QUERY_PARSE_SYSTEM.format(known_categories=", ".join(KNOWN_CATEGORIES)),
        messages=[Message(role="user", content=query)],
        tier="fast",
        temperature=0.2,
        mock_fallback=_build_parse_mock(query),
    )
    parsed = ParsedQuery(
        category=parse_data.get("category", "") or "",
        budget_max=parse_data.get("budget_max"),
        must_have=parse_data.get("must_have", []) or [],
        nice_to_have=parse_data.get("nice_to_have", []) or [],
        persona=parse_data.get("persona", "") or "",
    )
    log_lines.append(
        f"Sorgu parse edildi: kategori={parsed.category!r}, "
        f"bütçe={parsed.budget_max}, persona={parsed.persona!r}"
    )

    # Step 2: gather candidates from chosen source
    pool: list[Product] = []
    if source == "live":
        pool = _live_search(parsed, max_candidates, log_lines)
        if not pool:
            log_lines.append("Seed havuzuna geçiliyor (canlı veri yok).")
            pool = _filter_seed(parsed)
            if pool:
                log_lines.append(f"Seed havuzundan {len(pool)} aday seçildi.")
    else:
        pool = _filter_seed(parsed)
        log_lines.append(f"Seed havuzundan {len(pool)} aday seçildi (kategori + bütçe).")

    if not pool:
        return ScoutOutput(parsed=parsed, candidates=[], log=log_lines + ["Boş havuz."])

    if len(pool) <= max_candidates:
        log_lines.append(f"{len(pool)} aday var, hepsi finalist.")
        # Sort by rating for stable display order
        pool_sorted = sorted(pool, key=lambda p: p.rating, reverse=True)
        return ScoutOutput(parsed=parsed, candidates=pool_sorted, log=log_lines)

    # Step 3: rank
    rank_data = chat_json(
        system=RANK_SYSTEM.format(
            category=parsed.category,
            budget=parsed.budget_max or "belirtilmedi",
            must_have=", ".join(parsed.must_have) or "yok",
            nice_to_have=", ".join(parsed.nice_to_have) or "yok",
            persona=parsed.persona or "genel",
            candidates_json=json.dumps(
                [_summarize_candidate(p) for p in pool], ensure_ascii=False, indent=2
            ),
        ),
        messages=[Message(role="user", content="Sırala.")],
        tier="fast",
        temperature=0.3,
        mock_fallback=_build_rank_mock(pool, parsed),
    )

    ranked_ids = rank_data.get("ranked_ids", [])
    scores = rank_data.get("scores", {})
    log_lines.append(f"Ranker sıraladı: {rank_data.get('reasoning', '')[:100]}")

    by_id = {p.product_id: p for p in pool}
    ranked: list[Product] = []
    for pid in ranked_ids:
        if pid in by_id and pid not in {p.product_id for p in ranked}:
            ranked.append(by_id[pid])
    # Append any missed (rank robustness)
    for p in pool:
        if p.product_id not in {x.product_id for x in ranked}:
            ranked.append(p)

    finalists = ranked[:max_candidates]
    log_lines.append(f"İlk {len(finalists)} finalist seçildi.")

    # Store scores for downstream usage
    for p in finalists:
        if p.product_id in scores:
            p.metadata["scout_score"] = scores[p.product_id]

    return ScoutOutput(parsed=parsed, candidates=finalists, log=log_lines)
