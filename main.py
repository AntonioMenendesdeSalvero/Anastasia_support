import sqlite3
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from keyboard.client_key import get_manager_consultation
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN, ADMIN_IDS, DATABASE_PATH
from db.db_utils import (init_manager_table, init_clients_table,
                         is_manager, init_consultations_table)
from handlers import admin, client_record, manager, admin_common
import logging

# Перевіряємо наявність папки для логів
if not os.path.exists("logs"):
    os.makedirs("logs")
# Ініціалізація логування
logging.basicConfig(level=logging.INFO, filename='logs/bot.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Ініціалізація бази даних
init_manager_table()
init_clients_table()
init_consultations_table()

# Ініціалізація бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


@dp.message(CommandStart())
async def start_handler(message: types.Message):
    """Обробка команди /start."""
    user_id = message.from_user.id

    # Для адміністратора
    if user_id in ADMIN_IDS:
        await message.answer(
            "Привіт, адміністраторе! Ось доступні команди:\n"
            "/add_manager — Додати менеджера\n"
            "/list_managers — Переглянути список менеджерів\n"
            "/remove_manager — Видалити менеджера\n"
            "/broadcast - Зробити розсилку\n"
            "/download_clients — Завантажити базу клієнтів.\n"
            "\nВітаю, менеджере! Оберіть дію:\n"
            "/start_work – Почати роботу\n"
            "/end_work – Завершити роботу\n"
            "/end_chat - Завершити чат з користувачем"
        )
    # Для менеджера
    elif is_manager(user_id):
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM managers WHERE id = ?",
                (user_id,)
            )
            manager_name = cursor.fetchone()[0]
        await message.answer(
            f"Вітаю, менеджере {manager_name}! Оберіть дію:\n"
            "/start_work – Почати роботу\n"
            "/end_work – Завершити роботу\n"
            "/end_chat - Завершити чат з користувачем"
        )
    # Для клієнта
    else:
        # Реплай-клавіатура для зв'язку з менеджером
        reply_keyboard = get_manager_consultation()
        await message.answer(
            "Привіт! Яка послуга вас цікавить? Оберіть один з варіантів:\n"
            "- SEO (оптимізація сайту для пошукових систем)\n"
            "- ASO (оптимізація додатків для магазинів додатків)",
            reply_markup=reply_keyboard
        )


# Реєстрація маршрутів
dp.include_router(admin.router)  # запуск функціоналу адміна
dp.include_router(admin_common.router)  # завантаження бази та розсилка
dp.include_router(client_record.router)  # запис клієнта на консультацію
dp.include_router(manager.router)  # консультація клієнта менеджером

if __name__ == "__main__":
    dp.run_polling(bot)
