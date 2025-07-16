import platform
import random
import string
import json
import traceback
from difflib import SequenceMatcher
from PIL import Image
import discord
from discord import app_commands
import difflib
from datetime import datetime, time, timezone, timedelta
import requests
import os
import legion_api


def random_color():
    return random.randrange(0, 2 ** 24)

with open('Files/json/const.json', 'r') as f:
    const_file = json.load(f)
    f.close()

with open("Files/json/slang.json", "r") as slang_file:
    slang = json.load(slang_file)
    slang_file.close()

with open('Files/json/Secrets.json') as f:
    secret_file = json.load(f)
    f.close()

# task_times2 = datetime.time(datetime.now(timezone.utc)+timedelta(seconds=5))
# task_times3 = datetime.time(datetime.now(timezone.utc)+timedelta(minutes=10))
# task_times4 = datetime.time(datetime.now(timezone.utc)+timedelta(minutes=15))

task_times2=[
    time(hour=4, minute=45, second=0, tzinfo=timezone.utc),
    time(hour=10, minute=45, second=0, tzinfo=timezone.utc),
    time(hour=16, minute=45, second=0, tzinfo=timezone.utc),
    time(hour=22, minute=45, second=0, tzinfo=timezone.utc)
]

task_times3=[
    time(hour=4, minute=50, second=0, tzinfo=timezone.utc),
    time(hour=10, minute=50, second=0, tzinfo=timezone.utc),
    time(hour=16, minute=50, second=0, tzinfo=timezone.utc),
    time(hour=22, minute=50, second=0, tzinfo=timezone.utc)
]

task_times4=[
    time(hour=4, minute=55, second=0, tzinfo=timezone.utc),
    time(hour=10, minute=55, second=0, tzinfo=timezone.utc),
    time(hour=16, minute=55, second=0, tzinfo=timezone.utc),
    time(hour=22, minute=55, second=0, tzinfo=timezone.utc)
]

if platform.system() == "Linux":
    shared_folder_livegames = "/shared/livegames/"
    shared_folder_livegames1v1 = "/shared/livegames1v1/"
    shared_folder = "/shared/Images/"
    shared2_folder = "/shared2/"
else:
    shared_folder_livegames = "shared/livegames/"
    shared_folder_livegames1v1 = "shared/livegames1v1/"
    shared_folder = "shared/Images/"
    shared2_folder = "shared2/"

#0 = Current Patches, 1 = min elo, 2 = Ltdle min elo, 3 = Website data patch, 4 = Twitch noti ping threshold elo

def get_current_patches(only_current = False, player_patches = False):
    with open(f"{shared2_folder}currents.txt", 'r') as f:
        patches = f.readlines()
    if player_patches:
        return patches[5].replace("\n", "")
    if only_current:
        #return ["12.05", "12.04", "12.03", "12.02", "12.01", "12.00", "11.11", "11.10", "11.09", "11.08" ,"11.07", "11.06", "11.05", "11.04", "11.03", "11.02", "11.01", "11.00"]
        return patches[3].replace("\n", "").split(",")
    else:
        return patches[0].replace("\n", "")

def get_current_minelo(twitch = False):
    with open(f"{shared2_folder}currents.txt", 'r') as f:
        patches = f.readlines()
    if twitch:
        return int(patches[4].replace("\n", ""))
    else:
        return int(patches[1].replace("\n", ""))

def get_current_ltdle_minelo():
    with open(f"{shared2_folder}currents.txt", 'r') as f:
        patches = f.readlines()
    return int(patches[2].replace("\n", ""))

DEBUG = secret_file["debug"]
website_elos = [1600, 1800, 2000, 2200, 2400, 2600, 2800]
incmercs = const_file.get("incmercs")
powermercs = const_file.get("powermercs")
creep_values = const_file.get("creep_values")
wave_values = const_file.get("wave_values")
rank_emotes = const_file.get("rank_emotes")
wave_emotes = const_file.get("wave_emotes")
mm_emotes = const_file.get("mm_emotes")

