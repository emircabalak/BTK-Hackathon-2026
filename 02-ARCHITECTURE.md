# 02 — Mimari

## Yüksek Seviye Şema

```
┌──────────────────────────────────────────────────────────────┐
│                         FRONTEND                              │
│  Next.js (App Router) + Tailwind + shadcn + Framer Motion     │
│  - Sorgu girişi                                                │
│  - 4 ajan canlı panelleri (WebSocket stream)                  │
│  - Pazarlık chat penceresi                                    │
│  - Sonuç kartı                                                │
└────────────────────────┬─────────────────────────────────────┘
                         │ WebSocket (agent events)
                         │ REST (query, result)
┌────────────────────────▼─────────────────────────────────────┐
│                         BACKEND                               │
│  FastAPI + LangGraph + Gemini SDK                             │
│                                                                │
│           ┌─────────────┐                                     │
│           │ Orchestrator │  (LangGraph state machine)          │
│           └──────┬──────┘                                     │
│                  │                                             │
│      ┌───────────┼───────────┐                                │
│      ▼           ▼           ▼                                │
│  ┌────────┐ ┌────────┐ ┌──────────┐                          │
│  │ Scout  │ │ Critic │ │ Verifier │  (paralel çalışır)        │
│  └───┬────┘ └───┬────┘ └─────┬────┘                          │
│      │          │            │                                 │
│      └──────────┼────────────┘                                 │
│                 ▼                                              │
│           ┌──────────┐                                         │
│           │Negotiator│  (sıralı, sonda)                        │
│           └────┬─────┘                                         │
│                │                                               │
│                ▼                                               │
│         ┌─────────────────┐                                    │
│         │  Sandbox Seller │  (Gemini-powered roleplay)         │
│         │     Agents      │                                    │
│         └─────────────────┘                                    │
└──────────────────────────────────────────────────────────────┘
        │                          │
        ▼                          ▼
┌──────────────┐          ┌────────────────┐
│  SQLite +    │          │  Playwright    │
│  Chroma      │          │  scrapers      │
│  (ürün cache)│          │  (Trendyol vb.)│
└──────────────┘          └────────────────┘
```

## LangGraph State Şeması

```python
class AgentState(TypedDict):
    # Girdi
    query: str
    budget_max: int | None
    user_persona: str | None  # "öğrenci, oyuncu, 4 saat/gün kullanım"

    # Scout çıktısı
    candidates: list[Product]  # 8 finalist
    scout_log: list[str]

    # Critic çıktısı
    review_analysis: dict[str, ReviewReport]  # product_id → rapor
    critic_log: list[str]

    # Verifier çıktısı
    authenticity: dict[str, AuthenticityReport]
    verifier_log: list[str]

    # Negotiator çıktısı
    negotiation: NegotiationTranscript
    final_offer: Offer
    negotiator_log: list[str]

    # Karar
    winner: Product
    trust_score: float  # 0..100
    savings_tl: float
    explanation: str
```

## Akış (LangGraph topolojisi)

```python
graph = StateGraph(AgentState)
graph.add_node("scout", scout_agent)
graph.add_node("critic", critic_agent)
graph.add_node("verifier", verifier_agent)
graph.add_node("negotiator", negotiator_agent)
graph.add_node("decider", decision_node)

graph.set_entry_point("scout")
# Scout sonrası Critic + Verifier paralel
graph.add_edge("scout", "critic")
graph.add_edge("scout", "verifier")
# İkisi de bittikten sonra Negotiator
graph.add_edge("critic", "negotiator")
graph.add_edge("verifier", "negotiator")
# Birleştirme: Negotiator iki edge'i bekler
graph.add_edge("negotiator", "decider")
graph.add_edge("decider", END)
```

## Streaming Katmanı

Her ajan, kendi node'unda `yield` ile **adım adım** durum bildiriyor (LangGraph'ın `astream_events` API'si). Backend bunu WebSocket üzerinden frontend'e push ediyor:

```json
{
  "agent": "scout",
  "event": "thinking",
  "message": "Trendyol'da 47 sonuç buldum, filtreliyorum...",
  "timestamp": 1715852400.123
}
```

Frontend bu eventleri ajan kartlarına satır satır akıtıyor. **Demoda jüri bu canlı akışı görüyor.**

## Sandbox Seller Agents

Pazarlığın **etik/yasal** yönünü çözmek için: her aday ürün için Gemini'ye o satıcının public verilerini (yorum geçmişi, ortalama yanıt tonu, kategori) vererek bir **roleplay seller agent** çalıştırıyoruz. Negotiator bu sandbox ile pazarlık yapıyor.

- Avantaj: yasal/etik temiz, demo'da %100 kontrol edilebilir
- Avantaj: satıcı kişiliği kalibre edilebilir (cömert satıcı, sert satıcı, ortada)
- Üretim için: marketplace partnerships (pitch'te belirtilecek)

Detay: [10-DATA-SOURCES.md](10-DATA-SOURCES.md).

## Persistans

- **SQLite:** ürün cache, sorgu logu, demo "altın senaryo" cache
- **Chroma:** yorum embeddings (Critic'in benzer yorum gruplaması için)
- **In-memory:** çalışma anındaki AgentState (LangGraph)

## Gemini Model Dağılımı

| Ajan | Model | Sebep |
|---|---|---|
| Scout | Gemini 2.5 Flash | Hızlı filtreleme, basit reasoning |
| Critic | Gemini 2.5 Flash | Çok sayıda yorum, throughput öncelik |
| Verifier | Gemini 2.5 Flash + Vision | Multimodal gerekli |
| Negotiator | Gemini 2.5 Pro | Stratejik reasoning, dilbilgisi |
| Seller (sandbox) | Gemini 2.5 Flash | Roleplay, ucuz |
| Decider | Gemini 2.5 Pro | Final açıklama metni |

## Ölçeklenme

Hackathonda gerek yok ama Q&A için hazır cevap:
- Scout → Cloud Run / AWS Lambda, ürün başına bağımsız
- Critic → batch processing, Gemini batch API
- Cache → Redis (production'da)
- Negotiator → her satıcı için isolated worker
