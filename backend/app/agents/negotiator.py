"""Negotiator agent — runs the multi-turn pazarlık loop.

Top-level API:
- `negotiate(context, seller_persona) -> NegotiationOutcome`
  runs a full turn loop between Negotiator and Seller agents and returns the
  final transcript + outcome.
- `respond_negotiator(...)` produces a single negotiator turn.
"""

from __future__ import annotations

import logging
from typing import Any

from app.agents.seller import respond_seller
from app.llm import Message, chat_json
from app.models import (
    NegotiationContext,
    NegotiationOutcome,
    Product,
    SellerPersona,
    Turn,
)
from app.prompts.negotiator import build_negotiator_system_prompt

log = logging.getLogger(__name__)


def _target_price(ctx: NegotiationContext) -> float:
    return ctx.product.price * (1 - ctx.target_discount_pct / 100)


def _walk_away_price(ctx: NegotiationContext) -> float:
    return ctx.product.price * (1 - ctx.walk_away_discount_pct / 100)


# --- Mock fallback ---


def _build_mock_negotiator(ctx: NegotiationContext, transcript: list[Turn]):
    target = _target_price(ctx)
    walk_away = _walk_away_price(ctx)

    def mock(system: str, messages: list[Message]) -> dict:
        n_self_turns = sum(1 for t in transcript if t.speaker == "negotiator")
        last_seller = next(
            (t for t in reversed(transcript) if t.speaker == "seller"), None
        )
        last_offer = last_seller.offered_price if last_seller else None
        seller_intent = last_seller.intent if last_seller else None

        if n_self_turns == 0:
            return {
                "internal_thought": (
                    f"Açılış. Yüksek anchor: ~{ctx.target_discount_pct:.0f}% indirim iste."
                ),
                "message": (
                    f"Merhaba, ürününüzle ilgileniyorum. Bütçem biraz dar — "
                    f"%{ctx.target_discount_pct:.0f} civarı bir indirim mümkün mü?"
                ),
                "intent": "open",
                "target_price": target,
                "would_accept_price": target,
            }

        # If seller has flatly refused
        if seller_intent == "refuse":
            if last_offer is not None and last_offer <= walk_away:
                return {
                    "internal_thought": (
                        f"Satıcı reddetti ama teklif vazgeçme eşiğinin altında "
                        f"({last_offer:.0f} TL). Kabul ediyorum."
                    ),
                    "message": "Anlaştık, bu fiyatta alıyorum. Teşekkürler.",
                    "intent": "accept",
                    "target_price": None,
                    "would_accept_price": last_offer,
                }
            return {
                "internal_thought": "Satıcı katı ve teklif yeterli değil. Çekiliyorum.",
                "message": "Anlıyorum, bu fiyatta benim için uygun değil. Vazgeçtim, teşekkürler.",
                "intent": "walk_away",
                "target_price": None,
                "would_accept_price": None,
            }

        # If we have a seller offer in good range
        if last_offer is not None:
            # Hedef bölgesinde → kabul
            if last_offer <= target + 1:
                return {
                    "internal_thought": (
                        f"Mükemmel — teklif hedefte ({last_offer:.0f} ≤ {target:.0f}). Anlaştık."
                    ),
                    "message": "Harika fiyat, anlaştık. Siparişimi veriyorum, teşekkürler!",
                    "intent": "accept",
                    "target_price": None,
                    "would_accept_price": last_offer,
                }

            # Eşik ile hedef arası → biraz daha bas
            if last_offer <= walk_away:
                # 3+ tur olduysa ve ekstralar varsa, kabul
                if n_self_turns >= 2 and last_seller and last_seller.extras:
                    return {
                        "internal_thought": "Ekstralarla birlikte iyi paket, kabul.",
                        "message": "Tamam, kargo dahil bu fiyata anlaştık. Teşekkürler!",
                        "intent": "accept",
                        "target_price": None,
                        "would_accept_price": last_offer,
                    }
                # Tur 2: rakip referansı
                if n_self_turns == 1 and ctx.competitor_avg_price:
                    return {
                        "internal_thought": "Rakip fiyatla baskı yap.",
                        "message": (
                            f"Aynı ürünü başka bir pazaryerinde "
                            f"{ctx.competitor_avg_price:.0f} TL'ye gördüm. "
                            f"{target:.0f} TL civarına çekebilirsek hemen alıyorum."
                        ),
                        "intent": "counter",
                        "target_price": target,
                        "would_accept_price": walk_away,
                    }
                # Tur 3+: ekstra iste
                if n_self_turns == 2:
                    return {
                        "internal_thought": "Fiyatı çok kıramazsak ekstralarla telafi.",
                        "message": (
                            "Fiyatı çok zorlamak istemiyorum ama kargo bedava ve "
                            f"birkaç TL daha indirim olursa hemen anlaşırız. {target:.0f} TL + ücretsiz kargo?"
                        ),
                        "intent": "counter",
                        "target_price": target,
                        "would_accept_price": walk_away,
                    }

            # Eşik altı → push harder
            return {
                "internal_thought": "Hâlâ uzak. Bir tur daha esnemeye davet et.",
                "message": (
                    f"Anlıyorum ama bütçem biraz daha esnek olmamı engelliyor. "
                    f"{target:.0f} TL olabilir mi? Bu fiyatta hemen siparişi veriyorum."
                ),
                "intent": "counter",
                "target_price": target,
                "would_accept_price": walk_away,
            }

        # Fallback (no offer info yet)
        return {
            "internal_thought": "Daha somut teklif al.",
            "message": "Bu ürün için bana özel bir fiyat verebilir misiniz?",
            "intent": "counter",
            "target_price": target,
            "would_accept_price": walk_away,
        }

    return mock


