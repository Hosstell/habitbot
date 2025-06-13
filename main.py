import asyncio
import io
import logging
import os
import sqlite3
from datetime import date, datetime, time as dtime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardButton, InlineKeyboardMarkup,
    BufferedInputFile  # <- добавили здесь
)

from heatmap import plot_habit_heatmap_binary

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Bot token
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not set")

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Database
db_path = '/db/habits.db'

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

def get_habits(user_id: int) -> list[tuple[int,str]]:
    with sqlite3.connect(db_path) as conn:
        return conn.cursor().execute(
            'SELECT id, name FROM habits WHERE user_id = ?', (user_id,)
        ).fetchall()

def get_habit_name(hid: int) -> str:
    with sqlite3.connect(db_path) as conn:
        row = conn.cursor().execute(
            'SELECT name FROM habits WHERE id = ?', (hid,)
        ).fetchone()
    return row[0] if row else ''

def get_statuses(hid: int) -> dict[str,int]:
    with sqlite3.connect(db_path) as conn:
        rows = conn.cursor().execute(
            'SELECT date, status FROM statuses WHERE habit_id = ? ORDER BY date', (hid,)
        ).fetchall()
    return {dt: 1 if st == "done" else 0 for dt, st in rows}

# Track last menu per user
last_menu: dict[int,int] = {}

# FSM
class Form(StatesGroup):
    create = State()
    rename = State()

# ——— Меню ———

async def send_main_menu(
        chat_id: int,
        text: str = '👋 Привет! Выберите действие:',
        message_id: int | None = None
):
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='➕ Создать привычку', callback_data='menu:create')],
            [InlineKeyboardButton(text='📋 Список привычек',   callback_data='menu:list')],
        ]
    )
    try:
        if message_id:
            await bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
        elif last_menu.get(chat_id):
            await bot.edit_message_text(text, chat_id, last_menu[chat_id], reply_markup=markup)
        else:
            msg = await bot.send_message(chat_id, text, reply_markup=markup)
            last_menu[chat_id] = msg.message_id
    except:
        msg = await bot.send_message(chat_id, text, reply_markup=markup)
        last_menu[chat_id] = msg.message_id

# ——— Хендлеры ———

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await send_main_menu(message.from_user.id)

@dp.callback_query(F.data.startswith('menu:'))
async def main_menu(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    action = cb.data.split(':')[1]
    uid = cb.from_user.id
    mid = cb.message.message_id

    if action == 'create':
        markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='🔙 Назад', callback_data='menu:back')],
            ]
        )
        await cb.message.edit_text('🧐 Введите название новой привычки:', reply_markup=markup)
        await state.set_state(Form.create)

    elif action == 'list':
        habits = get_habits(uid)
        if not habits:
            await send_main_menu(uid, text='ℹ️ У вас нет привычек.', message_id=mid)
        else:
            rows = [
                [InlineKeyboardButton(text=f'📖 {name}', callback_data=f'habit:show:{hid}')]
                for hid, name in habits
            ]
            rows.append([InlineKeyboardButton(text='🔙 Назад', callback_data='menu:back')])
            markup = InlineKeyboardMarkup(inline_keyboard=rows)
            await cb.message.edit_text('📋 Ваши привычки:', reply_markup=markup)
            last_menu[uid] = mid

    elif action == 'back':
        await send_main_menu(uid, message_id=mid)

@dp.message(Form.create)
async def process_create(message: Message, state: FSMContext):
    uid = message.from_user.id
    name = message.text.strip()
    await message.delete()
    if not name:
        await send_main_menu(uid, text='⚠️ Название не может быть пустым.')
    else:
        with sqlite3.connect(db_path) as conn:
            conn.cursor().execute(
                'INSERT INTO habits(user_id, name) VALUES(?, ?)', (uid, name)
            )
            conn.commit()
        await send_main_menu(uid, text=f'🎉 Привычка «{name}» создана!')
    await state.clear()

