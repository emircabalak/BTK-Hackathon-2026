# 08 — 2 Haftalık Sprint

> Hackathon tarihini bilmediğim için "T-14" formatında planladım. T-0 = jüri sunum günü.

---

## T-14 → T-13 (Faz 0: Kurulum)

### T-14 (Gün 1)
- [ ] Repo oluştur: `agentmarket` (backend + frontend monorepo)
- [ ] Gemini API key al + quota test
- [ ] Backend iskeleti: FastAPI + tek "hello agent" endpoint
- [ ] LangGraph minimal: 2 node + edge
- [ ] WebSocket testi: backend'ten frontend'e ping

**End-of-day:** Backend ayakta, frontend "hello" stream alıyor.

### T-13 (Gün 2)
- [ ] Frontend boilerplate: Next.js + Tailwind + shadcn install
- [ ] Sahne 1 (sorgu ekranı) statik mockup
- [ ] WebSocket client hook
- [ ] State management: Zustand store kurulu
- [ ] CI: lint, format

**End-of-day:** Sorgu yazılıyor, "fake agent" cevap döndürüyor, ekranda akıyor.

---

## T-12 → T-10 (Faz 1: Scout + Critic)

### T-12 (Gün 3) — Scout
- [ ] Playwright kurulumu, Trendyol arama sayfası tarayıcı
- [ ] `search_trendyol(query, max_price)` çalışıyor, 50 sonuç dönüyor
- [ ] Gemini Flash ile sorgu parse + filtreleme
- [ ] LangGraph node olarak Scout, streaming log

**Risk:** Trendyol anti-bot. Düşerse Hepsiburada'ya geç, ya da seed data hazır.

### T-11 (Gün 4) — Critic kısmi
- [ ] Yorum scraper (ürün sayfasından review listesi)
- [ ] Gemini batch ile yorum analizi
- [ ] Sahte yorum heuristikleri (kısa+5yıldız+benzer kalıp)
- [ ] Chroma embedding clustering

### T-10 (Gün 5) — Critic tam + Frontend
- [ ] Critic raporu tam JSON
- [ ] Frontend Sahne 2 — 4 ajan kart grid'i statik
- [ ] WebSocket eventleri → Scout + Critic kartına akış
- [ ] Framer Motion typewriter animasyonu

**End-of-day:** "kulaklık 300 TL altı" → Scout + Critic çalışıyor, frontend canlı, finalist listesi geliyor.

---

## T-9 → T-7 (Faz 2: Verifier + Negotiator)

### T-9 (Gün 6) — Verifier
- [ ] Gemini Vision integration
- [ ] Image otantiklik prompt
- [ ] Text consistency (specs vs açıklama)
- [ ] Frontend'de Verifier kartı dolduruluyor

### T-8 (Gün 7) — Sandbox Seller Agents
- [ ] Her finalist için bir seller persona üret (Gemini Flash)
- [ ] Seller agent prompt iskeleti
- [ ] Test: insan seller agent'la pazarlık edebiliyor mu?

### T-7 (Gün 8) — Negotiator
- [ ] Negotiator strateji prompt'u
- [ ] Multi-turn dialogue loop (LangGraph subgraph)
- [ ] Frontend pazarlık chat UI
- [ ] Mesaj streaming animasyonu

**End-of-day:** End-to-end demo çalışıyor — sorgu → 4 ajan → pazarlık → karar.

---

## T-6 → T-5 (Faz 3: Orkestrasyon ve UI Cilası)

### T-6 (Gün 9) — Decider + Karar Kartı
- [ ] Decider node: tüm raporları birleştir
- [ ] Trust score formülü
- [ ] Sahne 3 karar kartı UI
- [ ] Count-up animasyon, reveal efektleri

### T-5 (Gün 10) — UI Cila Tam Tur
- [ ] Mikro-etkileşimler (hover, focus, transition)
- [ ] Renk paleti son hali
- [ ] Mobile responsive check
- [ ] Loading skeleton'ları

**End-of-day:** Görsel olarak demo "production-grade" hissi veriyor.

---

## T-4 → T-3 (Faz 4: Demo Hazırlık)

### T-4 (Gün 11) — Altın Senaryolar
- [ ] 3 senaryo seç (balık seti, kulaklık, anne hediyesi)
- [ ] Her birini cache'le (ürünler, yorumlar, fiyatlar)
- [ ] "Live" mode + "cache" mode toggle
- [ ] Demo akış provası (3 kez)

### T-3 (Gün 12) — Pitch Hazırlığı
- [ ] Slayt setini hazırla (6 slayt, [07-JURY-PITCH.md](07-JURY-PITCH.md))
- [ ] Demo videosu yedek olarak çek (Plan C)
- [ ] Q&A hazırlığı: olası soruları cevapla, ezberle
- [ ] Pitch provasını 3 kez tam yap

---

## T-2 → T-1 (Faz 5: Buffer + Polish)

### T-2 (Gün 13) — Bug Fix Buffer
- [ ] Tüm demoyu 5 kere üst üste çalıştır, fail point bul
- [ ] 3 farklı arkadaşa izlet
- [ ] Önemli olmayan özellikleri kapat
- [ ] Error handling: graceful fallback'ler

### T-1 (Gün 14) — Final Provası
- [ ] Sunum tam tur (zaman tut, 3 dk altında)
- [ ] Plan B/C/D test
- [ ] Cihazlar şarj, kablo, adaptör
- [ ] İnternet test
- [ ] Erken uyu

---

## T-0 — Jüri Günü

**Sabah:**
- 2 saat önce kahvaltı + hafif tekrar
- 1 saat önce makine başında — son akıcılık testi
- 30 dakika önce: kapat, sakinleş

**Sunum:**
- Demo + pitch (3 dk)
- Q&A (2 dk)
- Gülümse, teşekkür et, otur

---

## Kişi Sayısı Bazında Görev Dağılımı

### 1 kişi (sadece sen)
Bu plan agresif ama olabilir. Cut list'i T-7'den itibaren agresif uygula:
- Sadece Trendyol (Hepsiburada at)
- Verifier'da Vision son aşamada
- Pazarlık 3 turdan kısa

### 2 kişi
- Sen: Backend + ajanlar
- Ortak: Frontend + UI

### 3-4 kişi
- Backend lead: orkestrasyon + ajanlar
- Frontend lead: UI + streaming
- Veri/scraping: Playwright + cache
- Pitch/demo lead: sunum, video, Q&A

---

## "Geceyi Kurtarma" Listesi (T-2 felaket senaryosu)

Eğer T-2'de hala kritik şey çalışmıyorsa, bu sırayla kes:
1. Critic'in Chroma embedding clustering — sadece heuristik kalsın
2. Verifier Vision — sadece text consistency kalsın
3. Negotiator çok turlu loop — 2 turla sınırla
4. Hepsiburada — sadece Trendyol
5. Live mode — yalnızca cache modu kalsın

Bu kesimlerle hala demo cilalı ve "wow" anlarını koruyor.
