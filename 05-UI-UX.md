# 05 — UI / UX Tasarımı

## Tasarım Prensibi

> "Bir mühendis çatlağıyla yapay zekanın canlı düşündüğünü göster, sonra bir sihirbazın final hilesini yap."

3 sahnede demo: **(1) sorgu**, **(2) çoklu-ajan tiyatrosu**, **(3) karar kartı**.

---

## Sahne 1 — Sorgu Ekranı

Tek sayfa, koyu tema, ortada büyük input.

```
┌──────────────────────────────────────────────────────────┐
│                                                          │
│              AgentMarket                                  │
│         AI ajansınız sizin için pazarlık eder            │
│                                                          │
│   ┌────────────────────────────────────────────────┐    │
│   │  300 TL altı gürültü engelleyici kulaklık...   │    │
│   └────────────────────────────────────────────────┘    │
│                                                          │
│        [ Ajansı Çalıştır → ]                             │
│                                                          │
│   Öneriler:                                              │
│   • Anneme doğum günü hediyesi 500 TL altı               │
│   • Oyuncular için mekanik klavye 1000 TL altı           │
│   • Üniversiteli için sırt çantası                       │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

- **Font:** Geist veya Inter, ferah typography
- **Renk:** Dark slate background, accent: yeşil (BTK Hackathon temasına nod — slaytta yeşil var)
- **Mikro-detay:** Input focus'unda yumuşak glow, "Çalıştır" butonunda hover'da hafif ölçek

---

## Sahne 2 — Çoklu-Ajan Tiyatrosu (en kritik ekran)

**"Hava Trafik Kontrolü"** metaforu. 4 ajan kartı bir grid'de, her biri kendi düşünce akışını canlı gösteriyor.

```
┌──────────────────────────────────────────────────────────────┐
│  [Sorgu özet bar — soruyu, parsed bütçeyi gösterir]          │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────┐    ┌──────────────────────┐       │
│  │ 🛒 SCOUT             │    │ 🔍 CRITIC            │       │
│  │ ●●●● Aktif           │    │ ●●○○ Bekliyor       │       │
│  │                      │    │                      │       │
│  │ ⊙ Trendyol'da arıyor │    │ ░ Scout'u bekliyor   │       │
│  │ ⊙ 47 sonuç bulundu   │    │                      │       │
│  │ ⊙ Filtreleniyor...   │    │                      │       │
│  │ ⊙ 23 aday kaldı      │    │                      │       │
│  │ → 8 finalist seçildi │    │                      │       │
│  └──────────────────────┘    └──────────────────────┘       │
│                                                              │
│  ┌──────────────────────┐    ┌──────────────────────┐       │
│  │ 🛡 VERIFIER          │    │ 🤝 NEGOTIATOR        │       │
│  │ ●●○○ Bekliyor        │    │ ○○○○ Pasif           │       │
│  │                      │    │                      │       │
│  └──────────────────────┘    └──────────────────────┘       │
│                                                              │
│  [İlerleme: ████░░░░░ %42]                                   │
└──────────────────────────────────────────────────────────────┘
```

**Davranış:**
- Her satır, WebSocket event'i gelince **typewriter** animasyonuyla yazılır (Framer Motion).
- Ajan durumu: `Pasif | Bekliyor | Aktif | Tamam` — sol üstte 4 küçük nokta renkle değişir.
- Aktif ajanın kartında ince bir gradient pulse.
- Tool call satırları farklı renk (mavi: `→`, sarı: `⚠`, yeşil: `✓`).

**Negotiator aktif olunca:**

Negotiator kartı **ekrana büyür** (modal değil, in-place expand) ve içinde **gerçek bir chat penceresi** açılır:

```
┌──────────────────────────────────────────────────────┐
│ 🤝 NEGOTIATOR ──── Pazarlık başlıyor                 │
│                                                       │
│ ┌─────────────────────────────────────────┐          │
│ │ 👤 Negotiator                           │          │
│ │ Merhaba, ürününüzle ilgileniyorum...    │ 12:04   │
│ └─────────────────────────────────────────┘          │
│                                                       │
│        ┌─────────────────────────────────────────┐   │
│        │ 🏪 Satıcı                              │   │
│ 12:04  │ Hoş geldiniz! Hangi ürünü...           │   │
│        └─────────────────────────────────────────┘   │
│                                                       │
│ ┌─────────────────────────────────────────┐          │
│ │ 👤 Negotiator                           │          │
│ │ %20 indirim mümkün mü?                  │ 12:05   │
│ └─────────────────────────────────────────┘          │
│                                                       │
│ [yazıyor...]                                          │
└──────────────────────────────────────────────────────┘
```

Mesajlar **streamlenir** (kelime kelime gelir, Gemini stream API). Bu görüntü demo'nun şah damarı.

---

## Sahne 3 — Karar Kartı (Reveal)

Negotiator anlaşmayı kapatınca tüm sahne **fade out**, ortada büyük bir karar kartı **scale-up** animasyonuyla belirir.

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│           ⭐ Önerim                                          │
│                                                              │
│   ┌─────┐   Sony WH-XB910N Muadili                          │
│   │ IMG │   Wireless ANC Kulaklık                            │
│   └─────┘                                                    │
│                                                              │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━           │
│                                                              │
│   299 TL  →  252 TL    Tasarruf: 47 TL  (-%16)              │
│                                                              │
│   Güven skoru:    ████████████████░░░░  84/100              │
│   Gerçek yorum:   %82                                        │
│   Marka otantik:  %92                                        │
│   Kargo ücretsiz: ✓ (pazarlıkla kazanıldı)                  │
│                                                              │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━           │
│                                                              │
│   "Bütçenle eşleşen 47 üründen bunu seçtim. Yorumların       │
│   %82'si gerçek, ses kalitesinden çok memnunlar. Konfor      │
│   konusunda azınlık eleştiri var ama bu fiyata makul.        │
│   Satıcıyla pazarlık sonucu kargo ücreti kalktı."            │
│                                                              │
│   [ Satıcıya Git → ]   [ Alternatifleri Gör ]                │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Animasyon:**
- Tasarruf rakamı **count-up** animasyonu (0'dan 47'ye)
- Güven skoru barı sağa doğru dolar
- Açıklama paragrafı stream'lenir

---

## Mikro-Etkileşimler (Cilanın sırrı)

| Yer | Detay |
|---|---|
| Sorgu odağında | Subtle ışıma + placeholder fade-cycle |
| Ajan kartı aktif | İnce gradient pulse (1.5s loop) |
| Tool call satırı | Sola kayan ince oklu marker |
| Pazarlık mesajı | Yazıcı (typewriter) + tipping bubble |
| Tasarruf reveal | Spring-bouncy scale-up + count-up |
| Hover'lar | 200ms ease-out scale 1.02 |

## Erişilebilirlik / Detay

- Klavye: Tab ile ajan kartları arası geçiş, Enter ile detay görmek
- Renkler WCAG AA kontrast
- Mobile: 4 ajan kartı dikey stack, pazarlık tam ekran
- Yükleme durumu: skeleton (Tailwind shimmer)

---

## Mockup Üretim Stratejisi

Tasarım maketi için **v0.dev** veya **claude.ai artifacts** ile hızlı prototip → onaylayınca shadcn componentlerine çevir. Hackathondan önce 1 saat mockup, 1 saat onay.

## "Cila" Önceliği

Süre kısalırsa düşeceğimiz tek bir şey: **Sahne 1 minimal kalabilir**. Sahne 2 ve 3 her halükarda parlak olmalı — jüri en çok orayı görecek.
