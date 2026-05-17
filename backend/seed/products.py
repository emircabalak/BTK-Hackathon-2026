"""Sample products for testing and demo cache.

Structure:
- 4 categories: kulaklik, olta, klavye, anne_hediye
- Each category has 4-5 products with varying price/quality/seller profiles
- Some products are seeded with suspicious-looking review patterns so that
  Critic's fake-review detector has signal to work with.

In production these come from Scout's live scrape.
"""

from __future__ import annotations

from app.models import Product, Review, Seller


def _r(items: list[tuple[str, int, str]], *, verified=True) -> list[Review]:
    return [
        Review(author=name, rating=r, text=txt, verified_purchase=verified)
        for name, r, txt in items
    ]


# Suspicious review templates — short, all 5-star, generic praise. Critic should
# flag these as likely fake/promoted.
def _suspicious_pattern(authors: list[str]) -> list[Review]:
    canned = "Harika ürün, çok memnun kaldım. Tavsiye ederim."
    return [
        Review(author=a, rating=5, text=canned, verified_purchase=False) for a in authors
    ]


# ════════════════════════════════════════════════════════════════
# KULAKLIK (Bluetooth/ANC kulaklık, çoğunlukla 250-450 TL aralığı)
# ════════════════════════════════════════════════════════════════

KULAKLIK_SONY_MUADIL = Product(
    product_id="kulaklik_001",
    title="Wireless ANC Kulaklık (Sony WH-XB910N Muadili)",
    price=299.0,
    marketplace="seed",
    description="Aktif gürültü engelleme, 30 saate kadar pil, Bluetooth 5.2.",
    category="kulaklik",
    tags=["bluetooth", "anc", "kablosuz", "gurultu_engelleme"],
    rating=4.4,
    review_count=823,
    seller=Seller(
        seller_id="seller_alpha",
        name="AlphaTeknoloji",
        rating=4.7,
        total_sales=2400,
        response_style="kibar, hızlı yanıt",
    ),
    reviews=_r([
        ("Ahmet K.", 5, "Ses kalitesi fiyatına göre çok iyi, ANC harika."),
        ("Mehmet T.", 4, "Konfor biraz kıymadan sonra azalıyor ama genel iyi."),
        ("Zeynep Y.", 5, "Pil ömrü uzun, kargo hızlıydı."),
        ("Burak A.", 3, "Mikrofon zayıf, görüşmelerde sıkıntı."),
        ("Ayşe D.", 5, "Bu fiyata muhteşem, herkese öneririm."),
    ]),
)

KULAKLIK_PREMIUM_JBL = Product(
    product_id="kulaklik_002",
    title="JBL Tune 770NC ANC Kulaklık",
    price=449.0,
    marketplace="seed",
    description="44 saat pil, adaptive ANC, JBL imzalı bas, hızlı şarj.",
    category="kulaklik",
    tags=["bluetooth", "anc", "kablosuz", "premium_marka"],
    rating=4.7,
    review_count=2150,
    seller=Seller(
        seller_id="seller_jblstore",
        name="JBLOfficialStore",
        rating=4.8,
        total_sales=125000,
        response_style="standart kurumsal cevap",
    ),
    reviews=_r([
        ("Mert C.", 5, "Orijinal JBL, satıcı güvenilir, bas mükemmel."),
        ("Selin Ö.", 5, "44 saat gerçekten dayanıyor, ANC etkili."),
        ("Tuğçe G.", 4, "Kulak yastıkları biraz sıkı, alışınca rahat."),
        ("Cem N.", 5, "JBL marka değeri zaten ortada, fiyatı uygun."),
    ]),
)

KULAKLIK_NONAME_UCUZ = Product(
    product_id="kulaklik_003",
    title="Super Bass ANC Wireless Headphone Pro Max+",  # sus title style
    price=159.0,
    marketplace="seed",
    description="ANC, bluetooth, dahili mikrofon, 20 saat pil. (Marka belirtilmemiş.)",
    category="kulaklik",
    tags=["bluetooth", "anc", "ucuz"],
    rating=4.9,  # şüpheli yüksek
    review_count=87,  # düşük sayı + yüksek puan = red flag
    seller=Seller(
        seller_id="seller_xshop",
        name="XShopGlobal",
        rating=4.3,
        total_sales=380,
        response_style="otomatik cevap",
    ),
    reviews=(
        _suspicious_pattern(["User123", "Buyer88", "Alıcı34", "Test99"])
        + _r([
            ("Hakan T.", 2, "Resimde gördüğümden farklı geldi, kalite kötü."),
            ("Esra B.", 3, "Bluetooth bağlantısı sürekli kopuyor."),
        ])
    ),
)

