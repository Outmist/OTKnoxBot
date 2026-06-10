import discord
#from core import chat_parser
from discord.ext import commands
from config import settings
from core import pvp_parser
import os
import threading
from core import log_parser

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

async def load_cogs():
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and not filename.startswith('__'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f' Loaded cog: {filename}')
            except Exception as e:
                print(f' Loading error {filename}: {e}')

@bot.event
async def on_ready():
    print(f'\n Bot {bot.user} loaded!')
    await load_cogs()
    try:
        synced = await bot.tree.sync()
        print(f' Synchronized {len(synced)} slash-commands')
    except Exception as e:
        print(f' Synchronization error: {e}')
    print(' Bot listens to events...\n')

#chat_thread = threading.Thread(target=chat_parser.start_chat_monitoring, args=(bot,), daemon=True)
#chat_thread.start()

pvp_thread = threading.Thread(target=pvp_parser.start_pvp_monitoring, args=(bot,), daemon=True)
pvp_thread.start()

log_thread = threading.Thread(target=log_parser.start_log_monitoring, args=(bot,), daemon=True)
log_thread.start()

if __name__ == "__main__":
    bot.run(settings.DISCORD_TOKEN)