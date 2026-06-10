import discord
from discord import app_commands
from discord.ext import commands
import sqlite3
import os
import asyncio
from config import settings

class PlayerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # @app_commands.command(name="top", description="Топ игроков по убийствам (из БД статистики сервера)")
    # async def top(self, interaction: discord.Interaction):
    #     await interaction.response.defer()
    #     def get_top_data():
    #         db_path = settings.STATS_DB_PATH
    #         if not db_path or not os.path.exists(db_path):
    #             return None
    #         conn = sqlite3.connect(db_path)
    #         conn.row_factory = sqlite3.Row
    #         cursor = conn.cursor()
    #         try:
    #             cursor.execute("SELECT player_name, kills FROM player_stats ORDER BY kills DESC LIMIT 10")
    #             rows = cursor.fetchall()
    #             return [(row["player_name"], row["kills"]) for row in rows]
    #         except Exception as e:
    #             print(f"[TOP] Ошибка: {e}")
    #             return None
    #         finally:
    #             conn.close()

    #     top_players = await asyncio.to_thread(get_top_data)
    #     if not top_players:
    #         await interaction.followup.send("📭 Статистика пока недоступна.")
    #         return

    #     message = "**🏆 Топ игроков по убийствам 🏆**\n"
    #     for i, (name, kills) in enumerate(top_players, 1):
    #         message += f"{i}. **{name}** — {kills} убийств\n"
    #     await interaction.followup.send(message)

    @app_commands.command(name="topkills", description="Топ PvP убийц (из логов PvP)")
    async def topkills(self, interaction: discord.Interaction):
        await interaction.response.defer()
        # Используем переменную из настроек или создаём путь по умолчанию
        db_path = getattr(settings, 'PVP_STATS_DB_PATH', None)
        if not db_path:
            db_path = os.path.join(settings.PZ_LOG_DIR, "pvp_stats.db")

        def get_pvp_data():
            if not os.path.exists(db_path):
                return None
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT player, kills, deaths FROM kills ORDER BY kills DESC LIMIT 10")
                rows = cursor.fetchall()
                return rows
            except Exception as e:
                print(f"[TOPKILLS] Ошибка: {e}")
                return None
            finally:
                conn.close()

        rows = await asyncio.to_thread(get_pvp_data)
        if not rows:
            await interaction.followup.send("📭 Статистика PvP пока отсутствует.")
            return

        message = "**🏆 Топ убийц по PvP 🏆**\n"
        for i, (player, kills, deaths) in enumerate(rows, 1):
            message += f"{i}. **{player}** — убийств: {kills}, смертей: {deaths}\n"
        embed = discord.Embed(title="📊 Статистика PvP", description=message, color=0xff0000)
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(PlayerCommands(bot))