import sqlite3
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (CallbackQuery, InlineKeyboardMarkup,
                           ReplyKeyboardMarkup, InlineKeyboardButton,
                           KeyboardButton)
from config import DATABASE_PATH, ADMIN_IDS
from aiogram.fsm.state import State, StatesGroup
from keyboard.client_key import get_manager_consultation

router = Router()


# Стан менеджера
class ManagerStates(StatesGroup):
    waiting_for_client = State()
    in_chat = State()


# Перевірка чи є користувач менеджером
def is_manager(user_id: int) -> bool:
    """Перевірка чи є користувач менеджером."""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM managers WHERE id = ?",
            (user_id,)
        )
        return bool(cursor.fetchone())


reply_keyboard = get_manager_consultation()



# @router.message(Command("start_work"))
# async def start_work(message: types.Message, state: FSMContext):
#     """Активація статусу менеджера та надсилання невідправлених заявок."""
#     user_id = message.from_user.id
#     manager_name = message.from_user.full_name
#
#     # Активуємо менеджера
#     with sqlite3.connect(DATABASE_PATH) as conn:
#         cursor = conn.cursor()
#         cursor.execute(
#             "UPDATE managers SET active = 1 WHERE id = ?",
#             (user_id,)
#         )
#         conn.commit()
#
#     await state.set_state(ManagerStates.waiting_for_client)
#     await message.answer(f"Вітаю, {manager_name}! Ви активували "
#                          f"робочий статус. Очікуйте на заявки клієнтів..."
#                          )
#
#     # Перевіряємо невідправлені заявки
#     with sqlite3.connect(DATABASE_PATH) as conn:
#         cursor = conn.cursor()
#         cursor.execute("""
#             SELECT username, full_name, seo_link, aso_link, user_text, chat_id
#             FROM clients
#             WHERE is_sent = 0
#         """)
#         pending_requests = cursor.fetchall()
#
#     # Відправка всіх невідправлених заявок
#     if pending_requests:
#         for username, full_name, seo_link, aso_link, user_text, chat_id in pending_requests:
#             # Перевіряємо, чи заявка вже знаходиться в таблиці consultations
#             with sqlite3.connect(DATABASE_PATH) as conn:
#                 cursor = conn.cursor()
#                 cursor.execute(
#                     "SELECT manager_id FROM consultations WHERE client_id = ?",
#                     (chat_id,)
#                 )
#                 consultation = cursor.fetchone()
#
#             if consultation:
#                 # Якщо заявка вже в роботі, пропускаємо її
#                 continue
#
#             # Визначаємо тему консультації
#             topic = "SEO" if seo_link else "ASO" if aso_link else "Не обрано"
#             link = seo_link if seo_link else aso_link if aso_link else "Не вказано"
#
#             # Створюємо клавіатуру для початку консультації
#             keyboard = InlineKeyboardMarkup(
#                 inline_keyboard=[
#                     [InlineKeyboardButton(
#                         text="Почати консультацію",
#                         callback_data=f"start_consult:{chat_id}"
#                     )
#                     ]
#                 ]
#             )
#
#             # Відправка заявки менеджеру
#             try:
#                 await message.bot.send_message(
#                     chat_id=user_id,
#                     text=f"Нова заявка від клієнта:\n"
#                          f"👤 Ім'я: {full_name}\n"
#                          f"🔗 Тема: {topic}\n"
#                          f"🔗 Посилання: {link}\n"
#                          f"📝 Опис проблеми: {user_text or 'Не надано'}",
#                     reply_markup=keyboard
#                 )
#
#                 # Оновлюємо статус заявки як надісланий
#                 with sqlite3.connect(DATABASE_PATH) as conn:
#                     cursor = conn.cursor()
#                     cursor.execute(
#                         "UPDATE clients SET is_sent = 1 WHERE chat_id = ?",
#                         (chat_id,)
#                     )
#                     conn.commit()
#
#             except Exception as e:
#                 print(f"Помилка надсилання заявки менеджеру {manager_name}: {e}")
#
#         await message.answer("Всі заявки, подані в неробочий час, "
#                              "були надіслані вам для обробки.")
#     else:
#         await message.answer("Немає нових заявок для обробки.")


# Команда /end_work
@router.message(Command("end_work"))
async def end_work(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE managers SET active = 0 WHERE id = ?",
            (user_id,)
        )
        conn.commit()

    await state.clear()  # Очищаємо всі активні стани менеджера
    await message.answer("Ви завершили роботу. До зустрічі!")

