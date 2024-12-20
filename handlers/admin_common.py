import sqlite3
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import DATABASE_PATH, ADMIN_IDS
import pandas as pd

router = Router()


# Стан для розсилки
class BroadcastStates(StatesGroup):
    waiting_for_message = State()


# Функція для отримання клієнтів із бази
def get_all_clients():
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id FROM clients")
        return [row[0] for row in cursor.fetchall()]


# Функція для отримання клієнтів з бази даних
def get_all_clients_data():
    """Отримує всі дані клієнтів із бази даних."""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, full_name, chat_id, date, seo_link, aso_link, user_text 
            FROM clients
        ''')
        return cursor.fetchall()


# Команда /broadcast: Запуск розсилки
@router.message(Command("broadcast"))
async def start_broadcast(message: types.Message, state: FSMContext):
    """Команда для запуску розсилки."""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("У вас немає прав для цієї команди.")
        return

    await state.set_state(BroadcastStates.waiting_for_message)
    await message.answer("Надішліть текст або текст із фото для розсилки.")


# Обробка текстового повідомлення або фото
@router.message(BroadcastStates.waiting_for_message, F.content_type.in_(['text', 'photo']))
async def handle_broadcast_message(message: types.Message, state: FSMContext):
    """Отримання тексту або фото для розсилки."""
    clients = get_all_clients()

    if not clients:
        await message.answer("У базі немає клієнтів для розсилки.")
        await state.clear()
        return

    # Збереження контенту для розсилки
    content = {"text": message.text}
    photo = None

    if message.photo:
        photo = message.photo[-1].file_id  # Останнє фото найвищої якості
        caption = message.caption or ""
        content = {"photo": photo, "caption": caption}

    # Надсилання розсилки всім клієнтам
    sent_count = 0
    failed_count = 0

    for chat_id in clients:
        try:
            if photo:  # Якщо є фото
                await message.bot.send_photo(chat_id, photo=content['photo'], caption=content['caption'])
            else:  # Якщо лише текст
                await message.bot.send_message(chat_id, content['text'])
            sent_count += 1
        except Exception as e:
            failed_count += 1
            print(f"Помилка надсилання до {chat_id}: {e}")

    # Відповідь адмінам про результат розсилки
    await message.answer(f"✅ Розсилку завершено!\n"
                         f"Успішно надіслано: {sent_count}\n"
                         f"Не вдалося надіслати: {failed_count}")

    await state.clear()


# Команда /download_clients
@router.message(Command("download_clients"))
async def download_clients(message: types.Message):
    """Команда для завантаження бази клієнтів у форматі Excel."""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("У вас немає прав для цієї команди.")
        return

    # Отримання даних клієнтів
    clients_data = get_all_clients_data()

    if not clients_data:
        await message.answer("База клієнтів порожня.")
        return

    # Формування Excel-файлу
    columns = ["ID", "Username", "Full Name", "Chat ID", "Date", "SEO Link", "ASO Link", "User Text"]
    df = pd.DataFrame(clients_data, columns=columns)

    file_path = "clients_data.xlsx"
    df.to_excel(file_path, index=False)

    # Відправка файлу адміністратору
    await message.answer_document(types.FSInputFile(file_path), caption="База клієнтів успішно завантажена.")
