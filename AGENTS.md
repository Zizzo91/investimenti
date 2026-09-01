# investimenti-main

## Descrizione
Progressive Web App per il tracciamento di investimenti e fondi pensione personali con sincronizzazione cloud su **Supabase**, protetta da **login PIN a 6 cifre** (server-side). Supporta dark mode, grafici (Chart.js), calcolatrice inline, PAC (piano di accumulo) con auto-update, notifiche obiettivo, drag & drop di widget e righe, export CSV/backup JSON e sincronizzazione cross-device.

## Struttura
```
investimenti-main/
├── index.html                    — UI principale (Chart.js, SortableJS); schermata login PIN
├── manifest.json                 — PWA manifest
├── sw.js                         — Service Worker (pass-through, niente cache contenuti)
├── config/
│   └── supabase-config.js        — window.SUPABASE_CONFIG {url, anonKey, pinEmail} (pubblico, committato)
├── script/
│   └── seed_supabase.py          — Seed/ripristino dati da investimenti.json locale (usa service_role)
├── supabase/
│   ├── migrations/               — 0001 init schema + RLS, 0002 keepalive anon
│   └── config.toml               — Config CLI
├── investimenti.json             — ⚠️ gitignored: solo origine locale del seed, mai nel repo
└── .github/workflows/keepalive.yml — Anti-pausa free tier (URL e anon key da Actions variables)
```

## Stack
- HTML/CSS/JS vanilla, Chart.js, SortableJS
- PWA con Service Worker
- Backend: **Supabase** (Postgres + Auth + RLS) — SDK `supabase-js` CDN UMD (global `window.supabase`).

## Login
- **PIN 6 cifre**: il PIN è la PASSWORD dell'account Supabase (`config/supabase-config.js → pinEmail`). Il codice non contiene mai il PIN: vive solo su Supabase (hashed), mai in repo, non clonabile.
- Primo accesso su un dispositivo: se l'utente non esiste ancora viene creato (`signUp`); con "Conferma email" attiva serve cliccare la mail di conferma una volta, poi reinserire lo stesso PIN.
- Se appare "email rate limit exceeded" → NON riprovare: attendere ~1 ora (quota oraria) e riprovare con lo stesso PIN.
- **PIN ad ogni accesso**: la sessione NON è persistita (`auth.persistSession:false`) e non ci sono auto-login all'avvio. Ad ogni apertura (anche su un dispositivo già usato) viene richiesto il PIN; i dati si caricano solo dopo il login. Button "🚪 Esci" nella topbar per l'uscita.
- Senza sessione valida l'app **non carica né renderizza** alcun dato cloud (schermata di login a schermo intero); il server rifiuta comunque le richieste anon (RLS).

## Database (Supabase, progetto `gfglazxhxxplhoteaahr`, schema `investimenti`)
- `profiles(id uuid PK → auth.users, email, created_at)` — creato via trigger `handle_new_user` al primo accesso (nel target schema `public`)
- `investimenti.state(user_id uuid PK → auth.users, investments jsonb, pensions jsonb, history jsonb, last_update timestamptz, updated_at)` — **una riga per utente** in schema `investimenti` (query via SDK `.schema('investimenti')`)
- RLS: solo ruolo `authenticated` legge/scrive la propria riga (`auth.uid()`); l'anon può leggere solo `state.user_id` (policy `using(false)`: 200 senza dati) per il keepalive
- Salvataggi: ogni mutazione (form, drag righe, PAC) scrive su localStorage (cache/mirror) e fa upsert della propria riga `state` su Supabase via SDK

## Note operative
- Keepalive generico: le Actions variables del repo `SUPABASE_URL` e `SUPABASE_ANON_KEY` vanno impostate su GitHub (Settings → Secrets and variables → Actions → Variables), altrimenti il workflow si salta con un warning.
- `script/seed_supabase.py` legge `investimenti.json` locale (gitignored) e upserta la riga `state` con la `service_role` key. Va eseguito DOPO il primo login dell'utente (la riga `state` è keyata sul `user_id` di auth.users).
- **Segreti**: `config/supabase-config.js` è committato perché serve a GitHub Pages, ma contiene SOLO dati pubblici (url, anon key, `pinEmail` = email di login). `service_role` e `db_password` stanno SOLO in `Config Utility/supabase-secrets-investimenti.json` — mai nel repo/progetto pubblico. I dati finanziari (`investimenti.json`) non devono MAI essere committati.
