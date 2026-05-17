"use client";

import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, Check, Crown, Loader2, Star } from "lucide-react";
import type { FinalistState } from "../lib/types";

export function FinalistsPanel({
  finalistOrder,
  finalists,
  winnerId,
  negotiationStarted,
}: {
  finalistOrder: string[];
  finalists: Record<string, FinalistState>;
  winnerId: string | null;
  negotiationStarted: boolean;
}) {
  if (finalistOrder.length === 0) return null;

  // Sort: winner first, then by trust_score desc, then by original order
  const sorted = [...finalistOrder].sort((a, b) => {
    if (a === winnerId) return -1;
    if (b === winnerId) return 1;
    const ta = finalists[a]?.trust_score ?? -1;
    const tb = finalists[b]?.trust_score ?? -1;
    return tb - ta;
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="mx-auto w-full max-w-7xl px-4 pb-6"
    >
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs uppercase tracking-wider text-white/40">
          <span>Adaylar</span>
          <span className="rounded-full bg-white/[0.04] px-1.5 py-0.5 text-[10px] text-white/50">
            {finalistOrder.length}
          </span>
        </div>
        {winnerId && (
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-1.5 rounded-full bg-emerald-500/15 px-3 py-1 text-[11px] font-medium text-emerald-300"
          >
            <Crown size={11} />
            Kazanan seçildi
          </motion.div>
        )}
      </div>

      <motion.div
        layout
        className="grid grid-cols-2 gap-2.5 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5"
      >
        <AnimatePresence>
          {sorted.map((pid) => {
            const state = finalists[pid];
            if (!state) return null;
            const isWinner = pid === winnerId;
            const isDimmed = !!winnerId && !isWinner && negotiationStarted;
            return (
              <FinalistCard
                key={pid}
                state={state}
                isWinner={isWinner}
                isDimmed={isDimmed}
              />
            );
          })}
        </AnimatePresence>
      </motion.div>
    </motion.div>
  );
}

function FinalistCard({
  state,
  isWinner,
  isDimmed,
}: {
  state: FinalistState;
  isWinner: boolean;
  isDimmed: boolean;
}) {
  const { summary } = state;
  const trust = state.trust_score;
  const both_done = state.critic_done && state.verifier_done;
  const has_red = (state.red_flags?.length ?? 0) > 0 || (state.flags?.length ?? 0) > 0;
  const suspicious = (state.fake_ratio ?? 0) > 0.3 || (state.authenticity ?? 100) < 60;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{
        opacity: isDimmed ? 0.35 : 1,
        scale: isWinner ? 1.02 : 1,
        y: 0,
      }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
      className={`relative flex flex-col gap-2 overflow-hidden rounded-xl border p-3 transition-colors ${
        isWinner
          ? "border-emerald-400/50 bg-emerald-500/[0.05] shadow-lg shadow-emerald-500/10"
          : suspicious
          ? "border-rose-400/20 bg-rose-500/[0.02]"
          : "border-white/[0.06] bg-white/[0.02]"
      }`}
    >
      {isWinner && (
        <div className="pointer-events-none absolute -top-px left-0 right-0 h-px bg-gradient-to-r from-transparent via-emerald-400 to-transparent" />
      )}

      {/* Title */}
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="line-clamp-2 text-xs font-medium leading-tight text-white/90">
            {summary.title}
          </div>
          <div className="mt-1 flex items-center gap-2 text-[10px] text-white/40">
            <span className="flex items-center gap-0.5">
              <Star size={9} className="text-amber-300" />
              {summary.rating.toFixed(1)}
            </span>
            <span>·</span>
            <span>{summary.review_count} yorum</span>
          </div>
        </div>
        <div className="shrink-0 text-right">
          <div className="text-sm font-semibold text-white">{summary.price.toFixed(0)}</div>
          <div className="text-[10px] text-white/40">TL</div>
        </div>
      </div>

      {/* Score bars */}
      <div className="space-y-1.5">
        <ScoreBar
          label="Sahte"
          value={state.fake_ratio == null ? null : (1 - state.fake_ratio) * 100}
          loading={!state.critic_done}
          invert
          tone={state.fake_ratio != null && state.fake_ratio > 0.3 ? "danger" : "emerald"}
        />
        <ScoreBar
          label="Otantik"
          value={state.authenticity ?? null}
          loading={!state.verifier_done}
          tone={(state.authenticity ?? 100) < 60 ? "danger" : "cyan"}
        />
      </div>

      {/* Footer */}
      <div className="mt-auto flex items-center justify-between border-t border-white/5 pt-2 text-[10px]">
        <div className="flex items-center gap-1">
          {both_done ? (
            has_red ? (
              <span className="flex items-center gap-1 text-rose-300">
                <AlertTriangle size={10} />
                <span>{(state.red_flags?.length ?? 0) + (state.flags?.length ?? 0)} bayrak</span>
              </span>
            ) : (
              <span className="flex items-center gap-1 text-emerald-300">
                <Check size={10} />
                <span>Temiz</span>
              </span>
            )
          ) : (
            <span className="flex items-center gap-1 text-white/40">
              <Loader2 size={10} className="animate-spin" />
              <span>Analiz</span>
            </span>
          )}
        </div>
        {trust != null && (
          <div
            className={`rounded-md px-1.5 py-0.5 font-mono text-[10px] font-semibold ${
              isWinner
                ? "bg-emerald-500/20 text-emerald-200"
                : trust >= 75
                ? "bg-emerald-500/10 text-emerald-300"
                : trust >= 50
                ? "bg-amber-500/10 text-amber-300"
                : "bg-rose-500/10 text-rose-300"
            }`}
          >
            {trust}
          </div>
        )}
      </div>
    </motion.div>
  );
}

function ScoreBar({
  label,
  value,
  loading,
  tone,
  invert: _invert,
}: {
  label: string;
  value: number | null;
  loading: boolean;
  tone: "emerald" | "cyan" | "danger";
  invert?: boolean;
}) {
  const colorMap = {
    emerald: "bg-emerald-400/80",
    cyan: "bg-cyan-400/80",
    danger: "bg-rose-400/80",
  } as const;

  return (
    <div className="flex items-center gap-2 text-[10px]">
      <span className="w-12 shrink-0 text-white/40">{label}</span>
      <div className="relative flex-1 overflow-hidden rounded-full bg-white/[0.04]">
        {loading ? (
          <div className="h-1 w-full bg-gradient-to-r from-white/5 via-white/10 to-white/5 bg-[length:200%_100%]">
            <div className="absolute inset-0 animate-pulse bg-white/[0.04]" />
          </div>
        ) : (
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.max(0, Math.min(100, value ?? 0))}%` }}
            transition={{ duration: 0.7, ease: "easeOut" }}
            className={`h-1 rounded-full ${colorMap[tone]}`}
          />
        )}
      </div>
      <span className="w-7 shrink-0 text-right font-mono text-white/60">
        {value == null ? "—" : `${Math.round(value)}`}
      </span>
    </div>
  );
}
