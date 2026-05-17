"""Pre-cache golden demo scenarios.

Run this ONCE in live mode (with fresh Gemini quota) to populate the
local LLM cache (.llm_cache/). After that, every demo run uses the
cache (0 quota, ~0.1s instead of ~25s).

Usage:
    # 1. Ensure .env has MOCK_MODE=false and a working GEMINI_API_KEY
    # 2. Run:
    python -m scripts.build_cache

    # 3. To rebuild a single scenario:
    python -m scripts.build_cache --only kulaklik

The cache files are deterministic per (system, messages, tier, temperature)
so subsequent calls hit the cache. Safe to commit `.llm_cache/` to git
for demo guarantee — these are golden, vetted responses.
"""

from __future__ import annotations

import argparse
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


GOLDEN_SCENARIOS: list[dict] = [
    {
        "id": "olta",
        "query": "Babam emekli oldu, balık tutmak istiyor. 2000 TL altı kaliteli olta seti",
        "competitor": 1750,
    },
    {
        "id": "kulaklik",
        "query": "Oyuncu kuzenim için 400 TL altı bluetooth kulaklık",
        "competitor": 320,
    },
    {
        "id": "anne_hediye",
        "query": "Anneme doğum günü için 500 TL altı kişiye özel bir hediye",
        "competitor": 380,
    },
    {
        "id": "klavye",
        "query": "Yazılımcı arkadaşıma 1000 TL altı mekanik klavye",
        "competitor": 850,
    },
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Gemini cache for demo scenarios")
    parser.add_argument("--only", help="Sadece bu id'yi çalıştır (örn: olta)", default=None)
    args = parser.parse_args()

    settings = get_settings()
    if settings.mock_mode:
        print("⚠ MOCK_MODE=true → bu script yalnızca live modda işe yarar.")
        print("  .env dosyasında MOCK_MODE=false yap, sonra yeniden çalıştır.")
        return 1

    scenarios = [s for s in GOLDEN_SCENARIOS if (args.only is None or s["id"] == args.only)]
    if not scenarios:
        print(f"Bilinen id'ler: {[s['id'] for s in GOLDEN_SCENARIOS]}")
        return 1

    print(f"\n{'='*60}")
    print(f"  Cache builder — {len(scenarios)} senaryo, live Gemini")
    print(f"{'='*60}\n")

    total_start = time.time()
    results: list[tuple[str, float, bool]] = []

    for sc in scenarios:
        print(f"▶ [{sc['id']}] {sc['query']}")
        start = time.time()
        try:
            result = run_pipeline(
                sc["query"],
                competitor_avg_price=sc.get("competitor"),
            )
            elapsed = time.time() - start
            ok = result.final is not None
            results.append((sc["id"], elapsed, ok))
            if ok:
                neg = result.negotiation
                print(
                    f"  ✓ {elapsed:.1f}s · kazanan: {result.final.winner.title[:50]} "
                    f"({neg.savings_tl:.0f} TL tasarruf)"
                    if neg
                    else f"  ✓ {elapsed:.1f}s"
                )
            else:
                print(f"  ✗ aday bulunamadı ({elapsed:.1f}s)")
        except Exception as e:  # noqa: BLE001
            elapsed = time.time() - start
            results.append((sc["id"], elapsed, False))
            print(f"  ✗ HATA: {e}")
            if "429" in str(e):
                print(
                    "    ↳ Quota tükenmiş. Yarın tekrar dene veya billing aktive et."
                )

    total = time.time() - total_start
    print(f"\n{'='*60}")
    print(f"  Bitti — toplam {total:.1f}s, {sum(1 for _, _, ok in results if ok)}/{len(results)} başarılı")
    print(f"  Cache: {_BACKEND_ROOT / '.llm_cache'}")
    print(f"{'='*60}\n")

    return 0 if all(ok for _, _, ok in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
