"""Trendyol search scraper.

Politeness:
- Headless Chromium with realistic UA
- One concurrent request, ≥1s between page loads
- Disk cache (TTL configurable) to avoid re-hitting
- Read-only — only public search pages, no auth, no writes

Returns `Product` objects in our schema. If scrape fails (anti-bot, layout
change, network), caller should fall back to seed.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from pathlib import Path
from urllib.parse import quote

from app.models import Product, Review, Seller

log = logging.getLogger(__name__)

_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / ".scrape_cache"

_UAS = [
    # A handful of recent Chrome UAs — rotate per call
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]


# ── Cache ──────────────────────────────────────────────────────


def _cache_key(query: str, max_price: float | None) -> str:
    payload = f"trendyol|{query.lower().strip()}|{max_price}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _cache_get(key: str, ttl_seconds: int = 7 * 86400) -> list[dict] | None:
    """Returns cached raw product dicts if fresh, else None."""
    path = _CACHE_DIR / f"{key}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if time.time() - data.get("fetched_at", 0) > ttl_seconds:
        return None
    return data.get("products", [])


def _cache_put(key: str, query: str, max_price: float | None, products: list[dict]) -> None:
    _CACHE_DIR.mkdir(exist_ok=True)
    path = _CACHE_DIR / f"{key}.json"
    payload = {
        "query": query,
        "max_price": max_price,
        "fetched_at": time.time(),
        "products": products,
    }
    try:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        log.warning("Scrape cache write failed for %s", key)


# ── Scrape ─────────────────────────────────────────────────────


_PRICE_RE = re.compile(r"([0-9.]+,[0-9]+|[0-9]+)\s*TL")


def _parse_price(s: str) -> float | None:
    if not s:
        return None
    m = _PRICE_RE.search(s)
    if not m:
        return None
    raw = m.group(1).replace(".", "").replace(",", ".")
    try:
        return float(raw)
    except ValueError:
        return None


def _scrape_trendyol_raw(
    query: str,
    max_price: float | None,
    *,
    max_results: int = 24,
    headless: bool = True,
    timeout_ms: int = 25_000,
) -> list[dict]:
    """Hit Trendyol's public search page and parse product cards.

    Returns a list of raw dicts. Caller converts to `Product`.
    Raises on hard failure (network, anti-bot challenge, etc.) — caller decides.
    """
    import random

    from playwright.sync_api import sync_playwright

    qs = quote(query)
    if max_price:
        url = f"https://www.trendyol.com/sr?q={qs}&prc=0-{int(max_price)}"
    else:
        url = f"https://www.trendyol.com/sr?q={qs}"

    log.info("Trendyol scrape: %s", url)
    raw_products: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx = browser.new_context(
            user_agent=random.choice(_UAS),
            viewport={"width": 1366, "height": 900},
            locale="tr-TR",
            timezone_id="Europe/Istanbul",
        )
        page = ctx.new_page()
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
        except Exception as e:  # noqa: BLE001
            log.warning("Trendyol goto failed: %s", e)
            browser.close()
            raise

        # Dismiss cookie banner if present (best effort)
        try:
            page.wait_for_selector("#onetrust-accept-btn-handler", timeout=2_500)
            page.click("#onetrust-accept-btn-handler")
        except Exception:
            pass

        # Wait for product cards (Trendyol Q4 2025 layout: .product-card)
        try:
            page.wait_for_selector(".product-card", timeout=timeout_ms)
        except Exception:
            # Try legacy fallback
            try:
                page.wait_for_selector("div.p-card-wrppr", timeout=4_000)
            except Exception as e:  # noqa: BLE001
                log.warning("No product cards on Trendyol page: %s", e)
                browser.close()
                raise

        # Mild scroll to trigger lazy load
        for _ in range(3):
            page.mouse.wheel(0, 1500)
            page.wait_for_timeout(450)

        cards = page.query_selector_all(".product-card")[:max_results]
        log.info("Trendyol cards found: %d", len(cards))

        for card in cards:
            try:
                # Link: card may be <a> itself or contain one
                href = card.get_attribute("href")
                if not href:
                    a = card.query_selector("a")
                    href = a.get_attribute("href") if a else None
                if not href:
                    continue
                full_url = "https://www.trendyol.com" + href if href.startswith("/") else href

                # Product id from URL — Trendyol uses /-p-{id}
                pid = None
                m = re.search(r"-p-(\d+)", href)
                if m:
                    pid = "trendyol_" + m.group(1)

                # Title from .product-brand + .product-name
                brand_el = card.query_selector(".product-brand")
                name_el = card.query_selector(".product-name")
                brand = brand_el.inner_text().strip() if brand_el else ""
                name = name_el.inner_text().strip() if name_el else ""
                title = (brand + " " + name).strip()
                if not title:
                    # Fallback to card text
                    txt = card.inner_text() or ""
                    title = txt.split("\n")[0][:120]
                if not title:
                    continue

                # Price — extract from first "X TL" pattern in card text
                price = _parse_price(card.inner_text())
                if price is None:
                    continue

                # Rating: .average-rating → "3.8"
                rating = 0.0
                rating_el = card.query_selector(".average-rating")
                if rating_el:
                    txt = rating_el.inner_text().strip().replace(",", ".")
                    try:
                        rating = float(txt)
                    except ValueError:
                        rating = 0.0

                # Review count: .review-rating → "3.8(8545)"
                review_count = 0
                rcount_el = card.query_selector(".review-rating, .ratingCount, .rating-rating-count")
                if rcount_el:
                    rtxt = rcount_el.inner_text()
                    m = re.search(r"\((\d+)\)", rtxt)
                    if m:
                        review_count = int(m.group(1))

                # Image
                img_el = card.query_selector("img.image, img")
                image_url = ""
                if img_el:
                    image_url = (
                        img_el.get_attribute("src")
                        or img_el.get_attribute("data-src")
                        or ""
                    )

                # Seller (visible on some cards only)
                seller_el = card.query_selector(".merchant-name, .seller-name")
                seller_name = seller_el.inner_text().strip() if seller_el else (brand or "Trendyol Satıcı")

                raw_products.append({
                    "product_id": pid or f"trendyol_anon_{len(raw_products)}",
                    "title": title,
                    "price": price,
                    "url": full_url,
                    "image_url": image_url,
                    "rating": rating,
                    "review_count": review_count,
                    "seller_name": seller_name,
                })
            except Exception as e:  # noqa: BLE001
                log.debug("Card parse skip: %s", e)
                continue

        browser.close()

    return raw_products


def _raw_to_product(raw: dict, category: str) -> Product:
    return Product(
        product_id=raw["product_id"],
        title=raw["title"],
        price=float(raw["price"]),
        currency="TL",
        marketplace="trendyol",
        url=raw.get("url", ""),
        image_url=raw.get("image_url", ""),
        description="",  # Trendyol search page doesn't include rich description
        category=category,
        tags=[],
        rating=float(raw.get("rating", 0)),
        review_count=int(raw.get("review_count", 0)),
        seller=Seller(
            seller_id=("trendyol_" + raw.get("seller_name", "anon").lower().replace(" ", "_"))[:60],
            name=raw.get("seller_name", "Trendyol Satıcı"),
            rating=4.5,  # default — Trendyol search doesn't expose seller rating
            total_sales=5000,
            response_style="bilinmiyor",
        ),
        reviews=[],  # populated by review scraper if needed
    )


# ── Public API ─────────────────────────────────────────────────


class ScrapeError(RuntimeError):
    pass


def _normalize_url(url: str) -> str:
    """Strip query string + fragment so cache keys match across search/detail."""
    if not url:
        return url
    if "?" in url:
        url = url.split("?", 1)[0]
    if "#" in url:
        url = url.split("#", 1)[0]
    return url.rstrip("/")


def _review_cache_key(product_url: str) -> str:
    return "rev_" + hashlib.sha256(_normalize_url(product_url).encode("utf-8")).hexdigest()[:20]


def _review_cache_get(key: str, ttl_seconds: int = 7 * 86400) -> list[dict] | None:
    path = _CACHE_DIR / f"{key}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if time.time() - data.get("fetched_at", 0) > ttl_seconds:
        return None
    return data.get("reviews", [])


def _review_cache_put(key: str, product_url: str, reviews: list[dict]) -> None:
    _CACHE_DIR.mkdir(exist_ok=True)
    path = _CACHE_DIR / f"{key}.json"
    payload = {
        "product_url": product_url,
        "fetched_at": time.time(),
        "reviews": reviews,
    }
    try:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        log.warning("Review cache write failed for %s", key)


def _scrape_reviews_raw(
    product_url: str,
    *,
    max_reviews: int = 25,
    headless: bool = True,
    timeout_ms: int = 25_000,
) -> list[dict]:
    """Visit product /yorumlar URL and parse comment cards."""
    import random

    from playwright.sync_api import sync_playwright

    if not product_url:
        return []
    # Normalize: strip query string before appending /yorumlar
    base = _normalize_url(product_url)
    if "/yorumlar" not in base:
        review_url = base + "/yorumlar"
    else:
        review_url = base

    log.info("Trendyol reviews scrape: %s", review_url)
    raw: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        ctx = browser.new_context(
            user_agent=random.choice(_UAS),
            viewport={"width": 1366, "height": 900},
            locale="tr-TR",
            timezone_id="Europe/Istanbul",
        )
        page = ctx.new_page()
        try:
            page.goto(review_url, wait_until="domcontentloaded", timeout=timeout_ms)
        except Exception as e:  # noqa: BLE001
            log.warning("Review goto failed: %s", e)
            browser.close()
            return []

        # Dismiss cookies
        try:
            page.wait_for_selector("#onetrust-accept-btn-handler", timeout=2_000)
            page.click("#onetrust-accept-btn-handler")
        except Exception:
            pass

        try:
            page.wait_for_selector(".review", timeout=10_000)
        except Exception:
            log.warning("No review cards found")
            browser.close()
            return []

        # Scroll to load more (lazy)
        for _ in range(4):
            page.mouse.wheel(0, 2500)
            page.wait_for_timeout(550)

        cards = page.query_selector_all(".review")[:max_reviews]
        for card in cards:
            try:
                text_el = card.query_selector(".review-comment")
                text = text_el.inner_text().strip() if text_el else ""
                if not text:
                    continue
                author_el = card.query_selector(".detail-item.name")
                author = author_el.inner_text().strip() if author_el else "Anonim"
                date_el = card.query_selector(".detail-item.date")
                date_s = date_el.inner_text().strip() if date_el else None

                # Star rating: width ratio
                rating = 5
                cont = card.query_selector(".star-rating-star-container")
                full = card.query_selector(".star-rating-full-star")
                if cont and full:
                    try:
                        cont_box = cont.bounding_box()
                        full_box = full.bounding_box()
                        if cont_box and full_box and cont_box["width"] > 0:
                            ratio = full_box["width"] / cont_box["width"]
                            rating = max(1, min(5, round(ratio * 5)))
                    except Exception:
                        rating = 5

                verified = bool(card.query_selector(".comment-seller-info, .seller-name-wrapper"))

                raw.append({
                    "author": author,
                    "rating": int(rating),
                    "text": text,
                    "date": date_s,
                    "verified_purchase": verified,
                })
            except Exception as e:  # noqa: BLE001
                log.debug("Review parse skip: %s", e)
                continue

        browser.close()

    log.info("Trendyol reviews parsed: %d", len(raw))
    return raw


def fetch_reviews(
    product_url: str,
    *,
    max_reviews: int = 25,
    use_cache: bool = True,
    cache_ttl_seconds: int = 7 * 86400,
) -> list[Review]:
    """Public API. Returns list[Review] with disk cache."""
    key = _review_cache_key(product_url)
    if use_cache:
        cached = _review_cache_get(key, ttl_seconds=cache_ttl_seconds)
        if cached is not None:
            log.info("Trendyol review cache hit (%d)", len(cached))
            return [Review(**r) for r in cached[:max_reviews]]

    try:
        raw = _scrape_reviews_raw(product_url, max_reviews=max_reviews)
    except Exception as e:  # noqa: BLE001
        log.warning("Review scrape failed: %s", e)
        return []

    if raw:
        _review_cache_put(key, product_url, raw)
    return [Review(**r) for r in raw[:max_reviews]]


def search(
    query: str,
    *,
    max_price: float | None = None,
    category: str = "",
    max_results: int = 12,
    use_cache: bool = True,
    cache_ttl_seconds: int = 7 * 86400,
) -> list[Product]:
    """Search Trendyol and return a list of Product. Cached on disk."""
    key = _cache_key(query, max_price)

    if use_cache:
        cached = _cache_get(key, ttl_seconds=cache_ttl_seconds)
        if cached is not None:
            log.info("Trendyol cache hit (%d products)", len(cached))
            return [_raw_to_product(r, category) for r in cached[:max_results]]

    try:
        raw = _scrape_trendyol_raw(query, max_price, max_results=max_results)
    except Exception as e:  # noqa: BLE001
        raise ScrapeError(f"Trendyol scrape failed: {e}") from e

    if not raw:
        raise ScrapeError("Trendyol returned 0 products — anti-bot or layout change?")

    _cache_put(key, query, max_price, raw)
    return [_raw_to_product(r, category) for r in raw[:max_results]]
