import sqlite3
from aiogram import Router, F, types
from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           ReplyKeyboardRemove, InlineKeyboardMarkup,
                           InlineKeyboardButton)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from config import DATABASE_PATH
from db.db_utils import get_active_managers

router = Router()


# Стан для клієнта
class ClientStates(StatesGroup):
    waiting_for_topic = State()
    waiting_for_seo_link = State()
    waiting_for_aso_link = State()
    waiting_for_contact = State()


# Вибір послуги (SEO/ASO)
@router.message(
    F.text.in_({"SEO (оптимізація сайту для пошукових систем)", "ASO (оптимізація додатків для магазинів додатків)"}))
async def handle_service_choice(message: types.Message, state: FSMContext):
    """Обробка вибору послуги."""
    service = message.text
    await state.update_data(service=service)

    if "SEO" in service:
        await state.set_state(ClientStates.waiting_for_seo_link)
        await message.answer(
            "Чудовий вибір! Будь ласка, вкажіть адресу вашого сайту (наприклад: https://yourwebsite.com).")
    elif "ASO" in service:
        await state.set_state(ClientStates.waiting_for_aso_link)
        await message.answer(
            "Чудово! Будь ласка, вкажіть посилання на ваш додаток у магазині (наприклад, Google Play або App Store).")


# Отримання посилання для SEO
@router.message(ClientStates.waiting_for_seo_link)
async def handle_seo_link(message: types.Message, state: FSMContext):
    """Отримання посилання для SEO."""
    seo_link = message.text
    await state.update_data(seo_link=seo_link)

    await message.answer("Дякуємо! Поділіться своїм контактом, щоб наш менеджер міг з вами зв'язатися.",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="Поділитися контактом", request_contact=True)]],
                             resize_keyboard=True
                         ))
    await state.set_state(ClientStates.waiting_for_contact)


# Отримання посилання для ASO
@router.message(ClientStates.waiting_for_aso_link)
async def handle_aso_link(message: types.Message, state: FSMContext):
    """Отримання посилання для ASO."""
    aso_link = message.text
    await state.update_data(aso_link=aso_link)

    await message.answer("Дякуємо! Поділіться своїм контактом, щоб наш менеджер міг з вами зв'язатися.",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[[KeyboardButton(text="Поділитися контактом", request_contact=True)]],
                             resize_keyboard=True
                         ))
    await state.set_state(ClientStates.waiting_for_contact)


# Отримання контакту клієнта
@router.message(F.contact)
async def handle_contact(message: types.Message, state: FSMContext):
    """Обробка контакту клієнта."""
    contact = message.contact.phone_number
    user_data = await state.get_data()
    user_id = message.from_user.id
    user_name = message.from_user.username or "Не вказано"
    full_name = message.from_user.full_name
    seo_link = user_data.get("seo_link", "Не вказано")
    aso_link = user_data.get("aso_link", "Не вказано")
    date = message.date.strftime("%Y-%m-%d")

    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            # Перевіряємо, чи запис уже існує
            cursor.execute("SELECT * FROM clients WHERE chat_id = ?", (user_id,))
            existing_client = cursor.fetchone()

            if existing_client:
                # Якщо запис існує, оновлюємо його
                cursor.execute('''
                    UPDATE clients 
                    SET username = ?, full_name = ?, date = ?, seo_link = ?, aso_link = ?
                    WHERE chat_id = ?
                ''', (user_name, full_name, date, seo_link, aso_link, user_id))
            else:
                # Якщо запису немає, додаємо новий
                cursor.execute('''
                    INSERT INTO clients (username, full_name, chat_id, date, seo_link, aso_link)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (user_name, full_name, user_id, date, seo_link, aso_link))

            conn.commit()

        # Визначення теми консультації
        topic = "SEO" if seo_link != "Не вказано" else "ASO"

        # Надсилання заявки менеджерам
        active_managers = get_active_managers()
        for manager_id, manager_name in active_managers:
            try:
                keyboard = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="Почати консультацію", callback_data=f"start_consult:{user_id}")]
                    ]
                )
                await message.bot.send_message(
                    chat_id=manager_id,
                    text=f"Нова заявка від клієнта:\n"
                         f"👤 Ім'я: {full_name}\n"
                         f"📞 Контакт: {contact}\n"
                         f"🔗 Тема: {topic}\n"
                         f"🔗 Посилання: {seo_link if topic == 'SEO' else aso_link}\n\n"
                         f"Натисніть кнопку, щоб почати консультацію.",
                    reply_markup=keyboard
                )
            except Exception as err:
                print(f"Помилка відправки заявки менеджеру {manager_name}: {err}")

        await message.answer("Дякуємо! Наш менеджер зв'яжеться з вами найближчим часом.",
                             reply_markup=ReplyKeyboardRemove())
        await state.clear()
    except sqlite3.Error as e:
        await message.answer(f"Сталася помилка збереження даних: {e}")
