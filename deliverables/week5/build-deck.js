const pptxgen = require("pptxgenjs");
const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";            // 13.3 x 7.5
pres.author = "Quinn Evans";
pres.title = "PanTS — 3D Pancreatic Lesion Segmentation";

// ---- palette: pulled from the actual UI so the deck matches the product ----
const BG        = "071019";
const PANEL     = "0E1A26";
const PANEL_HI  = "13212F";
const TEXT      = "EDF5F7";
const SOFT      = "BFD0D6";
const MUTED     = "7C919D";
const TEAL      = "26C5A6";   // model / pancreas
const RED       = "F96363";   // lesion / limitation
const AMBER     = "F4BC55";   // reference / caution
const BLUE      = "6CB9DC";

const F = "Calibri";
const W = 13.3, H = 7.5;

// ---------- helpers ----------
function base(title, kicker) {
  const s = pres.addSlide();
  s.background = { color: BG };
  if (kicker) {
    s.addText(kicker.toUpperCase(), {
      x: 0.7, y: 0.42, w: 11.9, h: 0.28, fontFace: F, fontSize: 11,
      color: TEAL, bold: true, charSpacing: 2, margin: 0,
    });
  }
  if (title) {
    s.addText(title, {
      x: 0.7, y: 0.75, w: 11.9, h: 0.85, fontFace: F, fontSize: 34,
      color: TEXT, bold: true, margin: 0, valign: "top",
    });
  }
  return s;
}
function foot(s, n, label) {
  s.addText(label, { x: 0.7, y: 6.95, w: 8, h: 0.3, fontFace: F, fontSize: 10, color: MUTED, margin: 0 });
  s.addText(String(n), { x: 12.1, y: 6.95, w: 0.5, h: 0.3, fontFace: F, fontSize: 10, color: MUTED, align: "right", margin: 0 });
}
// bullet block
function bullets(s, items, o = {}) {
  const arr = items.map((t, i) => ({
    text: t,
    options: { bullet: true, breakLine: i !== items.length - 1 },
  }));
  s.addText(arr, {
    x: o.x || 0.75, y: o.y || 1.9, w: o.w || 7.2, h: o.h || 4.4,
    fontFace: F, fontSize: o.fontSize || 17, color: o.color || SOFT,
    lineSpacing: o.lineSpacing || 30, paraSpaceAfter: o.gap || 12, margin: 0, valign: "top",
  });
}
// card
function card(s, x, y, w, h, fill) {
  s.addShape(pres.ShapeType.roundRect, {
    x, y, w, h, rectRadius: 0.09,
    fill: { color: fill || PANEL }, line: { color: "1D2E3D", width: 1 },
  });
}
// big stat
function stat(s, x, y, w, value, label, color) {
  s.addText(value, { x, y, w, h: 0.95, fontFace: F, fontSize: 44, bold: true, color: color || TEAL, align: "center", margin: 0 });
  s.addText(label, { x, y: y + 0.92, w, h: 0.75, fontFace: F, fontSize: 12, color: MUTED, align: "center", margin: 0 });
}
// numbered motif chip (the repeated visual element)
function chip(s, x, y, txt, color) {
  s.addShape(pres.ShapeType.roundRect, {
    x, y, w: 0.42, h: 0.42, rectRadius: 0.21,
    fill: { color: color || TEAL }, line: { color: color || TEAL, width: 1 },
  });
  s.addText(txt, { x, y, w: 0.42, h: 0.42, fontFace: F, fontSize: 13, bold: true,
    color: BG, align: "center", valign: "middle", margin: 0 });
}

/* =====================================================================
   1 · PROBLEM & BUSINESS VALUE  (4 min)
   ===================================================================== */

// ---- S1 title ----
{
  const s = pres.addSlide();
  s.background = { color: BG };
  s.addText("PanTS Review", { x: 0.9, y: 2.15, w: 11.5, h: 0.9, fontFace: F, fontSize: 54, bold: true, color: TEXT, margin: 0 });
  s.addText("Finding pancreatic tumors in 3D CT — a segmentation and annotation-assist tool",
    { x: 0.9, y: 3.1, w: 11, h: 0.5, fontFace: F, fontSize: 20, color: TEAL, margin: 0 });
  s.addText("Quinn Evans  ·  five-week independent ML project  ·  Johns Hopkins PanTS dataset",
    { x: 0.9, y: 3.85, w: 11, h: 0.4, fontFace: F, fontSize: 14, color: MUTED, margin: 0 });
  card(s, 0.9, 4.75, 7.6, 0.75, PANEL);
  s.addText("Research use only — this is not a diagnostic system.",
    { x: 1.15, y: 4.75, w: 7.1, h: 0.75, fontFace: F, fontSize: 14, color: SOFT, valign: "middle", margin: 0 });
  s.addNotes("30 min talk + 10 min Q&A. Open by naming the scope out loud: segmentation + a CADe flag, never a diagnosis.");
}

