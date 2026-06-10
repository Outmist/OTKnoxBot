import discord
from discord import app_commands
from discord.ext import commands, tasks
from core import rcon_wrapper
from config import settings

class Maintenance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.maintenance_active = settings.MAINTENANCE_MODE
        if self.maintenance_active and not self.update_maintenance_status.is_running():
            self.update_maintenance_status.start()

    @app_commands.command(name="maintenance", description="Включить/выключить режим технических работ")
    @app_commands.describe(mode="on/off")
    async def maintenance(self, interaction: discord.Interaction, mode: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Требуются права администратора.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        mode_lower = mode.lower()
        if mode_lower == "on":
            self.maintenance_active = True
            rcon_response = rcon_wrapper.RconWrapper.send_command('say "⚠️ Сервер переходит в режим технических работ. Вход только для администраторов."')
            if rcon_response.startswith("❌"):
                await interaction.followup.send(f"⚠️ Сервер не отвечает: {rcon_response}\nРежим обслуживания включён локально.", ephemeral=True)
            else:
                rcon_wrapper.RconWrapper.send_command('setaccesslevel "*" none')
                for steamid in settings.MAINTENANCE_ADMIN_STEAMIDS:
                    if steamid.strip():
                        rcon_wrapper.RconWrapper.send_command(f'setaccesslevel "{steamid.strip()}" admin')
                await interaction.followup.send("✅ Режим технических работ ВКЛЮЧЁН. Обычные игроки не могут зайти.", ephemeral=True)

            await self.bot.change_presence(activity=discord.Game(name="🔧 Технические работы"), status=discord.Status.dnd)
            if not self.update_maintenance_status.is_running():
                self.update_maintenance_status.start()

        elif mode_lower == "off":
            self.maintenance_active = False
            rcon_response = rcon_wrapper.RconWrapper.send_command('setaccesslevel "*" user')
            if rcon_response.startswith("❌"):
                await interaction.followup.send(f"⚠️ Сервер не отвечает: {rcon_response}\nРежим обслуживания выключен локально.", ephemeral=True)
            else:
                rcon_wrapper.RconWrapper.send_command('say "✅ Технические работы завершены."')
                await interaction.followup.send("✅ Режим технических работ ВЫКЛЮЧЕН.", ephemeral=True)

            if self.update_maintenance_status.is_running():
                self.update_maintenance_status.cancel()
        else:
            await interaction.followup.send("❌ Используйте `on` или `off`", ephemeral=True)

    @tasks.loop(seconds=30)
    async def update_maintenance_status(self):
        if self.maintenance_active:
            await self.bot.change_presence(activity=discord.Game(name="🔧 Технические работы"), status=discord.Status.dnd)

    @update_maintenance_status.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()

    async def apply_maintenance_settings(self):
        """Применяет текущие настройки техрежима к работающему серверу."""
        if not self.maintenance_active:
            return
        rcon_wrapper.RconWrapper.send_command('setaccesslevel "*" none')
        for steamid in settings.MAINTENANCE_ADMIN_STEAMIDS:
            if steamid.strip():
                rcon_wrapper.RconWrapper.send_command(f'setaccesslevel "{steamid.strip()}" admin')
        print("[MAINTENANCE] Применены настройки техрежима к серверу.")

async def setup(bot):
    await bot.add_cog(Maintenance(bot))