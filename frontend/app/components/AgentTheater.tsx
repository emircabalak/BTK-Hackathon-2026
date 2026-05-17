"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  ScanSearch,
  ShieldCheck,
  Handshake,
  Star,
  Loader2,
  Check,
} from "lucide-react";
import type { AgentName, AgentState, AgentStatus } from "../lib/types";

const AGENT_META: Record<
  AgentName,
  { label: string; tagline: string; icon: React.ComponentType<{ size?: number; className?: string }>; color: string }
> = {
  scout: {
    label: "Scout",
    tagline: "Pazaryerlerini tarar, finalistleri seçer",
    icon: Search,
    color: "blue",
  },
  critic: {
    label: "Critic",
    tagline: "Yorumları analiz eder, sahte olanları eler",
    icon: ScanSearch,
    color: "amber",
  },
  verifier: {
    label: "Verifier",
    tagline: "Marka & ürün otantikliğini doğrular",
    icon: ShieldCheck,
    color: "cyan",
  },
  negotiator: {
    label: "Negotiator",
    tagline: "Satıcıyla pazarlık yapar, indirim alır",
    icon: Handshake,
    color: "emerald",
  },
  decider: {
    label: "Decider",
    tagline: "Tüm raporları birleştirir, kararı verir",
    icon: Star,
    color: "violet",
  },
  // orchestrator never rendered as a card
  orchestrator: { label: "Orchestrator", tagline: "", icon: Star, color: "white" },
};

const COLOR_MAP = {
  blue: {
    text: "text-blue-300",
    bg: "bg-blue-500/10",
    border: "border-blue-400/30",
    glow: "shadow-blue-500/20",
  },
  amber: {
    text: "text-amber-300",
    bg: "bg-amber-500/10",
    border: "border-amber-400/30",
    glow: "shadow-amber-500/20",
  },
  cyan: {
    text: "text-cyan-300",
    bg: "bg-cyan-500/10",
    border: "border-cyan-400/30",
    glow: "shadow-cyan-500/20",
  },
  emerald: {
    text: "text-emerald-300",
    bg: "bg-emerald-500/10",
    border: "border-emerald-400/30",
    glow: "shadow-emerald-500/20",
  },
  violet: {
    text: "text-violet-300",
    bg: "bg-violet-500/10",
    border: "border-violet-400/30",
    glow: "shadow-violet-500/20",
  },
  white: {
    text: "text-white",
    bg: "bg-white/5",
    border: "border-white/10",
    glow: "",
  },
} as const;

function StatusDot({ status }: { status: AgentStatus }) {
  if (status === "running") {
    return <Loader2 size={14} className="animate-spin text-emerald-300" />;
  }
  if (status === "done") {
    return <Check size={14} className="text-emerald-300" />;
  }
  return <span className="block h-2 w-2 rounded-full bg-white/20" />;
}

function AgentCard({
  name,
  state,
}: {
  name: Exclude<AgentName, "orchestrator">;
  state: AgentState;
}) {
  const meta = AGENT_META[name];
  const Icon = meta.icon;
  const palette = COLOR_MAP[meta.color as keyof typeof COLOR_MAP];

  const isRunning = state.status === "running";
  const isDone = state.status === "done";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, ease: "easeOut" }}
      className={`relative flex h-full min-h-[260px] flex-col overflow-hidden rounded-2xl border bg-white/[0.02] p-4 transition-all duration-300 ${
        isRunning ? `${palette.border} shadow-lg ${palette.glow}` : "border-white/[0.06]"
      } ${isDone ? "border-emerald-400/20" : ""}`}
    >
      {isRunning && (
        <div
          className={`pointer-events-none absolute -top-px left-0 right-0 h-px bg-gradient-to-r from-transparent via-emerald-400/60 to-transparent`}
        />
      )}

      {/* Header */}
      <div className="mb-3 flex items-start justify-between gap-2">
        <div className="flex items-center gap-3">
          <div
            className={`flex h-9 w-9 items-center justify-center rounded-lg ${palette.bg} ${
              isRunning ? "ring-pulse" : ""
            }`}
          >
            <Icon size={18} className={palette.text} />
          </div>
          <div>
            <h3 className={`text-sm font-semibold ${palette.text}`}>{meta.label}</h3>
            <p className="text-[11px] text-white/40">{meta.tagline}</p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1.5 rounded-full bg-white/[0.03] px-2 py-1 text-[10px] uppercase tracking-wider text-white/50">
          <StatusDot status={state.status} />
          <span>
            {state.status === "running" ? "Aktif" : state.status === "done" ? "Tamam" : "Bekliyor"}
          </span>
        </div>
      </div>

      {/* Logs */}
      <div className="relative flex-1 overflow-hidden">
        <div className="flex h-full flex-col gap-1.5 overflow-y-auto pr-1 font-mono text-[11px] leading-relaxed text-white/60">
          {state.logs.length === 0 && (
            <div className="flex h-full items-center justify-center text-white/20">
              {state.status === "pending" ? "—" : ""}
            </div>
          )}
          <AnimatePresence initial={false}>
            {state.logs.slice(-12).map((line, idx) => (
              <motion.div
                key={`${state.logs.length - 12 + idx}-${line.text.slice(0, 24)}`}
                initial={{ opacity: 0, x: -4 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.2 }}
                className={`flex items-start gap-1.5 ${
                  line.kind === "result"
                    ? "text-emerald-200"
                    : line.kind === "warn"
                    ? "text-amber-300"
                    : "text-white/55"
                }`}
              >
                <span className={`mt-1 inline-block h-1 w-1 shrink-0 rounded-full ${
                  line.kind === "result" ? "bg-emerald-400" : line.kind === "warn" ? "bg-amber-400" : "bg-white/30"
                }`} />
                <span className="break-words">{line.text}</span>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
        {/* Fade bottom */}
        <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-[#060814] to-transparent" />
      </div>
    </motion.div>
  );
}

export function AgentTheater({
  agents,
  query,
}: {
  agents: Record<AgentName, AgentState>;
  query: string;
}) {
  const cards: Exclude<AgentName, "orchestrator">[] = [
    "scout",
    "critic",
    "verifier",
    "negotiator",
    "decider",
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
      className="mx-auto w-full max-w-7xl px-4 pb-8 pt-4"
    >
      {/* Query bar */}
      <div className="mb-6 rounded-xl border border-white/5 bg-white/[0.02] px-4 py-3">
        <div className="flex items-center gap-3">
          <span className="text-xs uppercase tracking-wider text-white/40">Sorgu</span>
          <span className="flex-1 truncate text-sm text-white/80">{query}</span>
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {cards.map((name) => (
          <AgentCard key={name} name={name} state={agents[name]} />
        ))}
      </div>
    </motion.div>
  );
}
