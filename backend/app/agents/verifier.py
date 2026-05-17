"""Verifier agent — text-based authenticity check (Vision deferred)."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable

from app.llm import Message, chat_json
from app.models import Product, VerifierReport
from app.prompts.verifier import VERIFIER_SYSTEM

log = logging.getLogger(__name__)


_SCAMMY_WORDS = ["LÜKS", "ULTRA", "SÜPER", "Pro Max+", "BÜYÜK", "%70 İNDİRİM", "Sınırlı Stok"]


def _has_scammy_title(title: str) -> bool:
    upper_ratio = sum(1 for c in title if c.isupper()) / max(1, len(title))
    if upper_ratio > 0.4:
        return True
    return any(w in title for w in _SCAMMY_WORDS)


def _build_verifier_mock(product: Product) -> Callable:
    def mock(system: str, messages: list[Message]) -> dict:
        flags = []
        seller = product.seller

        # Brand consistency: established brand keywords + sane title
        brand_score = 85
        if _has_scammy_title(product.title):
            brand_score -= 35
            flags.append("Başlık abartılı veya tüm büyük harfli")
        if not any(b in product.title for b in ["Sony", "JBL", "Logitech", "Cherry", "Daiwa"]) and "Muadili" not in product.title:
            brand_score -= 5

        # Spec consistency: description present + reviews not contradicting
        spec_score = 80
        if not product.description or len(product.description) < 40:
            spec_score -= 25
            flags.append("Açıklama çok kısa veya eksik")
        # Reviews that contradict
        bad_revs = [r for r in product.reviews if r.rating <= 2]
        if len(bad_revs) >= 2:
            spec_score -= 15
            flags.append("Birden fazla 2★ veya altı yorum — beklenti uyumsuzluğu")

        # Seller score
        seller_score = min(100, seller.rating * 18 + min(seller.total_sales / 1000, 10))
        if seller.total_sales < 500:
            seller_score -= 15
            flags.append("Satıcı yeni veya az satış geçmişi")
        if seller.rating < 4.5:
            seller_score -= 10
        seller_score = max(0, min(100, seller_score))

        overall = round((brand_score + spec_score + seller_score) / 3, 1)

        return {
            "brand_consistency": max(0, min(100, brand_score)),
            "spec_consistency": max(0, min(100, spec_score)),
            "seller_score": round(seller_score, 1),
            "overall_authenticity": overall,
            "flags": flags,
        }
    return mock


def _format_excerpts(product: Product) -> str:
    if not product.reviews:
        return "(Yorum yok)"
    # Top 3 most informative — pick range of ratings
    sorted_revs = sorted(product.reviews, key=lambda r: (r.rating, len(r.text)), reverse=True)
    picks = sorted_revs[:3]
    return "\n".join(f"- [{r.rating}★] {r.text}" for r in picks)


def run_verifier_one(product: Product) -> VerifierReport:
    system = VERIFIER_SYSTEM.format(
        title=product.title,
        description=product.description or "(açıklama yok)",
        price=product.price,
        category=product.category or "?",
        rating=product.rating,
        review_count=product.review_count,
        seller_name=product.seller.name,
        seller_rating=product.seller.rating,
        seller_sales=product.seller.total_sales,
        review_excerpts=_format_excerpts(product),
    )

    data = chat_json(
        system=system,
        messages=[Message(role="user", content="Otantikliği denetle.")],
        tier="fast",
        temperature=0.2,
        mock_fallback=_build_verifier_mock(product),
    )

    return VerifierReport(
        product_id=product.product_id,
        brand_consistency=float(data.get("brand_consistency", 70) or 70),
        spec_consistency=float(data.get("spec_consistency", 70) or 70),
        seller_score=float(data.get("seller_score", 70) or 70),
        overall_authenticity=float(data.get("overall_authenticity", 70) or 70),
        flags=data.get("flags", []) or [],
    )


def run_verifier(products: list[Product], *, on_progress=None) -> dict[str, VerifierReport]:
    reports: dict[str, VerifierReport] = {}
    for i, p in enumerate(products):
        if on_progress:
            on_progress(p, i, len(products))
        reports[p.product_id] = run_verifier_one(p)
    return reports
