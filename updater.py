import os
import json
import requests
from datetime import datetime

API_KEY = os.getenv("RAPIDAPI_KEY")
HEADERS = {
    "x-apisports-key": API_KEY
}

BETS_FILE = "bets.json"

def clean_team_name(name):
    unwanted = ["fc", "cf", "calcio", "as", "ss", "ac", "us", "sc", "de", "the"]
    parts = name.lower().replace("-", " ").replace("/", " ").split()
    return [p for p in parts if p not in unwanted and len(p) > 2]

def evaluate_single_match(prediction, market, h_goals, a_goals):
    tot_goals = h_goals + a_goals
    p = prediction.lower()
    m = market.lower()

    # 1X2
    if "segno 1" in p or p == "1" or "w1" in p:
        return "won" if h_goals > a_goals else "lost"
    if "segno 2" in p or p == "2" or "w2" in p:
        return "won" if a_goals > h_goals else "lost"
    if "segno x" in p or p == "x":
        return "won" if h_goals == a_goals else "lost"

    # Goal / No Goal
    if "goal" in p or "gg" in p or "both teams" in p:
        return "won" if (h_goals > 0 and a_goals > 0) else "lost"
    if "no gol" in p or "ng" in p:
        return "won" if (h_goals == 0 or a_goals == 0) else "lost"

    # Under / Over Generali
    if "over 1.5" in p:
        return "won" if tot_goals > 1.5 else "lost"
    if "over 2.5" in p:
        return "won" if tot_goals > 2.5 else "lost"
    if "over 3.5" in p or "over 3.0" in p or "over 3" in p:
        return "won" if tot_goals > 3 else ("void" if tot_goals == 3 else "lost")
    if "under 2.5" in p:
        return "won" if tot_goals < 2.5 else "lost"
    if "under 3.5" in p:
        return "won" if tot_goals < 3.5 else "lost"

    # Combo 1 + Over 2.5
    if ("1 +" in p or "1+" in p) and "over 2.5" in p:
        return "won" if (h_goals > a_goals and tot_goals > 2.5) else "lost"

    return "pending"

def run_update():
    if not API_KEY:
        print("Errore: Chiave API non configurata in RAPIDAPI_KEY.")
        return

    if not os.path.exists(BETS_FILE):
        print("File bets.json non trovato.")
        return

    with open(BETS_FILE, "r", encoding="utf-8") as f:
        bets = json.load(f)

    pending_bets = [b for b in bets if b.get("status") == "pending"]
    if not pending_bets:
        print("Nessun pronostico in corso da aggiornare.")
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    url = f"https://v3.football.api-sports.io/fixtures?date={today_str}"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=25)
        if res.status_code != 200:
            print("Errore chiamata API:", res.status_code, res.text)
            return
        data = res.json()
    except Exception as e:
        print("Errore connessione API:", e)
        return

    fixtures = data.get("response", [])
    print(f"Scaricati {len(fixtures)} eventi in programma oggi ({today_str}).")

    updated_count = 0

    for bet in pending_bets:
        match_raw = bet.get("match_name", "")
        
        # Gestione Singole (non multiple con '/')
        if "/" not in match_raw:
            keywords = clean_team_name(match_raw)
            for fix in fixtures:
                h_name = fix["teams"]["home"]["name"].lower()
                a_name = fix["teams"]["away"]["name"].lower()
                status_short = fix["fixture"]["status"]["short"]

                # Verifica corrispondenza squadre
                match_home = any(k in h_name for k in keywords)
                match_away = any(k in a_name for k in keywords)

                if (match_home or match_away) and status_short in ["FT", "AET", "PEN"]:
                    hg = fix["goals"]["home"]
                    ag = fix["goals"]["away"]
                    res_eval = evaluate_single_match(bet.get("prediction", ""), bet.get("market", ""), hg, ag)
                    
                    if res_eval in ["won", "lost", "void"]:
                        bet["status"] = res_eval
                        updated_count += 1
                        print(f"Match concluso: {bet['match_name']} -> {res_eval.upper()} ({hg}-{ag})")
                    break

    if updated_count > 0:
        with open(BETS_FILE, "w", encoding="utf-8") as f:
            json.dump(bets, f, ensure_ascii=False, indent=2)
        print(f"Salvate {updated_count} giocate aggiornate con successo in bets.json!")
    else:
        print("Nessuna giocata conclusa trovata in questo controllo.")

if __name__ == "__main__":
    run_update()
