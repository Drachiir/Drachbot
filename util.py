import random
import string
import json
from difflib import SequenceMatcher
from PIL import Image
import discord
from discord import app_commands

def random_color():
    return random.randrange(0, 2 ** 24)

with open('Files/json/const.json', 'r') as f:
    const_file = json.load(f)
    f.close()

with open("Files/json/slang.json", "r") as slang_file:
    slang = json.load(slang_file)
    slang_file.close()

mercs = const_file.get("mercs")
creep_values = const_file.get("creep_values")
wave_values = const_file.get("wave_values")
rank_emotes = const_file.get("rank_emotes")
wave_emotes = const_file.get("wave_emotes")
current_season = const_file.get("current_patches")
current_minelo = const_file.get("current_minelo")

mm_list = ['LockIn', 'Greed', 'Redraw', 'Yolo', 'Fiesta', 'CashOut', 'Castle', 'Cartel', 'Chaos', 'Champion', 'DoubleLockIn', 'Kingsguard', 'Megamind']
mm_choices = []
for mm in mm_list:
    mm_choices.append(discord.app_commands.Choice(name=mm, value=mm))

def human_format(num):
    num = float('{:.3g}'.format(num))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])

async def unit_autocomplete(interaction: discord.Interaction, interaction_input):
    if interaction.command.name == "openstats":
        max_cost = 270
    else:
        max_cost = 1337
    unit_list = []
    with open('Files/json/units.json', 'r') as f:
        units_json = json.load(f)
    for u_js in units_json:
        if u_js["totalValue"] != '':
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

def get_ranked_emote(rank):
    rank_emote = ""
    for emote in rank_emotes:
        if rank >= rank_emotes[emote][0]:
            rank_emote = rank_emotes[emote][1]
    return rank_emote

def get_icons_image(type, name):
    match type:
        case "avatar":
            if name == "icons/DefaultAvatar.png":
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
            if image_path == "Files/icons/PriestessOfTheAbyss.png":
                image_path = "Files/icons/PriestessoftheAbyss.png"
            if image_path == "Files/icons/PackRat(footprints).png":
                image_path = "Files/icons/PackRatNest.png"
        case "icon_send":
            image_path = 'Files/icons/' + name + ".png"
            if image_path == "Files/icons/PresstheAttack.png":
                image_path = "Files/icons/PressTheAttack.png"
        case "legion":
            image_path = 'Files/icons/Items/' + name.replace(" ", "") + ".png"
        case _:
            image_path = "Files/icons/Granddaddy.png"
    return Image.open(open(image_path, "rb"))

def count_mythium(send):
    if type(send) != type(list()):
        if send == "":
            send = []
        else:
            send = send.split("!")
    send_amount = 0
    for x in send:
        if "Upgrade" in x:
            continue
        send_amount += mercs.get(x)[0]
    return send_amount

def calc_leak(leak, wave):
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
        else:
            leak_amount += mercs.get(x)[1]
    return round(leak_amount / wave_total * 100, 1)

def im_has_alpha(img_arr):
    h,w,c = img_arr.shape
    return True if c ==4 else False
