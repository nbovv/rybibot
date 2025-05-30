import discord
from discord import app_commands
from discord.ext import commands

class Dealer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="stworz", description="Stwórz salon samochodowy")
    async def stworz(self, interaction: discord.Interaction):
        # tutaj twoja logika komendy, np.
        await interaction.response.send_message("Salon został stworzony!")

async def setup(bot):
    await bot.add_cog(Dealer(bot))
