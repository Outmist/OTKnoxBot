	Discord Bot for Project Zomboid Dedicated Server (B42+)
Author: Outmist

-------------------------------------------------------------------------------
DESCRIPTION
-------------------------------------------------------------------------------
Full server management via Discord:
- Start / stop / restart server
- Player online & status monitoring (RCON)
- PvP statistics + kill feed
- Auto-restart every 4 hours (configurable)
- Maintenance mode (block non-admin players)
- Top PvP players (/topkills)
- Execute any RCON command (/rcon)

-------------------------------------------------------------------------------
REQUIREMENTS
-------------------------------------------------------------------------------
- Windows / Linux (tested on Windows)
- Python 3.10+
- Project Zomboid Dedicated Server (configured, with RCON enabled)
- Discord bot with MESSAGE CONTENT INTENT enabled
- Game logs: chat.txt, connections.txt, pvp.txt (auto-generated)
- discord.py>=2.3.0
- rcon>=1.0.0
- watchdog>=4.0.0
- python-dotenv>=1.0.0

-------------------------------------------------------------------------------
INSTALLATION
-------------------------------------------------------------------------------
1. Clone or copy bot files into a folder (e.g., C:\OTDNXBOT)
2. Install dependencies: pip install -r requirements.txt
3. Copy .env.example to .env and edit it (see below)
4. Run: python main.py

-------------------------------------------------------------------------------
CONFIGURATION (.env)
-------------------------------------------------------------------------------
1. REQUIRED:
 - DISCORD_TOKEN=your_bot_token
 - RCON_HOST=localhost
 - RCON_PORT=27015
 - RCON_PASSWORD=your_rcon_password
 - PZ_SERVER_DIR=C:\pzserver
 - PZ_SERVER_NAME=servertest
 - PZ_LOG_DIR=C:\Users\Admin\Zomboid\Logs
 - DISCORD_CHAT_CHANNEL_ID=1234567890

1. OPTIONAL:
 - PVP_STATS_DB_PATH=C:\path\to\pvp_stats.db
 - DISCORD_KILL_CHANNEL_ID=1234567890 (0 to disable)
 - AUTO_RESTART_ENABLED=True
 - MAINTENANCE_MODE=False
 - MAINTENANCE_ADMIN_STEAMIDS=765611...,765612...

-------------------------------------------------------------------------------
SLASH COMMANDS
-------------------------------------------------------------------------------
- /status          - Show online players
- /start_pz        - Start server (with progress)
- /restart <min>   - Scheduled restart with in-game warnings
- /rcon <cmd>      - Send any RCON command
- /help            - List commands
- /topkills        - Top PvP killers
- /maintenance on/off - Toggle maintenance mode (blocks non-admins)
-------------------------------------------------------------------------------
TROUBLESHOOTING
-------------------------------------------------------------------------------
- Bot doesn't respond to messages: check DISCORD_CHAT_CHANNEL_ID,
  MESSAGE CONTENT INTENT in Discord Developer Portal, and bot's channel
  permissions.

- RCON connection error: verify RCON_PORT, RCON_PASSWORD, and that the server
  is fully started (firewall open).

- /topkills shows no data: ensure pvp_stats.db exists (default in log folder)
  and that kill lines appear in pvp.txt.

- Maintenance mode doesn't block players: verify MAINTENANCE_ADMIN_STEAMIDS
  and that RCON is reachable.
