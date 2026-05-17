"""Orchestrator — drives the full AgentMarket pipeline.

Flow:
    Scout
      ├─▶ Critic (per-product, parallel internally)
      └─▶ Verifier (per-product, parallel internally)
            └─▶ Negotiator (on top winner)
                  └─▶ Decider
                        └─▶ FinalCard

Each stage emits events via the `on_event` callback so a WebSocket layer
can stream agent activity to the frontend in real time.

This is a hand-rolled LangGraph-shaped coordinator. We can swap to real
LangGraph later without changing the event shape.
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from app.agents.critic import run_critic_one
from app.agents.decider import compute_trust_score, pick_winner, run_decider
from app.agents.negotiator import negotiate
from app.agents.scout import run_scout
from app.agents.seller import build_persona
from app.agents.verifier import run_verifier_one
from app.models import (
    NegotiationContext,
    NegotiationOutcome,
    PipelineResult,
    Product,
    Turn,
)

log = logging.getLogger(__name__)


EventCallback = Callable[[dict[str, Any]], None]


def _emit(on_event: EventCallback | None, **payload: Any) -> None:
    if on_event is None:
        return
    payload.setdefault("ts", time.time())
    on_event(payload)


def _leverage_points_from_reports(critic, verifier) -> list[str]:
    out = []
    if critic.fake_ratio > 0.2:
        out.append("yorumlarda sahte yorum şüphesi var")
    for t in critic.topics:
        if t.score < -0.2:
            out.append(f"{t.topic.replace('_', ' ')} ile ilgili şikayetler var")
    for f in (verifier.flags or [])[:2]:
        out.append(f"satıcı/açıklama: {f}")
    if not out:
        out.append("genel müşteri memnuniyeti yüksek, hızlı kapanış")
    return out[:3]


def run_pipeline(
    query: str,
    *,
    budget_max: float | None = None,
    competitor_avg_price: float | None = None,
    on_event: EventCallback | None = None,
    target_discount_pct: float = 15.0,
    walk_away_discount_pct: float = 5.0,
    max_negotiation_turns: int = 6,
    source: str = "seed",
) -> PipelineResult:
    pipeline_start = time.time()
    _emit(on_event, agent="orchestrator", event="start", query=query)

    # ── Stage 1: Scout ─────────────────────────────────────────────
    _emit(on_event, agent="scout", event="start", message="Sorgu inceleniyor...")
    scout_out = run_scout(query, source=source)
    for line in scout_out.log:
        _emit(on_event, agent="scout", event="thinking", message=line)
    _emit(
        on_event,
        agent="scout",
        event="done",
        message=f"{len(scout_out.candidates)} finalist seçildi",
        candidates=[p.product_id for p in scout_out.candidates],
        finalists=[
            {
                "product_id": p.product_id,
                "title": p.title,
                "price": p.price,
                "rating": p.rating,
                "review_count": p.review_count,
                "image_url": p.image_url,
                "seller_name": p.seller.name,
                "seller_rating": p.seller.rating,
                "seller_sales": p.seller.total_sales,
            }
            for p in scout_out.candidates
        ],
    )

    finalists = scout_out.candidates
    if not finalists:
        _emit(on_event, agent="orchestrator", event="aborted", reason="no_candidates")
        return PipelineResult(query=query, scout=scout_out)

    # ── Stage 2: Critic + Verifier in parallel ─────────────────────
    _emit(on_event, agent="critic", event="start", message=f"{len(finalists)} ürün yorum analizine alındı")
    _emit(on_event, agent="verifier", event="start", message=f"{len(finalists)} ürün doğrulamaya alındı")

    critic_reports: dict[str, Any] = {}
    verifier_reports: dict[str, Any] = {}

    def _critic_task(p: Product):
        _emit(on_event, agent="critic", event="thinking", message=f"{p.title[:40]}... yorumları analiz ediliyor", product_id=p.product_id)
        rep = run_critic_one(p)
        msg = f"%{rep.fake_ratio*100:.0f} şüpheli yorum, gerçek memnuniyet %{rep.real_sentiment*100:.0f}"
        if rep.red_flags:
            msg += f" — kırmızı bayrak: {rep.red_flags[0]}"
        _emit(
            on_event,
            agent="critic",
            event="result",
            message=msg,
            product_id=p.product_id,
            fake_ratio=rep.fake_ratio,
            real_sentiment=rep.real_sentiment,
            red_flags=rep.red_flags,
        )
        return p.product_id, rep

    def _verifier_task(p: Product):
        _emit(on_event, agent="verifier", event="thinking", message=f"{p.title[:40]}... otantiklik kontrolü", product_id=p.product_id)
        rep = run_verifier_one(p)
        msg = f"otantiklik skoru {rep.overall_authenticity:.0f}/100"
        if rep.flags:
            msg += f" — bayrak: {rep.flags[0]}"
        _emit(
            on_event,
            agent="verifier",
            event="result",
            message=msg,
            product_id=p.product_id,
            authenticity=rep.overall_authenticity,
            flags=rep.flags,
        )
        return p.product_id, rep

    with ThreadPoolExecutor(max_workers=min(8, len(finalists) * 2)) as ex:
        critic_futures = [ex.submit(_critic_task, p) for p in finalists]
        verifier_futures = [ex.submit(_verifier_task, p) for p in finalists]
        for fut in critic_futures:
            pid, rep = fut.result()
            critic_reports[pid] = rep
        for fut in verifier_futures:
            pid, rep = fut.result()
            verifier_reports[pid] = rep

    _emit(on_event, agent="critic", event="done", message=f"{len(critic_reports)} rapor tamam")
    _emit(on_event, agent="verifier", event="done", message=f"{len(verifier_reports)} rapor tamam")

    # ── Stage 3: Pick top for negotiation ──────────────────────────
    winner, _alts = pick_winner(finalists, critic_reports, verifier_reports)
    winner_trust, _ = compute_trust_score(
        critic=critic_reports[winner.product_id],
        verifier=verifier_reports[winner.product_id],
    )
    _emit(
        on_event,
        agent="orchestrator",
        event="winner_picked",
        product_id=winner.product_id,
        title=winner.title,
        trust_score=winner_trust,
    )

    # ── Stage 4: Negotiator ────────────────────────────────────────
    _emit(on_event, agent="negotiator", event="start", message=f"{winner.seller.name} ile pazarlık başlıyor")
    persona = build_persona(winner)
    leverage = _leverage_points_from_reports(
        critic_reports[winner.product_id], verifier_reports[winner.product_id]
    )
    ctx = NegotiationContext(
        product=winner,
        budget_max=budget_max,
        competitor_avg_price=competitor_avg_price,
        user_persona=scout_out.parsed.persona or None,
        leverage_points=leverage,
        target_discount_pct=target_discount_pct,
        walk_away_discount_pct=walk_away_discount_pct,
        max_turns=max_negotiation_turns,
    )

    def _emit_turn(turn: Turn) -> None:
        _emit(
            on_event,
            agent="negotiator",
            event="turn",
            speaker=turn.speaker,
            message=turn.message,
            intent=turn.intent,
            offered_price=turn.offered_price,
            extras=turn.extras,
            internal_thought=turn.internal_thought,
        )

    negotiation: NegotiationOutcome = negotiate(
        context=ctx,
        seller_persona=persona,
        on_turn=_emit_turn,
    )

    _emit(
        on_event,
        agent="negotiator",
        event="done",
        status=negotiation.status,
        savings_tl=negotiation.savings_tl,
        savings_pct=negotiation.savings_pct,
    )

    # ── Stage 5: Decider ───────────────────────────────────────────
    _emit(on_event, agent="decider", event="start", message="Karar metni üretiliyor")
    final = run_decider(
        finalists=finalists,
        critic_reports=critic_reports,
        verifier_reports=verifier_reports,
        negotiation=negotiation,
    )
    _emit(
        on_event,
        agent="decider",
        event="done",
        winner=final.winner.product_id,
        trust_score=final.trust_score,
        headline=final.headline,
    )

    total_ms = int((time.time() - pipeline_start) * 1000)
    _emit(on_event, agent="orchestrator", event="finished", elapsed_ms=total_ms)

    return PipelineResult(
        query=query,
        scout=scout_out,
        critic=critic_reports,
        verifier=verifier_reports,
        negotiation=negotiation,
        final=final,
    )
