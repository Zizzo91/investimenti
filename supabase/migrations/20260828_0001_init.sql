-- investimenti: schema iniziale
-- Tabella profili (creata via trigger al primo accesso Supabase Auth),
-- tabella state single-row-per-user con dati JSONB, politiche RLS per-utente.

-- Profili utente (una riga per utente autenticato)
create table public.profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null unique,
  created_at timestamptz not null default now()
);

-- Stato dell'app: una riga per utente con le tre collezioni JSONB
create table public.state (
  user_id uuid primary key references auth.users(id) on delete cascade,
  investments jsonb not null default '[]',
  pensions jsonb not null default '[]',
  history jsonb not null default '[]',
  last_update timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.profiles enable row level security;
alter table public.state enable row level security;

-- Funzione + trigger: crea il profilo al primo accesso dell'utente autenticato
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, email)
  values (new.id, new.email)
  on conflict (id) do nothing;
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

-- Politiche RLS: ogni utente autenticato legge/scrive SOLO la propria riga.
-- L'anon/public non può leggere né scrivere nulla (gestito nella migrazione keepalive).
create policy "profiles select own"
  on public.profiles for select
  to authenticated using (auth.uid() = id);

create policy "state select own"
  on public.state for select
  to authenticated using (auth.uid() = user_id);

create policy "state upsert own"
  on public.state for all
  to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);
