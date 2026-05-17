# AgentMarket Backend

Çoklu-ajan pazarlık asistanı. Faz 1: Sandbox seller + Negotiator çalışıyor (mock + live modlar).

## Klasör Yapısı

```
backend/
├── pyproject.toml            # Bağımlılıklar
├── .env.example              # Env değişkenleri şablonu
├── app/
│   ├── config.py             # Settings (env loader)
│   ├── models.py             # Pydantic: Product, Turn, NegotiationOutcome
│   ├── llm.py                # Gemini wrapper + mock fallback
│   ├── prompts/
│   │   ├── seller.py         # Türkçe satıcı sistem promptu
│   │   └── negotiator.py     # Türkçe müzakereci sistem promptu
│   └── agents/
│       ├── seller.py         # Sandbox satıcı + mock + persona
│       └── negotiator.py     # Müzakereci + pazarlık döngüsü
├── scripts/
│   └── test_negotiation.py   # CLI test runner
└── seed/
    └── products.py           # 4 deterministic test ürünü
```

## Hızlı Başlangıç (Mock Mode — API key gerekmez)

```bash
cd backend
pip install pydantic python-dotenv
python -m scripts.test_negotiation olta
```

Mevcut ürünler: `olta`, `kulaklik`, `klavye`, `anne_hediye`.

### Parametreler

```bash
python -m scripts.test_negotiation klavye \
    --budget 800 \
    --competitor 750 \
    --persona "öğrenci, oyuncu" \
    --target-discount 18 \
    --walk-away-discount 8
```

## Live Mode (Gerçek Gemini)

### 1. API key al

