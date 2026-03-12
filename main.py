import telebot
from telebot import types
import sqlite3

DB_PATH = "cybersport_final.db"

# === Токен Telegram бота ===
BOT_TOKEN = "8359229646:AAGcxQBHRbwJsQq75YtNKt8RItFDAmZYDkQ"

bot = telebot.TeleBot(BOT_TOKEN)

# === Подключение к базе данных ===
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# === Главное меню ===
@bot.message_handler(commands=['start'])
def start(message):
    main_menu(message.chat.id)

def main_menu(chat_id):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("🎮 Игроки", callback_data="players"),
        types.InlineKeyboardButton("🏅 Команды", callback_data="teams"),
        types.InlineKeyboardButton("🏆 Турниры", callback_data="tournaments")
    )
    bot.send_message(chat_id, "Добро пожаловать в киберспортивного бота!\nВыберите категорию или введите никнейм игрока для поиска:", reply_markup=keyboard)

# === Обработка кнопок ===
@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    if call.data == "players":
        show_players(call)
    elif call.data == "teams":
        show_teams(call)
    elif call.data.startswith("team_"):
        team_id = int(call.data.split("_")[1])
        show_team_players(call, team_id)
    elif call.data == "tournaments":
        show_tournaments(call)
    elif call.data.startswith("tournament_"):
        tournament_id = int(call.data.split("_")[1])
        show_tournament_teams(call, tournament_id)
    elif call.data == "back_main":
        bot.delete_message(call.message.chat.id, call.message.message_id)
    elif call.data == "back_teams":
        bot.delete_message(call.message.chat.id, call.message.message_id)
    elif call.data == "back_tournaments":
        bot.delete_message(call.message.chat.id, call.message.message_id)

# === Игроки ===
def show_players(call):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.nickname, p.rating_2_0, p.kpr, p.adr, t.name AS team_name
            FROM players p
            LEFT JOIN teams t ON p.team_id = t.id
        """)
        players = cursor.fetchall()
        cursor.close()

    if players:
        text = "🎮 <b>Игроки</b>:\n\n"
        for p in players:
            text += f"• <b>{p['nickname']}</b> ({p['rating_2_0']})\n"
            text += f"  Команда: {p['team_name'] or 'Без команды'}\n"
            text += f"  kpr - {p['kpr']}\n"
            text += f"  adr - {p['adr']}\n\n"
    else:
        text = "Нет данных об игроках."

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_main"))
    bot.send_message(call.message.chat.id, text, parse_mode="HTML", reply_markup=keyboard)

# === Команды ===
def show_teams(call):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, country FROM teams")
        teams = cursor.fetchall()
        cursor.close()

    if not teams:
        bot.send_message(call.message.chat.id, "Нет данных о командах.")
        return

    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for t in teams:
        keyboard.add(types.InlineKeyboardButton(f"{t['name']} ({t['country']})", callback_data=f"team_{t['id']}"))
    keyboard.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_main"))
    bot.send_message(call.message.chat.id, "🏅 Выберите команду:", reply_markup=keyboard)

# === Игроки выбранной команды ===
def show_team_players(call, team_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM teams WHERE id = ?", (team_id,))
        team = cursor.fetchone()

        cursor.execute("""
            SELECT nickname, position, rating_2_0
            FROM players
            WHERE team_id = ?
        """, (team_id,))
        players = cursor.fetchall()
        cursor.close()

    if not team:
        bot.send_message(call.message.chat.id, "Команда не найдена.")
        return

    if players:
        text = f"🎯 <b>{team['name']}</b> — состав:\n\n"
        for p in players:
            text += f"• <b>{p['nickname']}</b> ({p['position']}) {p['rating_2_0']}\n"
    else:
        text = f"В команде <b>{team['name']}</b> нет зарегистрированных игроков."

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_teams"))
    bot.send_message(call.message.chat.id, text, parse_mode="HTML", reply_markup=keyboard)

# === Турниры ===
def show_tournaments(call):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, location, year, prize_money FROM tournaments ORDER BY year DESC")
        tournaments = cursor.fetchall()
        cursor.close()

    if not tournaments:
        bot.send_message(call.message.chat.id, "Нет данных о турнирах.")
        return

    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for t in tournaments:
        keyboard.add(types.InlineKeyboardButton(f"{t['name']} ({t['year']})", callback_data=f"tournament_{t['id']}"))
    keyboard.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_main"))
    bot.send_message(call.message.chat.id, "🏆 Выберите турнир:", reply_markup=keyboard)

# === Команды выбранного турнира ===
def show_tournament_teams(call, tournament_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, year, location, prize_money FROM tournaments WHERE id = ?", (tournament_id,))
        tournament = cursor.fetchone()

        cursor.execute("""
            SELECT t.name, tt.placement
            FROM tournament_teams tt
            JOIN teams t ON tt.team_id = t.id
            WHERE tt.tournament_id = ?
            ORDER BY tt.placement ASC
        """, (tournament_id,))
        results = cursor.fetchall()
        cursor.close()

    if not tournament:
        bot.send_message(call.message.chat.id, "Турнир не найден.")
        return

    text = f"🏆 <b>{tournament['name']}</b> ({tournament['year']}) — {tournament['location']}\n💰 Призовой фонд: {tournament['prize_money']}$\n\n"
    if results:
        text += "📊 <b>Результаты:</b>\n\n"
        for r in results:
            text += f"{r['placement']}. {r['name']}\n"
    else:
        text += "Нет данных об участниках."

    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back_tournaments"))
    bot.send_message(call.message.chat.id, text, parse_mode="HTML", reply_markup=keyboard)

# === Поиск игрока по никнейму ===
@bot.message_handler(func=lambda message: True)
def search_player(message):
    nickname = message.text.strip()

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.nickname, p.rating, p.kpr, p.adr, t.name AS team_name
            FROM players p
            LEFT JOIN teams t ON p.team_id = t.id
            WHERE LOWER(p.nickname) = LOWER(?)
        """, (nickname,))
        player = cursor.fetchone()
        cursor.close()

    if player:
        text = (
            f"🎮 <b>{player['nickname']}</b>\n"
            f"📊 Rating 2.0: {player['rating']}\n"
            f"🔫 KPR: {player['kpr']}\n"
            f"🔥 ADR: {player['adr']}\n"
            f"🏅 Команда: {player['team_name'] or 'Без команды'}"
        )
    else:
        text = f"Игрок с ником <b>{nickname}</b> не найден."

    bot.send_message(message.chat.id, text, parse_mode="HTML")

# === Запуск ===
bot.polling(none_stop=True)