// ---- S2 why the pancreas ----
{
  const s = base("Why the pancreas is hard", "The problem");
  bullets(s, [
    "Pancreatic cancer is among the deadliest — outcomes hinge on catching it early",
    "The organ is soft, irregular, and hidden behind other structures",
    "Tumors are often nearly invisible to the human eye on a CT slice",
    "A radiologist reads hundreds of slices per scan, and most scans are normal",
  ], { w: 7.3, y: 2.0 });
  card(s, 8.5, 1.95, 4.1, 3.5);
  stat(s, 8.5, 2.35, 4.1, "10.4%", "of scans in this dataset\ncontain a tumor", AMBER);
  s.addText("A needle-in-a-haystack read, repeated all day.",
    { x: 8.85, y: 4.35, w: 3.4, h: 0.9, fontFace: F, fontSize: 13, color: SOFT, italic: true, align: "center", margin: 0 });
  foot(s, 2, "Problem & business value");
  s.addNotes("[RIFF] Expand on whichever lands: the biology, the invisibility, or the volume of reading. The 10.4% is the business framing — most of the work is ruling things out.");
}

// ---- S3 who it's for ----
{
  const s = base("Who it's for, and what changes", "The user");
  card(s, 0.75, 1.95, 5.6, 3.9, PANEL);
  card(s, 6.9, 1.95, 5.6, 3.9, PANEL_HI);
  s.addText("Today", { x: 1.1, y: 2.2, w: 5, h: 0.4, fontFace: F, fontSize: 18, bold: true, color: MUTED, margin: 0 });
  bullets(s, [
    "Trace the pancreas by hand, slice by slice",
    "Hunt for a lesion that may not be visible",
    "Slow, tedious, and easy to miss something",
  ], { x: 1.1, y: 2.75, w: 4.9, fontSize: 15, color: SOFT });

  s.addText("With this tool", { x: 7.25, y: 2.2, w: 5, h: 0.4, fontFace: F, fontSize: 18, bold: true, color: TEAL, margin: 0 });
  bullets(s, [
    "A proposed outline is already drawn",
    "Accept, edit, or reject it",
    "A flag says “look here first”",
    "Export the mask and finish the job",
  ], { x: 7.25, y: 2.75, w: 4.9, fontSize: 15, color: SOFT });
  s.addText("User: radiologist / imaging annotator", { x: 0.75, y: 6.15, w: 11.8, h: 0.4, fontFace: F, fontSize: 14, color: MUTED, margin: 0 });
  foot(s, 3, "Problem & business value");
  s.addNotes("[RIFF] The decision this supports is triage and time: where to look first, and how much tracing work is left.");
}

// ---- S4 scope ----
{
  const s = base("What this is — and what it isn't", "Scope");
  const rows = [
    ["It IS", "A segmentation tool: it outlines the pancreas and any suspicious region", TEAL],
    ["It IS", "A CADe assist: it flags “there could be a tumor here” for review", TEAL],
    ["It is NOT", "A diagnosis — it never decides whether a patient has cancer", RED],
    ["It is NOT", "Autonomous — a human reviews and edits every single output", RED],
  ];
  let y = 2.0;
  rows.forEach((r, i) => {
    card(s, 0.75, y, 11.75, 0.95, i < 2 ? PANEL : PANEL_HI);
    s.addText(r[0], { x: 1.05, y, w: 1.6, h: 0.95, fontFace: F, fontSize: 14, bold: true, color: r[2], valign: "middle", margin: 0 });
    s.addText(r[1], { x: 2.75, y, w: 9.4, h: 0.95, fontFace: F, fontSize: 15, color: SOFT, valign: "middle", margin: 0 });
    y += 1.12;
  });
  foot(s, 4, "Problem & business value");
  s.addNotes("[TRANSIT] 20 seconds. Stating scope up front pre-empts half the Q&A.");
}

/* =====================================================================
   2 · LIVE DEMO  (7 min)
   ===================================================================== */

// ---- S5 what you're about to see ----
{
  const s = base("Three things to watch", "Live demo");
  const beats = [
    ["1", "An unmarked scan", "Exactly what a radiologist sees — nothing drawn on it yet", TEAL],
    ["2", "The model scores it live", "A real call to the deployed endpoint, about half a second", BLUE],
    ["3", "The truth is revealed", "Expert contours overlaid on the prediction — how close was it?", AMBER],
  ];
  let x = 0.75;
  beats.forEach((b) => {
    card(s, x, 2.1, 3.85, 3.4);
    chip(s, x + 0.35, 2.45, b[0], b[3]);
    s.addText(b[1], { x: x + 0.35, y: 3.1, w: 3.2, h: 0.5, fontFace: F, fontSize: 19, bold: true, color: TEXT, margin: 0 });
    s.addText(b[2], { x: x + 0.35, y: 3.7, w: 3.2, h: 1.4, fontFace: F, fontSize: 14, color: SOFT, margin: 0 });
    x += 4.03;
  });
  s.addText("Every scan shown is held-out data the model never trained on.",
    { x: 0.75, y: 5.85, w: 11.8, h: 0.4, fontFace: F, fontSize: 14, color: MUTED, italic: true, margin: 0 });
  foot(s, 5, "Live demo");
  s.addNotes("[TRANSIT] Set expectations in 30 seconds, then switch to the app.");
}

