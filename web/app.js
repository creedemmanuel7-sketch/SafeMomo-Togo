/* SafeMomo — logique d'écran seulement.
   Le verdict vient du serveur (server.py → analyzer.py → Gemma 4).
   Ici : prendre la photo, l'envoyer, afficher la phrase, la lire, ouvrir WhatsApp.
   Aucune règle de fraude dans ce fichier. */
"use strict";

// ---------- Libellés visibles ----------
const TEXTS = {
  pillDanger: "DANGER",
  pillCheck: "VÉRIFIE QUAND MÊME",
  listen: "Écouter",
  listenStop: "Arrêter la lecture",
  listenMissing: "Voix indisponible sur ce téléphone",
  score: (n) => `Repère pour le jury : ${n} / 100`,
  serverOk: "Serveur SafeMomo joignable",
  serverKey: "Serveur SafeMomo joignable · clé déjà réglée",
  serverKo: "Serveur SafeMomo injoignable",
  keyFromServer: "Le serveur a déjà sa clé. Laisse vide.",
  keyLocal: "Gardée seulement sur ce téléphone.",
  lastError: (t) => `Dernier souci technique : ${t}`,
};

const SCENES = {
  boutique: "Le client est devant toi",
  famille: "Quelqu'un demande de renvoyer l'argent",
  autre: "Message à vérifier",
};

const ERRORS = {
  network: {
    title: "Je n'arrive pas à joindre SafeMomo.",
    text: "Vérifie que le téléphone est sur le même Wi-Fi que l'ordinateur. Ne donne rien en attendant.",
    action: "Réessayer",
  },
  no_key: {
    title: "SafeMomo n'est pas encore réglé.",
    text: "Ouvre le menu Équipe pour ajouter la clé, ou active le mode démo.",
    action: "Ouvrir le menu Équipe",
  },
  bad_image: {
    title: "Je ne vois pas bien cette photo.",
    text: "Reprends la photo bien en face, sans reflet, avec tout le message.",
    action: "Reprendre la photo",
  },
  analysis: {
    title: "Je n'ai pas pu regarder la photo.",
    text: "Le réseau ou le service a coupé. Ne donne rien en attendant, et réessaie.",
    action: "Réessayer",
  },
};

const CODE = "*145#";
const DEMO_DELAY_MS = 1200; // le temps de voir l'écran d'attente pendant la démo
const TIMEOUT_MS = 60000;
const MAX_EDGE = 1600; // on réduit la photo avant l'envoi : plus rapide sur le Wi-Fi

// ---------- Petits outils ----------
const $ = (id) => document.getElementById(id);
const store = {
  get(key, fallback = "") {
    try { const v = localStorage.getItem("safemomo." + key); return v === null ? fallback : v; } catch { return fallback; }
  },
  set(key, value) {
    try { localStorage.setItem("safemomo." + key, value); } catch { /* stockage indisponible : on continue */ }
  },
};

// ---------- État ----------
const state = {
  blob: null,        // photo prête à envoyer
  previewUrl: null,  // URL locale pour l'aperçu
  controller: null,  // pour Annuler
  verdict: null,
  config: null,
};

const SCREENS = ["empty", "ready", "waiting", "verdict", "error"];
function show(name) {
  for (const s of SCREENS) $("screen-" + s).hidden = s !== name;
  window.scrollTo(0, 0);
  if (name !== "verdict") stopSpeaking();
}

// ---------- Photo ----------
async function prepareImage(file) {
  // Réduction côté téléphone : même image, moins d'octets. Gemma reçoit l'image dans analyzer.py.
  try {
    const bitmap = await createImageBitmap(file, { imageOrientation: "from-image" });
    const scale = Math.min(1, MAX_EDGE / Math.max(bitmap.width, bitmap.height));
    if (scale === 1 && file.size < 2_500_000) { bitmap.close?.(); return file; }
    const canvas = document.createElement("canvas");
    canvas.width = Math.round(bitmap.width * scale);
    canvas.height = Math.round(bitmap.height * scale);
    canvas.getContext("2d").drawImage(bitmap, 0, 0, canvas.width, canvas.height);
    bitmap.close?.();
    const out = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.9));
    return out || file;
  } catch {
    return file; // navigateur ancien : on envoie la photo telle quelle
  }
}

function setPhoto(blob) {
  if (state.previewUrl) URL.revokeObjectURL(state.previewUrl);
  state.blob = blob;
  state.previewUrl = URL.createObjectURL(blob);
  for (const id of ["preview-ready", "preview-waiting", "preview-error"]) $(id).src = state.previewUrl;
  state.verdict = null;
  show("ready");
}

async function onFileChosen(event) {
  const file = event.target.files && event.target.files[0];
  event.target.value = ""; // permet de reprendre la même photo
  if (!file) return;
  if (!file.type.startsWith("image/")) { showError("bad_image"); return; }
  setPhoto(await prepareImage(file));
}

