# database.py
import sqlite3

# Ваш ID администратора/тестировщика, для которого нет ограничений на повторное прохождение
ADMIN_TELEGRAM_ID = 5673599533

def init_db():
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            full_name TEXT,
            username TEXT,
            shift_type TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def check_candidate_exists(telegram_id: int) -> bool:
    # Если это ваш ID, разрешаем проходить собеседование сколько угодно раз
    if telegram_id == ADMIN_TELEGRAM_ID:
        return False
        
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM candidates WHERE telegram_id = ?", (telegram_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def save_candidate(telegram_id: int, full_name: str, username: str, shift_type: str, status: str):
    # Результаты тестов администратора можно не дублировать или сохранять перезаписью
    conn = sqlite3.connect("candidates.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO candidates (telegram_id, full_name, username, shift_type, status)
        VALUES (?, ?, ?, ?, ?)
    """, (telegram_id, full_name, username, shift_type, status))
    conn.commit()
    conn.close()

init_db()