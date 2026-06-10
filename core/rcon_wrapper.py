import concurrent.futures
import time
from config import settings

class RconWrapper:
    @staticmethod
    def send_command(command: str, timeout: int = 5) -> str:
        """
        Sends an RCON command with a timeout (default 5 seconds).
        If the server does not respond, returns an error.
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
            return "❌ RCON timeout (5 sec). Check if the server is running."
        except Exception as e:
            return f"❌ RCON error: {e}"