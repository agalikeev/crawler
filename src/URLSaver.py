import sqlite3
from datetime import datetime


def save_url_to_sqlite(url: str, content: str):
    try:
        # Подключение к базе данных (файл создастся автоматически)
        conn = sqlite3.connect('urls.db')
        cursor = conn.cursor()

        # Создание таблицы, если её нет
        cursor.execute('''CREATE TABLE IF NOT EXISTS urls
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          url TEXT NOT NULL,
                          content TEXT,
                          created_at TIMESTAMP)''')

        # Вставка данных
        cursor.execute('''INSERT INTO urls (url, content, created_at)
                          VALUES (?, ?, ?)''',
                       (url, content, datetime.now()))

        # Сохранение изменений
        conn.commit()
        print("Ссылка успешно сохранена в SQLite")

    except sqlite3.Error as e:
        print(f"Ошибка при работе с SQLite: {e}")
    finally:
        if conn:
            conn.close()
            print("Соединение с SQLite закрыто")
