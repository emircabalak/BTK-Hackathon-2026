// AgentMarket pitch deck generator — produces AgentMarket-Pitch.pptx
// Run: NODE_PATH=$(npm root -g) node build_pitch.js

const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const {
  FaSearch,
  FaSearchPlus,
  FaShieldAlt,
  FaHandshake,
  FaCrown,
  FaCheckCircle,
  FaShoppingCart,
  FaBolt,
  FaLayerGroup,
  FaCode,
  FaCloud,
  FaLock,
} = require("react-icons/fa");

// ───────────────────────────────────────────────────────────────
// Palette + design tokens
// ───────────────────────────────────────────────────────────────

const BG = "060814";          // dark navy
const BG_CARD = "0F1424";     // card background
const BG_CARD_HI = "131A2E";  // slightly brighter card
const EMERALD = "34D399";
const EMERALD_DEEP = "10B981";
const CYAN = "38BDF8";
const AMBER = "FBBF24";
const ROSE = "F87171";
const VIOLET = "A78BFA";
const TEXT = "E6EAF2";
const TEXT_MUTED = "94A3B8";
const TEXT_DIM = "64748B";
const BORDER = "1E293B";

const HEADER_FONT = "Calibri";
const BODY_FONT = "Calibri";

// ───────────────────────────────────────────────────────────────
// Icon helper
// ───────────────────────────────────────────────────────────────

function renderIconSvg(IconComponent, color, size = 256) {
  return ReactDOMServer.renderToStaticMarkup(
    React.createElement(IconComponent, { color, size: String(size) }),
  );
}

async function icon(IconComponent, hex) {
  const svg = renderIconSvg(IconComponent, "#" + hex, 256);
  const pngBuffer = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + pngBuffer.toString("base64");
}

// ───────────────────────────────────────────────────────────────
// Reusable helpers
// ───────────────────────────────────────────────────────────────

function fillCard(slide, pres, { x, y, w, h, fill = BG_CARD, accent = null, accentColor = EMERALD }) {
  slide.addShape(pres.shapes.RECTANGLE, {
    x, y, w, h,
    fill: { color: fill },
    line: { color: BORDER, width: 0.75 },
  });
  if (accent === "top") {
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w, h: 0.04,
      fill: { color: accentColor },
      line: { color: accentColor, width: 0 },
    });
  } else if (accent === "left") {
    slide.addShape(pres.shapes.RECTANGLE, {
      x, y, w: 0.06, h,
      fill: { color: accentColor },
      line: { color: accentColor, width: 0 },
    });
  }
}

function chip(slide, pres, { x, y, w = 3.3, text, color = EMERALD }) {
  slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
    x, y, w, h: 0.36,
    rectRadius: 0.18,
    fill: { color: BG_CARD_HI },
    line: { color: color, width: 0.75 },
  });
  slide.addText(text, {
    x, y, w, h: 0.36,
    fontFace: BODY_FONT,
    fontSize: 10,
    color: color,
    bold: true,
    align: "center",
    valign: "middle",
    charSpacing: 4,
    margin: 0,
  });
}

function pageNum(slide, n, total) {
  slide.addText(`${String(n).padStart(2, "0")} / ${total}`, {
    x: 12.5, y: 7.05, w: 0.7, h: 0.3,
    fontFace: BODY_FONT,
    fontSize: 9,
    color: TEXT_DIM,
    align: "right",
    valign: "middle",
  });
  slide.addText("AGENTMARKET", {
    x: 0.6, y: 7.05, w: 2, h: 0.3,
    fontFace: BODY_FONT,
    fontSize: 9,
    color: TEXT_DIM,
    charSpacing: 4,
    bold: true,
    valign: "middle",
  });
}

// ───────────────────────────────────────────────────────────────
// Build presentation
// ───────────────────────────────────────────────────────────────

