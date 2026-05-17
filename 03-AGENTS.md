# 03 — Ajan Spec'leri

Her ajanın: amacı, girdisi, çıktısı, kullandığı araçlar, prompt iskeleti ve başarısızlık modu.

---

## Orchestrator (LangGraph)

**Rol:** Conductor. Kullanıcı sorgusunu parse eder, Scout'u başlatır, Critic+Verifier'ı paralel tetikler, sonuçları Negotiator'a iletir, Decider'da kapatır.

**Giriş:** `query: str`

**Çıkış:** `AgentState` (her node'un ürettikleriyle dolu)

**Mantık:** LangGraph state machine — kod 02-ARCHITECTURE.md'de.

**Yan görev:** Her node geçişinde WebSocket'e "stage_change" eventi at.

---

## 1. Scout (İz Sürücü)

**Amaç:** Pazaryerlerinde geniş arama → 50-100 sonuç → ilk 8 finalist.

**Girdi:**
```python
{
  "query": "300 TL altı bluetooth oyuncu kulaklığı",
  "budget_max": 300,
  "marketplaces": ["trendyol", "hepsiburada"]
}
```

**Çıkış:**
```python
{
  "candidates": [Product, ...],  # 8 adet
  "log": ["Trendyol'da 47 sonuç", "fiyat filtresi sonrası 23", ...]
}
```

**Araçlar:**
- `search_trendyol(query, max_price) -> list[ProductRaw]` — Playwright
- `search_hepsiburada(query, max_price) -> list[ProductRaw]` — Playwright
- `gemini.parse_query(query)` — bütçe, kategori, persona çıkarma

**Prompt iskeleti (parse aşaması):**
```
Sen bir Türk e-ticaret asistanısın. Aşağıdaki kullanıcı sorgusundan
şunları çıkar: kategori, max_fiyat, must_have_özellikler, nice_to_have, persona.
Sorgu: {query}
JSON formatında dön.
```

**Filtreleme heuristiği (Gemini'ye geçmeden önce):**
- Bütçe dışı: at
- Yıldız < 3.5: at
- Yorum sayısı < 10: at
- Stokta yok: at

**Skorlama (Gemini Flash ile, top 8 için):**
```
Ürün listesi: {products}
Kullanıcı ihtiyacı: {parsed_query}
Her ürüne 0-100 arası "uygunluk" skoru ver, gerekçeyle.
Top 8'i seç.
```

**Başarısızlık modları:**
- Pazaryeri scraping bloklanırsa → cache'lenmiş 200 ürünlük seed dataset
- Boş sonuç → "Bütçeyi 50 TL arttırmayı dener misin?" önerisi

---

## 2. Critic (Eleştirmen)

**Amaç:** Her finalist için tüm yorumları analiz et → "yorum sağlığı" raporu.

**Girdi:** `candidates: list[Product]` (8 adet)

**Çıkış:**
```python
{
  product_id: {
    "fake_ratio": 0.18,        # şüpheli yorum %
    "real_sentiment": 0.72,    # gerçek yorumların ortalaması
    "topics": {                # ne diyorlar
      "ses_kalitesi": +0.8,
      "konfor": -0.3,
      "pil_ömrü": +0.6,
      "kargo": -0.5
    },
    "red_flags": ["satıcı yorumlara cevap vermiyor", ...],
    "quote": "En çok şikayet edilen: 'mikrofon zayıf'",
  }
}
```

**Araçlar:**
- `fetch_reviews(product_id) -> list[Review]` — Playwright
- `gemini.batch_classify(reviews)` — Flash, batch

**Sahte yorum tespiti (üç sinyal birleşimi):**
1. **Heuristik:** kısa yorum + 5 yıldız + benzer kelime kalıbı + yeni hesap
2. **Embedding clustering:** Chroma ile çok benzer yorumları kümeleme (tek elden yazılmış mı?)
3. **Gemini judgment:** "Bu yorum gerçek bir alıcıdan mı, satıcıdan/promotörden mi geliyor olabilir? Sebebini belirt."

**Prompt iskeleti (her ürün için):**
```
Sen bir e-ticaret yorum dedektifisin. Aşağıdaki {N} yorumu analiz et:
{reviews}

Çıktı (JSON):
1. fake_ratio: şüpheli yorum oranı (0-1) + neden
2. topic_sentiment: {konu: skor} formatında
3. red_flags: kırmızı bayraklar listesi
4. representative_quote: en bilgilendirici tek alıntı
```

**Başarısızlık modları:**
- Yorum sayısı az → "yetersiz veri" bayrağı, skoru düşür
- Hepsi şüpheli → ürünü Decider'a "düşük güven" işaretiyle ilet

---

## 3. Verifier (Doğrulayıcı)

**Amaç:** Ürün otantikliği. Aldığın gerçekten resimdeki ürün mü, satıcı sahte mi?

**Girdi:** `candidates: list[Product]`

**Çıkış:**
```python
{
  product_id: {
    "image_score": 87,           # orijinal foto mu, kalitesi nasıl
    "brand_consistency": 92,     # marka-açıklama-görsel tutarlı mı
    "spec_consistency": 78,      # specler birbiriyle çelişiyor mu
    "seller_score": 65,          # satıcı geçmişi, eski yorumları
    "overall_authenticity": 80,
    "flags": ["görsel başka bir ürünün stok fotosu olabilir", ...]
  }
}
```

**Araçlar:**
- `gemini.vision(image_url, prompt)` — multimodal
- `gemini.text(specs)` — tutarlılık check

**Vision prompt:**
```
Bu görseli analiz et:
1. Stok fotoğrafı mı, gerçek ürün fotoğrafı mı?
2. Görseldeki ürün, açıklama ile uyumlu mu? Açıklama: {description}
3. Logo/etiket görünüyor mu, marka iddiası ile uyumlu mu?
4. Şüpheli unsurlar (bulanık, çakma görünüm, başka ürün) var mı?

JSON dön.
```

**Başarısızlık modları:**
- Görsel yok → "stok foto eksik" işareti
- Vision API yavaş → Faz 1'de skip, sadece metin tutarlılığı yap

---

## 4. Negotiator (Müzakereci)

**Amaç:** En iyi 1-2 finalist için satıcıyla sandbox kanalda pazarlık → indirim/kupon al.

**Girdi:**
- `winner_candidates: list[Product]` (top 2)
- `user_persona`
- `critic_report` + `verifier_report` (kaldıraç için: "yorumlarda kargo şikayeti çok, kargo ücretsiz olur mu?")

**Çıkış:**
```python
{
  "transcript": [
    {"from": "negotiator", "msg": "..."},
    {"from": "seller", "msg": "..."},
    ...
  ],
  "final_offer": {
    "original_price": 299,
    "negotiated_price": 252,
    "savings_pct": 15.7,
    "extras": ["ücretsiz kargo", "2 yıl garanti"]
  },
  "log": ["İlk teklif: %20 indirim", "Satıcı %10'da direndi", ...]
}
```

**Stratejik aşamalar:**
1. **Açılış:** kibar selamlama, ürün ilgisi
2. **Kaldıraç sun:** rakip fiyat referansı, kullanım niyeti, ödeme yöntemi
3. **İlk teklif:** %20-25 indirim (yüksek anchor)
4. **Karşı teklif değerlendir:** Eğer satıcı %5 verdiyse → %12 iste; eğer hiç vermediyse → kombinasyon iste (indirim + kargo)
5. **Kapanış:** Hedef %10-15 indirim civarında anlaş, ekstra koparmaya çalış

**Prompt iskeleti (her tur):**
```
Sen bir uzman tüketici müzakerecisin. Görev: bu satıcıdan
{ürün} için en iyi indirimi kopar.

Bilgiler:
- Liste fiyatı: {price}
- Rakip ortalama: {competitor_avg}
- Kullanıcı bütçesi: {budget}
- Yorumlardan eldeki kozlar: {leverage_points}
- Şimdiye kadar yapılan diyalog: {transcript}

Bir sonraki mesajın ne olmalı? Türkçe, kibar ama kararlı.
Hedef: anlaşma %X-Y aralığında. Vazgeçme noktası: %Z.
```

**Sandbox Seller (karşı taraf):**
```
Sen bir Türk e-ticaret satıcısısın. Profilin:
- Yıllık satış: {volume}
- Kâr marjı: {margin}
- Karakter: {personality}  # cömert/normal/sıkı
- Yorum tonu: {past_response_style}

Müşteri sana mesaj atıyor. Tipik bir satıcı gibi cevap ver.
Asla %{max_discount}'tan fazla indirim verme. Marjın izin verdiği kadar pazarlık et.
```

**Başarısızlık modları:**
- 5 turdan uzun → "anlaşma sağlanamadı, mevcut fiyat" deyip kapat
- Satıcı hostil → diğer adayla pazarlık başlat

---

## 5. Decider (Karar Verici)

**Amaç:** Tüm raporları birleştir → tek karar kartı + açıklama.

**Girdi:** Tüm AgentState

**Çıkış:**
```python
{
  "winner": Product,
  "trust_score": 84,  # critic + verifier ağırlıklı
  "savings_tl": 47,
  "headline": "Sony WH-1000 muadili, %92 gerçek yorumlu, %16 indirimli.",
  "explanation_md": "Bu ürünü öneriyorum çünkü...",
  "alternatives": [Product, Product],
  "buy_link": "https://..."
}
```

**Skorlama formülü:**
```
trust_score = 0.4 * (1 - fake_ratio) * 100
            + 0.3 * authenticity_score
            + 0.2 * real_sentiment * 100
            + 0.1 * seller_score
```

**Gemini Pro prompt:**
```
Tüm ajan raporları:
- Scout: {top_8}
- Critic: {review_reports}
- Verifier: {auth_reports}
- Negotiator: {final_offers}

Kullanıcıya 2-3 cümlelik bir öneri yaz. Hangi ürünü neden seçtiğini,
neden diğerlerinin önüne geçtiğini, dürüstçe söyle. Türkçe, sıcak ton.
```

---

## Ajan İletişim Protokolü (A2A esinli)

Ajanlar arası mesajlar şu şekilde:

```python
@dataclass
class AgentMessage:
    from_agent: str
    to_agent: str | Literal["broadcast"]
    intent: str  # "request", "report", "warn"
    payload: dict
    timestamp: float
```

Slayttaki "A2A" vurgusuna doğrudan karşılık geliyor — Q&A'de "biz LangGraph üstünde A2A-uyumlu mesaj şeması kullandık" denilebilir.
