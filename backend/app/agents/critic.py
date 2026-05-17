"""Critic agent — per-product review analysis with fake detection."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable

from app.llm import Message, chat_json
from app.models import CriticReport, Product, TopicSentiment
from app.prompts.critic import CRITIC_SYSTEM

log = logging.getLogger(__name__)


# --- Mock heuristic ---

_GENERIC_PHRASES = [
    "harika ürün",
    "çok beğendim",
    "çok memnun",
    "tavsiye ederim",
]


def _looks_suspicious(text: str, rating: int, verified: bool) -> bool:
    t = text.lower().strip()
    if not verified and rating == 5 and len(t) < 80:
        return True
    if any(p in t for p in _GENERIC_PHRASES) and len(t) < 60:
        return True
    return False


def _suspicious_username(name: str) -> bool:
    if re.match(r"^(User|Kullanıcı|Müşteri|Anonim|Buyer|Test)[_ ]?\w*$", name, re.IGNORECASE):
        return True
    return False


def _build_critic_mock(product: Product) -> Callable:
    def mock(system: str, messages: list[Message]) -> dict:
        revs = product.reviews
        if not revs:
            return CriticReport(
                product_id=product.product_id,
                fake_ratio=0.0,
                real_sentiment=0.5,
                confidence=0.2,
                representative_quote="(yorum yok)",
            ).model_dump()

        sus_count = 0
        for r in revs:
            if _looks_suspicious(r.text, r.rating, r.verified_purchase):
                sus_count += 1
            elif _suspicious_username(r.author):
                sus_count += 1
        fake_ratio = sus_count / len(revs)

        # Sentiment from rating of non-suspicious reviews
        real_revs = [
            r for r in revs
            if not _looks_suspicious(r.text, r.rating, r.verified_purchase)
            and not _suspicious_username(r.author)
        ]
        if real_revs:
            avg = sum(r.rating for r in real_revs) / len(real_revs)
            sentiment = max(0.0, min(1.0, (avg - 1) / 4))  # 1→0, 5→1
        else:
            sentiment = 0.4

        # Synthetic topics
        topics = []
        if any("kargo" in r.text.lower() for r in revs):
            negs = [r for r in revs if "kargo" in r.text.lower() and r.rating <= 3]
            score = -0.4 if negs else 0.5
            topics.append({"topic": "kargo", "score": score, "sample": ""})
        if any("ses" in r.text.lower() for r in revs):
            topics.append({"topic": "ses_kalitesi", "score": 0.6, "sample": ""})
        if any("kalite" in r.text.lower() for r in revs):
            topics.append({"topic": "kalite", "score": 0.5, "sample": ""})
        topics.append({"topic": "fiyat_performans", "score": 0.5, "sample": ""})

        red_flags = []
        if fake_ratio > 0.3:
            red_flags.append(f"Şüpheli yorum oranı yüksek (%{fake_ratio*100:.0f})")
        if product.rating >= 4.85 and product.review_count < 100:
            red_flags.append("Çok yüksek rating ama az yorum — şüphe uyandırıcı")
        if any(w in product.title for w in ["LÜKS", "ULTRA", "SÜPER", "Pro Max+"]):
            red_flags.append("Başlık abartılı / spam tarzı")

        quote = next(
            (r.text for r in real_revs if r.rating in (4, 5)),
            real_revs[0].text if real_revs else "(yorum yok)",
        )

        return {
            "fake_ratio": round(fake_ratio, 2),
            "real_sentiment": round(sentiment, 2),
            "topics": topics,
            "red_flags": red_flags,
            "representative_quote": quote,
            "confidence": 0.7,
        }
    return mock


def _format_reviews(product: Product) -> str:
    if not product.reviews:
        return "(Yorum yok)"
    lines = []
    for i, r in enumerate(product.reviews, 1):
        verified = "✓" if r.verified_purchase else "✗"
        lines.append(f"{i}. [{r.rating}★ {verified} {r.author}] {r.text}")
    return "\n".join(lines)


def run_critic_one(product: Product) -> CriticReport:
    system = CRITIC_SYSTEM.format(
        product_title=product.title,
        product_description=product.description or "(açıklama yok)",
        price=product.price,
        rating=product.rating,
        review_count=product.review_count,
        seller_name=product.seller.name,
        seller_rating=product.seller.rating,
        seller_sales=product.seller.total_sales,
        reviews_text=_format_reviews(product),
    )

    data = chat_json(
        system=system,
        messages=[Message(role="user", content="Yorumları analiz et.")],
        tier="fast",
        temperature=0.3,
        mock_fallback=_build_critic_mock(product),
    )

    topics = []
    for t in data.get("topics", []) or []:
        try:
            topics.append(
                TopicSentiment(
                    topic=t.get("topic", "konu"),
                    score=float(t.get("score", 0.0)),
                    sample=t.get("sample", ""),
                )
            )
        except (TypeError, ValueError):
            continue

    return CriticReport(
        product_id=product.product_id,
        fake_ratio=float(data.get("fake_ratio", 0.0) or 0.0),
        real_sentiment=float(data.get("real_sentiment", 0.5) or 0.5),
        topics=topics,
        red_flags=data.get("red_flags", []) or [],
        representative_quote=data.get("representative_quote", "") or "",
        confidence=float(data.get("confidence", 0.5) or 0.5),
    )


def run_critic(products: list[Product], *, on_progress=None) -> dict[str, CriticReport]:
    """Run Critic for every product. Returns a dict keyed by product_id."""
    reports: dict[str, CriticReport] = {}
    for i, p in enumerate(products):
        if on_progress:
            on_progress(p, i, len(products))
        report = run_critic_one(p)
        reports[p.product_id] = report
    return reports