async function main() {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13.3" × 7.5"
  pres.author = "AgentMarket Team";
  pres.title = "AgentMarket — Pitch Deck";
  pres.company = "BTK Hackathon 2026";

  // Pre-render icons we'll use
  const I = {
    scout: await icon(FaShoppingCart, EMERALD),
    critic: await icon(FaSearchPlus, AMBER),
    verifier: await icon(FaShieldAlt, CYAN),
    negotiator: await icon(FaHandshake, EMERALD_DEEP),
    crown: await icon(FaCrown, EMERALD),
    check: await icon(FaCheckCircle, EMERALD),
    bolt: await icon(FaBolt, AMBER),
    layers: await icon(FaLayerGroup, VIOLET),
    code: await icon(FaCode, CYAN),
    cloud: await icon(FaCloud, EMERALD),
    lock: await icon(FaLock, ROSE),
    search: await icon(FaSearch, CYAN),
  };

  const TOTAL = 6;

  // ════════════════════════════════════════════════════════════
  // Slide 1 — TITLE
  // ════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: BG };

    // Subtle accent shape (left side bar)
    s.addShape(pres.shapes.RECTANGLE, {
      x: 0, y: 0, w: 0.18, h: 7.5,
      fill: { color: EMERALD },
      line: { color: EMERALD, width: 0 },
    });

    // Top chip
    chip(s, pres, {
      x: 0.9, y: 0.9, w: 6.7,
      text: "BTK HACKATHON 2026  ·  ÇOKLU AJAN ALIŞVERİŞ ASİSTANI",
    });

    // Massive title
    s.addText("AgentMarket", {
      x: 0.85, y: 2.0, w: 11.5, h: 1.7,
      fontFace: HEADER_FONT,
      fontSize: 96,
      bold: true,
      color: EMERALD,
      align: "left",
      valign: "middle",
      margin: 0,
    });

    // Tagline
    s.addText([
      { text: "AI ajansınız sizin için arar, eler, doğrular ve ", options: { color: TEXT } },
      { text: "pazarlık eder", options: { color: EMERALD, italic: true } },
      { text: ".", options: { color: TEXT } },
    ], {
      x: 0.9, y: 3.95, w: 11.5, h: 0.7,
      fontFace: BODY_FONT,
      fontSize: 26,
      align: "left",
      valign: "middle",
      margin: 0,
    });

    // Sub-stat row
    s.addImage({ data: I.bolt, x: 0.9, y: 5.0, w: 0.22, h: 0.22 });
    s.addText("30 saniyede karar  ·  4 ajan paralel  ·  Gerçek pazarlık", {
      x: 1.2, y: 4.95, w: 8, h: 0.4,
      fontFace: BODY_FONT,
      fontSize: 14,
      color: TEXT_MUTED,
      valign: "middle",
    });

    // Bottom: presenter info
    s.addText("Sunan: AgentMarket Takımı  ·  agentmarket.local", {
      x: 0.9, y: 6.7, w: 8, h: 0.4,
      fontFace: BODY_FONT,
      fontSize: 11,
      color: TEXT_DIM,
      valign: "middle",
    });

    pageNum(s, 1, TOTAL);
  }

  // ════════════════════════════════════════════════════════════
  // Slide 2 — PROBLEM
  // ════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: BG };

    // Section header
    chip(s, pres, { x: 0.6, y: 0.5, w: 1.4, text: "PROBLEM", color: ROSE });
    s.addText("Online alışveriş, kullanıcıyı yoruyor", {
      x: 0.6, y: 1.0, w: 12, h: 0.7,
      fontFace: HEADER_FONT,
      fontSize: 32,
      bold: true,
      color: TEXT,
      valign: "middle",
    });

    // Big stats row
    const stats = [
      { num: "150B TL", unit: "", label: "Türkiye e-ticaret hacmi 2025", color: EMERALD },
      { num: "14", unit: "dk", label: "ortalama sorgu başına araştırma", color: CYAN },
      { num: "%18", unit: "", label: "sahte/şüpheli yorum oranı (sektör tahmini)", color: AMBER },
    ];
    stats.forEach((st, i) => {
      const x = 0.6 + i * 4.1;
      const y = 2.0;
      const w = 3.9;
      const h = 2.1;
      fillCard(s, pres, { x, y, w, h, accent: "top", accentColor: st.color });

      s.addText([
        { text: st.num, options: { color: st.color, fontSize: 56, bold: true } },
        { text: st.unit ? "  " + st.unit : "", options: { color: TEXT_MUTED, fontSize: 22, bold: false } },
      ], {
        x: x + 0.3, y: y + 0.35, w: w - 0.6, h: 1.1,
        fontFace: HEADER_FONT,
        align: "left",
        valign: "middle",
        margin: 0,
      });

      s.addText(st.label, {
        x: x + 0.3, y: y + 1.4, w: w - 0.6, h: 0.6,
        fontFace: BODY_FONT,
        fontSize: 12,
        color: TEXT_MUTED,
        align: "left",
        valign: "top",
      });
    });

    // Story card
    const sy = 4.6;
    fillCard(s, pres, { x: 0.6, y: sy, w: 12.1, h: 2.0, accent: "left", accentColor: ROSE });

    s.addText("BİR KULLANICI HİKAYESİ", {
      x: 0.85, y: sy + 0.2, w: 11.6, h: 0.3,
      fontFace: BODY_FONT,
      fontSize: 10,
      color: TEXT_DIM,
      charSpacing: 4,
      bold: true,
    });

    s.addText([
      { text: "Ali", options: { color: EMERALD, bold: true } },
      { text: ", balık tutmak isteyen babasına olta seti almak istiyor. Trendyol'da 200 sonuç çıkıyor — yarısı çakma görünüyor, yorumların yarısı şüpheli. ", options: { color: TEXT } },
      { text: "40 dakika sonra hala karar veremedi. ", options: { color: TEXT } },
      { text: "Sonunda yine yanlış aldı.", options: { color: ROSE, italic: true } },
    ], {
      x: 0.85, y: sy + 0.55, w: 11.6, h: 1.3,
      fontFace: BODY_FONT,
      fontSize: 16,
      align: "left",
      valign: "top",
      paraSpaceAfter: 4,
    });

    pageNum(s, 2, TOTAL);
  }

  // ════════════════════════════════════════════════════════════
  // Slide 3 — SOLUTION (pipeline)
  // ════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: BG };

    chip(s, pres, { x: 0.6, y: 0.5, w: 1.4, text: "ÇÖZÜM", color: EMERALD });
    s.addText("4 uzman ajan — paralel, otonom", {
      x: 0.6, y: 1.0, w: 12, h: 0.7,
      fontFace: HEADER_FONT,
      fontSize: 32,
      bold: true,
      color: TEXT,
      valign: "middle",
    });

    // Pipeline diagram — 4 agent cards + result
    const agents = [
      { icon: I.scout, label: "SCOUT", verb: "Tara", color: EMERALD,
        desc: "Pazaryerlerini\ntara, finalistleri\nseç" },
      { icon: I.critic, label: "CRITIC", verb: "Ele", color: AMBER,
        desc: "Yorumları analiz\net, sahte olanları\nele" },
      { icon: I.verifier, label: "VERIFIER", verb: "Doğrula", color: CYAN,
        desc: "Marka & otantiklik\nGemini Vision ile\ndenetle" },
      { icon: I.negotiator, label: "NEGOTIATOR", verb: "Pazarlık", color: EMERALD_DEEP,
        desc: "Satıcıyla canlı\npazarlık yap, indirim\nve ekstra al" },
    ];

    const py = 2.1;
    const ph = 3.0;
    const cardW = 2.45;
    const gap = 0.22;
    const startX = 0.6;

    agents.forEach((a, i) => {
      const x = startX + i * (cardW + gap);
      fillCard(s, pres, { x, y: py, w: cardW, h: ph, accent: "top", accentColor: a.color });

      // Icon circle
      s.addShape(pres.shapes.OVAL, {
        x: x + cardW / 2 - 0.4, y: py + 0.35, w: 0.8, h: 0.8,
        fill: { color: BG_CARD_HI },
        line: { color: a.color, width: 1.25 },
      });
      s.addImage({ data: a.icon, x: x + cardW / 2 - 0.25, y: py + 0.5, w: 0.5, h: 0.5 });

      // Label
      s.addText(a.label, {
        x, y: py + 1.3, w: cardW, h: 0.4,
        fontFace: HEADER_FONT,
        fontSize: 14,
        bold: true,
        color: a.color,
        align: "center",
        charSpacing: 4,
        valign: "middle",
      });

      // Verb
      s.addText(a.verb, {
        x, y: py + 1.7, w: cardW, h: 0.4,
        fontFace: HEADER_FONT,
        fontSize: 22,
        bold: true,
        color: TEXT,
        align: "center",
        valign: "middle",
      });

      // Description
      s.addText(a.desc, {
        x: x + 0.2, y: py + 2.2, w: cardW - 0.4, h: 0.8,
        fontFace: BODY_FONT,
        fontSize: 11,
        color: TEXT_MUTED,
        align: "center",
        valign: "top",
      });
    });

    // Result card on the right
    const rx = startX + 4 * (cardW + gap);
    const rw = 13.3 - rx - 0.4; // leave margin from slide right edge
    fillCard(s, pres, { x: rx, y: py, w: rw, h: ph, accent: "top", accentColor: VIOLET });
    s.addImage({ data: I.crown, x: rx + rw / 2 - 0.22, y: py + 0.5, w: 0.44, h: 0.44 });
    s.addText("KARAR", {
      x: rx, y: py + 1.05, w: rw, h: 0.4,
      fontFace: HEADER_FONT,
      fontSize: 12,
      bold: true,
      color: VIOLET,
      align: "center",
      charSpacing: 3,
      valign: "middle",
    });
    s.addText("Ürün\nGüven\nTasarruf", {
      x: rx, y: py + 1.55, w: rw, h: 1.3,
      fontFace: BODY_FONT,
      fontSize: 13,
      bold: true,
      color: TEXT,
      align: "center",
      valign: "top",
      paraSpaceAfter: 6,
    });

    // 3 supporting bullets below
    const by = 5.4;
    const bullets = [
      { icon: I.layers, text: "LangGraph orkestrasyonu  ·  A2A-uyumlu çoklu-ajan mesajlaşma" },
      { icon: I.bolt, text: "Gemini 2.5 Pro · Flash · Vision  —  her ajan için doğru model" },
      { icon: I.check, text: "Doğal dilde sorgudan 30 saniyede karara" },
    ];
    bullets.forEach((b, i) => {
      const by_i = by + i * 0.45;
      s.addImage({ data: b.icon, x: 0.7, y: by_i + 0.06, w: 0.24, h: 0.24 });
      s.addText(b.text, {
        x: 1.05, y: by_i, w: 11.5, h: 0.36,
        fontFace: BODY_FONT,
        fontSize: 14,
        color: TEXT,
        valign: "middle",
      });
    });

    pageNum(s, 3, TOTAL);
  }

  // ════════════════════════════════════════════════════════════
  // Slide 4 — DEMO
  // ════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: BG };

    chip(s, pres, { x: 0.6, y: 0.5, w: 1.7, text: "CANLI DEMO", color: EMERALD });

    // Massive centerpiece
    s.addText("DEMO", {
      x: 0.6, y: 2.0, w: 12.1, h: 2.5,
      fontFace: HEADER_FONT,
      fontSize: 220,
      bold: true,
      color: EMERALD,
      align: "center",
      valign: "middle",
      charSpacing: 24,
      margin: 0,
    });

    s.addText("3 dakika  ·  4 ajan  ·  gerçek bir pazarlık", {
      x: 0.6, y: 4.7, w: 12.1, h: 0.5,
      fontFace: BODY_FONT,
      fontSize: 22,
      color: TEXT_MUTED,
      align: "center",
      italic: true,
      valign: "middle",
    });

    // Bottom small hint
    s.addImage({ data: I.bolt, x: 5.8, y: 6.55, w: 0.22, h: 0.22 });
    s.addText("Hiçbir tuşa basmıyorum.", {
      x: 6.05, y: 6.5, w: 4, h: 0.4,
      fontFace: BODY_FONT,
      fontSize: 13,
      color: EMERALD,
      bold: true,
      valign: "middle",
    });

    pageNum(s, 4, TOTAL);
  }

  // ════════════════════════════════════════════════════════════
  // Slide 5 — ARCHITECTURE
  // ════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: BG };

    chip(s, pres, { x: 0.6, y: 0.5, w: 1.6, text: "MİMARİ", color: CYAN });
    s.addText("Slaytta istenen tüm framework'ler", {
      x: 0.6, y: 1.0, w: 12, h: 0.7,
      fontFace: HEADER_FONT,
      fontSize: 32,
      bold: true,
      color: TEXT,
      valign: "middle",
    });

    // 4 quadrant cards
    const cards = [
      {
        title: "FRONTEND",
        icon: I.code,
        accent: CYAN,
        items: [
          "Next.js 15  +  App Router",
          "Tailwind  +  Framer Motion",
          "WebSocket canlı agent streaming",
        ],
      },
      {
        title: "BACKEND",
        icon: I.layers,
        accent: VIOLET,
        items: [
          "FastAPI  +  async pipeline",
          "LangGraph-shaped orchestrator",
          "ThreadPool ile paralel ajanlar",
        ],
      },
      {
        title: "LLM",
        icon: I.bolt,
        accent: EMERALD,
        items: [
          "Gemini 2.5 Flash · Pro · Vision",
          "Her ajan kendi model tier'ında",
          "Disk cache  →  0 quota tekrar",
        ],
      },
      {
        title: "SANDBOX",
        icon: I.lock,
        accent: ROSE,
        items: [
          "Etik pazarlık katmanı",
          "Roleplay seller (Gemini ile kalibre)",
          "Production: marketplace partnership",
        ],
      },
    ];

    const cy = 2.0;
    const ch = 2.15;
    const cw = 5.95;
    const gx = 0.3;
    cards.forEach((c, i) => {
      const col = i % 2;
      const row = Math.floor(i / 2);
      const x = 0.6 + col * (cw + gx);
      const y = cy + row * (ch + 0.25);

      fillCard(s, pres, { x, y, w: cw, h: ch, accent: "left", accentColor: c.accent });

      // Icon + title
      s.addImage({ data: c.icon, x: x + 0.3, y: y + 0.3, w: 0.32, h: 0.32 });
      s.addText(c.title, {
        x: x + 0.75, y: y + 0.27, w: cw - 0.8, h: 0.4,
        fontFace: HEADER_FONT,
        fontSize: 16,
        bold: true,
        color: c.accent,
        charSpacing: 5,
        valign: "middle",
        margin: 0,
      });

      // Bullet list
      const bullets = c.items.map((it, idx) => ({
        text: it,
        options: {
          bullet: { code: "25CF" },
          color: TEXT,
          fontSize: 13,
          breakLine: idx < c.items.length - 1,
        },
      }));
      s.addText(bullets, {
        x: x + 0.3, y: y + 0.85, w: cw - 0.6, h: ch - 1.0,
        fontFace: BODY_FONT,
        paraSpaceAfter: 8,
        valign: "top",
      });
    });

    pageNum(s, 5, TOTAL);
  }

  // ════════════════════════════════════════════════════════════
  // Slide 6 — ROADMAP
  // ════════════════════════════════════════════════════════════
  {
    const s = pres.addSlide();
    s.background = { color: BG };

    chip(s, pres, { x: 0.6, y: 0.5, w: 2.0, text: "YOL HARİTASI", color: EMERALD });
    s.addText("Hackathon'dan ürüne", {
      x: 0.6, y: 1.0, w: 12, h: 0.7,
      fontFace: HEADER_FONT,
      fontSize: 32,
      bold: true,
      color: TEXT,
      valign: "middle",
    });

    // Horizontal timeline
    const tl = [
      { when: "ŞİMDİ", what: "Hackathon MVP", detail: "4 ajan + sandbox + canlı UI", color: EMERALD },
      { when: "1 AY", what: "Browser Extension", detail: "Chrome + Edge", color: CYAN },
      { when: "3 AY", what: "Partner Pilotu", detail: "Trendyol / Hepsiburada", color: VIOLET },
      { when: "6 AY", what: "Mobil + B2B", detail: "Satıcı tarafı sürümü", color: AMBER },
      { when: "1 YIL", what: "AI Alışveriş Katmanı", detail: "Türkiye için", color: ROSE },
    ];

    const ty = 2.2;
    const stepW = 2.4;
    const startX = 0.65;
    const gap = 0.1;

    // Connecting baseline
    s.addShape(pres.shapes.LINE, {
      x: startX + 0.6, y: ty + 0.55, w: (5 * stepW + 4 * gap) - 1.2, h: 0,
      line: { color: BORDER, width: 1.5 },
    });

    tl.forEach((step, i) => {
      const x = startX + i * (stepW + gap);
      // Numbered circle
      s.addShape(pres.shapes.OVAL, {
        x: x + stepW / 2 - 0.4, y: ty + 0.15, w: 0.8, h: 0.8,
        fill: { color: BG_CARD_HI },
        line: { color: step.color, width: 1.5 },
      });
      s.addText(String(i + 1), {
        x: x + stepW / 2 - 0.4, y: ty + 0.15, w: 0.8, h: 0.8,
        fontFace: HEADER_FONT,
        fontSize: 22,
        bold: true,
        color: step.color,
        align: "center",
        valign: "middle",
      });

      // When chip
      s.addText(step.when, {
        x, y: ty + 1.15, w: stepW, h: 0.3,
        fontFace: BODY_FONT,
        fontSize: 10,
        color: step.color,
        bold: true,
        charSpacing: 4,
        align: "center",
        valign: "middle",
      });

      // What
      s.addText(step.what, {
        x, y: ty + 1.5, w: stepW, h: 0.5,
        fontFace: HEADER_FONT,
        fontSize: 15,
        bold: true,
        color: TEXT,
        align: "center",
        valign: "middle",
      });

      // Detail
      s.addText(step.detail, {
        x: x + 0.1, y: ty + 2.05, w: stepW - 0.2, h: 0.7,
        fontFace: BODY_FONT,
        fontSize: 11,
        color: TEXT_MUTED,
        align: "center",
        valign: "top",
      });
    });

    // Closing statement
    const cy = 5.6;
    fillCard(s, pres, { x: 0.6, y: cy, w: 12.1, h: 1.2, accent: "left", accentColor: EMERALD });
    s.addText([
      { text: "Slayttaki tüm gereklilikleri karşıladık. ", options: { color: TEXT_MUTED } },
      { text: "Gemini ana ürün, LangGraph orkestrasyon, A2A çoklu-ajan protokolü.\n", options: { color: TEXT, bold: true, breakLine: true } },
      { text: "Üretime hazır mimari. Hackathon zamanı geldi.", options: { color: EMERALD, italic: true, fontSize: 17, bold: true } },
    ], {
      x: 0.85, y: cy + 0.15, w: 11.6, h: 0.9,
      fontFace: BODY_FONT,
      fontSize: 15,
      align: "left",
      valign: "middle",
    });

    pageNum(s, 6, TOTAL);
  }

  // ───────────────────────────────────────────────────────────────
  await pres.writeFile({ fileName: "AgentMarket-Pitch.pptx" });
  console.log("✓ Wrote AgentMarket-Pitch.pptx");
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
