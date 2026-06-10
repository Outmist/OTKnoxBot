import os
import re
import time
import glob
import asyncio
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config import settings

CHAT_PATTERN = re.compile(r'Got message:ChatMessage\{chat=(.+?), author=[\'"](.+?)[\'"], text=[\'"](.+?)[\'"]\}')

ALLOWED_CHATS = ["Общий", "All", "General"]  # Keep original chat names as they appear in logs

current_chat_file = None
file_position = 0
observer = None
bot_instance = None

def get_latest_chat_file():
    pattern = os.path.join(settings.PZ_LOG_DIR, "*_chat.txt")
    files = glob.glob(pattern)
    if not files:
        return None
    latest = max(files, key=os.path.getmtime)
    return latest

def send_to_discord(channel_id, author, text):
    if not bot_instance or not channel_id:
        return
    channel = bot_instance.get_channel(channel_id)
    if channel:
        future = asyncio.run_coroutine_threadsafe(
            channel.send(f"**{author}** (in-game): {text}"),
            bot_instance.loop
        )
        future.add_done_callback(lambda f: f.exception() if f.exception() else None)

def process_new_lines():
    global file_position, current_chat_file
    if not current_chat_file or not os.path.exists(current_chat_file):
        return
    try:
        with open(current_chat_file, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(file_position)
            lines = f.readlines()
            if lines:
                file_position = f.tell()
                for line in lines:
                    process_line(line)
    except Exception as e:
        print(f"[CHAT] Error reading {current_chat_file}: {e}")

def process_line(line):
    line = line.strip()
    if not line:
        return
    match = CHAT_PATTERN.search(line)
    if match:
        chat_name = match.group(1)
        author = match.group(2)
        text = match.group(3)

        if chat_name not in ALLOWED_CHATS:
            print(f"[CHAT] Skipped chat '{chat_name}' from {author}")
            return

        if text.startswith("[Discord]"):
            return

        print(f"[CHAT] General chat: {author}: {text}")
        send_to_discord(settings.DISCORD_CHAT_CHANNEL_ID, author, text)

class ChatLogHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.src_path.endswith("_chat.txt"):
            return
        if event.src_path == current_chat_file:
            process_new_lines()
        else:
            check_and_switch_file()

def check_and_switch_file():
    global current_chat_file, file_position
    latest = get_latest_chat_file()
    if latest is None:
        return
    if current_chat_file is None or latest != current_chat_file:
        print(f"[CHAT] Switching to new chat file: {os.path.basename(latest)}")
        current_chat_file = latest
        with open(current_chat_file, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(0, 2)
            file_position = f.tell()
        process_new_lines()

def start_chat_monitoring(bot):
    global observer, current_chat_file, file_position, bot_instance
    bot_instance = bot
    if not os.path.exists(settings.PZ_LOG_DIR):
        print(f"[CHAT] Log folder does not exist: {settings.PZ_LOG_DIR}")
        return
    current_chat_file = get_latest_chat_file()
    if current_chat_file is None:
        print("[CHAT] *_chat.txt not found. Chat bridge disabled.")
        return
    print(f"[CHAT] Watching file: {os.path.basename(current_chat_file)}")
    with open(current_chat_file, 'r', encoding='utf-8', errors='ignore') as f:
        f.seek(0, 2)
        file_position = f.tell()
    event_handler = ChatLogHandler()
    observer = Observer()
    observer.schedule(event_handler, path=settings.PZ_LOG_DIR, recursive=False)
    observer.start()
    print("[CHAT] Chat monitoring started (watchdog)")
    def periodic_check():
        while True:
            time.sleep(30)
            check_and_switch_file()
    Thread(target=periodic_check, daemon=True).start()

def stop_chat_monitoring():
    if observer:
        observer.stop()
        observer.join()
        print("[CHAT] Chat monitoring stopped")