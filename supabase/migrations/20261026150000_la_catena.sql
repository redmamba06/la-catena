-- La Catena: dati dell'app per account e telefoni iscritti alle notifiche.

create table public.trackers (
  user_id uuid primary key default auth.uid() references auth.users on delete cascade,
  state jsonb not null,
  saved_at bigint not null default 0,          -- Date.now() dell'ultimo salvataggio sul telefono
  tz text not null default 'Europe/Rome',
  last_morning date,                           -- ultimo giorno in cui è partita la notifica delle 8
  last_evening date,                           -- ultimo giorno in cui è partita la notifica delle 20
  updated_at timestamptz not null default now()
);

alter table public.trackers enable row level security;

create policy "leggi i tuoi dati" on public.trackers
  for select to authenticated using ((select auth.uid()) = user_id);
create policy "crea i tuoi dati" on public.trackers
  for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "aggiorna i tuoi dati" on public.trackers
  for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);

create table public.push_subscriptions (
  endpoint text primary key,
  user_id uuid not null default auth.uid() references auth.users on delete cascade,
  subscription jsonb not null,
  created_at timestamptz not null default now()
);

alter table public.push_subscriptions enable row level security;

create policy "leggi i tuoi telefoni" on public.push_subscriptions
  for select to authenticated using ((select auth.uid()) = user_id);
create policy "aggiungi un telefono" on public.push_subscriptions
  for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "aggiorna un telefono" on public.push_subscriptions
  for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "togli un telefono" on public.push_subscriptions
  for delete to authenticated using ((select auth.uid()) = user_id);

-- Ogni ora, al minuto 0, chiama la funzione notify. È lei a decidere, per ogni account,
-- se nel suo fuso sono le 8 o le 20 e a non mandare mai due volte la stessa notifica.
create extension if not exists pg_cron;
create extension if not exists pg_net with schema extensions;

select cron.schedule(
  'la-catena-notify',
  '0 * * * *',
  $$
  select net.http_post(
    url := 'https://jthzincpedchogxnlzmi.supabase.co/functions/v1/notify',
    headers := jsonb_build_object(
      'Content-Type', 'application/json',
      'apikey', 'sb_publishable_bHLqSuhBA0m7VgCuhpItLA__-7Bd74r'
    ),
    body := '{}'::jsonb,
    timeout_milliseconds := 30000
  );
  $$
);
