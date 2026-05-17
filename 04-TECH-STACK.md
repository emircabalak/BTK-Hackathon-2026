# 04 — Teknoloji Yığını

## Hızlı Özet

| Katman | Seçim | Sebep |
|---|---|---|
| Frontend | Next.js 15 (App Router) | SSR + WebSocket + ekosistem |
| UI | Tailwind + shadcn/ui + Framer Motion | Hızlı + cilalı görünüm |
| Backend | Python 3.12 + FastAPI | Gemini SDK Python, async, WebSocket |
| Agent Framework | LangGraph (Langchain ekosistemi) | Slaytta açıkça izinli + state machine |
| LLM | Gemini 2.5 Flash / Pro / Vision | Slaytta zorunlu, multimodal |
| Scraping | Playwright (async) | Trendyol/Hepsiburada SPA destekler |
| DB | SQLite | Sıfır setup, hackathon için yeterli |
| Vector | Chroma (in-process) | Yorum embeddings, kolay |
| Streaming | WebSocket (FastAPI + Next.js native) | Agent events canlı |
| Deploy | Vercel (FE) + Railway/Render (BE) veya local + ngrok | Demo için yeterli |
| Package | `uv` (Python), `pnpm` (JS) | Hızlı |

---

## Detaylı Gerekçeler

### Frontend: Next.js + Tailwind + shadcn + Framer Motion

- **Next.js:** App Router ile WebSocket route'u kolay; SSR landing page → demo açılış görüntüsü cilalı.
- **shadcn/ui:** Hazır cilalı componentler — Card, Dialog, Toast, Progress. Kendi tasarım sistemini kurmaya gerek yok.
- **Framer Motion:** Ajan kartlarının "thinking..." pulse animasyonları, pazarlık penceresinin mesaj animasyonları, sonuç kartının "reveal" efekti. Jüri için ciddi cila farkı yaratır.
- **Tailwind:** Hız.

> Alternatif olarak Streamlit/Gradio düşünülebilir ama jüri "AI demo'sunda Gradio" görmeye alışkın — Next.js cilası buradan ayrışma yaratır.

### Backend: Python + FastAPI

- Gemini Python SDK olgun.
- LangGraph Python-first.
- FastAPI async + WebSocket native.
- Pydantic state şeması ile uyumlu.

### Agent Framework: LangGraph

- Slaytta açıkça izinli ("Gemini API, Langchain, Langgraph, A2A vb.").
- Paralel node desteği (Scout sonrası Critic+Verifier paralel için kritik).
- Streaming için `astream_events` API.
- Checkpoint desteği (interrupt + resume — demo'da yedek için).

> CrewAI da düşünüldü; LangGraph daha "engineer-friendly" ve slayttaki Langchain ekosistemine yakın.

### LLM: Gemini Model Karması

- **Gemini 2.5 Flash:** Scout, Critic, Verifier ve sandbox seller — yüksek throughput, düşük maliyet, paralel çalışacak.
- **Gemini 2.5 Pro:** Negotiator ve Decider — stratejik reasoning, kapanış cümlesi.
- **Gemini 2.5 Vision (Flash veya Pro):** Verifier — görsel analiz.

> Maliyet: hackathon süresinde ücretsiz tier yetmezse Anthropic kredisi yerine Google AI Studio kredisi (genelde cömert). Maliyet kontrolü için response caching agresif.

### Scraping: Playwright

- Trendyol ve Hepsiburada SPA, requests yetmez.
- Async Playwright: aynı anda 5-10 tab.
- User-agent rotation, throttle. Detay: [10-DATA-SOURCES.md](10-DATA-SOURCES.md).

### Persistance: SQLite + Chroma

- SQLite: ürün cache, query log, demo "altın senaryo" snapshot.
- Chroma: yorum embedding clustering (Critic için sahte yorum tespiti).
- Hepsi tek dosya — repo'ya commit edilebilir cache var.

### Streaming: WebSocket

```
Client (Next.js)              Server (FastAPI)
     │                              │
     ├── ws://api/agent ────────────▶
     │                              │
     │◀── {agent: "scout", ...} ────┤
     │◀── {agent: "scout", ...} ────┤
     │◀── {agent: "critic", ...} ───┤
     │◀── {agent: "critic", ...} ───┤
     │   (paralel akış)             │
     │                              │
     │◀── {stage: "done", result} ──┤
```

Frontend her event'i ilgili ajan kartına satır olarak ekler. Tipi (`thinking | tool_call | output | warn`) renge eşlenir.

### Deploy

İki opsiyon, gün-1'de karar:

**Opsiyon A — Full deploy:**
- FE: Vercel
- BE: Railway veya Render (Playwright destekler)
- Etki alanı: agentmarket.app gibi

**Opsiyon B — Local + ngrok:**
- Sunum yapan laptop'ta her şey
- ngrok ile public URL
- Avantaj: tam kontrol, internet kesilse bile demo çalışır (local-first)

> **Öneri:** Opsiyon B. Hackathonda internet kapasitesi çakışabilir; local çalışma demo güvencesi.

---

## Dependency Listesi (Tahmin)

### Backend (`pyproject.toml`)
```toml
[project]
dependencies = [
  "fastapi[standard]>=0.115",
  "uvicorn[standard]>=0.30",
  "google-genai>=0.5",        # Gemini SDK
  "langgraph>=0.2",
  "langchain-google-genai>=2.0",
  "playwright>=1.47",
  "chromadb>=0.5",
  "pydantic>=2.9",
  "websockets>=13",
  "python-dotenv>=1.0",
  "httpx>=0.27",
]
```

### Frontend (`package.json`)
```json
{
  "dependencies": {
    "next": "^15",
    "react": "^19",
    "tailwindcss": "^3.4",
    "framer-motion": "^11",
    "lucide-react": "^0.450",
    "zustand": "^4.5",
    "@radix-ui/react-*": "latest"
  }
}
```

## Çevre Değişkenleri

```
GEMINI_API_KEY=
SANDBOX_MODE=true              # gerçek satıcıya mesaj atmayı kapat
SCRAPER_CACHE_TTL=3600
DEMO_GOLDEN_QUERIES=kulaklik,klavye,hediye
```
