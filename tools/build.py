import sys, os, zlib, struct, math, json

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
html = open(src, encoding="utf-8").read()

SB_URL = "https://jthzincpedchogxnlzmi.supabase.co"
SB_KEY = "sb_publishable_bHLqSuhBA0m7VgCuhpItLA__-7Bd74r"
VAPID_PUBLIC = "BF3Nbd4uhJhlTFkMDPPOlXYopoh6vN13jxpPTk-scXD4zMVzYJljiw0F2qXxB9RnWglcOj9Vsc5O5JY-leHpRDQ"

def rep(old, new):
    global html
    assert html.count(old) == 1, old[:60]
    html = html.replace(old, new)

rep('<meta name="claude:viewport-fit-sides" content="cover">\n', "")
head_end = html.index("</style>") + len("</style>")
head, rest = html[:head_end], html[head_end:]
html = (
    '<!doctype html>\n<html lang="it">\n<head>\n'
    '<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
    '<meta name="theme-color" content="#EDEFF3" media="(prefers-color-scheme: light)">\n'
    '<meta name="theme-color" content="#0E1014" media="(prefers-color-scheme: dark)">\n'
    '<meta name="apple-mobile-web-app-capable" content="yes">\n'
    '<meta name="mobile-web-app-capable" content="yes">\n'
    '<meta name="apple-mobile-web-app-status-bar-style" content="default">\n'
    '<meta name="apple-mobile-web-app-title" content="La Catena">\n'
    '<link rel="manifest" href="manifest.webmanifest">\n'
    '<link rel="icon" type="image/png" href="icon-192.png">\n'
    '<link rel="apple-touch-icon" href="apple-touch-icon.png">\n'
    '<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.js"></script>\n'
    + head + '\n</head>\n<body>' + rest + '\n</body>\n</html>\n'
)

rep("* { box-sizing: border-box; }",
    "* { box-sizing: border-box; }\n"
    "html { -webkit-text-size-adjust: 100%; padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }\n"
    "body { margin: 0; min-height: 100vh; }\n"
    "[hidden] { display: none !important; }\n"
    ".backup { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }\n"
    ".backup button, .backup label { height: 46px; border-radius: 12px; border: 1.5px solid var(--line); background: var(--bg); font-weight: 600; font-size: 15px; display: flex; align-items: center; justify-content: center; cursor: pointer; }\n"
    ".backup input { position: absolute; width: 1px; height: 1px; opacity: 0; }\n"
    ".acct { display: flex; flex-direction: column; gap: 10px; }\n"
    ".acct input { height: 46px; border-radius: 12px; border: 1.5px solid var(--line); background: var(--bg); padding: 0 14px; font-size: 16px; }\n"
    ".acct .err { color: var(--bad); }\n"
    ".banner.info { background: var(--surface); border: 1.5px solid var(--accent); }\n"
    ".banner.info h2 { color: var(--accent); }")

rep("    try { localStorage.setItem(LS_KEY, JSON.stringify(state)); } catch (e) {}\n    if (!docRef) return;",
    "    state.savedAt = Date.now();\n"
    "    try { localStorage.setItem(LS_KEY, JSON.stringify(state)); } catch (e) {}\n"
    "    mirror(); cloudSave();\n"
    "    if (!docRef) return;")

rep('<div id="banners" style="display:flex;flex-direction:column;gap:10px"></div>',
    '<div id="banners" style="display:flex;flex-direction:column;gap:10px"></div>\n  <div id="acct-banner-box"></div>')

