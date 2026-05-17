# 10 — Veri Kaynakları, ToS ve Sandbox Stratejisi

## Veri Kategori Haritası

| Veri | Kaynak | Yöntem | Risk | Demo'da |
|---|---|---|---|---|
| Ürün listesi | Trendyol arama | Playwright public scrape | Düşük | Live + cache |
| Ürün listesi | Hepsiburada arama | Playwright public scrape | Düşük | Cache |
| Yorumlar | Ürün detay sayfası | Playwright | Orta (volume) | Cache |
| Görsel | Ürün listing | Direct URL | Düşük | Live |
| Satıcı profil | Marketplace seller page | Playwright | Düşük | Cache |
| Pazarlık kanalı | Marketplace mesaj | **Sandbox roleplay (üretim için API/extension)** | — | Sandbox |

---

## Sandbox Seller Stratejisi (Çekirdek)

Pazarlığın gerçek satıcıya yapılması hackathon kapsamında:
- **Yasal:** Tüketici-satıcı sözleşmesi öncesi mesajlaşma marketplace ToS'lerinde kontrollü.
- **Pratik:** Her demoda canlı satıcı bulunması zor.
- **Etik:** Otomatik mesajlaşma marketplace'leri rahatsız edebilir.

**Çözüm:** Her finalist ürün için bir **roleplay seller agent** üretiyoruz.

### Seller Agent Üretim Pipeline

```python
def build_seller_agent(product: Product) -> SellerAgent:
    public_data = {
        "product_title": product.title,
        "list_price": product.price,
        "seller_name": product.seller,
        "seller_rating": product.seller_rating,
        "past_responses": fetch_seller_replies(product.seller_id),  # public yorumlardaki cevaplar
        "category_margin": estimate_margin(product.category),
    }
    personality = infer_personality(public_data)  # cömert/normal/sıkı
    return SellerAgent(
        system_prompt=SELLER_PROMPT.format(**public_data, personality=personality),
        max_discount_pct=margin_to_discount(public_data["category_margin"]),
    )
```

**Kalibrasyon:**
- Cömert satıcı: %15-25 indirim aralığı
- Normal: %5-15
- Sıkı: %0-8

Demo için: **2 cömert + 1 normal seller** seçilir, böylece pazarlık her zaman güzel bitiyor.

---

## Trendyol Scrape Notları

Public arama sayfası, anti-bot var ama nazikçe davranınca geçilebilir:

```python
async def search_trendyol(query: str, max_price: int):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=random.choice(UAS),
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()
        url = f"https://www.trendyol.com/sr?q={quote(query)}&prc=0-{max_price}"
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(2000)  # nazik bekle
        items = await page.query_selector_all("div.p-card-wrppr")
        # parse...
```

**Anti-detection:**
- Playwright-stealth eklentisi
- User-agent rotation (5'lik liste)
- Mouse hareketi simülasyonu
- Sayfa başına 3 saniye delay

**Rate limit kuralı:** Saniyede 1 istek, dakikada 30. Daha hızlı ise sırada bekle.

**Cache layer:**
```python
@cache_with_ttl(seconds=3600)
def search_trendyol_cached(query, max_price):
    return search_trendyol(query, max_price)
```

Cache miss → live; cache hit → instant. Demo'da sıklıkla cache hit (önceden ısıtılmış).

---

## Yorum Scrape

Trendyol ürün sayfası, yorumlar lazy-load. Çözüm: "Yorumlar" tabına tıkla, scroll, JSON request'i yakala.

```python
async def fetch_reviews(product_url: str, max_reviews=200):
    # detay sayfası aç
    # yorum tabına scroll
    # network'ten JSON'u intercept et
    # alternatif: HTML parse
```

200 yoruma kadar çekiyoruz (Gemini context'i hatır sayar, 1M-token tutar ama batch'te 200 yeterli).

---

## Görsel İndirme

Görsel URL'leri ürün cevabıyla geliyor. İndirme gereksiz — Gemini Vision URL'i direkt alabiliyor:

```python
response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[
        Part.from_uri(image_url, mime_type="image/jpeg"),
        "Bu fotoğrafı analiz et: stok mu, orijinal mi?"
    ]
)
```

---

## Seed Dataset (Cache / Fallback)

Anti-bot sıkışırsa kullanılacak `seed/` klasörü:

```
seed/
├── kulaklik_300tl.json       # 25 ürün + yorumlar
├── klavye_1000tl.json        # 25 ürün + yorumlar
├── olta_2000tl.json          # 25 ürün + yorumlar
├── anne_hediye_500tl.json    # 25 ürün + yorumlar
└── sirt_cantasi_800tl.json   # 25 ürün + yorumlar
```

Toplam ~125 ürün, ~5000 yorum. Repo'da commit. **Demo'nun beli buradan kırılır.**

Her dosya formatı:
```json
{
  "query": "300 TL altı bluetooth kulaklık",
  "fetched_at": "2026-05-10",
  "products": [
    {
      "id": "trendyol_12345",
      "title": "...",
      "price": 299,
      "image_url": "...",
      "seller": {...},
      "reviews": [...]
    }
  ]
}
```

---

## Yasal ve ToS Notları (Pitch'te savunma için)

- **Robots.txt:** Trendyol robots.txt'sini denetledik, arama sayfası public/indexable. Saygılı rate limit ile uyumlu.
- **Mesajlaşma:** Üretim sürümünde marketplace partnership ile resmi API. Hackathon kapsamı: sandbox.
- **KVKK:** Kullanıcı sorgusu dışında kişisel veri toplamıyoruz. Demo sırasında log'lar local.
- **Telif:** Görseller marketplace üzerinden referans, indirme ve yeniden dağıtım yok.

---

## Veri Saklama ve Temizlik

- Sorgu logları SQLite, 30 gün TTL
- Yorum embeddings Chroma, sorgu sonrası flush
- Kullanıcı email/identifier yok (anonim)
- Demo sonrası tüm cache temizlenir

---

## Production Geçişi (Vizyon)

| Şimdi (Sandbox) | Üretim |
|---|---|
| Playwright scrape | Trendyol/Hepsiburada Partner API |
| Roleplay seller agents | Gerçek satıcı mesaj kanalları (extension veya API) |
| 5 senaryo seed | Live, sürekli güncel |
| Local SQLite | Postgres + Redis |
| Tek kullanıcı | Multi-tenant + auth |

Pitch'te bu tablo: **"Hackathon'da temeli kurduk, üretime hazır."**
