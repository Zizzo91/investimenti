-- Keepalive GitHub Actions (free tier anti-pausa).
-- L'anon può leggere solo la colonna non sensibile `user_id` di state;
-- la policy `using (false)` esclude sempre le righe: l'API torna 200
-- senza esporre alcun dato. Gli altri accessi anon restano vietati.
revoke all on table public.state, public.profiles from anon, public;
grant select (user_id) on public.state to anon;

create policy "state user_id for anon keepalive"
  on public.state for select
  to anon using (false);