// ---- S6 DEMO marker ----
{
  const s = pres.addSlide();
  s.background = { color: BG };
  s.addText("LIVE DEMO", { x: 0.9, y: 2.6, w: 11.5, h: 1.1, fontFace: F, fontSize: 60, bold: true, color: TEAL, margin: 0 });
  s.addText("PanTS Review  ·  localhost:5173  ·  live inference on port 8000",
    { x: 0.95, y: 3.75, w: 11, h: 0.4, fontFace: F, fontSize: 16, color: MUTED, margin: 0 });
  foot(s, 6, "Live demo");
  s.addNotes([
    "[RIFF] 6-7 minutes. Runsheet:",
    "1. Scan library — real held-out studies",
    "2. Load one UNMARKED — this is what the radiologist sees",
    "3. Analyze — live endpoint call, ~0.6s, 'scored just now' badge",
    "4. Read the finding — flag, size, confidence",
    "5. Reveal source of truth — red vs amber, Dice appears",
    "6. 3D — rotate the pancreas with the lesion inside",
    "7. Show the honest case: the healthy scan it over-calls",
    "Fallback: if the endpoint drops, the UI serves cached results — say so out loud, it is a designed behavior.",
  ].join("\n"));
}

// ---- S7 what just happened ----
{
  const s = base("What just happened", "Live demo");
  const items = [
    ["Real model", "The registered model, version 1 — the same checkpoint I evaluated", TEAL],
    ["Real call", "A live HTTP request to a deployed FastAPI endpoint, ~0.6s per scan", BLUE],
    ["Real data", "Held-out scans from the official test split — never seen in training", AMBER],
  ];
  let y = 2.15;
  items.forEach((it, i) => {
    card(s, 0.75, y, 11.75, 1.15);
    chip(s, 1.1, y + 0.36, String(i + 1), it[2]);
    s.addText(it[0], { x: 1.75, y, w: 2.4, h: 1.15, fontFace: F, fontSize: 17, bold: true, color: TEXT, valign: "middle", margin: 0 });
    s.addText(it[1], { x: 4.2, y, w: 8, h: 1.15, fontFace: F, fontSize: 15, color: SOFT, valign: "middle", margin: 0 });
    y += 1.35;
  });
  s.addText("Not a recording, not a screenshot.", { x: 0.75, y: 6.1, w: 11.8, h: 0.4, fontFace: F, fontSize: 15, color: TEAL, italic: true, margin: 0 });
  foot(s, 7, "Live demo");
  s.addNotes("[TRANSIT] 20 seconds. Then move into how it's built.");
}

/* =====================================================================
   3 · SYSTEM WALKTHROUGH  (6 min)
   ===================================================================== */

// ---- S8 architecture ----
{
  const s = base("End to end", "Architecture");
  const steps = ["Index\n9,901 scans", "Split\nby patient", "Audit\nmasks", "Train\nSegResNet", "Evaluate\nheld-out", "Register\nMLflow", "Serve\nFastAPI", "Review\nReact UI"];
  let x = 0.62;
  const w = 1.46, gap = 0.06;
  steps.forEach((t, i) => {
    const isLast3 = i >= 5;
    card(s, x, 2.5, w, 1.5, isLast3 ? PANEL_HI : PANEL);
    s.addText(t, { x: x + 0.05, y: 2.5, w: w - 0.1, h: 1.5, fontFace: F, fontSize: 12,
      color: isLast3 ? TEAL : SOFT, align: "center", valign: "middle", margin: 0, bold: isLast3 });
    if (i < steps.length - 1) {
      s.addText("›", { x: x + w, y: 2.5, w: gap + 0.12, h: 1.5, fontFace: F, fontSize: 16, color: MUTED, align: "center", valign: "middle", margin: 0 });
    }
    x += w + gap + 0.06;
  });
  const notes = [
    ["Config-driven", "One YAML defines the recipe; nothing hardcoded"],
    ["Reproducible", "Fixed seed, committed splits, every run logged to MLflow"],
    ["Guarded", "Startup abort if a training split ever touches validation"],
  ];
  let nx = 0.75;
  notes.forEach((n) => {
    s.addText(n[0], { x: nx, y: 4.6, w: 3.7, h: 0.35, fontFace: F, fontSize: 15, bold: true, color: TEAL, margin: 0 });
    s.addText(n[1], { x: nx, y: 5.0, w: 3.7, h: 0.9, fontFace: F, fontSize: 13, color: SOFT, margin: 0 });
    nx += 3.95;
  });
  foot(s, 8, "System walkthrough");
  s.addNotes("[RIFF] Walk left to right. The last three boxes are what turns a model into a system.");
}

