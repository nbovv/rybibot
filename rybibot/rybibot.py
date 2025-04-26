import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True  # potrzebne do czytania wiadomości

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Zalogowano jako {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

# Zamień 'YOUR_TOKEN_HERE' na swój token bota z Discord Developer Portal
bot.run(os.getenv('TOKEN'))
