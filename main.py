import io
import logging
import os
import sqlite3
from datetime import date, datetime, time as dtime, timedelta
import threading
import telebot
from telebot import types

from heatmap import plot_habit_heatmap_binary

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Bot token
token = os.getenv("BOT_TOKEN")

if not token:
    raise "NO TOKEN"

bot = telebot.TeleBot(token)

# Database file path
db_path = 'habits.db'

# Track last menu message per user
global last_menu
last_menu = {}  # uid -> message_id

def init_db():
    with sqlite3.connect(db_path) as conn:
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS statuses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                status TEXT CHECK(status IN ('done','cancel'))
            )
        ''')
        conn.commit()

# Helpers
def get_habits(user_id):
    with sqlite3.connect(db_path) as conn:
        rows = conn.cursor().execute(
            'SELECT id, name FROM habits WHERE user_id = ?', (user_id,)
        ).fetchall()
    return rows

def get_habit_name(hid):
    with sqlite3.connect(db_path) as conn:
        row = conn.cursor().execute(
            'SELECT name FROM habits WHERE id = ?', (hid,)
        ).fetchone()
    return row[0] if row else ''

def get_statuses(hid):
    with sqlite3.connect(db_path) as conn:
        rows = conn.cursor().execute(
            'SELECT date, status FROM statuses WHERE habit_id = ? ORDER BY date', (hid,)
        ).fetchall()
    return rows

# Unified menu display
def send_main_menu(uid, text=None, mid=None):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('➕ Создать привычку', callback_data='menu:create'))
    markup.add(types.InlineKeyboardButton('📋 Список привычек', callback_data='menu:list'))
    display_text = text or '👋 Привет! Выберите действие:'
    try:
        if mid:
            bot.edit_message_text(display_text, uid, mid, reply_markup=markup)
            last_menu[uid] = mid
        elif uid in last_menu:
            bot.edit_message_text(display_text, uid, last_menu[uid], reply_markup=markup)
        else:
            msg = bot.send_message(uid, display_text, reply_markup=markup)
            last_menu[uid] = msg.message_id
    except:
        msg = bot.send_message(uid, display_text, reply_markup=markup)
        last_menu[uid] = msg.message_id

# Handlers
def start(msg):
    send_main_menu(msg.chat.id)
bot.register_message_handler(start, commands=['start'])

@bot.callback_query_handler(lambda c: c.data.startswith('menu:'))
def main_menu_handler(cq):
    bot.answer_callback_query(cq.id)
    action = cq.data.split(':')[1]
    uid = cq.message.chat.id
    mid = cq.message.message_id
    if action == 'create':
        # Prompt for new habit name with back button
        back_markup = types.InlineKeyboardMarkup()
        back_markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data='menu:back'))
        bot.edit_message_text('🧐 Введите название новой привычки:', uid, mid, reply_markup=back_markup)
        bot.register_next_step_handler_by_chat_id(uid, create_habit, mid)
    elif action == 'list':
        habits = get_habits(uid)
        if not habits:
            send_main_menu(uid, text='ℹ️ У вас нет привычек.', mid=mid)
        else:
            markup = types.InlineKeyboardMarkup()
            for hid, name in habits:
                markup.add(types.InlineKeyboardButton(f'📖 {name}', callback_data=f'habit:show:{hid}'))
            # add back button
            markup.add(types.InlineKeyboardButton('🔙 Назад', callback_data='menu:back'))
            bot.edit_message_text('📋 Ваши привычки:', uid, mid, reply_markup=markup)
            last_menu[uid] = mid
    elif action == 'back':
        send_main_menu(uid, mid=mid)

@bot.callback_query_handler(lambda c: c.data.startswith('habit:'))
def habit_action_handler(cq):
    bot.answer_callback_query(cq.id)
    parts = cq.data.split(':')
    action, hid = parts[1], parts[2]
    uid = cq.message.chat.id
    mid = cq.message.message_id
    # prepare back button
    back_btn = types.InlineKeyboardButton('🔙 Назад', callback_data='menu:back')
    name = get_habit_name(hid)
    if action == 'show':
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton('✏️ Переименовать', callback_data=f'habit:rename:{hid}'))
        mk.add(types.InlineKeyboardButton('🗑️ Удалить', callback_data=f'habit:delete:{hid}'))
        mk.add(types.InlineKeyboardButton('📊 Просмотреть статусы', callback_data=f'habit:view:{hid}'))
        mk.add(back_btn)
        bot.edit_message_text(f'🔹 Привычка «{name}»:', uid, mid, reply_markup=mk)
        last_menu[uid] = mid
    elif action == 'delete':
        with sqlite3.connect(db_path) as conn:
            conn.cursor().execute(
                'DELETE FROM habits WHERE id = ? AND user_id = ?', (hid, uid)
            )
            conn.commit()
        send_main_menu(uid, text='✅ Привычка удалена.', mid=mid)
    elif action == 'rename':
        bot.edit_message_text('✏️ Введите новое название:', uid, mid, reply_markup=None)
        bot.register_next_step_handler_by_chat_id(uid, rename_habit, hid, mid)
    elif action == 'status':
        status = parts[3]
        today = date.today().isoformat()
        with sqlite3.connect(db_path) as conn:
            conn.cursor().execute(
                'INSERT INTO statuses(habit_id, date, status) VALUES(?,?,?)', (hid, today, status)
            )
            conn.commit()
        # send_main_menu(uid, text=f'🎉 Привычка отмечена как {"✅ done" if status=="done" else "❌ cancel"}.', mid=mid)
        # cq.message.delete()
        bot.delete_message(uid, cq.message.message_id)
    elif action == 'view':
        statuses = get_statuses(hid)
        statuses = {dt: 1 if st == "done" else 0 for dt, st in statuses}
        buff = plot_habit_heatmap_binary(
            statuses,
            datetime.now().date() - timedelta(days=365),
            datetime.now().date(),
            name
        )
        buff = io.BytesIO(buff)
        buff.name = 'heatmap.png'


        back_btn = types.InlineKeyboardButton('🔙 Назад', callback_data='menu:back')
        mk = types.InlineKeyboardMarkup()
        mk.add(back_btn)
        bot.send_photo(chat_id=uid, photo=buff, caption='Ваш график за год',reply_markup=mk)

# Next-step handlers
def create_habit(msg, mid):
    uid = msg.chat.id
    bot.delete_message(uid, msg.message_id)
    name = msg.text.strip()
    if not name:
        send_main_menu(uid, text='⚠️ Название не может быть пустым.', mid=mid)
    else:
        with sqlite3.connect(db_path) as conn:
            conn.cursor().execute(
                'INSERT INTO habits(user_id, name) VALUES(?, ?)', (uid, name)
            )
            conn.commit()
        send_main_menu(uid, text=f'🎉 Привычка «{name}» создана!', mid=mid)


def rename_habit(msg, hid, mid):
    uid = msg.chat.id
    bot.delete_message(uid, msg.message_id)
    new_name = msg.text.strip()
    if not new_name:
        send_main_menu(uid, text='⚠️ Ошибка при переименовании.', mid=mid)
    else:
        with sqlite3.connect(db_path) as conn:
            conn.cursor().execute(
                'UPDATE habits SET name = ? WHERE id = ?', (new_name, hid)
            )
            conn.commit()
        send_main_menu(uid, text='✔️ Название изменено.', mid=mid)

# Daily reminders
def schedule_reminders():
    now = datetime.now()
    next_run = datetime.combine(date.today(), dtime(hour=22))
    if now > next_run:
        next_run = next_run.replace(day=now.day + 1)
    delay = (next_run - now).total_seconds()
    threading.Timer(delay, do_remind).start()

def do_remind():
    today = date.today().isoformat()
    with sqlite3.connect(db_path) as conn:
        users = [row[0] for row in conn.cursor().execute(
            'SELECT DISTINCT user_id FROM habits'
        ).fetchall()]
    for uid in users:
        for hid, _ in get_habits(uid):
            name = get_habit_name(hid)
            mk = types.InlineKeyboardMarkup()
            mk.add(
                types.InlineKeyboardButton('✅ Done', callback_data=f'habit:status:{hid}:done'),
                types.InlineKeyboardButton('❌ Cancel', callback_data=f'habit:status:{hid}:cancel')
            )
            mk.add(types.InlineKeyboardButton('🔙 Назад', callback_data='menu:back'))
            bot.send_message(
                chat_id=uid, text=f'⏰ Привычка «{name}» на {today}:', reply_markup=mk
            )
    schedule_reminders()

# Entry point
def main():
    init_db()
    schedule_reminders()
    bot.polling()

if __name__ == '__main__':
    main()
