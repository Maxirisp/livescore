import os
import requests
from datetime import date, timedelta
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Variabili ambiente
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": FOOTBALL_API_KEY}

COMPETITION = "SA"  # Serie A

# ------------------------------
# Utility per chiamare API
# ------------------------------
def get_matches(date_from, date_to):
    url = f"{BASE_URL}/competitions/{COMPETITION}/matches?dateFrom={date_from}&dateTo={date_to}"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        return []
    return r.json().get("matches", [])

def get_standings():
    url = f"{BASE_URL}/competitions/{COMPETITION}/standings"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        return None
    return r.json()

def get_scorers():
    url = f"{BASE_URL}/competitions/{COMPETITION}/scorers"
    r = requests.get(url, headers=HEADERS)
    if r.status_code != 200:
        return None
    return r.json()

# ------------------------------
# Comandi del bot
# ------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Ciao! Sono MaidireStat ⚽\n"
        "Comandi disponibili (solo Serie A):\n"
        "/oggi → partite di oggi\n"
        "/domani → partite di domani\n"
        "/livescore → partite in corso\n"
        "/classifica → classifica Serie A\n"
        "/marcatori → top scorer Serie A\n"
    )

async def oggi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = date.today().isoformat()
    matches = get_matches(today, today)
    if not matches:
        await update.message.reply_text("Nessuna partita di Serie A oggi.")
        return
    
    msg = "📅 Partite di Serie A oggi:\n\n"
    for m in matches:
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]
        status = m["status"]
        full = m["score"]["fullTime"]
        risultato = f"{full['home']} - {full['away']}" if full["home"] is not None else "da giocare"
        msg += f"{home} vs {away} → {risultato} ({status})\n"
    await update.message.reply_text(msg)

async def domani(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    matches = get_matches(tomorrow, tomorrow)
    if not matches:
        await update.message.reply_text("Nessuna partita di Serie A domani.")
        return
    
    msg = "📅 Partite di Serie A domani:\n\n"
    for m in matches:
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]
        msg += f"{home} vs {away}\n"
    await update.message.reply_text(msg)

async def livescore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = date.today().isoformat()
    matches = get_matches(today, today)
    live = [m for m in matches if m["status"] == "LIVE"]
    if not live:
        await update.message.reply_text("⚽ Nessuna partita di Serie A live ora.")
        return
    
    msg = "🔥 Partite in corso (Serie A):\n\n"
    for m in live:
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]
        score = m["score"]["fullTime"]
        msg += f"{home} {score['home']} - {score['away']} {away}\n"
    await update.message.reply_text(msg)

async def classifica(update: Update, context: ContextTypes.DEFAULT_TYPE):
    standings = get_standings()
    if not standings:
        await update.message.reply_text("Errore nel recupero classifica.")
        return
    
    table = standings["standings"][0]["table"]
    msg = "📊 Classifica Serie A:\n\n"
    for t in table:
        msg += f"{t['position']}. {t['team']['name']} ({t['points']} pt)\n"
    await update.message.reply_text(msg)

async def marcatori(update: Update, context: ContextTypes.DEFAULT_TYPE):
    scorers = get_scorers()
    if not scorers or not scorers.get("scorers"):
        await update.message.reply_text("⚠️ Marcatori non disponibili con piano free.")
        return
    
    msg = "⚽ Marcatori Serie A:\n\n"
    for s in scorers["scorers"][:10]:
        msg += f"{s['player']['name']} ({s['team']['name']}) - {s['numberOfGoals']} gol\n"
    await update.message.reply_text(msg)

# ------------------------------
# MAIN
# ------------------------------
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("oggi", oggi))
    app.add_handler(CommandHandler("domani", domani))
    app.add_handler(CommandHandler("livescore", livescore))
    app.add_handler(CommandHandler("classifica", classifica))
    app.add_handler(CommandHandler("marcatori", marcatori))

    app.run_polling()

if __name__ == "__main__":
    main()
