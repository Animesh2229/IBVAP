const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "IBVAP Team";
pres.title = "IBVAP – Intelligent Border Video Analytics Platform";
pres.subject = "SSB Force Multiplier – Hackathon Pitch";

const BG = "0B1220";
const CARD = "111827";
const CYAN = "22D3EE";
const WHITE = "F8FAFC";
const MUTED = "94A3B8";
const ORANGE = "FB923C";
const GREEN = "34D399";
const VIOLET = "A78BFA";

function addBg(slide) {
  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 5.625, fill: { color: BG } });
}

// 1 Title
{
  const s = pres.addSlide();
  addBg(s);
  s.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 0.15, h: 5.625, fill: { color: CYAN } });
  s.addText("IBVAP", { x: 0.6, y: 1.5, w: 8.5, h: 0.7, fontSize: 44, bold: true, color: WHITE, fontFace: "Arial" });
  s.addText("Intelligent Border Video Analytics Platform", {
    x: 0.6, y: 2.2, w: 8.5, h: 0.4, fontSize: 20, color: CYAN, fontFace: "Arial"
  });
  s.addText("AI intelligence layer on existing CCTV for Sashastra Seema Bal", {
    x: 0.6, y: 2.8, w: 8.5, h: 0.35, fontSize: 14, color: MUTED, fontFace: "Arial"
  });
  s.addText("AI assists  ·  Humans decide  ·  Nation secured", {
    x: 0.6, y: 4.6, w: 8.5, h: 0.3, fontSize: 13, color: GREEN, fontFace: "Arial"
  });
}

// 2 Problem
{
  const s = pres.addSlide();
  addBg(s);
  s.addText("1  ·  Problem", { x: 0.5, y: 0.3, w: 9, h: 0.4, fontSize: 22, bold: true, color: CYAN, fontFace: "Arial" });
  const problems = [
    "Huge CCTV feeds — critical events missed in manual monitoring",
    "Legacy cameras, weak/no internet at remote BOPs",
    "High cost of replacing every camera with smart hardware",
    "~2,450 km open Indo-Nepal / Indo-Bhutan border — force multiplier needed",
    "Need tamper-proof audit trail of critical events"
  ];
  problems.forEach((t, i) => {
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, {
      x: 0.5, y: 0.9 + i * 0.75, w: 9, h: 0.65,
      fill: { color: CARD }, rectRadius: 0.08
    });
    s.addText(t, { x: 0.7, y: 0.95 + i * 0.75, w: 8.6, h: 0.5, fontSize: 14, color: WHITE, fontFace: "Arial", valign: "middle" });
  });
}

// 3 Solution
{
  const s = pres.addSlide();
  addBg(s);
  s.addText("2  ·  Solution Overview", { x: 0.5, y: 0.3, w: 9, h: 0.4, fontSize: 22, bold: true, color: CYAN, fontFace: "Arial" });
  const sols = [
    ["Edge AI on existing CCTV", "No full camera replacement"],
    ["Event-driven, edge-first, offline-first", "Works without internet"],
    ["Human-in-the-loop", "Every alert becomes action after review"],
    ["Privacy-by-design", "Watchlist-only matching"],
    ["Tamper-evident log", "SHA-256 hash-chain + future blockchain anchor"]
  ];
  sols.forEach((row, i) => {
    const y = 0.9 + i * 0.8;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y, w: 9, h: 0.7, fill: { color: CARD }, rectRadius: 0.08 });
    s.addText(row[0], { x: 0.7, y: y + 0.08, w: 8.6, h: 0.3, fontSize: 15, bold: true, color: WHITE, fontFace: "Arial" });
    s.addText(row[1], { x: 0.7, y: y + 0.35, w: 8.6, h: 0.28, fontSize: 12, color: MUTED, fontFace: "Arial" });
  });
}

// 4 Demo features
{
  const s = pres.addSlide();
  addBg(s);
  s.addText("3  ·  Core Demo Features", { x: 0.5, y: 0.3, w: 9, h: 0.4, fontSize: 22, bold: true, color: CYAN, fontFace: "Arial" });
  const feats = [
    { t: "Virtual Fence", d: "Define digital boundary. Detect entry into prohibited / critical zone.", c: CYAN },
    { t: "Behavioral Alert Engine", d: "Dwell time, direction, repeated crossing, multi-camera link → priority score.", c: ORANGE },
    { t: "Tamper-Evident Local Log", d: "Every critical event in local hash-chain. Any change breaks the chain.", c: VIOLET }
  ];
  feats.forEach((f, i) => {
    const x = 0.4 + i * 3.15;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.1, w: 3.0, h: 3.6, fill: { color: CARD }, rectRadius: 0.1 });
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.1, w: 3.0, h: 0.12, fill: { color: f.c } });
    s.addText(String(i + 1), { x: x + 0.2, y: 1.4, w: 2.6, h: 0.4, fontSize: 28, bold: true, color: f.c, fontFace: "Arial" });
    s.addText(f.t, { x: x + 0.2, y: 2.0, w: 2.6, h: 0.7, fontSize: 16, bold: true, color: WHITE, fontFace: "Arial" });
    s.addText(f.d, { x: x + 0.2, y: 2.8, w: 2.6, h: 1.5, fontSize: 13, color: MUTED, fontFace: "Arial" });
  });
}

