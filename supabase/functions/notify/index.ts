// Notifiche di La Catena.
// - Chiamata ogni ora da pg_cron (body {}): per ogni account, se nel suo fuso sono le 8 o le 20,
//   manda la notifica del mattino o della sera, una sola volta al giorno.
// - Chiamata dall'app con {test: true} e il token dell'utente: manda subito una notifica di prova.
import webpush from "npm:web-push@3.6.7";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const admin = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, {
  auth: { persistSession: false },
});
webpush.setVapidDetails(
  "https://redmamba06.github.io/la-catena/",
  Deno.env.get("VAPID_PUBLIC_KEY")!,
  Deno.env.get("VAPID_PRIVATE_KEY")!,
);

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info",
};
const json = (data: unknown, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { ...cors, "Content-Type": "application/json" } });

// ---- date nel fuso dell'utente, chiavi YYYY-MM-DD ----
type Kind = "morning" | "evening";
const pad = (n: number) => String(n).padStart(2, "0");
function localNow(tz: string) {
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("en-GB", { timeZone: tz, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", hourCycle: "h23" })
      .formatToParts(new Date()).map((p) => [p.type, p.value]),
  );
  return { today: `${parts.year}-${parts.month}-${parts.day}`, hour: Number(parts.hour) };
}
const toUTC = (k: string) => { const [y, m, d] = k.split("-").map(Number); return new Date(Date.UTC(y, m - 1, d)); };
const addDays = (k: string, n: number) => {
  const d = toUTC(k); d.setUTCDate(d.getUTCDate() + n);
  return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())}`;
};
const dow = (k: string) => (toUTC(k).getUTCDay() + 6) % 7;
const fmtH = (x: number) => String(Math.round(x * 100) / 100).replace(".", ",");

// ---- stessa logica dell'app per capire com'è andata la giornata ----
// deno-lint-ignore no-explicit-any
type State = any;
function makeEval(st: State) {
  const rec = (k: string) => st.days?.[k] || {};
  const planFor = (k: string) => { let p = st.plans[0]; for (const q of st.plans) if (q.from <= k) p = q; return p; };
  const dayGoal = (k: string) => planFor(k).days[dow(k)];
  function evalDay(k: string) {
    const r = rec(k), g = dayGoal(k), missing: string[] = [];
    if (r.j) return { done: true, missing };
    const s = r.s || 0, p = r.p || 0;
    if (s < g.study) missing.push(`studio ${fmtH(g.study - s)} h`);
    if (g.lesson > 0 && r.l !== "si" && r.l !== "na") missing.push(r.l === "no" ? "lezione saltata" : "lezione da segnare");
    if (g.gym && !r.g) missing.push("palestra");
    if (p < g.pages) missing.push(`lettura ${g.pages - p} pagine`);
    return { done: missing.length === 0, missing };
  }
  function streakEnding(k: string) { let n = 0; while (k >= st.start && evalDay(k).done) { n++; k = addDays(k, -1); } return n; }
  return { dayGoal, evalDay, streakEnding };
}

function compose(kind: Kind, st: State, t: string) {
  if (!st || !Array.isArray(st.plans) || !st.plans.length) {
    return kind === "morning"
      ? { title: "La Catena", body: "Buongiorno. Apri l'app e guarda cosa c'è oggi." }
      : { title: "La Catena", body: "Sono le 20: hai chiuso la giornata? Apri l'app e segnala." };
  }
  const S = makeEval(st), y = addDays(t, -1);
  if (t < st.start) return { title: "Domani si parte", body: "Controlla la settimana tipo: da domani la catena conta." };
  const plural = (n: number) => `${n} ${n === 1 ? "giorno" : "giorni"}`;
  if (kind === "morning") {
    const evY = S.evalDay(y);
    if (y >= st.start && !evY.done) {
      const lost = S.streakEnding(addDays(y, -1));
      return {
        title: lost > 0 ? `Ieri hai buttato ${plural(lost)} di catena` : "Ieri non hai chiuso la giornata",
        body: `Mancava: ${evY.missing.join(", ")}. Oggi si riparte da zero.`,
      };
    }
    const g = S.dayGoal(t), c = S.streakEnding(y), parts: string[] = [];
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

async function sendTo(userId: string, kind: Kind, msg: { title: string; body: string }) {
  const { data: subs } = await admin.from("push_subscriptions").select("endpoint, subscription").eq("user_id", userId);
  let sent = 0;
  for (const s of subs ?? []) {
    try {
      await webpush.sendNotification(s.subscription, JSON.stringify({ kind, ...msg }), { TTL: 3600, urgency: "high" });
      sent++;
    } catch (e) {
      const code = (e as { statusCode?: number }).statusCode;
      if (code === 404 || code === 410) await admin.from("push_subscriptions").delete().eq("endpoint", s.endpoint);
      else console.error("invio non riuscito", code, (e as Error).message);
    }
  }
  return sent;
}

Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  const body = await req.json().catch(() => ({}));

  if (body.test) {
    const token = (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
    const { data } = await admin.auth.getUser(token);
    if (!data?.user) return json({ error: "not_signed_in" }, 401);
    const { data: t } = await admin.from("trackers").select("state, tz").eq("user_id", data.user.id).maybeSingle();
    const tz = t?.tz || "Europe/Rome";
    const kind: Kind = body.kind === "morning" ? "morning" : "evening";
    const sent = await sendTo(data.user.id, kind, compose(kind, t?.state, localNow(tz).today));
    return json({ sent });
  }

  // giro orario: ognuno nel suo fuso, al massimo una notifica per tipo al giorno
  const { data: rows, error } = await admin.from("trackers").select("user_id, state, tz, last_morning, last_evening");
  if (error) return json({ error: error.message }, 500);
  let sent = 0;
  for (const t of rows ?? []) {
    const { hour, today } = localNow(t.tz || "Europe/Rome");
    const kind: Kind | null = hour === 8 ? "morning" : hour === 20 ? "evening" : null;
    if (!kind) continue;
    const col = kind === "morning" ? "last_morning" : "last_evening";
    if (t[col] === today) continue;
    // prima segna il giorno, poi invia: due chiamate ravvicinate non mandano doppioni
    const { data: claimed } = await admin.from("trackers").update({ [col]: today })
      .eq("user_id", t.user_id).or(`${col}.is.null,${col}.neq.${today}`).select("user_id");
    if (!claimed?.length) continue;
    sent += await sendTo(t.user_id, kind, compose(kind, t.state, today));
  }
  return json({ sent });
});
