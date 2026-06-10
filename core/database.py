import sqlite3
import os
import time
from config import settings

def get_top_players(limit: int = 10, retries: int = 3):
    """
    Reads the actual server stats file and returns top players by kills.
    Assumes table `player_stats` with columns `player_name`, `kills`.
    Retries on DB lock errors.
    """
    db_path = settings.STATS_DB_PATH
    if not db_path or not os.path.exists(db_path):
        return []

    for attempt in range(retries):
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

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
                print(f"Error reading DB: {e}")
                return []
        except Exception as e:
            print(f"Unexpected error: {e}")
            return []
    return []