// ---- S9 data pipeline ----
{
  const s = base("The data was the hard part", "Data pipeline");
  bullets(s, [
    "9,901 real CT volumes — about 380 GB, on an external drive, never in the repo",
    "Split by patient, stratified by tumor, so no patient appears on both sides",
    "Roughly 1 in 8 scans had a broken or empty mask — audited and excluded",
    "Volumes range from 8 to over 1,000 slices, across four scanner manufacturers",
  ], { w: 7.4, y: 2.05 });
  card(s, 8.6, 2.0, 4.0, 1.55);
  stat(s, 8.6, 2.2, 4.0, "9,901", "CT volumes indexed", TEAL);
  card(s, 8.6, 3.75, 4.0, 1.55);
  stat(s, 8.6, 3.95, 4.0, "~1 in 8", "masks broken or empty", AMBER);
  s.addText("Auditing data integrity turned out to be the work, not a distraction from it.",
    { x: 0.75, y: 5.9, w: 11.8, h: 0.5, fontFace: F, fontSize: 15, color: TEAL, italic: true, margin: 0 });
  foot(s, 9, "System walkthrough");
  s.addNotes("[RIFF] Good place to talk about real-world messiness versus clean teaching datasets.");
}

// ---- S10 the model ----
{
  const s = base("The model", "Model");
  card(s, 0.75, 1.95, 5.65, 4.0);
  s.addText("3D SegResNet", { x: 1.1, y: 2.2, w: 5, h: 0.45, fontFace: F, fontSize: 21, bold: true, color: TEXT, margin: 0 });
  bullets(s, [
    "Fine-tuned from SuPreM — pretrained by the same Johns Hopkins lab",
    "Three classes: background, pancreas, lesion",
    "Whole-box input: the entire pancreas region as one cube",
    "Trained on Apple Silicon (MPS), ~7-14 h per run",
  ], { x: 1.1, y: 2.75, w: 4.95, fontSize: 14 });

  card(s, 6.85, 1.95, 5.65, 4.0, PANEL_HI);
  s.addText("Does the pretraining matter?", { x: 7.2, y: 2.2, w: 5, h: 0.45, fontFace: F, fontSize: 21, bold: true, color: TEAL, margin: 0 });
  s.addText("I measured it instead of assuming.", { x: 7.2, y: 2.7, w: 5, h: 0.35, fontFace: F, fontSize: 14, color: MUTED, margin: 0 });
  stat(s, 7.2, 3.25, 2.5, "0.120", "from scratch", MUTED);
  stat(s, 9.85, 3.25, 2.5, "0.257", "SuPreM transfer", TEAL);
  s.addText("+0.13 lesion Dice — the pretraining is what makes this work at my data scale.",
    { x: 7.2, y: 4.95, w: 5.0, h: 0.8, fontFace: F, fontSize: 13, color: SOFT, margin: 0 });
  foot(s, 10, "System walkthrough");
  s.addNotes("[RIFF] EXP-09. Single variable, same recipe. From scratch also flagged every healthy scan.");
}

// ---- S11 deployment ----
{
  const s = base("From checkpoint to product", "Deployment");
  const cols = [
    ["MLflow registry", ["pancreas-lesion-segmenter v1", "Checkpoint step 18000", "SHA + config + git commit logged"], TEAL],
    ["FastAPI endpoint", ["GET /health, GET /cases", "POST /predict → CADe summary", "~0.6 s per scan"], BLUE],
    ["React + NiiVue UI", ["Live analyze against the endpoint", "Falls back to cached results", "3D surfaces from marching cubes"], AMBER],
  ];
  let x = 0.75;
  cols.forEach((c) => {
    card(s, x, 2.05, 3.85, 3.6);
    s.addText(c[0], { x: x + 0.32, y: 2.35, w: 3.3, h: 0.45, fontFace: F, fontSize: 18, bold: true, color: c[2], margin: 0 });
    bullets(s, c[1], { x: x + 0.32, y: 2.95, w: 3.25, fontSize: 13, lineSpacing: 22, gap: 8 });
    x += 4.03;
  });
  s.addText("The model is versioned, served, and consumed — not a notebook artifact.",
    { x: 0.75, y: 5.95, w: 11.8, h: 0.4, fontFace: F, fontSize: 15, color: SOFT, italic: true, margin: 0 });
  foot(s, 11, "System walkthrough");
  s.addNotes("[TRANSIT] 40 seconds unless asked. This is the layer that makes the demo possible.");
}

/* =====================================================================
   4 · HOW I ACTUALLY WORKED  (5 min)
   ===================================================================== */

