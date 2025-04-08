import random
import asyncio
from datetime import date
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
import aiosqlite
import os

API_TOKEN = os.getenv('API_TOKEN')  # Токен бота из переменных окружения

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

# Пример списка заданий
task_list = [
    "Сделай афишу концерта в стиле 80-х, используя Midjourney.",
    "Придумай логотип для бренда воды в минималистичном стиле.",
    "Создай обложку для подкаста о технологиях с акцентом на AI.",
    "Сделай баннер для NFT-выставки в духе неонового киберпанка.",
    "Придумай интерфейс приложения погоды в стиле brutalism UI."
]

# Создание базы данных при старте
async def init_db():
    async with aiosqlite.connect("users.db") as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                last_date TEXT,
                free_count INTEGER
            )
        """)
        await db.commit()

# Получение или создание пользователя
async def get_user(user_id):
    async with aiosqlite.connect("users.db") as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            row = await cursor.fetchone()
            today = date.today().isoformat()
            if row:
                if row[1] != today:
                    await db.execute("UPDATE users SET last_date = ?, free_count = ? WHERE user_id = ?",
                                     (today, 5, user_id))
                    await db.commit()
                    return {"user_id": user_id, "last_date": today, "free_count": 5}
                return {"user_id": row[0], "last_date": row[1], "free_count": row[2]}
            else:
                await db.execute("INSERT INTO users (user_id, last_date, free_count) VALUES (?, ?, ?)",
                                 (user_id, today, 5))
                await db.commit()
                return {"user_id": user_id, "last_date": today, "free_count": 5}

# Обновление количества генераций
async def update_free_count(user_id, new_count):
    async with aiosqlite.connect("users.db") as db:
        await db.execute("UPDATE users SET free_count = ? WHERE user_id = ?", (new_count, user_id))
        await db.commit()

# Команда /start
@dp.message_handler(commands=["start"])
async def start_handler(message: types.Message):
    await get_user(message.from_user.id)
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("Сгенерировать задание"))
    await message.answer("Привет! Я генератор заданий для дизайнеров. Нажми кнопку ниже, чтобы получить задание.",
                         reply_markup=kb)

# Кнопка "Сгенерировать задание"
@dp.message_handler(lambda message: message.text == "Сгенерировать задание")
async def generate_task(message: types.Message):
    user = await get_user(message.from_user.id)
    if user["free_count"] > 0:
        task = random.choice(task_list)
        await update_free_count(message.from_user.id, user["free_count"] - 1)
        await message.answer(f"Твое задание:\n\n{task}\n\nОсталось сегодня: {user['free_count'] - 1}/5")
    else:
        await message.answer("Ты использовал все 5 бесплатных заданий на сегодня.\nПриходи завтра или купи доп. задания!")

# Запуск
if __name__ == "__main__":
    asyncio.run(init_db())
    executor.start_polling(dp, skip_updates=True)
