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

    @app_commands.command(name="maintenance", description="Enable/disable maintenance mode")
    @app_commands.describe(mode="on/off")
    async def maintenance(self, interaction: discord.Interaction, mode: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Administrator privileges required.", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        mode_lower = mode.lower()
        if mode_lower == "on":
            self.maintenance_active = True
            rcon_response = rcon_wrapper.RconWrapper.send_command('say "⚠️ Server is entering maintenance mode. Admin access only."')
            if rcon_response.startswith("❌"):
                await interaction.followup.send(f"⚠️ Server not responding: {rcon_response}\nMaintenance mode enabled locally.", ephemeral=True)
            else:
                rcon_wrapper.RconWrapper.send_command('setaccesslevel "*" none')
                for steamid in settings.MAINTENANCE_ADMIN_STEAMIDS:
                    if steamid.strip():
                        rcon_wrapper.RconWrapper.send_command(f'setaccesslevel "{steamid.strip()}" admin')
                await interaction.followup.send("✅ Maintenance mode ENABLED. Regular players cannot join.", ephemeral=True)

            await self.bot.change_presence(activity=discord.Game(name="🔧 Maintenance"), status=discord.Status.dnd)
            if not self.update_maintenance_status.is_running():
                self.update_maintenance_status.start()

        elif mode_lower == "off":
            self.maintenance_active = False
            rcon_response = rcon_wrapper.RconWrapper.send_command('setaccesslevel "*" user')
            if rcon_response.startswith("❌"):
                await interaction.followup.send(f"⚠️ Server not responding: {rcon_response}\nMaintenance mode disabled locally.", ephemeral=True)
            else:
                rcon_wrapper.RconWrapper.send_command('say "✅ Maintenance work completed."')
                await interaction.followup.send("✅ Maintenance mode DISABLED.", ephemeral=True)

            if self.update_maintenance_status.is_running():
                self.update_maintenance_status.cancel()
        else:
            await interaction.followup.send("❌ Use `on` or `off`", ephemeral=True)

    @tasks.loop(seconds=30)
    async def update_maintenance_status(self):
        if self.maintenance_active:
            await self.bot.change_presence(activity=discord.Game(name="🔧 Maintenance"), status=discord.Status.dnd)

    @update_maintenance_status.before_loop
    async def before_update(self):
        await self.bot.wait_until_ready()

    async def apply_maintenance_settings(self):
        """Applies current maintenance settings to the running server."""
        if not self.maintenance_active:
            return
        rcon_wrapper.RconWrapper.send_command('setaccesslevel "*" none')
        for steamid in settings.MAINTENANCE_ADMIN_STEAMIDS:
            if steamid.strip():
                rcon_wrapper.RconWrapper.send_command(f'setaccesslevel "{steamid.strip()}" admin')
        print("[MAINTENANCE] Maintenance settings applied to server.")

async def setup(bot):
    await bot.add_cog(Maintenance(bot))