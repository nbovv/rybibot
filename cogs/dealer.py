from discord import app_commands
from discord.ext import commands

class Dealer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="stworz_salon", description="Tworzy nowy salon samochodowy")
    async def stworz_salon(self, interaction: commands.Interaction, nazwa: str):
        # Tu wpiszemy funkcję, która zapisuje salon do JSON
        # Na razie zróbmy tylko potwierdzenie
        await interaction.response.send_message(f"Salon '{nazwa}' został stworzony!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Dealer(bot))
