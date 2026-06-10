import discord
from discord import app_commands
from discord.ext import commands
from core import rcon_wrapper

class RconCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="rcon", description="Отправить любую команду на сервер")
    @app_commands.describe(command="Команда (например: players, servermsg 'Hello', banid 765611...)")
    async def rcon(self, interaction: discord.Interaction, command: str):
        await interaction.response.defer(ephemeral=True)

        if command.strip().lower() == "help":
            await interaction.followup.send("Используй `/help` для списка команд.", ephemeral=True)
            return

        response = rcon_wrapper.RconWrapper.send_command(command)

        if not response or response.isspace():
            await interaction.followup.send("✅ Команда выполнена (сервер не вернул текстового ответа).", ephemeral=True)
            return

        if len(response) > 1990:
            if len(response) > 5000:
                file = discord.File(
                    fp=discord.BytesIO(response.encode()),
                    filename="rcon_output.txt"
                )
                await interaction.followup.send("📄 Ответ слишком длинный, отправлен файлом:", file=file, ephemeral=True)
            else:
                await interaction.followup.send(f"```\n{response[:1990]}...\n```", ephemeral=True)
        else:
            await interaction.followup.send(f"```\n{response}\n```", ephemeral=True)

    @app_commands.command(name="help", description="Список полезных RCON-команд")
    async def help_rcon(self, interaction: discord.Interaction):
        help_text = """
**🛠️ Управление сервером через `/rcon`**

Все команды отправляются через `/rcon <команда>`

**Основные:**
• `players` — список игроков онлайн
• `servermsg "текст"` — сообщение в игру
• `save` — сохранить мир
• `quit` — остановить сервер

**Баны/кики:**
• `kick "ник"` — кикнуть
• `banuser "ник"` — бан по нику
• `unbanuser "ник"` — разбан по нику
• `banid "steamid"` — бан по SteamID
• `unbanid "steamid"` — разбан по SteamID

**Администрирование:**
• `setaccesslevel "ник" admin` — выдать права админа
• `setaccesslevel "ник" none` — забрать права

**Запуск сервера:**
• `/start_pz` — запустить сервер (если настроен путь)

**Примеры:**
`/rcon players`
`/rcon servermsg "Рестарт через 5 минут"`
`/rcon banid "76561199153480327"`

**Другие команды бота:**
`/status` — онлайн и список игроков
`/start_pz` — запуск сервера
`/top` — топ игроков (если есть БД статистики)
        """
        embed = discord.Embed(title="📋 Помощь по командам", description=help_text, color=0x00ff00)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(RconCommands(bot))