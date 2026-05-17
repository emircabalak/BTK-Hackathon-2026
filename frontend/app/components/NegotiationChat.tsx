"use client";

import { motion, AnimatePresence } from "framer-motion";
import { Store, User } from "lucide-react";
import { useEffect, useRef } from "react";
import type { Turn } from "../lib/types";

export function NegotiationChat({
  turns,
  status,
  sellerName,
}: {
  turns: Turn[];
  status: string | null;
  sellerName?: string;
}) {
  const bottomRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns.length, status]);

  if (turns.length === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="mx-auto w-full max-w-3xl px-4 pb-8"
    >
      <div className="overflow-hidden rounded-2xl border border-emerald-400/20 bg-gradient-to-b from-emerald-500/[0.04] to-transparent">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-white/5 bg-white/[0.02] px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-400" />
            </span>
            <span className="text-sm font-medium text-emerald-200">
              Canlı Pazarlık {sellerName ? `— ${sellerName}` : ""}
            </span>
          </div>
          {status && (
            <span
              className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                status === "agreement"
                  ? "bg-emerald-500/15 text-emerald-300"
                  : status === "walk_away"
                  ? "bg-amber-500/15 text-amber-300"
                  : "bg-white/10 text-white/60"
              }`}
            >
              {labelFor(status)}
            </span>
          )}
        </div>

        {/* Messages */}
        <div className="flex flex-col gap-3 p-4">
          <AnimatePresence initial={false}>
            {turns.map((t, idx) => (
              <ChatBubble key={`${idx}-${t.message.slice(0, 16)}`} turn={t} />
            ))}
          </AnimatePresence>
          <div ref={bottomRef} />
        </div>
      </div>
    </motion.div>
  );
}

function labelFor(status: string): string {
  return (
    {
      agreement: "✓ Anlaşma",
      walk_away: "Vazgeçildi",
      no_movement: "Hareket yok",
      max_turns: "Tur dolu",
    } as Record<string, string>
  )[status] ?? status;
}

function ChatBubble({ turn }: { turn: Turn }) {
  const isNegotiator = turn.speaker === "negotiator";
  const Icon = isNegotiator ? User : Store;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={`flex items-end gap-2 ${isNegotiator ? "flex-row" : "flex-row-reverse"}`}
    >
      <div
        className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${
          isNegotiator ? "bg-cyan-500/15 text-cyan-300" : "bg-amber-500/15 text-amber-300"
        }`}
      >
        <Icon size={14} />
      </div>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm ${
          isNegotiator
            ? "rounded-bl-sm bg-cyan-500/[0.08] text-cyan-50"
            : "rounded-br-sm bg-amber-500/[0.08] text-amber-50"
        }`}
      >
        <div className="text-[10px] font-medium uppercase tracking-wider opacity-50">
          {isNegotiator ? "Negotiator" : "Satıcı"}
        </div>
        <div className="mt-0.5 leading-relaxed">{turn.message}</div>
        {(turn.offered_price != null || (turn.extras && turn.extras.length > 0)) && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {turn.offered_price != null && (
              <span className="rounded-full bg-white/[0.06] px-2 py-0.5 text-[10px] text-white/70">
                {turn.offered_price.toFixed(0)} TL
              </span>
            )}
            {turn.extras?.map((ex) => (
              <span
                key={ex}
                className="rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] text-emerald-200"
              >
                + {ex}
              </span>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}
