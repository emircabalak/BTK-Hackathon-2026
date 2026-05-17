"use client";

import { motion, useMotionValue, animate } from "framer-motion";
import { Award, ExternalLink, RotateCw, Star, TrendingDown } from "lucide-react";
import { useEffect, useState } from "react";
import type { FinalCard as FinalCardType, FinalistState } from "../lib/types";

function CountUp({ to, duration = 1 }: { to: number; duration?: number }) {
  const mv = useMotionValue(0);
  const [val, setVal] = useState(0);

  useEffect(() => {
    const ctrl = animate(mv, to, { duration, ease: "easeOut" });
    const unsub = mv.on("change", (v) => setVal(v));
    return () => {
      ctrl.stop();
      unsub();
    };
  }, [to, duration, mv]);

  return <span>{Math.round(val).toLocaleString("tr-TR")}</span>;
}

export function FinalCard({
  card,
  onReset,
  finalistsLookup,
}: {
  card: FinalCardType;
  onReset: () => void;
  finalistsLookup?: Record<string, FinalistState>;
}) {
  const w = card.winner;
  const neg = card.negotiation;
  const trustPct = Math.max(0, Math.min(100, card.trust_score));

  return (
    <motion.div
      initial={{ opacity: 0, y: 24, scale: 0.96 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.6, ease: [0.2, 0.8, 0.2, 1] }}
      className="mx-auto w-full max-w-3xl px-4 pb-12"
    >
      <div className="overflow-hidden rounded-3xl border border-emerald-400/20 bg-gradient-to-br from-emerald-500/[0.08] via-white/[0.02] to-cyan-500/[0.05] p-8 shadow-[0_20px_80px_-20px_rgba(52,211,153,0.4)]">
        {/* Top badge */}
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-300">
          <Award size={12} />
          Önerim
        </div>

        {/* Title */}
        <h2 className="text-2xl font-bold leading-tight text-white md:text-3xl">
          {w.title}
        </h2>
        <div className="mt-2 flex items-center gap-3 text-sm text-white/50">
          <span className="flex items-center gap-1">
            <Star size={12} className="text-amber-300" />
            {w.rating} ({w.review_count} yorum)
          </span>
          <span>•</span>
          <span>{w.seller.name}</span>
        </div>

        {/* Headline */}
        <div className="mt-6 rounded-xl border border-white/5 bg-white/[0.02] px-4 py-3 text-base leading-relaxed text-white/90">
          {card.headline}
        </div>

        {/* Pricing strip */}
        <div className="mt-6 flex flex-wrap items-end gap-6 border-y border-white/5 py-5">
          <div>
            <div className="text-xs uppercase tracking-wider text-white/40">Liste fiyatı</div>
            <div className="mt-0.5 text-xl font-medium text-white/50 line-through decoration-white/30">
              {w.price.toFixed(0)} TL
            </div>
          </div>
          <div className="text-2xl text-white/30">→</div>
          <div>
            <div className="text-xs uppercase tracking-wider text-emerald-300/70">Pazarlık sonrası</div>
            <div className="mt-0.5 text-3xl font-bold text-white">
              <CountUp to={neg?.final_price ?? w.price} /> TL
            </div>
          </div>
          {neg && neg.savings_tl > 0 && (
            <div className="ml-auto flex items-center gap-2 rounded-full bg-emerald-500/15 px-3 py-1.5 text-emerald-300">
              <TrendingDown size={14} />
              <span className="text-sm font-semibold">
                <CountUp to={neg.savings_tl} /> TL tasarruf (%{neg.savings_pct.toFixed(1)})
              </span>
            </div>
          )}
        </div>

        {/* Extras */}
        {neg?.extras && neg.extras.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-1.5">
            {neg.extras.map((ex) => (
              <span
                key={ex}
                className="rounded-full bg-emerald-500/15 px-2.5 py-1 text-xs font-medium text-emerald-200"
              >
                + {ex}
              </span>
            ))}
          </div>
        )}

        {/* Trust score */}
        <div className="mt-6 space-y-2">
          <div className="flex items-baseline justify-between">
            <span className="text-xs uppercase tracking-wider text-white/40">Güven Skoru</span>
            <span className="text-xl font-bold text-white">
              <CountUp to={trustPct} duration={1.4} />/100
            </span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/[0.05]">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${trustPct}%` }}
              transition={{ duration: 1.4, ease: "easeOut" }}
              className={`h-full rounded-full ${
                trustPct >= 75
                  ? "bg-gradient-to-r from-emerald-400 to-emerald-300"
                  : trustPct >= 50
                  ? "bg-gradient-to-r from-amber-400 to-amber-300"
                  : "bg-gradient-to-r from-rose-400 to-rose-300"
              }`}
            />
          </div>
          <div className="grid grid-cols-2 gap-x-4 gap-y-1 pt-1 text-xs text-white/50 md:grid-cols-4">
            <div className="flex items-center justify-between rounded-md bg-white/[0.02] px-2 py-1">
              <span className="opacity-60">Sahte yorum</span>
              <span className="font-mono text-white/80">{card.trust_breakdown.fake_ratio_contribution.toFixed(1)}</span>
            </div>
            <div className="flex items-center justify-between rounded-md bg-white/[0.02] px-2 py-1">
              <span className="opacity-60">Otantiklik</span>
              <span className="font-mono text-white/80">{card.trust_breakdown.authenticity_contribution.toFixed(1)}</span>
            </div>
            <div className="flex items-center justify-between rounded-md bg-white/[0.02] px-2 py-1">
              <span className="opacity-60">Memnuniyet</span>
              <span className="font-mono text-white/80">{card.trust_breakdown.sentiment_contribution.toFixed(1)}</span>
            </div>
            <div className="flex items-center justify-between rounded-md bg-white/[0.02] px-2 py-1">
              <span className="opacity-60">Satıcı</span>
              <span className="font-mono text-white/80">{card.trust_breakdown.seller_contribution.toFixed(1)}</span>
            </div>
          </div>
        </div>

        {/* Explanation */}
        <p className="mt-6 leading-relaxed text-white/70">{card.explanation}</p>

        {/* Actions */}
        <div className="mt-7 flex flex-wrap items-center gap-3">
          <a
            href={card.buy_link || "#"}
            target={card.buy_link ? "_blank" : undefined}
            rel="noreferrer"
            className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-500 px-5 py-2.5 text-sm font-semibold text-emerald-950 shadow-lg shadow-emerald-500/20 transition hover:scale-[1.03]"
          >
            Satıcıya git
            <ExternalLink size={14} />
          </a>
          <button
            onClick={onReset}
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/[0.02] px-5 py-2.5 text-sm text-white/70 transition hover:border-white/20 hover:bg-white/[0.05] hover:text-white"
          >
            <RotateCw size={14} />
            Yeni sorgu
          </button>
        </div>
      </div>

      {/* Alternatives */}
      {card.alternatives.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 0.4 }}
          className="mt-6"
        >
          <p className="mb-3 text-xs uppercase tracking-wider text-white/40">
            Alternatifler — neden kazanmadılar?
          </p>
          <div className="grid grid-cols-1 gap-2 md:grid-cols-2 lg:grid-cols-3">
            {card.alternatives.map((alt) => {
              const fs = finalistsLookup?.[alt.product_id];
              const trust = fs?.trust_score;
              const flags = (fs?.red_flags?.length ?? 0) + (fs?.flags?.length ?? 0);
              return (
              <div
                key={alt.product_id}
                className={`rounded-xl border p-3 transition ${
                  flags > 0
                    ? "border-rose-500/15 bg-rose-500/[0.02] hover:border-rose-500/30"
                    : "border-white/5 bg-white/[0.02] hover:border-white/10"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="text-sm leading-tight text-white/80">{alt.title}</div>
                  {trust != null && (
                    <span
                      className={`shrink-0 rounded-md px-1.5 py-0.5 font-mono text-[10px] font-semibold ${
                        trust >= 75
                          ? "bg-emerald-500/10 text-emerald-300"
                          : trust >= 50
                          ? "bg-amber-500/10 text-amber-300"
                          : "bg-rose-500/15 text-rose-300"
                      }`}
                    >
                      {trust}
                    </span>
                  )}
                </div>
                {flags > 0 && (
                  <div className="mt-1 text-[10px] text-rose-300/80">⚠ {flags} kırmızı bayrak</div>
                )}
                <div className="mt-1 flex items-center justify-between text-xs text-white/40">
                  <span>{alt.price.toFixed(0)} TL</span>
                  <span className="flex items-center gap-1">
                    <Star size={10} className="text-amber-300" />
                    {alt.rating}
                  </span>
                </div>
              </div>
              );
            })}
          </div>
        </motion.div>
      )}
    </motion.div>
  );
}
