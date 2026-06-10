import discord
from discord import app_commands
from discord.ext import commands, tasks
from core import rcon_wrapper, server_manager
import re
import asyncio
from threading import Thread
from config import settings

class StatusCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.update_status.start()
        if settings.AUTO_RESTART_ENABLED:
            self.auto_restart.start()

    @app_commands.command(name="status", description="Real online servers via RCON")
    async def status(self, interaction: discord.Interaction):
        await interaction.response.defer()
        response = rcon_wrapper.RconWrapper.send_command("players")
        if response.startswith("❌"):
            await interaction.followup.send(response)
            return
        match = re.search(r'\((\d+)\)', response)
        count = int(match.group(1)) if match else 0
        if count == 0:
            await interaction.followup.send("🟢 The server is running, but there are no players.")
            return
        names = re.findall(r'-\s+(.+?)(?:\n|$)', response)
        if names:
            players_str = ', '.join(names[:50])
            if len(players_str) > 1800:
                players_str = players_str[:1800] + "..."
            await interaction.followup.send(f"🟢 The server is working\n**Online players:** {count}\n**List:** {players_str}")
        else:
            await interaction.followup.send(f"🟢 The server is working\n**Online players:** {count}")

    @app_commands.command(name="start_pz", description="Start the server and track progress")
    async def start_pz(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        process = server_manager.start_server_process()
        if not process:
            await interaction.followup.send("❌ Server startup error", ephemeral=True)
            return

        msg = await interaction.followup.send("🟡 Starting the server... 0s", ephemeral=True)

        def update_progress(stage, elapsed):
            asyncio.run_coroutine_threadsafe(
                msg.edit(content=f"🟡 {stage}... {elapsed}с"),
                self.bot.loop
            )

        def wait_thread():
            server_manager.wait_for_server_ready(callback=update_progress)
            maintenance_cog = self.bot.get_cog('Maintenance')
            if maintenance_cog and maintenance_cog.maintenance_active:
                asyncio.run_coroutine_threadsafe(
                    maintenance_cog.apply_maintenance_settings(),
                    self.bot.loop
                )
            asyncio.run_coroutine_threadsafe(
                msg.edit(content="✅ The server has been successfully launched and is ready to accept players!"),
                self.bot.loop
            )

        thread = Thread(target=wait_thread, daemon=True)
        thread.start()

    @tasks.loop(seconds=30)
    async def update_status(self):
        maintenance_cog = self.bot.get_cog('Maintenance')
        if maintenance_cog and maintenance_cog.maintenance_active:
            return

        try:
            response = rcon_wrapper.RconWrapper.send_command("players")
            if response.startswith("❌"):
                await self.bot.change_presence(activity=discord.Game(name="The server is offline"), status=discord.Status.dnd)
                return
            match = re.search(r'\((\d+)\)', response)
            count = int(match.group(1)) if match else 0
            if count == 0:
                await self.bot.change_presence(activity=discord.Game(name="The server is empty"), status=discord.Status.idle)
            else:
                await self.bot.change_presence(activity=discord.Game(name=f"Online: {count} players"), status=discord.Status.online)
        except Exception as e:
            print(f"[STATUS] Status update error: {e}")

    @update_status.before_loop
    async def before_update_status(self):
        await self.bot.wait_until_ready()

    @tasks.loop(hours=4)
    async def auto_restart(self):
        await self.bot.wait_until_ready()
        if not settings.AUTO_RESTART_ENABLED:
            return

        def game_message(text):
            rcon_wrapper.RconWrapper.send_command(f'servermsg "{text}"')

        total_seconds = 4 * 3600
        warnings = [
            (total_seconds - 30*60, "⚠️ The server will reboot in 30 minutes!"),
            (total_seconds - 10*60, "⚠️ The server will reboot in 10 minutes!"),
            (total_seconds - 5*60,  "⚠️ The server will reboot in 5 minutes!"),
        ]

        last_time = 0
        for delay, msg in warnings:
            wait = delay - last_time
            if wait > 0:
                await asyncio.sleep(wait)
                game_message(msg)
                last_time = delay

        await asyncio.sleep(5*60)
        game_message("🔄 The server is shutting down to reboot. Saving the world...")
        rcon_wrapper.RconWrapper.send_command("save")
        await asyncio.sleep(5)
        rcon_wrapper.RconWrapper.send_command("quit")
        await asyncio.sleep(20)
        server_manager.start_server_process()

    @auto_restart.before_loop
    async def before_auto_restart(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="restart", description="Run a server restart with a timer")
    @app_commands.describe(minutes="How many minutes does it take to restart the server (1-60)")
    async def restart_timer(self, interaction: discord.Interaction, minutes: int):
        if minutes < 1 or minutes > 60:
            await interaction.response.send_message("❌ Specify time from 1 to 60 minutes.", ephemeral=True)
            return

        await interaction.response.send_message(f"🔄 Restart timer started after {minutes} minutes.", ephemeral=False)

        total_seconds = minutes * 60

        # Предупреждение за 5 минут (если время больше 5 минут)
        if total_seconds > 5 * 60:
            await asyncio.sleep(total_seconds - 5 * 60)
            rcon_wrapper.RconWrapper.send_command('say "⚠️ The server will reboot in 5 minutes!"')
            await asyncio.sleep(4 * 60)  # остаётся 1 минута
            rcon_wrapper.RconWrapper.send_command('say "⚠️ The server will reboot in 1 minute!"')
            await asyncio.sleep(60)
        elif total_seconds > 60:
            # Время от 1 до 5 минут
            await asyncio.sleep(total_seconds - 60)
            rcon_wrapper.RconWrapper.send_command('say "⚠️ The server will reboot in 1 minute!"')
            await asyncio.sleep(60)
        else:
            # Меньше или равно 1 минуте
            await asyncio.sleep(total_seconds)

        # Финальное сообщение и остановка
        rcon_wrapper.RconWrapper.send_command('say "🔄 The server is shutting down to reboot. Saving the world..."')
        rcon_wrapper.RconWrapper.send_command("save")
        await asyncio.sleep(5)
        rcon_wrapper.RconWrapper.send_command("quit")
        await asyncio.sleep(20)

        # Запуск сервера заново (если нужно)
        server_manager.start_server_process()

async def setup(bot):
    await bot.add_cog(StatusCommands(bot))