# --- Public API ---


def respond_negotiator(
    *,
    context: NegotiationContext,
    transcript: list[Turn],
) -> Turn:
    """Generate the negotiator's next turn."""
    system = build_negotiator_system_prompt(
        product_title=context.product.title,
        list_price=context.product.price,
        budget=context.budget_max,
        competitor_avg=context.competitor_avg_price,
        persona=context.user_persona,
        leverage=context.leverage_points,
        target_discount_pct=context.target_discount_pct,
        walk_away_discount_pct=context.walk_away_discount_pct,
    )

    # From negotiator's POV: own past = "model", seller messages = "user".
    messages: list[Message] = []
    for t in transcript:
        if t.speaker == "negotiator":
            messages.append(Message(role="model", content=t.message))
        elif t.speaker == "seller":
            messages.append(Message(role="user", content=t.message))

    mock = _build_mock_negotiator(context, transcript)
    data = chat_json(
        system=system,
        messages=messages,
        tier="pro",
        temperature=0.5,
        mock_fallback=mock,
    )

    return Turn(
        speaker="negotiator",
        message=data.get("message", ""),
        intent=data.get("intent", "counter"),
        offered_price=data.get("target_price"),
        internal_thought=data.get("internal_thought"),
        extras=[],
    )


def negotiate(
    *,
    context: NegotiationContext,
    seller_persona: SellerPersona,
    on_turn=None,
) -> NegotiationOutcome:
    """Run a full negotiation between Negotiator and sandbox Seller.

    Parameters
    ----------
    on_turn : Callable[[Turn], None] | None
        Optional observer — called after each turn. Used by the streaming
        WebSocket layer to push events to the frontend.
    """
    product = context.product
    transcript: list[Turn] = []

    def emit(turn: Turn) -> None:
        transcript.append(turn)
        if on_turn is not None:
            on_turn(turn)

    # Seller opens
    seller_open = respond_seller(product=product, persona=seller_persona, transcript=transcript)
    emit(seller_open)

    last_seller_offer: float | None = None
    last_extras: list[str] = []
    status: str = "max_turns"

    for turn_idx in range(context.max_turns):
        # Negotiator responds
        neg_turn = respond_negotiator(context=context, transcript=transcript)
        emit(neg_turn)

        if neg_turn.intent == "accept":
            status = "agreement"
            break
        if neg_turn.intent == "walk_away":
            status = "walk_away"
            break

        # Seller responds
        seller_turn = respond_seller(
            product=product, persona=seller_persona, transcript=transcript
        )
        emit(seller_turn)

        if seller_turn.offered_price is not None:
            last_seller_offer = seller_turn.offered_price
        if seller_turn.extras:
            last_extras = seller_turn.extras

        if seller_turn.intent == "accept":
            status = "agreement"
            break
        if seller_turn.intent == "refuse" and turn_idx >= 1:
            # Give negotiator one more chance to accept or walk away
            final_neg = respond_negotiator(context=context, transcript=transcript)
            emit(final_neg)
            status = "agreement" if final_neg.intent == "accept" else "walk_away"
            break

    final_price = last_seller_offer if last_seller_offer is not None else product.price
    if status != "agreement":
        # No deal → user pays list (or doesn't buy). For reporting, report list.
        final_price = product.price
        savings_tl = 0.0
    else:
        savings_tl = product.price - final_price

    savings_pct = (savings_tl / product.price * 100) if product.price else 0.0

    summary = _build_summary(
        product=product,
        status=status,
        original=product.price,
        final=final_price,
        extras=last_extras,
    )

    return NegotiationOutcome(
        status=status,
        original_price=product.price,
        final_price=final_price,
        savings_tl=savings_tl,
        savings_pct=savings_pct,
        extras=last_extras,
        turn_count=len(transcript),
        transcript=transcript,
        summary=summary,
    )


def _build_summary(*, product: Product, status: str, original: float, final: float, extras: list[str]) -> str:
    if status != "agreement":
        return f"Anlaşma sağlanamadı. Liste fiyatı {original:.0f} TL geçerli."
    saved = original - final
    pct = saved / original * 100 if original else 0
    extras_str = f", ekstra: {', '.join(extras)}" if extras else ""
    return (
        f"{product.title}: {original:.0f} TL → {final:.0f} TL "
        f"(-{saved:.0f} TL / %{pct:.1f}){extras_str}."
    )
