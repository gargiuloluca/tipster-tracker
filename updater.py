import os
import json
import requests
from datetime import datetime, timedelta, timezone

API_KEY = os.getenv("RAPIDAPI_KEY")
HEADERS = {
    "x-apisports-key": API_KEY
}

# Database (Supabase). La chiave "service_role" sta SOLO nei Secrets di GitHub, mai nel sito.
SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or ""
API_BASE = os.getenv("FOOTBALL_API_BASE", "https://v3.football.api-sports.io")
SB_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}

def clean_tokens(text):
    unwanted = {"fc", "cf", "calcio", "as", "ss", "ac", "us", "sc", "de", "the", "vs", "-", "/", "v"}
    raw = text.lower().replace("-", " ").replace("/", " ").replace("vs", " ").split()
    return [w for w in raw if w not in unwanted and len(w) > 2]

def match_teams_strictly(bet_match, api_home, api_away):
    parts = bet_match.lower().split("vs") if "vs" in bet_match.lower() else bet_match.lower().split("-")
    if len(parts) < 2:
        return False

    bet_home_tokens = clean_tokens(parts[0])
    bet_away_tokens = clean_tokens(parts[1])

    home_target = clean_tokens(api_home)
    away_target = clean_tokens(api_away)

    has_home = any(t in api_home.lower() for t in bet_home_tokens)
    has_away = any(t in api_away.lower() for t in bet_away_tokens)

    # Devono corrispondere ENTRAMBE le squadre
    return has_home and has_away

def evaluate_single_match(prediction, market, h_goals, a_goals):
    tot_goals = h_goals + a_goals
    p = prediction.lower()

    if "segno 1" in p or p == "1" or "w1" in p:
        return "won" if h_goals > a_goals else "lost"
    if "segno 2" in p or p == "2" or "w2" in p:
        return "won" if a_goals > h_goals else "lost"
    if "segno x" in p or p == "x":
        return "won" if h_goals == a_goals else "lost"

    if "goal" in p or "gg" in p or "both teams" in p:
        return "won" if (h_goals > 0 and a_goals > 0) else "lost"
    if "no gol" in p or "ng" in p:
        return "won" if (h_goals == 0 or a_goals == 0) else "lost"

    if "over 1.5" in p:
        return "won" if tot_goals > 1.5 else "lost"
    if "over 2.5" in p:
        return "won" if tot_goals > 2.5 else "lost"
    if "over 3.5" in p or "over 3.0" in p or "over 3" in p:
        return "won" if tot_goals > 3 else ("void" if tot_goals == 3 else "lost")

    if ("1 +" in p or "1+" in p) and "over 2.5" in p:
        return "won" if (h_goals > a_goals and tot_goals > 2.5) else "lost"

    return "pending"

def fetch_pending_bets():
    res = requests.get(
        f"{SUPABASE_URL}/rest/v1/bets",
        params={"status": "eq.pending", "select": "id,match_name,market,prediction,event_date,status"},
        headers=SB_HEADERS, timeout=25,
    )
    res.raise_for_status()
    return res.json()

def save_bet_status(bet_id, new_status):
    res = requests.patch(
        f"{SUPABASE_URL}/rest/v1/bets",
        params={"id": f"eq.{bet_id}", "status": "eq.pending"},   # aggiorna solo se e ancora "pending"
        json={"status": new_status},
        headers=SB_HEADERS, timeout=25,
    )
    res.raise_for_status()

def run_update():
    if not API_KEY:
        print("Errore: Chiave API non configurata.")
        return
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("Errore: SUPABASE_URL / SUPABASE_SERVICE_KEY non configurati nei Secrets di GitHub.")
        return

    pending_bets = fetch_pending_bets()
    if not pending_bets:
        print("Nessun pronostico 'pending' da verificare.")
        return

    now_utc = datetime.now(timezone.utc)
    # oggi e ieri: le partite serali finiscono spesso dopo la mezzanotte UTC
    dates = [(now_utc - timedelta(days=1)).strftime("%Y-%m-%d"), now_utc.strftime("%Y-%m-%d")]
    fixtures = []
    for day in dates:
        res = requests.get(f"{API_BASE}/fixtures?date={day}", headers=HEADERS, timeout=25)
        if res.status_code != 200:
            print("Errore API:", res.status_code, "per", day)
            continue
        fixtures.extend(res.json().get("response", []))
    print(f"Scaricati {len(fixtures)} eventi ({dates[0]} e {dates[1]}).")

    updated_count = 0

    for bet in pending_bets:
        match_raw = bet.get("match_name", "")
        if "/" in match_raw:
            # Per le multiple complesse rimandiamo la chiusura manuale o analisi dedicata
            continue

        for fix in fixtures:
            status_short = fix["fixture"]["status"]["short"]
            timestamp = fix["fixture"]["timestamp"]
            fixture_time = datetime.fromtimestamp(timestamp, tz=timezone.utc)

            # Se la partita è in programma nel futuro, saltala
            if fixture_time > now_utc:
                continue

            # Considera SOLO partite terminate al 100%
            if status_short not in ["FT", "AET", "PEN"]:
                continue

            h_name = fix["teams"]["home"]["name"]
            a_name = fix["teams"]["away"]["name"]

            if match_teams_strictly(match_raw, h_name, a_name):
                hg = fix["goals"]["home"]
                ag = fix["goals"]["away"]
                res_eval = evaluate_single_match(bet.get("prediction", ""), bet.get("market", ""), hg, ag)

                if res_eval in ["won", "lost", "void"]:
                    save_bet_status(bet["id"], res_eval)
                    updated_count += 1
                    print(f"VERIFICATA CONCLUSA: {match_raw} ({h_name} vs {a_name}) -> {res_eval.upper()} [{hg}-{ag}]")
                break

    if updated_count > 0:
        print(f"Aggiornate {updated_count} giocate terminate.")
    else:
        print("Nessuna delle partite in corso è ancora terminata al fischio finale.")

if __name__ == "__main__":
    run_update()
