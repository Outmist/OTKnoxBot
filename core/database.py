import sqlite3
import os
import time
from config import settings

def get_top_players(limit: int = 10, retries: int = 3):
    """
    Читает реальный файл статистики сервера и возвращает топ игроков по убийствам.
    Предполагается таблица `player_stats` с колонками `player_name`, `kills`.
    При ошибке блокировки БД выполняет повторные попытки.
    """
    db_path = settings.STATS_DB_PATH
    if not db_path or not os.path.exists(db_path):
        return []  # файл отсутствует

    for attempt in range(retries):
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Попытка запроса — если структура другая, поменяйте имена таблицы/колонок
            cursor.execute(
                "SELECT player_name, kills FROM player_stats ORDER BY kills DESC LIMIT ?",
                (limit,)
            )
            rows = cursor.fetchall()
            result = [(row["player_name"], row["kills"]) for row in rows]
            conn.close()
            return result

        except sqlite3.OperationalError as e:
            conn.close()
            if "locked" in str(e).lower() and attempt < retries - 1:
                time.sleep(0.2)
                continue
            else:
                # Неизвестная структура или другая ошибка
                print(f"Ошибка чтения БД: {e}")
                return []
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")
            return []
    return []