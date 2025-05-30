import discord
from discord.ext import commands
import json
import os

DATA_FILE = "dealer_data.json"
CAR_CATALOG_FILE = "car_catalog.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_catalog():
    with open(CAR_CATALOG_FILE, "r") as f:
        return json.load(f)

class DealerGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.catalog = load_catalog()

    @commands.command()
    async def startdealer(self, ctx):
        data = load_data()
        user_id = str(ctx.author.id)
        if user_id in data:
            await ctx.send("🔧 Już masz swój salon samochodowy.")
            return

        data[user_id] = {
            "money": 100000,
            "dealer": {
                "name": f"Salon {ctx.author.name}",
                "cars": []
            }
        }
        save_data(data)
        await ctx.send(f"✅ Salon **{ctx.author.name}** został utworzony! Masz 100 000$ na start.")

    @commands.command()
    async def katalog(self, ctx):
        msg = "**📘 Katalog aut dostępnych do kupienia:**\n"
        for car in self.catalog:
            msg += f"- {car['brand']} {car['model']} — ${car['price']}\n"
        await ctx.send(msg)

    @commands.command()
    async def buycar(self, ctx, brand: str, *, model: str):
        data = load_data()
        user_id = str(ctx.author.id)
        if user_id not in data:
            await ctx.send("❌ Najpierw załóż salon komendą `!startdealer`.")
            return

        # Szukaj auta w katalogu
        car = next((c for c in self.catalog if c["brand"].lower() == brand.lower() and c["model"].lower() == model.lower()), None)
        if not car:
            await ctx.send("🚫 Nie znaleziono takiego auta w katalogu.")
            return

        if data[user_id]["money"] < car["price"]:
            await ctx.send("💸 Nie masz wystarczająco pieniędzy.")
            return

        data[user_id]["money"] -= car["price"]
        data[user_id]["dealer"]["cars"].append(car)
        save_data(data)
        await ctx.send(f"✅ Kupiono {car['brand']} {car['model']} za ${car['price']}!")

    @commands.command()
    async def autosalon(self, ctx):
        data = load_data()
        user_id = str(ctx.author.id)
        if user_id not in data:
            await ctx.send("❌ Najpierw załóż salon komendą `!startdealer`.")
            return

        cars = data[user_id]["dealer"]["cars"]
        if not cars:
            await ctx.send("🚗 Twój salon nie ma jeszcze żadnych aut.")
            return

        msg = f"**🚘 Auta w salonie {ctx.author.name}:**\n"
        total_value = 0
        for car in cars:
            msg += f"- {car['brand']} {car['model']} — ${car['price']}\n"
            total_value += car["price"]

        msg += f"\n💰 Łączna wartość salonu: ${total_value}"
        await ctx.send(msg)

async def setup(bot):
    await bot.add_cog(DealerGame(bot))