// 5 Architecture
{
  const s = pres.addSlide();
  addBg(s);
  s.addText("4  ·  Technical Architecture", { x: 0.5, y: 0.3, w: 9, h: 0.4, fontSize: 22, bold: true, color: CYAN, fontFace: "Arial" });
  const steps = ["CCTV", "Compat Layer", "Edge AI", "Analytics", "Human Review", "Dashboard", "Hash Log"];
  steps.forEach((t, i) => {
    const x = 0.35 + i * 1.35;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 1.3, w: 1.25, h: 0.9, fill: { color: CARD }, rectRadius: 0.08 });
    s.addText(t, { x, y: 1.45, w: 1.25, h: 0.6, fontSize: 11, color: WHITE, fontFace: "Arial", align: "center", valign: "middle" });
    if (i < steps.length - 1) {
      s.addText("→", { x: x + 1.15, y: 1.5, w: 0.3, h: 0.5, fontSize: 16, color: CYAN, fontFace: "Arial" });
    }
  });
  const boxes = [
    ["Always-On (light)", "Motion · Virtual Fence\nLow compute, always running"],
    ["Triggered (heavy)", "Tracking · ANPR · Watchlist\nRuns only on relevant events"],
    ["Behavioral Score", "Multi-signal → priority\nNo single cue escalates alone"]
  ];
  boxes.forEach((b, i) => {
    const x = 0.5 + i * 3.15;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y: 2.6, w: 3.0, h: 2.2, fill: { color: CARD }, rectRadius: 0.1 });
    s.addText(b[0], { x: x + 0.15, y: 2.8, w: 2.7, h: 0.4, fontSize: 14, bold: true, color: CYAN, fontFace: "Arial" });
    s.addText(b[1], { x: x + 0.15, y: 3.3, w: 2.7, h: 1.2, fontSize: 13, color: MUTED, fontFace: "Arial" });
  });
}

// 6 Stack
{
  const s = pres.addSlide();
  addBg(s);
  s.addText("5  ·  Final Tech Stack", { x: 0.5, y: 0.3, w: 9, h: 0.4, fontSize: 22, bold: true, color: CYAN, fontFace: "Arial" });
  const rows = [
    ["Edge", "Laptop demo · Mini-PC N100 / Jetson / Coral (deploy)"],
    ["Ingestion", "RTSP / ONVIF / Analog→IP · FFmpeg · OpenCV"],
    ["AI", "YOLOv8 · ByteTrack · PaddleOCR · Watchlist face"],
    ["Backend", "FastAPI · SQLite SHA-256 chain · MQTT store-forward · WebSocket"],
    ["Dashboard", "React/Tailwind path · Leaflet maps · Live alerts"]
  ];
  rows.forEach((r, i) => {
    const y = 0.9 + i * 0.8;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: 0.5, y, w: 9, h: 0.7, fill: { color: CARD }, rectRadius: 0.08 });
    s.addText(r[0], { x: 0.7, y: y + 0.15, w: 1.8, h: 0.4, fontSize: 14, bold: true, color: CYAN, fontFace: "Arial" });
    s.addText(r[1], { x: 2.6, y: y + 0.15, w: 6.7, h: 0.4, fontSize: 13, color: WHITE, fontFace: "Arial" });
  });
}

// 7 USPs
{
  const s = pres.addSlide();
  addBg(s);
  s.addText("6  ·  Unique Selling Points", { x: 0.5, y: 0.3, w: 9, h: 0.4, fontSize: 22, bold: true, color: CYAN, fontFace: "Arial" });
  const usps = [
    "Works with existing CCTV (audited compatibility)",
    "Event-driven edge AI — efficient & feasible",
    "Offline-first, store-and-forward sync",
    "Privacy-by-design, watchlist-only",
    "Lightweight hash-chain + blockchain anchor path",
    "Human-in-the-loop decision making",
    "Realistic TCO with full deployment cost",
    "Risk-based, phased, measurable rollout"
  ];
  usps.forEach((u, i) => {
    const col = i < 4 ? 0 : 1;
    const row = i % 4;
    const x = 0.5 + col * 4.7;
    const y = 0.95 + row * 1.0;
    s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w: 4.4, h: 0.85, fill: { color: CARD }, rectRadius: 0.08 });
    s.addText("✓  " + u, { x: x + 0.2, y: y + 0.15, w: 4.0, h: 0.55, fontSize: 13, color: WHITE, fontFace: "Arial", valign: "middle" });
  });
}

// 8 Judge line
{
  const s = pres.addSlide();
  addBg(s);
  s.addText("Judge-ready answer", { x: 0.5, y: 1.5, w: 9, h: 0.4, fontSize: 16, color: CYAN, fontFace: "Arial" });
  s.addText("IBVAP adds an intelligence layer to existing CCTV — detecting, prioritising and verifying suspicious activity with privacy safeguards and tamper-evident auditing — so our jawans see more, miss less, and act with confidence.", {
    x: 0.5, y: 2.1, w: 9, h: 1.8, fontSize: 18, color: WHITE, fontFace: "Arial"
  });
  s.addText("Force multiplier. Not a replacement.", {
    x: 0.5, y: 4.3, w: 9, h: 0.4, fontSize: 16, bold: true, color: GREEN, fontFace: "Arial"
  });
}

pres.writeFile({ fileName: "/home/workdir/artifacts/ibvap/docs/IBVAP_Pitch_Deck.pptx" })
  .then(() => console.log("PITCH_OK"))
  .catch((e) => console.error(e));
