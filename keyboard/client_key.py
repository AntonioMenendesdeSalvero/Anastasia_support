from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_manager_consultation():
    """Кнопка для зв'язку з менеджером."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="SEO (оптимізація сайту для пошукових систем)")],
            [KeyboardButton(text="ASO (оптимізація додатків для магазинів додатків)")]
        ],
        resize_keyboard=True
    )
