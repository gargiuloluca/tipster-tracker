#!/usr/bin/env python3
"""Esporta le tabelle Supabase in file JSON (usato dal workflow di backup)."""
import json
import os
import sys
import urllib.error
import urllib.request

URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_SERVICE_KEY"]
OUT = sys.argv[1] if len(sys.argv) > 1 else "backup_out"
TABLES = ["bets", "profiles", "access_codes", "code_redemptions", "app_settings"]
PAGE = 1000


def get(path, start, end):
    req = urllib.request.Request(
        f"{URL}/rest/v1/{path}",
        headers={
            "apikey": KEY,
            "Authorization": f"Bearer {KEY}",
            "Range-Unit": "items",
            "Range": f"{start}-{end}",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch(table):
    # Prima provo con ordinamento stabile per id, se la tabella non ha id ripiego senza.
    for order in ("&order=id.asc", ""):
        rows, off = [], 0
        try:
            while True:
                chunk = get(f"{table}?select=*{order}", off, off + PAGE - 1)
                rows.extend(chunk)
                if len(chunk) < PAGE:
                    return rows
                off += PAGE
        except urllib.error.HTTPError as e:
            if e.code == 400 and order:
                continue
            raise
    return []


def main():
    os.makedirs(OUT, exist_ok=True)
    for t in TABLES:
        rows = fetch(t)
        if t == "bets" and not rows:
            print("ERRORE: tabella bets vuota, backup annullato", file=sys.stderr)
            sys.exit(1)
        with open(os.path.join(OUT, f"{t}.json"), "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=1)
        print(f"{t}: {len(rows)} righe")


if __name__ == "__main__":
    main()
