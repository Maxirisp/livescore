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
API_FOOTBALL_KEY = os.environ.get('API_FOOTBALL_KEY')

# ID fisso per la Serie A
SERIE_A_ID = 135
# Anno corrente per la stagione
CURRENT_SEASON = datetime.now().year

API_HOST = 'v3.football.api-sports.io'
API_URL = f'https://{API_HOST}'
HEADERS = {
    'x-rapidapi-host': API_HOST,
    'x-rapidapi-key': API_FOOTBALL_KEY
}

# --- FUNZIONE HELPER PER LE RICHIESTE API ---
def fetch_api(endpoint, params=None):
    """Esegue una richiesta all'API di API-Football e gestisce la risposta."""
    try:
        response = requests.get(f"{API_URL}/{endpoint}", headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get('response'):
            return data
        else:
            print(f"Errore nella risposta API: {data.get('errors')}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Errore durante la richiesta API: {e}")
        return None

# --- COMANDI DEL BOT ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Messaggio di benvenuto con la lista dei comandi."""
    welcome_text = (
        "🇮🇹 **Benvenuto nel Bot sulla Serie A!** 🇮🇹\n\n"
        "Tutte le informazioni si riferiscono alla stagione in corso.\n\n"
        "Usa questi comandi:\n\n"
        "📊 `/classifica` - Mostra la classifica aggiornata.\n"
        "🗓 `/calendario` - Mostra le prossime 5 partite.\n"
        "⚽️ `/marcatori` - La classifica dei migliori 15 marcatori.\n"
        "🔴 `/live` - Mostra le partite in corso in questo momento."
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def classifica(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ottiene e mostra la classifica della Serie A."""
    await update.message.reply_text("📊 Sto caricando la classifica...")
    params = {'league': SERIE_A_ID, 'season': CURRENT_SEASON}
    data = fetch_api("standings", params=params)
    
    if data and data['results'] > 0 and data['response']:
        standings = data['response'][0]['league']['standings'][0]
        league_name = data['response'][0]['league']['name']
        message = f"🏆 **Classifica {league_name}** 🏆\n\n`Pos Squadra              Pt   G`\n"
        message += "`--------------------------------`\n"
        for team in standings:
            pos = str(team['rank']).rjust(2)
            name = team['team']['name'][:18].ljust(18)
            points = str(team['points']).rjust(3)
            played = str(team['all']['played']).rjust(3)
            message += f"`{pos}. {name} {points} {played}`\n"
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text("Impossibile trovare la classifica. La stagione è iniziata?")

async def calendario(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostra le prossime 5 partite in calendario."""
    await update.message.reply_text("🗓 Sto cercando le prossime partite...")
    # Prende le partite da oggi in poi e le ordina per data
    params = {'league': SERIE_A_ID, 'season': CURRENT_SEASON, 'next': 5}
    data = fetch_api("fixtures", params=params)

    if data and data['results'] > 0:
        message = f"📅 **Prossime 5 Partite di Serie A** 📅\n\n"
        for fixture in data['response']:
            home = fixture['teams']['home']['name']
            away = fixture['teams']['away']['name']
            
            # Converte la data UTC in formato italiano (orario di Roma)
            time_utc = datetime.fromisoformat(fixture['fixture']['date'])
            time_local = time_utc.astimezone() # Converte all'orario locale del server
            date_str = time_local.strftime("%d/%m ore %H:%M")

            message += f"▪️ *{date_str}* |  {home} vs {away}\n"
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text("Nessuna partita trovata in programma.")

async def marcatori(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostra la classifica marcatori della Serie A."""
    await update.message.reply_text("⚽️ Sto caricando la classifica marcatori...")
    params = {'league': SERIE_A_ID, 'season': CURRENT_SEASON}
    data = fetch_api("players/topscorers", params=params)

    if data and data['results'] > 0:
        message = "🥅 **Classifica Marcatori Serie A** 🥅\n\n"
        for i, player_info in enumerate(data['response'][:15], 1): # Mostra i primi 15
            player = player_info['player']
            stats = player_info['statistics'][0]
            name = player['name']
            team = stats['team']['name']
            goals = stats['goals']['total']
            message += f"*{i}.* {name} (*{team}*) - **{goals}** gol\n"
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text("Impossibile recuperare la classifica marcatori.")

async def live(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostra le partite in corso della Serie A."""
    await update.message.reply_text("🔴 Sto cercando le partite in corso...")
    params = {'league': SERIE_A_ID, 'live': 'all'}
    data = fetch_api("fixtures", params=params)

    if data and data['results'] > 0:
        message = "🔴 **Partite di Serie A in corso** 🔴\n\n"
        for fixture in data['response']:
            home = fixture['teams']['home']['name']
            away = fixture['teams']['away']['name']
            goals_home = fixture['goals']['home']
            goals_away = fixture['goals']['away']
            elapsed = fixture['fixture']['status']['elapsed']
            message += f"▪️ {home} **{goals_home} - {goals_away}** {away} `({elapsed}')`\n"
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text("Nessuna partita della Serie A è in corso in questo momento.")

def main() -> None:
    """Funzione principale per avviare il bot."""
    if not TELEGRAM_TOKEN or not API_FOOTBALL_KEY:
        print("Errore: Assicurati che TELEGRAM_TOKEN e API_FOOTBALL_KEY siano impostati.")
        return

    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Registrazione dei comandi
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("classifica", classifica))
    application.add_handler(CommandHandler("calendario", calendario))
    application.add_handler(CommandHandler("marcatori", marcatori))
    application.add_handler(CommandHandler("live", live))

    print("Bot Serie A avviato...")
    application.run_polling()

if __name__ == '__main__':
    main()