[Google AI Studio](https://aistudio.google.com/apikey) → "Create API Key". Ücretsiz tier hackathon için yeterli.

### 2. `.env` dosyasını oluştur

```bash
cp .env.example .env
```

İçeriği düzenle:

```
GEMINI_API_KEY=AIzaSy...                  # senin anahtarın
MOCK_MODE=false                           # gerçek Gemini'ye git
GEMINI_MODEL_FAST=gemini-2.5-flash
GEMINI_MODEL_PRO=gemini-2.5-pro
```

### 3. Gemini SDK yükle

```bash
pip install google-genai
```

### 4. Çalıştır

```bash
python -m scripts.test_negotiation olta
```

Aynı CLI, bu kez gerçek Gemini'ye gider. Pazarlık metinleri canlı üretilir.

## Beklenen Sonuçlar (Mock Mode)

| Ürün | Satıcı | Kişilik | Son fiyat | Tasarruf | Ekstra |
|---|---|---|---|---|---|
| olta | BalikDunyasi (4.8★, 890 satış) | cömert | 1576 TL | %17 | ücretsiz kargo |
| kulaklik | AlphaTeknoloji (4.7★, 2400) | cömert | 248 TL | %17 | ücretsiz kargo |
| klavye | GamingStoreTR (4.6★, 68k) | sıkı | 807 TL | %5 | ücretsiz kargo |
| anne_hediye | ButikAtelye (4.9★, 1100) | cömert | 406 TL | %17 | ücretsiz kargo |

## Test (geçen vs başarısız)

```bash
# Anlaşma senaryosu
python -m scripts.test_negotiation olta              # exit 0 = anlaşma

# Walk-away senaryosu (yüksek hedef + sıkı satıcı)
python -m scripts.test_negotiation klavye \
    --target-discount 25 --walk-away-discount 15     # exit 1 = anlaşma yok
```

## Mimari Notlar

- **`chat_json()` (app/llm.py):** Tek tek mock fallback yerleşik. Her ajan kendi mock'unu kendi enjekte ediyor — böylece mock mode'da bile davranış gerçekçi.
- **Concession schedule (app/agents/seller.py):** Her kişilik için 6 turluk indirim takvimi. Cömert: 0→6→12→17→19→20. Sıkı: 0→2→4→5→6→6.
- **Pazarlık akışı (app/agents/negotiator.py):** Negotiator → Seller → Negotiator → Seller … Her tur sonrası `intent="accept"` veya `intent="walk_away"` kontrolü.
- **`on_turn` callback'i:** WebSocket streaming için. Frontend bunu doğrudan tüketebilir (Faz 3).

## Sonraki Adımlar

- [x] Scout, Critic, Verifier, Decider ajanları
- [x] Orchestrator (LangGraph-shaped hand-rolled coordinator)
- [x] FastAPI WebSocket endpoint
- [x] Frontend (Next.js, ../frontend/)
- [x] LLM response cache (.llm_cache/)
- [ ] Trendyol/Hepsiburada Playwright scraper'ları
- [ ] Pitch deck slaytları
- [ ] Demo video (Plan C yedek)

## Gemini Quota Yönetimi

Ücretsiz tier sınırı: ~20 istek/gün (model başına). Bir tam pipeline çalıştırması
~25-30 Gemini çağrısı yapar — günde yalnızca 1 fresh run yapılabilir.

**Çözüm:** Disk cache (`.llm_cache/`) — aynı (system, messages, model, temperature)
imzasıyla yapılan her çağrı diskten okunur, 0 quota tüketir.

### Demo öncesi cache hazırlama

```bash
# 1. Quotanız taze olduğu bir gün:
#    .env'de MOCK_MODE=false olmalı
python -m scripts.build_cache

# Bu komut 4 altın senaryoyu çalıştırır:
# - olta (babam için)
# - kulaklik (oyuncu kuzen)
# - anne_hediye (doğum günü)
# - klavye (yazılımcı arkadaş)
#
# Toplam ~100 Gemini çağrısı → cache'lenir
# Sonraki çalıştırmalar 0 quota + ~5 saniye
```

### Geliştirme sırasında

```bash
# Mock mode: kod yapısını doğrulamak için
MOCK_MODE=true python -m scripts.test_pipeline "olta 2000 TL altı"

# Mock mode FastAPI server
MOCK_MODE=true python -m uvicorn app.api.main:app --port 8765
```

### Cache kontrol

```bash
ls .llm_cache | wc -l       # cache dosya sayısı
LLM_CACHE=0 python -m scripts.test_pipeline ...   # cache devre dışı
LLM_CACHE_BUST=1 python -m scripts.test_pipeline ...  # cache görmezden gel
```

## Trendyol Canlı Scrape (Opsiyonel)

Pitch için "gerçek ürünlerle çalışıyor" iddiasını destekleyen Playwright tabanlı
public arama sayfası okuyucusu.

### Setup

```bash
pip install playwright
python -m playwright install chromium
```

### Kullanım

```bash
# CLI:
python -m scripts.test_pipeline "oyuncu için 400 TL altı kulaklık" --source live

# Frontend: sorgu ekranında "Trendyol Canlı" toggle'ına tıkla
```

### Davranış

- Headless Chromium, gerçek UA + Türkiye locale
- İlk çağrı 10-30 saniye (network bağımlı), sonraki çağrılar `~15ms` (disk cache)
- Cache TTL: 7 gün (`backend/.scrape_cache/`)
- Hata durumunda **seed'e otomatik fallback** — UI bunu agent log'unda gösterir

### Rate limit & Etik

- Saniyede en fazla 1 arama
- Robots.txt'e ve ToS'a uyumlu (public arama sayfası)
- Üretimde marketplace partnership / resmi API yerine geçer

### Yorum Scrape

Live mode'da Scout, en popüler (yorum sayısına göre) ilk **4 ürün** için ürün
detay sayfasının `/yorumlar` URL'sini de gezer ve her birinden ilk 15 yorumu
çeker. Bu yorumlar sonra Critic'in girdisi olur.

```
Trendyol search → 8 ürün → sırala → top 4 → yorum scrape
                                            (sequential, ~5s/ürün, cached)
```

İlk live sorgu ~25 sn, sonraki cache'li sorgular ~5 sn. Yorum cache TTL 7 gün.

Çekilen alanlar:
- Yıldız (1-5, full-star/container width oranından)
- Yazar (Trendyol'un anonimleştirdiği şekilde, örn "**** ****")
- Yorum metni
- Tarih
- Verified purchase (satıcı bilgisi var mı)

API:

```python
from app.scrapers import trendyol

# Tek ürün için
reviews = trendyol.fetch_reviews(product_url, max_reviews=15)
# → list[Review] (Pydantic)
```
