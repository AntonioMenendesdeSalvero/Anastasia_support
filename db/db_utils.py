import sqlite3
from config import DATABASE_PATH


def init_manager_table():
    """Створює таблицю managers і додає стовпець active, якщо він відсутній."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            # Створення таблиці managers, якщо вона не існує
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS managers (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL
                )
            ''')
            conn.commit()

            # Перевірка наявності стовпця 'active'
            cursor.execute("PRAGMA table_info(managers);")
            columns = [column[1] for column in cursor.fetchall()]

            if "active" not in columns:
                cursor.execute('ALTER TABLE managers ADD COLUMN active INTEGER DEFAULT 0;')
                conn.commit()
    except sqlite3.Error as e:
        raise RuntimeError(f"Помилка створення таблиці managers або додавання стовпця active: {e}")



def init_clients_table():
    """Створює таблицю clients і додає необхідні стовпці."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            # Створення таблиці, якщо вона не існує
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    chat_id INTEGER UNIQUE
                )
            ''')
            conn.commit()

            # Додаємо стовпці, якщо вони ще не існують
            cursor.execute("PRAGMA table_info(clients);")
            columns = [column[1] for column in cursor.fetchall()]  # Отримуємо список стовпців

            if "date" not in columns:
                cursor.execute('ALTER TABLE clients ADD COLUMN date TEXT;')
            if "seo_link" not in columns:
                cursor.execute('ALTER TABLE clients ADD COLUMN seo_link TEXT;')
            if "aso_link" not in columns:
                cursor.execute('ALTER TABLE clients ADD COLUMN aso_link TEXT;')
            if "user_text" not in columns:
                cursor.execute('ALTER TABLE clients ADD COLUMN user_text TEXT;')
            if "is_sent" not in columns:
                cursor.execute('ALTER TABLE clients ADD COLUMN is_sent INTEGER DEFAULT 0;')

            conn.commit()
    except sqlite3.Error as e:
        raise RuntimeError(f"Помилка створення таблиці clients або додавання стовпців: {e}")

def is_manager(user_id: int) -> bool:
    """Перевірка чи є користувач менеджером у базі даних."""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM managers WHERE id = ?", (user_id,))
        return bool(cursor.fetchone())

def get_active_managers():
    """Отримання списку активних менеджерів."""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM managers WHERE active = 1")
        return cursor.fetchall()


def init_consultations_table():
    """Створює таблицю consultations для активних консультацій."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS consultations (
                    client_id INTEGER PRIMARY KEY,
                    manager_id INTEGER NOT NULL
                )
            ''')
            conn.commit()
    except sqlite3.Error as e:
        raise RuntimeError(f"Помилка створення таблиці consultations: {e}")

