#!/usr/bin/env python3
"""Carica i dati locali (investimenti.json) nella tabella `state` su Supabase.

Uso (usa la service_role key SOLO qui, mai nel frontend):
  python3 script/seed_supabase.py path/to/supabase-secrets-investimenti.json

La riga di `state` è unica per utente (user_id = uuid di auth.users). Lo script
trova lo user_id tramite la tabella `profiles` (popolata dal trigger
handle_new_user al primo login) cercando l'email del PIN.

Opzionale: --email <email> per indicare l'email (default: pinEmail da config).
           --skip-existing per non sovrascrivere una riga già presente.
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def request(method, url, key, body=None, prefer=None):
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    if prefer:
        headers["Prefer"] = prefer
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"{method} {url} -> {e.code}: {e.read().decode('utf-8','replace')[:500]}") from e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("secrets", nargs="?", help="percorso supabase-secrets-investimenti.json")
    ap.add_argument("--email", default=None, help="email utente (default: pinEmail)")
    ap.add_argument("--skip-existing", action="store_true")
    args = ap.parse_args()

    secrets = args.secrets or os.path.join(os.path.dirname(BASE_DIR), "Config Utility", "supabase-secrets-investimenti.json")
    with open(secrets) as f:
        s = json.load(f)
    svc_url = s["project_url"].rstrip("/")
    key = s["service_role_key_secret"]
    email = (args.email or s.get("pinEmail") or "").strip().lower()

    with open(os.path.join(BASE_DIR, "investimenti.json")) as f:
        data = json.load(f)

    investments = data.get("investments") or []
    pensions = data.get("pensions") or []
    history = data.get("history") or []
    last_update = data.get("lastUpdate")

    print(f"investments : {len(investments)}")
    print(f"pensions    : {len(pensions)}")
    print(f"history     : {len(history)}")
    print(f"last_update : {last_update}")

    if not email:
        raise SystemExit("Nessuna email: indica --email o pinEmail qui non presente.")
    print(f"email utente: {email}")

    # Trova lo user_id dall'email (profiles popolato dal trigger handle_new_user)
    _, profiles = request("GET", f"{svc_url}/rest/v1/profiles?email=eq.{urllib.parse.quote(email)}", key)
    if not profiles or len(profiles) == 0:
        raise SystemExit(f"Nessun profilo per {email}: l'utente deve fare login almeno una volta (signUp) prima del seed.")
    user_id = profiles[0]["id"]
    print(f"user_id     : {user_id}")

    if args.skip_existing:
        _, existing = request("GET", f"{svc_url}/rest/v1/state?user_id=eq.{user_id}&select=user_id", key)
        if existing:
            print("Riga state già presente: --skip-existing, nessuna sovrascrittura.")
            return

    row = {
        "user_id": user_id,
        "investments": investments,
        "pensions": pensions,
        "history": history,
        "last_update": last_update,
    }
    status, _ = request("POST", f"{svc_url}/rest/v1/state", key, [row], prefer="resolution=merge-duplicates,return=minimal")
    print(f"seed {status} -> riga state upsertata.")


if __name__ == "__main__":
    sys.exit(main())
