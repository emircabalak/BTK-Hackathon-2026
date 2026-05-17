"""Decider agent — synthesize all reports into a final decision card."""

from __future__ import annotations

import logging
from collections.abc import Callable

from app.llm import Message, chat_json
from app.models import (
    CriticReport,
    FinalCard,
    NegotiationOutcome,
    Product,
    TrustBreakdown,
    VerifierReport,
)
from app.prompts.decider import DECIDER_SYSTEM

log = logging.getLogger(__name__)


def compute_trust_score(
    *,
    critic: CriticReport,
    verifier: VerifierReport,
) -> tuple[float, TrustBreakdown]:
    """Weighted aggregate of agent signals → 0..100."""
    fake_contrib = 0.30 * (1 - critic.fake_ratio) * 100  # 30 pts max
    auth_contrib = 0.30 * (verifier.overall_authenticity / 100) * 100  # 30 pts max
    sent_contrib = 0.20 * critic.real_sentiment * 100  # 20 pts max
    seller_contrib = 0.20 * (verifier.seller_score / 100) * 100  # 20 pts max

    total = fake_contrib + auth_contrib + sent_contrib + seller_contrib

    return round(total, 1), TrustBreakdown(
        fake_ratio_contribution=round(fake_contrib, 1),
        authenticity_contribution=round(auth_contrib, 1),
        sentiment_contribution=round(sent_contrib, 1),
        seller_contribution=round(seller_contrib, 1),
    )


def pick_winner(
    products: list[Product],
    critic: dict[str, CriticReport],
    verifier: dict[str, VerifierReport],
) -> tuple[Product, list[Product]]:
    """Pick winner by trust score; return (winner, ranked_others)."""
    scored: list[tuple[float, Product]] = []
    for p in products:
        c = critic.get(p.product_id)
        v = verifier.get(p.product_id)
        if c is None or v is None:
            continue
        score, _ = compute_trust_score(critic=c, verifier=v)
        scored.append((score, p))
    if not scored:
        return products[0], products[1:]
    scored.sort(key=lambda t: t[0], reverse=True)
    winner = scored[0][1]
    rest = [p for _, p in scored[1:]]
    return winner, rest


def _top_topic(critic: CriticReport, *, positive: bool) -> str:
    if not critic.topics:
        return "(veri yok)"
    if positive:
        best = max(critic.topics, key=lambda t: t.score)
        if best.score > 0:
            return best.topic.replace("_", " ")
    else:
        worst = min(critic.topics, key=lambda t: t.score)
        if worst.score < 0:
            return worst.topic.replace("_", " ")
    return "—"


def _alternatives_summary(alts: list[Product]) -> str:
    if not alts:
        return "(başka aday yok)"
    lines = []
    for p in alts[:3]:
        lines.append(f"- {p.title} ({p.price:.0f} TL, {p.rating}★)")
    return "\n".join(lines)


def _build_decider_mock(
    *,
    winner: Product,
    final_price: float,
    savings_tl: float,
    trust_score: float,
    critic: CriticReport,
    extras: list[str],
) -> Callable:
    strength = _top_topic(critic, positive=True)
    weakness = _top_topic(critic, positive=False)

    def mock(system: str, messages: list[Message]) -> dict:
        if savings_tl > 0:
            headline = f"%{(savings_tl/winner.price*100):.0f} indirimle güvenilir seçim"
        else:
            headline = "Güvenilir seçim, ama indirim alınamadı"

        parts = []
        parts.append(
            f"Bu ürünü seçtim çünkü güven skoru {trust_score:.0f}/100 ile "
            f"adaylar arasında en yüksek."
        )
        if strength and strength != "—" and strength != "(veri yok)":
            parts.append(f"Yorumlar özellikle {strength} konusunda olumlu.")
        if weakness and weakness != "—":
            parts.append(f"Tek dikkat noktası: bazı kullanıcılar {weakness} konusunda eleştiri yapmış.")
        if savings_tl > 0:
            extras_str = ""
            if extras:
                extras_str = f" + {', '.join(extras)}"
            parts.append(
                f"Pazarlık sonucu {savings_tl:.0f} TL tasarruf{extras_str} sağlandı."
            )
        return {
            "headline": headline,
            "explanation": " ".join(parts),
        }
    return mock


def run_decider(
    *,
    finalists: list[Product],
    critic_reports: dict[str, CriticReport],
    verifier_reports: dict[str, VerifierReport],
    negotiation: NegotiationOutcome | None,
) -> FinalCard:
    winner, alternatives = pick_winner(finalists, critic_reports, verifier_reports)
    c = critic_reports[winner.product_id]
    v = verifier_reports[winner.product_id]
    trust_score, breakdown = compute_trust_score(critic=c, verifier=v)

    final_price = negotiation.final_price if negotiation else winner.price
    savings_tl = negotiation.savings_tl if negotiation else 0.0
    savings_pct = negotiation.savings_pct if negotiation else 0.0
    extras = negotiation.extras if negotiation else []

    system = DECIDER_SYSTEM.format(
        winner_title=winner.title,
        list_price=f"{winner.price:.0f}",
        final_price=f"{final_price:.0f}",
        savings_tl=f"{savings_tl:.0f}",
        savings_pct=f"{savings_pct:.1f}",
        extras=", ".join(extras) or "yok",
        trust_score=f"{trust_score:.0f}",
        fake_ratio_pct=f"{c.fake_ratio*100:.0f}",
        real_sentiment_pct=f"{c.real_sentiment*100:.0f}",
        authenticity_pct=f"{v.overall_authenticity:.0f}",
        seller_score=f"{v.seller_score:.0f}",
        negotiation_summary=(negotiation.summary if negotiation else "Pazarlık yapılmadı."),
        top_strength=_top_topic(c, positive=True),
        top_weakness=_top_topic(c, positive=False),
        alternatives_summary=_alternatives_summary(alternatives),
    )

    mock_fn = _build_decider_mock(
        winner=winner,
        final_price=final_price,
        savings_tl=savings_tl,
        trust_score=trust_score,
        critic=c,
        extras=extras,
    )

    data = chat_json(
        system=system,
        messages=[Message(role="user", content="Karar açıklamasını yaz.")],
        tier="pro",
        temperature=0.4,
        mock_fallback=mock_fn,
    )

    return FinalCard(
        winner=winner,
        trust_score=trust_score,
        trust_breakdown=breakdown,
        negotiation=negotiation,
        headline=data.get("headline", "Önerim hazır"),
        explanation=data.get("explanation", ""),
        alternatives=alternatives[:3],
        buy_link=winner.url or "",
    )
