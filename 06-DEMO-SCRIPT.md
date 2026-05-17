# 06 — Jüri Demo Script

**Hedef süre:** 3 dakika sunum + 1-2 dakika Q&A
**Hedef his:** "Hiç görmediğim bir şey gördüm."

---

## 3 Dakikalık Akış

### 0:00 — 0:20 — Sahne Açılışı (Problem)

> "Yılda Türkiye'de **150 milyar TL**'lik online alışveriş yapılıyor. Ama ortalama bir tüketici, bir ürün almadan önce ortalama 14 dakikasını yorum karıştırmaya, sahte yorumları ayıklamaya, fiyat karşılaştırmaya, satıcıyla mesajlaşmaya harcıyor. Çoğunlukla yine de yanılıyor, kötü ürün alıyor, ya da pazarlık şansını kaçırıyor."

> "Biz dedik ki — bunu sen yapma. **Bir AI ajansı çalıştır**."

**Görsel:** Logo + tagline. Bir slayt.

### 0:20 — 0:30 — Çözümü Tanıt

> "AgentMarket. **4 uzman AI ajanı**, sizin için arar, eler, doğrular ve pazarlık eder. Hadi canlı gösterelim."

**Görsel:** Sorgu ekranı açılır.

### 0:30 — 1:00 — Canlı Sorgu

Sorguya yazarsın (önceden ezberlenmiş **altın senaryo**):

> "Babam emekli oldu, hobisi balık tutmak. Ona 2000 TL altı kaliteli bir olta seti almak istiyorum."

> "Şimdi şuna bakın — 4 ajan paralel çalışıyor."

**Görsel:** 4 ajan kartı canlı doluyor. Sen anlatıyorsun:

> "Scout — Trendyol ve Hepsiburada'yı taradı, 67 ürün buldu, sizin için 8'e indirdi."

> "Critic — her finalist için yüzlerce yorumu okuyor. Şu an sahte yorum oranını çıkarıyor — bakın bu üründe %23 şüpheli yorum buldu, kırmızı bayrak."

> "Verifier — ürünün görselini Gemini Vision'a sokuyor. 'Bu fotoğraf stok foto', 'logo açıklamayla uyumsuz' gibi tespitler yapıyor."

### 1:00 — 1:50 — Pazarlık Sahnesi (Hook An)

Negotiator devreye girer. Kart büyür, chat penceresi açılır.

> "Şimdi en kritik kısım — Negotiator, **gerçekten satıcıya yazıyor**. İzleyin."

**Görsel:** Mesajlar canlı stream:
- "Merhaba, ürününüzle ilgileniyorum..."
- (Satıcı) "Hoş geldiniz..."
- "Aynı modeli rakip pazaryerinde 1750 TL'ye gördüm, fiyatınız 1899 TL — pazarlık şansımız var mı?"
- (Satıcı) "Size 1850 TL'ye verebilirim..."
- "Kargo ücretsiz olursa anlaşırız, eklerseniz hemen satın alıyorum."
- (Satıcı) "Tamam, kargo ücretsiz, 1850 TL."

> "**49 TL kazandık, üstüne kargo ücretsiz**."

**Anahtar an:** Burada jüriye dön, gülümse. "Hiçbir tuşa basmadım."

### 1:50 — 2:30 — Karar Kartı

Sahne kapanır, karar kartı belirir.

> "Sonuçta ne aldık? **Babanın oltası**, **84/100 güven skoru**, **49 TL tasarruf** ve **kargo bedava**. Bot 47 saniyede yaptı."

**Görsel:** Sayısal animasyonlar, açıklama metni akıyor.

### 2:30 — 3:00 — Teknik + Vizyon Kapanış

> "Arka planda: **LangGraph** ile orkestre edilmiş, **Gemini 2.5 Pro + Flash + Vision** modelleri ile çalışan 4 ajan. Slaytlarda istenen **A2A multi-agent** protokolüyle birbirleriyle konuşuyorlar."

> "Bu hackathonda yaptığımız sandbox. Production'da: marketplace partnership'leri ile gerçek pazarlık, browser extension, ve B2B 'satıcı tarafı' sürümü."