async function useSample() {
  try {
    const res = await fetch("samples/fake_tmoney_sample.png", { cache: "force-cache" });
    if (!res.ok) throw new Error("absent");
    setPhoto(await res.blob());
  } catch {
    showError("network");
  }
}

function reset() {
  abortScan();
  state.verdict = null;
  show("empty");
}

// ---------- Analyse ----------
function demoMode() { return $("team-demo").checked; }

async function scan() {
  if (!state.blob) { show("empty"); return; }
  show("waiting");
  const controller = new AbortController();
  state.controller = controller;
  const timer = setTimeout(() => controller.abort("timeout"), TIMEOUT_MS);

  try {
    if (demoMode()) {
      await wait(DEMO_DELAY_MS, controller.signal);
      renderVerdict(await getDemoVerdict(controller.signal), true);
      return;
    }
    const headers = { "Content-Type": state.blob.type || "image/jpeg" };
    const key = $("team-key").value.trim();
    if (key) headers["X-Api-Key"] = key;
    headers["X-Model"] = $("team-model").value;

    const res = await fetch("api/analyze", { method: "POST", body: state.blob, headers, signal: controller.signal });
    let data = null;
    try { data = await res.json(); } catch { /* réponse vide */ }
    if (!res.ok || !data || !data.verdict) {
      const kind = data && data.error && data.error.kind;
      rememberTechError(data && data.error ? data.error.detail : `HTTP ${res.status}`);
      showError(ERRORS[kind] ? kind : "analysis");
      return;
    }
    renderVerdict(data.verdict, Boolean(data.demo));
  } catch (err) {
    if (controller.signal.aborted && controller.signal.reason === "cancel") return; // Annuler : déjà revenu en arrière
    if (controller.signal.aborted) { rememberTechError("délai dépassé"); showError("analysis"); return; }
    rememberTechError(String(err && err.message || err));
    showError("network");
  } finally {
    clearTimeout(timer);
    if (state.controller === controller) state.controller = null;
  }
}

function abortScan() {
  if (state.controller) state.controller.abort("cancel");
  state.controller = null;
}

function wait(ms, signal) {
  return new Promise((resolve, reject) => {
    const t = setTimeout(resolve, ms);
    signal.addEventListener("abort", () => { clearTimeout(t); reject(new Error("abort")); }, { once: true });
  });
}

async function getDemoVerdict(signal) {
  // demo_verdict() vit dans analyzer.py ; on garde sa dernière réponse pour une démo sans aucun réseau.
  try {
    const res = await fetch("api/demo", { signal, cache: "no-store" });
    const data = await res.json();
    store.set("demoVerdict", JSON.stringify(data.verdict));
    return data.verdict;
  } catch (err) {
    if (signal.aborted) throw err;
    const cached = store.get("demoVerdict");
    if (cached) return JSON.parse(cached);
    throw err;
  }
}

// ---------- Verdict ----------
function fillWithCode(el, text) {
  // Écrit la phrase sans HTML, et garde *145# insécable.
  el.textContent = "";
  const parts = String(text).split(CODE);
  parts.forEach((part, i) => {
    el.append(document.createTextNode(part));
    if (i < parts.length - 1) {
      const span = document.createElement("span");
      span.className = "code";
      span.textContent = CODE;
      el.append(span);
    }
  });
}

function renderVerdict(v, demo) {
  state.verdict = v;
  const danger = v.is_scam === true;
  const card = $("card");
  card.className = "card " + (danger ? "card-danger" : "card-check");
  card.setAttribute("aria-live", danger ? "assertive" : "polite");
  $("pill-text").textContent = danger ? TEXTS.pillDanger : TEXTS.pillCheck;
  $("scene").textContent = SCENES[v.scene] || SCENES.autre;
  fillWithCode($("sentence"), v.spoken_sentence);
  $("demo-line").hidden = !demo;

  $("btn-whatsapp").href = "https://wa.me/?text=" + encodeURIComponent(v.whatsapp_alert || v.spoken_sentence);

  // Voir pourquoi : fermé à chaque nouveau verdict.
  $("why").open = false;
  $("why-title").textContent = v.verdict_title || "";
  fillWithCode($("why-sender"), v.sender_analysis || "");
  const list = $("why-flags");
  list.textContent = "";
  for (const flag of v.red_flags || []) {
    const li = document.createElement("li");
    fillWithCode(li, flag);
    list.append(li);
  }
  $("why-flags-block").hidden = !(v.red_flags && v.red_flags.length);
  fillWithCode($("why-advice"), v.plain_advice || "");
  $("why-score").textContent = TEXTS.score(v.risk_score);

  show("verdict");
  $("sentence").focus({ preventScroll: true });
  if (navigator.vibrate && danger) navigator.vibrate([120, 80, 120]);
}