rep('  <p class="foot" id="sync">Caricamento…</p>',
    '  <section class="card" id="account">\n'
    '    <div class="card-h"><h2>Account</h2></div>\n'
    '    <form class="acct" id="login-form" hidden>\n'
    '      <p class="note">Entra per salvare i dati online: non li perdi se cancelli l\'app o cambi telefono.</p>\n'
    '      <input id="login-email" type="email" autocomplete="username" inputmode="email" placeholder="Email" aria-label="Email" required>\n'
    '      <input id="login-pass" type="password" autocomplete="current-password" placeholder="Password (almeno 8 caratteri)" aria-label="Password" minlength="8" required>\n'
    '      <div class="backup"><button type="submit" id="login-in">Entra</button><button type="button" id="login-new">Crea account</button></div>\n'
    '      <p class="note err" id="login-msg" hidden></p>\n'
    '    </form>\n'
    '    <div class="acct" id="logged" hidden>\n'
    '      <p class="note">Collegato come <b id="logged-email"></b>. I dati si salvano online da soli.</p>\n'
    '      <button class="linkbtn" id="logout" style="align-self:flex-start">Esci</button>\n'
    '    </div>\n'
    '  </section>\n\n'
    '  <section class="card">\n'
    '    <div class="card-h"><h2>Notifiche</h2></div>\n'
    '    <p class="note">Alle 8 ti dico cosa hai in programma (o com\'è andata ieri), alle 20 cosa ti manca per chiudere la giornata.</p>\n'
    '    <button class="btn-main" id="notif-btn" hidden>Attiva notifiche</button>\n'
    '    <p class="note" id="notif-msg" hidden></p>\n'
    '    <div class="backup" id="notif-on" hidden><button id="notif-test">Notifica di prova</button><button id="notif-off">Disattiva</button></div>\n'
    '  </section>\n\n'
    '  <section class="card">\n'
    '    <div class="card-h"><h2>Backup</h2></div>\n'
    '    <p class="note">Una copia dei tuoi dati in un file, da tenere per sicurezza.</p>\n'
    '    <div class="backup">\n'
    '      <button id="export">Esporta backup</button>\n'
    '      <label for="import">Importa backup</label>\n'
    '      <input id="import" type="file" accept="application/json,.json">\n'
    '    </div>\n'
    '    <p class="note" id="backup-msg" hidden></p>\n'
    '  </section>\n\n'
    '  <p class="foot" id="sync">Caricamento…</p>')