// ---- S12 method ----
{
  const s = base("26 experiments, bars set in advance", "Method");
  bullets(s, [
    "Every experiment: a hypothesis and an accept/reject bar written BEFORE the run",
    "One variable at a time — everything else held fixed",
    "Each result logged with its decision, including the failures",
    "Roughly one experiment per night: a training run is 7 to 14 hours",
  ], { w: 7.4, y: 2.1 });
  card(s, 8.6, 2.05, 4.0, 3.3);
  stat(s, 8.6, 2.45, 4.0, "26", "numbered experiments", TEAL);
  s.addText("Accepted, rejected, or null —\nall of them written down.",
    { x: 8.9, y: 4.15, w: 3.4, h: 0.9, fontFace: F, fontSize: 13, color: SOFT, align: "center", margin: 0 });
  s.addText("If I couldn't say in advance what would make me abandon an idea, I wasn't testing it.",
    { x: 0.75, y: 5.9, w: 11.8, h: 0.5, fontFace: F, fontSize: 15, color: TEAL, italic: true, margin: 0 });
  foot(s, 12, "How I worked");
  s.addNotes("[RIFF] This is the frame for the next three slides. Method first, then the three stories.");
}

// ---- S13 whole-box ----
{
  const s = base("The breakthrough was an idea, not a knob", "Story 1");
  bullets(s, [
    "The model found tumors but over-predicted them — flagging something on 92% of healthy scans",
    "I tried the obvious knobs. Sampling: null. Loss function: null.",
    "Two nulls told me the problem was structural, not a hyperparameter",
    "So: stop feeding random patches. Feed the ENTIRE pancreas region as one cube.",
  ], { w: 7.35, y: 2.05, fontSize: 16 });
  card(s, 8.55, 2.0, 4.05, 3.55, PANEL_HI);
  s.addText("One change", { x: 8.85, y: 2.25, w: 3.5, h: 0.4, fontFace: F, fontSize: 16, bold: true, color: TEAL, margin: 0 });
  const deltas = [["Pancreas Dice", "0.72 → 0.81"], ["Specificity", "8% → 55%"], ["Lesion Dice", "new best"]];
  let dy = 2.85;
  deltas.forEach((d) => {
    s.addText(d[0], { x: 8.85, y: dy, w: 1.9, h: 0.45, fontFace: F, fontSize: 13, color: MUTED, valign: "middle", margin: 0 });
    s.addText(d[1], { x: 10.75, y: dy, w: 1.6, h: 0.45, fontFace: F, fontSize: 15, bold: true, color: TEAL, align: "right", valign: "middle", margin: 0 });
    dy += 0.62;
  });
  s.addText("Became the architecture of the final model.",
    { x: 8.85, y: 4.75, w: 3.5, h: 0.7, fontFace: F, fontSize: 13, color: SOFT, italic: true, margin: 0 });
  foot(s, 13, "How I worked");
  s.addNotes("[RIFF] The point: the nulls were informative. They told me where the problem wasn't, which is how I found where it was.");
}

// ---- S14 leakage ----
{
  const s = base("I found out my own number was wrong", "Story 2");
  bullets(s, [
    "An adversarial code audit found my data-scaling script sampled from the wrong column",
    "My training set overlapped my validation set — 30 of the 40 cases I was reporting on had been trained on",
    "I verified it myself, then fixed the root cause rather than the symptom",
    "Added a guard that aborts training if a split ever touches validation — that class of bug can't recur silently",
    "Rebuilt the splits, retrained, and re-reported the honest number",
  ], { w: 7.35, y: 2.0, fontSize: 15.5 });
  card(s, 8.55, 2.0, 4.05, 2.9, PANEL_HI);
  s.addText("Reported", { x: 8.85, y: 2.25, w: 3.5, h: 0.35, fontFace: F, fontSize: 13, color: MUTED, margin: 0 });
  s.addText("0.528", { x: 8.85, y: 2.6, w: 3.5, h: 0.6, fontFace: F, fontSize: 32, bold: true, color: MUTED, strike: true, margin: 0 });
  s.addText("Honest", { x: 8.85, y: 3.3, w: 3.5, h: 0.35, fontFace: F, fontSize: 13, color: TEAL, margin: 0 });
  s.addText("0.474", { x: 8.85, y: 3.65, w: 3.5, h: 0.7, fontFace: F, fontSize: 38, bold: true, color: TEAL, margin: 0 });
  s.addText("Lower, real — and it didn't collapse, so the underlying result was genuine.",
    { x: 8.55, y: 5.05, w: 4.05, h: 0.9, fontFace: F, fontSize: 13, color: SOFT, italic: true, margin: 0 });
  foot(s, 14, "How I worked");
  s.addNotes("[RIFF] The strongest credibility moment in the talk. Caught before external validation, which is exactly when you want it.");
}

