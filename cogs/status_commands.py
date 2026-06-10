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

    @app_commands.command(name="status", description="Реальный онлайн сервера через RCON")
    async def status(self, interaction: discord.Interaction):
        await interaction.response.defer()
        response = rcon_wrapper.RconWrapper.send_command("players")
        if response.startswith("❌"):
            await interaction.followup.send(response)
            return
        match = re.search(r'\((\d+)\)', response)
        count = int(match.group(1)) if match else 0
        if count == 0:
            await interaction.followup.send("🟢 Сервер работает, но игроков нет.")
            return
        names = re.findall(r'-\s+(.+?)(?:\n|$)', response)
        if names:
            players_str = ', '.join(names[:50])
            if len(players_str) > 1800:
                players_str = players_str[:1800] + "..."
            await interaction.followup.send(f"🟢 Сервер работает\n**Игроков онлайн:** {count}\n**Список:** {players_str}")
        else:
            await interaction.followup.send(f"🟢 Сервер работает\n**Игроков онлайн:** {count}")

    @app_commands.command(name="start_pz", description="Запустить сервер и отслеживать прогресс")
    async def start_pz(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        process = server_manager.start_server_process()
        if not process:
            await interaction.followup.send("❌ Ошибка запуска сервера", ephemeral=True)
            return

        msg = await interaction.followup.send("🟡 Запуск сервера... 0с", ephemeral=True)

        def update_progress(stage, elapsed):
            asyncio.run_coroutine_threadsafe(
                msg.edit(content=f"🟡 {stage}... {elapsed}с"),
                self.bot.loop
            )

        def wait_thread():
            server_manager.wait_for_server_ready(callback=update_progress)
            # После готовности сервера проверим техрежим
            maintenance_cog = self.bot.get_cog('Maintenance')
            if maintenance_cog and maintenance_cog.maintenance_active:
                # Применяем настройки техрежима к серверу
                asyncio.run_coroutine_threadsafe(
                    maintenance_cog.apply_maintenance_settings(),
                    self.bot.loop
                )
            asyncio.run_coroutine_threadsafe(
                msg.edit(content="✅ Сервер успешно запущен и готов принимать игроков!"),
                self.bot.loop
            )

        thread = Thread(target=wait_thread, daemon=True)
        thread.start()

    @tasks.loop(seconds=30)
    async def update_status(self):
        # Проверяем, включён ли режим технических работ
        maintenance_cog = self.bot.get_cog('Maintenance')
        if maintenance_cog and maintenance_cog.maintenance_active:
            # Если техработы включены, не меняем статус (он уже установлен как "🔧 Технические работы")
            return

        try:
            response = rcon_wrapper.RconWrapper.send_command("players")
            if response.startswith("❌"):
                await self.bot.change_presence(activity=discord.Game(name="Сервер оффлайн"), status=discord.Status.dnd)
                return
            match = re.search(r'\((\d+)\)', response)
            count = int(match.group(1)) if match else 0
            if count == 0:
                await self.bot.change_presence(activity=discord.Game(name="Сервер пуст"), status=discord.Status.idle)
            else:
                await self.bot.change_presence(activity=discord.Game(name=f"Онлайн: {count} игроков"), status=discord.Status.online)
        except Exception as e:
            print(f"[STATUS] Ошибка обновления статуса: {e}")

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
            (total_seconds - 30*60, "⚠️ Сервер будет перезагружен через 30 минут! Сохраните прогресс."),
            (total_seconds - 10*60, "⚠️ Сервер будет перезагружен через 10 минут!"),
            (total_seconds - 5*60,  "⚠️ Сервер будет перезагружен через 5 минут!"),
        ]

        last_time = 0
        for delay, msg in warnings:
            wait = delay - last_time
            if wait > 0:
                await asyncio.sleep(wait)
                game_message(msg)
                last_time = delay

        await asyncio.sleep(5*60)
        game_message("🔄 Сервер выключается на перезагрузку. Сохранение мира...")
        rcon_wrapper.RconWrapper.send_command("save")
        await asyncio.sleep(5)
        rcon_wrapper.RconWrapper.send_command("quit")
        await asyncio.sleep(20)
        server_manager.start_server_process()

    @auto_restart.before_loop
    async def before_auto_restart(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="restart", description="Запустить перезапуск сервера с таймером")
    @app_commands.describe(minutes="Через сколько минут перезапустить сервер (1-60)")
    async def restart_timer(self, interaction: discord.Interaction, minutes: int):
        if minutes < 1 or minutes > 60:
            await interaction.response.send_message("❌ Укажите время от 1 до 60 минут.", ephemeral=True)
            return

        await interaction.response.send_message(f"🔄 Запущен таймер перезапуска через {minutes} минут.", ephemeral=False)

        total_seconds = minutes * 60

        # Предупреждение за 5 минут (если время больше 5 минут)
        if total_seconds > 5 * 60:
            await asyncio.sleep(total_seconds - 5 * 60)
            rcon_wrapper.RconWrapper.send_command('say "⚠️ Сервер будет перезагружен через 5 минут!"')
            await asyncio.sleep(4 * 60)  # остаётся 1 минута
            rcon_wrapper.RconWrapper.send_command('say "⚠️ Сервер будет перезагружен через 1 минуту!"')
            await asyncio.sleep(60)
        elif total_seconds > 60:
            # Время от 1 до 5 минут
            await asyncio.sleep(total_seconds - 60)
            rcon_wrapper.RconWrapper.send_command('say "⚠️ Сервер будет перезагружен через 1 минуту!"')
            await asyncio.sleep(60)
        else:
            # Меньше или равно 1 минуте
            await asyncio.sleep(total_seconds)

        # Финальное сообщение и остановка
        rcon_wrapper.RconWrapper.send_command('say "🔄 Сервер выключается на перезагрузку. Сохранение мира..."')
        rcon_wrapper.RconWrapper.send_command("save")
        await asyncio.sleep(5)
        rcon_wrapper.RconWrapper.send_command("quit")
        await asyncio.sleep(20)

        # Запуск сервера заново (если нужно)
        server_manager.start_server_process()

async def setup(bot):
    await bot.add_cog(StatusCommands(bot))