KULAKLIK_OYUNCU = Product(
    product_id="kulaklik_004",
    title="Gaming RGB Kulaklık 7.1 Surround",
    price=389.0,
    marketplace="seed",
    description="7.1 surround ses, RGB aydınlatma, esnek mikrofon, PC/PS5 uyumlu.",
    category="kulaklik",
    tags=["oyuncu", "rgb", "kablolu", "mikrofon"],
    rating=4.5,
    review_count=614,
    seller=Seller(
        seller_id="seller_gamingstore",
        name="GamingStoreTR",
        rating=4.6,
        total_sales=68000,
        response_style="standart, kalıp cevaplar",
    ),
    reviews=_r([
        ("Emre K.", 5, "Oyunda yön tayini çok iyi, mikrofon temiz."),
        ("Selim D.", 4, "RGB cazip, kabloyu kısa buldum."),
        ("Kerem Y.", 5, "Surround etkisi gerçekçi."),
        ("Mert A.", 3, "PS5'te driver sorunu yaşadım, PC'de sorun yok."),
    ]),
)


# ════════════════════════════════════════════════════════════════
# OLTA (Balıkçı seti, hediye odaklı, 1500-2200 TL aralığı)
# ════════════════════════════════════════════════════════════════

OLTA_PREMIUM = Product(
    product_id="olta_001",
    title="Kaliteli Olta Seti (Premium Balıkçı Paketi)",
    price=1899.0,
    marketplace="seed",
    description="Karbon kamış 2.4m, makara, 50m misina, çantalı, 12 farklı sahte yem.",
    category="olta",
    tags=["balikci", "hediye", "tam_paket", "tasinabilir"],
    rating=4.6,
    review_count=341,
    seller=Seller(
        seller_id="seller_balik",
        name="BalikDunyasi",
        rating=4.8,
        total_sales=890,
        response_style="samimi, balıkçı diline hakim",
    ),
    reviews=_r([
        ("Hasan A.", 5, "Babam çok beğendi, hediye için ideal."),
        ("Cem K.", 5, "Kalite çok iyi, taşıma çantası şık."),
        ("Onur S.", 4, "Yemler biraz hafif ama makara çok iyi."),
        ("İbrahim T.", 5, "Bu fiyata bulunmaz, kargo da hızlıydı."),
    ]),
)

OLTA_EKONOMIK = Product(
    product_id="olta_002",
    title="Başlangıç Olta Seti — Yeni Başlayanlara",
    price=1299.0,
    marketplace="seed",
    description="2m fiberglass kamış, basit makara, 30m misina, 6 yem, kullanım kılavuzu.",
    category="olta",
    tags=["balikci", "ekonomik", "yeni_baslayan"],
    rating=4.3,
    review_count=156,
    seller=Seller(
        seller_id="seller_basicfishing",
        name="BasicFishingTR",
        rating=4.4,
        total_sales=2100,
        response_style="kısa, bilgilendirici",
    ),
    reviews=_r([
        ("Murat E.", 4, "Yeni başlayan için ideal, kâfi gelir."),
        ("Bahadır K.", 3, "Kamış hafif, deniz balığı için zor olur."),
        ("Sinan T.", 5, "Fiyatına göre çok iyi, çocuğum için aldım."),
    ]),
)

OLTA_PROFESYONEL = Product(
    product_id="olta_003",
    title="Profesyonel Karbon Olta — Daiwa Muadili Premium Set",
    price=2199.0,
    marketplace="seed",
    description="Yüksek karbon 2.7m, paslanmaz makara, profesyonel hediye kutusu, 24 sahte yem.",
    category="olta",
    tags=["balikci", "profesyonel", "premium", "hediye_kutulu"],
    rating=4.8,
    review_count=412,
    seller=Seller(
        seller_id="seller_proFishing",
        name="ProFishingTR",
        rating=4.9,
        total_sales=1450,
        response_style="profesyonel, hızlı",
    ),
    reviews=_r([
        ("Selçuk B.", 5, "Karbon kamış inanılmaz hafif, balık hissi keskin."),
        ("Adnan H.", 5, "Hediye kutusu profesyonel, baba için aldım çok beğendi."),
        ("Tahir M.", 4, "Fiyat biraz yüksek ama kalite ortada."),
        ("Erdal C.", 5, "Profesyonel kullanım için ideal."),
    ]),
)

