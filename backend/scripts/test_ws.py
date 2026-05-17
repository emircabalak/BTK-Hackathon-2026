"""Quick WebSocket smoke-test.

Connects to the local API, sends a run request, prints every event.
"""

from __future__ import annotations

import asyncio
import json
import sys

import websockets


async def main() -> int:
    query = sys.argv[1] if len(sys.argv) > 1 else "oyuncu kuzenim için 400 TL altı bluetooth kulaklık"
    url = "ws://127.0.0.1:8765/api/agent"

    async with websockets.connect(url) as ws:
        await ws.send(json.dumps({"type": "run", "query": query, "competitor": 320}))
        n_events = 0
        while True:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=60)
            except asyncio.TimeoutError:
                print("[timeout]")
                return 1
            msg = json.loads(raw)
            mtype = msg.get("type")
            if mtype == "event":
                n_events += 1
                a = msg.get("agent", "?")
                e = msg.get("event", "?")
                m = msg.get("message", "")
                spk = msg.get("speaker", "")
                summary = m or spk or json.dumps({k: v for k, v in msg.items() if k not in ("type","agent","event","ts")})[:80]
                print(f"  [{a:13}/{e:9}] {summary[:120]}")
            elif mtype == "final":
                final = msg["result"].get("final") or {}
                neg = msg["result"].get("negotiation") or {}
                print(f"\n=== FINAL ===")
                print(f"Winner: {final.get('winner', {}).get('title')}")
                print(f"Trust:  {final.get('trust_score')}/100")
                if neg:
                    print(f"Saved:  {neg.get('savings_tl')} TL ({neg.get('savings_pct'):.1f}%)")
                print(f"Headline: {final.get('headline')}")
                print(f"Total events: {n_events}")
            elif mtype == "done":
                return 0
            elif mtype == "error":
                print(f"ERROR: {msg.get('message')}")
                return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
