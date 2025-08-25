import os
import requests
from datetime import datetime
import pytz

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from dotenv import load_dotenv

# Carica le variabili d'ambiente da un file .env per test locali
load_dotenv()

# --- CONFIGURAZIONE ---
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
API_FOOTBALL_KEY = os.environ.get('API_FOOTBALL_KEY')

# ID fisso per la Serie A e fuso orario italiano
SERIE_A_ID = 135
ITALY_TZ = pytz.timezone('Europe/Rome')
# Prendiamo la stagione corrente per i comandi che la richiedono obbligatoriamente
CURRENT_SEASON = datetime.now(ITALY_TZ).year

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
        print(f"Chiamata API a {endpoint} con parametri: {params}") # Riga di debug
        response = requests.get(f"{API_URL}/{endpoint}", headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get('response'):
            print(f"API ha risposto con {data.get('results')} risultati.") # Riga di debug
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
        "Tutte le informazioni si riferiscono alla stagione in corso.\n"
        "*(Nota: Classifica e Marcatori potrebbero non essere disponibili all'inizio della stagione)*\n\n"
        "Usa questi comandi:\n\n"
        "📅 `/oggi` - Mostra le partite in programma oggi.\n"
        "🔴 `/live` - Mostra solo le partite in corso adesso.\n"
        "📊 `/classifica` - La classifica aggiornata.\n"
        "🗓 `/prossime` - Le prossime 5 partite in calendario.\n"
        "⚽️ `/marcatori` - La classifica dei migliori marcatori."
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def oggi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostra tutte le partite in programma per la data corrente in Italia."""
    today_str = datetime.now(ITALY_TZ).strftime('%Y-%m-%d')
    await update.message.reply_text(f"📅 Sto cercando le partite di oggi ({today_str})...")
    
    # MODIFICA CHIAVE: Rimuoviamo 'season' per rendere la richiesta più flessibile
    params = {'league': SERIE_A_ID, 'date': today_str}
    data = fetch_api("fixtures", params=params)

    if data and data['results'] > 0:
        message = f"⚽ **Partite di Serie A di oggi** ⚽\n\n"
        # ... (il resto del codice rimane uguale)
        for fixture in data['response']:
            home = fixture['teams']['home']['name']
            away = fixture['teams']['away']['name']
            status = fixture['fixture']['status']['short']
            time_utc = datetime.fromisoformat(fixture['fixture']['date'])
            time_italy = time_utc.astimezone(ITALY_TZ)
            time_str = time_italy.strftime('%H:%M')
            if status == 'NS': score_or_time = f"*{time_str}*"
            elif status == 'FT': score_or_time = f"{fixture['goals']['home']} - {fixture['goals']['away']} (Finita)"
            else: score_or_time = f"{fixture['goals']['home']} - {fixture['goals']['away']} `({fixture['fixture']['status']['elapsed']}')`"
            message += f"▪️ {home} vs {away}  `{score_or_time}`\n"
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text(f"Nessuna partita di Serie A in programma per oggi.")

async def classifica(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("📊 Sto caricando la classifica...")
    # 'season' qui è obbligatorio, quindi lo manteniamo
    params = {'league': SERIE_A_ID, 'season': CURRENT_SEASON}
    data = fetch_api("standings", params=params)
    if data and data['results'] > 0 and data['response']:
        standings = data['response'][0]['league']['standings'][0]
        league_name = data['response'][0]['league']['name']
        message = f"🏆 **Classifica {league_name}** 🏆\n\n`Pos Squadra              Pt   G`\n`--------------------------------`\n"
        for team in standings:
            pos, name, points, played = str(team['rank']).rjust(2), team['team']['name'][:18].ljust(18), str(team['points']).rjust(3), str(team['all']['played']).rjust(3)
            message += f"`{pos}. {name} {points} {played}`\n"
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text("Classifica non ancora disponibile per la nuova stagione.")

async def prossime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🗓 Sto cercando le prossime partite...")
    # MODIFICA CHIAVE: Rimuoviamo 'season' anche qui
    params = {'league': SERIE_A_ID, 'next': 5}
    data = fetch_api("fixtures", params=params)
    if data and data['results'] > 0:
        message = f"📅 **Prossime 5 Partite di Serie A** 📅\n\n"
        for fixture in data['response']:
            home, away = fixture['teams']['home']['name'], fixture['teams']['away']['name']
            time_utc = datetime.fromisoformat(fixture['fixture']['date'])
            time_italy = time_utc.astimezone(ITALY_TZ)
            date_str = time_italy.strftime("%d/%m ore %H:%M")
            message += f"▪️ *{date_str}* |  {home} vs {away}\n"
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text("Nessuna partita trovata in programma.")

async def marcatori(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("⚽️ Sto caricando la classifica marcatori...")
    # 'season' qui è obbligatorio, quindi lo manteniamo
    params = {'league': SERIE_A_ID, 'season': CURRENT_SEASON}
    data = fetch_api("players/topscorers", params=params)
    if data and data['results'] > 0:
        message = "🥅 **Classifica Marcatori Serie A** 🥅\n\n"
        for i, p_info in enumerate(data['response'][:15], 1):
            player, stats = p_info['player'], p_info['statistics'][0]
            name, team, goals = player['name'], stats['team']['name'], stats['goals']['total']
            message += f"*{i}.* {name} (*{team}*) - **{goals}** gol\n"
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text("Classifica marcatori non ancora disponibile per la nuova stagione.")

async def live(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("🔴 Sto cercando le partite in corso...")
    # Questo comando non usa 'season' ed è per questo che ha sempre funzionato
    params = {'league': SERIE_A_ID, 'live': 'all'}
    data = fetch_api("fixtures", params=params)
    if data and data['results'] > 0:
        message = "🔴 **Partite di Serie A in corso** 🔴\n\n"
        for fixture in data['response']:
            home, away, g_home, g_away, elapsed = fixture['teams']['home']['name'], fixture['teams']['away']['name'], fixture['goals']['home'], fixture['goals']['away'], fixture['fixture']['status']['elapsed']
            message += f"▪️ {home} **{g_home} - {g_away}** {away} `({elapsed}')`\n"
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text("Nessuna partita della Serie A è in corso in questo momento.")

def main() -> None:
    if not TELEGRAM_TOKEN or not API_FOOTBALL_KEY:
        print("Errore: Assicurati che TELEGRAM_TOKEN e API_FOOTBALL_KEY siano impostati.")
        return
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("oggi", oggi))
    application.add_handler(CommandHandler("classifica", classifica))
    application.add_handler(CommandHandler("prossime", prossime))
    application.add_handler(CommandHandler("marcatori", marcatori))
    application.add_handler(CommandHandler("live", live))
    print("Bot Serie A avviato...")
    application.run_polling()

if __name__ == '__main__':
    main()