@dp.callback_query(F.data.startswith('habit:show:'))
async def habit_show(cb: CallbackQuery):
    await cb.answer()
    _, _, hid = cb.data.split(':')
    uid = cb.from_user.id
    mid = cb.message.message_id
    name = get_habit_name(int(hid))

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='✏️ Переименовать', callback_data=f'habit:rename:{hid}')],
            [InlineKeyboardButton(text='🗑️ Удалить',       callback_data=f'habit:delete:{hid}')],
            [InlineKeyboardButton(text='📊 Просмотреть статусы', callback_data=f'habit:view:{hid}')],
            [InlineKeyboardButton(text='🔙 Назад', callback_data='menu:back')],
        ]
    )
    await cb.message.edit_text(f'🔹 Привычка «{name}»:', reply_markup=markup)
    last_menu[uid] = mid

@dp.callback_query(F.data.startswith('habit:delete:'))
async def habit_delete(cb: CallbackQuery):
    await cb.answer()
    _, _, hid = cb.data.split(':')
    uid = cb.from_user.id
    with sqlite3.connect(db_path) as conn:
        conn.cursor().execute(
            'DELETE FROM habits WHERE id = ? AND user_id = ?', (hid, uid)
        )
        conn.commit()
    await send_main_menu(uid, text='✅ Привычка удалена.')

@dp.callback_query(F.data.startswith('habit:rename:'))
async def habit_rename_start(cb: CallbackQuery, state: FSMContext):
    await cb.answer()
    _, _, hid = cb.data.split(':')
    await cb.message.edit_text('✏️ Введите новое название:')
    await state.update_data(renaming_id=int(hid))
    await state.set_state(Form.rename)

@dp.message(Form.rename, F.text)
async def process_rename(message: Message, state: FSMContext):
    data = await state.get_data()
    hid = data.get('renaming_id')
    new_name = message.text.strip()
    await message.delete()
    if hid and new_name:
        with sqlite3.connect(db_path) as conn:
            conn.cursor().execute(
                'UPDATE habits SET name = ? WHERE id = ?', (new_name, hid)
            )
            conn.commit()
        await send_main_menu(message.from_user.id, text='✔️ Название изменено.')
    else:
        await send_main_menu(message.from_user.id, text='⚠️ Ошибка при переименовании.')
    await state.clear()

@dp.callback_query(F.data.startswith('habit:view:'))
async def habit_view(cb: CallbackQuery):
    await cb.answer()
    _, _, hid = cb.data.split(':')
    uid = cb.from_user.id

    # Генерируем изображение
    img_bytes = plot_habit_heatmap_binary(
        get_statuses(int(hid)),
        datetime.now().date() - timedelta(days=365),
        datetime.now().date(),
        get_habit_name(int(hid))
    )
    file = BufferedInputFile(img_bytes, filename='heatmap.png')

    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='🔙 Назад', callback_data='menu:back')]
        ]
    )

    # await bot.send_photo(chat_id=uid, photo=bio, caption='Ваш график за год', reply_markup=markup)
    await bot.send_photo(chat_id=uid, photo=file, caption='Ваш график за год', reply_markup=markup)

# Напоминания
async def reminder_loop():
    while True:
        now = datetime.now()
        next_run = datetime.combine(date.today(), dtime(hour=22))
        if now > next_run:
            next_run += timedelta(days=1)
        await asyncio.sleep((next_run - now).total_seconds())

        today = date.today().isoformat()
        with sqlite3.connect(db_path) as conn:
            users = [r[0] for r in conn.cursor().execute(
                'SELECT DISTINCT user_id FROM habits'
            ).fetchall()]

        for uid in users:
            for hid, name in get_habits(uid):
                rows = [
                    [
                        InlineKeyboardButton(text='✅ Done',   callback_data=f'habit:status:{hid}:done'),
                        InlineKeyboardButton(text='❌ Cancel', callback_data=f'habit:status:{hid}:cancel'),
                    ],
                    [InlineKeyboardButton(text='🔙 Назад', callback_data='menu:back')]
                ]
                markup = InlineKeyboardMarkup(inline_keyboard=rows)
                await bot.send_message(
                    uid,
                    f'⏰ Привычка «{name}» на {today}:',
                    reply_markup=markup
                )

async def main():
    init_db()
    asyncio.create_task(reminder_loop())
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())
