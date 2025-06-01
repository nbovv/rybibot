import discord
from discord.ext import commands, tasks
from discord import app_commands, Message
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging
import asyncio
logging.basicConfig(level=logging.INFO)
from discord import ui
import random
from discord import Interaction
from discord import Embed, Color
from discord.ui import View, Button

ACTIVE_RACE = None  # Słownik z danymi wyścigu lub None
BETS = {}

DATA_FILE = "/var/data/dealer_data.json"

with open("auta.json", "r", encoding="utf-8") as f:
    KATALOG_AUT = json.load(f)  # KATALOG_AUT to lista słowników

#def save_user_roles(user_id, role_ids):
    #"""Zapisz role użytkownika do pliku."""
    #if not os.path.exists("roles.json"):
        #with open("roles.json", "w") as f:
            #json.dump({}, f)

    #with open("roles.json", "r") as f:
        #data = json.load(f)

    #data[str(user_id)] = role_ids

    #with open("roles.json", "w") as f:
        #json.dump(data, f)

#def load_user_roles(user_id):
    #"""Wczytaj zapisane role użytkownika."""
    #if not os.path.exists("roles.json"):
        #return []

    #with open("roles.json", "r") as f:
        #data = json.load(f)

    #return data.get(str(user_id), [])


load_dotenv()
TOKEN = os.getenv("TOKEN")
LOG_CHANNEL_ID = 1376659262389878925  # <- Zamień na ID twojego kanału logów

intents = discord.Intents.all()
previous_roles = {}

ostatnia_wiadomosc: Message = None

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# Funkcje pomocnicze

# Ścieżka do Persistent Storage
PERSISTENT_PATH = "/var/data"  # Jeśli masz inny mount path na Renderze, np. /mnt/data, zmień tutaj!

# Funkcje pomocnicze
def get_zadania_file(guild_id):
    # Sprawdź czy katalog istnieje
    if not os.path.exists(PERSISTENT_PATH):
        os.makedirs(PERSISTENT_PATH)
        print(f"📁 Utworzono brakujący folder: {PERSISTENT_PATH}")
    return f"{PERSISTENT_PATH}/zadania_{guild_id}.json"

def load_zadania(guild_id):
    file = get_zadania_file(guild_id)
    if os.path.exists(file):
        try:
            with open(file, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Błąd podczas ładowania pliku {file}: {e}")
    return []

def save_zadania(guild_id, zadania):
    file = get_zadania_file(guild_id)
    try:
        with open(file, "w") as f:
            json.dump(zadania, f, indent=4)
        print(f"✅ Zadania zapisane do pliku: {file}")
    except Exception as e:
        print(f"❌ Błąd podczas zapisywania pliku {file}: {e}")


def ma_dozwolona_role(member: discord.Member):
    perms = member.guild_permissions
    return (
        perms.administrator or
        perms.manage_guild or
        perms.kick_members or
        perms.ban_members or
        perms.manage_roles or
        perms.manage_channels
    )

@tasks.loop(minutes=1)
async def sprawdz_zadania():
    for guild in bot.guilds:
        zadania = load_zadania(guild.id)
        nowe_zadania = []
        for zadanie in zadania:
            user_id = zadanie["user_id"]
            role_id = zadanie["role_id"]
            usun_o = datetime.fromisoformat(zadanie["usun_o"])

            member = guild.get_member(user_id)
            role = guild.get_role(role_id)

            if member and role and datetime.utcnow() >= usun_o:
                try:
                    await member.remove_roles(role)
                    print(f"✅ Usunięto rolę {role.name} użytkownikowi {member.display_name}")

                    # Usunięcie kanału mute (jeśli był zapisany)
                    if "channel_id" in zadanie:
                        kanal = guild.get_channel(zadanie["channel_id"])
                        if kanal:
                            await kanal.delete(reason="Koniec muta – automatyczne usunięcie kanału")
                            print(f"🗑️ Usunięto kanał {kanal.name}")

                except Exception as e:
                    print(f"⚠️ Błąd przy usuwaniu roli lub kanału: {e}")
                else:
                    nowe_zadania.append(zadanie)
            else:
                nowe_zadania.append(zadanie)
        else:
                # Jeśli użytkownika lub roli nie ma, nie przenosimy zadania dalej
            print(f"⚠️ Użytkownik lub rola nie istnieje w guild {guild.name}")
        
        save_zadania(guild.id, nowe_zadania)


# Event on_ready
@bot.event
async def on_ready():
    print(f"✅ Zalogowano jako {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🌐 Slash komendy zsynchronizowane ({len(synced)}).")
    except Exception as e:
        print(f"❌ Błąd synchronizacji: {e}")

async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"🔌 Załadowano cog: {filename}")

#@tasks.loop(hours=2)
#async def wysylaj_wiadomosc():
 #   global ostatnia_wiadomosc
  #  channel_id = 1366034718696407090  # <-- zmień na swój prawdziwy ID kanału!
   # message = """**WYSYŁAJCIE DWA ZDJĘCIA, W NOCY I ZA DNIA (MOŻECIE POPROSTU ROLETY ZASŁONIĆ)**

#**POJEDYNCZE ZDJĘCIA BĘDĄ KASOWANE I NIE BIORĄ UDZIAŁU W KONKURSIE**

#**KOMENTOWAĆ MOŻECIE TYLKO W WĄTKU**
#**KOMENTOWANIE POZA WĄTKIEM = MUTE**
#"""

 #   for guild in bot.guilds:
  #      channel = guild.get_channel(channel_id)
   #     if channel:
    #        try:
     #           if ostatnia_wiadomosc:
      #              try:
       #                 await ostatnia_wiadomosc.delete()
        #                print(f"🗑️ Usunięto poprzednią wiadomość na kanale: {channel.name}")
         #           except Exception as e:
          #              print(f"⚠️ Nie udało się usunąć poprzedniej wiadomości: {e}")

#                ostatnia_wiadomosc = await channel.send(message)
 #               print(f"✅ Wysłano wiadomość na kanał: {channel.name}")
  #          except Exception as e:
   #             print(f"❌ Nie udało się wysłać wiadomości: {e}")



@bot.event
async def on_disconnect():
    print("⚡ Bot utracił połączenie!")

@bot.event
async def on_resumed():
    print("✅ Bot ponownie połączony!")

@bot.event
async def on_error(event, *args, **kwargs):
    print(f"❌ Błąd w evencie: {event}")

@bot.event
async def on_member_join(member):
    channel = member.guild.get_channel(1262162083286482944)  # <- podmień KANAL_ID na liczbę (ID twojego kanału)
    if channel:
        await channel.send(f"Witamy na Kwaterze Rybiego Gangu, {member.mention}! 🎉")