// ---- S15 rejections ----
{
  const s = base("Two experiments I rejected", "Story 3");
  const items = [
    ["Anatomy-aware supervision", "Looked like a clear win at an intermediate checkpoint — +0.041 lesion Dice.",
      "I trained both arms to convergence before deciding. The effect vanished. Rejected.", RED],
    ["More healthy training data", "Cleared its specificity bar decisively — 17% up to 46%.",
      "But detection fell to 88%, three cases below the floor I set in advance. Rejected.", RED],
  ];
  let y = 2.05;
  items.forEach((it) => {
    card(s, 0.75, y, 11.75, 1.85);
    s.addText(it[0], { x: 1.15, y: y + 0.18, w: 10.9, h: 0.42, fontFace: F, fontSize: 18, bold: true, color: TEXT, margin: 0 });
    s.addText(it[1], { x: 1.15, y: y + 0.65, w: 10.9, h: 0.35, fontFace: F, fontSize: 14, color: SOFT, margin: 0 });
    s.addText(it[2], { x: 1.15, y: y + 1.05, w: 10.9, h: 0.55, fontFace: F, fontSize: 14, color: it[3], margin: 0 });
    y += 2.05;
  });
  s.addText("A result you stop at because it looks good is not a result you can trust.",
    { x: 0.75, y: 6.2, w: 11.8, h: 0.45, fontFace: F, fontSize: 16, color: TEAL, italic: true, margin: 0 });
  foot(s, 15, "How I worked");
  s.addNotes("[RIFF] Both rejections are wins for the method. The second is the honest 'I didn't move my own goalposts' story.");
}

/* =====================================================================
   5 · RESULTS & LIMITS  (5 min)
   ===================================================================== */

// ---- S16 final numbers ----
{
  const s = base("Final numbers", "Results");
  s.addText("Official held-out test set — 901 scans, scored once, never touched during development",
    { x: 0.75, y: 1.72, w: 11.8, h: 0.4, fontFace: F, fontSize: 15, color: MUTED, margin: 0 });
  const cells = [
    ["96%", "detection sensitivity\n145 of 151 tumors flagged", TEAL],
    ["0.474", "lesion Dice\n95% CI 0.42 – 0.52", TEAL],
    ["0.827", "pancreas Dice", BLUE],
    ["17%", "specificity\non healthy scans", RED],
  ];
  let x = 0.75;
  cells.forEach((c) => {
    card(s, x, 2.3, 2.85, 2.5);
    stat(s, x, 2.65, 2.85, c[0], c[1], c[2]);
    x += 2.97;
  });
  card(s, 0.75, 5.1, 11.75, 1.1, PANEL_HI);
  s.addText("Published PanTS benchmark: ~0.53 lesion Dice   (MedFormer 0.529 · R-Super 0.534, which uses additional external data)",
    { x: 1.1, y: 5.1, w: 11.1, h: 1.1, fontFace: F, fontSize: 15, color: SOFT, valign: "middle", margin: 0 });
  foot(s, 16, "Results & limits");
  s.addNotes("[RIFF] Lead with detection — it's the number that matters for a CADe tool. The benchmark line gives the audience a yardstick.");
}

// ---- S17 business terms ----
{
  const s = base("What those numbers mean for the user", "Results");
  const rows = [
    ["96% detection", "Catch rate. Of the tumors present, the tool surfaces almost all of them for review.", TEAL],
    ["0.474 lesion Dice", "Edit burden. The outline is a usable starting point that still needs a human pass.", BLUE],
    ["0.827 pancreas Dice", "The organ outline is close to expert quality — the tedious tracing is largely done.", BLUE],
    ["17% specificity", "False-alarm rate. It cries wolf often, so every flag is a prompt, never a verdict.", RED],
  ];
  let y = 2.0;
  rows.forEach((r) => {
    card(s, 0.75, y, 11.75, 1.05);
    s.addText(r[0], { x: 1.1, y, w: 3.1, h: 1.05, fontFace: F, fontSize: 17, bold: true, color: r[2], valign: "middle", margin: 0 });
    s.addText(r[1], { x: 4.3, y, w: 7.9, h: 1.05, fontFace: F, fontSize: 14.5, color: SOFT, valign: "middle", margin: 0 });
    y += 1.2;
  });
  foot(s, 17, "Results & limits");
  s.addNotes("[TRANSIT] 45 seconds. Translate once, clearly, then move to the limitations.");
}

// ---- S18 limitation 1 ----
{
  const s = base("Limitation: the model is given the pancreas region", "Honest limits");
  card(s, 0.75, 1.9, 11.75, 0.9, PANEL_HI);
  s.addText("It is pointed at the pancreas rather than searching the whole scan on its own.",
    { x: 1.1, y: 1.9, w: 11.1, h: 0.9, fontFace: F, fontSize: 16, color: RED, valign: "middle", margin: 0 });
  s.addText("Why that was the right call for this project", { x: 0.75, y: 3.0, w: 11.8, h: 0.4, fontFace: F, fontSize: 17, bold: true, color: TEAL, margin: 0 });
  bullets(s, [
    "It is a real workflow — in annotation-assist, the reviewer supplies the region",
    "It isolates segmentation quality from localization error, so the number measures one thing",
    "That constraint IS the whole-box breakthrough — the fix for over-prediction came from it",
    "Not ignored: I built and evaluated the autonomous version, with a millimetre-level containment audit",
  ], { y: 3.5, w: 11.7, fontSize: 15.5, lineSpacing: 28 });
  foot(s, 18, "Results & limits");
  s.addNotes("[RIFF] Own it first, then justify. Emphasise: this was a scoped decision, tested, not an oversight.");
}

