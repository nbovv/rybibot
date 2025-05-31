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
    cena = auto["price"]
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


@bot.tree.command(name="katalog_aut", description="Wyświetl katalog dostępnych aut")
async def katalog_aut(interaction: discord.Interaction):
    embed = discord.Embed(
        title="📋 Katalog dostępnych aut",
        description="Wybierz numer auta, aby je kupić komendą `/kup_auto <numer>`",
        color=discord.Color.blue()
    )

    for idx, auto in enumerate(KATALOG_AUT, start=1):
        embed.add_field(
            name=f"{idx}. {auto['brand']} {auto['model']}",
            value=f"💰 Cena: {auto['price']} zł",
            inline=False
        )

    await interaction.response.send_message(embed=embed, ephemeral=True)

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

@bot.tree.command(name="salon", description="Wyświetl swój salon samochodowy")
async def salon(interaction: discord.Interaction):
    user_id = str(interaction.user.id)
    dane = wczytaj_dane()

    if user_id not in dane["salony"] or user_id not in dane["gracze"]:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Błąd",
                description="Nie masz jeszcze salonu. Użyj `/stworz`, aby go założyć.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
        return

    salon = dane["salony"][user_id]
    gracz = dane["gracze"][user_id]

    auta = salon["auta"]
    if auta:
        auta_lista = "\n".join([f"{i+1}. {a['brand']} {a['model']}" for i, a in enumerate(auta)])
    else:
        auta_lista = "Brak aut w salonie."

    embed = discord.Embed(
        title=f"🚗 {salon['nazwa']}",
        color=discord.Color.blue()
    )
    embed.add_field(name="💰 Saldo", value=f"{gracz['pieniadze']} zł", inline=False)
    embed.add_field(name="📦 Wartość salonu", value=f"{salon['wartosc']} zł", inline=False)
    embed.add_field(name="🚘 Auta", value=auta_lista, inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.event
async def on_message(message):
        if message.author.bot:
            return

        logging.info(f"✉️ Wiadomość od {message.author}: {message.content}")

        await bot.process_commands(message)


    
# keep_alive()

# Uruchomienie bota
bot.run(TOKEN)
