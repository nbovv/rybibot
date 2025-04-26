import discord
from discord.ext import tasks
from discord import app_commands
import json
import os
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

ZADANIA_FILE = "zadania.json"
DOZWOLONE_ROLE = ["🐡 | Rybi moderator", "Rybi Support", "🐙| Rybi Admin"]

def load_zadania():
    if os.path.exists(ZADANIA_FILE):
        with open(ZADANIA_FILE, "r") as f:
            return json.load(f)
    return []

def save_zadania(zadania):
    with open(ZADANIA_FILE, "w") as f:
        json.dump(zadania, f, indent=4)

def ma_dozwolona_role(member):
    return any(role.name in DOZWOLONE_ROLE for role in member.roles)

@bot.event
async def on_ready():
    print(f"✅ Bot działa jako {bot.user}")
    sprawdz_zadania.start()
    await tree.sync()
    print("✅ Slash komendy zsynchronizowane!")

@tree.command(name="pomoc", description="Wyświetla listę komend")
async def pomoc(interaction: discord.Interaction):
    if not ma_dozwolona_role(interaction.user):
        await interaction.response.send_message("❌ Nie masz uprawnień do używania tej komendy.", ephemeral=True)
        return

    embed = discord.Embed(title="📋 Lista Komend", color=discord.Color.blue())
    embed.add_field(name="/temprole", value="Zaplanuj usunięcie roli dla wszystkich jej członków.", inline=False)
    embed.add_field(name="/temprole_add", value="Nadaj rolę użytkownikowi i zaplanuj jej usunięcie.", inline=False)
    embed.add_field(name="/temprole_cancel", value="Anuluj zaplanowane usunięcie roli.", inline=False)
    embed.add_field(name="/temprole_cancel_role", value="Anuluj zaplanowane usunięcie roli dla wszystkich.", inline=False)
    embed.add_field(name="/temprole_list", value="Wyświetla listę zaplanowanych usunięć ról.", inline=False)
    embed.add_field(name="Jednostki czasu", value="s = sekundy, m = minuty, h = godziny, d = dni, mo = miesiące (30 dni)", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@tree.command(name="temprole", description="Zaplanuj usunięcie roli dla wszystkich członków")
@app_commands.describe(role="Rola do usunięcia", time="Czas", unit="Jednostka czasu: s, m, h, d, mo")
async def temprole(interaction: discord.Interaction, role: discord.Role, time: int, unit: str):
    if not ma_dozwolona_role(interaction.user):
        await interaction.response.send_message("❌ Nie masz uprawnień do tej komendy.", ephemeral=True)
        return

    unit = unit.lower()
    if unit not in ["s", "m", "h", "d", "mo"]:
        await interaction.response.send_message("❌ Niepoprawna jednostka czasu: s, m, h, d, mo", ephemeral=True)
        return

    seconds = time
    if unit == "m":
        seconds *= 60
    elif unit == "h":
        seconds *= 3600
    elif unit == "d":
        seconds *= 86400
    elif unit == "mo":
        seconds *= 2592000

    if not role.members:
        await interaction.response.send_message("⚠️ Nikt nie ma tej roli.", ephemeral=True)
        return

    usun_o = datetime.utcnow() + timedelta(seconds=seconds)
    zadania = load_zadania()
    zadania = [z for z in zadania if not (z["role_id"] == role.id and z["guild_id"] == interaction.guild.id)]

    for member in role.members:
        zadania.append({
            "user_id": member.id,
            "guild_id": interaction.guild.id,
            "role_id": role.id,
            "usun_o": usun_o.isoformat()
        })

    save_zadania(zadania)
    await interaction.response.send_message(f"📝 Zaplanowano usunięcie roli `{role.name}` za {time} {unit}.", ephemeral=True)

@tree.command(name="temprole_add", description="Nadaj rolę użytkownikowi i zaplanuj jej usunięcie")
@app_commands.describe(member="Użytkownik", role="Rola do nadania", time="Czas", unit="Jednostka czasu: s, m, h, d, mo", powod="Powód")
async def temprole_add(interaction: discord.Interaction, member: discord.Member, role: discord.Role, time: int, unit: str, powod: str = None):
    if not ma_dozwolona_role(interaction.user):
        await interaction.response.send_message("❌ Nie masz uprawnień do tej komendy.", ephemeral=True)
        return

    unit = unit.lower()
    if unit not in ["s", "m", "h", "d", "mo"]:
        await interaction.response.send_message("❌ Niepoprawna jednostka czasu: s, m, h, d, mo", ephemeral=True)
        return

    seconds = time
    if unit == "m":
        seconds *= 60
    elif unit == "h":
        seconds *= 3600
    elif unit == "d":
        seconds *= 86400
    elif unit == "mo":
        seconds *= 2592000

    await member.add_roles(role)
    usun_o = datetime.utcnow() + timedelta(seconds=seconds)

    zadania = load_zadania()
    zadania = [z for z in zadania if not (z["user_id"] == member.id and z["role_id"] == role.id and z["guild_id"] == interaction.guild.id)]

    zadania.append({
        "user_id": member.id,
        "guild_id": interaction.guild.id,
        "role_id": role.id,
        "usun_o": usun_o.isoformat()
    })
    save_zadania(zadania)

    if powod:
        await interaction.response.send_message(f"{member.mention} ({role.name})\no tak {powod}")
    else:
        await interaction.response.send_message(f"{member.mention} ({role.name})")

@tree.command(name="temprole_cancel", description="Anuluj zaplanowane usunięcie roli u użytkownika")
@app_commands.describe(member="Użytkownik", role="Rola do anulowania")
async def temprole_cancel(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if not ma_dozwolona_role(interaction.user):
        await interaction.response.send_message("❌ Nie masz uprawnień do tej komendy.", ephemeral=True)
        return

    zadania = load_zadania()
    nowe = [z for z in zadania if not (z["user_id"] == member.id and z["role_id"] == role.id and z["guild_id"] == interaction.guild.id)]

    if len(nowe) == len(zadania):
        await interaction.response.send_message("❌ Nie znaleziono zaplanowanego usunięcia tej roli.", ephemeral=True)
    else:
        save_zadania(nowe)
        await interaction.response.send_message(f"✅ Anulowano zaplanowane usunięcie roli `{role.name}` u {member.mention}.", ephemeral=True)

@tree.command(name="temprole_cancel_role", description="Anuluj zaplanowane usunięcie roli dla wszystkich użytkowników")
@app_commands.describe(role="Rola do anulowania")
async def temprole_cancel_role(interaction: discord.Interaction, role: discord.Role):
    if not ma_dozwolona_role(interaction.user):
        await interaction.response.send_message("❌ Nie masz uprawnień do tej komendy.", ephemeral=True)
        return

    zadania = load_zadania()
    nowe = [z for z in zadania if not (z["role_id"] == role.id and z["guild_id"] == interaction.guild.id)]

    if len(nowe) == len(zadania):
        await interaction.response.send_message("❌ Nie znaleziono zaplanowanego usunięcia tej roli.", ephemeral=True)
    else:
        save_zadania(nowe)
        await interaction.response.send_message(f"✅ Anulowano zaplanowane usunięcie roli `{role.name}` dla wszystkich.", ephemeral=True)

@tree.command(name="temprole_list", description="Wyświetla listę zaplanowanych usunięć ról")
async def temprole_list(interaction: discord.Interaction):
    if not ma_dozwolona_role(interaction.user):
        await interaction.response.send_message("❌ Nie masz uprawnień do tej komendy.", ephemeral=True)
        return

    zadania = load_zadania()
    if not zadania:
        await interaction.response.send_message("📭 Brak zaplanowanych usunięć ról.", ephemeral=True)
        return

    teksty = {}
    for z in zadania:
        guild = bot.get_guild(z["guild_id"])
        member = guild.get_member(z["user_id"])
        role = guild.get_role(z["role_id"])
        czas_usuniecia = datetime.fromisoformat(z["usun_o"]).strftime('%Y-%m-%d %H:%M:%S')

        if role and member:
            if role.name not in teksty:
                teksty[role.name] = []
            teksty[role.name].append(f"- {member.mention} (usuniecie: {czas_usuniecia})")

    embeds = []
    for role_name, members in teksty.items():
        description = "\n".join(members)
        while len(description) > 4096:
            part = description[:4096]
            embeds.append(discord.Embed(title=f"📋 Zaplanowane usunięcia ról ({role_name})", description=part, color=discord.Color.green()))
            description = description[4096:]
        embeds.append(discord.Embed(title=f"📋 Zaplanowane usunięcia ról ({role_name})", description=description, color=discord.Color.green()))

    for embed in embeds:
        await interaction.channel.send(embed=embed)

    await interaction.response.send_message("📋 Lista zaplanowanych usunięć ról:", ephemeral=True)

@tasks.loop(seconds=60)
async def sprawdz_zadania():
    zadania = load_zadania()
    nowe_zadania = []
    teraz = datetime.utcnow()

    for z in zadania:
        czas_usuniecia = datetime.fromisoformat(z["usun_o"])
        if teraz >= czas_usuniecia:
            guild = bot.get_guild(z["guild_id"])
            if guild:
                member = guild.get_member(z["user_id"])
                role = guild.get_role(z["role_id"])
                if member and role:
                    try:
                        await member.remove_roles(role)
                        print(f"✅ Usunięto rolę {role.name} u {member.display_name}")
                    except Exception as e:
                        print(f"❌ Błąd usuwania roli: {e}")
        else:
            nowe_zadania.append(z)

    save_zadania(nowe_zadania)

bot.run("TWOJ_TOKEN")
