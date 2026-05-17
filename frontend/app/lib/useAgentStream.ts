"use client";

import { useCallback, useReducer, useRef } from "react";
import type {
  AgentEvent,
  AgentName,
  AgentState,
  AppState,
  ServerMessage,
  Turn,
} from "./types";

const AGENTS: AgentName[] = ["scout", "critic", "verifier", "negotiator", "decider"];

const initialAgent: AgentState = { status: "pending", logs: [] };

const initialState: AppState = {
  scene: "idle",
  query: "",
  agents: AGENTS.reduce(
    (acc, name) => ({ ...acc, [name]: { ...initialAgent } }),
    {} as Record<AgentName, AgentState>,
  ),
  candidates: [],
  finalists: {},
  finalistOrder: [],
  winnerId: null,
  negotiationTurns: [],
  negotiationStatus: null,
  final: null,
  errorMessage: null,
  startedAt: null,
  finishedAt: null,
};

function computeTrust(f: { fake_ratio?: number; authenticity?: number; real_sentiment?: number; }): number | undefined {
  if (f.fake_ratio == null || f.authenticity == null || f.real_sentiment == null) return undefined;
  // Approximate the backend trust formula (without seller_score split)
  const fake = (1 - f.fake_ratio) * 100;
  return Math.round(0.35 * fake + 0.35 * f.authenticity + 0.30 * f.real_sentiment * 100);
}

type Action =
  | { kind: "reset" }
  | { kind: "start"; query: string }
  | { kind: "event"; event: AgentEvent }
  | { kind: "final"; result: AppState["final"]; turns: Turn[] }
  | { kind: "done" }
  | { kind: "error"; message: string };

function reducer(state: AppState, action: Action): AppState {
  switch (action.kind) {
    case "reset":
      return initialState;
    case "start":
      return {
        ...initialState,
        scene: "running",
        query: action.query,
        startedAt: Date.now(),
      };
    case "error":
      return {
        ...state,
        scene: "error",
        errorMessage: action.message,
        finishedAt: Date.now(),
      };
    case "done":
      return {
        ...state,
        scene: state.scene === "error" ? "error" : "done",
        finishedAt: state.finishedAt ?? Date.now(),
      };
    case "final":
      return {
        ...state,
        final: action.result,
        negotiationTurns:
          action.turns.length > 0 ? action.turns : state.negotiationTurns,
      };
    case "event": {
      const ev = action.event;
      const next: AppState = { ...state, agents: { ...state.agents } };

      // Track candidates from scout + capture finalist summaries
      if (ev.agent === "scout" && ev.event === "done") {
        if (ev.candidates) next.candidates = ev.candidates;
        if (ev.finalists) {
          const finalists: AppState["finalists"] = {};
          const order: string[] = [];
          for (const f of ev.finalists) {
            finalists[f.product_id] = {
              summary: f,
              critic_done: false,
              verifier_done: false,
            };
            order.push(f.product_id);
          }
          next.finalists = finalists;
          next.finalistOrder = order;
        }
      }

      // Track Critic / Verifier per-product results
      if (ev.agent === "critic" && ev.event === "result" && ev.product_id) {
        const cur = state.finalists[ev.product_id];
        if (cur) {
          const updated = {
            ...cur,
            fake_ratio: ev.fake_ratio,
            real_sentiment: ev.real_sentiment,
            red_flags: ev.red_flags,
            critic_done: true,
          };
          updated.trust_score = computeTrust(updated);
          next.finalists = { ...state.finalists, [ev.product_id]: updated };
        }
      }
      if (ev.agent === "verifier" && ev.event === "result" && ev.product_id) {
        const cur = state.finalists[ev.product_id];
        if (cur) {
          const updated = {
            ...cur,
            authenticity: ev.authenticity,
            flags: ev.flags,
            verifier_done: true,
          };
          updated.trust_score = computeTrust(updated);
          next.finalists = { ...next.finalists, [ev.product_id]: updated };
        }
      }

      // Track winner
      if (ev.agent === "orchestrator" && ev.event === "winner_picked" && ev.product_id) {
        next.winnerId = ev.product_id;
      }

      // Update per-agent status + logs
      if (ev.agent !== "orchestrator") {
        const cur = state.agents[ev.agent] ?? { status: "pending", logs: [] };
        let status = cur.status;
        if (ev.event === "start") status = "running";
        if (ev.event === "done") status = "done";

        const logs = [...cur.logs];
        const text = formatEventLine(ev);
        if (text) {
          const kind = pickKind(ev);
          logs.push({ text, kind });
          // Cap log lines per agent
          if (logs.length > 30) logs.splice(0, logs.length - 30);
        }
        next.agents = { ...next.agents, [ev.agent]: { status, logs } };
      }

      // Negotiation turns
      if (ev.agent === "negotiator" && ev.event === "turn" && ev.speaker && ev.message) {
        const turn: Turn = {
          speaker: ev.speaker,
          message: ev.message,
          intent: ev.intent ?? "counter",
          offered_price: ev.offered_price ?? null,
          internal_thought: ev.internal_thought,
          extras: ev.extras,
        };
        next.negotiationTurns = [...state.negotiationTurns, turn];
      }
      if (ev.agent === "negotiator" && ev.event === "done" && ev.status) {
        next.negotiationStatus =
          ev.status as AppState["negotiationStatus"];
      }

      return next;
    }
  }
}

function pickKind(ev: AgentEvent): "thinking" | "result" | "warn" {
  if (ev.event === "result") return "result";
  if (ev.event === "warn" || ev.event === "error") return "warn";
  return "thinking";
}

function formatEventLine(ev: AgentEvent): string {
  if (ev.message) return ev.message;
  if (ev.event === "winner_picked") return `Kazanan seçildi: ${ev.title ?? ""}`;
  if (ev.event === "finished" && ev.elapsed_ms != null)
    return `Pipeline bitti (${ev.elapsed_ms}ms)`;
  return "";
}

export function useAgentStream() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const wsRef = useRef<WebSocket | null>(null);

  const start = useCallback(
    (query: string, opts?: { budget?: number; competitor?: number; source?: string }) => {
      dispatch({ kind: "reset" });
      dispatch({ kind: "start", query });

      const wsUrl =
        process.env.NEXT_PUBLIC_WS_URL ?? "ws://127.0.0.1:8765/api/agent";
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        ws.send(
          JSON.stringify({
            type: "run",
            query,
            budget: opts?.budget,
            competitor: opts?.competitor,
            source: opts?.source ?? "seed",
          }),
        );
      };

      ws.onmessage = (evt) => {
        let msg: ServerMessage;
        try {
          msg = JSON.parse(evt.data);
        } catch {
          return;
        }
        if (msg.type === "event") {
          dispatch({ kind: "event", event: msg });
        } else if (msg.type === "final") {
          dispatch({
            kind: "final",
            result: msg.result.final ?? null,
            turns: msg.result.negotiation?.transcript ?? [],
          });
        } else if (msg.type === "done") {
          dispatch({ kind: "done" });
          ws.close();
        } else if (msg.type === "error") {
          dispatch({ kind: "error", message: msg.message });
          ws.close();
        }
      };

      ws.onerror = () => {
        dispatch({
          kind: "error",
          message: "WebSocket bağlantısı kurulamadı. Backend çalışıyor mu?",
        });
      };

      ws.onclose = () => {
        wsRef.current = null;
      };
    },
    [],
  );

  const reset = useCallback(() => {
    wsRef.current?.close();
    dispatch({ kind: "reset" });
  }, []);

  return { state, start, reset };
}
