import concurrent.futures
import time
from config import settings

class RconWrapper:
    @staticmethod
    def send_command(command: str, timeout: int = 5) -> str:
        """
        Отправляет RCON-команду с таймаутом (по умолчанию 5 секунд).
        Если сервер не отвечает, возвращает ошибку.
        """
        def _send():
            from rcon.source import Client
            with Client(
                host=settings.RCON_HOST,
                port=settings.RCON_PORT,
                passwd=settings.RCON_PASSWORD
            ) as client:
                response = client.run(command)
                return response.strip()

        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(_send)
                return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return "❌ RCON не отвечает (таймаут 5 сек). Проверьте, запущен ли сервер."
        except Exception as e:
            return f"❌ Ошибка RCON: {e}"