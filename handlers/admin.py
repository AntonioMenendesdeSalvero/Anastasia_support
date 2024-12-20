import sqlite3
from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_IDS, DATABASE_PATH

router = Router()


# Стан для процесу додавання менеджера
class AddManagerState(StatesGroup):
    waiting_for_name = State()
    waiting_for_id = State()


# Визначення станів для видалення менеджера
class RemoveManagerState(StatesGroup):
    waiting_for_manager_id = State()


# Команда /add_manager
@router.message(Command("add_manager"))
async def add_manager_start(message: types.Message, state: FSMContext):
    """Початок процесу додавання менеджера."""
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        await message.answer("У вас немає прав для цієї дії.")
        return

    await message.answer("Введіть ім'я менеджера:")
    await state.set_state(AddManagerState.waiting_for_name)


# Обробка введення імені менеджера
@router.message(AddManagerState.waiting_for_name)
async def process_manager_name(message: types.Message, state: FSMContext):
    """Зберігає ім'я менеджера та переходить до введення ID."""
    manager_name = message.text.strip()
    if not manager_name:
        await message.answer("Ім'я менеджера не може бути порожнім. Спробуйте ще раз.")
        return

    await state.update_data(manager_name=manager_name)
    await message.answer("Тепер введіть ID менеджера (число):")
    await state.set_state(AddManagerState.waiting_for_id)


# Обробка введення ID менеджера
@router.message(AddManagerState.waiting_for_id)
async def process_manager_id(message: types.Message, state: FSMContext):
    """Зберігає ID менеджера та додає його в базу."""
    try:
        manager_id = int(message.text.strip())
    except ValueError:
        await message.answer("ID має бути числом. Спробуйте ще раз:")
        return

    # Отримання даних про менеджера зі стану
    data = await state.get_data()
    manager_name = data["manager_name"]

    try:
        # Додавання менеджера в базу
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO managers (id, name) VALUES (?, ?)",
                (manager_id, manager_name)
            )
            conn.commit()

        await message.answer(
            f"Менеджера '{manager_name}' із ID {manager_id} "
            f"успішно зареєстровано."
        )
        await state.clear()  # Очищення стану
    except sqlite3.IntegrityError:
        await message.answer(
            f"Менеджер із ID {manager_id} вже існує. "
            f"Спробуйте ще раз із іншим ID."
        )
    except Exception as e:
        await message.answer(f"Сталася помилка: {e}")


# Команда для перегляду списку менеджерів
@router.message(Command("list_managers"))
async def list_managers(message: types.Message):
    """Виводить список менеджерів із бази."""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("У вас немає прав для цієї дії.")
        return

    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM managers")
            managers = cursor.fetchall()

        if not managers:
            await message.answer("Список менеджерів порожній.")
        else:
            response = "\n".join([f"{name} (ID: {manager_id})" for manager_id, name in managers])
            await message.answer(f"Список менеджерів:\n{response}")
    except Exception as e:
        await message.answer(f"Сталася помилка: {e}")


# Команда /remove_manager
@router.message(Command("remove_manager"))
async def remove_manager_start(message: types.Message, state: FSMContext):
    """Початок процесу видалення менеджера."""
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("У вас немає прав для цієї дії.")
        return

    await message.answer("Введіть ID менеджера, якого потрібно видалити:")
    await state.set_state(RemoveManagerState.waiting_for_manager_id)


# Обробка введення ID менеджера
@router.message(RemoveManagerState.waiting_for_manager_id)
async def process_manager_id(message: types.Message, state: FSMContext):
    """Обробляє ID менеджера для видалення."""
    manager_id = message.text.strip()

    # Перевірка, чи введений ID є числом
    if not manager_id.isdigit():
        await message.answer("ID має бути числом. Спробуйте ще раз.")
        return

    manager_id = int(manager_id)

    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()

            # Перевірка, чи існує менеджер у базі
            cursor.execute(
                "SELECT name FROM managers WHERE id = ?",
                (manager_id,)
            )
            manager = cursor.fetchone()

            if not manager:
                await message.answer(
                    "Менеджера з таким ID не знайдено. Спробуйте ще "
                    "раз або завершіть процес."
                )
                return

            # Видалення менеджера
            cursor.execute(
                "DELETE FROM managers WHERE id = ?",
                (manager_id,)
            )
            conn.commit()

        await message.answer(
            f"Менеджера '{manager[0]}' із "
            f"ID {manager_id} успішно видалено.")
        await state.clear()

    except Exception as e:
        await message.answer(f"Сталася помилка: {e}")
        await state.clear()
