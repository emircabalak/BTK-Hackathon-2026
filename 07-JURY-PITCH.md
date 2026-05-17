# 07 — Jüri Pitch & Slayt İçerikleri

## Pitch'in 5 Tek Cümle Versiyonu

> **AgentMarket — AI ajansınız Türk pazaryerlerinde sizin için arar, sahte yorumları eler, ürün otantikliğini doğrular ve satıcıyla pazarlık yapar.**

## Pitch'in 30 Saniyelik Versiyonu

> "Bir tüketici online alışverişe ortalama 14 dakika harcıyor — çoğu sahte yorum ayıklamak ve fiyat kıyaslamakla geçiyor. AgentMarket dört uzman AI ajanı kullanarak bunu sizin için 30 saniyeye indiriyor. Scout pazaryerlerini tarar, Critic yorumlardan sahte olanları eler, Verifier ürün otantikliğini Gemini Vision ile doğrular, Negotiator satıcıyla canlı pazarlık yapar. Çıktı: tek bir karar kartı — ürün, güven skoru, ve sizin için kazanılan tasarruf."

---

## Slayt Akışı (6 Slayt)

### Slayt 1 — Başlık

```
        AgentMarket
        AI ajansınız sizin için pazarlık eder.

        BTK Hackathon 2026 — Takım: [Takım Adı]
```

Tek görsel: logo + tagline. Koyu zemin.

### Slayt 2 — Problem

**Üst yarı — büyük rakamlar:**
```
150 milyar TL    14 dakika      %18
e-ticaret 2025   sorgu başı     sahte yorum oranı
                 araştırma       (sektör tahmini)
```

**Alt yarı — bir karakter hikâyesi:**
> Ali, balık tutmak isteyen babasına olta seti almak istiyor.
> Trendyol açar — 200 sonuç. Yarısı çakma görünüyor. Yorumların yarısı şüpheli.
> 40 dakika sonra hala karar veremedi. Sonunda yine yanlış aldı.

### Slayt 3 — Çözüm (Tek Slayt)

```
┌──────────────────────────────────────────┐
│ AgentMarket Multi-Agent Pipeline         │
│                                          │
│   🛒 SCOUT ─┬─▶ 🔍 CRITIC ──┐           │
│             │                │           │
│             └─▶ 🛡 VERIFIER ─┴─▶ 🤝 NEGOTIATOR ──▶ KARAR     │
│                                                              │
│   Tara          Yorumları       Otantikliği    Pazarlık     │
│                 Ele             Doğrula        Yap          │
└──────────────────────────────────────────┘
```

3 cümle alt-açıklama:
- 4 ajan, LangGraph orkestrasyonu, A2A mesajlaşma
- Gemini 2.5 Pro + Flash + Vision karması
- Doğal dilde sorgudan 30 sn'de karara

### Slayt 4 — Canlı Demo

> "Slayt yok. Demo zamanı."

**Demo geçişi.** Detay: [06-DEMO-SCRIPT.md](06-DEMO-SCRIPT.md).

### Slayt 5 — Teknik Mimari

Mimari diyagramı ([02-ARCHITECTURE.md](02-ARCHITECTURE.md)). Önemli not satırları:

- **Frontend:** Next.js 15 + Tailwind + Framer Motion (canlı agent streaming UI)
- **Backend:** FastAPI + LangGraph (4 paralel ajan)
- **LLM:** Gemini 2.5 (Pro/Flash/Vision) — slaytta zorunlu Gemini-ana-ürün gereği
- **Sandbox:** Etik pazarlık katmanı (üretim için: marketplace partnerships)

### Slayt 6 — Yol Haritası ve Kapanış

```
Şimdi    → Hackathon MVP — 4 ajan + sandbox
1 ay     → Browser extension (Chrome, Edge)
3 ay     → Trendyol partnership pilotu
6 ay     → Mobil + B2B "satıcı tarafı" sürümü
1 yıl    → Türkiye'nin AI alışveriş katmanı
```

Alt: **"Slaytlarda istenen tüm framework'leri kullandık. Gemini ana ürün, LangGraph orkestrasyon, A2A multi-agent protokolü. Üretime hazır mimari, hackathon zamanı geldi."**

---

## Değerlendirme Kriterlerine Eşleme (BTK Hackathon kriterleri — slaytlarda örnekler verilmiş)

| Kriter | Bizim cevabımız |
|---|---|
| **Yenilikçilik** | Multi-agent pazarlık + sandbox seller mimarisi Türkiye'de örneği yok |
| **Teknik Derinlik** | LangGraph paralel orkestrasyon, multimodal Gemini Vision, A2A protokol, streaming UI |
| **Kullanılabilirlik** | 30 sn'de karar, doğal dil sorgu, tek bir kart sonuç |
| **Pazar Potansiyeli** | 150 milyar TL e-ticaret pazarı + tüketici aracı + B2B satıcı tarafı |
| **Sunum / Demo** | Canlı pazarlık görüntüsü, hava trafik kontrolü UI'ı, akıcı 3 dk demo |
| **Gemini Kullanımı** | 3 farklı Gemini modeli (Pro, Flash, Vision), her ajan farklı kullanım |

---

## Sıkça Beklenen Eleştiriler ve Cevaplar

### "Bu Honey/Karma gibi extension'ların aynısı değil mi?"

> Hayır. Honey kupon ekler; Karma fiyat takip eder. Hiçbiri **yorumları okuyup eleştirmiyor**, **görsel otantiklik kontrolü yapmıyor**, ve hiçbiri **satıcıyla pazarlık yapmıyor**. AgentMarket bu üçünü tek paket sunan ilk üründür.

### "Pazarlık etik mi?"

> Tüketici, satıcıyla pazarlık etmek için bir insan vekiline (ör. asistan) yetki verebilir. AI vekil aynı prensipte çalışır, şeffaflıkla — mesaj başlığında "AI asistan olarak yazıyorum" notu var. Bu ABD'de "AI agents" kategorisinde aktif tartışılan bir alan; Türkiye'de erken olmak avantaj.

### "Sahte yorum tespiti %100 değil"

> Hiçbir sahte yorum tespit sistemi %100 değil. Bizim sistemimiz **şeffaf**: kullanıcıya "bu üründe %23 şüpheli yorum, sebep şu kalıplar" diye gerekçe veriyor. Karar son kullanıcının; biz aracı sunuyoruz.

### "Gerçek ürünleri scrape etmek yasal mı?"

> Public arama sayfalarını rate-limit'e uyarak okuyoruz; bu Türk hukukunda ve marketplace ToS'lerinde tüketici yararına izin verilen bir alan. Üretimde resmi API/partner sürümüne geçiyoruz.

### "Neden 1.-3. olmadığınızı kanıtlayın"

> Slaytta "2024 ve 2025'te derece alan takımlar katılamaz" — bizim ekibimiz [doğrula]. Üye listesi public.

---

## Sunum Yapan İçin Stil Notları

- **Hız:** Konuştuğunla aynı şey ekranda olsun. "Şu an critic'i izleyin" derken o kart vurgulanmalı.
- **Sessizlik:** Pazarlık akarken **sus**. Mesajlar konuşsun. Bu en güçlü an.
- **Vücut:** Laptop'a değil jüriye bak. Demo otomatik akıyor.
- **Kapanış:** "Teşekkürler" sonrası 2 saniye sessiz dur, sonra otur.

## Ekibe Kıyafet Notu

Hackathon casual ama sunan kişi tek tip, sade (siyah/koyu). Marka logosu olmasın — dikkat dağıtır.
