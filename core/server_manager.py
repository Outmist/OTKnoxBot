import subprocess
import os
import time
from config import settings
from core.rcon_wrapper import RconWrapper

def start_server_process():
    server_dir = settings.PZ_SERVER_DIR
    start_script = "StartServer64.bat"
    server_name = settings.PZ_SERVER_NAME
    start_command = f'"{os.path.join(server_dir, start_script)}" "{server_name}"'

    print(f"\n[СЕРВЕР] Запуск... Папка: {server_dir}")
    if not os.path.exists(server_dir):
        print(f"[ОШИБКА] Папка не найдена: {server_dir}")
        return None

    try:
        process = subprocess.Popen(
            start_command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            shell=True
        )
        print(f"[СЕРВЕР] Процесс запущен, PID: {process.pid}")
        return process
    except Exception as e:
        print(f"[ОШИБКА] {e}")
        return None

def wait_for_server_ready(callback=None):
    """
    Ожидает, пока сервер не начнёт отвечать на RCON-запросы.
    Вызывает callback(stage, elapsed_seconds) каждые 5 секунд.
    """
    start_time = time.time()
    max_wait = 300  # 5 минут

    print("[СЕРВЕР] Ожидание готовности RCON... (до 5 минут)")
    if callback:
        callback("ожидание RCON", 0)

    while time.time() - start_time < max_wait:
        elapsed = int(time.time() - start_time)
        # Пробуем выполнить простую команду
        response = RconWrapper.send_command("players")
        if not response.startswith("❌"):
            print(f"[СЕРВЕР] ✅ Сервер готов! (время: {elapsed}с)")
            if callback:
                callback("готов", elapsed)
            return True
        if callback and elapsed % 5 == 0:
            callback("ожидание RCON", elapsed)
        time.sleep(5)

    print("[СЕРВЕР] ❌ Таймаут: сервер не запустился за 5 минут")
    if callback:
        callback("таймаут", max_wait)
    return False