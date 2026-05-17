"use client";

import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle } from "lucide-react";
import { AgentTheater } from "./components/AgentTheater";
import { FinalCard } from "./components/FinalCard";
import { FinalistsPanel } from "./components/FinalistsPanel";
import { NegotiationChat } from "./components/NegotiationChat";
import { QueryInput } from "./components/QueryInput";
import { useAgentStream } from "./lib/useAgentStream";

export default function Home() {
  const { state, start, reset } = useAgentStream();

  const elapsedSec =
    state.startedAt && state.finishedAt
      ? ((state.finishedAt - state.startedAt) / 1000).toFixed(1)
      : null;

  return (
    <main className="min-h-screen">
      <AnimatePresence mode="wait">
        {state.scene === "idle" && (
          <motion.div
            key="scene-1"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, y: -16 }}
            transition={{ duration: 0.4 }}
            className="flex min-h-screen items-center justify-center"
          >
            <QueryInput
              onSubmit={(q, opts) => start(q, opts)}
            />
          </motion.div>
        )}

        {state.scene !== "idle" && (
          <motion.div
            key="scene-active"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="pt-8"
          >
            {/* Top header */}
            <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 pb-2">
              <div className="flex items-center gap-3">
                <span className="bg-gradient-to-br from-emerald-200 to-cyan-200 bg-clip-text text-2xl font-bold tracking-tight text-transparent">
                  AgentMarket
                </span>
                {elapsedSec && (
                  <span className="rounded-full bg-white/[0.04] px-2.5 py-0.5 text-xs text-white/50">
                    {elapsedSec}s
                  </span>
                )}
                {/* Agent dot row — at-a-glance progress */}
                <div className="ml-2 hidden items-center gap-1.5 sm:flex">
                  {(["scout", "critic", "verifier", "negotiator", "decider"] as const).map((name) => {
                    const st = state.agents[name].status;
                    return (
                      <span
                        key={name}
                        title={name}
                        className={`block h-1.5 w-6 rounded-full transition-colors ${
                          st === "done"
                            ? "bg-emerald-400"
                            : st === "running"
                            ? "bg-emerald-400/60 animate-pulse"
                            : "bg-white/10"
                        }`}
                      />
                    );
                  })}
                </div>
              </div>
              <button
                onClick={reset}
                className="rounded-lg border border-white/10 bg-white/[0.02] px-3 py-1.5 text-xs text-white/60 transition hover:border-white/20 hover:text-white"
              >
                Yeni sorgu
              </button>
            </div>

            {/* Error */}
            {state.scene === "error" && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mx-auto mb-4 flex w-full max-w-3xl items-start gap-3 rounded-xl border border-rose-500/30 bg-rose-500/5 p-4 text-rose-200"
              >
                <AlertTriangle size={18} className="mt-0.5 shrink-0" />
                <div>
                  <div className="font-medium">Bir sorun oldu</div>
                  <div className="mt-1 text-sm text-rose-200/80">
                    {state.errorMessage ?? "Bilinmeyen hata."}
                  </div>
                  <div className="mt-2 text-xs text-rose-200/60">
                    Backend çalışıyor mu? <code className="rounded bg-rose-500/10 px-1 py-0.5">uvicorn app.api.main:app --port 8765</code>
                  </div>
                </div>
              </motion.div>
            )}

            {/* Agent theater (always visible during run + done) */}
            <AgentTheater agents={state.agents} query={state.query} />

            {/* Finalists panel — shows per-product analysis as it happens */}
            <FinalistsPanel
              finalistOrder={state.finalistOrder}
              finalists={state.finalists}
              winnerId={state.winnerId}
              negotiationStarted={state.negotiationTurns.length > 0}
            />

            {/* Negotiation chat appears once turns start coming */}
            <NegotiationChat
              turns={state.negotiationTurns}
              status={state.negotiationStatus}
              sellerName={state.final?.winner.seller.name}
            />

            {/* Final card */}
            <AnimatePresence>
              {state.final && (
                <FinalCard
                  card={state.final}
                  onReset={reset}
                  finalistsLookup={state.finalists}
                />
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}
