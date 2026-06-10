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
        # === ОТЛАДКА: всегда пишем в консоль, когда приходит любое сообщение ===
        print(f"[DEBUG] Сообщение от {message.author} (ID: {message.author.id}) в канале {message.channel.id}: {message.content}")

        # Не реагируем на свои сообщения
        if message.author == self.bot.user:
            print("[DEBUG] Сообщение от самого бота, игнорирую")
            return

        # Проверяем, что канал совпадает с заданным в .env
        if message.channel.id != settings.DISCORD_CHAT_CHANNEL_ID:
            print(f"[DEBUG] Канал {message.channel.id} не равен {settings.DISCORD_CHAT_CHANNEL_ID}, игнорирую")
            return

        # Игнорируем команды бота (начинающиеся с /)
        if message.content.startswith('/'):
            print("[DEBUG] Сообщение начинается с '/', игнорирую")
            return

        # Если дошли до сюда – отправляем в игру
        print("[DEBUG] Сообщение будет отправлено в игру")
        discord_name = message.author.display_name
        full_message = f"[Discord] {discord_name}: {message.content}"

        # Пробуем say (или all, если say не работает)
        response = rcon_wrapper.RconWrapper.send_command(f'say "{full_message}"')
        if response.startswith("❌"):
            # Пробуем all как запасной вариант
            response2 = rcon_wrapper.RconWrapper.send_command(f'all "{full_message}"')
            if response2.startswith("❌"):
                print(f"[CHAT] Не удалось отправить сообщение в игру: {response2}")
            else:
                print(f"[CHAT] Отправлено в игру (через all): {full_message}")
        else:
            print(f"[CHAT] Отправлено в игру (через say): {full_message}")

    @app_commands.command(name="say", description="Отправить сообщение в игровой чат (из Discord)")
    @app_commands.describe(message="Текст сообщения")
    async def say_command(self, interaction: discord.Interaction, message: str):
        await interaction.response.defer(ephemeral=True)
        discord_name = interaction.user.display_name
        full_message = f"[Discord] {discord_name}: {message}"
        response = rcon_wrapper.RconWrapper.send_command(f'say "{full_message}"')
        if response.startswith("❌"):
            response2 = rcon_wrapper.RconWrapper.send_command(f'all "{full_message}"')
            if response2.startswith("❌"):
                await interaction.followup.send(f"❌ Ошибка: {response2}", ephemeral=True)
            else:
                await interaction.followup.send(f"✅ Отправлено (через all): `{full_message}`", ephemeral=True)
        else:
            await interaction.followup.send(f"✅ Отправлено (через say): `{full_message}`", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ChatBridge(bot))