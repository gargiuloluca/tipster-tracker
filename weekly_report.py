"""Email settimanale: utenti scaduti da poco e in scadenza (con username Telegram)."""
import html
import json
import os
import urllib.request
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

URL = os.environ["SUPABASE_URL"].rstrip("/")
KEY = os.environ["SUPABASE_SERVICE_KEY"]
RESEND_KEY = os.environ["RESEND_API_KEY"]
TO = os.environ["ADMIN_EMAIL"]
RESEND_URL = os.environ.get("RESEND_URL", "https://api.resend.com/emails")
FROM = "AtmBet <noreply@atmbetofficial.com>"


def get(path):
    req = urllib.request.Request(f"{URL}/rest/v1/{path}", headers={"apikey": KEY, "Authorization": f"Bearer {KEY}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def table(rows, titolo, vuoto):
    h = f'<h3 style="margin:18px 0 6px">{html.escape(titolo)}</h3>'
    if not rows:
        return h + f'<p style="color:#666">{html.escape(vuoto)}</p>'
    out = h + '<table style="border-collapse:collapse;font-size:14px;width:100%">'
    out += '<tr style="background:#f3f3f3;text-align:left"><th style="padding:6px">Telegram</th><th style="padding:6px">Email</th><th style="padding:6px">Piano</th><th style="padding:6px">Scadenza</th></tr>'
    for r in rows:
        tg = (r.get("telegram_username") or "").strip() or "(nessuno)"
        out += (f'<tr><td style="padding:6px;border-top:1px solid #ddd"><b>{html.escape(tg)}</b></td>'
                f'<td style="padding:6px;border-top:1px solid #ddd">{html.escape(r.get("email") or "")}</td>'
                f'<td style="padding:6px;border-top:1px solid #ddd">{html.escape(r.get("plan") or "")}</td>'
                f'<td style="padding:6px;border-top:1px solid #ddd">{html.escape(str(r.get("expires_at")))}</td></tr>')
    return out + "</table>"


def main():
    today = datetime.now(ZoneInfo("Europe/Rome")).date()
    sel = "email,telegram_username,plan,expires_at"
    piani = "plan=in.(pure,all_inclusive)"
    scaduti = get(f"profiles?select={sel}&{piani}&expires_at=gte.{today - timedelta(days=7)}&expires_at=lt.{today}&order=expires_at.asc")
    in_scad = get(f"profiles?select={sel}&{piani}&expires_at=gte.{today}&expires_at=lte.{today + timedelta(days=7)}&order=expires_at.asc")
    body = ('<div style="font-family:Arial,sans-serif;max-width:640px;margin:auto;color:#111">'
            f'<h2>Report settimanale AtmBet</h2><p>Aggiornato al {today.strftime("%d/%m/%Y")}.</p>'
            + table(scaduti, f"Scaduti negli ultimi 7 giorni ({len(scaduti)}) - da rimuovere dai gruppi Telegram", "Nessuno.")
            + table(in_scad, f"In scadenza nei prossimi 7 giorni ({len(in_scad)})", "Nessuno.")
            + '<p style="color:#666;font-size:12px;margin-top:20px">Lo username Telegram lo scrive l\'utente: se manca o non corrisponde, riconoscilo dall\'email.</p></div>')
    data = json.dumps({"from": FROM, "to": [TO], "subject": f"AtmBet: {len(scaduti)} scaduti, {len(in_scad)} in scadenza", "html": body}).encode()
    req = urllib.request.Request(RESEND_URL, data=data, method="POST",
                                 headers={"Authorization": f"Bearer {RESEND_KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        print("Email inviata:", r.status, f"scaduti={len(scaduti)} in_scadenza={len(in_scad)}")


if __name__ == "__main__":
    main()
