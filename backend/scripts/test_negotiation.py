"""CLI test runner — runs a full negotiation against the sandbox seller.

Usage:
    python -m scripts.test_negotiation                  # default: olta
    python -m scripts.test_negotiation kulaklik
    python -m scripts.test_negotiation klavye --budget 700
    python -m scripts.test_negotiation anne_hediye --competitor 450

Works in mock mode out of the box (no API key needed). Set MOCK_MODE=false
in `.env` to run against real Gemini once you've got a key.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Force UTF-8 on stdout/stderr — Windows default (cp1254) chokes on Turkish
# characters and ANSI box-drawing glyphs used by the runner.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass

# Ensure backend root is on sys.path when run as script
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.agents.negotiator import negotiate  # noqa: E402
from app.agents.seller import build_persona  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.models import NegotiationContext, Turn  # noqa: E402
from seed.products import ALL_SEED_PRODUCTS, get_product  # noqa: E402


def _emoji(speaker: str) -> str:
    return {"negotiator": "🤝", "seller": "🏪", "system": "⚙"}.get(speaker, "•")


def _color(speaker: str) -> str:
    # ANSI colors — gracefully ignored on terminals that don't support them
    return {
        "negotiator": "\033[96m",  # cyan
        "seller": "\033[93m",  # yellow
    }.get(speaker, "\033[0m")


RESET = "\033[0m"
DIM = "\033[2m"
BOLD = "\033[1m"


def print_turn(turn: Turn) -> None:
    color = _color(turn.speaker)
    emoji = _emoji(turn.speaker)
    name = turn.speaker.upper().ljust(10)
    print(f"\n{color}{BOLD}{emoji} {name}{RESET}  {color}{turn.message}{RESET}")
    if turn.internal_thought:
        print(f"  {DIM}└─ düşünce: {turn.internal_thought}{RESET}")
    if turn.offered_price is not None:
        print(f"  {DIM}└─ teklif: {turn.offered_price:.0f} TL{RESET}")
    if turn.extras:
        print(f"  {DIM}└─ ekstralar: {', '.join(turn.extras)}{RESET}")
    print(f"  {DIM}└─ intent: {turn.intent}{RESET}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AgentMarket negotiation test runner")
    parser.add_argument(
        "product",
        nargs="?",
        default="olta",
        choices=list(ALL_SEED_PRODUCTS.keys()),
        help="Hangi seed ürünü için pazarlık yapılsın",
    )
    parser.add_argument("--budget", type=float, default=None, help="Kullanıcı bütçesi")
    parser.add_argument(
        "--competitor",
        type=float,
        default=None,
        help="Rakip pazaryerindeki ortalama fiyat (kaldıraç)",
    )
    parser.add_argument(
        "--persona", default=None, help="Kullanıcı profili (örn: 'oyuncu, üniversiteli')"
    )
    parser.add_argument(
        "--target-discount", type=float, default=15.0, help="Hedef indirim yüzdesi"
    )
    parser.add_argument(
        "--walk-away-discount",
        type=float,
        default=5.0,
        help="Vazgeçme eşiği (bu altındaki indirimde alma)",
    )
    parser.add_argument("--max-turns", type=int, default=6, help="Max pazarlık turu")
    args = parser.parse_args(argv)

    settings = get_settings()
    mode = "MOCK" if settings.mock_mode else "LIVE (Gemini)"
    print(f"\n{BOLD}━━━ AgentMarket Negotiation Test ━━━{RESET}")
    print(f"{DIM}Mod: {mode}{RESET}\n")

    product = get_product(args.product)
    persona = build_persona(product)

    leverage_points = []
    weak_topics = [r for r in product.reviews if r.rating <= 3]
    if weak_topics:
        leverage_points.append(
            f"yorumlarda zayıflık: {weak_topics[0].text[:60]}"
        )
    if args.competitor:
        leverage_points.append(f"rakip fiyat ortalaması {args.competitor:.0f} TL")

    context = NegotiationContext(
        product=product,
        budget_max=args.budget,
        competitor_avg_price=args.competitor,
        user_persona=args.persona,
        leverage_points=leverage_points,
        target_discount_pct=args.target_discount,
        walk_away_discount_pct=args.walk_away_discount,
        max_turns=args.max_turns,
    )

    print(f"{BOLD}Ürün:{RESET}        {product.title}")
    print(f"{BOLD}Liste fiyatı:{RESET} {product.price:.0f} TL")
    print(
        f"{BOLD}Satıcı:{RESET}       {product.seller.name} "
        f"(puan {product.seller.rating}, {product.seller.total_sales} satış)"
    )
    print(
        f"{BOLD}Satıcı kişiliği:{RESET} {persona.personality} "
        f"(max indirim %{persona.max_discount_pct:.0f})"
    )
    target = product.price * (1 - args.target_discount / 100)
    walk = product.price * (1 - args.walk_away_discount / 100)
    print(
        f"{BOLD}Hedef:{RESET}       {target:.0f} TL (-%{args.target_discount:.0f})  "
        f"{BOLD}Vazgeçme:{RESET} {walk:.0f} TL üstü kabul etme"
    )

    print(f"\n{DIM}─── Pazarlık başlıyor ───{RESET}")

    outcome = negotiate(
        context=context,
        seller_persona=persona,
        on_turn=print_turn,
    )

    print(f"\n{DIM}─── Pazarlık bitti ───{RESET}\n")
    print(f"{BOLD}Durum:{RESET}         {outcome.status}")
    print(f"{BOLD}Tur sayısı:{RESET}    {outcome.turn_count}")
    print(f"{BOLD}Liste fiyatı:{RESET}  {outcome.original_price:.0f} TL")
    print(f"{BOLD}Final fiyat:{RESET}   {outcome.final_price:.0f} TL")
    print(
        f"{BOLD}Tasarruf:{RESET}      "
        f"{outcome.savings_tl:.0f} TL (%{outcome.savings_pct:.1f})"
    )
    if outcome.extras:
        print(f"{BOLD}Ekstralar:{RESET}     {', '.join(outcome.extras)}")
    print(f"\n{BOLD}Özet:{RESET} {outcome.summary}\n")

    return 0 if outcome.status == "agreement" else 1


if __name__ == "__main__":
    raise SystemExit(main())
