import discord
from discord import app_commands
from discord.ext import commands
import json
import os

class DealerGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.DATA_FILE = "dealer_data.json"
        self.CATALOG_FILE = "car_catalog.json"
        self.catalog = self.load_catalog()

    def load_data(self):
        if not os.path.exists(self.DATA_FILE):
            with open(self.DATA_FILE, "w") as f:
                json.dump({}, f)
        with open(self.DATA_FILE, "r") as f:
            return json.load(f)

    def save_data(self, data):
        with open(self.DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)

    def load_catalog(self):
        with open(self.CATALOG_FILE, "r") as f:
            return json.load(f)

    @app_commands.command(name="startdealer", description="Załóż własny salon samochodowy")
    async def startdealer(self, interaction: discord.Interaction):
        data = self.load_data()
        user_id = str(interaction.user.id)

        if user_id in data:
            await interaction.response.send_message("🔧 Już masz swój salon samochodowy.", ephemeral=True)
            return

        data[user_id] = {
            "money": 100000,
            "dealer": {
                "name": f"Salon {interaction.user.name}",
                "cars": []
            }
        }
        self.save_data(data)
        await interaction.response.send_message(f"✅ Salon **{interaction.user.name}** został utworzony! Masz 100 000$ na start.")

    @app_commands.command(name="katalog", description="Wyświetla katalog dostępnych aut")
    async def katalog(self, interaction: discord.Interaction):
        msg = "**📘 Katalog aut:**\n"
        for car in self.catalog:
            msg += f"- {car['brand']} {car['model']} — ${car['price']}\n"
        await interaction.response.send_message(msg)

    @app_commands.command(name="kupauto", description="Kup auto do swojego salonu")
    @app_commands.describe(marka="Marka auta", model="Model auta")
    async def kupauto(self, interaction: discord.Interaction, marka: str, model: str):
        data = self.load_data()
        user_id = str(interaction.user.id)

        if user_id not in data:
            await interaction.response.send_message("❌ Najpierw załóż salon komendą `/startdealer`.", ephemeral=True)
            return

        car = next((c for c in self.catalog if c["brand"].lower() == marka.lower() and c["model"].lower() == model.lower()), None)
        if not car:
            await interaction.response.send_message("🚫 Nie znaleziono takiego auta w katalogu.", ephemeral=True)
            return

        if data[user_id]["money"] < car["price"]:
            await interaction.response.send_message("💸 Nie masz wystarczająco pieniędzy.", ephemeral=True)
            return

        data[user_id]["money"] -= car["price"]
        data[user_id]["dealer"]["cars"].append(car)
        self.save_data(data)
        await interaction.response.send_message(f"✅ Kupiono {car['brand']} {car['model']} za ${car['price']}!")

    @app_commands.command(name="autosalon", description="Pokaż auta w swoim salonie")
    async def autosalon(self, interaction: discord.Interaction):
        data = self.load_data()
        user_id = str(interaction.user.id)

        if user_id not in data:
            await interaction.response.send_message("❌ Najpierw załóż salon komendą `/startdealer`.", ephemeral=True)
            return

        cars = data[user_id]["dealer"]["cars"]
        if not cars:
            await interaction.response.send_message("🚗 Twój salon nie ma jeszcze żadnych aut.")
            return

        msg = f"**🚘 Auta w salonie {interaction.user.name}:**\n"
        total_value = 0
        for car in cars:
            msg += f"- {car['brand']} {car['model']} — ${car['price']}\n"
            total_value += car["price"]

        msg += f"\n💰 Łączna wartość salonu: ${total_value}"
        await interaction.response.send_message(msg)

async def setup(bot):
    await bot.add_cog(DealerGame(bot))