# Komenda /pomoc
@tree.command(name="pomoc", description="Wyświetla listę komend")
async def pomoc(interaction: discord.Interaction):
    if not ma_dozwolona_role(interaction.user):
        embed = discord.Embed(title="Brak uprawnień", description="❌ Nie masz uprawnień do tej komendy.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    embed = discord.Embed(title="📋 Lista Komend", color=discord.Color.blue())
    embed.add_field(name="/temprole", value="Zaplanuj usunięcie roli dla wszystkich członków.", inline=False)
    embed.add_field(name="/temprole_add", value="Nadaj rolę użytkownikowi i zaplanuj jej usunięcie.", inline=False)
    embed.add_field(name="/temprole_cancel", value="Anuluj zaplanowane usunięcie roli użytkownika.", inline=False)
    embed.add_field(name="/temprole_cancel_role", value="Anuluj zaplanowane usunięcie roli dla wszystkich.", inline=False)
    embed.add_field(name="/temprole_list", value="Wyświetl listę zaplanowanych usunięć ról.", inline=False)
    embed.add_field(name="/warn", value="Nadaj ostrzeżenie użytkownikowi.", inline=False)
    embed.add_field(name="/unwarn", value="Usuń ostrzeżenie od użytkownika.", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Komenda /temprole
@tree.command(name="temprole", description="Zaplanuj usunięcie roli wszystkim jej członkom")
@app_commands.describe(role="Rola do zaplanowania", time="Czas", unit="Jednostka czasu: s, m, h, d, mo")
async def temprole(interaction: discord.Interaction, role: discord.Role, time: int, unit: str):
    if not ma_dozwolona_role(interaction.user):
        await interaction.response.send_message(embed=discord.Embed(title="Brak uprawnień", description="❌ Nie masz uprawnień.", color=discord.Color.red()), ephemeral=True)
        return

    unit = unit.lower()
    if unit not in ["s", "m", "h", "d", "mo"]:
        await interaction.response.send_message(embed=discord.Embed(title="Błąd", description="❌ Niepoprawna jednostka czasu.", color=discord.Color.red()), ephemeral=True)
        return

    seconds = time * {"s": 1, "m": 60, "h": 3600, "d": 86400, "mo": 2592000}[unit]

    if not role.members:
        await interaction.response.send_message(embed=discord.Embed(title="Informacja", description="⚠️ Nikt nie ma tej roli.", color=discord.Color.orange()), ephemeral=True)
        return

    usun_o = datetime.utcnow() + timedelta(seconds=seconds)
    zadania = load_zadania(interaction.guild.id)

    for member in role.members:
        zadania.append({
            "user_id": member.id,
            "guild_id": interaction.guild.id,
            "role_id": role.id,
            "usun_o": usun_o.isoformat()
        })

    save_zadania(interaction.guild.id, zadania)

    embed = discord.Embed(title="✅ Zaplanowano", description=f"Rola `{role.name}` zostanie usunięta za {time} {unit}.", color=discord.Color.green())
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Komenda /temprole_add
@tree.command(name="temprole_add", description="Nadaj rolę i zaplanuj jej usunięcie")
@app_commands.describe(member="Użytkownik", role="Rola do nadania", time="Czas", unit="Jednostka czasu: s, m, h, d, mo", powod="Powód")
async def temprole_add(interaction: discord.Interaction, member: discord.Member, role: discord.Role, time: int, unit: str, powod: str = None):
    if not ma_dozwolona_role(interaction.user):
        await interaction.response.send_message(embed=discord.Embed(title="Brak uprawnień", description="❌ Nie masz uprawnień.", color=discord.Color.red()), ephemeral=True)
        return

    unit = unit.lower()
    if unit not in ["s", "m", "h", "d", "mo"]:
        await interaction.response.send_message(embed=discord.Embed(title="Błąd", description="❌ Niepoprawna jednostka czasu.", color=discord.Color.red()), ephemeral=True)
        return

    seconds = time * {"s": 1, "m": 60, "h": 3600, "d": 86400, "mo": 2592000}[unit]
    usun_o = datetime.utcnow() + timedelta(seconds=seconds)

    await member.add_roles(role)

    zadania = load_zadania(interaction.guild.id)
    zadania.append({
        "user_id": member.id,
        "guild_id": interaction.guild.id,
        "role_id": role.id,
        "usun_o": usun_o.isoformat()
    })
    save_zadania(interaction.guild.id, zadania)

    embed = discord.Embed(title="✅ Nadano rolę", description=f"{member.mention} otrzymał rolę `{role.name}`", color=discord.Color.green())
    if powod:
        embed.add_field(name="Powód", value=powod, inline=False)

    await interaction.response.send_message(embed=embed)

# Komenda /temprole_cancel
@tree.command(name="temprole_cancel", description="Anuluj zaplanowane usunięcie roli u użytkownika")
@app_commands.describe(member="Użytkownik", role="Rola")
async def temprole_cancel(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    if not ma_dozwolona_role(interaction.user):
        await interaction.response.send_message(embed=discord.Embed(title="Brak uprawnień", description="❌ Nie masz uprawnień.", color=discord.Color.red()), ephemeral=True)
        return

    zadania = load_zadania(interaction.guild.id)
    nowe_zadania = [z for z in zadania if not (z["user_id"] == member.id and z["role_id"] == role.id)]

    if len(nowe_zadania) == len(zadania):
        embed = discord.Embed(title="❌ Błąd", description="Nie znaleziono zaplanowanego usunięcia tej roli dla użytkownika.", color=discord.Color.red())
    else:
        save_zadania(interaction.guild.id, nowe_zadania)
        embed = discord.Embed(title="✅ Anulowano", description=f"Anulowano zaplanowane usunięcie roli `{role.name}` u {member.mention}.", color=discord.Color.green())

    await interaction.response.send_message(embed=embed, ephemeral=True)

# Komenda /temprole_cancel_role
@tree.command(name="temprole_cancel_role", description="Anuluj zaplanowane usunięcie roli dla wszystkich")
@app_commands.describe(role="Rola")
async def temprole_cancel_role(interaction: discord.Interaction, role: discord.Role):
    if not ma_dozwolona_role(interaction.user):
        await interaction.response.send_message(embed=discord.Embed(title="Brak uprawnień", description="❌ Nie masz uprawnień.", color=discord.Color.red()), ephemeral=True)
        return

    zadania = load_zadania(interaction.guild.id)
    nowe_zadania = [z for z in zadania if z["role_id"] != role.id]

    save_zadania(interaction.guild.id, nowe_zadania)

    embed = discord.Embed(title="✅ Anulowano", description=f"Anulowano wszystkie zaplanowane usunięcia roli `{role.name}`.", color=discord.Color.green())
    await interaction.response.send_message(embed=embed, ephemeral=True)

# Komenda /temprole_list
class PaginatorView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction, embeds: list):
        super().__init__(timeout=180)
        self.embeds = embeds
        self.interaction = interaction
        self.current_page = 0

    @discord.ui.button(label="⬅️", style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.interaction.user:
            await interaction.response.send_message("❌ Nie możesz używać tych przycisków.", ephemeral=True)
            return

        self.current_page = (self.current_page - 1) % len(self.embeds)
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @discord.ui.button(label="➡️", style=discord.ButtonStyle.secondary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.interaction.user:
            await interaction.response.send_message("❌ Nie możesz używać tych przycisków.", ephemeral=True)
            return

        self.current_page = (self.current_page + 1) % len(self.embeds)
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

@tree.command(name="temprole_list", description="Wyświetl listę zaplanowanych usunięć ról")
async def temprole_list(interaction: discord.Interaction):
    if not ma_dozwolona_role(interaction.user):
        await interaction.response.send_message(embed=discord.Embed(
            title="Brak uprawnień",
            description="❌ Nie masz uprawnień.",
            color=discord.Color.red()
        ), ephemeral=True)
        return

    zadania = load_zadania(interaction.guild.id)
    if not zadania:
        embed = discord.Embed(title="📭 Brak zadań", description="Nie ma żadnych zaplanowanych usunięć ról.", color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    embeds = []
    per_page = 10
    for i in range(0, len(zadania), per_page):
        embed = discord.Embed(title="📋 Zaplanowane usunięcia ról", color=discord.Color.green())
        for zadanie in zadania[i:i+per_page]:
            member = interaction.guild.get_member(zadanie["user_id"])
            role = interaction.guild.get_role(zadanie["role_id"])
            czas_usuniecia = datetime.fromisoformat(zadanie["usun_o"]).strftime("%d.%m.%Y %H:%M:%S")
            if member and role:
                embed.add_field(
                    name=f"{member.display_name}",
                    value=f"Rola: `{role.name}`\nUsunięcie: `{czas_usuniecia}`",
                    inline=False
                )
        embed.set_footer(text=f"Strona {i//per_page+1}/{(len(zadania)-1)//per_page+1}")
        embeds.append(embed)

    view = PaginatorView(interaction, embeds)
    await interaction.response.send_message(embed=embeds[0], view=view, ephemeral=True)
    





   # embed = discord.Embed(title="📋 Zaplanowane usunięcia ról", color=discord.Color.green())

# for zadanie in zadania:
#     member = interaction.guild.get_member(zadanie["user_id"])
#     role = interaction.guild.get_role(zadanie["role_id"])
#     czas_usuniecia = datetime.fromisoformat(zadanie["usun_o"]).strftime("%d.%m.%Y %H:%M:%S")

#     if member and role:
#         embed.add_field(
#             name=f"{member.display_name}",
#             value=f"Rola: `{role.name}`\nUsunięcie: `{czas_usuniecia}`",
#             inline=False
#         )

# await interaction.response.send_message(embed=embed, ephemeral=True)

# Komenda /warn
import typing

@tree.command(name="warn", description="Nadaj ostrzeżenie użytkownikowi (lub wielu użytkownikom)")
@app_commands.describe(members="Wzmianki użytkowników oddzielone spacją", powod="Powód", months="Liczba miesięcy (domyślnie 4)")
async def warn(interaction: discord.Interaction, members: str, powod: str, months: int = 4):
    if not ma_dozwolona_role(interaction.user):
        await interaction.response.send_message(
            embed=discord.Embed(title="Brak uprawnień", description="❌ Nie masz uprawnień.", color=discord.Color.red()),
            ephemeral=True
        )
        return

    member_ids = []
    for part in members.split():
        if part.startswith("<@") and part.endswith(">"):
            part = part.replace("<@", "").replace("!", "").replace(">", "")
            if part.isdigit():
                member_ids.append(int(part))

    if not member_ids:
        await interaction.response.send_message(
            embed=discord.Embed(title="Błąd", description="❌ Nie wykryto żadnych użytkowników we wpisanym polu.", color=discord.Color.red()),
            ephemeral=True
        )
        return

    zadania = load_zadania(interaction.guild.id)

    for member_id in member_ids:
        member = interaction.guild.get_member(member_id)
                # 🥚 Easter Egg
        if member.id == 1283132036357554237 and "boar" in powod.lower():
            embed = discord.Embed(
                title="🐗",
                description=f"Kocham cię najbardziej na swiecie {interaction.user.mention}, twój Oluś😚",
                color = discord.Color.from_rgb(255, 105, 180)  # Hot Pink
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        if not member:
            try:
                member = await interaction.guild.fetch_member(member_id)
            except Exception:
                continue

        rola_warn_3 = discord.utils.get(interaction.guild.roles, name="WARN 3/3")
        if rola_warn_3 and rola_warn_3 in member.roles:
            await member.remove_roles(rola_warn_3)

            try:
                czas_timeoutu = timedelta(days=1)
                await member.timeout(czas_timeoutu, reason=f"3/3 WARN — {powod}")

                embed = discord.Embed(
                    title="⏳ Timeout nadany",
                    description=f"{member.mention} otrzymał timeout na {czas_timeoutu.days} dzień.",
                    color=discord.Color.red()
                )
                embed.add_field(name="Powód", value=powod, inline=False)
                embed.set_footer(text="Ostrzeżenia: 4/3 — Timeout nadany automatycznie")

                await interaction.channel.send(content=member.mention, embed=embed)

                log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
                if log_channel:
                    log_embed = discord.Embed(title="📛 Timeout po 3/3 WARN", color=discord.Color.dark_red())
                    log_embed.add_field(name="Użytkownik", value=member.mention, inline=True)
                    log_embed.add_field(name="Czas", value="1 dzień", inline=True)
                    log_embed.add_field(name="Powód", value=powod, inline=False)
                    log_embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
                    log_embed.timestamp = datetime.utcnow()
                    await log_channel.send(embed=log_embed)

            except Exception as e:
                await interaction.channel.send(
                    embed=discord.Embed(
                        title="❌ Błąd timeoutu",
                        description=f"Nie udało się nadać timeoutu {member.mention}: {e}",
                        color=discord.Color.red()
                    )
                )
            continue  # pomijamy dalsze ostrzeżenia dla tej osoby
                # ZAPISZ ROLE I USUN WSZYSTKO OPRÓCZ @everyone
                #previous_roles[member.id] = [role.id for role in member.roles if role != interaction.guild.default_role]
                #for role in member.roles:
                    #if role != interaction.guild.default_role:
                        #await member.remove_roles(role)
                        # Przywróć poprzednie role
                        #role_ids = load_user_roles(member.id)
                        #roles_to_restore = [discord.utils.get(guild.roles, id=rid) for rid in role_ids if discord.utils.get(guild.roles, id=rid)]
                        #if roles_to_restore:
                            #await member.add_roles(*roles_to_restore)
                            #print(f"✅ Przywrócono role użytkownikowi {member.display_name}")

                        # Zapisujemy role (bez roli Muted i @everyone)
                        #role_ids = [role.id for role in member.roles if role != rola_muted and role.name != "@everyone"]
                        #save_user_roles(member.id, role_ids)

                        #if user_id in warns and warns[user_id] >= 3:
                            #guild = interaction.guild
                            #member = await guild.fetch_member(user_id)
                            #mute_role = discord.utils.get(guild.roles, name="Muted")

                            #if not mute_role:
                                #mute_role = await guild.create_role(name="Muted", reason="Tworzenie roli do mutowania")

                            #old_roles = [role.id for role in member.roles if role != guild.default_role]

                            # 🔐 Zapis na trwałym dysku Rendera
                            #mute_file = "/var/data/mutes.json"
                            #try:
                                #with open(mute_file, "r") as f:
                                    #mutes = json.load(f)
                            #except (FileNotFoundError, json.JSONDecodeError):
                                #mutes = []

                            #mute_entry = {
                                #"user_id": user_id,
                                #"guild_id": guild.id,
                                #"roles": old_roles,
                                #"muted_until": (datetime.datetime.utcnow() + datetime.timedelta(days=1)).timestamp()
                            #}

                            #mutes.append(mute_entry)

                            #with open(mute_file, "w") as f:
                                #json.dump(mutes, f, indent=4)

                            #await member.edit(roles=[mute_role])
                            #await interaction.followup.send(f"{member.mention} otrzymał mute na 1 dzień za przekroczenie 3 ostrzeżeń.")


                    
        #embed = discord.Embed(
            #title="🔴 Nadano rolę Muted",
            #description=f"{member.mention} otrzymał rolę **Muted** za przekroczenie 3/3 WARN.",
            #color=discord.Color.red()
        #)
        #embed.add_field(name="Powód", value=powod, inline=False)
        #await interaction.channel.send(content=member.mention, embed=embed)
    

        obecny_warn = 0
        for i in range(1, 4):
            rola = discord.utils.get(interaction.guild.roles, name=f"WARN {i}/3")
            if rola and rola in member.roles:
                obecny_warn = i
                await member.remove_roles(rola)

        nowy_warn = obecny_warn + 1
        if nowy_warn > 3:
            nowy_warn = 3

        rola_warn = discord.utils.get(interaction.guild.roles, name=f"WARN {nowy_warn}/3")
        if not rola_warn:
            await interaction.response.send_message(
                embed=discord.Embed(title="Błąd", description=f"❌ Brak roli `WARN {nowy_warn}/3`.", color=discord.Color.red()),
                ephemeral=True
            )
            return

        await member.add_roles(rola_warn)

        czas_usuniecia = datetime.utcnow() + timedelta(days=30 * months)
        zadania.append({
            "user_id": member.id,
            "guild_id": interaction.guild.id,
            "role_id": rola_warn.id,
            "usun_o": czas_usuniecia.isoformat()
        })

        
        embed = discord.Embed(title="⚠️ Ostrzeżenie", color=discord.Color.orange())
        embed.add_field(name="Użytkownik", value=member.mention, inline=False)
        embed.add_field(name="Warn", value=f"{nowy_warn}/3", inline=True)
        embed.add_field(name="Powód", value=powod, inline=False)
        await interaction.channel.send(content=member.mention, embed=embed)

        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            log_embed = discord.Embed(title="⚠️ Nowy WARN", color=discord.Color.orange())
            log_embed.add_field(name="Użytkownik", value=member.mention, inline=True)
            log_embed.add_field(name="Warn", value=f"{nowy_warn}/3", inline=True)
            log_embed.add_field(name="Powód", value=powod, inline=False)
            log_embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
            log_embed.timestamp = datetime.utcnow()
            await log_channel.send(embed=log_embed)
    save_zadania(interaction.guild.id, zadania)

    await interaction.response.send_message(
        embed=discord.Embed(title="✅ Ostrzeżenia nadane", description="Wysłano wszystkie ostrzeżenia.", color=discord.Color.green()),
        ephemeral=True
    )


# Komenda /unwarn
@tree.command(name="unwarn", description="Usuń ostrzeżenie użytkownikowi")
@app_commands.describe(member="Użytkownik")
async def unwarn(interaction: discord.Interaction, member: discord.Member):
    if not ma_dozwolona_role(interaction.user):
        await interaction.response.send_message(embed=discord.Embed(title="Brak uprawnień", description="❌ Nie masz uprawnień.", color=discord.Color.red()), ephemeral=True)
        return

    znaleziono = False
    for i in range(1, 4):
        rola = discord.utils.get(interaction.guild.roles, name=f"WARN {i}/3")
        if rola in member.roles:
            await member.remove_roles(rola)
            # PRZYWRÓĆ POPRZEDNIE ROLE JEŚLI SĄ ZAPISANE
            #role_ids = previous_roles.get(member.id, [])
            #roles_to_add = [guild.get_role(role_id) for role_id in role_ids if guild.get_role(role_id)]
            #if roles_to_add:
                #await member.add_roles(*roles_to_add)
                #print(f"🎭 Przywrócono role użytkownikowi {member.display_name}")

            znaleziono = True

    if znaleziono:
        embed = discord.Embed(title="✅ Ostrzeżenie usunięte", description=f"Ostrzeżenie u {member.mention} zostało usunięte.", color=discord.Color.green())
    else:
        embed = discord.Embed(title="ℹ️ Informacja", description=f"{member.mention} nie posiada żadnych ostrzeżeń.", color=discord.Color.blue())

    await interaction.response.send_message(embed=embed)

@tree.command(name="show_files", description="Pokaż pliki zapisane w katalogu Persistent Storage")
async def show_files(interaction: discord.Interaction):
    if not ma_dozwolona_role(interaction.user):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Brak uprawnień",
                description="❌ Nie masz uprawnień do tej komendy.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
        return

    try:
        files = os.listdir("/var/data/")
        if not files:
            opis = "Brak plików w katalogu `/var/data/`."
        else:
            opis = "\n".join(f"- `{file}`" for file in files)

        embed = discord.Embed(title="📂 Pliki w /var/data/", description=opis, color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    except Exception as e:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Błąd",
                description=f"Nie udało się odczytać plików: {e}",
                color=discord.Color.red()
            ),
            ephemeral=True
        )



        for z in zadania:
            czas_usuniecia = datetime.fromisoformat(z["usun_o"])
            if teraz >= czas_usuniecia:
                member = guild.get_member(z["user_id"])
                role = guild.get_role(z["role_id"])
                if member and role:
                    try:
                        await member.remove_roles(role)
                        print(f"✅ Usunięto rolę {role.name} u {member.display_name}")
                    except Exception as e:
                        print(f"❌ Błąd przy usuwaniu roli: {e}")
            else:
                nowe_zadania.append(z)

        save_zadania(guild.id, nowe_zadania)

@tree.command(name="import_zadania", description="Importuj zadania z pliku JSON do bazy danych")
@app_commands.describe(plik="Plik JSON do zaimportowania")
async def import_zadania(interaction: discord.Interaction, plik: discord.Attachment):
    if not ma_dozwolona_role(interaction.user):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Brak uprawnień",
                description="❌ Nie masz uprawnień do tej komendy.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
        return

    try:
        zawartosc = await plik.read()
        tekst = zawartosc.decode('utf-8')
        dane = json.loads(tekst)
        
        guild_id = interaction.guild.id
        save_zadania(guild_id, dane)

        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ Import zakończony",
                description=f"Zaimportowano {len(dane)} zadań dla serwera `{guild_id}`.",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

    except Exception as e:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Błąd importu",
                description=f"Nie udało się zaimportować danych: {e}",
                color=discord.Color.red()
            ),
            ephemeral=True
        )

@tree.command(name="unmute", description="Usuń rolę Muted użytkownikowi")
@app_commands.describe(member="Użytkownik, któremu chcesz usunąć Muted")
async def unmute(interaction: discord.Interaction, member: discord.Member):
    if not ma_dozwolona_role(interaction.user):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="Brak uprawnień",
                description="❌ Nie masz uprawnień do używania tej komendy.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
        return

    #rola_muted = discord.utils.get(interaction.guild.roles, name="Muted")
#if rola_muted:
    #await member.add_roles(rola_muted)
    #await member.remove_roles(rola_warn_3)

    #czas_usuniecia = datetime.utcnow() + timedelta(days=1)
    #zadania.append({
        #"user_id": member.id,
        #"guild_id": interaction.guild.id,
        #"role_id": rola_muted.id,
        #"usun_o": czas_usuniecia.isoformat()
    #})
    #save_zadania(interaction.guild.id, zadania)
    
    
    #rola_muted = discord.utils.get(interaction.guild.roles, name="Muted")
    #if not rola_muted:
        #await interaction.response.send_message(
            #embed=discord.Embed(
                #title="Błąd",
                #description="❌ Brak roli `Muted` na serwerze.",
                #color=discord.Color.red()
            #),
            #ephemeral=True
        #)
        #return

    #if rola_muted not in member.roles:
        #await interaction.response.send_message(
            #embed=discord.Embed(
                #title="Informacja",
                #description=f"ℹ️ {member.mention} nie posiada roli `Muted`.",
                #color=discord.Color.blue()
            #),
            #ephemeral=True
        #)
        #return

    await member.remove_roles(rola_muted)

    embed = discord.Embed(
        title="✅ Unmute",
        description=f"Użytkownik {member.mention} został odmutowany.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

# Komenda slash
def wczytaj_dane():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            dane = json.load(f)
    except FileNotFoundError:
        dane = {}

    if "salony" not in dane:
        dane["salony"] = {}
    if "gracze" not in dane:
        dane["gracze"] = {}

    return dane

def zapisz_dane(dane):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dane, f, indent=4)

@bot.tree.command(name="stworz", description="Stwórz swój salon")
async def stworz(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    dane = wczytaj_dane()

    if user_id in dane["salony"]:
        embed = discord.Embed(
            title="❌ Błąd",
            description="Masz już stworzony salon.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    dane["salony"][user_id] = {
        "nazwa": f"Salon {interaction.user.display_name}",
        "auta": [],
        "wartosc": 0
    }

    dane["gracze"][user_id] = {
        "pieniadze": 100000
    }

    zapisz_dane(dane)

    embed = discord.Embed(
        title="✅ Sukces!",
        description="Twój salon został stworzony z budżetem 100 000 zł.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

class PotwierdzenieUsuniecia(ui.View):
    def __init__(self, interaction, user_id, dane):
        super().__init__(timeout=30)
        self.interaction = interaction
        self.user_id = user_id
        self.dane = dane

    @ui.button(label="🗑️ Tak, usuń", style=discord.ButtonStyle.danger)
    async def potwierdz(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != int(self.user_id):
            embed = discord.Embed(
                title="❌ Błąd",
                description="To nie jest Twoja decyzja!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        self.dane["salony"].pop(self.user_id, None)
        self.dane["gracze"].pop(self.user_id, None)

        zapisz_dane(self.dane)

        embed = discord.Embed(
            title="✅ Usunięto",
            description="Twój salon i konto zostały usunięte.",
            color=discord.Color.green()
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

    @ui.button(label="❌ Anuluj", style=discord.ButtonStyle.secondary)
    async def anuluj(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id != int(self.user_id):
            embed = discord.Embed(
                title="❌ Błąd",
                description="To nie jest Twoja decyzja!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(
            title="❎ Anulowano",
            description="Usuwanie salonu zostało anulowane.",
            color=discord.Color.orange()
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

@bot.tree.command(name="usun_salon", description="Usuń swój salon (bezpowrotnie)")
async def usun_salon(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    dane = wczytaj_dane()

    if user_id not in dane["salony"]:
        embed = discord.Embed(
            title="❌ Błąd",
            description="Nie masz jeszcze salonu do usunięcia.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    view = PotwierdzenieUsuniecia(interaction, user_id, dane)

    embed = discord.Embed(
        title="⚠️ Potwierdzenie",
        description="Na pewno chcesz usunąć swój salon i konto? Tej operacji nie można cofnąć!",
        color=discord.Color.orange()
    )
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="kup_auto", description="Kup wybrane auto do swojego salonu")
async def kup_auto(interaction: discord.Interaction, numer: int):
    user_id = str(interaction.user.id)
    dane = wczytaj_dane()

    if user_id not in dane["salony"]:
        embed = discord.Embed(
            title="❌ Błąd",
            description="Nie masz jeszcze salonu.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if user_id not in dane["gracze"]:
        embed = discord.Embed(
            title="❌ Błąd",
            description="Nie masz konta gracza.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    if numer < 1 or numer > len(KATALOG_AUT):
        embed = discord.Embed(
            title="❌ Błąd",
            description="Niepoprawny numer auta!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    auto = KATALOG_AUT[numer - 1]
    cena = next((a["price"] for a in dane["ceny"] if a["brand"] == auto["brand"] and a["model"] == auto["model"]), None)
    pieniadze = dane["gracze"][user_id]["pieniadze"]

    if pieniadze < cena:
        embed = discord.Embed(
            title="❌ Brak środków",
            description="Nie masz wystarczająco pieniędzy!",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    dane["gracze"][user_id]["pieniadze"] -= cena
    dane["salony"][user_id]["auta"].append(auto)
    dane["salony"][user_id]["wartosc"] += cena
    zapisz_dane(dane)

    embed = discord.Embed(
        title="🚗 Zakup udany!",
        description=f"Kupiłeś **{auto['brand']} {auto['model']}** za **{cena} zł**.",
        color=discord.Color.green()
    )
    embed.add_field(name="📦 Aut w salonie", value=str(len(dane['salony'][user_id]['auta'])), inline=True)
    embed.add_field(name="💼 Wartość salonu", value=f"{dane['salony'][user_id]['wartosc']} zł", inline=True)
    embed.set_footer(text=f"💰 Pozostało: {dane['gracze'][user_id]['pieniadze']} zł")

    await interaction.response.send_message(embed=embed, ephemeral=True)


def wczytaj_dane():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            dane = json.load(f)
    except FileNotFoundError:
        dane = {}

    if "salony" not in dane:
        dane["salony"] = {}
    if "gracze" not in dane:
        dane["gracze"] = {}
    if "ceny" not in dane:
        dane["ceny"] = generuj_ceny_aut()
    if "ostatnia_aktualizacja" not in dane:
        dane["ostatnia_aktualizacja"] = ""

    sprawdz_aktualizacje(dane)
    return dane

def zapisz_dane(dane):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dane, f, indent=4)

def generuj_ceny_aut():
    return [
        {
            "brand": auto["brand"],
            "model": auto["model"],
            "price": int(auto["base_price"] * random.uniform(0.85, 1.15))
        }
        for auto in KATALOG_AUT
    ]

def sprawdz_aktualizacje(dane):
    dzisiaj = datetime.now().strftime("%Y-%m-%d")
    if dane.get("ostatnia_aktualizacja") != dzisiaj:
        dane["ostatnia_aktualizacja"] = dzisiaj
        dane["ceny"] = generuj_ceny_aut()

        # Aktualizuj wartość salonów
        for salon in dane["salony"].values():
            salon["wartosc"] = sum(
                next((a["price"] for a in dane["ceny"] if a["brand"] == auto["brand"] and a["model"] == auto["model"]), 0)
                for auto in salon["auta"]
            )

        zapisz_dane(dane)



    

@bot.tree.command(name="ranking", description="Zobacz ranking najlepszych salonów")
async def ranking(interaction: discord.Interaction):
    dane = wczytaj_dane()

    salony = dane.get("salony", {})
    if not salony:
        await interaction.response.send_message(
            embed=discord.Embed(description="❌ Brak salonów w rankingu.", color=discord.Color.red()),
            ephemeral=True
        )
        return

    # Posortuj salony malejąco według wartości
    top_salony = sorted(salony.items(), key=lambda x: x[1].get("wartosc", 0), reverse=True)[:10]

    embed = discord.Embed(
        title="🏆 Ranking Salonów (Top 10)",
        description="Najlepsze salony według wartości 💰",
        color=discord.Color.gold()
    )

    for miejsce, (user_id, salon) in enumerate(top_salony, start=1):
        user = await interaction.client.fetch_user(int(user_id))
        embed.add_field(
            name=f"{miejsce}. {salon['nazwa']} ({user.display_name})",
            value=f"Wartość: {salon['wartosc']} zł",
            inline=False
        )

    await interaction.response.send_message(embed=embed, ephemeral=False)

def wczytaj_dane():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            dane = json.load(f)
    except FileNotFoundError:
        dane = {}

    if "salony" not in dane:
        dane["salony"] = {}
    if "gracze" not in dane:
        dane["gracze"] = {}
    if "ceny" not in dane:
        dane["ceny"] = generuj_ceny_aut()
    if "ostatnia_aktualizacja" not in dane:
        dane["ostatnia_aktualizacja"] = ""

    sprawdz_aktualizacje(dane)
    return dane

def zapisz_dane(dane):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(dane, f, indent=4)

def generuj_ceny_aut():
    return [
        {
            "brand": auto["brand"],
            "model": auto["model"],
            "price": int(auto["base_price"] * random.uniform(0.85, 1.15))
        }
        for auto in KATALOG_AUT
    ]

def sprawdz_aktualizacje(dane):
    teraz = datetime.now()
    ostatnia = dane.get("ostatnia_aktualizacja")

    if ostatnia is None:
        ostatnia = teraz - timedelta(days=1)  # jeśli brak daty, wymuś aktualizację
    else:
        # Jeśli masz timestamp w formacie string, zamień na datetime
        if isinstance(ostatnia, str):
            try:
                ostatnia = datetime.fromisoformat(ostatnia)
            except Exception:
                ostatnia = teraz - timedelta(days=1)  # zabezpieczenie na wypadek błędu

    # Jeśli minęła 1 godzina (3600 sekund) od ostatniej aktualizacji, wykonaj aktualizację
    if (teraz - ostatnia).total_seconds() > 1800:
        dane["ostatnia_aktualizacja"] = teraz.isoformat()
        dane["ceny"] = generuj_ceny_aut()

        # Aktualizuj wartość salonów
        for salon in dane["salony"].values():
            salon["wartosc"] = sum(
                next((a["price"] for a in dane["ceny"] if a["brand"] == auto["brand"] and a["model"] == auto["model"]), 0)
                for auto in salon["auta"]
            )

        zapisz_dane(dane)

@bot.tree.command(name="katalog_aut", description="Wyświetl katalog aut")
async def katalog_aut(interaction: discord.Interaction):
    dane = wczytaj_dane()
    embed = discord.Embed(title="📋 Katalog aut (ceny dynamiczne)", color=discord.Color.blue())

    for idx, auto in enumerate(dane["ceny"], start=1):
        # Szukamy mocy z katalogu
        katalog_auto = next((a for a in KATALOG_AUT if a["brand"] == auto["brand"] and a["model"] == auto["model"]), None)
        moc = katalog_auto["moc_bazowa"] if katalog_auto else "Brak danych"

        embed.add_field(
            name=f"{idx}. {auto['brand']} {auto['model']}",
            value=f"💰 Cena: {auto['price']} zł\n🏁 Moc: {moc} KM",
            inline=False
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="salon", description="Zobacz swój salon")
async def salon(interaction: discord.Interaction):
    dane = wczytaj_dane()
    user_id = str(interaction.user.id)

    if user_id not in dane["salony"]:
        await interaction.response.send_message(embed=discord.Embed(description="❌ Nie masz jeszcze salonu.", color=discord.Color.red()), ephemeral=True)
        return

    salon = dane["salony"][user_id]
    embed = discord.Embed(title=f"🏢 {salon['nazwa']}", color=discord.Color.green())
    embed.add_field(name="💰 Wartość salonu", value=f"{salon['wartosc']} zł", inline=False)
    auta = salon["auta"]
    if auta:
        for auto in auta:
            embed.add_field(name=f"{auto['brand']} {auto['model']}", value=f"Szacowana wartość: {auto['base_price']} zł", inline=False)
    else:
        embed.add_field(name="Brak aut", value="Kup coś w katalogu!", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


# --- Komenda sprzedaży auta z klientami zwykłymi i premium ---

@bot.tree.command(name="sprzedaj_auto", description="Spróbuj sprzedać wybrane auto z salonu klientowi")
@app_commands.describe(numer="Numer auta z Twojego salonu do sprzedaży")
async def sprzedaj_auto(interaction: discord.Interaction, numer: int):
    dane = wczytaj_dane()
    user_id = str(interaction.user.id)

    if user_id not in dane["salony"] or not dane["salony"][user_id]["auta"]:
        await interaction.response.send_message(
            embed=discord.Embed(description="❌ Nie masz aut do sprzedaży.", color=discord.Color.red()),
            ephemeral=True
        )
        return

    auta = dane["salony"][user_id]["auta"]

    if numer < 1 or numer > len(auta):
        await interaction.response.send_message(
            embed=discord.Embed(description="❌ Niepoprawny numer auta.", color=discord.Color.red()),
            ephemeral=True
        )
        return

    auto = auta[numer - 1]

    # Sprawdź, czy klient się pojawi
    if random.random() > 0.7:  # 30% szans że nikt nie chce kupić
        await interaction.response.send_message(
            embed=discord.Embed(description="😞 Dziś brak chętnych klientów na to auto.", color=discord.Color.dark_grey()),
            ephemeral=True
        )
        return

    # Sprawdź, czy klient premium (20% szans)
    klient_premium = random.random() < 0.2

    # Znajdź aktualną wartość z katalogu
    dane_ceny = next((a for a in dane["ceny"] if a["brand"] == auto["brand"] and a["model"] == auto["model"]), None)
    if not dane_ceny:
        await interaction.response.send_message(
            embed=discord.Embed(description="❌ Nie udało się znaleźć ceny katalogowej.", color=discord.Color.red()),
            ephemeral=True
        )
        return

    cena_katalogowa = dane_ceny["price"]

    if klient_premium:
        # Premium klient - lepsza oferta i wyższe prawdopodobieństwo zaakceptowania
        cena_oferta = int(random.uniform(1.05, 1.3) * cena_katalogowa)
        cena_oferta = max(cena_oferta, auto["base_price"])
        opis_klienta = "✨ Klient premium"
        kolor_embed = discord.Color.gold()
    else:
        # Zwykły klient
        cena_oferta = int(random.uniform(0.8, 1.2) * cena_katalogowa)
        cena_oferta = max(cena_oferta, auto["base_price"])
        opis_klienta = "Klient standardowy"
        kolor_embed = discord.Color.orange()

    embed = discord.Embed(
        title="💼 Oferta sprzedaży",
        description=(
            f"📢 {opis_klienta} chce kupić **{auto['brand']} {auto['model']}**.\n"
            f"💵 Oferuje: **{cena_oferta} zł**\n\n"
            "✅ Akceptujesz tę ofertę?"
        ),
        color=kolor_embed
    )

    view = PotwierdzenieSprzedazy(auto, cena_oferta, dane, user_id)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


class PotwierdzenieSprzedazy(ui.View):
    def __init__(self, auto, cena, dane, user_id):
        super().__init__(timeout=30)
        self.auto = auto
        self.cena = cena
        self.dane = dane
        self.user_id = user_id

    @ui.button(label="✅ Sprzedaj", style=discord.ButtonStyle.green)
    async def sprzedaj(self, interaction: discord.Interaction, button: ui.Button):
        salon = self.dane["salony"][self.user_id]
        gracz = self.dane["gracze"][self.user_id]

        if self.auto not in salon["auta"]:
            await interaction.response.send_message("❌ Auto zostało już sprzedane lub nie istnieje.", ephemeral=True)
            return

        salon["auta"].remove(self.auto)

        wartosc_auta = next((a["price"] for a in self.dane["ceny"]
                             if a["brand"] == self.auto["brand"] and a["model"] == self.auto["model"]), 0)
        salon["wartosc"] = max(salon["wartosc"] - wartosc_auta, 0)  # Nie pozwól zejść poniżej 0

        gracz["pieniadze"] += self.cena
        zapisz_dane(self.dane)

        await interaction.response.edit_message(
            embed=discord.Embed(
                description=f"✅ Sprzedałeś **{self.auto['brand']} {self.auto['model']}** za **{self.cena} zł**.",
                color=discord.Color.green()
            ),
            view=None
        )
        self.stop()

    @ui.button(label="❌ Odrzuć", style=discord.ButtonStyle.red)
    async def anuluj(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(
            embed=discord.Embed(description="❎ Odrzuciłeś ofertę sprzedaży.", color=discord.Color.greyple()),
            view=None
        )
        self.stop()

@tree.command(name="balans", description="Sprawdź ile masz pieniędzy.")
async def balans(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    dane = wczytaj_dane()

    # Upewnij się, że gracz istnieje w danych
    if user_id not in dane["gracze"]:
        dane["gracze"][user_id] = {"pieniadze": 0}
        zapisz_dane(dane)

    pieniadze = dane["gracze"][user_id].get("pieniadze", 0)

    await interaction.response.send_message(
        f"💰 Masz {pieniadze} pieniędzy.", ephemeral=True
    )

@bot.tree.command(name="kupauto", description="Kup prywatne auto z katalogu")
@app_commands.describe(numer="Numer auta z katalogu do kupienia")
async def kupauto(interaction: Interaction, numer: int):
    dane = wczytaj_dane()
    user_id = str(interaction.user.id)

    gracz = dane["gracze"].setdefault(user_id, {})
    gracz.setdefault("pieniadze", 0)
    gracz.setdefault("auto_prywatne", None)

    if gracz["auto_prywatne"] is not None:
        await interaction.response.send_message(
            embed=Embed(description="❌ Masz już prywatne auto. Sprzedaj je przed zakupem nowego.", color=Color.red()),
            ephemeral=True
        )
        return

    katalog = dane.get("ceny", [])
    if numer < 1 or numer > len(katalog):
        await interaction.response.send_message(
            embed=Embed(description="❌ Niepoprawny numer auta z katalogu.", color=Color.red()),
            ephemeral=True
        )
        return

    auto_do_kupienia = katalog[numer - 1]
    cena = auto_do_kupienia["price"]

    # Tutaj dodajemy losową obniżkę ceny od 15% do 30%
    procent_obnizki = random.uniform(15, 30)
    cena_po_obnizce = int(cena * (1 - procent_obnizki / 100))

    if gracz["pieniadze"] < cena_po_obnizce:
        await interaction.response.send_message(
            embed=Embed(description=f"❌ Nie masz wystarczająco pieniędzy. Potrzebujesz {cena_po_obnizce} zł (po obniżce).", color=Color.red()),
            ephemeral=True
        )
        return

    # Kupno auta z ceną po obniżce
    gracz["pieniadze"] -= cena_po_obnizce
    gracz["auto_prywatne"] = {
        "brand": auto_do_kupienia["brand"],
        "model": auto_do_kupienia["model"],
        "price": cena_po_obnizce,
        "tuning": {
            "silnik": 0,
            "turbo": 0,
            "nitro": 0,
            "opony": 0,
            "zawieszenie": 0,
            "aero": 0
        }
    }

    zapisz_dane(dane)

    await interaction.response.send_message(
        embed=Embed(description=f"✅ Kupiłeś {auto_do_kupienia['brand']} {auto_do_kupienia['model']} za {cena_po_obnizce} zł (obniżka {procent_obnizki:.2f}%) jako swoje prywatne auto.", color=Color.green()),
        ephemeral=True
    )


@bot.tree.command(name="mojeauto", description="Pokaż swoje prywatne auto z tuningiem")
async def mojeauto(interaction: discord.Interaction):
    dane = wczytaj_dane()
    user_id = str(interaction.user.id)

    gracz = dane["gracze"].get(user_id)
    if not gracz or "auto_prywatne" not in gracz:
        await interaction.response.send_message("❌ Nie masz prywatnego auta.", ephemeral=True)
        return

    auto = gracz["auto_prywatne"]

    katalog_auto = next((a for a in KATALOG_AUT if a["brand"] == auto["brand"] and a["model"] == auto["model"]), None)
    if not katalog_auto:
        await interaction.response.send_message("❌ Nie znaleziono auta w katalogu.", ephemeral=True)
        return

    moc_bazowa = katalog_auto.get("moc_bazowa", 0)
    tuning = auto.get("tuning", {})

    moc_dodatkowa = 0
    for czesc, poziom in tuning.items():
        moc_dodatkowa += TUNING_POWER_INCREASE.get(czesc, 0) * poziom

    moc_calkowita = moc_bazowa + moc_dodatkowa

    embed = discord.Embed(title="🚗 Twoje prywatne auto", color=discord.Color.blue())
    embed.add_field(name="Marka", value=auto["brand"], inline=True)
    embed.add_field(name="Model", value=auto["model"], inline=True)
    embed.add_field(name="Cena", value=f"{auto.get('price', 0)} zł", inline=True)
    embed.add_field(name="Moc bazowa", value=f"{moc_bazowa} KM", inline=True)
    embed.add_field(name="Moc z tuningu", value=f"+{moc_dodatkowa} KM", inline=True)
    embed.add_field(name="Moc całkowita", value=f"{moc_calkowita} KM", inline=True)

    tuning_opis = "\n".join(f"{czesc.capitalize()}: {poziom}" for czesc, poziom in tuning.items() if poziom > 0)
    if tuning_opis:
        embed.add_field(name="Poziomy tuningu", value=tuning_opis, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="sprzedajauto", description="Sprzedaj swoje prywatne auto")
async def sprzedajauto(interaction: Interaction):
    dane = wczytaj_dane()
    user_id = str(interaction.user.id)

    gracz = dane["gracze"].get(user_id)
    if not gracz or not gracz.get("auto_prywatne"):
        await interaction.response.send_message(embed=Embed(description="❌ Nie masz prywatnego auta do sprzedaży.", color=Color.red()), ephemeral=True)
        return

    auto = gracz["auto_prywatne"]
    cena_sprzedazy = auto["price"]
    # Można dodać wycenę uwzględniającą tuning — póki co bazowa cena

    gracz["pieniadze"] += cena_sprzedazy
    gracz["auto_prywatne"] = None

    dane["gracze"][user_id] = gracz
    zapisz_dane(dane)

    await interaction.response.send_message(embed=Embed(description=f"✅ Sprzedałeś swoje prywatne auto za {cena_sprzedazy} zł.", color=Color.green()), ephemeral=True)

# Bazowy koszt 1 poziomu danej części tuningu
TUNING_BASE_COSTS = {
    "silnik": 5000,
    "turbo": 7000,
    "nitro": 4000,
    "opony": 3000,
    "zawieszenie": 3500,
    "aero": 2000
}

# Ile KM dodaje każdy poziom danej części
TUNING_POWER_INCREASE = {
    "silnik": 30,
    "turbo": 40,
    "nitro": 20,
    "opony": 5,
    "zawieszenie": 10,
    "aero": 5
}

# O ile procent wzrasta wartość auta za każdy poziom danej części
TUNING_VALUE_INCREASE_PERCENT = {
    "silnik": 5,        # 5% za poziom
    "turbo": 6,
    "nitro": 3,
    "opony": 1,
    "zawieszenie": 2,
    "aero": 1
}

@bot.tree.command(name="tuning", description="Kup tuning dla swojego auta")
@app_commands.describe(czesc="Część do tuningu: silnik, turbo, nitro, opony, zawieszenie, aero")
async def tunuj(interaction: discord.Interaction, czesc: str):
    czesc = czesc.lower()
    if czesc not in TUNING_BASE_COSTS:
        embed = discord.Embed(
            title="❌ Błąd",
            description=f"Nieznana część tuningu: **{czesc}**",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    dane = wczytaj_dane()
    user_id = str(interaction.user.id)
    gracz = dane["gracze"].get(user_id)

    if not gracz or "auto_prywatne" not in gracz:
        embed = discord.Embed(
            description="❌ Nie posiadasz prywatnego auta do tuningu.",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    auto = gracz["auto_prywatne"]
    tuning = auto.get("tuning", {
        "silnik": 0,
        "turbo": 0,
        "nitro": 0,
        "opony": 0,
        "zawieszenie": 0,
        "aero": 0
    })

    obecny_poziom = tuning.get(czesc, 0)

    if obecny_poziom >= 5:
        embed = discord.Embed(
            title="❌ Maksymalny poziom",
            description=f"Część **{czesc}** ma już maksymalny poziom (5).",
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    nowy_poziom = obecny_poziom + 1

    # Rosnący koszt bazujący na obecnym poziomie i typie części
    bazowy_koszt = TUNING_BASE_COSTS[czesc]
    koszt = int(bazowy_koszt * (3.3 ** obecny_poziom))

    if gracz["pieniadze"] < koszt:
        embed = discord.Embed(
            title="❌ Za mało pieniędzy",
            description=(f"Nie masz wystarczająco pieniędzy na zakup poziomu {nowy_poziom} części **{czesc}**.\nKoszt: **{koszt} zł**."),
            color=discord.Color.red()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return

    tuning[czesc] = nowy_poziom
    auto["tuning"] = tuning

    gracz["pieniadze"] -= koszt

    procent_zwiekszenia = TUNING_VALUE_INCREASE_PERCENT[czesc] * nowy_poziom
    wartosc_bazowa = auto.get("price", 0)
    wartosc_nowa = int(wartosc_bazowa * (1 + procent_zwiekszenia / 100))
    auto["price"] = wartosc_nowa

    zapisz_dane(dane)

    embed = discord.Embed(
        title="✅ Tuning zakupiony!",
        description=(
            f"Udało się kupić tuning **{czesc}** poziom **{nowy_poziom}**!\n"
            f"Koszt: **{koszt} zł**\n"
            f"Wartość auta wzrosła do **{wartosc_nowa} zł**\n"
            f"Pozostało Ci **{gracz['pieniadze']} zł**"
        ),
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

TUNING_BASE_COSTS = {
    "silnik": 5000,
    "turbo": 7000,
    "nitro": 6000,
    "opony": 3000,
    "zawieszenie": 4000,
    "aero": 3500
}
TUNING_VALUE_INCREASE_PERCENT = {
    "silnik": 1.5,
    "turbo": 2.0,
    "nitro": 1.8,
    "opony": 1.0,
    "zawieszenie": 1.2,
    "aero": 1.1
}

ACTIVE_RACES = {}
BETS = {}

COMMENTARY_MESSAGES = [
    "🔥 {driver1} startuje z piskiem opon!",
    "💨 {driver2} rzuca się do przodu jak rakieta!",
    "🏁 Obaj kierowcy są łeb w łeb!",
    "🚧 {driver1} omija pachołki jak mistrz slalomu!",
    "⚡ {driver2} aktywuje nitro i przyspiesza!",
    "🛞 {driver1} traci przyczepność na zakręcie!",
    "💥 {driver2} prawie zalicza krawężnik, ale ratuje sytuację!",
    "🚀 {driver1} łapie niesamowite przyspieszenie!",
    "🌀 {driver2} robi piękny drift przez zakręt!",
    "👀 Widzowie nie mogą oderwać wzroku od tej akcji!",
    "🚧 {driver1} omija przeszkody jak zawodowiec!",
    "💨 {driver2} śmiga przez zakręt jak błyskawica!",
    "🏁 Obaj kierowcy walczą o każdy centymetr trasy!",
    "🌀 {driver1} pokazuje mistrzowski drift!",
    "⚡ {driver2} aktywuje turbo – co za prędkość!",
    "💥 {driver1} ledwo unika kolizji – serce staje!",
    "🔥 {driver2} jedzie na granicy możliwości!",
    "🚀 {driver1} wyprzedza z chirurgiczną precyzją!",
    "🛞 {driver2} gubi przyczepność, ale opanowuje sytuację!",
    "👀 Publiczność szaleje – co za przejazd {driver1}!",
    "🚗 {driver2} zbliża się niebezpiecznie do {driver1}!",
    "🧠 {driver1} analizuje każdy ruch rywala!",
    "💪 {driver2} nie odpuszcza nawet na milimetr!",
    "🚨 {driver1} ociera się o barierkę – to było blisko!",
    "🏎️ {driver2} znajduje idealną linię jazdy!",
    "🎯 {driver1} trafia w punkt z wejściem w zakręt!",
    "🏔️ {driver2} pokonuje trudną sekcję bezbłędnie!",
    "🎢 To prawdziwa kolejka górska – {driver1} szaleje na trasie!",
    "🌪️ {driver2} przemyka jak huragan!",
    "🧊 {driver1} zachowuje zimną krew pod presją!",
    "🧨 {driver2} odpala manewr godny mistrza świata!",
    "📉 {driver1} nieco traci tempo – czy to problem techniczny?",
    "📈 {driver2} nadrabia straty z niesamowitą skutecznością!",
    "⚔️ Walka pomiędzy {driver1} i {driver2} wchodzi na nowy poziom!",
    "🛑 {driver1} blokuje przeciwnika genialnym ruchem!",
    "🔁 {driver2} próbuje wewnętrznego ataku – odważnie!",
    "🎮 Jazda {driver1} wygląda jak z gry komputerowej!",
    "🎥 Kamery ledwo nadążają za {driver2}!",
    "🔧 {driver1} świetnie radzi sobie mimo wcześniejszych problemów!",
    "🎓 {driver2} uczy resztę jak się jeździ pod presją!",
    "🪄 {driver1} czaruje na trasie – magia kierownicy!",
    "📣 Tłum wiwatuje – {driver2} zyskuje prowadzenie!",
    "🕹️ {driver1} steruje bolidem z niezwykłą finezją!",
    "🌉 {driver2} przechodzi przez zakręt jak po sznurku!",
    "🚦 Nie ma litości – {driver1} ciśnie gaz do dechy!",
    "💢 {driver2} z wściekłością ściga rywala!",
    "🌈 {driver1} pokazuje kunszt techniczny – prawdziwy artysta!",
    "📍 {driver2} trzyma się linii idealnie – bezbłędnie!",
    "🔒 {driver1} zamyka każdy możliwy atak!",
    "🫣 Ciężko patrzeć – {driver2} jedzie na granicy katastrofy!",
    "🧩 Manewr {driver1} był jak z podręcznika!",
    "🪤 {driver2} zastawia pułapkę w zakręcie – sprytne!",
    "🫧 {driver1} wchodzi w zakręt z lekkością motyla!",
    "🪶 {driver2} płynie przez trasę, jakby nie dotykał asfaltu!",
    "🪜 {driver1} pięknie pnie się w górę stawki!",
    "🪙 {driver2} rzuca monetą – atak czy czekać?",
    "🔮 Czy {driver1} przewidział ten ruch rywala?",
    "🧗 {driver2} wspina się po pozycjach z niesamowitą determinacją!",
    "⛓️ {driver1} nie daje się oderwać – trzyma się jak cień!",
    "🚿 {driver2} zmywa rywala jak deszcz z szyby!",
    "🚧 {driver1} przeciska się między autami jak duch!",
    "💨 {driver2} mknie przez skrzyżowanie bez cienia zawahania!",
    "🏁 Obaj kierowcy pędzą w ciasnym tunelu – brak miejsca na błędy!",
    "🌀 {driver1} driftuje na skrzyżowaniu – mistrzostwo uliczne!",
    "⚡ {driver2} łapie rytm i pokonuje kolejny zakręt z finezją!",
    "💥 {driver1} prawie trąca zaparkowane auto – to była o włos!",
    "🔥 {driver2} wbija się w zakręt z rykiem silnika!",
    "🚀 {driver1} odbija w prawo tuż przed taksówką!",
    "🛞 {driver2} gubi tył w ciasnej alejce – ale odzyskuje kontrolę!",
    "👀 Tłum na chodnikach wariuje – {driver1} jedzie jak w filmie!",
    "🚗 {driver2} ścina zakręt przez pasy – totalna dominacja!",
    "🧠 {driver1} kalkuluje ryzyko i wygrywa zakręt pod presją!",
    "💪 {driver2} nie daje się zepchnąć mimo ciasnej ulicy!",
    "🚨 {driver1} prawie otarł się o hydrant – co za precyzja!",
    "🏎️ {driver2} wbija się w zakręt jak strzała!",
    "🎯 {driver1} trafia idealny punkt hamowania przy sklepie!",
    "🌃 {driver2} przemyka przez ulice oświetlone neonami!",
    "🎢 Co za emocje! {driver1} przeskakuje przez próg zwalniający bez straty prędkości!",
    "🌪️ {driver2} zostawia rywala w tumanach kurzu!",
    "🧊 {driver1} trzyma chłodną głowę w szaleństwie miasta!",
    "🧨 {driver2} przemyka pod wiaduktem w milimetrach od ściany!",
    "📉 {driver1} zwalnia na mokrej nawierzchni – mądrze!",
    "📈 {driver2} nadrabia każdy centymetr na prostej między blokami!",
    "⚔️ Walka między {driver1} i {driver2} przenosi się na wąską uliczkę!",
    "🛑 {driver1} odcina {driver2} na wjeździe w rondo – bezlitosny manewr!",
    "🔁 {driver2} próbuje objazdu przez boczną ulicę!",
    "🎮 Jazda {driver1} wygląda jak wyjęta z gry arcade!",
    "🎥 Kamery uliczne rejestrują jak {driver2} wchodzi bokiem w skrzyżowanie!",
    "🔧 {driver1} pokazuje, że zna każdy zakręt w tym mieście!",
    "🎓 {driver2} prowadzi jak lokalna legenda ulicy!",
    "🪄 {driver1} tańczy między samochodami jak iluzjonista!",
    "📣 Ludzie na dachach wiwatują – to przejazd {driver2}!",
    "🕹️ {driver1} kontroluje każdy ruch jakby prowadził dron!",
    "🌉 {driver2} leci przez most bez mrugnięcia okiem!",
    "🚦 Czerwone światła? Dla {driver1} to tylko dekoracja!",
    "💢 {driver2} zaciska zęby i przyspiesza na zatłoczonej ulicy!",
    "🌈 {driver1} ślizga się przez deszczową alejkę – jak po lodzie!",
    "📍 {driver2} trzyma się środka pasa z chirurgiczną precyzją!",
    "🔒 {driver1} zamyka {driver2} między kontenerami – co za ruch!",
    "🫣 Ludzie cofają się na chodnik – {driver2} pędzi jak burza!",
    "🧩 {driver1} układa manewr z zegarmistrzowską dokładnością!",
    "🪤 {driver2} zwalnia, by zaskoczyć nagłym przyspieszeniem!",
    "🫧 {driver1} wślizguje się między ciężarówki jak cień!",
    "🪶 {driver2} prawie unosi się w powietrzu na wyboju!",
    "🪜 {driver1} wspina się po pozycjach mimo chaosu!",
    "🪙 {driver2} ryzykuje wszystko przy śliskim rondzie!",
    "🔮 {driver1} czyta ruchy rywala jak z książki!",
    "🧗 {driver2} wspina się po stawce jak po drabinie!",
    "⛓️ {driver1} nie odpuszcza – jedzie przy zderzaku!",
    "🚿 {driver2} przebija się przez mgłę dymu po poślizgu!",
    "📦 {driver1} unika kartonów na ulicy jak ninja!",
    "🎆 {driver2} błyszczy w świetle neonów i reflektorów!",
    "📡 {driver1} zna każdą uliczkę – jakby miał GPS w głowie!",
    "🛰️ {driver2} patrzy z góry – kontroluje wszystko z wyprzedzeniem!",
    "🔊 Ludzie na balkonach krzyczą imiona kierowców!",
    "🏙️ Uliczny labirynt staje się polem bitwy dla {driver1} i {driver2}!",
    "🧨 Kolejny drift {driver1} – tym razem tuż przy kiosku!",
    "🕰️ {driver2} jedzie z taką precyzją, jakby mierzył czas co do sekundy!",
    "🚫 {driver1} blokuje przejazd – totalna dominacja!",
    "🚹 Pieszy ledwo uskakuje – {driver2} z opanowaniem omija wszystko!",
    "🏚️ {driver1} przeciska się przez starą uliczkę między murami!",
    "🛠️ {driver2} wykorzystuje każdą nierówność do kontroli auta!",
    "🎇 {driver1} błyszczy jak gwiazda na trasie nocnego wyścigu!",
    "🌌 Nocne niebo nad miastem rozświetlają światła {driver2}!",
    "🌫️ {driver1} ginie na chwilę w dymie, by wrócić z impetem!",
    "💣 {driver2} odważnie wbija się między dwa busy!",
    "🪁 {driver1} sunie po trasie jak wiatr!",
    "🧃 {driver2} przepływa przez ruch jakby to był sok przez słomkę!",
    "🧊 {driver1} chłodny jak lód, nawet przy ryzykownym wyprzedzaniu!",
    "🔥 {driver2} nie gasi ognia – jedzie na limicie!",
    "🚨 Policja w tle, ale {driver1} skupia się tylko na trasie!",
    "🧨 Każdy zakręt to eksplozja stylu u {driver2}!",
    "🛣️ {driver1} zna każdy wybój, każdą dziurę – lokalny mistrz!",
    "🎲 {driver2} ryzykuje – albo wszystko, albo nic!",
    "🏗️ {driver1} skacze przez próg remontowy z gracją!",
    "🪚 {driver2} przecina powietrze jak ostrze!",
    "🌫️ {driver1} znika we mgle i wraca na czoło stawki!",
    "🏴‍☠️ {driver2} jedzie jak pirat uliczny – zero zasad!",
    "🔋 {driver1} wykorzystuje każdy procent mocy!",
    "🛸 {driver2} porusza się jak pojazd z innej planety!",
    "🚀 Beton, światła, adrenalina – {driver1} jest w swoim żywiole!",
    "🎤 Komentatorzy nie nadążają – {driver2} prze do przodu jak burza!",
    "🦺 {driver1} o milimetry mija ekipę robotników – nieprawdopodobne!",
    "🩶 {driver2} nie pokazuje emocji – pełna koncentracja!",
    "🌃 Miasto nie śpi – {driver1} też nie!",
    "🔦 Reflektory {driver2} przecinają noc jak miecze!",
    "🚔 Policyjne syreny gdzieś w tle, ale {driver1} skupiony na trasie!",
    "🚧 Remont nie zatrzymuje {driver2} – tylko przyspiesza tempo!",
    "🛞 {driver1} jedzie jakby znał ten asfalt od dziecka!",
    "🎈 {driver2} leci lekko przez próg jak balon z nitro!",
    "🛒 {driver1} omija wózki sklepowe jak zawodowiec!",
    "🚛 {driver2} mija ciężarówkę z milimetrowym marginesem!",
    "🎭 Emocje na twarzy {driver1} to mieszanka skupienia i szału!",
    "🧠 {driver2} analizuje trasę jak komputer wyścigowy!",
    "🫀 Serce bije szybciej – co za jazda {driver1}!",
    "🛣️ Betonowa dżungla – {driver2} króluje w niej bezapelacyjnie!",
    "💨 {driver1} śmiga przez ciemny zaułek jak błyskawica!",
    "🔥 {driver2} rozgrzewa asfalt pod kołami!",
    "🚧 {driver1} przejeżdża przez rozkopaną ulicę bez zwolnienia!",
    "⚡ {driver2} korzysta z każdego ułamka sekundy!",
    "🌀 {driver1} robi ciasny obrót między słupkami – co za kontrola!",
    "🛞 {driver2} traci przyczepność, ale od razu to koryguje!",
    "🎇 {driver1} mknie w świetle fajerwerków – magia nocnego miasta!",
    "🎢 {driver2} zalicza skok na wyboju – co za lot!",
    "🚀 {driver1} nabiera niesamowitej prędkości na prostej!",
    "👀 Przechodnie zatrzymują się – {driver2} jedzie jak szalony!",
    "🏙️ {driver1} przemyka pod wiaduktem z milimetrową precyzją!",
    "🎯 {driver2} celuje idealnie w wewnętrzną linię zakrętu!",
    "🧊 {driver1} nie pokazuje stresu – pełna kontrola!",
    "🚦 {driver2} ignoruje czerwone – liczy się tylko zwycięstwo!",
    "🎥 Kamery CCTV uchwyciły perfekcyjny manewr {driver1}!",
    "🎮 Jazda {driver2} wygląda jak replay z symulatora!",
    "🧩 {driver1} układa swój wyścig jak mistrz puzzli!",
    "🎤 Komentatorzy krzyczą – {driver2} wyprzedza w niewiarygodnym stylu!",
    "🧨 {driver1} zostawia za sobą dym i hałas!",
    "💢 {driver2} odpłaca pięknym za nadobne – nie odpuszcza ani metra!",
    "📈 {driver1} zyskuje pozycję mimo haosu wokół!",
    "📉 {driver2} musi uważać – za dużo ryzyka na mokrej nawierzchni!",
    "🧠 {driver1} podejmuje genialną decyzję w ułamku sekundy!",
    "🔁 {driver2} powtarza manewr, który wcześniej dał mu przewagę!",
    "🏁 Wyścig nabiera szaleńczego tempa – {driver1} nie zwalnia!",
    "🚗 {driver2} przemyka obok jadącego dostawczaka – minimalny margines!",
    "🛣️ {driver1} zna każdą kostkę brukową na tej trasie!",
    "📦 {driver2} przeskakuje przez rozrzucone pudełka – co za styl!",
    "🎇 Nocne światła odbijają się w karoserii {driver1} – widowiskowa jazda!",
    "🧗 {driver2} wspina się po stawce z nieprawdopodobną determinacją!",
    "🌪️ {driver1} zostawia za sobą tornado kurzu i gumy!",
    "🧃 {driver2} płynie po trasie jak po wodzie!",
    "💪 {driver1} nie pozwala rywalowi złapać oddechu!",
    "🎓 {driver2} pokazuje, jak jeżdżą weterani ulicznych bitew!",
    "🔧 {driver1} walczy z autem – i wygrywa!",
    "🛑 {driver2} zatrzymuje atak {driver1} w ostatnim momencie!",
    "🪄 {driver1} robi coś, co wydaje się niemożliwe!",
    "📣 Tłum na dachu centrum handlowego wiwatuje dla {driver2}!",
    "🪤 {driver1} podpuszcza przeciwnika do złego ruchu!",
    "🕹️ {driver2} steruje autem jakby grał na padzie – niesamowita precyzja!",
    "🛰️ {driver1} kontroluje sytuację z lotu ptaka – całkowita dominacja!",
    "🏗️ {driver2} przeciska się przez remontowany odcinek jak w labiryncie!",
    "🔮 {driver1} przewiduje każdy ruch {driver2} – czyta grę perfekcyjnie!",
    "🪶 {driver2} leci przez trasę jak piórko, mimo zakrętów!",
    "💨 {driver1} mija ściany budynków z zawrotną prędkością!",
    "🛠️ {driver2} wyciska maksimum z maszyny!",
    "🩶 {driver1} opanowany, skupiony, zabójczo skuteczny!",
    "🪜 {driver2} pięknie pnie się w górę tabeli!",
    "⛓️ {driver1} nie daje się zgubić – przyklejony do rywala!",
    "🎲 {driver2} podejmuje ryzyko – i opłaca się!",
    "🕰️ {driver1} perfekcyjnie zarządza czasem i odległością!",
    "🛸 {driver2} porusza się jak obiekt latający – lekko i zwinnie!",
    "🧠 {driver1} nie daje się ponieść emocjom – zimna kalkulacja!",
    "🌌 {driver2} przemyka przez nocne miasto jak kometa!",
    "🚿 {driver1} jedzie przez wodę jakby to był suchy asfalt!",
    "🌫️ {driver2} ginie na chwilę w dymie, ale wychodzi przed rywala!",
    "🎭 {driver1} pokazuje pokerową twarz, mimo ryzykownych manewrów!",
    "🪚 {driver2} tnie zakręty jak ostrze przecinające asfalt!",
    "🧊 {driver1} nie drgnął ani na milimetr – stalowe nerwy!",
    "🚧 {driver2} balansuje na granicy przepaści w wąskiej alejce!",
    "🔒 {driver1} zamyka przeciwnikowi wszystkie drogi ucieczki!",
    "🧩 {driver2} układa swój plan jazdy z zegarmistrzowską precyzją!",
    "🔊 Dźwięk silnika {driver1} odbija się od ścian budynków!",
    "🚹 Piesi dosłownie zamierają, gdy {driver2} mija ich o milimetry!",
    "🏴‍☠️ {driver1} łamie wszelkie zasady – ale jedzie jak król ulicy!",
    "🎤 Komentatorzy nie wierzą własnym oczom – {driver2} robi to znowu!",
    "💥 {driver1} unika kolizji z porzuconym wózkiem sklepowym!",
    "🎈 {driver2} przelatuje przez wyboj jakby był balonem z azotem!",
    "🏚️ {driver1} prześlizguje się między zdewastowanymi kamienicami!",
    "🌃 {driver2} wykorzystuje światła latarni do manewru idealnego!",
    "🚛 {driver1} omija ciężarówkę z niesamowitą gracją!",
    "💣 {driver2} wbija się w tempo jak pocisk!",
    "📡 {driver1} analizuje trasę z dokładnością GPS-a!",
    "🔦 {driver2} przecina ciemność reflektorami jak miecz świetlny!",
    "🧊 {driver1} balansuje na granicy poślizgu – ale jeszcze go trzyma!",
    "🚨 {driver2} przecina ulicę tuż przed radiowozem – bez strachu!",
    "🎆 {driver1} robi manewr w rytm muzyki miasta!",
    "🛒 {driver2} unika przeszkód jakby był w slalomie!",
    "🚹 Ludzie krzyczą, ale {driver1} widzi tylko trasę!",
    "🛞 {driver2} odbija się od krawężnika i wraca na linię jazdy!",
    "🛠️ {driver1} wyciska z auta wszystko, co możliwe!",
    "🔧 {driver2} nie daje po sobie poznać, że coś się psuje!",
    "🧨 {driver1} eksploduje z zakrętu na pełnym gazie!",
    "🎯 {driver2} trafia idealnie w punkt wejścia w uliczkę!",
    "💡 {driver1} reaguje szybciej niż zapala się światło!",
    "🚛 {driver2} ścina zakręt tuż obok wielkiego tira – perfekcyjny timing!",
    "🎢 {driver1} przejeżdża przez muldy jak na rollercoasterze!",
    "📍 {driver2} zna każdy metr tej dzielnicy!",
    "🛠️ {driver1} walczy nie tylko z rywalami, ale też z nawierzchnią!",
    "🚿 {driver2} przecina wodę jak łódź motorowa!",
    "🌪️ {driver1} kręci zakręt, zostawiając po sobie wir kurzu!",
    "🔊 {driver2} sprawia, że całe miasto słyszy jego silnik!",
    "🛸 {driver1} porusza się jakby nie dotykał asfaltu!",
    "🩶 {driver2} zachowuje zimną krew mimo jazdy centymetry od ściany!",
    "🌉 {driver1} przeskakuje przez próg jak po rampie!",
    "🛞 {driver2} odbija się na wyboju, ale ląduje stabilnie!",
    "🔋 {driver1} nie spuszcza nogi z gazu – jedzie na pełnej mocy!",
    "🚧 {driver1} wyprzedza w miejscu, gdzie nikt nie miałby odwagi!",
    "🧊 {driver2} wchodzi w zakręt jak po szynach – pełna kontrola!",
    "💨 {driver1} zostawia za sobą kurz i zawiedzionych przeciwników!",
    "🎯 {driver2} trafia w lukę między samochodami jak strzała do celu!",
    "🌀 {driver1} obraca tył auta tylko po to, by lepiej wejść w zakręt!",
    "🪞 {driver2} patrzy tylko w lusterka – ma wszystkich za sobą!",
    "🌪️ {driver1} przejeżdża przez krzyżówkę zostawiając za sobą chaos!",
    "🧠 {driver2} analizuje trasę w ułamku sekundy!",
    "📸 {driver1} robi show dla wszystkich kamer miejskich!",
    "🛣️ {driver2} zna każdy skrót – teraz to wykorzystuje!",
    "🪤 {driver1} zastawia pułapkę na rywala – i ten wpada!",
    "🎮 {driver2} porusza się jak z innej gry!",
    "🌌 {driver1} wpisuje się w nocne ulice jakby był ich częścią!",
    "🎢 {driver2} walczy z podskakującym autem jak z rodeo!",
    "📉 {driver1} traci kontrolę – ale wraca z jeszcze większą siłą!",
    "🧱 {driver2} prawie ociera się o ścianę – dosłownie centymetry!",
    "🧨 {driver1} przeciska się między barierkami jak przez igielne ucho!",
    "🎤 Widownia wyje z emocji, gdy {driver2} przegania {driver1}!",
    "💢 {driver1} pokazuje, że nie zamierza się poddać!",
    "🧃 {driver2} sunie przez mokrą nawierzchnię jak po maśle!",
    "🎆 {driver1} wykorzystuje wybuchy świateł jako osłonę!",
    "🚦 {driver2} ignoruje wszystko, co nie jest celem przed nim!",
    "🔮 {driver1} przewiduje, co zrobi przeciwnik – i kontruje!",
    "🎯 {driver2} nie traci nawet ułamka sekundy na zbędne ruchy!",
    "🧠 {driver1} prowadzi jak komputer – bezbłędnie!",
    "💨 {driver2} zostawia za sobą smugę światła – absolutna prędkość!",
    "🌃 {driver1} zlewa się z cieniami budynków – duch ulicy!",
    "🔦 {driver2} wyprzedza w tunelu – całkowicie w ciemno!",
    "🧊 {driver1} przejeżdża po śliskim bruku bez zawahania!",
    "📡 {driver2} wybiera trasę na podstawie najnowszych danych GPS!",
    "🛞 {driver1} balansuje na granicy przyczepności – i nie odpuszcza!",
    "🔧 {driver2} zna każdy dźwięk swojego silnika – i reaguje natychmiast!",
    "🎲 {driver1} ryzykuje i... zyskuje pozycję!",
    "📸 {driver2} pojawia się na kamerze z nowej perspektywy – lider!",
    "🪄 {driver1} manewruje jakby miał magię w rękach!",
    "🛑 {driver2} zmusza przeciwnika do gwałtownego hamowania – świetna taktyka!",
    "🌉 {driver1} przelatuje przez most na granicy przyczepności!",
    "🧱 {driver2} ucieka rywalowi pod samą ścianą – totalny brak miejsca!",
    "🌀 {driver1} driftem wyprzedza na wąskiej uliczce – nie do wiary!",
    "🎥 {driver2} wygląda jak główny bohater filmu akcji!",
    "🚛 {driver1} wykorzystuje cień ciężarówki do niespodziewanego ataku!",
    "💡 {driver2} jedzie szybciej niż odbijające się światła!",
    "🛠️ {driver1} ledwo trzyma auto w kupie – ale trzyma się trasy!",
    "🚦 {driver2} przemyka przez skrzyżowanie przy zapalającym się czerwonym!",
    "🧊 {driver1} jak zawsze spokojny – nawet w najbardziej ekstremalnej sytuacji!",
    "🎭 {driver2} zmienia styl jazdy jak aktor role – rywale są zdezorientowani!",
    "🪚 {driver1} ścina zakręty jakby miał laser pod maską!",
    "📦 {driver2} przelatuje nad rozrzuconymi przeszkodami jak nad rampą!",
    "🔒 {driver1} zamyka linie ataku przeciwnikowi – totalna blokada!",
    "🚷 {driver2} łamie każdą zasadę ruchu – ale nie sposób go złapać!",
    "🧠 {driver1} wykorzystuje każdy błysk, każdy cień, każdą szczelinę w trasie!",
    "🪞 {driver2} jedzie z głową odwróconą do tyłu – tak dobrze zna trasę!",
    "🌪️ {driver1} wiruje między pachołkami i barierami – perfekcyjna jazda!",
    "💬 Ludzie na forach już piszą: {driver2} to legenda tej nocy!",
    "🛣️ {driver1} wraca do głównej trasy z nowym impetem!",
    "🧩 {driver2} ustawia przeciwnika w mat – niczym w szachach!",
    "🎮 {driver1} manewruje jakby to była plansza, nie rzeczywistość!",
    "🚧 {driver2} wykorzystuje remont jako okazję do niespodziewanego manewru!",
    "🎆 {driver1} pędzi, gdy nad miastem wybuchają fajerwerki – symbol zwycięstwa?",
    "🕹️ {driver2} naciska każdy przycisk perfekcyjnie – steruje instynktem!",
    "🛞 {driver1} ledwo utrzymuje się na torze – ale jedzie dalej!",
    "🚿 {driver2} jak duch przemyka w strugach deszczu!",
    "🎤 Komentatorzy nie mogą nadążyć za {driver1}!",
    "🧊 {driver2} przemyka między autami jak zamrożony w czasie!",
    "🔮 {driver1} znów przewiduje ruch przeciwnika – jest wszędzie!",
    "🚗 {driver2} przeskakuje między liniami jakby je malował!",
    "🏙️ {driver1} dopasowuje się do rytmu miasta – prawdziwy artysta ulic!",
    "🛠️ {driver2} ciągle coś poprawia w aucie – ale jedzie perfekcyjnie!",
    "🧊 {driver1} nie poci się nawet w zakręcie przy 150 km/h!",
    "🚦 {driver2} wygrywa milisekundy przy każdym manewrze!",
    "🌉 {driver1} rzuca cień na rzekę, jadąc górą jak król tras!",
    "🧩 {driver2} korzysta z ułamków luk między pojazdami!",
    "🎥 {driver1} trafia na nagranie z drona – wygląda jak scena z filmu!",
    "🛞 {driver2} odbija się od krawężnika i wraca jakby nic się nie stało!",
    "🪞 {driver1} śledzi {driver2} tylko przez lusterko – jest tuż za nim!",
    "🎯 {driver2} wbija się idealnie w środek zakrętu!",
    "📦 {driver1} omija porozrzucane przeszkody jak tancerz!",
    "🛠️ {driver2} naprawił sytuację jednym ruchem kierownicy!",
    "💣 {driver1} eksploduje tempem na ostatnim odcinku!",
    "🎤 {driver2} robi show – to nie jest tylko jazda, to występ!",
    "🔧 {driver1} mimo usterki walczy jak lew!",
    "🚧 {driver2} śmiga przez zwężenie, zostawiając za sobą pył!",
    "🌪️ {driver1} jak tornado – zmienia wszystko, gdzie się pojawi!",
    "🛞 {driver2} co chwilę balansuje, ale nigdy nie wypada z rytmu!",
    "🎲 {driver1} zaryzykował i... opłaciło się z nawiązką!",
    "📍 {driver2} zna każdy skrót w tym mieście!",
    "🧠 {driver1} nie robi nic przypadkiem – to czysta strategia!",
    "🔮 {driver2} czuje trasę całym ciałem!",
    "🚀 {driver1} nie przestaje przyspieszać – to jakaś maszyna!",
    "🕹️ {driver2} przesuwa się po ulicach jak po torze wyścigowym!",
    "🌌 {driver1} zlewa się z neonami nocnego miasta – hipnotyzujące!",
    "🧱 {driver2} ociera się o mur i jedzie dalej jakby nigdy nic!",
    "🚧 {driver1} wykorzystuje każdą szczelinę między barierkami!",
    "💨 {driver2} wystrzelił z zakrętu niczym z katapulty!",
    "🌀 {driver1} driftuje po mokrej nawierzchni jak mistrz świata!",
    "🛞 {driver2} balansuje na krawędzi poślizgu – pełna kontrola!",
    "🎯 {driver1} idealnie trafia w punkt hamowania!",
    "🌃 {driver2} mknie przez oświetlone ulice, zostawiając za sobą świetlisty ślad!",
    "🧠 {driver1} podejmuje błyskawiczne decyzje – geniusz za kierownicą!",
    "🚦 {driver2} wykorzystuje każdy centymetr asfaltu do maksimum!",
    "🪞 {driver1} śledzi rywala w lusterku, gotowy do kontrataku!",
    "🎢 {driver2} przejeżdża przez wyboje niczym po gładkim torze!",
    "🧩 {driver1} ustawia auto jak pionek na szachownicy – perfekcyjna taktyka!",
    "🚿 {driver2} przecina kałuże, nie tracąc ani sekundy!",
    "🔧 {driver1} wyczuwa moment, by zaatakować z zaskoczenia!",
    "🎤 Komentatorzy nie mogą się nadziwić – {driver2} to prawdziwy uliczny mistrz!",
    "🏙️ {driver1} wykorzystuje miejskie przeszkody na swoją korzyść!",
    "🚀 {driver2} przyspiesza, jakby miał turbo w silniku!",
    "🧊 {driver1} zachowuje zimną krew w najbardziej krytycznych momentach!",
    "🛣️ {driver2} zna każdy zakręt jak własną kieszeń!",
    "💥 {driver1} unika kolizji w ostatniej chwili – co za refleks!",
    "🎯 {driver2} trafia idealnie w linię wyścigu – niesamowita precyzja!",
    "🧠 {driver1} analizuje ruchy rywala i dostosowuje strategię na bieżąco!",
    "🚧 {driver2} przeciska się przez wąskie przejście – mistrz manewrowania!",
    "🌪️ {driver1} zostawia za sobą wir kurzu i spalin!",
    "🛞 {driver2} nie pozwala sobie na żadne błędy – perfekcyjna jazda!",
    "🎮 {driver1} prowadzi auto jak zdalnie sterowany model – pełna kontrola!",
    "🏁 {driver2} zbliża się do mety z niesamowitą prędkością!",
    "🧩 {driver1} łączy elementy trasy w perfekcyjny układ!",
    "💨 {driver2} pędzi jak błyskawica przez miejskie ulice!",
    "🚦 {driver1} wykorzystuje każdy moment światła zielonego na swoją korzyść!",
    "🎢 {driver2} jedzie jak na rollercoasterze – z pełnym zaangażowaniem!",
    "🧊 {driver1} utrzymuje kontrolę na śliskiej nawierzchni jak profesjonalista!",
    "🔮 {driver2} przewiduje ruchy przeciwnika z niesamowitą dokładnością!",
    "🛠️ {driver1} walczy z awarią auta, ale nie zamierza się poddać!",
    "🎤 Tłum szaleje, gdy {driver2} wyprzedza na ostatnim zakręcie!",
    "🏙️ {driver1} wykorzystuje cienie budynków do ukrycia swoich manewrów!",
    "🚛 {driver2} unika kolizji z ciężarówką na wąskiej ulicy – co za refleks!",
    "🧠 {driver1} podejmuje ryzykowne decyzje, które się opłacają!",
    "🛞 {driver2} perfekcyjnie wykorzystuje przyczepność opon na zakrętach!",
    "🎯 {driver1} celuje idealnie w najlepszą linię przejazdu!",
    "🌀 {driver2} robi drift na granicy poślizgu – efektowny pokaz umiejętności!",
    "🚿 {driver1} przejeżdża przez kałuże, nie tracąc tempa!",
    "💥 {driver2} unika zderzenia z innym autem na milimetry!",
    "🎤 Komentatorzy są zachwyceni – {driver1} pokazuje klasę!",
    "🏁 {driver2} zbliża się do mety – walka o zwycięstwo trwa!",
    "🧩 {driver1} łączy każdy element trasy w jedną, płynną jazdę!",
    "🚧 {driver2} wykorzystuje każdy zakręt do maksymalnego przyspieszenia!",
    "🌪️ {driver1} zostawia za sobą smugi dymu i kurzu!",
    "🛞 {driver2} jedzie jak z mechanizmem precyzyjnym jak zegarek!",
    "🎮 {driver1} manewruje jakby grał na konsoli – perfekcyjna kontrola!",
    "🏙️ {driver2} doskonale zna każdy fragment miejskiej trasy!",
    "🧠 {driver1} wyprzedza z niesamowitą precyzją i pewnością siebie!",
    "🚦 {driver2} wykorzystuje każdy moment światła zielonego!",
    "🎢 {driver1} jedzie po nierównościach, zachowując pełną kontrolę!",
    "🧊 {driver2} balansuje na granicy poślizgu – pełna koncentracja!",
    "💨 {driver1} pędzi przez miasto, zostawiając konkurencję daleko w tyle!",
    "🎤 Publiczność szaleje, gdy {driver2} wykonuje perfekcyjny manewr!",
    "🏁 {driver1} zbliża się do mety z nieustępliwą determinacją!",
    "🛠️ {driver2} walczy z każdym zakrętem i każdy centymetr trasy jest jego!",
    "🎯 {driver1} nie traci ani sekundy na zbędne ruchy!",
    "🌀 {driver2} robi drift, który zapiera dech w piersiach!",
    "🚧 {driver1} przeciska się przez wąskie przejścia z niesamowitą precyzją!",
    "🌪️ {driver2} zostawia za sobą wir kurzu i spalin!",
    "🛞 {driver1} nie pozwala sobie na najmniejszy błąd!",
    "🎮 {driver2} kontroluje auto jak mistrz gry wyścigowej!",
    "🏙️ {driver1} idealnie wpisuje się w rytm miejskich ulic!",
    "🧠 {driver2} podejmuje błyskawiczne decyzje pod presją!",
    "🚦 {driver1} wykorzystuje każdy centymetr drogi do wyprzedzenia!",
    "🎢 {driver2} jedzie jak na rollercoasterze, zachowując pełną kontrolę!",
    "🧊 {driver1} utrzymuje przyczepność na mokrej nawierzchni jak profesjonalista!",
    "💥 {driver2} unika kolizji na milimetry – prawdziwy popis umiejętności!",
    "🎤 Komentatorzy nie mogą nadziwić się, jak {driver1} radzi sobie z presją!",
    "🏁 {driver2} zbliża się do mety – walka o zwycięstwo trwa do ostatniej chwili!",
    "🧩 {driver1} łączy każdy fragment trasy w perfekcyjną całość!",
    "🚧 {driver1} przeciska się między zaparkowanymi autami niczym cień!",
    "💨 {driver2} wyprzedza przeciwników z zawrotną prędkością!",
    "🌀 {driver1} driftuje perfekcyjnie na ostrym zakręcie!",
    "🛞 {driver2} balansuje na granicy poślizgu, ale nie traci kontroli!",
    "🎯 {driver1} wchodzi w zakręt z precyzją chirurga!",
    "🌃 {driver2} mknie po nocnych ulicach, zostawiając za sobą rozmyte światła!",
    "🧠 {driver1} podejmuje błyskawiczne decyzje – taktyka na najwyższym poziomie!",
    "🚦 {driver2} wykorzystuje każdy metr asfaltu, by wyprzedzić rywala!",
    "🪞 {driver1} patrzy w lusterka, analizując ruchy przeciwnika!",
    "🎢 {driver2} jedzie po nierównościach, zachowując doskonałą stabilność!",
    "🧩 {driver1} planuje każdy manewr z chirurgiczną precyzją!",
    "🚿 {driver2} przejeżdża przez kałuże, nie tracąc tempa!",
    "🔧 {driver1} doskonale wyczuwa moment, by zaatakować!",
    "🎤 Tłum szaleje, gdy {driver2} wyprzedza na ostatnim zakręcie!",
    "🏙️ {driver1} wykorzystuje miejskie przeszkody na swoją korzyść!",
    "🚀 {driver2} przyspiesza z nieprawdopodobną siłą!",
    "🧊 {driver1} zachowuje zimną krew nawet w najtrudniejszych momentach!",
    "🛣️ {driver2} zna każdy zakręt trasy na pamięć!",
    "💥 {driver1} unika kolizji na ostatnią chwilę – co za refleks!",
    "🎯 {driver2} trafia idealnie w linię przejazdu – niesamowita precyzja!",
    "🧠 {driver1} analizuje każdy ruch rywala i dopasowuje strategię!",
    "🚧 {driver2} przeciska się przez wąskie przejścia z mistrzowską precyzją!",
    "🌪️ {driver1} zostawia za sobą chmurę kurzu i spalin!",
    "🛞 {driver2} nie dopuszcza do najmniejszego błędu!",
    "🎮 {driver1} prowadzi auto jak mistrz symulatora wyścigowego!",
    "🏁 {driver2} zbliża się do mety z zawrotną prędkością!",
    "🧩 {driver1} łączy wszystkie elementy trasy w płynną jazdę!",
    "💨 {driver2} pędzi jak błyskawica przez ulice miasta!",
    "🚦 {driver1} wykorzystuje każdy moment zielonego światła!",
    "🎢 {driver2} jedzie jak na rollercoasterze, zachowując pełną kontrolę!",
    "🧊 {driver1} utrzymuje przyczepność na mokrej nawierzchni jak ekspert!",
    "🔮 {driver2} przewiduje ruchy przeciwnika z niezwykłą dokładnością!",
    "🛠️ {driver1} walczy z awarią, ale nie odpuszcza!",
    "🎤 Publiczność szaleje, gdy {driver2} wykonuje efektowny manewr!",
    "🏙️ {driver1} korzysta z cieni budynków, by zaskoczyć rywali!",
    "🚛 {driver2} unika kolizji z ciężarówką na wąskiej ulicy – fenomenalny refleks!",
    "🧠 {driver1} podejmuje ryzykowne decyzje, które przynoszą efekt!",
    "🛞 {driver2} perfekcyjnie wykorzystuje przyczepność opon na zakrętach!",
    "🎯 {driver1} celuje w najlepszą linię przejazdu i nie myli się!",
    "🌀 {driver2} driftuje na granicy poślizgu – czysta magia!",
    "🚿 {driver1} mknie przez kałuże, nie tracąc ani sekundy!",
    "💥 {driver2} unika zderzenia na milimetry – popis umiejętności!",
    "🎤 Komentatorzy są zachwyceni – {driver1} pokazuje klasę!",
    "🏁 {driver2} walczy do samej mety – to będzie pamiętny wyścig!",
    "🧩 {driver1} łączy każdy element trasy w perfekcyjną całość!",
    "🚧 {driver2} wykorzystuje każdy zakręt do maksimum!",
    "🌪️ {driver1} zostawia za sobą wir kurzu i spalin!",
    "🛞 {driver2} prowadzi auto jak precyzyjny mechanizm!",
    "🎮 {driver1} manewruje jak mistrz symulatora – pełna kontrola!",
    "🏙️ {driver2} doskonale zna każdy fragment trasy miejskiej!",
    "🧠 {driver1} wyprzedza rywali z niezwykłą precyzją!",
    "🚦 {driver2} wykorzystuje każdy moment zielonego światła!",
    "🎢 {driver1} jedzie po nierównościach, zachowując pełną stabilność!",
    "🧊 {driver2} balansuje na granicy poślizgu – pełna koncentracja!",
    "💨 {driver1} zostawia konkurencję daleko w tyle!",
    "🎤 Tłum szaleje, gdy {driver2} wykonuje perfekcyjny manewr!",
    "🏁 {driver1} zbliża się do mety z nieustępliwą determinacją!",
    "🛠️ {driver2} walczy z każdym zakrętem i nie oddaje pola!",
    "🎯 {driver1} nie traci ani sekundy na zbędne ruchy!",
    "🌀 {driver2} driftuje efektownie, wzbudzając podziw tłumu!",
    "🚧 {driver1} przeciska się przez wąskie przejścia z mistrzowską precyzją!",
    "🌪️ {driver2} zostawia za sobą smugi kurzu i spalin!",
    "🛞 {driver1} jedzie bezbłędnie, nie dopuszczając do pomyłek!",
    "🎮 {driver2} kontroluje auto jak mistrz symulatora wyścigowego!",
    "🏙️ {driver1} idealnie wpisuje się w rytm miejskich ulic!",
    "🧠 {driver2} podejmuje błyskawiczne decyzje pod presją!",
    "🚦 {driver1} wykorzystuje każdy centymetr drogi do wyprzedzenia!",
    "🎢 {driver2} jedzie jak na rollercoasterze, zachowując pełną kontrolę!",
    "🧊 {driver1} utrzymuje przyczepność na mokrej nawierzchni jak ekspert!",
    "💥 {driver2} unika kolizji na milimetry – prawdziwy popis umiejętności!",
    "🎤 Komentatorzy nie mogą nadziwić się, jak {driver1} radzi sobie z presją!",
    "🏁 {driver2} walczy o zwycięstwo do ostatnich metrów!",
    "🧩 {driver1} łączy każdy fragment trasy w perfekcyjną całość!",
    
]

#async def rozlicz_zaklady(channel, winner_id, dane):
    #if winner_id not in BETS:
        #return None

    #bets = BETS.pop(winner_id)
    #tekst = "**🎉 Rozliczenie zakładów:**\n"
    #for bettor_id, kwota in bets:
        #wygrana = kwota * 2
        #dane["gracze"][str(bettor_id)]["pieniadze"] += wygrana
        #user = channel.guild.get_member(bettor_id)
        #user_mention = user.mention if user else f"<@{bettor_id}>"
        #tekst += f"{user_mention} wygrał(a) {wygrana} zł z zakładu.\n"
    #return tekst

class JoinRaceButton(ui.View):
    def __init__(self, wpisowe, challenger_id, channel, dane):
        super().__init__(timeout=60)  # 60 sekund na dołączenie
        self.wpisowe = wpisowe
        self.challenger_id = challenger_id
        self.channel = channel
        self.dane = dane
        self.challenger_joined = False
        self.joiner_id = None

    @ui.button(label="Dołącz do wyścigu!", style=discord.ButtonStyle.green)
    async def join(self, interaction: Interaction, button: ui.Button):
        user_id = str(interaction.user.id)
        gracz = self.dane["gracze"].get(user_id)
        if not gracz or gracz["pieniadze"] < self.wpisowe:
            await interaction.response.send_message("❌ Nie masz wystarczająco pieniędzy, aby dołączyć.", ephemeral=True)
            return
        
        # Challenger automatycznie dołącza przy starcie, ale potwierdź jeśli to challenger:
        if interaction.user.id == self.challenger_id:
            if self.challenger_joined:
                await interaction.response.send_message("❌ Już jesteś w wyścigu.", ephemeral=True)
                return
            self.challenger_joined = True
            await interaction.response.send_message("✅ Dołączyłeś do wyścigu jako wyzywający.", ephemeral=True)
            return
        
        # Ktoś inny dołącza jako przeciwnik:
        if self.joiner_id:
            await interaction.response.send_message("❌ Wyścig już ma przeciwnika.", ephemeral=True)
            return

        if user_id == str(self.challenger_id):
            await interaction.response.send_message("❌ Nie możesz dołączyć do własnego wyścigu jako przeciwnik.", ephemeral=True)
            return

        self.joiner_id = interaction.user.id
        await interaction.response.send_message(f"✅ Dołączyłeś do wyścigu przeciwko <@{self.challenger_id}>!", ephemeral=False)

        # Po dołączeniu obu graczy — start wyścigu
        self.stop()  # Kończymy timeout i uruchamiamy wyścig


@bot.tree.command(name="wyscig", description="Hostuj wyścig 1v1 z wpisowym")
@app_commands.describe(wpisowe="Kwota wpisowego (minimum 0)")
async def wyscig(interaction: Interaction, wpisowe: int):
    global ACTIVE_RACE

    if wpisowe < 0:
        await interaction.response.send_message("❌ Wpisowe nie może być ujemne.", ephemeral=True)
        return

    dane = wczytaj_dane()
    user_id = str(interaction.user.id)
    gracz = dane["gracze"].get(user_id)

    if not gracz or not gracz.get("auto_prywatne"):
        await interaction.response.send_message("❌ Musisz mieć prywatne auto, aby zorganizować wyścig.", ephemeral=True)
        return

    if gracz["pieniadze"] < wpisowe:
        await interaction.response.send_message("❌ Nie masz wystarczająco pieniędzy na wpisowe.", ephemeral=True)
        return

    if ACTIVE_RACE is not None:
        await interaction.response.send_message("❌ Już trwa aktywny wyścig, poczekaj na jego zakończenie.", ephemeral=True)
        return

    ACTIVE_RACE = {
        "challenger_id": interaction.user.id,
        "wpisowe": wpisowe,
        "channel": interaction.channel,
        "dane": dane,
    }

    embed = Embed(
        title="🏁 Wyścig uliczny - nowe wyzwanie!",
        description=(
            f"Organizator: {interaction.user.mention}\n"
            f"Wpisowe: {wpisowe} zł\n\n"
            "Kliknij **Dołącz do wyścigu!**, aby wziąć udział.\n"
            "Musisz mieć prywatne auto i wystarczająco pieniędzy na wpisowe."
        ),
        color=Color.orange()
    )
    view = JoinRaceButton(wpisowe, interaction.user.id, interaction.channel, dane)

    await interaction.response.send_message(embed=embed, view=view)

    # Czekamy na dołączenie przeciwnika lub timeout
    timeout = await view.wait()
    if not view.joiner_id:
        ACTIVE_RACE = None
        await interaction.channel.send("❌ Nikt nie dołączył do wyścigu, anulowano.")
        return

    # Rozpoczynamy wyścig
    challenger_id = ACTIVE_RACE["challenger_id"]
    joiner_id = view.joiner_id
    wpisowe = ACTIVE_RACE["wpisowe"]
    dane = ACTIVE_RACE["dane"]
    channel = ACTIVE_RACE["channel"]

    # Sprawdź auta obu graczy:
    gracz1 = dane["gracze"].get(str(challenger_id))
    gracz2 = dane["gracze"].get(str(joiner_id))
    if not gracz1.get("auto_prywatne") or not gracz2.get("auto_prywatne"):
        await channel.send("❌ Jeden z graczy nie ma prywatnego auta, wyścig anulowany.")
        ACTIVE_RACE = None
        return

    if gracz1["pieniadze"] < wpisowe or gracz2["pieniadze"] < wpisowe:
        await channel.send("❌ Jeden z graczy nie ma wystarczająco pieniędzy na wpisowe, wyścig anulowany.")
        ACTIVE_RACE = None
        return

    # Odejmujemy wpisowe od obu:
    gracz1["pieniadze"] -= wpisowe
    gracz2["pieniadze"] -= wpisowe

    # Obliczamy moc auta + tuning
    def oblicz_moc(auto):
        bazowa = next((a["moc_bazowa"] for a in KATALOG_AUT if a["brand"] == auto["brand"] and a["model"] == auto["model"]), 0)
        bonus = sum(auto["tuning"].get(k, 0) * 5 for k in auto["tuning"])
        return bazowa + bonus

    moc1 = oblicz_moc(gracz1["auto_prywatne"])
    moc2 = oblicz_moc(gracz2["auto_prywatne"])

    embed = Embed(
        title="🏁 Wyścig uliczny - start!",
        description=f"{bot.get_user(challenger_id).mention} vs {bot.get_user(joiner_id).mention}\nStart za 3 sekundy...",
        color=Color.orange()
    )
    await channel.send(embed=embed)
    await asyncio.sleep(3)

    msg = await channel.send(embed=Embed(title="🏁 Wyścig trwa!", description="🔥 Ruszyli!", color=Color.blurple()))

    czas_wyscigu = random.randint(15, 30)
    for _ in range(czas_wyscigu):
        komentarz = random.choice(COMMENTARY_MESSAGES).format(
            driver1=bot.get_user(challenger_id).name,
            driver2=bot.get_user(joiner_id).name
        )
        await msg.edit(embed=Embed(title="🏁 Wyścig trwa!", description=komentarz, color=Color.blurple()))
        await asyncio.sleep(2)  # komentarze co 2 sekundy

    wynik1 = moc1 + random.randint(-20, 20)
    wynik2 = moc2 + random.randint(-20, 20)

    if wynik1 == wynik2:
        # remis - losujemy zwycięzcę
        winner_id = random.choice([challenger_id, joiner_id])
    else:
        winner_id = challenger_id if wynik1 > wynik2 else joiner_id

    suma = wpisowe * 2
    dane["gracze"][str(winner_id)]["pieniadze"] += suma

    # Tworzymy embed z wynikiem
    wynik_embed = Embed(
        title="🏁 Wyścig zakończony!",
        description=(
            f"Zwycięzca: {bot.get_user(winner_id).mention}\n"
            f"Wygrywa {suma} zł!\n\n"
        ),
        color=Color.green()
    )

    # Rozliczamy zakłady
    
    
@bot.tree.command(name="zaakceptuj_wyscig", description="Zaakceptuj zaproszenie na wyścig")
async def zaakceptuj_wyscig(interaction: Interaction):
    dane = wczytaj_dane()
    user_id = str(interaction.user.id)

    if interaction.user.id not in ACTIVE_RACES:
        await interaction.response.send_message("❌ Nie masz żadnego wyzwania.", ephemeral=True)
        return

    race = ACTIVE_RACES.pop(interaction.user.id)
    challenger_id = race["challenger"]
    wpisowe = race["fee"]

    gracz1 = dane["gracze"].get(str(challenger_id))
    gracz2 = dane["gracze"].get(user_id)

    auto1 = gracz1["auto_prywatne"]
    auto2 = gracz2["auto_prywatne"]

    # Odejmij wpisowe
    gracz1["pieniadze"] -= wpisowe
    gracz2["pieniadze"] -= wpisowe

    # Oblicz moc auta + tuning bonus
    def oblicz_moc(auto):
        bazowa = next((a["moc_bazowa"] for a in KATALOG_AUT if a["brand"] == auto["brand"] and a["model"] == auto["model"]), 0)
        bonus = sum(auto["tuning"].get(k, 0) * 5 for k in auto["tuning"])
        return bazowa + bonus

    moc1 = oblicz_moc(auto1)
    moc2 = oblicz_moc(auto2)

    await interaction.response.send_message(embed=Embed(
        title="🏁 Wyścig uliczny!",
        description=f"{bot.get_user(challenger_id).mention} vs {interaction.user.mention}\nStart za 3 sekundy...",
        color=Color.orange()
    ))
    await asyncio.sleep(3)

    msg = await interaction.followup.send(embed=Embed(title="🏁 Wyścig trwa!", description="🔥 Odliczanie zakończone, ruszyli!", color=Color.blurple()), wait=True)

    czas_wyscigu = random.randint(10, 20)
    for _ in range(czas_wyscigu):
        komentarz = random.choice(COMMENTARY_MESSAGES).format(driver1=bot.get_user(challenger_id).name, driver2=interaction.user.name)
        await msg.edit(embed=Embed(title="🏁 Wyścig trwa!", description=komentarz, color=Color.blurple()))
        await asyncio.sleep(2)

    wynik1 = moc1 + random.randint(-20, 20)
    wynik2 = moc2 + random.randint(-20, 20)

    winner_id = challenger_id if wynik1 > wynik2 else interaction.user.id
    winner_name = bot.get_user(winner_id).mention
    suma = wpisowe * 2

    dane["gracze"][str(winner_id)]["pieniadze"] += suma
    if BETS.get(winner_id):
        for uid, kwota in BETS[winner_id]:
            dane["gracze"][str(uid)]["pieniadze"] += kwota * 2
        del BETS[winner_id]

    zapisz_dane(dane)

    await msg.edit(embed=Embed(
        title="🏁 Wyścig zakończony!",
        description=f"Zwycięzca: {winner_name}\nWygrywa {suma} zł!",
        color=Color.green()
    ))


@bot.event
async def on_message(message):
        if message.author.bot:
            return

        logging.info(f"✉️ Wiadomość od {message.author}: {message.content}")

        await bot.process_commands(message)


    
# keep_alive()

# Uruchomienie bota
bot.run(TOKEN)