// ---------- Voix ----------
const synth = "speechSynthesis" in window ? window.speechSynthesis : null;
let frenchVoice = null;
function pickVoice() {
  if (!synth) return;
  const voices = synth.getVoices();
  frenchVoice = voices.find((v) => v.lang === "fr-FR") || voices.find((v) => v.lang && v.lang.startsWith("fr")) || null;
}
if (synth) { pickVoice(); synth.addEventListener?.("voiceschanged", pickVoice); }

function setListening(on) {
  $("btn-listen").setAttribute("aria-pressed", on ? "true" : "false");
  $("listen-text").textContent = on ? TEXTS.listenStop : TEXTS.listen;
}

function stopSpeaking() {
  if (synth) synth.cancel();
  setListening(false);
}

function speak() {
  if (!synth || !state.verdict) return;
  if ($("btn-listen").getAttribute("aria-pressed") === "true") { stopSpeaking(); return; }
  synth.cancel();
  const utterance = new SpeechSynthesisUtterance(state.verdict.spoken_sentence);
  utterance.lang = "fr-FR";
  if (frenchVoice) utterance.voice = frenchVoice;
  utterance.rate = 0.92;
  utterance.onend = utterance.onerror = () => setListening(false);
  setListening(true);
  synth.speak(utterance);
}

// ---------- Erreurs ----------
let errorKind = "analysis";
function showError(kind) {
  errorKind = ERRORS[kind] ? kind : "analysis";
  const e = ERRORS[errorKind];
  $("error-title").textContent = e.title;
  $("error-text").textContent = e.text;
  $("error-action-text").textContent = e.action;
  document.querySelector("#screen-error .photo").hidden = !state.blob;
  show("error");
}

function onErrorAction() {
  if (errorKind === "no_key") { openTeam(); return; }
  if (errorKind === "bad_image") { reset(); $("input-camera").click(); return; }
  if (state.blob) scan(); else reset();
}

function rememberTechError(text) {
  const el = $("team-last-error");
  el.textContent = TEXTS.lastError(text);
  el.hidden = false;
}

// ---------- Menu Équipe ----------
function openTeam() {
  const dialog = $("team");
  if (typeof dialog.showModal === "function") dialog.showModal();
  else dialog.setAttribute("open", "");
}

async function loadConfig() {
  const status = $("team-status");
  try {
    const res = await fetch("api/config", { cache: "no-store" });
    const cfg = await res.json();
    state.config = cfg;
    const select = $("team-model");
    select.textContent = "";
    for (const m of cfg.models) {
      const opt = document.createElement("option");
      opt.value = m.id;
      opt.textContent = m.label;
      select.append(opt);
    }
    select.value = store.get("model", cfg.default_model) || cfg.default_model;
    if (!select.value) select.value = cfg.default_model;
    status.className = "status ok";
    $("team-status-text").textContent = cfg.server_key ? TEXTS.serverKey : TEXTS.serverOk;
    $("team-key-note").textContent = cfg.server_key ? TEXTS.keyFromServer : TEXTS.keyLocal;
    getDemoVerdict(new AbortController().signal).catch(() => {}); // garde la phrase de démo en réserve
  } catch {
    status.className = "status ko";
    $("team-status-text").textContent = TEXTS.serverKo;
  }
}

function initTeam() {
  $("team-key").value = store.get("apiKey");
  $("team-demo").checked = store.get("demo") === "1";
  $("team-key").addEventListener("change", (e) => store.set("apiKey", e.target.value.trim()));
  $("team-model").addEventListener("change", (e) => store.set("model", e.target.value));
  $("team-demo").addEventListener("change", (e) => store.set("demo", e.target.checked ? "1" : "0"));
  $("team").addEventListener("click", (e) => { if (e.target === $("team")) $("team").close(); }); // toucher le fond ferme
}

// ---------- Branchements ----------
function init() {
  $("input-camera").addEventListener("change", onFileChosen);
  $("input-gallery").addEventListener("change", onFileChosen);
  $("btn-sample").addEventListener("click", useSample);
  $("btn-scan").addEventListener("click", scan);
  $("btn-cancel").addEventListener("click", () => { abortScan(); show(state.blob ? "ready" : "empty"); });
  $("btn-listen").addEventListener("click", speak);
  $("btn-error-action").addEventListener("click", onErrorAction);
  $("open-team").addEventListener("click", openTeam);
  document.querySelectorAll("[data-action='reset']").forEach((b) => b.addEventListener("click", reset));

  if (!synth) {
    $("btn-listen").disabled = true;
    $("listen-text").textContent = TEXTS.listenMissing;
  }

  initTeam();
  loadConfig();

  if ("serviceWorker" in navigator && window.isSecureContext) {
    navigator.serviceWorker.register("sw.js").catch(() => {});
  }
  show("empty");
}

init();
