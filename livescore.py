import os
import requests
from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Carica le variabili d'ambiente da un file .env per test locali
load_dotenv()

# --- CONFIGURAZIONE ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
# NOTA: Assicurati di usare la variabile giusta su Render!
FOOTBALL_DATA_TOKEN = os.environ.get('FOOTBALL_DATA_TOKEN') 

# ID della Serie A su football-data.org ('SA') e URL base
SERIE_A_CODE = 'SA'
BASE_API_URL = 'https://api.football-data.org/v4/'
HEADERS = {'X-Auth-Token': FOOTBALL_DATA_TOKEN}

# --- FUNZIONE HELPER PER LE RICHIESTE API ---
def fetch_api(endpoint):
    """Esegue una richiesta all'API di football-data.org."""
    try:
        print(f"Chiamata API a {endpoint}") # Debug
        response = requests.get(BASE_API_URL + endpoint, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        print("Chiamata API riuscita.") # Debug
        return data
    except requests.exceptions.RequestException as e:
        print(f"Errore durante la richiesta API: {e}")
        return None

# --- COMANDI DEL BOT ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Messaggio di benvenuto con la lista dei comandi."""
    welcome_text = (
        "🇮🇹 **Benvenuto nel Bot sulla Serie A!** 🇮🇹\n\n"
        "Dati forniti da football-data.org.\n\n"
        "Usa questi comandi:\n\n"
        "📅 `/oggi` - Mostra le partite in programma oggi.\n"
        "🔴 `/live` - Mostra le partite in corso adesso.\n"
        "📊 `/classifica` - La classifica aggiornata.\n"
        "🗓 `/calendario` - Le prossime 5 partite in programma.\n"
        "⚽️ `/marcatori` - La classifica dei migliori marcatori."
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def oggi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostra tutte le partite in programma per la data corrente, gestendo messaggi lunghi."""
    today_str = datetime.now().strftime('%Y-%m-%d')
    await update.message.reply_text(f"📅 Sto cercando le partite di oggi ({today_str})...")
    
    data = fetch_api(f"competitions/{SERIE_A_CODE}/matches?date={today_str}")

    if data and data.get('matches'):
        # --- LOGICA AGGIORNATA PER MESSAGGI LUNGHI ---
        
        all_match_lines = []
        for match in data['matches']:
            home_team = match['homeTeam']['name']
            away_team = match['away_team']['name']
            
            time_utc = datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00'))
            time_local = time_utc + timedelta(hours=2) # Da UTC a CEST
            time_str = time_local.strftime('%H:%M')

            # Creiamo una riga per ogni partita
            all_match_lines.append(f"▪️ {home_team} vs {away_team} `(ore {time_str})`\n")

        # Ora costruiamo i messaggi, assicurandoci che non superino il limite
        header = "⚽ **Partite di Serie A di oggi** ⚽\n\n"
        current_message = header
        
        for line in all_match_lines:
            # Se aggiungere la nuova riga supera il limite, invia il messaggio attuale e iniziane uno nuovo
            if len(current_message) + len(line) > 4096:
                await update.message.reply_text(current_message, parse_mode='Markdown')
                current_message = "" # Reset per il prossimo messaggio
            
            current_message += line
            
        # Invia l'ultimo messaggio rimasto (o l'unico, se la lista era corta)
        if current_message != header:
             await update.message.reply_text(current_message, parse_mode='Markdown')
        # -------------------------------------------

    else:
        await update.message.reply_text("Nessuna partita di Serie A in programma per oggi.")

async def classifica(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("📊 Sto caricando la classifica...")
    data = fetch_api(f"competitions/{SERIE_A_CODE}/standings")
    
    if data and data.get('standings'):
        table = data['standings'][0]['table']
        message = "🏆 **Classifica Serie A** 🏆\n\n`Pos Squadra              Pt   G`\n`--------------------------------`\n"
        for team in table:
            pos = str(team['position']).rjust(2)
            name = team['team']['name'][:18].ljust(18)
            points = str(team['points']).rjust(3)
            played = str(team['playedGames']).rjust(3)
            message += f"`{pos}. {name} {points} {played}`\n"
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text("Impossibile recuperare la classifica.")

async def calendario(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🗓 Sto cercando le prossime partite...")
    data = fetch_api(f"competitions/{SERIE_A_CODE}/matches?status=SCHEDULED")

    if data and data.get('matches'):
        message = "📅 **Prossime Partite di Serie A** 📅\n\n"
        for match in data['matches'][:5]: # Mostra solo le prossime 5
            home = match['homeTeam']['name']
            away = match['awayTeam']['name']
            
            time_utc = datetime.fromisoformat(match['utcDate'].replace('Z', '+00:00'))
            time_local = time_utc + timedelta(hours=2) # Da UTC a CEST
            date_str = time_local.strftime("%d/%m ore %H:%M")
            message += f"▪️ *{date_str}* | {home} vs {away}\n"
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text("Nessuna partita trovata in programma.")

async def marcatori(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("⚽️ Sto caricando la classifica marcatori...")
    data = fetch_api(f"competitions/{SERIE_A_CODE}/scorers")

    if data and data.get('scorers'):
        message = "🥅 **Classifica Marcatori Serie A** 🥅\n\n"
        for i, scorer in enumerate(data['scorers'][:15], 1):
            name = scorer['player']['name']
            team = scorer['team']['name']
            goals = scorer['goals']
            message += f"*{i}.* {name} (*{team}*) - **{goals}** gol\n"
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text("Impossibile recuperare la classifica marcatori.")

async def live(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🔴 Sto cercando le partite in corso...")
    data = fetch_api(f"competitions/{SERIE_A_CODE}/matches?status=LIVE")

    if data and data.get('matches'):
        message = "🔴 **Partite di Serie A in corso** 🔴\n\n"
        for match in data['matches']:
            home_team = match['homeTeam']['name']
            away_team = match['awayTeam']['name']
            score_home = match['score']['fullTime']['home']
            score_away = match['score']['fullTime']['away']
            message += f"▪️ {home_team} **{score_home} - {score_away}** {away_team}\n"
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text("Nessuna partita della Serie A è in corso in questo momento.")

def main() -> None:
    if not TELEGRAM_TOKEN or not FOOTBALL_DATA_TOKEN:
        print("Errore: Assicurati che TELEGRAM_TOKEN e FOOTBALL_DATA_TOKEN siano impostati.")
        return
        
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("oggi", oggi))
    application.add_handler(CommandHandler("classifica", classifica))
    application.add_handler(CommandHandler("calendario", calendario))
    application.add_handler(CommandHandler("marcatori", marcatori))
    application.add_handler(CommandHandler("live", live))
    
    print("Bot Serie A (football-data.org) avviato...")
    application.run_polling()

if __name__ == '__main__':
    main()
