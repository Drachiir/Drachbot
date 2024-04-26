import random
import string
import json
from PIL import Image
import discord
from discord import app_commands

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

def id_generator(size=10, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

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
    send_amount = 0
    for x in send:
        if "Upgrade" in x:
            continue
        send_amount += mercs.get(x)[0]
    return send_amount

def calc_leak(leak, wave):
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
