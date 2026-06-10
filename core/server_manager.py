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

    print(f"\n[SERVER] Starting... Folder: {server_dir}")
    if not os.path.exists(server_dir):
        print(f"[ERROR] Folder not found: {server_dir}")
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
        print(f"[SERVER] Process started, PID: {process.pid}")
        return process
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

def wait_for_server_ready(callback=None):
    """
    Waits until the server starts responding to RCON requests.
    Calls callback(stage, elapsed_seconds) every 5 seconds.
    """
    start_time = time.time()
    max_wait = 300

    print("[SERVER] Waiting for RCON readiness... (up to 5 minutes)")
    if callback:
        callback("waiting for RCON", 0)

    while time.time() - start_time < max_wait:
        elapsed = int(time.time() - start_time)
        response = RconWrapper.send_command("players")
        if not response.startswith("❌"):
            print(f"[SERVER] ✅ Server ready! (time: {elapsed}s)")
            if callback:
                callback("ready", elapsed)
            return True
        if callback and elapsed % 5 == 0:
            callback("waiting for RCON", elapsed)
        time.sleep(5)

    print("[SERVER] ❌ Timeout: server did not start within 5 minutes")
    if callback:
        callback("timeout", max_wait)
    return False