import discord
from discord import app_commands
from discord.ext import commands
from core import rcon_wrapper

class RconCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rcon", description="Send any command to the server")
    @app_commands.describe(command="Command (e.g.: players, servermsg 'Hello', banid 765611...)")
    async def rcon(self, interaction: discord.Interaction, command: str):
        await interaction.response.defer(ephemeral=True)

        if command.strip().lower() == "help":
            await interaction.followup.send("Use `/help` for command list.", ephemeral=True)
            return

        response = rcon_wrapper.RconWrapper.send_command(command)

        if not response or response.isspace():
            await interaction.followup.send("✅ Command executed (server returned no text response).", ephemeral=True)
            return

        if len(response) > 1990:
            if len(response) > 5000:
                file = discord.File(
                    fp=discord.BytesIO(response.encode()),
                    filename="rcon_output.txt"
                )
                await interaction.followup.send("📄 Response too long, sent as file:", file=file, ephemeral=True)
            else:
                await interaction.followup.send(f"```\n{response[:1990]}...\n```", ephemeral=True)
        else:
            await interaction.followup.send(f"```\n{response}\n```", ephemeral=True)

    @app_commands.command(name="help", description="List of useful RCON commands")
    async def help_rcon(self, interaction: discord.Interaction):
        help_text = """
**🛠️ Server control via `/rcon`**

All commands are sent via `/rcon <command>`

**Basic:**
• `players` — list online players
• `servermsg "text"` — send in‑game message
• `save` — save the world
• `quit` — stop the server

**Bans/kicks:**
• `kick "nick"` — kick a player
• `banuser "nick"` — ban by nickname
• `unbanuser "nick"` — unban by nickname
• `banid "steamid"` — ban by SteamID
• `unbanid "steamid"` — unban by SteamID

**Administration:**
• `setaccesslevel "nick" admin` — grant admin rights
• `setaccesslevel "nick" none` — revoke admin rights

**Start server:**
• `/start_pz` — start the server (if path is configured)

**Examples:**
`/rcon players`
`/rcon servermsg "Restart in 5 minutes"`
`/rcon banid "76561199153480327"`

**Other bot commands:**
`/status` — online and player list
`/start_pz` — start server
`/top` — top players (if stats DB exists)
        """
        embed = discord.Embed(title="📋 Command Help", description=help_text, color=0x00ff00)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(RconCommands(bot))