rep('''  let tries = 0;
  (function waitClaude() {
    if (window.claude && typeof claude.use === "function") connect();
    else if (++tries < 20) setTimeout(waitClaude, 150);
    else setSync("Salvato solo in questo browser");
  })();''',
'''  // ---- versione installabile ----
  if (navigator.storage && navigator.storage.persist) navigator.storage.persist().catch(() => {});
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});

  const msg = t => { const m = document.getElementById("backup-msg"); m.textContent = t; m.hidden = false; };
  document.getElementById("export").onclick = () => {
    const blob = new Blob([JSON.stringify(state, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `la-catena-backup-${todayKey()}.json`;
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
    msg("Backup esportato. Salvalo in File o mandalo a te stesso.");
  };
  document.getElementById("import").onchange = async e => {
    const f = e.target.files[0]; e.target.value = "";
    if (!f) return;
    try {
      const data = JSON.parse(await f.text());
      if (!data || typeof data.days !== "object") throw new Error("formato");
      state = hydrate(data); save(); todayBuiltFor = null; refresh();
      msg(`Backup importato: ${Object.keys(state.days).length} giorni.`);
    } catch (err) { msg("Questo file non è un backup di La Catena."); }
  };

  // copia dello stato per il service worker (notifiche di prova offline)
  function mirror() {
    if (!("caches" in window)) return;
    const body = JSON.stringify(state);
    caches.open("la-catena-state").then(c => c.put("state.json", new Response(body, { headers: { "content-type": "application/json" } }))).catch(() => {});
  }
  mirror();

  // ---- account Supabase: dati online, ultimo salvataggio vince ----
  const sb = window.supabase ? window.supabase.createClient("__SB_URL__", "__SB_KEY__", { auth: { persistSession: true, autoRefreshToken: true, storageKey: "la-catena-auth" } }) : null;
  let sbUser = null, cloudTimer = null, cloudBusy = false, cloudAgain = false;
  const tz = (() => { try { return Intl.DateTimeFormat().resolvedOptions().timeZone || "Europe/Rome"; } catch (e) { return "Europe/Rome"; } })();

  function cloudSave() {
    if (!sbUser) return;
    clearTimeout(cloudTimer);
    cloudTimer = setTimeout(cloudFlush, 800);
  }
  async function cloudFlush() {
    if (!sbUser) return;
    if (cloudBusy) { cloudAgain = true; return; }
    cloudBusy = true;
    const { error } = await sb.from("trackers").upsert({ user_id: sbUser.id, state, saved_at: state.savedAt || Date.now(), tz, updated_at: new Date().toISOString() });
    cloudBusy = false;
    setSync(error ? "Non salvato online (sei offline?). Riprovo al prossimo cambiamento." : "Salvato online");
    if (cloudAgain) { cloudAgain = false; cloudFlush(); }
  }
  function useRemote(remote) {
    state = hydrate(remote);
    try { localStorage.setItem(LS_KEY, JSON.stringify(state)); } catch (e) {}
    mirror(); todayBuiltFor = null; refresh();
  }
  async function cloudPull() {
    if (!sbUser) return;
    const { data, error } = await sb.from("trackers").select("state, saved_at").eq("user_id", sbUser.id).maybeSingle();
    if (error) { setSync("Offline: salvato su questo telefono"); return; }
    if (!data) { state.syncUser = sbUser.id; save(); return; }  // primo accesso: carica i dati di questo telefono
    if (state.syncUser !== sbUser.id) {
      // primo accesso da questo telefono con un account che ha già dati: unisce i giorni segnati qui
      const m = hydrate(data.state);
      for (const [k, v] of Object.entries(state.days || {})) if (!m.days[k]) m.days[k] = v;
      if (state.start < m.start && Object.keys(state.days || {}).length) m.start = state.start;
      m.syncUser = sbUser.id;
      useRemote(m); save();
      return;
    }
    if ((data.saved_at || 0) > (state.savedAt || 0)) { useRemote(data.state); setSync("Aggiornato dal tuo account"); }
    else if ((data.saved_at || 0) < (state.savedAt || 0)) cloudFlush();
    else setSync("Salvato online");
  }

  const loginForm = document.getElementById("login-form"), logged = document.getElementById("logged");
  const loginMsg = t => { const m = document.getElementById("login-msg"); m.textContent = t; m.hidden = !t; };
  function renderAccount() {
    loginForm.hidden = !!sbUser || !sb;
    logged.hidden = !sbUser;
    if (sbUser) document.getElementById("logged-email").textContent = sbUser.email || "";
    if (!sb) setSync("Salvato su questo telefono (servizio online non raggiungibile)");
    else if (!sbUser) setSync("Salvato solo su questo telefono: entra nell'account per salvarlo online");
    renderAccountBanner();
    renderNotif().catch(() => {});
  }
  function renderAccountBanner() {
    const box = document.getElementById("acct-banner-box");
    const old = document.getElementById("acct-banner");
    if (old) old.remove();
    if (!sb || sbUser) return;
    const b = el("div", "banner info"); b.id = "acct-banner";
    b.append(el("h2", null, "Salva i dati sul tuo account"), el("p", null, "Così non li perdi se cancelli l'app o cambi telefono, e ricevi le notifiche puntuali."));
    const go = el("button", null, "Entra o crea l'account");
    go.onclick = () => { document.getElementById("account").scrollIntoView({ behavior: "smooth" }); document.getElementById("login-email").focus(); };
    b.append(go); box.append(b);
  }
  const authError = e => {
    const m = (e && e.message || "").toLowerCase();
    if (m.includes("invalid login")) return "Email o password sbagliate.";
    if (m.includes("already registered") || m.includes("already been registered")) return "Questa email ha già un account: tocca Entra.";
    if (m.includes("password")) return "La password deve avere almeno 8 caratteri.";
    if (m.includes("signups not allowed") || m.includes("signup is disabled")) return "La creazione di nuovi account è chiusa. Tocca Entra con il tuo account.";
    if (m.includes("rate limit")) return "Troppi tentativi: riprova tra qualche minuto.";
    return "Non riesco a collegarmi. Controlla la connessione e riprova.";
  };
  async function doAuth(create) {
    const email = document.getElementById("login-email").value.trim(), password = document.getElementById("login-pass").value;
    if (!email || password.length < 8) { loginMsg("Scrivi l'email e una password di almeno 8 caratteri."); return; }
    loginMsg("");
    const { data, error } = create ? await sb.auth.signUp({ email, password }) : await sb.auth.signInWithPassword({ email, password });
    if (error) { loginMsg(authError(error)); return; }
    if (create && !data.session) { loginMsg("Account creato: tocca Entra."); return; }
  }
  if (sb) {
    loginForm.addEventListener("submit", e => { e.preventDefault(); doAuth(false); });
    document.getElementById("login-new").onclick = () => doAuth(true);
    document.getElementById("logout").onclick = async () => { await sb.auth.signOut(); };
    sb.auth.onAuthStateChange((event, session) => {
      const u = session ? session.user : null;
      const changed = (u && u.id) !== (sbUser && sbUser.id);
      sbUser = u;
      if (changed) { renderAccount(); if (sbUser) cloudPull(); }
    });
    document.addEventListener("visibilitychange", () => { if (!document.hidden) cloudPull(); });
  }

  // ---- notifiche push: l'iscrizione del telefono va nel tuo account ----
  const VAPID_PUBLIC = "__VAPID_PUBLIC__";
  const nBtn = document.getElementById("notif-btn"), nOn = document.getElementById("notif-on"), nMsg = document.getElementById("notif-msg");
  const nNote = t => { nMsg.textContent = t; nMsg.hidden = !t; };
  const keyBytes = b64 => {
    const s = atob((b64 + "=".repeat((4 - b64.length % 4) % 4)).replace(/-/g, "+").replace(/_/g, "/"));
    return Uint8Array.from(s, ch => ch.charCodeAt(0));
  };
  const standalone = matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;
  const saveSub = sub => sb.from("push_subscriptions").upsert({ endpoint: sub.endpoint, user_id: sbUser.id, subscription: sub.toJSON() });
  async function renderNotif() {
    nBtn.hidden = true; nOn.hidden = true; nNote("");
    if (!("serviceWorker" in navigator) || !("PushManager" in window) || !("Notification" in window)) {
      const ios = /iPhone|iPad|iPod/.test(navigator.userAgent);
      nNote(ios && !standalone
        ? "Su iPhone le notifiche funzionano solo dall'app sulla schermata Home: aggiungila con Condividi → Aggiungi alla schermata Home e aprila da lì."
        : "Questo browser non supporta le notifiche.");
      return;
    }
    if (!sbUser) { nNote("Entra nel tuo account (qui sopra) per attivarle."); return; }
    if (Notification.permission === "denied") { nNote("Hai bloccato le notifiche. Riattivale nelle impostazioni del telefono, alla voce Notifiche → La Catena."); return; }
    const reg = await navigator.serviceWorker.ready;
    const sub = await reg.pushManager.getSubscription();
    if (sub && Notification.permission === "granted") {
      const { error } = await saveSub(sub);
      nNote(error ? "Notifiche attive sul telefono, ma non riesco a registrarle online. Riapri l'app con internet." : "Notifiche attive: alle 8 e alle 20.");
      nOn.hidden = false;
    } else nBtn.hidden = false;
  }
  nBtn.onclick = async () => {
    try {
      const perm = await Notification.requestPermission();
      if (perm === "granted") {
        const reg = await navigator.serviceWorker.ready;
        await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: keyBytes(VAPID_PUBLIC) });
      }
    } catch (e) { nNote("Attivazione non riuscita. Riprova dall'app sulla schermata Home."); return; }
    renderNotif();
  };
  document.getElementById("notif-test").onclick = async () => {
    nNote("Invio in corso…");
    await cloudFlush();
    const { data, error } = await sb.functions.invoke("notify", { body: { test: true, kind: new Date().getHours() < 14 ? "morning" : "evening" } });
    nNote(error ? "Invio non riuscito. Controlla la connessione e riprova." : data && data.sent ? "Inviata: arriva tra qualche secondo." : "Nessun telefono registrato: tocca Disattiva e poi riattivale.");
  };
  document.getElementById("notif-off").onclick = async () => {
    const reg = await navigator.serviceWorker.ready;
    const sub = await reg.pushManager.getSubscription();
    if (sub) { await sb.from("push_subscriptions").delete().eq("endpoint", sub.endpoint); await sub.unsubscribe(); }
    renderNotif();
  };
  renderAccount();''')