@router.message(Command("start_work"))
async def start_work(message: types.Message, state: FSMContext):
    """Активація статусу менеджера та надсилання невідправлених заявок."""
    user_id = message.from_user.id
    manager_name = message.from_user.full_name

    # Активуємо менеджера
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE managers SET active = 1 WHERE id = ?", (user_id,))
        conn.commit()

    await state.set_state(ManagerStates.waiting_for_client)
    await message.answer(f"Вітаю, {manager_name}! Ви активували робочий статус. Очікуйте на заявки клієнтів...")

    # Отримуємо невідправлені заявки
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT username, full_name, seo_link, aso_link, user_text, chat_id
            FROM clients
            WHERE is_sent = 0
        """)
        pending_requests = cursor.fetchall()

    # Якщо є заявки
    if pending_requests:
        for username, full_name, seo_link, aso_link, user_text, chat_id in pending_requests:
            # Перевіряємо, чи заявка вже в роботі
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT manager_id FROM consultations WHERE client_id = ?", (chat_id,))
                consultation = cursor.fetchone()

            if consultation:
                # Якщо заявка вже в роботі, пропускаємо
                continue

            # Визначаємо тему консультації
            topic = "SEO" if seo_link else "ASO" if aso_link else "Не обрано"
            link = seo_link if seo_link else aso_link if aso_link else "Не вказано"

            # Клавіатура для менеджера
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="Почати консультацію", callback_data=f"start_consult:{chat_id}")]
                ]
            )

            # Відправка заявки менеджеру
            try:
                await message.bot.send_message(
                    chat_id=user_id,
                    text=f"Нова заявка від клієнта:\n"
                         f"👤 Ім'я: {full_name}\n"
                         f"🔗 Тема: {topic}\n"
                         f"🔗 Посилання: {link}\n"
                         f"📝 Опис проблеми: {user_text or 'Не надано'}",
                    reply_markup=keyboard
                )

                # Оновлюємо статус заявки
                with sqlite3.connect(DATABASE_PATH) as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE clients SET is_sent = 1 WHERE chat_id = ?", (chat_id,))
                    conn.commit()

            except Exception as e:
                print(f"Помилка надсилання заявки менеджеру {manager_name}: {e}")

        await message.answer("Всі заявки, подані в неробочий час, були надіслані вам для обробки.")
    else:
        await message.answer("Немає нових заявок для обробки.")



@router.message(Command("end_chat"))
async def end_chat(message: types.Message, state: FSMContext):
    """Завершення консультації."""
    data = await state.get_data()
    client_chat_id = data.get("client_chat_id")

    if client_chat_id:
        try:
            # Видаляємо запис із таблиці consultations
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM consultations WHERE client_id = ?",
                    (client_chat_id,))
                conn.commit()

            await message.bot.send_message(client_chat_id, "Консультацію "
                                                           "завершено. Дякуємо за "
                                                           "звернення!")
            await message.answer("Консультацію завершено. Ви можете очікувати "
                                 "на нові заявки.")
        except Exception as e:
            print(f"Помилка завершення консультації: {e}")
    else:
        await message.answer("Наразі немає активного чату для завершення.")

    await state.clear()  # Очищаємо стани менеджера

# Надсилання заявки менеджеру
async def send_request_to_manager(bot, manager_id, client_data):
    """Надсилає заявку менеджеру."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text="Почати консультацію",
                callback_data=f"start_consult_{client_data['chat_id']}")]
        ]
    )
    await bot.send_message(
        manager_id,
        f"Нова заявка від клієнта!\n"
        f"Ім'я: {client_data['username']}\n"
        f"Тема консультації: {client_data['topic']}\n"
        f"Посилання: {client_data['link']}\n"
        f"Опис проблеми: {client_data['user_text']}",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("start_consult:"))
