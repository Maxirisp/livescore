import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Recupera i token dalle variabili d'ambiente
TELEGRAM_TOKEN = os.getenv("8448591154:AAEJorp4NLnox6coY3zaB9iRu5p0h2jTLss")
FOOTBALL_API_KEY = os.getenv("437bdfc679224878ad25e2d8cff723a0")

BASE_URL = "https://api.football-data.org/v4"

# Funzione start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Ciao! Sono MaidireStat ⚽. Scrivi /oggi per i risultati.")

# Funzione per i risultati di oggi
async def oggi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = f"{BASE_URL}/matches?dateFrom=today&dateTo=today"
    headers = {"X-Auth-Token": FOOTBALL_API_KEY}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        await update.message.reply_text("Errore nel recupero dati ⚠️")
        return
    
    data = response.json()
    matches = data.get("matches", [])
    
    if not matches:
        await update.message.reply_text("Nessuna partita oggi.")
        return
    
    msg = "📅 Partite di oggi:\n\n"
    for m in matches[:10]:  # limitiamoci a 10 partite
        home = m["homeTeam"]["name"]
        away = m["awayTeam"]["name"]
        score = m["score"]
        full = score.get("fullTime")
        risultato = f"{full['home']} - {full['away']}" if full["home"] is not None else "da giocare"
        msg += f"{home} vs {away} → {risultato}\n"
    
    await update.message.reply_text(msg)

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("oggi", oggi))

    app.run_polling()

if __name__ == "__main__":
    main()
