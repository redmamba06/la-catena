// Cache per usare l'app anche offline, più le notifiche. Cambia VERSION a ogni aggiornamento.
const VERSION = "la-catena-v8";
const STATE_CACHE = "la-catena-state"; // copia dello stato scritta dalla pagina, letta qui per comporre le notifiche
const CORE = ["./", "index.html", "manifest.webmanifest", "icon-192.png", "icon-512.png", "apple-touch-icon.png"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(CORE)).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys()
    .then(keys => Promise.all(keys.filter(k => k !== VERSION && k !== STATE_CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  if (e.request.method !== "GET") return;
  // rete prima (così prendi gli aggiornamenti), cache se sei offline
  e.respondWith(
    fetch(e.request).then(res => {
      if (res.ok && (e.request.url.startsWith(self.location.origin) || e.request.url.includes("fonts.g") || e.request.url.startsWith("https://cdn.jsdelivr.net/"))) {
        const copy = res.clone();
        caches.open(VERSION).then(c => c.put(e.request, copy));
      }
      return res;
    }).catch(() => caches.match(e.request).then(r => r || caches.match("index.html")))
  );
});

// ---- stessa logica della pagina per capire com'è andata la giornata ----
const pad = n => String(n).padStart(2, "0");
const keyOf = d => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const parse = k => { const [y, m, d] = k.split("-").map(Number); return new Date(y, m - 1, d); };
const addDays = (k, n) => { const d = parse(k); d.setDate(d.getDate() + n); return keyOf(d); };
const dow = k => (parse(k).getDay() + 6) % 7;
const fmtH = x => String(Math.round(x * 100) / 100).replace(".", ",");

function makeEval(st) {
  const rec = k => st.days[k] || {};
  const planFor = k => { let p = st.plans[0]; for (const q of st.plans) if (q.from <= k) p = q; return p; };
  const dayGoal = k => planFor(k).days[dow(k)];
  function evalDay(k) {
    const r = rec(k), g = dayGoal(k), missing = [];
    if (r.j) return { done: true, missing };
    const s = r.s || 0, p = r.p || 0;
    if (s < g.study) missing.push(`studio ${fmtH(g.study - s)} h`);
    if (g.lesson > 0 && r.l !== "si" && r.l !== "na") missing.push(r.l === "no" ? "lezione saltata" : "lezione da segnare");
    if (g.gym && !r.g) missing.push("palestra");
    if (p < g.pages) missing.push(`lettura ${g.pages - p} pagine`);
    return { done: missing.length === 0, missing };
  }
  function streakEnding(k) { let n = 0; while (k >= st.start && evalDay(k).done) { n++; k = addDays(k, -1); } return n; }
  return { dayGoal, evalDay, streakEnding };
}

function compose(kind, st) {
  if (!st || !Array.isArray(st.plans) || !st.plans.length) {
    return kind === "morning"
      ? { title: "La Catena", body: "Buongiorno. Apri l'app e guarda cosa c'è oggi." }
      : { title: "La Catena", body: "Sono le 20: hai chiuso la giornata? Apri l'app e segnala." };
  }
  const S = makeEval(st), t = keyOf(new Date()), y = addDays(t, -1);
  if (t < st.start) return { title: "Domani si parte", body: "Controlla la settimana tipo: da domani la catena conta." };
  const plural = n => `${n} ${n === 1 ? "giorno" : "giorni"}`;
  if (kind === "morning") {
    const evY = S.evalDay(y);
    if (y >= st.start && !evY.done) {
      const lost = S.streakEnding(addDays(y, -1));
      return {
        title: lost > 0 ? `Ieri hai buttato ${plural(lost)} di catena` : "Ieri non hai chiuso la giornata",
        body: `Mancava: ${evY.missing.join(", ")}. Oggi si riparte da zero.`,
      };
    }
    const g = S.dayGoal(t), c = S.streakEnding(y), parts = [];
    if (g.lesson > 0) parts.push(`lezione ${fmtH(g.lesson)} h`);
    if (g.study > 0) parts.push(`studio ${fmtH(g.study)} h`);
    if (g.gym) parts.push("palestra");
    if (g.pages > 0) parts.push(`${g.pages} pagine`);
    return {
      title: c > 0 ? `Catena a ${plural(c)}. Non spezzarla.` : "Buongiorno, oggi si comincia",
      body: parts.length ? `Oggi: ${parts.join(", ")}.` : "Oggi non hai niente in programma.",
    };
  }
  const ev = S.evalDay(t);
  if (ev.done) return { title: "Giornata chiusa ✓", body: `La catena è a ${plural(S.streakEnding(t))}.` };
  const c = S.streakEnding(y);
  return {
    title: c > 0 ? `Sono le 20: rischi ${plural(c)} di catena` : "Sono le 20 e la giornata è ancora aperta",
    body: `Manca: ${ev.missing.join(", ")}.`,
  };
}

async function loadState() {
  try { const r = await (await caches.open(STATE_CACHE)).match("state.json"); return r ? await r.json() : null; }
  catch (e) { return null; }
}
async function notify(kind, tag) {
  const m = compose(kind, await loadState());
  return self.registration.showNotification(m.title, { body: m.body, icon: "icon-192.png", badge: "icon-192.png", tag });
}

self.addEventListener("push", e => {
  let data = {};
  try { data = e.data.json() || {}; } catch (err) {}
  const kind = data.kind || "evening", tag = "la-catena-" + kind;
  // il server (Supabase) manda già titolo e testo; senza, li compone il telefono
  e.waitUntil(data.title
    ? self.registration.showNotification(data.title, { body: data.body, icon: "icon-192.png", badge: "icon-192.png", tag })
    : notify(kind, tag));
});
self.addEventListener("message", e => {
  if (e.data && e.data.type === "test") e.waitUntil(notify(e.data.kind || "evening", "la-catena-test"));
});
self.addEventListener("notificationclick", e => {
  e.notification.close();
  e.waitUntil(self.clients.matchAll({ type: "window", includeUncontrolled: true }).then(list => {
    for (const c of list) if ("focus" in c) return c.focus();
    return self.clients.openWindow("./");
  }));
});