async def start_consultation(callback: CallbackQuery, state: FSMContext):
    client_chat_id = int(callback.data.split(":")[1])
    manager_id = callback.from_user.id

    try:
        # Перевіряємо, чи заявка вже в роботі
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT manager_id FROM consultations WHERE client_id = ?
            """, (client_chat_id,))
            result = cursor.fetchone()
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM managers WHERE id = ?
            """, (manager_id,))
            manager_name = cursor.fetchone()
        manager_name = manager_name[0]

        if result:
            # Заявка вже в роботі
            existing_manager_id = result[0]
            if existing_manager_id == manager_id:
                await callback.message.answer(
                    "Ви вже працюєте над цією заявкою."
                )
            else:
                await callback.message.answer(
                    "Заявку вже взяв в роботу інший менеджер."
                )
            await callback.answer()  # Закриваємо callback
            return

        # Додаємо заявку до таблиці consultations
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO consultations (client_id, manager_id)
                VALUES (?, ?)
            """, (client_chat_id, manager_id))
            conn.commit()

        # Початок консультації
        await state.set_state(ManagerStates.in_chat)
        await state.update_data(client_chat_id=client_chat_id)

        # Повідомлення менеджеру
        await callback.message.answer(
            "Ви почали консультацію. Тепер можете "
            "обмінюватися повідомленнями з клієнтом.")

        # Повідомлення клієнту
        await callback.bot.send_message(
            client_chat_id,
            f"Привіт 👋Мене звати {manager_name}. "
            f"Я менеджер діджитал агенції UPCORN AGENCY.  "
            f"Буду рада вам допомогти!")
        await callback.answer()

    except sqlite3.IntegrityError:
        # У разі конкурентного прийняття заявки
        await callback.message.answer("Заявку вже взяв інший менеджер.")
        await callback.answer()
    except Exception as e:
        print(f"Помилка початку консультації: {e}")
        await callback.message.answer(
            "Сталася помилка при початку консультації."
        )


@router.message(ManagerStates.in_chat)
async def chat_with_client(message: types.Message, state: FSMContext):
    """Пересилання повідомлення від менеджера до клієнта."""
    data = await state.get_data()
    client_chat_id = data.get("client_chat_id")

    if client_chat_id:
        try:
            await message.bot.send_message(
                client_chat_id,
                f"Менеджер: {message.text}"
            )
        except Exception as e:
            print(f"Помилка надсилання клієнту: {e}")
    else:
        await message.answer("Наразі немає активного чату з клієнтом.")


# Функція для отримання активного менеджера для клієнта
def get_manager_for_client(client_chat_id):
    """Отримує активного менеджера для клієнта."""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT manager_id FROM consultations
            WHERE client_id = ?
        """, (client_chat_id,))
        result = cursor.fetchone()
        return result[0] if result else None


# Обмін повідомленнями від клієнта до менеджера
@router.message()
async def client_message_handler(message: types.Message):
    """Пересилання повідомлень клієнта менеджеру."""
    client_chat_id = message.from_user.id
    manager_chat_id = get_manager_for_client(client_chat_id)

    if manager_chat_id:
        try:
            # Отримуємо ім'я клієнта з бази даних
            with sqlite3.connect(DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT full_name FROM clients WHERE chat_id = ?",
                    (client_chat_id,)
                )
                client_name = cursor.fetchone()

            # Якщо ім'я знайдено, використовуємо його, інакше ставимо "Невідомий клієнт"
            client_name = client_name[0] if client_name else "Невідомий клієнт"

            # Надсилаємо повідомлення менеджеру
            await message.bot.send_message(
                manager_chat_id,
                f"{client_name}: {message.text}"
            )
        except Exception as e:
            print(f"Помилка надсилання менеджеру: {e}")
    else:
        await message.answer(
            "На жаль, я не можу обробити ваше повідомлення зараз. "
            "Будь ласка, зачекайте, поки менеджер зв'яжеться з вами."
        )



# @router.message()
# async def client_message_handler(message: types.Message):
#     """Пересилання повідомлень клієнта менеджеру."""
#     user_id = message.from_user.id
#
#     # Якщо користувач клієнт
#     client_chat_id = message.from_user.id
#     manager_chat_id = get_manager_for_client(client_chat_id)
#
#     if manager_chat_id:
#         try:
#             await message.bot.send_message(
#                 manager_chat_id,
#                 f"Клієнт: {message.text}"
#             )
#         except Exception as e:
#             print(f"Помилка надсилання менеджеру: {e}")
#     else:
#         # Реплай-клавіатура для вибору опцій
#         reply_keyboard = ReplyKeyboardMarkup(
#             keyboard=[
#                 [KeyboardButton(text="SEO (оптимізація сайту для пошукових систем)")],
#                 [KeyboardButton(text="ASO (оптимізація додатків для магазинів додатків)")]
#             ],
#             resize_keyboard=True
#         )
#         await message.answer(
#             "На жаль, я не зовсім зрозумів ваш вибір. "
#             "Будь ласка, оберіть одну з опцій: SEO або ASO.",
#             reply_markup=reply_keyboard
#         )
#
#     # Якщо користувач адміністратор
#     if user_id in ADMIN_IDS:
#         await message.answer("Можете скористатися командою /start.")
#         return
#
#     # Якщо користувач менеджер
#     if is_manager(user_id):
#         await message.answer("Можете скористатися командою /start.")
#         return




