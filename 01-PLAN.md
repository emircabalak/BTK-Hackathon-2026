# 01 — Uygulama Planı

## Hedef

Jürinin önünde **3 dakikalık bir demo** içinde:
1. Doğal dilde alışveriş isteği gir
2. 4 ajan paralel çalışsın (canlı görsel)
3. 30 saniye içinde aday ürünler süzülsün
4. Bir satıcıyla canlı pazarlık penceresi açılsın
5. İndirim alındığını ve "güven skoru"nu göster
6. Tek bir karar kartında bitir

## Başarı Kriterleri

| Kriter | Eşik |
|---|---|
| Demo'da agent grafiği canlı görüntü | Zorunlu |
| Pazarlıkta indirim alma | %80+ deneme başarı |
| End-to-end süre | ≤ 60 sn |
| Sahte yorum tespiti | İnsana göre ≥ %75 uyum |
| UI cila seviyesi | "Production-grade" hissi |

> **Mantra:** "Daha fazla özellik" değil, **"daha keskin tek bir demo"**. Cut list (aşağıda) erken hazır olsun, sınırı geçen her özellik fedaya hazır.

---

## Faz Planı

### Faz 0 — Kurulum (1 gün)
- Repo iskeleti (backend + frontend monorepo)
- Gemini API anahtarı, ücretsiz limit testi
- LangGraph "merhaba dünya" minimal grafik
- Next.js + Tailwind + shadcn boilerplate

**DoD:** Tek bir Gemini çağrısı backend'ten frontend'e WebSocket ile akıyor.

### Faz 1 — Scout + Critic (3 gün)
- Trendyol/Hepsiburada arama scraperları (Playwright)
- 50 ürünü ilk 8'e indirme (Scout)
- Yorum çekme + Gemini analizi (Critic)
- Sahte yorum heuristikleri + Gemini judgment
- Backend → frontend canlı agent log streaming

**DoD:** Arama girişi → 8 finalist ürün listesi + her birinin "yorum sağlığı skoru".

### Faz 2 — Verifier + Negotiator (3 gün)
- Verifier: ürün görselini Gemini Vision'a verme, stok foto/orijinal foto/üretim hatası tespiti
- Marka otantiklik check (logo, etiket, açıklama tutarlılığı)
- **Sandbox seller agents:** her finalist için Gemini ile "satıcı kişiliği" simülasyonu (ürün, profil, geçmiş yorum tonu)
- Negotiator: gerçek satıcı diyaloğu (sandbox tarafı seller agent ile)
- İndirim/kupon alma mantığı

**DoD:** Bir ürün için canlı pazarlık penceresi + en az %5 indirim teklifi.

### Faz 3 — Orkestrasyon ve UI (2 gün)
- LangGraph state machine: parallel scout → critic → verifier → negotiator
- "Air traffic control" UI: 4 ajan kartı, canlı log akışı, ilerleme barı
- Sonuç kartı: ürün + güven skoru + tasarruf + "Satın al" linki
- Framer Motion animasyonları

**DoD:** End-to-end akış, 4 ajan canlı görselle, tek tıkla başlatılabilir.

### Faz 4 — Demo Cilası (2 gün)
- 3 dakikalık sunum akışı provası
- Yedek demo videosu (internet/API çökerse)
- Önbelleğe alınmış "altın senaryo": kesin çalışacak 3 örnek sorgu
- Pitch deck final
- Sunucu deploy (Vercel + Railway/Render veya local + ngrok)

**DoD:** 3 farklı senaryo (kulaklık, klavye, anne hediyesi) için %100 güvenilir demo.

### Tampon (1 gün)
- Bug fix, edge case, jüri Q&A hazırlığı

---

## Cut List (Süre Daralırsa Sırayla At)

1. ~~Birden fazla pazaryeri~~ → Sadece **Trendyol** kalsın
2. ~~Real-time scraping~~ → Önceden cache'lenmiş 200 ürün üzerinden çalış (jüri demo'da fark etmez, sahte değil — cache açıklanır)
3. ~~Verifier'da Vision~~ → Sadece metin tutarlılığıyla yetin (daha sonra Vision eklenir)
4. ~~Karmaşık pazarlık stratejisi~~ → Tek tur teklif/karşı teklif (3 turdan kısa)
5. ~~Kullanıcı hesabı / kayıtlı tercihler~~ → Stateless

## Kesinlikle Atmayacağımız Şeyler

- 4 ajanlı canlı görsel (bu olmadan demo ölü)
- Pazarlık penceresinin gerçekten akması (sandbox da olsa)
- Final sonuç kartı (tasarruf + güven skoru)
- 3 dakikalık akıcı sunum

---

## Ölçü-Düzelt Döngüsü

Her gün sonunda 3 soru:
1. Bugün demo'ya 1 dakika eklendi mi, çıktı mı?
2. "Kesilemez" listesinden bir şey hala risk altında mı?
3. Yarınki en kritik 1 görev nedir?

Cevap "evet/risk" ise → ertesi gün cut list'ten bir madde at.