aura_spells = ["hero", "magician", "vampire"]
buff_spells = ["hero", "magician", "vampire", "divine blessing", "glacial touch", "guardian angel", "protector", "pulverizer", "sorcerer", "titan", "villain", "executioner"]
mm_list = ['LockIn', 'Greed', 'Redraw', 'Yolo', 'Fiesta', 'CashOut', 'Castle', 'Cartel', 'Chaos', 'Champion', 'DoubleLockIn', 'Kingsguard', 'Saboteur', 'Stash', 'Scrapper', 'Megamind']
mm_choices = []
for mm in mm_list:
    mm_choices.append(discord.app_commands.Choice(name=mm, value=mm))

def zoom_at(img, x, y, zoom):
    w, h = img.size
    if zoom < 1:
        zoom = 1
    zoom2 = zoom * 2
    img = img.crop((x - w / zoom2, y - h / zoom2,
                    x + w / zoom2, y + h / zoom2))
    return img.resize((w, h), Image.LANCZOS)

def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

async def unit_autocomplete(interaction: discord.Interaction, interaction_input):
    unit_list = []
    if interaction.command.name == "openstats":
        max_cost = 270
        unit_list.append('pack rat nest')
        unit_list.append('worker')
    else:
        max_cost = 1337
    with open('Files/json/units.json', 'r') as f:
        units_json = json.load(f)
    for u_js in units_json:
        if (u_js["totalValue"] != '') and u_js["isEnabled"]:
            if u_js["unitId"] and int(u_js["totalValue"]) > 0 and int(u_js["totalValue"]) <= max_cost:
                string = u_js["unitId"]
                string = string.replace('_', ' ')
                string = string.replace(' unit id', '')
                unit_list.append(string)
    return [
        app_commands.Choice(name=u, value=u)
        for u in unit_list if interaction_input.lower() in u.lower()
    ][:25]

async def spell_autocomplete(interaction: discord.Interaction, interaction_input):
    spell_list = []
    with open('Files/json/spells.json', 'r') as f:
        spells_json = json.load(f)
    for s_js in spells_json:
        string = s_js["_id"]
        string = string.replace('_powerup_id', '')
        string = string.replace('_spell_damage', '')
        string = string.replace("_", " ")
        spell_list.append(string)
    spell_list.append("taxed allowance")
    return [
        app_commands.Choice(name=u, value=u)
        for u in spell_list if interaction_input.lower() in u.lower()
    ][:25]

def get_unit_stacks_value(unit, stacks, wave10):
    units_with_stacks = {"sakura_unit_id": 15, "kingpin_unit_id": 1.5, "hydra_unit_id": -72.5, "nekomata_unit_id": 30, "orchid_unit_id": 5, "infiltrator_unit_id": 1, "peewee_unit_id": 5, "veteran_unit_id": 20}
    if wave10 > 9: units_with_stacks["sakura_unit_id"] = 30
    try:
        return round(units_with_stacks[unit] * stacks)
    except Exception:
        return 0