OLTA_SUPHELI = Product(
    product_id="olta_004",
    title="ULTRA PRO Olta Seti Süper Kaliteli BÜYÜK İndirim 7 Parça",
    price=1599.0,
    marketplace="seed",
    description="Kamış, makara, misina, yem ve aksesuarlar.",
    category="olta",
    tags=["balikci"],
    rating=5.0,  # 5.0 + few reviews = suspicious
    review_count=43,
    seller=Seller(
        seller_id="seller_xshop",
        name="XShopGlobal",
        rating=4.3,
        total_sales=380,
        response_style="kalıp",
    ),
    reviews=(
        _suspicious_pattern(["Müşteri1", "Müşteri2", "Kullanıcı_A", "Kullanıcı_B"])
        + _r([
            ("Rıza B.", 2, "Karton kutu hasarlı geldi, yem eksikti."),
        ])
    ),
)


# ════════════════════════════════════════════════════════════════
# KLAVYE (Mekanik klavye, 700-1200 TL aralığı)
# ════════════════════════════════════════════════════════════════

KLAVYE_OUTEMU = Product(
    product_id="klavye_001",
    title="RGB Mekanik Gaming Klavye (Outemu Mavi Switch)",
    price=849.0,
    marketplace="seed",
    description="Türkçe Q, RGB aydınlatma, mekanik mavi switch, programlanabilir tuşlar.",
    category="klavye",
    tags=["mekanik", "rgb", "oyuncu", "outemu_mavi"],
    rating=4.5,
    review_count=1240,
    seller=Seller(
        seller_id="seller_gamingstore",
        name="GamingStoreTR",
        rating=4.6,
        total_sales=68000,
        response_style="standart, kalıp cevaplar",
    ),
    reviews=_r([
        ("Emre K.", 5, "Tuş hissi muazzam, RGB ışıklar parlak."),
        ("Selim D.", 4, "Sesli ama mavi switch zaten sesli olur, normal."),
        ("Kerem Y.", 5, "Bu fiyata mekanik klavye süper."),
        ("Mert A.", 3, "Yazılım biraz kötü, ışıklandırma ayarı zor."),
    ]),
)

KLAVYE_PREMIUM = Product(
    product_id="klavye_002",
    title="Logitech G413 SE TKL Mekanik Klavye",
    price=1199.0,
    marketplace="seed",
    description="Tactile mekanik switchler, alüminyum gövde, beyaz aydınlatma, TKL.",
    category="klavye",
    tags=["mekanik", "tkl", "logitech", "premium"],
    rating=4.8,
    review_count=890,
    seller=Seller(
        seller_id="seller_logiofficial",
        name="LogitechResmi",
        rating=4.9,
        total_sales=42000,
        response_style="kurumsal",
    ),
    reviews=_r([
        ("Berk T.", 5, "Logitech kalitesi belli, tactile his harika."),
        ("Furkan A.", 5, "Yazım için ideal, aydınlatma yumuşak."),
        ("Damla K.", 4, "TKL formatı masada yer açıyor, alıştım."),
    ]),
)

KLAVYE_KIRMIZI = Product(
    product_id="klavye_003",
    title="Cherry MX Red Switch Mekanik Klavye",
    price=1099.0,
    marketplace="seed",
    description="Cherry MX Red switchler, çift renkli ABS keycap, kompakt 75% layout.",
    category="klavye",
    tags=["mekanik", "cherry_mx_red", "75_percent"],
    rating=4.7,
    review_count=523,
    seller=Seller(
        seller_id="seller_meckeyboard",
        name="MechKeyboardTR",
        rating=4.7,
        total_sales=3200,
        response_style="hızlı, ürün bilgisi yüksek",
    ),
    reviews=_r([
        ("Can D.", 5, "Cherry MX Red yazım için müthiş, sessiz."),
        ("Ozan B.", 4, "75% layout alışkanlık gerektiriyor, sonra çok iyi."),
        ("Kerem A.", 5, "Yıllardır kullandığım en iyi klavye."),
        ("Mehmet G.", 4, "Keycap kalitesi PBT olsa daha iyi olurdu."),
    ]),
)


# ════════════════════════════════════════════════════════════════
# ANNE HEDIYE (300-700 TL aralığı, butik ürünler)
# ════════════════════════════════════════════════════════════════

HEDIYE_NOTEBOOK = Product(
    product_id="hediye_001",
    title="Premium Deri Notebook + Kalem Set (Anne Hediyesi)",
    price=489.0,
    marketplace="seed",
    description="Hakiki deri kapak, A5, 200 sayfa, hediye kutulu, ahşap kalem.",
    category="anne_hediye",
    tags=["anne", "deri", "hediye_kutulu", "kirtasiye"],
    rating=4.7,
    review_count=212,
    seller=Seller(
        seller_id="seller_butikatelye",
        name="ButikAtelye",
        rating=4.9,
        total_sales=1100,
        response_style="kişisel, sıcak",
    ),
    reviews=_r([
        ("Selin K.", 5, "Anneme aldım, çok beğendi. Hediye paketi şık."),
        ("Deniz O.", 5, "Deri gerçek, kalitesi süper."),
        ("Yasemin T.", 4, "Kalem güzel ama yazımı biraz zor."),
        ("Ece A.", 5, "Bu fiyata bu kalite şaşırtıcı."),
    ]),
)

