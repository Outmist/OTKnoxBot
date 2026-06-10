import os
import re
import time
import glob
import asyncio
from threading import Thread
from collections import deque
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config import settings

# Паттерн убийства
KILL_PATTERN = re.compile(r'\[IMPORTANT\]\s+Kill:\s+"(.+?)"\s+\([^)]+\)\s+killed\s+"(.+?)"\s+\([^)]+\)')
# Паттерн хита (боевое взаимодействие)
# Пример: [INFO] Combat: "Opisal" (x,y,z) hit "Farid" (x,y,z) weapon="Вилка" damage=...
HIT_PATTERN = re.compile(r'\[INFO\]\s+Combat:\s+"(.+?)".+?hit\s+"(.+?)".+?weapon="([^"]+)"')

current_pvp_file = None
file_position = 0
observer = None
bot_instance = None

# Очередь последних hit-строк (максимум 20)
recent_hits = deque(maxlen=20)

def get_latest_pvp_file():
    pattern = os.path.join(settings.PZ_LOG_DIR, "*_pvp.txt")
    files = glob.glob(pattern)
    if not files:
        return None
    latest = max(files, key=os.path.getmtime)
    return latest

def find_weapon_for_kill(victim):
    """Ищет в recent_hits оружие, которым последний раз ударили victim."""
    # Перебираем с конца (самые свежие)
    for hit in reversed(recent_hits):
        if hit["victim"] == victim:
            return hit["weapon"]
    return "неизвестное оружие"

def send_kill_to_discord(killer, victim, weapon):
    if not bot_instance:
        return
    kill_channel_id = getattr(settings, 'DISCORD_KILL_CHANNEL_ID', 0)
    if not kill_channel_id:
        return
    channel = bot_instance.get_channel(kill_channel_id)
    if channel:
        msg = f"⚔️ **{killer}** убил **{victim}** с помощью **{weapon}**"
        future = asyncio.run_coroutine_threadsafe(
            channel.send(msg),
            bot_instance.loop
        )
        future.add_done_callback(lambda f: f.exception() if f.exception() else None)

def update_stats(killer, victim):
    import sqlite3
    db_path = getattr(settings, 'PVP_STATS_DB_PATH', None)
    if not db_path:
        db_path = os.path.join(settings.PZ_LOG_DIR, "pvp_stats.db")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kills (
                player TEXT PRIMARY KEY,
                kills INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0
            )
        ''')
        cursor.execute('INSERT INTO kills (player, kills) VALUES (?, 1) ON CONFLICT(player) DO UPDATE SET kills = kills + 1', (killer,))
        cursor.execute('INSERT INTO kills (player, deaths) VALUES (?, 1) ON CONFLICT(player) DO UPDATE SET deaths = deaths + 1', (victim,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[PVP] Ошибка БД: {e}")

def process_new_lines():
    global file_position, current_pvp_file
    if not current_pvp_file or not os.path.exists(current_pvp_file):
        return
    try:
        with open(current_pvp_file, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(file_position)
            lines = f.readlines()
            if lines:
                file_position = f.tell()
                for line in lines:
                    process_line(line)
    except Exception as e:
        print(f"[PVP] Ошибка чтения {current_pvp_file}: {e}")

def process_line(line):
    global recent_hits
    line = line.strip()
    if not line:
        return

    # Обрабатываем хит
    hit_match = HIT_PATTERN.search(line)
    if hit_match:
        attacker = hit_match.group(1)
        victim = hit_match.group(2)
        weapon = hit_match.group(3)
        recent_hits.append({
            "attacker": attacker,
            "victim": victim,
            "weapon": weapon
        })
        return

    # Обрабатываем убийство
    kill_match = KILL_PATTERN.search(line)
    if kill_match:
        killer = kill_match.group(1)
        victim = kill_match.group(2)
        weapon = find_weapon_for_kill(victim)
        print(f"[PVP] Убийство: {killer} -> {victim} (оружие: {weapon})")
        send_kill_to_discord(killer, victim, weapon)
        update_stats(killer, victim)
        return

class PVPHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.src_path.endswith("_pvp.txt"):
            return
        if event.src_path == current_pvp_file:
            process_new_lines()
        else:
            check_and_switch_file()

def check_and_switch_file():
    global current_pvp_file, file_position
    latest = get_latest_pvp_file()
    if latest is None:
        return
    if current_pvp_file is None or latest != current_pvp_file:
        print(f"[PVP] Переключение на новый pvp-файл: {os.path.basename(latest)}")
        current_pvp_file = latest
        with open(current_pvp_file, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(0, 2)
            file_position = f.tell()
        process_new_lines()

def start_pvp_monitoring(bot):
    global observer, current_pvp_file, file_position, bot_instance
    bot_instance = bot
    if not os.path.exists(settings.PZ_LOG_DIR):
        print("[PVP] Папка логов не найдена")
        return
    current_pvp_file = get_latest_pvp_file()
    if current_pvp_file is None:
        print("[PVP] Файл *_pvp.txt не найден. PVP-мониторинг отключён.")
        return
    print(f"[PVP] Отслеживаем файл: {os.path.basename(current_pvp_file)}")
    with open(current_pvp_file, 'r', encoding='utf-8', errors='ignore') as f:
        f.seek(0, 2)
        file_position = f.tell()
    event_handler = PVPHandler()
    observer = Observer()
    observer.schedule(event_handler, path=settings.PZ_LOG_DIR, recursive=False)
    observer.start()
    print("[PVP] Мониторинг PVP запущен (watchdog)")
    def periodic_check():
        while True:
            time.sleep(30)
            check_and_switch_file()
    Thread(target=periodic_check, daemon=True).start()

def stop_pvp_monitoring():
    if observer:
        observer.stop()
        observer.join()
        print("[PVP] Мониторинг PVP остановлен")