def id_generator(size=10, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def division_by_zero(n, d):
    return n / d if d else 0

def get_ranked_emote(rank):
    rank_emote = ""
    for emote in rank_emotes:
        if rank >= rank_emotes[emote][0]:
            rank_emote = rank_emotes[emote][1]
    return rank_emote

def get_icons_image(type, name):
    fallback_path = "Files/icons/Caution.png"
    if name == "none":
        return Image.open(open(fallback_path, "rb"))
    match type:
        case "avatar":
            if name == "icons/DefaultAvatar.png" or not name:
                name = "Icons/DefaultAvatar.png"
            name = name.split("Icons/")
            image_path = 'Files/icons/' + name[1]
            if image_path == "Files/icons/PriestessOfTheAbyss.png":
                image_path = "Files/icons/PriestessoftheAbyss.png"
        case "icon":
            if "_" in name:
                name = name.split("_")
                new_name = ""
                for icon_string in name:
                    new_name += icon_string.capitalize()
            elif " " in name:
                name = name.split(" ")
                new_name = ""
                for icon_string in name:
                    new_name += icon_string.capitalize()
            else:
                new_name = name.capitalize()
            image_path = 'Files/icons/' + new_name + ".png"
            if image_path == "Files/icons/None.png":
                image_path = "Files/icons/Granddaddy.png"
            if image_path == "Files/icons/Aps.png":
                image_path = "Files/icons/APS.png"
            if image_path == "Files/icons/HellRaiserBuffed.png":
                image_path = "Files/icons/HellRaiser.png"
            if image_path == "Files/icons/Mps.png":
                image_path = "Files/icons/MPS.png"
            if image_path == "Files/icons/Skyfish.png":
                image_path = "Files/icons/MetalDragon.png"
            if image_path == "Files/icons/PriestessOfTheAbyss.png":
                image_path = "Files/icons/PriestessoftheAbyss.png"
            if image_path == "Files/icons/PackRat(footprints).png":
                image_path = "Files/icons/PackRatNest.png"
        case "splashes":
            if "_" in name:
                name = name.split("_")
                new_name = ""
                for icon_string in name:
                    new_name += icon_string.capitalize()
            elif " " in name:
                name = name.split(" ")
                new_name = ""
                for icon_string in name:
                    new_name += icon_string.capitalize()
            else:
                new_name = name.capitalize()
            image_path = 'Files/splashes/' + new_name + ".png"
            if image_path == "Files/splashes/None.png":
                image_path = "Files/splashes/Granddaddy.png"
            if image_path == "Files/splashes/Aps.png":
                image_path = "Files/splashes/APS.png"
            if image_path == "Files/splashes/HellRaiserBuffed.png":
                image_path = "Files/splashes/HellRaiser.png"
            if image_path == "Files/splashes/Mps.png":
                image_path = "Files/splashes/MPS.png"
            if image_path == "Files/icons/Skyfish.png":
                image_path = "Files/icons/MetalDragon.png"
            if image_path == "Files/icons/Octopus.png":
                image_path = "Files/icons/Quadrapus.png"
            if image_path == "Files/splashes/PackRat(footprints).png":
                image_path = "Files/splashes/PackRatNest.png"
            if image_path == "Files/splashes/ImpMercenary.png":
                image_path = "Files/splashes/Imp.png"
        case "icon_send":
            image_path = 'Files/icons/' + name + ".png"
            if image_path == "Files/icons/PresstheAttack.png":
                image_path = "Files/icons/PressTheAttack.png"
        case "legion":
            image_path = 'Files/icons/Items/' + name.replace(" ", "") + ".png"
        case _:
            image_path = "Files/icons/Granddaddy.png"
    try:
        image_url = f"https://cdn.legiontd2.com/{"/".join(image_path.split("/")[1:])}"
    except Exception:
        pass
    try:
        return Image.open(open(image_path, "rb"))
    except Exception:
        try:
            response = requests.get(image_url)
            response.raise_for_status()
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            with open(image_path, "wb") as f:
                f.write(response.content)
            return Image.open(open(image_path, "rb"))
        except Exception:
            traceback.print_exc()
            return Image.open(open(fallback_path, "rb"))

def validate_spell_input(spell):
    spell_list = []
    with open('Files/json/spells.json', 'r') as f:
        spells_json = json.load(f)
    for s_js in spells_json:
        string = s_js["_id"]
        string = string.replace('_powerup_id', '')
        string = string.replace('_spell_damage', '')
        string = string.replace("_", " ")
        spell_list.append(string)
    spell_list.append("taxed allowance")
    spell = spell.lower()
    if spell in slang:
        spell = slang.get(spell)
    if spell not in spell_list:
        close_matches = difflib.get_close_matches(spell, spell_list)
        if len(close_matches) > 0:
            return close_matches[0]
        else:
            return None
    else:
        return spell

def validate_unit_list_input(unit:list):
    unit_list = []
    with open('Files/json/units.json', 'r') as f:
        units_json = json.load(f)
    for u_js in units_json:
        if (u_js["totalValue"] != '') and u_js["isEnabled"]:
            if u_js["unitId"] and int(u_js["totalValue"]) > 0:
                string = u_js["unitId"]
                string = string.replace('_', ' ')
                string = string.replace(' unit id', '')
                unit_list.append(string)
    unit_list.append('pack rat nest')
    for i, unit_name in enumerate(unit):
        unit_name = unit_name.lower()
        unit[i] = unit_name
        if unit_name.startswith(" "):
            unit_name = unit_name[1:]
            unit[i] = unit_name
        if unit_name in slang:
            unit_name = slang.get(unit_name)
            unit[i] = unit_name
        if unit_name not in unit_list:
            close_matches = difflib.get_close_matches(unit_name, unit_list)
            if len(close_matches) > 0:
                unit[i] = close_matches[0]
            else:
                return unit_name + " unit not found."
    else:
        return unit

def get_inc_power_myth(send):
    income = 0
    power = 0
    for x in send:
        if not x:
            continue
        if "Upgrade" in x:
            continue
        if x in incmercs:
            income += incmercs.get(x)
        else:
            power += powermercs.get(x)
    return [income, power]

def count_mythium(send, seperate = False):
    if type(send) != type(list()):
        if send == "":
            send = []
        else:
            send = send.split("!")
    inc_amount = 0
    power_amount = 0
    for x in send:
        if "Upgrade" in x:
            continue
        if x in incmercs:
            inc_amount += incmercs.get(x)
        else:
            power_amount += powermercs.get(x)
    if seperate:
        return inc_amount, power_amount
    else:
        return inc_amount + power_amount
    
def calc_leak(leak, wave, return_gold = False):
    if type(leak) != type(list()):
        if leak == "":
            leak = []
        else:
            leak = leak.split("!")
    leak_amount = 0
    send_amount = 0
    wave_total = wave_values[wave]
    for x in leak:
        if x in creep_values:
            leak_amount += creep_values.get(x)[1]
        elif x in incmercs:
            leak_amount += incmercs.get(x) / 20 * 4
        elif x in powermercs:
            if x == "Imp":
                leak_amount += powermercs.get(x) / 20 * 3
            else:
                leak_amount += powermercs.get(x) / 20 * 6
    if return_gold:
        return leak_amount
    else:
        return round(leak_amount / wave_total * 100, 1)

def im_has_alpha(img_arr):
    h,w,c = img_arr.shape
    return True if c ==4 else False

def get_rank_name(elo):
    if elo >= 2800:
        rank_url = 'Legend'
    elif elo >= 2600:
        rank_url = 'Grandmaster'
    elif elo >= 2400:
        rank_url = 'SeniorMaster'
    elif elo >= 2200:
        rank_url = 'Master'
    elif elo >= 2000:
        rank_url = 'Expert'
    elif elo >= 1800:
        rank_url = 'Diamond'
    elif elo >= 1600:
        rank_url = 'Platinum'
    elif elo >= 1400:
        rank_url = 'Gold'
    elif elo >= 1200:
        rank_url = 'Silver'
    elif elo >= 1000:
        rank_url = 'Bronze'
    else:
        rank_url = 'Unranked'
    return rank_url

def validate_playername(playername):
    playerid = legion_api.getid(playername)
    if playerid == 0:
        raise RuntimeError('Player ' + playername + ' not found.')
    if playerid == 1:
        raise RuntimeError('API limit reached, you can still use "all" commands.')
    return playerid

def cleanup_version_string(version:str):
    return ".".join(version.replace("v", "").split(".")[:2])