// ---- S19 limitation 2 ----
{
  const s = base("Limitation: specificity is low", "Honest limits");
  card(s, 0.75, 1.9, 11.75, 0.9, PANEL_HI);
  s.addText("It over-calls on healthy scans — 17% specificity is the weakest number in the project.",
    { x: 1.1, y: 1.9, w: 11.1, h: 0.9, fontFace: F, fontSize: 16, color: RED, valign: "middle", margin: 0 });
  s.addText("Deliberately deprioritised — and worked, not forgotten", { x: 0.75, y: 3.0, w: 11.8, h: 0.4, fontFace: F, fontSize: 17, bold: true, color: TEAL, margin: 0 });
  bullets(s, [
    "For a CADe tool, a missed tumor costs more than a false alarm — detection came first",
    "Four documented attempts: sampling ratio, loss function, an anatomical constraint, more healthy data",
    "The model can discriminate — patient-level AUC 0.80 — so it is a threshold problem, not blindness",
    "The honest conclusion: it needs a decision layer in front of it, not a more timid segmenter",
  ], { y: 3.5, w: 11.7, fontSize: 15.5, lineSpacing: 28 });
  foot(s, 19, "Results & limits");
  s.addNotes("[RIFF] The AUC 0.80 line is the sophisticated point — the signal exists, the cut-off is misplaced. Retraining the segmenter to be timid made the outlines worse, which I measured.");
}

// ---- S20 where it fails ----
{
  const s = base("Where it fails, precisely", "Honest limits");
  const sizes = [
    ["Small  < 1 cm³", "0.067", "78% detected", RED],
    ["Medium  1–8 cm³", "0.512", "100% detected", AMBER],
    ["Large  > 8 cm³", "0.610", "100% detected", TEAL],
  ];
  let x = 0.75;
  sizes.forEach((z) => {
    card(s, x, 2.1, 3.85, 2.6);
    s.addText(z[0], { x: x + 0.3, y: 2.35, w: 3.25, h: 0.4, fontFace: F, fontSize: 15, color: MUTED, margin: 0 });
    s.addText(z[1], { x: x + 0.3, y: 2.8, w: 3.25, h: 0.85, fontFace: F, fontSize: 38, bold: true, color: z[3], margin: 0 });
    s.addText("lesion Dice  ·  " + z[2], { x: x + 0.3, y: 3.75, w: 3.25, h: 0.5, fontFace: F, fontSize: 13, color: SOFT, margin: 0 });
    x += 4.03;
  });
  card(s, 0.75, 5.0, 11.75, 1.25, PANEL_HI);
  s.addText("Small tumors are found but over-drawn — sometimes 25 to 50 times too large. The tool still surfaces them; the outline needs real editing.",
    { x: 1.1, y: 5.0, w: 11.1, h: 1.25, fontFace: F, fontSize: 15, color: SOFT, valign: "middle", margin: 0 });
  foot(s, 20, "Results & limits");
  s.addNotes("[RIFF] Size is the dominant driver. This one behaviour caps Dice AND drives the low specificity — two weaknesses, one cause.");
}

/* =====================================================================
   6 · REFLECTION  (3 min)
   ===================================================================== */

// ---- S21 week 1 takeaway ----
{
  const s = base("What I set out to learn", "Reflection");
  card(s, 0.75, 1.9, 11.75, 1.35, PANEL_HI);
  s.addText("“Learn to set up a 3D image processing pipeline end to end — and prove I can build something that holds up on real-world data.”",
    { x: 1.15, y: 1.9, w: 11.0, h: 1.35, fontFace: F, fontSize: 16, color: SOFT, italic: true, valign: "middle", margin: 0 });
  s.addText("Week 1 takeaway", { x: 1.15, y: 3.32, w: 4, h: 0.3, fontFace: F, fontSize: 12, color: MUTED, margin: 0 });
  const got = [
    ["The pipeline exists", "Indexing through training, evaluation, registry, endpoint, and interface", TEAL],
    ["2D → 3D taught me what changes", "Memory is the constraint; how you crop is a modelling decision, not preprocessing", BLUE],
    ["Real data was the part I underestimated", "Broken masks, wild geometry, four scanner makers — auditing WAS the work", AMBER],
  ];
  let y = 3.85;
  got.forEach((g, i) => {
    chip(s, 0.85, y + 0.14, String(i + 1), g[2]);
    s.addText(g[0], { x: 1.5, y, w: 4.3, h: 0.7, fontFace: F, fontSize: 15, bold: true, color: TEXT, valign: "middle", margin: 0 });
    s.addText(g[1], { x: 5.9, y, w: 6.5, h: 0.7, fontFace: F, fontSize: 13.5, color: SOFT, valign: "middle", margin: 0 });
    y += 0.82;
  });
  foot(s, 21, "Reflection");
  s.addNotes("[RIFF] Close the loop honestly. The 'thrilled if it flags cancer even modestly' line pairs well with 96% detection.");
}

