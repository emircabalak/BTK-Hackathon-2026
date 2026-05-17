# 09 — Risk Haritası

Hackathon kazanmanın yolu çoğunlukla risk yönetiminden geçer — "her şey çalışır" varsayımı yerine **"hangi tek şey çökerse demo ölür"** sorusuna cevap vermek.

---

## P0 — Demo Öldürücü Riskler

### R1. İnternet kesilir / API yavaşlar
- **Olasılık:** Orta
- **Etki:** Felaket — demo donuk kalır
- **Önlem:**
  1. **Cache mode:** Önceden çalıştırılmış 3 altın senaryo SQLite'da hazır
  2. **Pre-recorded video:** 60 sn'lik tam demo videosu yedek
  3. **Local-first:** Backend laptop'ta çalışıyor, dış servis bağımlılığı sadece Gemini API
- **Tetikleyici:** Demo başlamadan 2 dk önce Gemini'ye test ping. Yavaşsa cache moda manuel geç.

### R2. Trendyol/Hepsiburada anti-bot bloklar
- **Olasılık:** Yüksek (hackathon sırasında trafiğin artışıyla)
- **Etki:** Scout çalışmaz, demo kırılır
- **Önlem:**
  1. **Cache:** 200 ürünlük seed dataset commit edilmiş
  2. **User-agent rotation:** Playwright'ta 5 farklı UA
  3. **Rate limit:** Saniyede 1 istek max
  4. **Plan B:** Demo'da "cache mode" şeffaf bir badge ile (üretimde live)
- **Tetikleyici:** İlk istek 5 sn'de gelmezse cache'e fall-back.

### R3. Gemini API quota aşar
- **Olasılık:** Orta-Yüksek (4 ajan paralel, çok çağrı)
- **Etki:** Demo yarıda kalır
- **Önlem:**
  1. **İki API key:** Yedek anahtar `.env.backup`
  2. **Aggressive caching:** Aynı prompt → aynı cevap (Redis benzeri in-memory)
  3. **Model downgrade:** Pro çağrıları başarısızsa Flash'a düş
  4. **Demo öncesi quota check:** Sabah kullanım %'sini kontrol et

### R4. Negotiator pazarlığı bozar (mantıksız mesaj)
- **Olasılık:** Orta
- **Etki:** Demo'nun "wow" anı ölür
- **Önlem:**
  1. **Seller agent kalibrasyonu:** Cömert kişilik, max %20 indirim verir
  2. **Negotiator stratejisi:** İlk teklif %25, hedef %15
  3. **Guard rails:** Mesaj çıktısı boş/garip ise rerun
  4. **Altın senaryo cache:** Demo'da cached pazarlık transcript'i hazır
- **Tetikleyici:** 5 turdan uzun veya hostil yanıt → kapat, cache'e dön

---

## P1 — Kalite Düşürücü Riskler

### R5. Frontend stream gecikir (jittery UI)
- **Olasılık:** Orta
- **Etki:** "Production-grade" hissi gider
- **Önlem:** WebSocket batch (50ms aralıkla), animasyon throttling

### R6. Sahte yorum tespiti yanlış pozitif
- **Olasılık:** Orta
- **Etki:** "AI çok agresif" eleştirisi
- **Önlem:** Konfidans eşiği yüksek tut (%70+). Şeffaf gerekçe göster: "Bu yorumu işaretledim çünkü..."

### R7. UI cilası eksik kalır
- **Olasılık:** Yüksek (son aşamada zaman daralır)
- **Etki:** "Hackathon işi" hissi
- **Önlem:** UI'ı **Faz 1'den itibaren cilalı tut**, sonradan eklemek yerine başta polish.

### R8. Tek bir kişide bug
- **Olasılık:** Yüksek
- **Etki:** Tek kişi blocker → tüm ekip bekler
- **Önlem:** Daily 30 dk pair programming + rotation. Backend bilgisini en az 2 kişi taşısın.

---

## P2 — Yan Etki Riskleri

### R9. Etik soru (jüri pazarlığı etik bulmaz)
- **Olasılık:** Düşük-Orta
- **Etki:** Pitch'te savunmacı pozisyon
- **Önlem:** [07-JURY-PITCH.md](07-JURY-PITCH.md) Q&A bölümünde net cevap. **"Şeffaflık prensibi: mesaj başında 'AI asistan'."**

### R10. ToS / yasal soru
- **Olasılık:** Düşük
- **Etki:** Pitch zayıflar
- **Önlem:** Public arama sayfası okuma + rate limit = tüketici lehine standart pratik. Üretimde partnership.

### R11. Eleştiri: "Aynısını ChatGPT plugin yapar"
- **Olasılık:** Orta
- **Etki:** Yenilikçilik puanı düşer
- **Önlem:** Pitch'te farklılaşma açık: **multi-agent + Türk pazaryeri spesifik + pazarlık katmanı**. Hiçbir genel chatbot bu üçünü yapmıyor.

### R12. "Demo skripti ezberlenmiş, gerçek değil" şüphesi
- **Olasılık:** Orta
- **Etki:** Güvenilirlik düşer
- **Önlem:** **Jüriye sor:** "Siz de bir sorgu girin." Yedek 2-3 sorguda live mod çalışıyor. Bu güveni patlatır.

---

## Risk Haritası (Olasılık × Etki)

```
           Etki
            ▲
  Felaket   │ R1 R2 R3 R4
            │
  Yüksek    │ R7 R8       R6
            │
  Orta      │ R11 R12     R5
            │              R9
  Düşük     │              R10
            └─────────────────▶
              Düşük  Orta  Yüksek
                       Olasılık
```

Önceliklendirme: **R1, R2, R3, R4 her gün başı kontrol edilecek**.

---

## "Bugün Bir Şey Çökerse" Çek Listesi

Her sabah 5 dk:
- [ ] Gemini API: 1 ping at, response time?
- [ ] Trendyol scraper: 1 sorgu çek, ürün geldi mi?
- [ ] Cache modu: aktif altın senaryo açılıyor mu?
- [ ] WebSocket: frontend bağlanıyor mu?
- [ ] Yedek video: hala oynatılıyor mu?

5 maddenin biri kırmızı ise → o gün başka iş öncesi onu çöz.

---

## Plan B Hiyerarşisi

```
1. Live mode (tercih edilen)
   ↓ (fail)
2. Cache mode (önceden çekilmiş veri, gerçekmiş gibi akar)
   ↓ (fail)
3. Pre-recorded screen video
   ↓ (fail)
4. Manuel slayt anlatımı (vizyon + mimari)
   ↓ (fail)
5. Sözlü pitch + soru-cevap
```

Her seviyenin nasıl tetikleneceği [06-DEMO-SCRIPT.md](06-DEMO-SCRIPT.md)'de.
