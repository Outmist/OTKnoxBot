import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    RCON_HOST = os.getenv('RCON_HOST')
    RCON_PORT = int(os.getenv('RCON_PORT', 27015))
    RCON_PASSWORD = os.getenv('RCON_PASSWORD')
    STATS_DB_PATH = os.getenv('PZ_STATS_DB_PATH')
    PZ_SERVER_DIR = os.getenv('PZ_SERVER_DIR')
    PZ_SERVER_NAME = os.getenv('PZ_SERVER_NAME', 'servertest')
    PZ_LOG_DIR = os.getenv('PZ_LOG_DIR')
    DISCORD_CHAT_CHANNEL_ID = int(os.getenv('DISCORD_CHAT_CHANNEL_ID', 0))
    DISCORD_KILL_CHANNEL_ID = int(os.getenv('DISCORD_KILL_CHANNEL_ID', 0))
    AUTO_RESTART_ENABLED = os.getenv('AUTO_RESTART_ENABLED', 'False').lower() == 'true'
    MAINTENANCE_ADMIN_STEAMIDS = os.getenv('MAINTENANCE_ADMIN_STEAMIDS', '').split(',') if os.getenv('MAINTENANCE_ADMIN_STEAMIDS') else []
    
    _pvp_db = os.getenv('PVP_STATS_DB_PATH', '')
    if _pvp_db:
        PVP_STATS_DB_PATH = _pvp_db
    else:
        PVP_STATS_DB_PATH = os.path.join(PZ_LOG_DIR, "pvp_stats.db") if PZ_LOG_DIR else ""
    
    MAINTENANCE_MODE = os.getenv('MAINTENANCE_MODE', 'False').lower() == 'true'

    @classmethod
    def validate(cls):
        if not cls.DISCORD_TOKEN:
            raise ValueError("DISCORD_TOKEN is not set в .env")
        if not cls.RCON_HOST or not cls.RCON_PASSWORD:
            raise ValueError("RCON_HOST or RCON_PASSWORD is not set")
        if not cls.STATS_DB_PATH:
            raise ValueError("PZ_STATS_DB_PATH is not set in .env")
        if not cls.PZ_SERVER_DIR:
            raise ValueError("PZ_SERVER_DIR is not set in .env")
        if not cls.PZ_LOG_DIR:
            raise ValueError("PZ_LOG_DIR is not set in .env")
        print(f"[CONFIG] Auto restart: {'ON' if cls.AUTO_RESTART_ENABLED else 'OFF'}")
        print(f"[CONFIG] Maintenance mode: {'ON' if cls.MAINTENANCE_MODE else 'OFF'}")

settings = Settings()
settings.validate()