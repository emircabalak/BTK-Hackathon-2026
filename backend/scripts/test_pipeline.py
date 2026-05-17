"""End-to-end pipeline test runner.

Usage:
    python -m scripts.test_pipeline "balık seti 2000 TL altı babam için"
    python -m scripts.test_pipeline "anne hediyesi 500 TL altı"
    python -m scripts.test_pipeline "oyuncu kulaklığı 400 TL altı" --competitor 380

Streams agent events to stdout (like the WebSocket layer would).
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.agents.orchestrator import run_pipeline  # noqa: E402
from app.config import get_settings  # noqa: E402

# ANSI styling
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

COLORS = {
    "orchestrator": "\033[95m",  # magenta
    "scout": "\033[94m",  # blue
    "critic": "\033[93m",  # yellow
    "verifier": "\033[96m",  # cyan
    "negotiator": "\033[92m",  # green
    "decider": "\033[35m",  # purple
}

EMOJI = {
    "orchestrator": "🎼",
    "scout": "🛒",
    "critic": "🔍",
    "verifier": "🛡",
    "negotiator": "🤝",
    "decider": "⭐",
}


def _stream_print(event: dict) -> None:
    agent = event.get("agent", "?")
    color = COLORS.get(agent, "")
    emoji = EMOJI.get(agent, "•")
    name = agent.upper().ljust(13)
    ev = event.get("event", "")
    msg = event.get("message", "")
    extras = ""
    if event.get("speaker"):
        extras = f"  [{event['speaker']}] {event.get('message', '')}"
        msg = ""
    if msg:
        print(f"{color}{emoji} {name}{RESET} {DIM}{ev:9}{RESET} {msg}")
    elif extras:
        print(f"{color}{emoji} {name}{RESET} {DIM}{ev:9}{RESET}{extras}")
    else:
        # System events without message — print compact summary
        copy = {k: v for k, v in event.items() if k not in {"ts", "agent", "event"}}
        print(f"{color}{emoji} {name}{RESET} {DIM}{ev:9}{RESET} {json.dumps(copy, ensure_ascii=False)[:140]}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AgentMarket pipeline test runner")
    parser.add_argument("query", help="Doğal dilde alışveriş sorgusu")
    parser.add_argument("--budget", type=float, default=None)
    parser.add_argument("--competitor", type=float, default=None)
    parser.add_argument("--target-discount", type=float, default=15.0)
    parser.add_argument("--walk-away-discount", type=float, default=5.0)
    parser.add_argument("--max-turns", type=int, default=6)
    parser.add_argument(
        "--source",
        choices=["seed", "live"],
        default="seed",
        help="seed: yerleşik test ürünleri | live: Trendyol canlı scrape (fallback: seed)",
    )
    parser.add_argument("--json", action="store_true", help="Sadece JSON çıktı")
    args = parser.parse_args(argv)

    settings = get_settings()
    mode = "MOCK" if settings.mock_mode else "LIVE (Gemini)"

    if not args.json:
        print(f"\n{BOLD}━━━ AgentMarket Pipeline Test ━━━{RESET}")
        print(f"{DIM}Mod: {mode}{RESET}")
        print(f"{BOLD}Sorgu:{RESET} {args.query}\n")
        print(f"{DIM}─── Pipeline başlıyor ───{RESET}\n")

    started = time.time()
    result = run_pipeline(
        args.query,
        budget_max=args.budget,
        competitor_avg_price=args.competitor,
        target_discount_pct=args.target_discount,
        walk_away_discount_pct=args.walk_away_discount,
        max_negotiation_turns=args.max_turns,
        source=args.source,
        on_event=None if args.json else _stream_print,
    )

    if args.json:
        print(result.model_dump_json(indent=2))
        return 0

    elapsed = time.time() - started

    print(f"\n{DIM}─── Pipeline bitti ({elapsed:.1f}s) ───{RESET}\n")

    final = result.final
    neg = result.negotiation

    if final is None:
        print(f"{BOLD}Sonuç:{RESET} aday bulunamadı.")
        return 1

    print(f"{BOLD}KAZANAN{RESET}        {final.winner.title}")
    print(f"{BOLD}Liste:{RESET}         {final.winner.price:.0f} TL")
    if neg:
        print(f"{BOLD}Pazarlık:{RESET}      {neg.status} → {neg.final_price:.0f} TL ({neg.savings_tl:.0f} TL tasarruf, %{neg.savings_pct:.1f})")
        if neg.extras:
            print(f"{BOLD}Ekstralar:{RESET}     {', '.join(neg.extras)}")
    print(f"{BOLD}Güven skoru:{RESET}   {final.trust_score:.1f}/100")
    print(f"  {DIM}├─ Sahte yorum kontribü: {final.trust_breakdown.fake_ratio_contribution:.1f}{RESET}")
    print(f"  {DIM}├─ Otantiklik kontribü:  {final.trust_breakdown.authenticity_contribution:.1f}{RESET}")
    print(f"  {DIM}├─ Duygu kontribü:        {final.trust_breakdown.sentiment_contribution:.1f}{RESET}")
    print(f"  {DIM}└─ Satıcı kontribü:       {final.trust_breakdown.seller_contribution:.1f}{RESET}")

    print(f"\n{BOLD}{final.headline}{RESET}")
    print(final.explanation)

    if final.alternatives:
        print(f"\n{BOLD}Alternatifler:{RESET}")
        for alt in final.alternatives:
            print(f"  • {alt.title} — {alt.price:.0f} TL ({alt.rating}★)")

    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