> "AgentMarket. AI ajansınız sizin için pazarlık eder. Teşekkürler."

---

## Q&A Hazırlığı

| Olası Soru | Cevap |
|---|---|
| Trendyol'da gerçekten pazarlık olur mu? | "Sandbox'taki seller agent gerçek satıcı verisiyle kalibre edildi. Üretim sürümünde Trendyol/Hepsiburada API partnership'leri veya browser extension üzerinden gerçek mesajlaşma kanalı kullanılacak." |
| Sahte yorum tespiti güvenilir mi? | "3 sinyalli: heuristik + embedding clustering + Gemini judgment. Kendi etiketli setimizde insan değerlendirmesiyle %78 uyum. Beta'da kullanıcı feedback'iyle iyileşecek." |
| Hız nasıl? | "Şu an 30-60 sn. Cache + paralel batching ile 15 sn'ye iniyor. Production'da çoğu çağrı pre-fetched olacak." |
| Maliyet? | "Sorgu başı yaklaşık $0.02 Gemini maliyeti. SaaS modelinde aylık 10 TL'ye 50 sorgu — geri kazanılan tasarrufla pozitif." |
| Etik? Bot pazarlığa girmesi? | "Şeffaflık prensibi: satıcıya 'AI asistanım adınıza yazıyor' notuyla başlıyor. Bir tüketici aracı olarak satıcıyla iletişim insan vekili sözleşmesi kapsamında." |
| Hangi pazaryerleri? | "Şu an Trendyol + Hepsiburada. N11, Çiçeksepeti, GittiGidiyor ve uluslararası (Amazon) sırada." |
| Neden 4 ajan, neden tek değil? | "Tek bir LLM'in cognitive load'u kötü olur. Specialization → her ajan kendi alanında üst düzey performans + paralel hız + ayrı debug edilebilirlik." |
| Verifier Vision olmadan da çalışır mı? | "Evet, metin tutarlılığıyla degrade çalışıyor; Vision premium katman." |
| Üretime alma planı? | "1) Browser extension MVP (1 ay), 2) Marketplace partner pilot (3 ay), 3) Mobil + B2B satıcı tarafı (6 ay)." |

---

## Yedek Planlar

### Plan B — İnternet/API Çökerse

- **Önceden cache'lenmiş 3 altın senaryo** (balık seti, kulaklık, anne hediyesi) tam transcript'le SQLite'da hazır.
- Demo sırasında "live" mod başarısız olursa: sessizce cache moda geç. Tooltip'te küçük bir "demo mode" işareti olsun ama dikkat çekmesin.

### Plan C — Backend Hiç Çalışmazsa

- **Pre-recorded screen video** (60sn) hazır. Sunum ekranını anında ona çevir.
- "Saniyenizi geri verelim, ekranı geçiyorum" deyip videoyu çal.

### Plan D — Laptop Çökerse

- Tüm proje **GitHub + Vercel deployment** üzerinde de duruyor.
- Yedek dizüstü veya jürinin laptopunda URL aç.

---

## Provası

**Hackathondan 24 saat önce:**
- 5 kez bütün demo'yu çek, süre tut.
- 3 farklı kişiye izlet, "ne anlamadım" feedback'i topla.
- Her plan B/C/D'yi de en az 1 kez test et.

**Hackathon günü, jüri öncesi:**
- 1 saat önce başka makinede son çalıştır.
- Şarj %100, internet test, ses test.

**Sunum aktarımı:**
- Tek bir kişi konuşur (en akıcı olan).
- Diğeri laptop başında, sorun olursa Plan B/C tetikler.

---

## Sunumcu için Mini Card (cep notu)

```
0:00 Problem (20 sn): 150 milyar TL, 14 dakika, kayıp
0:20 Çözüm tanıt (10 sn): 4 ajan
0:30 Sorguyu yaz (30 sn): "babam, balık, 2000 TL"
1:00 Pazarlık (50 sn): canlı chat - sus, izlet
1:50 Karar kartı (40 sn): rakamı göster
2:30 Vizyon (30 sn): LangGraph, A2A, Gemini, sandbox
GÜLÜMSE - DURAKSAMA - DEMO HALA AKIYOR DEĞİL
```