HEDIYE_TAKI = Product(
    product_id="hediye_002",
    title="925 Ayar Gümüş Anne Kalp Kolye — Kişiye Özel Yazılı",
    price=349.0,
    marketplace="seed",
    description="925 ayar gümüş, kişiye özel kazıma, hediye kutulu, sertifikalı.",
    category="anne_hediye",
    tags=["anne", "taki", "gumus", "kisiye_ozel", "hediye_kutulu"],
    rating=4.8,
    review_count=445,
    seller=Seller(
        seller_id="seller_gumusatolye",
        name="GümüşAtölye",
        rating=4.9,
        total_sales=3400,
        response_style="hızlı, profesyonel",
    ),
    reviews=_r([
        ("Burcu N.", 5, "Annemin doğumgününde verdim, ağladı."),
        ("Pelin K.", 5, "Yazı çok temiz, sertifika ile geldi."),
        ("Tugay A.", 4, "Kargo geç geldi ama ürün mükemmel."),
        ("Eda M.", 5, "Bu kalitede bu fiyata bulunmaz."),
    ]),
)

HEDIYE_CICEK = Product(
    product_id="hediye_003",
    title="Solmayan Gül Kutusu — Cam Fanus İçinde Hediye Kutusu",
    price=599.0,
    marketplace="seed",
    description="Gerçek gül, koruyucu işlemli, cam fanus, hediye kutusu, kart dahil.",
    category="anne_hediye",
    tags=["anne", "cicek", "solmayan", "hediye_kutulu", "premium"],
    rating=4.6,
    review_count=178,
    seller=Seller(
        seller_id="seller_florarte",
        name="FlorArte",
        rating=4.8,
        total_sales=620,
        response_style="şiirsel, sıcak",
    ),
    reviews=_r([
        ("Sevgi B.", 5, "Annem fanusu hâlâ vitrinde saklıyor."),
        ("Naz T.", 5, "Cam fanus sağlam, ambalaj harika."),
        ("Cansu E.", 4, "Renk fotoğraftan daha koyu çıktı ama güzel."),
    ]),
)

HEDIYE_PARFUM_SUPHELI = Product(
    product_id="hediye_004",
    title="LÜKS Anne Parfüm Hediye Seti %70 İNDİRİM Sınırlı Stok",
    price=329.0,
    marketplace="seed",
    description="Premium parfüm seti, 3 farklı koku, hediye kutusu.",
    category="anne_hediye",
    tags=["anne", "parfum", "hediye_seti"],
    rating=4.9,
    review_count=24,
    seller=Seller(
        seller_id="seller_xshop",
        name="XShopGlobal",
        rating=4.3,
        total_sales=380,
        response_style="kalıp",
    ),
    reviews=(
        _suspicious_pattern(["Anonim1", "Anonim2", "Müşteri_X", "Test_Y"])
    ),
)


# ════════════════════════════════════════════════════════════════
# Registry
# ════════════════════════════════════════════════════════════════

ALL_PRODUCTS: list[Product] = [
    KULAKLIK_SONY_MUADIL, KULAKLIK_PREMIUM_JBL, KULAKLIK_NONAME_UCUZ, KULAKLIK_OYUNCU,
    OLTA_PREMIUM, OLTA_EKONOMIK, OLTA_PROFESYONEL, OLTA_SUPHELI,
    KLAVYE_OUTEMU, KLAVYE_PREMIUM, KLAVYE_KIRMIZI,
    HEDIYE_NOTEBOOK, HEDIYE_TAKI, HEDIYE_CICEK, HEDIYE_PARFUM_SUPHELI,
]


# Back-compat shortcuts used by older test_negotiation.py
ALL_SEED_PRODUCTS: dict[str, Product] = {
    "kulaklik": KULAKLIK_SONY_MUADIL,
    "olta": OLTA_PREMIUM,
    "klavye": KLAVYE_OUTEMU,
    "anne_hediye": HEDIYE_NOTEBOOK,
}


def get_product(key: str) -> Product:
    if key not in ALL_SEED_PRODUCTS:
        keys = ", ".join(ALL_SEED_PRODUCTS.keys())
        raise KeyError(f"Bilinmeyen ürün anahtarı: {key!r}. Mevcut: {keys}")
    return ALL_SEED_PRODUCTS[key]


def products_in_category(category: str) -> list[Product]:
    return [p for p in ALL_PRODUCTS if p.category == category]


KNOWN_CATEGORIES: list[str] = sorted({p.category for p in ALL_PRODUCTS})