// ---- S22 AI ----
{
  const s = base("How AI actually shaped the work", "Reflection");
  card(s, 0.75, 1.95, 5.65, 2.0);
  s.addText("What I planned", { x: 1.1, y: 2.2, w: 5, h: 0.4, fontFace: F, fontSize: 16, bold: true, color: MUTED, margin: 0 });
  s.addText("A coding accelerator and an explainer.", { x: 1.1, y: 2.7, w: 4.95, h: 0.9, fontFace: F, fontSize: 15, color: SOFT, margin: 0 });
  card(s, 6.85, 1.95, 5.65, 2.0, PANEL_HI);
  s.addText("What it became", { x: 7.2, y: 2.2, w: 5, h: 0.4, fontFace: F, fontSize: 16, bold: true, color: TEAL, margin: 0 });
  s.addText("An adversarial reviewer I stopped trusting by default.", { x: 7.2, y: 2.7, w: 4.95, h: 0.9, fontFace: F, fontSize: 15, color: SOFT, margin: 0 });
  bullets(s, [
    "The loop: write a spec → a second AI reviews the plan → write code → review the code → a regression test for every bug found",
    "It found my leakage bug — and it had also written that bug",
    "The consistent failure mode: AI is confident about data it has not inspected",
    "So the rule became: make it read the file and show me the output before it asserts anything",
  ], { y: 4.2, w: 11.7, fontSize: 15, lineSpacing: 27 });
  foot(s, 22, "Reflection");
  s.addNotes("[RIFF] Honest and non-defensive. Both facts are true: AI found the bug, AI wrote the bug.");
}

// ---- S23 more time ----
{
  const s = base("If I'd had more time", "Reflection");
  card(s, 0.75, 1.95, 11.75, 1.15, PANEL_HI);
  s.addText("These aren't regrets — they were deferred deliberately. I hit the goals I set for this project.",
    { x: 1.15, y: 1.95, w: 11.1, h: 1.15, fontFace: F, fontSize: 17, color: TEAL, valign: "middle", margin: 0 });
  const next = [
    ["Remove the provided region", "Let the system find the pancreas itself, so a raw scan goes in and a result comes out"],
    ["A decision layer for specificity", "The AUC says the signal is there — the fix is a gate in front of the model, not a timid model"],
    ["Train on all 9,000 scans", "Data scale was the only lever that consistently moved accuracy, and I never found its ceiling"],
  ];
  let y = 3.4;
  next.forEach((n, i) => {
    card(s, 0.75, y, 11.75, 0.95);
    chip(s, 1.1, y + 0.27, String(i + 1), TEAL);
    s.addText(n[0], { x: 1.75, y, w: 3.9, h: 0.95, fontFace: F, fontSize: 15, bold: true, color: TEXT, valign: "middle", margin: 0 });
    s.addText(n[1], { x: 5.75, y, w: 6.5, h: 0.95, fontFace: F, fontSize: 13.5, color: SOFT, valign: "middle", margin: 0 });
    y += 1.1;
  });
  foot(s, 23, "Reflection");
  s.addNotes("[TRANSIT] 30 seconds. Frame as deliberate scope, not regret. One line about carrying it into the capstone is enough.");
}

// ---- S24 close ----
{
  const s = pres.addSlide();
  s.background = { color: BG };
  s.addText("Where it landed", { x: 0.9, y: 1.6, w: 11.5, h: 0.7, fontFace: F, fontSize: 34, bold: true, color: TEXT, margin: 0 });
  const finals = [
    ["96%", "of tumors flagged for review", TEAL],
    ["0.474", "lesion Dice vs a ~0.53 benchmark", BLUE],
    ["901", "held-out scans, scored once", AMBER],
  ];
  let x = 0.9;
  finals.forEach((f) => {
    card(s, x, 2.6, 3.75, 2.0);
    stat(s, x, 2.95, 3.75, f[0], f[1], f[2]);
    x += 3.93;
  });
  s.addText("A working 3D pipeline, an honest evaluation, and a tool a radiologist could actually sit down with.",
    { x: 0.9, y: 5.0, w: 11.5, h: 0.5, fontFace: F, fontSize: 17, color: SOFT, margin: 0 });
  s.addText("Questions", { x: 0.9, y: 5.85, w: 11.5, h: 0.6, fontFace: F, fontSize: 26, bold: true, color: TEAL, margin: 0 });
  s.addNotes("[TRANSIT] Land it and stop. 10 minutes of Q&A follows — see the Q&A prep sheet.");
}

pres.writeFile({ fileName: "/sessions/gifted-clever-cannon/mnt/Neuro-data/week5/final-presentation.pptx" })
  .then((f) => console.log("wrote " + f));