html = html.replace("__SB_URL__", SB_URL).replace("__SB_KEY__", SB_KEY).replace("__VAPID_PUBLIC__", VAPID_PUBLIC)

open(os.path.join(out, "index.html"), "w", encoding="utf-8").write(html)

json.dump({
    "name": "La Catena",
    "short_name": "La Catena",
    "description": "Studio, lezioni, palestra e lettura: non spezzare la catena.",
    "lang": "it",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "background_color": "#EDEFF3",
    "theme_color": "#2A44E8",
    "icons": [
        {"src": "icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
    ],
}, open(os.path.join(out, "manifest.webmanifest"), "w"), indent=2)

# sw.js è mantenuto a mano nella cartella dell'app

# ---- icone: due anelli di catena bianchi su blu cobalto, PNG scritto a mano ----
def png(path, size):
    bg, fg = (42, 68, 232), (255, 255, 255)
    ss = 3
    R, w = 0.20 * size, 0.065 * size
    c1, c2 = (0.385 * size, 0.5 * size), (0.615 * size, 0.5 * size)
    rows = []
    for y in range(size):
        row = bytearray([0])
        for x in range(size):
            hit = 0
            for sy in range(ss):
                for sx in range(ss):
                    px, py = x + (sx + .5) / ss, y + (sy + .5) / ss
                    for cx, cy in (c1, c2):
                        d = math.hypot(px - cx, py - cy)
                        if abs(d - R) <= w / 2:
                            hit += 1; break
            a = hit / (ss * ss)
            row += bytes(round(bg[i] + (fg[i] - bg[i]) * a) for i in range(3))
        rows.append(bytes(row))
    raw = zlib.compress(b"".join(rows), 9)
    chunk = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)) + chunk(b"IDAT", raw) + chunk(b"IEND", b"")
    open(path, "wb").write(data)

png(os.path.join(out, "icon-192.png"), 192)
png(os.path.join(out, "icon-512.png"), 512)
png(os.path.join(out, "apple-touch-icon.png"), 180)
print("ok")
