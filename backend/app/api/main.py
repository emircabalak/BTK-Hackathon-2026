"""FastAPI app — REST + WebSocket endpoints wrapping the orchestrator.

Endpoints:
- GET  /api/health                → simple status
- POST /api/run                   → run pipeline, return final result (no streaming)
- WS   /api/agent                 → stream agent events live

WebSocket protocol:
1. Client connects to /api/agent
2. Client sends: {"type": "run", "query": "...", "budget": ..., "competitor": ...}
3. Server streams events: {"type": "event", "agent": "...", "event": "...", ...}
4. Server sends: {"type": "final", "result": <PipelineResult>}
5. Server sends: {"type": "done"} and closes
6. On error: {"type": "error", "message": "..."}
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.agents.orchestrator import run_pipeline
from app.config import get_settings

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI(title="AgentMarket", version="0.1.0")

# CORS — allow Next.js dev server (and anything else for local hackathon work)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict[str, Any]:
    settings = get_settings()
    return {
        "status": "ok",
        "mock_mode": settings.mock_mode,
        "models": {
            "fast": settings.gemini_model_fast,
            "pro": settings.gemini_model_pro,
        },
        "ts": time.time(),
    }


class RunRequest(BaseModel):
    query: str
    budget: float | None = None
    competitor: float | None = None
    target_discount_pct: float = 15.0
    walk_away_discount_pct: float = 5.0
    max_negotiation_turns: int = 6
    source: str = "seed"  # "seed" | "live"


@app.post("/api/run")
async def run(req: RunRequest) -> dict[str, Any]:
    """Synchronous run — no streaming. Returns final PipelineResult JSON."""
    result = await asyncio.to_thread(
        run_pipeline,
        req.query,
        budget_max=req.budget,
        competitor_avg_price=req.competitor,
        target_discount_pct=req.target_discount_pct,
        walk_away_discount_pct=req.walk_away_discount_pct,
        max_negotiation_turns=req.max_negotiation_turns,
        source=req.source,
    )
    return result.model_dump()


@app.websocket("/api/agent")
async def agent_ws(ws: WebSocket) -> None:
    """Run pipeline and stream every agent event to the client."""
    await ws.accept()
    try:
        msg = await ws.receive_json()
    except Exception as e:  # noqa: BLE001
        await ws.send_json({"type": "error", "message": f"Bad opening message: {e}"})
        await ws.close()
        return

    if msg.get("type") != "run":
        await ws.send_json({"type": "error", "message": "First message must be {type:'run'}"})
        await ws.close()
        return

    try:
        req = RunRequest(
            query=msg["query"],
            budget=msg.get("budget"),
            competitor=msg.get("competitor"),
            target_discount_pct=msg.get("target_discount_pct", 15.0),
            walk_away_discount_pct=msg.get("walk_away_discount_pct", 5.0),
            max_negotiation_turns=msg.get("max_negotiation_turns", 6),
            source=msg.get("source", "seed"),
        )
    except Exception as e:  # noqa: BLE001
        await ws.send_json({"type": "error", "message": f"Invalid run params: {e}"})
        await ws.close()
        return

    queue: asyncio.Queue[dict | None] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def on_event(payload: dict) -> None:
        # Called from worker thread → schedule a queue push on the loop.
        try:
            asyncio.run_coroutine_threadsafe(queue.put({"type": "event", **payload}), loop)
        except RuntimeError:
            log.warning("Event after loop closed: %s", payload)

    async def runner() -> None:
        try:
            result = await asyncio.to_thread(
                run_pipeline,
                req.query,
                budget_max=req.budget,
                competitor_avg_price=req.competitor,
                on_event=on_event,
                target_discount_pct=req.target_discount_pct,
                walk_away_discount_pct=req.walk_away_discount_pct,
                max_negotiation_turns=req.max_negotiation_turns,
                source=req.source,
            )
            await queue.put({"type": "final", "result": result.model_dump()})
        except Exception as e:  # noqa: BLE001
            log.exception("Pipeline failed")
            await queue.put({"type": "error", "message": str(e)})
        finally:
            await queue.put(None)  # sentinel

    runner_task = asyncio.create_task(runner())

    try:
        while True:
            item = await queue.get()
            if item is None:
                break
            await ws.send_json(item)
        await ws.send_json({"type": "done"})
    except WebSocketDisconnect:
        log.info("Client disconnected")
        runner_task.cancel()
    except Exception as e:  # noqa: BLE001
        log.exception("WebSocket loop failed")
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:  # noqa: BLE001
            pass
    finally:
        if not runner_task.done():
            runner_task.cancel()
        try:
            await ws.close()
        except Exception:  # noqa: BLE001
            pass
