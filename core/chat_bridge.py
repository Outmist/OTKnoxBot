import discord
from discord import app_commands
from discord.ext import commands
from core import rcon_wrapper
from config import settings

class ChatBridge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    #@commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # === DEBUG: always print any incoming message to console ===
        print(f"[DEBUG] Message from {message.author} (ID: {message.author.id}) in channel {message.channel.id}: {message.content}")

        if message.author == self.bot.user:
            print("[DEBUG] Message from bot itself, ignoring")
            return

        if message.channel.id != settings.DISCORD_CHAT_CHANNEL_ID:
            print(f"[DEBUG] Channel {message.channel.id} != {settings.DISCORD_CHAT_CHANNEL_ID}, ignoring")
            return

        if message.content.startswith('/'):
            print("[DEBUG] Message starts with '/', ignoring")
            return

        print("[DEBUG] Message will be sent to the game")
        discord_name = message.author.display_name
        full_message = f"[Discord] {discord_name}: {message.content}"

        response = rcon_wrapper.RconWrapper.send_command(f'say "{full_message}"')
        if response.startswith("❌"):
            response2 = rcon_wrapper.RconWrapper.send_command(f'all "{full_message}"')
            if response2.startswith("❌"):
                print(f"[CHAT] Failed to send message to game: {response2}")
            else:
                print(f"[CHAT] Sent to game (via all): {full_message}")
        else:
            print(f"[CHAT] Sent to game (via say): {full_message}")

    @app_commands.command(name="say", description="Send a message to the game chat (from Discord)")
    @app_commands.describe(message="Message text")
    async def say_command(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer(ephemeral=True)
        discord_name = interaction.user.display_name
        full_message = f"[Discord] {discord_name}: {message}"
        response = rcon_wrapper.RconWrapper.send_command(f'say "{full_message}"')
        if response.startswith("❌"):
            response2 = rcon_wrapper.RconWrapper.send_command(f'all "{full_message}"')
            if response2.startswith("❌"):
                await interaction.followup.send(f"❌ Error: {response2}", ephemeral=True)
            else:
                await interaction.followup.send(f"✅ Sent (via all): `{full_message}`", ephemeral=True)
        else:
            await interaction.followup.send(f"✅ Sent (via say): `{full_message}`", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ChatBridge(bot))