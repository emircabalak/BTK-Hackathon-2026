"""Sandbox seller agent.

Each finalist product gets its own seller agent calibrated from the product's
public data (price, category margin estimate, reviewer-inferred personality).

The agent exposes:
- `build_persona(product) -> SellerPersona`
- `respond(persona, product, transcript) -> Turn`

In mock mode, a deterministic concession schedule is used so we can validate
the negotiation flow without API access.
"""

from __future__ import annotations

import logging
from typing import Any

from app.llm import Message, chat_json
from app.models import Product, SellerPersona, Turn
from app.prompts.seller import build_seller_system_prompt

log = logging.getLogger(__name__)


# Concession schedules: per-turn cumulative discount (%) for each personality.
# Index = number of negotiator turns seen so far (1-based after first reply).
_CONCESSION_SCHEDULES: dict[str, list[float]] = {
    "comert": [0.0, 6.0, 12.0, 17.0, 19.0, 20.0],
    "normal": [0.0, 4.0, 8.0, 11.0, 13.0, 14.0],
    "siki":   [0.0, 2.0, 4.0, 5.0, 6.0, 6.0],
}

_PERSONALITY_MAX: dict[str, float] = {
    "comert": 20.0,
    "normal": 14.0,
    "siki": 6.0,
}


def build_persona(product: Product) -> SellerPersona:
    """Heuristic persona builder.

    Real-mode could call Gemini to infer personality from reviewer-reply
    patterns; for now we use simple signals so behavior is reproducible.
    """
    seller = product.seller

    # Generous = high rating + low volume (small seller hungry for customers)
    # Tough = high rating + high volume (established, doesn't need you)
    # Normal = everyone else
    if seller.rating >= 4.6 and seller.total_sales < 5000:
        # High rating + small seller → hungry for sales, generous
        personality = "comert"
    elif seller.total_sales > 50000:
        # Established big seller → doesn't need you, tougher
        personality = "siki"
    else:
        personality = "normal"

    return SellerPersona(
        personality=personality,
        max_discount_pct=_PERSONALITY_MAX[personality],
        cost_basis_pct=0.72,
        style_note=seller.response_style,
    )


def _floor_price(product: Product, persona: SellerPersona) -> float:
    return product.price * (1 - persona.max_discount_pct / 100)


def _cost_basis(product: Product, persona: SellerPersona) -> float:
    return product.price * persona.cost_basis_pct


# --- Mock fallback ---


