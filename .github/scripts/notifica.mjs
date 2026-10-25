// Invia un push vuoto di contenuto personale: dice solo "morning" o "evening".
// Il testo lo compone il telefono (sw.js) con i dati che restano sul telefono.
import webpush from "web-push";

const { VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY, PUSH_SUBSCRIPTION, SCHEDULE, KIND } = process.env;

if (!VAPID_PUBLIC_KEY || !VAPID_PRIVATE_KEY || !PUSH_SUBSCRIPTION) {
  console.log("Notifiche non ancora configurate: mancano i secret VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY o PUSH_SUBSCRIPTION.");
  process.exit(0);
}

let kind = KIND || null;
if (!kind && SCHEDULE) {
  // ora a Roma prevista da questa riga cron, indipendente dai ritardi di GitHub
  const utcHour = Number(SCHEDULE.split(" ")[1]);
  const now = new Date();
  const romeHour = Number(new Intl.DateTimeFormat("en-GB", { timeZone: "Europe/Rome", hour: "numeric", hourCycle: "h23" }).format(now));
  const offset = (romeHour - now.getUTCHours() + 24) % 24;
  const planned = (utcHour + offset) % 24;
  kind = planned === 8 ? "morning" : planned === 20 ? "evening" : null;
  if (!kind) { console.log(`Riga ${SCHEDULE}: a Roma sarebbero le ${planned}, salto.`); process.exit(0); }
}
if (!kind) kind = "evening";

webpush.setVapidDetails("https://redmamba06.github.io/la-catena/", VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY);

try {
  const res = await webpush.sendNotification(JSON.parse(PUSH_SUBSCRIPTION), JSON.stringify({ kind }), { TTL: 3600, urgency: "high" });
  console.log(`Notifica "${kind}" inviata (${res.statusCode}).`);
} catch (e) {
  if (e.statusCode === 404 || e.statusCode === 410) {
    console.error("Il telefono non accetta più le notifiche: riattivale dall'app e aggiorna il secret PUSH_SUBSCRIPTION.");
  } else {
    console.error("Invio non riuscito:", e.statusCode || "", e.body || e.message);
  }
  process.exit(1);
}
