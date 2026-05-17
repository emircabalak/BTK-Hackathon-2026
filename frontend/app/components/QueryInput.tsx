"use client";

import { ArrowRight, Database, Globe, Sparkles } from "lucide-react";
import { motion } from "framer-motion";
import { useState } from "react";

const EXAMPLES = [
  "Babam emekli oldu, balık tutmak istiyor. 2000 TL altı kaliteli olta seti",
  "Anneme doğum günü için 500 TL altı kişiye özel bir hediye",
  "Oyuncu kuzenim için 400 TL altı bluetooth kulaklık",
  "Mekanik klavye 1000 TL altı, yazılımcı için",
];

export type Source = "seed" | "live";

export function QueryInput({
  onSubmit,
}: {
  onSubmit: (query: string, opts: { competitor?: number; source: Source }) => void;
}) {
  const [value, setValue] = useState("");
  const [source, setSource] = useState<Source>("seed");

  const submit = (q: string) => {
    const trimmed = q.trim();
    if (!trimmed) return;
    onSubmit(trimmed, { source });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="mx-auto flex w-full max-w-3xl flex-col items-center gap-8 px-4 py-16"
    >
      <div className="flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/5 px-3 py-1 text-xs font-medium text-emerald-300">
        <Sparkles size={12} />
        <span>BTK Hackathon 2026 — Çoklu Ajan Alışveriş Asistanı</span>
      </div>

      <div className="text-center">
        <h1 className="bg-gradient-to-br from-white via-emerald-100 to-cyan-200 bg-clip-text text-5xl font-bold tracking-tight text-transparent md:text-6xl">
          AgentMarket
        </h1>
        <p className="mt-3 text-lg text-white/60">
          AI ajansınız sizin için arar, eler, doğrular ve <em className="text-emerald-300 not-italic">pazarlık eder</em>.
        </p>
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          submit(value);
        }}
        className="w-full"
      >
        <div className="group relative">
          <input
            value={value}
            onChange={(e) => setValue(e.target.value)}
            placeholder="Ne arıyorsunuz? (örn. babam için 2000 TL altı olta seti)"
            className="w-full rounded-2xl border border-white/10 bg-white/[0.03] px-5 py-5 pr-36 text-base text-white placeholder:text-white/30 outline-none transition focus:border-emerald-400/40 focus:bg-white/[0.05] focus:shadow-[0_0_30px_-5px_rgba(52,211,153,0.3)]"
            autoFocus
          />
          <button
            type="submit"
            disabled={!value.trim()}
            className="absolute right-2 top-1/2 -translate-y-1/2 rounded-xl bg-gradient-to-br from-emerald-400 to-emerald-500 px-4 py-2.5 text-sm font-semibold text-emerald-950 shadow-lg shadow-emerald-500/20 transition hover:scale-[1.03] hover:shadow-emerald-500/40 active:scale-95 disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:scale-100"
          >
            <span className="flex items-center gap-1.5">
              Ajansı Çalıştır
              <ArrowRight size={16} />
            </span>
          </button>
        </div>
      </form>

      {/* Source toggle */}
      <div className="flex w-full items-center justify-between gap-3 rounded-xl border border-white/[0.06] bg-white/[0.02] px-4 py-3">
        <div>
          <div className="text-xs uppercase tracking-wider text-white/40">Veri Kaynağı</div>
          <div className="mt-0.5 text-xs text-white/50">
            {source === "seed"
              ? "Yerleşik 15 test ürünü — hızlı, deterministik."
              : "Trendyol canlı arama — gerçek ürünler (ilk çağrı 10-30s)."}
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1 rounded-lg border border-white/10 bg-white/[0.02] p-0.5">
          <button
            type="button"
            onClick={() => setSource("seed")}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition ${
              source === "seed"
                ? "bg-emerald-500/15 text-emerald-300"
                : "text-white/50 hover:text-white"
            }`}
          >
            <Database size={12} />
            Seed
          </button>
          <button
            type="button"
            onClick={() => setSource("live")}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition ${
              source === "live"
                ? "bg-cyan-500/15 text-cyan-300"
                : "text-white/50 hover:text-white"
            }`}
          >
            <Globe size={12} />
            Trendyol Canlı
          </button>
        </div>
      </div>

      <div className="flex w-full flex-col gap-2">
        <p className="text-xs uppercase tracking-wider text-white/40">Örnekler</p>
        <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              type="button"
              onClick={() => {
                setValue(ex);
                submit(ex);
              }}
              className="rounded-xl border border-white/5 bg-white/[0.02] px-4 py-3 text-left text-sm text-white/70 transition hover:border-emerald-400/30 hover:bg-emerald-400/[0.03] hover:text-white"
            >
              {ex}
            </button>
          ))}
        </div>
      </div>
    </motion.div>
  );
}