def _build_mock_seller(product: Product, persona: SellerPersona):
    schedule = _CONCESSION_SCHEDULES[persona.personality]
    floor = _floor_price(product, persona)

    state: dict[str, Any] = {
        "current_offer": product.price,
        "extras_given": [],
        "agreed": False,
    }

    def mock(system: str, messages: list[Message]) -> dict:
        negotiator_msgs = [m for m in messages if m.role == "user"]
        n = len(negotiator_msgs)

        if n == 0:
            return {
                "internal_thought": "İlk temas. Selam ver, sıcak başla.",
                "message": "Merhaba, ürünümüzle ilgilendiğiniz için teşekkürler. Nasıl yardımcı olabilirim?",
                "intent": "open",
                "offered_price": None,
                "extras": [],
            }

        last = negotiator_msgs[-1].content.lower()

        # Did the buyer accept?
        accept_markers = ["anlaştık", "anlasti", "tamam alıyorum", "tamam aldim", "sipariş veriyorum", "siparis veriyorum", "anlaştık olur", "ok kabul"]
        if any(marker in last for marker in accept_markers):
            return {
                "internal_thought": "Müşteri anlaşmayı kapatıyor. Olumlu cevap.",
                "message": f"Harika! Siparişiniz {state['current_offer']:.0f} TL'den hazırlanıyor. Hayırlı olsun!",
                "intent": "accept",
                "offered_price": state["current_offer"],
                "extras": list(state["extras_given"]),
            }

        # Walk-away signal from buyer
        if "vazgeçtim" in last or "geri çekiliyorum" in last:
            return {
                "internal_thought": "Müşteri çekiliyor.",
                "message": "Anlıyorum, başka bir konuda yardıma ihtiyacınız olursa buradayız.",
                "intent": "refuse",
                "offered_price": None,
                "extras": [],
            }

        # Schedule-based concession
        idx = min(n, len(schedule) - 1)
        target_discount = schedule[idx]
        new_offer = max(product.price * (1 - target_discount / 100), floor)

        # Add extras after round 3 if we can't move price much
        extras = []
        if n >= 3 and "ücretsiz kargo" not in state["extras_given"]:
            extras = ["ücretsiz kargo"]
            state["extras_given"].extend(extras)

        # Refuse if hit floor and buyer keeps pushing
        if new_offer <= floor + 1 and n > 3 and not extras:
            return {
                "internal_thought": "Tabana ulaştık, daha indiremiyoruz.",
                "message": f"Maalesef {new_offer:.0f} TL son fiyatımız. Bunun altına inemiyoruz, ürün maliyetimizi karşılayamaz.",
                "intent": "refuse",
                "offered_price": new_offer,
                "extras": [],
            }

        state["current_offer"] = new_offer

        # Compose a natural-feeling Turkish message
        if idx == 1:
            msg = f"Sizin için özel olarak {new_offer:.0f} TL'ye verebilirim. Ne dersiniz?"
        elif idx <= 2:
            msg = f"Tamam, biraz daha esneyebiliriz — {new_offer:.0f} TL olur mu?"
        elif extras:
            msg = f"Fiyatı daha fazla aşağı çekemem ama size {', '.join(extras)} ekleyebilirim. {new_offer:.0f} TL + {extras[0]} olur."
        else:
            msg = f"Son teklifim {new_offer:.0f} TL. Bu fiyatta net anlaşırız."

        return {
            "internal_thought": f"Tur {n}, kademe {idx}, indirim {target_discount}%.",
            "message": msg,
            "intent": "counter",
            "offered_price": new_offer,
            "extras": extras,
        }

    return mock


# --- Public API ---


_OPEN_GREETING = (
    "Merhaba, ürünümüzle ilgilendiğiniz için teşekkürler. Nasıl yardımcı olabilirim?"
)


def respond_seller(
    *,
    product: Product,
    persona: SellerPersona,
    transcript: list[Turn],
) -> Turn:
    """Generate the seller's next turn."""
    # No prior conversation → return a fixed greeting. Saves an LLM call and
    # avoids Gemini's "contents required" error when messages are empty.
    has_buyer_msg = any(t.speaker == "negotiator" for t in transcript)
    if not has_buyer_msg:
        return Turn(
            speaker="seller",
            message=_OPEN_GREETING,
            intent="open",
            offered_price=None,
            internal_thought="İlk temas. Selam ver, sıcak başla.",
            extras=[],
        )

    system = build_seller_system_prompt(
        product_title=product.title,
        list_price=product.price,
        cost_basis=_cost_basis(product, persona),
        floor_price=_floor_price(product, persona),
        max_discount_pct=persona.max_discount_pct,
        personality=persona.personality,
    )

    # Convert transcript to chat messages from the seller's POV:
    # negotiator messages = "user", own past messages = "model".
    messages: list[Message] = []
    for t in transcript:
        if t.speaker == "negotiator":
            messages.append(Message(role="user", content=t.message))
        elif t.speaker == "seller":
            messages.append(Message(role="model", content=t.message))

    mock = _build_mock_seller(product, persona)
    data = chat_json(
        system=system,
        messages=messages,
        tier="fast",
        temperature=0.6,
        mock_fallback=mock,
    )

    return Turn(
        speaker="seller",
        message=data.get("message", ""),
        intent=data.get("intent", "counter"),
        offered_price=data.get("offered_price"),
        internal_thought=data.get("internal_thought"),
        extras=data.get("extras", []) or [],
    )
