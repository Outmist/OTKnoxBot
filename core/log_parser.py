import os
import re
import time
import glob
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config import settings
from core import rcon_wrapper

ATTEMPT_PATTERN = re.compile(r'(\d+)\s+"(.+?)"\s+attempting to join')
ALLOWED_PATTERN = re.compile(r'(\d+)\s+"(.+?)"\s+allowed to join')
FULLY_CONNECTED_PATTERN = re.compile(r'(\d+)\s+"(.+?)"\s+fully connected')
DISCONNECT_PATTERN = re.compile(r'Connection disconnect.*?id=(\d+)')
SHUTDOWN_PATTERN = re.compile(r'(?i)(server\s*(?:quit|stopped|shutdown)|quit\.|stopping server)')

current_log_file = None
file_position = 0
observer = None
_bot = None

def get_maintenance_cog():
    if _bot:
        return _bot.get_cog('Maintenance')
    return None

def is_maintenance_active():
    cog = get_maintenance_cog()
    if cog:
        return cog.maintenance_active
    return settings.MAINTENANCE_MODE

def get_latest_log_file():
    pattern = os.path.join(settings.PZ_LOG_DIR, "*_user.txt")
    files = glob.glob(pattern)
    if not files:
        return None
    latest = max(files, key=os.path.getmtime)
    return latest

def process_new_lines():
    global file_position, current_log_file
    if not current_log_file or not os.path.exists(current_log_file):
        return
    try:
        with open(current_log_file, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(file_position)
            lines = f.readlines()
            if lines:
                file_position = f.tell()
                for line in lines:
                    process_line(line)
    except Exception as e:
        print(f"[LOG] Error reading {current_log_file}: {e}")

def process_line(line):
    line = line.strip()
    if not line:
        return

    if SHUTDOWN_PATTERN.search(line):
        print("[PZ EVENT] 🛑 Server stopped")
        return

    attempt_match = ATTEMPT_PATTERN.search(line)
    if attempt_match:
        steam_id = attempt_match.group(1)
        username = attempt_match.group(2)
        print(f"[PZ EVENT] ⏳ {username} (SteamID: {steam_id}) attempting to join...")

        if is_maintenance_active():
            admin_steamids = settings.MAINTENANCE_ADMIN_STEAMIDS
            if steam_id not in admin_steamids:
                result = rcon_wrapper.RconWrapper.send_command(f'setaccesslevel "{steam_id}" none')
                print(f"[PZ EVENT] 🚫 Denied entry to {username} (SteamID: {steam_id}) during maintenance. RCON response: {result[:100]}")
        return

    allowed_match = ALLOWED_PATTERN.search(line)
    if allowed_match:
        steam_id = allowed_match.group(1)
        username = allowed_match.group(2)
        print(f"[PZ EVENT] ✅ {username} allowed to join")
        return

    full_match = FULLY_CONNECTED_PATTERN.search(line)
    if full_match:
        steam_id = full_match.group(1)
        username = full_match.group(2)
        print(f"[PZ EVENT] 🟢 Player joined: {username} (SteamID: {steam_id})")
        return

    disconnect_match = DISCONNECT_PATTERN.search(line)
    if disconnect_match:
        steam_id = disconnect_match.group(1)
        print(f"[PZ EVENT] 🔴 Disconnected SteamID: {steam_id}")
        return

class PZLogHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.src_path.endswith("_user.txt"):
            return
        if event.src_path == current_log_file:
            process_new_lines()
        else:
            check_and_switch_file()

def check_and_switch_file():
    global current_log_file, file_position
    latest = get_latest_log_file()
    if latest is None:
        return
    if current_log_file is None or latest != current_log_file:
        print(f"[LOG] Switching to new log file: {os.path.basename(latest)}")
        current_log_file = latest
        with open(current_log_file, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(0, 2)
            file_position = f.tell()
        process_new_lines()

def start_log_monitoring(bot):
    global observer, current_log_file, file_position, _bot
    _bot = bot

    if not os.path.exists(settings.PZ_LOG_DIR):
        print(f"[LOG] Log folder does not exist: {settings.PZ_LOG_DIR}")
        return

    current_log_file = get_latest_log_file()
    if current_log_file is None:
        print("[LOG] No suitable log file found. Monitoring disabled.")
        return

    print(f"[LOG] Watching file: {os.path.basename(current_log_file)}")
    with open(current_log_file, 'r', encoding='utf-8', errors='ignore') as f:
        f.seek(0, 2)
        file_position = f.tell()

    event_handler = PZLogHandler()
    observer = Observer()
    observer.schedule(event_handler, path=settings.PZ_LOG_DIR, recursive=False)
    observer.start()
    print("[LOG] Log monitoring started (watchdog)")

    def periodic_check():
        while True:
            time.sleep(30)
            check_and_switch_file()

    Thread(target=periodic_check, daemon=True).start()

def stop_log_monitoring():
    if observer:
        observer.stop()
        observer.join()
        print("[LOG] Log monitoring stopped")