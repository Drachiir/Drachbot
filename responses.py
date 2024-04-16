import io
import shutil
import requests
import json
from collections import Counter
import pathlib
from pathlib import Path
import datetime
from datetime import datetime, timezone
import traceback
import os
import os.path
import glob
import re
import time
import bot
import PIL
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import numpy as np
import math
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import csv
import asyncio
import concurrent.futures
import functools
import string
import random
import time
import difflib
import json_to_csv
import discord
from discord import utils
import discord_timestamps
from discord_timestamps import TimestampType

with open('Files/Secrets.json') as f:
    secret_file = json.load(f)
    f.close()

header = {'x-api-key': secret_file.get('apikey')}

site = "https://overlay.drachbot.site/Images/"

shared_folder = "/shared/Images/"

mercs = {"Snail": (20, 6), "Giant Snail": (20, 6), "Robo": (40, 10), "Lizard": (40, 12), "Dragon Turtle": (40, 12), "Brute": (60, 15), "Fiend": (60, 18), "Dino": (80, 24),
         "Hermit": (80, 20), "Cannoneer": (100, 30), "Imp": (100, 13), "Safety Mole": (120, 30), "Drake": (120, 36), "Pack Leader": (160, 40),
         "Mimic": (160, 40), "Witch": (200, 50), "Ogre": (200, 50), "Ghost Knight": (240, 60), "Four Eyes": (240, 60), "Centaur": (280, 70),
         "Shaman": (320, 80), "Siege Ram": (320, 80), "Needler": (360, 90), "Kraken": (400, 100), "Froggo": (0, 3)}

creep_values = {"Crab": (72, 6), "Wale": (84, 7), "Hopper": (90, 5), "Flying Chicken": (96, 8), "Scorpion": (108, 9), "Scorpion King": (108, 36),
                "Rocko": (114, 19), "Sludge": (120, 10), "Blob": (120, 2), "Kobra": (132, 11), "Carapace": (144, 12), "Granddaddy": (150, 63),
                "Quill Shooter": (156, 13), "Mantis": (168, 14), "Drill Golem": (180, 30), "Killer Slug": (192, 16), "Quadrapus": (204, 17),
                "Giant Quadrapus": (204, 68), "Cardinal": (216, 12), "Metal Dragon": (228, 19), "Wale Chief": (252, 42), "Dire Toad": (276, 23),
                "Maccabeus": (300, 126), "Legion Lord": (360, 30), "Legion King": (360, 120)}

wave_values = (72,84,90,96,108,114,120,132,144,150,156,168,180,192,204,216,228,252,276,300,360)

rank_emotes = {"bronze": [1000,"<:Bronze:1217999684484862057>"], "silver": [1200,"<:Silver:1217999706555158631>"], "gold": [1400,"<:Gold:1217999690369335407>"],
               "plat": [1600,"<:Platinum:1217999701337571379>"], "dia": [1800,"<:Diamond:1217999686888325150>"], "ruby": [2000,"<:Expert:1217999688494747718>"],
               "purple": [2200,"<:Master:1217999699114590248>"], "sm": [2400,"<:SeniorMaster:1217999704349081701>"], "gm": [2600,"<:Grandmaster:1217999691883741224>"],
               "legend": [2800, "<:Legend:1217999693234176050>"]}

wave_emotes = {"wave1": "<:Wave1:1228044855079600299>", "wave10": "<:Wave10:1228045034792681526>", "wave11": "<:Wave11:1228044870082625698>",
            "wave12": "<:Wave12:1228045036265013288>", "wave13": "<:Wave13:1228044874276671559>", "wave14": "<:Wave14:1228045037368115240>",
            "wave15": "<:Wave15:1228044877795688459>", "wave16": "<:Wave16:1228044879750369280>", "wave17": "<:Wave17:1228045038509097000>",
            "wave18": "<:Wave18:1228044883562856530>", "wave19": "<:Wave19:1228045039930839101>", "wave2": "<:Wave2:1228044857059315825>",
            "wave20": "<:Wave20:1228044887195254784>", "wave21": "<:Wave21:1228045041998495774>", "wave3": "<:Wave3:1228044858644500490>",
            "wave4": "<:Wave4:1228044860041199717>", "wave5": "<:Wave5:1228044861500948480>", "wave6": "<:Wave6:1228044862679678997>",
            "wave7": "<:Wave7:1228044864126717973>", "wave8": "<:Wave8:1228044865468764280>", "wave9": "<:Wave9:1228044866764673054>"}

with open("Files/slang.json", "r") as slang_file:
    slang = json.load(slang_file)
    slang_file.close()

def id_generator(size=10, chars=string.ascii_uppercase + string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def api_call_logger(request_type):
    try:
        with open("Files/api_calls.json", "r") as file:
            dict = json.load(file)
        date = datetime.now()
        if "next_reset" not in dict:
            dict["next_reset"] = (date + timedelta(days=1)).strftime("%m/%d/%Y")
        elif datetime.strptime(dict["next_reset"], "%m/%d/%Y") < datetime.now():
            dict = {"next_reset": (date + timedelta(days=1)).strftime("%m/%d/%Y")}
        if request_type not in dict:
            dict[request_type] = 1
        else:
            dict[request_type] += 1
        with open("Files/api_calls.json", "w") as file:
            json.dump(dict, file)
    except Exception:
        traceback.print_exc()

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
                for string in name:
                    new_name += string.capitalize()
            elif " " in name:
                name = name.split(" ")
                new_name = ""
                for string in name:
                    new_name += string.capitalize()
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

def stream_overlay(playername, stream_started_at="", elo_change=0, update = False):
    if not os.path.isfile("sessions/session_" + playername + ".json"):
        playerid = apicall_getid(playername)
        stats = apicall_getstats(playerid)
        initial_elo = stats["overallElo"]
        current_elo = stats["overallElo"]
        initial_wins = stats["rankedWinsThisSeason"]
        current_wins = stats["rankedWinsThisSeason"]
        initial_losses = stats["rankedLossesThisSeason"]
        current_losses = stats["rankedLossesThisSeason"]
        with open("sessions/session_" + playername + ".json", "w") as f:
            dict = {"started_at": stream_started_at, "int_elo": initial_elo, "current_elo": current_elo, "int_wins": initial_wins, "current_wins": current_wins, "int_losses": initial_losses, "current_losses": current_losses}
            json.dump(dict, f, default=str)
    else:
        with open("sessions/session_" + playername + ".json", "r") as f:
            dict = json.load(f)
            initial_elo = dict["int_elo"]
            initial_wins = dict["int_wins"]
            initial_losses = dict["int_losses"]
            if update == True:
                playerid = apicall_getid(playername)
                stats = apicall_getstats(playerid)
                current_elo = stats["overallElo"]
                current_wins = stats["rankedWinsThisSeason"]
                current_losses = stats["rankedLossesThisSeason"]
            else:
                current_elo = dict["current_elo"]+elo_change
                if elo_change > 0:
                    current_wins = dict["current_wins"]+1
                else:
                    current_wins = dict["current_wins"]
                if elo_change < 0:
                    current_losses = dict["current_losses"] + 1
                else:
                    current_losses = dict["current_losses"]
        with open("sessions/session_" + playername + ".json", "w") as f:
            dict = {"started_at": dict["started_at"], "int_elo": initial_elo, "current_elo": current_elo, "int_wins": initial_wins, "current_wins": current_wins, "int_losses": initial_losses, "current_losses": current_losses}
            json.dump(dict, f, default=str)
    wins = current_wins-initial_wins
    losses = current_losses-initial_losses
    try:
        winrate = round(wins/(wins+losses)*100)
    except ZeroDivisionError:
        winrate = 0
    rgb = ""
    rgb2 = ""
    if winrate < 50:
        rgb = 'class="redText"'
    else:
        rgb = 'class="greenText"'
    elo_diff = current_elo-initial_elo
    if elo_diff >= 0:
        elo_str = "+"
        rgb2 = 'class="greenText"'
    else:
        elo_str = ""
        rgb2 = 'class="redText"'
    def get_rank_url(elo):
        if elo >= 2800:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Legend.png'
        elif elo >= 2600:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Grandmaster.png'
        elif elo >= 2400:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/SeniorMaster.png'
        elif elo >= 2200:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Master.png'
        elif elo >= 2000:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Expert.png'
        elif elo >= 1800:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Diamond.png'
        elif elo >= 1600:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Platinum.png'
        elif elo >= 1400:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Gold.png'
        elif elo >= 1200:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Silver.png'
        return rank_url
    html_file = """
    <!doctype html>
        <html>
        <head>
          <meta http-equiv="refresh" content="5">
          <link rel="preconnect" href="https://fonts.googleapis.com">
          <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
          <link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100;0,300;0,400;0,500;0,700;0,900;1,100;1,300;1,400;1,500;1,700;1,900&display=swap" rel="stylesheet">
        <style>
          .container {
            min-height: 0px;
            max-height: 120px;
            max-width: 700px;
            display: flex;
            flex-direction: right;
            align-items: center;
          }
          r {
            font-family: "Roboto", sans-serif;
            font-weight: 700;
            font-style: normal;
            font-size: 220%;
            padding-left: 10px;
            color: white;
            letter-spacing: 1px;
            text-shadow:
            /* Outline */
            -1px -1px 0 #000000,
            1px -1px 0 #000000,
            -1px 1px 0 #000000,
            1px 1px 0 #000000,
            -2px 0 0 #000000,
            2px 0 0 #000000,
            0 2px 0 #000000,
            0 -2px 0 #000000;
          }
          .redText
          {
            color:rgb(219, 0, 0);
          }
          .greenText
          {
            color:rgb(0, 153, 0);
          }
        </style>
        <title>"""+playername+"""</title>
        </head>
        <body>
        <div class="container">
              <r><b>Starting elo:</b></r>
              <img src="""+get_rank_url(initial_elo)+""">
              <r><b>"""+str(initial_elo)+"""</b></r>
            </div>
        <div class="container">
              <r><b>Current elo:&nbsp;</b></r>
              <img src="""+get_rank_url(current_elo)+""">
              <r><b>"""+str(current_elo)+"""</b></r><r """+rgb2+""" ><b>("""+elo_str+str(elo_diff)+""")</b></r>
            </div>
        <div class="container">
              <r><b>Win:"""+str(wins)+""",&thinsp;Lose:"""+str(losses)+""",&thinsp;Winrate:</b></r><r """+rgb+""" ><b>"""+str(winrate)+"""%</b></r>
            </div>
        </body>
    </html>"""
    with open('/shared/'+playername+'_output.html', "w") as f:
        f.write(html_file)
    return playername+'_output.html'

def create_image_stats(dict, games, playerid, avgelo, patch, mode, megamind = False, megamind_count = 0, transparency = False):
    if playerid != 'all' and 'nova cup' not in playerid:
        playername = apicall_getprofile(playerid)['playerName']
        avatar = apicall_getprofile(playerid)['avatarUrl']
    else:
        playername = playerid.capitalize()
    def calc_pr(dict, mm):
        if megamind: games2 = megamind_count
        else: games2 = games
        return str(round(dict[mm]['Count'] / games2 * 100, 1))
    def get_perf_score(dict2, key):
        new_dict = {}
        for xy in dict2[key]:
            if dict2[key][xy]['Wins'] / dict2[key][xy]['Count'] < dict2['Wins'] / dict2['Count']:
                continue
            new_dict[xy] = dict2[key][xy]['Wins'] / dict2[key][xy]['Count'] * (dict2[key][xy]['Count'] / dict2['Count'])
        newIndex = sorted(new_dict, key=lambda k: new_dict[k], reverse=True)
        return newIndex
    if transparency: config = ['RGBA', (0,0,0,0)]
    else: config = ['RGB', (49,51,56)]
    match mode:
        case "Mastermind":
            if megamind: im = PIL.Image.new(mode=config[0], size=(1380, 770), color=config[1])
            else: im = PIL.Image.new(mode=config[0], size=(1485, 770), color=config[1])
            keys = ['Games:', 'Winrate:', 'Pickrate', 'W on 10:', 'Best Open:', '', 'Games:', 'Winrate:', 'Playrate:','Best Spell:', '', 'Games:', 'Winrate:', 'Playrate:']
            dict_values = ["Opener", "Spell"]
            icon_type = "legion"
        case "Open":
            im = PIL.Image.new(mode=config[0], size=(1700, 975), color=config[1])
            keys = ['Games:', 'Winrate:', 'Playrate:', 'W on 4:', 'Best Add:', '', 'Games:', 'Winrate:', 'Playrate:', 'Best MMs:', '', 'Games:', 'Winrate:', 'Playrate:', 'Best Spell:', '', 'Games:', 'Winrate:', 'Playrate:']
            dict_values = ["OpenWith", "MMs", "Spells"]
            icon_type = "icon"
        case "Spell":
            im = PIL.Image.new(mode=config[0], size=(1700, 770), color=config[1])
            keys = ['Games:', 'Winrate:', 'Playrate:', 'W on 10:', 'Best Open:', '', 'Games:', 'Winrate:', 'Playrate:', 'Best MMs:', '', 'Games:', 'Winrate:', 'Playrate:']
            dict_values = ["Opener", "MMs"]
            icon_type = "icon"
        case "Unit":
            im = PIL.Image.new(mode=config[0], size=(1700, 930), color=config[1])
            keys = ['Games:', 'Winrate:', 'Playrate:', 'Best\nCombo:', '', 'Games:', 'Winrate:', 'Playrate:', 'Best MM:', '', 'Games:', 'Winrate:', 'Playrate:', 'Best Spell:', '', 'Games:', 'Winrate:', 'Playrate:']
            dict_values = ["ComboUnit", "MMs", "Spells"]
            icon_type = "icon"
    im2 = PIL.Image.new(mode="RGB", size=(88, 900), color=(25,25,25))
    I1 = ImageDraw.Draw(im)
    ttf = 'Files/RobotoCondensed-Regular.ttf'
    myFont_small = ImageFont.truetype(ttf, 20)
    myFont = ImageFont.truetype(ttf, 25)
    myFont_title = ImageFont.truetype(ttf, 30)
    if playername == 'All' or 'Nova cup' in playername:
        string = ''
    else:
        string = "'s"
        av_image = get_icons_image("avatar", avatar)
        gold_border = Image.open('Files/gold_64.png')
        if im_has_alpha(np.array(av_image)):
            im.paste(av_image, (24, 100), mask=av_image)
        else:
            im.paste(av_image, (24, 100))
        im.paste(gold_border, (24, 100), mask=gold_border)
    if megamind: I1.text((10, 15), str(playername)+string+" Megamind stats (From "+str(games)+" ranked games, Avg elo: "+str(avgelo)+")", font=myFont_title, stroke_width=2, stroke_fill=(0,0,0), fill=(255, 255, 255))
    else: I1.text((10, 15), str(playername) + string + " "+mode+" stats (From " + str(games) + " ranked games, Avg elo: " + str(avgelo) + ")", font=myFont_title, stroke_width=2,stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    I1.text((10, 55), 'Patches: ' + ', '.join(patch), font=myFont_small, stroke_width=2, stroke_fill=(0,0,0), fill=(255, 255, 255))
    x = 126
    y = 175
    offset = 45
    offset2 = 25
    offset3 = 0
    offset_counter = 4
    for i, dict_key in enumerate(dict):
        if dict[dict_key]["Count"] == 0 or i == 15:
            break
        im.paste(im2, (x - 12, 88))
        im.paste(get_icons_image(icon_type, dict_key), (x, 100))
        I1.text((x, y), str(dict[dict_key]['Count']), font=myFont, fill=(255, 255, 255))
        I1.text((x, y + offset), str(round(dict[dict_key]['Wins']/dict[dict_key]['Count'] * 100, 1)) + '%', font=myFont, fill=(255, 255, 255))
        I1.text((x, y + offset * 2), str(calc_pr(dict, dict_key)) + '%', font=myFont, fill=(255, 255, 255))
        try:
            I1.text((x, y + offset * 3), str(round(dict[dict_key]['Worker'] / dict[dict_key]['Count'], 1)), font=myFont, fill=(255, 255, 255))
        except KeyError: offset_counter = 3
        for val in dict_values:
            newIndex = get_perf_score(dict[dict_key], val)
            if newIndex:
                if newIndex[0] == "none":
                    try:
                        index = newIndex[1]
                    except IndexError:
                        index = newIndex[0]
                else:
                    index = newIndex[0]
                if val != "MMs": type = "icon"
                else: type = "legion"
                im.paste(get_icons_image(type, index), (x, y + offset3 + offset * offset_counter))
                I1.text((x, y + offset2 + offset * (offset_counter+1)), str(dict[dict_key][val][index]['Count']), font=myFont, fill=(255, 255, 255))
                I1.text((x, y + offset2 + offset * (offset_counter+2)), str(round(dict[dict_key][val][index]['Wins'] / dict[dict_key][val][index]['Count'] * 100, 1)) + '%', font=myFont, fill=(255, 255, 255))
                I1.text((x, y + offset2 + offset * (offset_counter+3)), str(round(dict[dict_key][val][index]['Count'] / dict[dict_key]['Count'] * 100, 1)) + '%', font=myFont, fill=(255, 255, 255))
            offset2 += 25
            offset3 += 25
            offset_counter += 4
        offset2 = 25
        offset3 = 0
        offset_counter = 4
        x += 106
    im3 = PIL.Image.new(mode="RGB", size=(x-38, 4), color=(169, 169, 169))
    for k in keys:
        I1.text((8, y), k, font=myFont, stroke_width=2, stroke_fill=(0,0,0), fill=(255, 255, 255))
        if k.startswith("Best") == False and (k != ''):
            im.paste(im3, (8, y + 30))
            y += offset
        else:
            y += offset-10
    image_id = id_generator()
    im.save(shared_folder + image_id + '.png')
    return site + image_id + '.png'

def create_image_stats_specific(dict, games, playerid, avgelo, patch, mode, specific_value, transparency = False):
    if playerid != 'all' and 'nova cup' not in playerid:
        playername = apicall_getprofile(playerid)['playerName']
        avatar = apicall_getprofile(playerid)['avatarUrl']
    else:
        playername = playerid.capitalize()
    if transparency:
        config = ['RGBA', (0, 0, 0, 0)]
    else:
        config = ['RGB', (49, 51, 56)]
    match mode:
        case "Mastermind":
            im = PIL.Image.new(mode=config[0], size=(1700, 545), color=config[1])
            keys = ['Open:', '', 'Games:', 'Winrate:', 'Playrate:', 'Spell:', '', 'Games:', 'Winrate:', 'Playrate:']
            dict_values = ["Opener", "Spell"]
            icon_type = "legion"
        case "Open":
            im = PIL.Image.new(mode=config[0], size=(1700, 745), color=config[1])
            keys = ['Adds:', '', 'Games:', 'Winrate:', 'Playrate:', 'MMs:','', 'Games:', 'Winrate:', 'Playrate:', 'Spell:','', 'Games:', 'Winrate:', 'Playrate:']
            dict_values = ["OpenWith", "MMs", "Spells"]
            icon_type = "icon"
        case "Spell":
            im = PIL.Image.new(mode=config[0], size=(1700, 545), color=config[1])
            keys = ['Open:', '', 'Games:', 'Winrate:', 'Playrate:', 'MMs:','', 'Games:', 'Winrate:', 'Playrate:']
            dict_values = ["Opener", "MMs"]
            icon_type = "icon"
        case "Unit":
            im = PIL.Image.new(mode=config[0], size=(1700, 745), color=config[1])
            keys = ['Combo:', '', 'Games:', 'Winrate:', 'Playrate:', 'MMs:', '', 'Games:', 'Winrate:', 'Playrate:', 'Spell:', '', 'Games:', 'Winrate:', 'Playrate:']
            dict_values = ["ComboUnit", "MMs", "Spells"]
            icon_type = "icon"
    im2 = PIL.Image.new(mode="RGB", size=(88, 205), color=(25, 25, 25))
    I1 = ImageDraw.Draw(im)
    ttf = 'Files/RobotoCondensed-Regular.ttf'
    myFont_small = ImageFont.truetype(ttf, 20)
    myFont = ImageFont.truetype(ttf, 25)
    myFont_title = ImageFont.truetype(ttf, 30)
    unit_name = ""
    if playername == 'All' or 'Nova cup' in playername:
        suffix = ''
    else:
        suffix = "'s"
    im.paste(get_icons_image(icon_type, specific_value), (10, 10))
    if dict[specific_value]["Count"] == 0:
        return "No " + specific_value + " games found."
    I1.text((82, 10), str(playername) + suffix + " " + specific_value.capitalize() + " stats (From " + str(games) + " ranked games, Avg elo: " + str(avgelo) + ")", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    I1.text((82, 55), 'Patches: ' + ', '.join(patch), font=myFont_small, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    try:
        I1.text((10, 80), "Games: " + str(dict[specific_value]["Count"]) + ", Wins: " + str(dict[specific_value]["Wins"]) + ", Losses: " + str(dict[specific_value]["Count"] - dict[specific_value]["Wins"]) + ", Winrate: " + str(round(dict[specific_value]["Wins"] / dict[specific_value]["Count"] * 100, 1)) + "%", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    except ZeroDivisionError:
        I1.text((10, 80), "Games: " + str(dict[specific_value]["Count"]) + ", Wins: " + str(dict[specific_value]["Wins"]) + ", Losses: " + str(dict[specific_value]["Count"] - dict[specific_value]["Wins"]) + ", Winrate: " + str(0) + "%", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    x = 126
    y = 130
    offset = 45
    offset2 = 25
    offset3 = 0
    offset_counter = 0
    max_x = []
    for i, val in enumerate(dict_values):
        newIndex = sorted(dict[specific_value][val], key=lambda k: int(dict[specific_value][val][k]["Count"]), reverse=True)
        for idx, val2 in enumerate(newIndex):
            if idx == 15: break
            im.paste(im2, (x - 12, y - 12 + offset3 + (offset * offset_counter)))
            if val != "MMs": type = "icon"
            else: type = "legion"
            im.paste(get_icons_image(type, val2), (x, y + offset3 + (offset * offset_counter)))
            I1.text((x, y + offset2 + offset * (offset_counter+1)), str(dict[specific_value][val][val2]['Count']), font=myFont, fill=(255, 255, 255))
            I1.text((x, y + offset2 + offset * (offset_counter+2)), str(round(dict[specific_value][val][val2]['Wins'] / dict[specific_value][val][val2]['Count'] * 100, 1)) + '%', font=myFont, fill=(255, 255, 255))
            I1.text((x, y + offset2 + offset * (offset_counter+3)), str(round(dict[specific_value][val][val2]['Count'] / dict[specific_value]['Count'] * 100, 1)) + '%', font=myFont, fill=(255, 255, 255))
            x += 106
        max_x.append(x)
        offset2 += 25
        offset3 += 25
        offset_counter += 4
        x = 126
    exclude = ["Open:", "Adds:", "MMs:", "Spell:", "Combo:"]
    dict_values_counter = 0
    for i, k in enumerate(keys):
        I1.text((8, y), k, font=myFont, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
        if k not in exclude and (k != ''):
            if k == "Playrate:": rgb =(200,20,0)
            else: rgb = (169, 169, 169)
            im3 = PIL.Image.new(mode="RGB", size=(max_x[dict_values_counter] - 38, 4), color=rgb)
            im.paste(im3, (8, y + 30))
            y += offset
        else:
            y += offset - 10
        if i == 4 or i == 9: dict_values_counter += 1
    image_id = id_generator()
    im.save(shared_folder + image_id + '.png')
    return site + image_id + '.png'

def handle_response(message, author) -> str:
    p_message = message.lower()
    if '!elo fine' in p_message:
        embed = apicall_elo('fine', 0)
        embed.add_field(name="", value=":eggplant:")
        return embed
    if 'julian' in p_message:       return 'julian sucks'
    if 'penny' in p_message:        return 'penny sucks'
    if 'green' in p_message:        return '<:green:1136426397619978391> & aggressive'
    if 'kidkpro' in p_message:      return ':eggplant:'
    if 'widderson' in p_message:    return ':banana:'
    if 'ofma' in p_message:         return ':a: :b:'
    if 'drachir' in p_message:      return '<:GK:1161013811927601192>'
    if 'shea' in p_message:         return 'sister? <:sheastare:1121047323464712273>'
    if 'aviator' in p_message:      return '<:aviator:1180232477537738944>'
    if 'lucy' in p_message:         return 'snail angle <:Dice:1180232938399469588>'
    if 'kingdan' in p_message:      return "like its the most fun i've had playing legion pretty much"
    if 'genom' in p_message:        return ":rat:"
    if 'quacker' in p_message:      return ":duck: quack"
    if 'toikan' in p_message:       return "nyctea, :older_man:"
    if 'jokeonu' in p_message:      return "look dis brah, snacc <:snacc:1225281693393616936>"
    if 'mrbuzz' in p_message:       return "(On his smurf)"
    if 'nyctea' in p_message:       return "toikan,"
    if 'lwon' in p_message:         return "<:AgentEggwon:1215622131187191828> fucking teamates, nothing you can do"
    if '!github' in p_message:      return 'https://github.com/Drachiir/Drachbot'
    if '!update' in p_message and str(author) == 'drachir_':
        input = p_message.split(" ")
        return ladder_update(input[1])
    if '!novaupdate' in p_message and str(author) == 'drachir_':    return pull_games_by_id(message.split('|')[1],message.split('|')[2])
    if '!update' in p_message and str(author) != 'drachir_':    return 'thanks ' + str(author) + '!'
    if "!csv_data" in p_message and (str(author) == 'drachir_' or str(author) == 'pennywiseuk'): return json_to_csv.legion_json_to_csv()
    if '!script' and str(author) == "drachir_":
        path1 = str(pathlib.Path(__file__).parent.resolve()) + "/Games/"
        path3 = str(pathlib.Path(__file__).parent.resolve()) + "/Profiles/"
        games = sorted(os.listdir(path3))
        for i, x in enumerate(games):
            print(str(i+1) + " out of " + str(len(games)))
            path2 = str(pathlib.Path(__file__).parent.resolve()) + "/Profiles/" + x + "/gamedata/"
            try:
                print(path2)
                games2 = os.listdir(path2)
            except FileNotFoundError:
                print("not found")
                continue
            for game in games2:
                file_name = os.path.join(path2, game)
                try:
                    shutil.copy(file_name, path1)
                except shutil.Error:
                    continue

def apicall_getid(playername):
    request_type = 'players/byName/'
    url = 'https://apiv2.legiontd2.com/' + request_type + playername
    try:
        api_response = requests.get(url, headers=header)
        if 'Limit Exceeded' in api_response.text:
            return 1
        api_response.raise_for_status()
    except requests.exceptions.HTTPError:
        return 0
    else:
        api_call_logger(request_type)
        playerid = json.loads(api_response.text)
        return playerid['_id']

def apicall_getprofile(playerid):
    request_type = 'players/byId/'
    url = 'https://apiv2.legiontd2.com/' + request_type + playerid
    api_response = requests.get(url, headers=header)
    player_profile = json.loads(api_response.text)
    api_call_logger(request_type)
    return player_profile

def apicall_getstats(playerid):
    request_type = 'players/stats/'
    url = 'https://apiv2.legiontd2.com/' + request_type + playerid
    api_response = requests.get(url, headers=header)
    stats = json.loads(api_response.text)
    api_call_logger(request_type)
    return stats

def get_games_saved_count(playerid):
    path = str(pathlib.Path(__file__).parent.resolve()) + "/Profiles/" + playerid + "/gamedata/"
    if Path(Path(str(path))).is_dir():
        json_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.json')]
        if len(json_files) == 0:
            return 200
        else:
            return len(json_files)
    else:
        return 200

def apicall_pullgamedata(playerid, offset, path, expected):
    ranked_count = 0
    games_count = 0
    output = []
    url = 'https://apiv2.legiontd2.com/players/matchHistory/' + str(playerid) + '?limit=' + str(50) + '&offset=' + str(offset) + '&countResults=false'
    print('Pulling ' + str(50) + ' games from API...')
    api_response = requests.get(url, headers=header)
    api_call_logger("players/matchHistory/")
    raw_data = json.loads(api_response.text)
    print('Saving ranked games.')
    for x in raw_data:
        if ranked_count == expected:
            break
        if (raw_data == {'message': 'Internal server error'}) or (raw_data == {'err': 'Entry not found.'}):
            break
        if (x['queueType'] == 'Normal'):
            if Path(Path(str(path + 'gamedata/')+x['date'].split('.')[0].replace('T', '-').replace(':', '-')+'_'+x['version'].replace('.', '-')+'_'+str(x['gameElo'])+ '_' + str(x['_id']) + ".json")).is_file():
                print('File already there, breaking loop.')
                break
            ranked_count += 1
            with open(str(path + 'gamedata/')+x['date'].split('.')[0].replace('T', '-').replace(':', '-')+'_'+x['version'].replace('.', '-')+'_'+str(x['gameElo'])+'_' + str(x['_id']) + ".json", "w") as f:
                json.dump(x, f)
                f.close()
            if not Path(Path(str(pathlib.Path(__file__).parent.resolve()) + "/Games/"+x['date'].split('.')[0].replace('T', '-').replace(':', '-')+'_'+x['version'].replace('.', '-')+'_'+str(x['gameElo'])+ '_' + str(x['_id']) + ".json")).is_file():
                with open(str(pathlib.Path(__file__).parent.resolve()) + "/Games/"+x['date'].split('.')[0].replace('T', '-').replace(':', '-')+'_'+x['version'].replace('.', '-')+'_'+str(x['gameElo'])+'_' + str(x['_id']) + ".json", "w") as f2:
                    json.dump(x, f2)
                    f2.close()
        games_count += 1
    output.append(ranked_count)
    output.append(games_count)
    return output

def get_games_loop(playerid, offset, path, expected, timeout_limit = 3):
    print("Starting get_games_loop, expecting " + str(expected) + " games.")
    data = apicall_pullgamedata(playerid, offset, path, expected)
    count = data[0]
    games_count = data[1]
    timeout = 0
    while count < expected:
        if timeout == timeout_limit:
            print('Timeout while pulling games.')
            break
        offset += 50
        data = apicall_pullgamedata(playerid, offset, path, expected)
        if data[0] + data[1] == 0:
            timeout += 1
        count += data[0]
        games_count += data[1]
    else:
        print('All '+str(expected)+' required games pulled.')
    return games_count

def apicall_getmatchistory(playerid, games, min_elo=0, patch='0', update = 0, earlier_than_wave10 = False, sort_by = "date"):
    patch_list = []
    if patch != '0' and "," in patch:
        patch_list = patch.replace(" ", "").split(',')
    elif patch != '0' and "-" not in patch and "+" not in patch:
        patch_list = patch.replace(" ", "").split(',')
    elif patch != "0" and "+" in patch and "-" not in patch:
        patch_new = patch.replace(" ", "").split("+")
        if len(patch_new) == 2:
            patch_new = patch_new[1].split('.')
            for x in range(13 - int(patch_new[1])):
                if int(patch_new[1]) + x < 10:
                    prefix = "0"
                else:
                    prefix = ""
                patch_list.append(patch_new[0] + "." + prefix + str(int(patch_new[1]) + x))
        else:
            return []
    elif patch != "0" and "-" in patch:
        patch_new = patch.split("-")
        if len(patch_new) == 2:
            patch_new2 = patch_new[0].split('.')
            patch_new3 = patch_new[1].split('.')
            for x in range(int(patch_new3[1])-int(patch_new2[1])+1):
                if int(patch_new2[1]) + x < 10:
                    prefix = "0"
                else:
                    prefix = ""
                patch_list.append(patch_new2[0] + "." + prefix + str(int(patch_new2[1]) + x))
        else:
            return []
    games_count = 0
    if playerid != 'all' and 'nova cup' not in playerid:
        if games == 0:
            games2 = get_games_saved_count(playerid)
        else:
            games2 = games
        path = str(pathlib.Path(__file__).parent.resolve()) + "/Profiles/" + playerid + "/"
        if not Path(Path(str(path))).is_dir():
            print(playerid + ' profile not found, creating new folder...')
            new_profile = True
            Path(str(path+'gamedata/')).mkdir(parents=True, exist_ok=True)
            with open(str(path) + "gamecount_" + playerid + ".txt", "w") as f:
                data = get_games_loop(playerid, 0, path, games2)
                playerstats = apicall_getstats(playerid)
                try:
                    wins = playerstats['rankedWinsThisSeason']
                except KeyError:
                    wins = 0
                try:
                    losses = playerstats['rankedLossesThisSeason']
                except KeyError:
                    losses = 0
                ranked_games = wins + losses
                lines = [str(ranked_games), str(data)]
                f.write('\n'.join(lines))
        else:
            new_profile = False
            for file in glob.glob(path + '*.txt'):
                file_path = file
            with open(file, 'r') as f:
                txt = f.readlines()
                ranked_games_old = int(txt[0])
                games_amount_old = int(txt[1])
            playerstats = apicall_getstats(playerid)
            try:
                wins = playerstats['rankedWinsThisSeason']
            except KeyError:
                wins = 0
            try:
                losses = playerstats['rankedLossesThisSeason']
            except KeyError:
                losses = 0
            ranked_games = wins + losses
            games_diff = ranked_games - ranked_games_old
            if ranked_games_old < ranked_games:
                games_count += get_games_loop(playerid, 0, path, games_diff)
            json_files = [pos_json for pos_json in os.listdir(path + 'gamedata/') if pos_json.endswith('.json')]
            if len(json_files) < games2:
                games_count += get_games_loop(playerid, games_amount_old, path, games2-len(json_files))
            with open(str(path) + "gamecount_" + playerid + ".txt", "w") as f:
                f.truncate(0)
                lines = [str(ranked_games), str(games_amount_old+games_count)]
                f.write('\n'.join(lines))
        if update == 0:
            raw_data = []
            if games == 0:
                games2 = get_games_saved_count(playerid)
            json_files = [pos_json for pos_json in os.listdir(path + 'gamedata/') if pos_json.endswith('.json')]
            count = 0
            if sort_by == "date":
                sorted_json_files = sorted(json_files, key=lambda x: time.mktime(time.strptime(x.split('_')[-4].split('/')[-1], "%Y-%m-%d-%H-%M-%S")), reverse=True)
            elif sort_by == "elo":
                sorted_json_files = sorted(json_files, key=lambda x: x.split("_")[-2], reverse=True)
            for i, x in enumerate(sorted_json_files):
                with open(path + '/gamedata/' + x) as f:
                    raw_data_partial = json.load(f)
                    f.close()
                    if raw_data_partial['gameElo'] >= min_elo:
                        if patch == '0':
                            if count == games2:
                                break
                            if earlier_than_wave10 == True:
                                count += 1
                                raw_data.append(raw_data_partial)
                            elif raw_data_partial['endingWave'] > 10 and earlier_than_wave10 == False:
                                count += 1
                                raw_data.append(raw_data_partial)
                        else:
                            if count == games2:
                                break
                            for x in patch_list:
                                if str(raw_data_partial['version']).startswith('v'+x):
                                    if earlier_than_wave10 == True:
                                        count += 1
                                        raw_data.append(raw_data_partial)
                                    elif raw_data_partial['endingWave'] > 10 and earlier_than_wave10 == False:
                                        count += 1
                                        raw_data.append(raw_data_partial)
    else:
        if 'nova cup' in playerid:
            path2 = str(pathlib.Path(__file__).parent.resolve()) + "/Profiles/" + playerid + '/gamedata/'
            json_files = []
            raw_data = []
            try:
                if patch != '0':
                    for y in patch_list:
                        json_files.extend([path2 + pos_json for pos_json in os.listdir(path2) if pos_json.endswith('.json') and pos_json.split('_')[-3].startswith('v' + y.replace('.', '-')) and int(pos_json.split('_')[-2]) >= min_elo])
                else:
                    json_files.extend([path2 + pos_json for pos_json in os.listdir(path2) if pos_json.endswith('.json') and int(pos_json.split('_')[-2]) >= min_elo])
                sorted_json_files = sorted(json_files, key=lambda x: time.mktime(time.strptime(x.split('_')[-4].split('/')[-1], "%Y-%m-%d-%H-%M-%S")), reverse=True)
            except FileNotFoundError:
                return playerid + " not found. :("
        else:
            path1 = str(pathlib.Path(__file__).parent.resolve()) + "/Games/"
            raw_data = []
            json_files = []
            json_counter = 0
            if patch != '0':
                for y in patch_list:
                    json_files.extend([path1 + pos_json for pos_json in os.listdir(path1) if pos_json.endswith('.json') and pos_json.split('_')[-3].startswith('v'+y.replace('.', '-')) and int(pos_json.split('_')[-2]) >= min_elo])
            else:
                    json_files.extend([path1 + pos_json for pos_json in os.listdir(path1) if pos_json.endswith('.json') and int(pos_json.split('_')[-2]) >= min_elo])
            if sort_by == "date":
                sorted_json_files = sorted(json_files, key=lambda x: time.mktime(time.strptime(x.split('_')[-4].split('/')[-1],"%Y-%m-%d-%H-%M-%S")), reverse=True)
            elif sort_by == "elo":
                sorted_json_files = sorted(json_files, key=lambda x: x.split("_")[-2], reverse=True)
        count = 0
        for i, x in enumerate(sorted_json_files):
            if count == games and games != 0:
                break
            with open(x) as f:
                try:
                    raw_data_partial = json.load(f)
                except json.decoder.JSONDecodeError:
                    os.remove(x)
                    print("file error")
                f.close()
                if earlier_than_wave10 == True:
                    count += 1
                    raw_data.append(raw_data_partial)
                elif raw_data_partial['endingWave'] > 10 and earlier_than_wave10 == False:
                    count += 1
                    raw_data.append(raw_data_partial)
    if update == 0:
        print(len(raw_data))
        return raw_data
    else:
        if new_profile:
            return data
        else:
            return games_diff

def ladder_update(amount=100):
    url = 'https://apiv2.legiontd2.com/players/stats?limit='+str(amount)+'&sortBy=overallElo&sortDirection=-1'
    api_response = requests.get(url, headers=header)
    leaderboard = json.loads(api_response.text)
    games_count = 0
    for i, player in enumerate(leaderboard):
        print(str(i+1) + '. ' + player["profile"][0]["playerName"])
        ranked_games = player['rankedWinsThisSeason'] + player['rankedLossesThisSeason']
        print(ranked_games)
        if ranked_games >= 200:
            games_count += apicall_getmatchistory(player["_id"], 200, 0, '0', 1)
        elif ranked_games == 0:
            print('No games this season.')
            continue
        else:
            games_count += apicall_getmatchistory(player["_id"], ranked_games, 0, '0', 1)
    return 'Pulled ' + str(games_count) + ' new games from the Top ' + str(amount)

def pull_games_by_id(file, name):
    path = '/home/container/Profiles/' + name
    if not Path(Path(str(path + '/gamedata/'))).is_dir():
        print(name + ' profile not found, creating new folder...')
        Path(str(path + '/gamedata/')).mkdir(parents=True, exist_ok=True)
    with open(file, 'r') as f:
        txt = f.readlines()
        print('Pulling ' + str(len(txt)) + ' games from API...')
        for game_id in txt:
            game_id = str(game_id).replace('\n', '')
            print('Pulling game id: ' + str(game_id))
            url = 'https://apiv2.legiontd2.com/games/byId/'+game_id+'?includeDetails=true'
            print(url)
            api_response = requests.get(url, headers=header)
            x = json.loads(api_response.text)
            if (x == {'message': 'Internal server error'}) or (x == {'err': 'Entry not found.'}):
                    print(x)
                    break
            if Path(Path(str(path + '/gamedata/') + x['date'].split('.')[0].replace('T', '-').replace(':','-') + '_' +x['version'].replace('.', '-') + '_' + str(x['gameElo']) + '_' + str(x['_id']) + ".json")).is_file():
                print('File already there, breaking loop.')
                break
            with open(str(path + '/gamedata/') + x['date'].split('.')[0].replace('T', '-').replace(':','-') + '_' +x['version'].replace('.', '-') + '_' + str(x['gameElo']) + '_' + str(x['_id']) + ".json","w") as f:
                json.dump(x, f)
    return 'Success'

def apicall_leaderboard(ranks=10, transparency=False):
    url = 'https://apiv2.legiontd2.com/players/stats?limit=' + str(ranks) + '&sortBy=overallElo&sortDirection=-1'
    api_response = requests.get(url, headers=header)
    api_call_logger("players/stats")
    leaderboard = json.loads(api_response.text)
    player_dict = {}
    url = 'https://cdn.legiontd2.com/icons/Items/'
    url2 = 'https://cdn.legiontd2.com/icons/'
    if transparency:
        mode = 'RGBA'
        colors = (0, 0, 0, 0)
    else:
        mode = 'RGB'
        colors = (49, 51, 56)
    im = PIL.Image.new(mode=mode, size=(758, 830), color=colors)
    im2 = PIL.Image.new(mode="RGB", size=(720, 76), color=(25, 25, 25))
    I1 = ImageDraw.Draw(im)
    ttf = 'Files/RobotoCondensed-Regular.ttf'
    myFont_small = ImageFont.truetype(ttf, 20)
    myFont = ImageFont.truetype(ttf, 25)
    myFont_title = ImageFont.truetype(ttf, 30)
    x = 24
    y = 24
    offset = 80
    for i, player in enumerate(leaderboard):
        im.paste(im2, (x-6,y-6))
        avatar_url = 'https://cdn.legiontd2.com/' + player["profile"][0]["avatarUrl"]
        avatar_response = requests.get(avatar_url)
        av_image = Image.open(BytesIO(avatar_response.content))
        gold_border = Image.open('Files/gold_64.png')
        if im_has_alpha(np.array(av_image)):
            im.paste(av_image, (x, y), mask=av_image)
        else:
            im.paste(av_image, (x, y))
        im.paste(gold_border, (x, y), mask=gold_border)
        last_game = apicall_getmatchistory(player["_id"], 1, earlier_than_wave10=True)
        game_date = datetime.strptime(last_game[0]["date"].split(".000Z")[0].replace("T", "-"), '%Y-%m-%d-%H:%M:%S')
        if game_date < datetime.now() - timedelta(days=2) or player["profile"][0]["playerName"] == "InDaHole":
            tent = Image.open('Files/tent.png')
            im.paste(tent, (x, y), mask=tent)
        I1.text((x + offset, y), str(i+1)+". "+player["profile"][0]["playerName"], font=myFont, stroke_width=2, stroke_fill=(0, 0, 0),fill=(255, 255, 255))
        width = I1.textlength(str(i+1)+". "+player["profile"][0]["playerName"], font=myFont)
        try:
            I1.text((x+width+10+offset, y+5), player["profile"][0]["guildTag"], font=myFont_small, stroke_width=2, stroke_fill=(0, 0, 0),fill=(247, 203, 27))
        except KeyError:
            print(player["profile"][0]["playerName"]+ " has no guild.")
        if player["overallElo"] >= 2800:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Legend.png'
        elif player["overallElo"] >= 2600:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Grandmaster.png'
        elif player["overallElo"] >= 2400:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/SeniorMaster.png'
        elif player["overallElo"] >= 2200:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Master.png'
        else:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Expert.png'
        rank_response = requests.get(rank_url)
        rank_image = Image.open(BytesIO(rank_response.content))
        rank_image = rank_image.resize((32,32))
        im.paste(rank_image, (x + offset, y+30), mask=rank_image)
        I1.text((x + offset+ 40, y+30), str(player["overallElo"]), font=myFont, stroke_width=2, stroke_fill=(0, 0, 0),fill=(255, 255, 255))
        width2 = I1.textlength(str(player["overallElo"]), font=myFont)
        I1.text((x + offset + 60+width2, y + 33), "W: "+str(player["rankedWinsThisSeason"])+" L: "+str(player["rankedLossesThisSeason"]), font=myFont_small, stroke_width=2,stroke_fill=(0, 0, 0), fill=(255, 255, 255))
        width2 += I1.textlength("W: "+str(player["rankedWinsThisSeason"])+" L: "+str(player["rankedLossesThisSeason"]), font=myFont_small)
        winrate = round(player["rankedWinsThisSeason"]/(player["rankedWinsThisSeason"]+player["rankedLossesThisSeason"])*100, 1)
        if winrate >= 50:
            rgb = (0,255,0)
        else:
            rgb = (255, 0, 0)
        I1.text((x + offset + 70+width2, y + 33), "(WR: "+str(winrate)+ "%)", font=myFont_small, stroke_width=2,stroke_fill=(0, 0, 0), fill=(rgb))
        width2 += I1.textlength("(WR: "+str(winrate)+ "%)", font=myFont_small)
        if player["winStreak"] != 0:
            I1.text((x + offset + 90+width2, y + 33), "Win Streak: "+str(player["winStreak"]), font=myFont_small, stroke_width=2,stroke_fill=(0, 0, 0), fill=(0, 255, 0))
            width2 +=  I1.textlength("Win Streak: "+str(player["winStreak"]), font=myFont_small)
        else:
            I1.text((x + offset + 90+width2, y + 33), "Loss Streak: "+str(player["lossStreak"]), font=myFont_small, stroke_width=2,stroke_fill=(0, 0, 0), fill=(255, 0, 0))
            width2 += I1.textlength("Loss Streak: "+str(player["lossStreak"]), font=myFont_small)
        lp_response = requests.get("https://cdn.legiontd2.com/icons/LadderPoints.png")
        lp_image = Image.open(BytesIO(lp_response.content))
        lp_image = lp_image.resize((32, 32))
        im.paste(lp_image, (x + offset+int(width2)+110, y + 30), mask=lp_image)
        I1.text((x + offset + 142 + width2, y + 33), " LP: "+str(player["ladderPoints"]), font=myFont_small, stroke_width=2,stroke_fill=(0, 0, 0), fill=(255,255,255))
        y += offset
    image_id = id_generator()
    im.save(shared_folder + image_id + '.png')
    return site + image_id + '.png'

def apicall_elograph(playername, games, patch, transparency = False):
    playerid = apicall_getid(playername)
    if playerid == 0:
        return 'Player ' + playername + ' not found.'
    if playerid == 1:
        return 'API limit reached.'
    try:
        history_raw = apicall_getmatchistory(playerid, games, 0, patch, earlier_than_wave10=True)
    except TypeError as e:
        print(e)
        return playername + ' has not played enough games.'
    if type(history_raw) == str:
        return history_raw
    games = len(history_raw)
    if games == 0:
        return 'No games found.'
    patches = []
    elo_per_game = []
    date_per_game = []
    for game in history_raw:
        for player in game["playersData"]:
            if player["playerId"] == playerid:
                patches.append(game["version"])
                elo_per_game.insert(0, player["overallElo"]+player["eloChange"])
                date_this = game["date"].replace("T", "-").replace(":", "-").split(".")[0]
                date_per_game.insert(0, datetime.strptime(date_this, "%Y-%m-%d-%H-%M-%S").strftime("%d/%m/%y"))
    new_patches = []
    for x in patches:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches = list(dict.fromkeys(new_patches))
    patches = sorted(patches, key=lambda x: int(x.split(".")[0] + x.split(".")[1]), reverse=True)
    #Image generation
    x = 126
    y = 160
    if transparency:
        mode = 'RGBA'
        colors = (0,0,0,0)
    else:
        mode = 'RGB'
        colors = (49,51,56)
    im = PIL.Image.new(mode=mode, size=(1300, 810), color=colors)
    im2 = PIL.Image.new(mode="RGB", size=(88, 900), color=(25, 25, 25))
    im3 = PIL.Image.new(mode="RGB", size=(1676, 4), color=(169, 169, 169))
    I1 = ImageDraw.Draw(im)
    ttf = 'Files/RobotoCondensed-Regular.ttf'
    myFont_small = ImageFont.truetype(ttf, 20)
    myFont = ImageFont.truetype(ttf, 25)
    myFont_title = ImageFont.truetype(ttf, 30)
    I1.text((10, 15), playername.capitalize() + "'s Elo Graph (From " + str(games) + " ranked games)", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    I1.text((10, 55), 'Patches: ' + ', '.join(patches), font=myFont_small, stroke_width=2, stroke_fill=(0, 0, 0),fill=(255, 255, 255))
    #matplotlib graph
    params = {"ytick.color": "w",
              "xtick.color": "w",
              "axes.labelcolor": "w",
              "axes.edgecolor": "w",
              "figure.figsize": (15, 8),
              'axes.autolimit_mode': 'round_numbers',
              'font.weight': 'bold'}
    if len(elo_per_game) > 100:
        marker_plot = ''
    else:
        marker_plot = 'o'
    plt.rcParams.update(params)
    fig, ax = plt.subplots()
    ax2 = ax.twiny()
    ax.grid(linewidth=2)
    ax.margins(x=0)
    ax.set_xlabel('Games', weight='bold')
    ax.set_ylabel('Elo', weight='bold')
    ax2.set_xlabel("Date d/m/y", weight='bold')
    ax.plot(range(1, games + 1), elo_per_game, color='red', marker=marker_plot, linewidth=2, label='Elo')
    ax2.set_xlim(ax.get_xlim())
    new_tick_locs = []
    for d in range(0, games):
        new_tick_locs.append(d)
    ax2.set_xticks(new_tick_locs)
    ax2.set_xticklabels(date_per_game)
    locator = plt.MaxNLocator(nbins=len(ax.get_xticks())-1, min_n_ticks=1)
    ax2.xaxis.set_major_locator(locator)
    img_buf = io.BytesIO()
    fig.savefig(img_buf, transparent=True, format='png')
    plt.close()
    elo_graph = Image.open(img_buf)
    im.paste(elo_graph, (-100,40), elo_graph)
    
    image_id = id_generator()
    im.save(shared_folder + image_id + '.png')
    return site + image_id + '.png'

def apicall_statsgraph(playernames: list, games, min_elo, patch, key, transparency = False, sort="date", waves = [1,21]) -> str:
    playerids = set()
    total_games = 0
    for name in playernames:
        if name == "all":
            playerid = "all"
        else:
            playerid = apicall_getid(name)
        if playerid == 0:
            return name + ' not found.'
        if playerid == 1:
            return 'API limit reached.'
        playerids.add(playerid)
    players_dict = dict()
    print("Starting stats graph command...")
    patches = []
    for j, id in enumerate(playerids):
        history_raw = apicall_getmatchistory(id, games, min_elo, patch, sort_by=sort)
        if type(history_raw) == str:
            return history_raw
        games2 = len(history_raw)
        total_games += games2
        if games2 == 0:
            return 'No games found for ' + playernames[j] + "."
        for game in history_raw:
            patches.append(game["version"])
            for player in game["playersData"]:
                if player["playerId"] == id or id == "all":
                    if id in players_dict:
                        players_dict[id]["Data"].append(player[key])
                    else:
                        players_dict[id] = {"Data": [player[key]]}
    for player in players_dict:
        players_dict[player]["Waves"] = []
        for w in range(21):
            players_dict[player]["Waves"].append([0,0])
        for data in players_dict[player]["Data"]:
            for c, wave_data in enumerate(data):
                players_dict[player]["Waves"][c][0] += 1
                players_dict[player]["Waves"][c][1] += wave_data
        players_dict[player]["FinalData"] = []
        for index, wave in enumerate(players_dict[player]["Waves"]):
            if index+1 >= waves[0] and index+1 <= waves[1]:
                try:
                    players_dict[player]["FinalData"].append(round(wave[1]/wave[0], 1))
                except ZeroDivisionError:
                    players_dict[player]["FinalData"].append(0)
        del players_dict[player]["Data"]
        del players_dict[player]["Waves"]
    new_patches = []
    count = 0
    for x in patches:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches = list(dict.fromkeys(new_patches))
    patches = sorted(patches, key=lambda x: int(x.split(".")[0] + x.split(".")[1]), reverse=True)
    #Image generation
    x = 126
    y = 160
    if transparency:
        mode = 'RGBA'
        colors = (0,0,0,0)
    else:
        mode = 'RGB'
        colors = (49,51,56)
    im = PIL.Image.new(mode=mode, size=(1300, 800), color=colors)
    I1 = ImageDraw.Draw(im)
    ttf = 'Files/RobotoCondensed-Regular.ttf'
    myFont_small = ImageFont.truetype(ttf, 20)
    myFont = ImageFont.truetype(ttf, 25)
    myFont_title = ImageFont.truetype(ttf, 30)
    I1.text((10, 15), key+" Graph (From " + str(total_games) + " ranked games)", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    I1.text((10, 55), 'Patches: ' + ', '.join(patches), font=myFont_small, stroke_width=2, stroke_fill=(0, 0, 0),fill=(255, 255, 255))
    #matplotlib graph
    params = {"ytick.color": "w",
              "xtick.color": "w",
              "axes.labelcolor": "w",
              "axes.edgecolor": "w",
              "figure.figsize": (15, 8),
              'font.weight': 'bold'}
    marker_plot = 'o'
    plt.rcParams.update(params)
    fig, ax = plt.subplots()
    ax.grid(linewidth=2)
    ax.margins(x=0)
    ax.set_xlabel('Wave', weight='bold')
    ax.set_ylabel(key, weight='bold')
    colors = ["red","deepskyblue","green"]
    waves_list = []
    for v in range(waves[0],waves[1]+1):
        waves_list.append(str(v))
    for index, player in enumerate(players_dict):
        if player == "all":
            label_string = "All"
        else:
            label_string = apicall_getprofile(player)["playerName"]
        ax.plot(waves_list, players_dict[player]["FinalData"], color=colors[index], marker=marker_plot, linewidth=2, label=label_string)
    ax.legend(bbox_to_anchor=(0.57, 1.07), prop={'size': 13})
    img_buf = io.BytesIO()
    fig.savefig(img_buf, transparent=True, format='png')
    plt.close()
    elo_graph = Image.open(img_buf)
    im.paste(elo_graph, (-100,30), elo_graph)
    image_id = id_generator()
    im.show()
    im.save(shared_folder + image_id + '.png')
    return site + image_id + '.png'

def apicall_sendstats(playername, starting_wave, games, min_elo, patch, sort="date", transparency = False):
    if starting_wave > 20:
        return "Enter a wave before 21."
    elif starting_wave < 0:
        return "Invalid Wave number."
    starting_wave -= 1
    if playername.lower() == 'all':
        playerid = 'all'
    elif 'nova cup' in playername:
        playerid = playername
    else:
        playerid = apicall_getid(playername)
        if playerid == 0:
            return 'Player ' + playername + ' not found.'
        if playerid == 1:
            return 'API limit reached.'
        profile = apicall_getprofile(playerid)
        playername = apicall_getprofile(playerid)['playerName']
        avatar = apicall_getprofile(playerid)['avatarUrl']
    try:
        history_raw = apicall_getmatchistory(playerid, games, min_elo=min_elo, patch=patch, sort_by=sort)
    except TypeError as e:
        print(e)
        return playername + ' has not played enough games.'
    if type(history_raw) == str:
        return history_raw
    games = len(history_raw)
    if games == 0:
        return 'No games found.'
    if 'nova cup' in playerid:
        playerid = 'all'
    gameelo_list = []
    patches = []
    print('starting sendstats command...')
    send_count = 0
    game_count = 0
    sends_dict = {}
    for game in history_raw:
        for player in game["playersData"]:
            if player["playerId"] == playerid or playerid == 'all':
                patches.append(game["version"])
                save_on_1 = False
                if game["endingWave"] < starting_wave+1:
                    continue
                else:
                    game_count += 1
                    gameelo_list.append(game["gameElo"])
                if starting_wave != -1:
                    if len(player["mercenariesSentPerWave"][starting_wave]) == 0 and len(player["kingUpgradesPerWave"][starting_wave]) == 0:
                        continue
                elif starting_wave == -1:
                    if len(player["mercenariesSentPerWave"][0]) == 0 and len(player["kingUpgradesPerWave"][0]) == 0:
                        save_on_1 = True
                    else:
                        continue
                send = count_mythium(player["mercenariesSentPerWave"][starting_wave]) + len(player["kingUpgradesPerWave"][starting_wave]) * 20
                small_send = (player["workersPerWave"][starting_wave] - 5) / 4 * 20
                if (save_on_1 == False) and (send > small_send):
                    send_count += 1
                    if "Wave " + str(starting_wave + 1) in sends_dict:
                        sends_dict["Wave " + str(starting_wave+1)]["Count"] += 1
                        sends_dict["Wave " + str(starting_wave+1)]["Sends"].extend(player["mercenariesSentPerWave"][starting_wave])
                        if len(player["kingUpgradesPerWave"][starting_wave]) > 0:
                            sends_dict["Wave " + str(starting_wave + 1)]["Sends"].extend(player["kingUpgradesPerWave"][starting_wave])
                    else:
                        sends_dict["Wave " + str(starting_wave+1)] = {"Count": 1, "Sends": player["mercenariesSentPerWave"][starting_wave]}
                        if len(player["kingUpgradesPerWave"][starting_wave]) > 0:
                            sends_dict["Wave " + str(starting_wave + 1)]["Sends"].extend(player["kingUpgradesPerWave"][starting_wave])
                    for n in range(game["endingWave"]-starting_wave-1):
                        try:
                            send2 = count_mythium(player["mercenariesSentPerWave"][starting_wave+n+1]) + len(player["kingUpgradesPerWave"][starting_wave+n+1]) * 20
                        except IndexError:
                            break
                        small_send2 = (player["workersPerWave"][starting_wave+n+1] - 5) / 4 * 20
                        if send2 > small_send2:
                            if "Wave " + str(starting_wave+n+2) in sends_dict:
                                sends_dict["Wave " + str(starting_wave+n+2)]["Count"] += 1
                                sends_dict["Wave " + str(starting_wave+n+2)]["Sends"].extend(player["mercenariesSentPerWave"][starting_wave+n+1])
                                if len(player["kingUpgradesPerWave"][starting_wave+n+1]) > 0:
                                    sends_dict["Wave " + str(starting_wave+n+2)]["Sends"].extend(player["kingUpgradesPerWave"][starting_wave+n+1])
                                break
                            else:
                                sends_dict["Wave " + str(starting_wave+n+2)] = {"Count": 1, "Sends": player["mercenariesSentPerWave"][starting_wave+n+1]}
                                if len(player["kingUpgradesPerWave"][starting_wave+n+1]) > 0:
                                    sends_dict["Wave " + str(starting_wave+n+2)]["Sends"].extend(player["kingUpgradesPerWave"][starting_wave+n+1])
                                break
                elif save_on_1 == True:
                    send_count += 1
                    for n in range(game["endingWave"]-1):
                        if len(player["mercenariesSentPerWave"][n+1]) > 0 or len(player["kingUpgradesPerWave"][n+1]) > 0:
                            if "Wave " + str(n+2) in sends_dict:
                                sends_dict["Wave " + str(n+2)]["Count"] += 1
                                sends_dict["Wave " + str(n+2)]["Sends"].extend(player["mercenariesSentPerWave"][n+1])
                                if len(player["kingUpgradesPerWave"][n+1]) > 0:
                                    sends_dict["Wave " + str(n+2)]["Sends"].extend(player["kingUpgradesPerWave"][n+1])
                                break
                            else:
                                sends_dict["Wave " + str(n+2)] = {"Count": 1,"Sends": player["mercenariesSentPerWave"][n+1]}
                                if len(player["kingUpgradesPerWave"][n+1]) > 0:
                                    sends_dict["Wave " + str(n+2)]["Sends"].extend(player["kingUpgradesPerWave"][n+1])
                                break
    new_patches = []
    for x in patches:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches = list(dict.fromkeys(new_patches))
    patches = sorted(patches, key=lambda x: int(x.split(".")[0] + x.split(".")[1]), reverse=True)
    if not sends_dict:
        return "No Wave" + str(starting_wave+1) + " sends found."
    else:
        avg_gameelo = round(sum(gameelo_list) / len(gameelo_list))
        newIndex = sorted(sends_dict, key=lambda x: sends_dict[x]["Count"], reverse=True)
        sends_dict = {k: sends_dict[k] for k in newIndex}
        if transparency:
            mode = 'RGBA'
            colors = (0, 0, 0, 0)
        else:
            mode = 'RGB'
            colors = (49, 51, 56)
        im = PIL.Image.new(mode=mode, size=(1300, 1120), color=colors)
        im2 = PIL.Image.new(mode="RGB", size=(1300, 76), color=(25, 25, 25))
        I1 = ImageDraw.Draw(im)
        ttf = 'Files/RobotoCondensed-Regular.ttf'
        myFont_small = ImageFont.truetype(ttf, 20)
        myFont = ImageFont.truetype(ttf, 25)
        myFont_title = ImageFont.truetype(ttf, 30)
        if playername == 'all' or 'nova cup' in playername:
            string = ''
        else:
            string = "'s"
            avatar_url = 'https://cdn.legiontd2.com/' + avatar
            avatar_response = requests.get(avatar_url)
            av_image = Image.open(BytesIO(avatar_response.content))
            gold_border = Image.open('Files/gold_64.png')
            if im_has_alpha(np.array(av_image)):
                im.paste(av_image, (10, 10), mask=av_image)
            else:
                im.paste(av_image, (10, 10))
            im.paste(gold_border, (10, 10), mask=gold_border)
        starting_wave += 1
        if starting_wave > 0:
            string_2 = "Wave " + str(starting_wave) + " send"
        else:
            string_2 = "Wave 1 save"
        I1.text((80, 10), str(playername.capitalize()) + string + " " + string_2 + " stats (From " + str(games) + " ranked games, Avg elo: " + str(avg_gameelo) + ")", font=myFont_title, stroke_width=2,stroke_fill=(0, 0, 0), fill=(255, 255, 255))
        I1.text((80, 50), 'Patches: ' + ', '.join(patches), font=myFont_small, stroke_width=2, stroke_fill=(0, 0, 0),fill=(255, 255, 255))
        x = 400
        y = 100
        for wave in sends_dict:
            im.paste(im2, (4,y-6))
            im.paste(Image.open('Files/Waves/'+wave.replace(" ", "")+".png"), (10, y))
            I1.text((80, y), wave, font=myFont, stroke_width=2,stroke_fill=(0, 0, 0), fill=(255, 255, 255))
            most_common_sends = Counter(sends_dict[wave]["Sends"]).most_common(6)
            I1.text((270, y), 'Fav. Sends:', font=myFont, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
            for send in most_common_sends:
                im.paste(Image.open(BytesIO(requests.get('https://cdn.legiontd2.com/icons/'+send[0].replace(" ", "")+".png").content)), (x, y))
                x += 70
                I1.text((x, y+20), ": "+str(send[1]), font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0),fill=(255, 255, 255))
                width = int(I1.textlength(": "+str(send[1]), font=myFont_title))
                x += width+5
            if wave == "Wave "+str(starting_wave):
                I1.text((80, y+32), "Sends: " + str(sends_dict[wave]["Count"]) + " (" + str(round(sends_dict[wave]["Count"] / game_count * 100, 1))+"%)",font=myFont, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
                I1.text((10, y+83), 'Next Send(s):', font=myFont_title, stroke_width=2,stroke_fill=(0, 0, 0), fill=(255, 255, 255))
                y += 140
            else:
                I1.text((80, y+32), "Sends: " + str(sends_dict[wave]["Count"]) + " (" + str(round(sends_dict[wave]["Count"] / send_count * 100, 1))+"%)",font=myFont, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
                y += 100
            x = 400
        image_id = id_generator()
        im.save(shared_folder + image_id + '.png')
        return site + image_id + '.png'

def novacup(division):
    html = requests.get('https://docs.google.com/spreadsheets/u/3/d/e/2PACX-1vQKndupwCvJdwYYzSNIm-olob9k4JYK4wIoSDXlxiYr2h7DFlO7NgveneoFtlBlZaMvQUP6QT1eAYkN/pubhtml#').text
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table")
    with open("novacup.csv", "w", encoding="utf-8") as f:
        wr = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
        wr.writerows([[td.text for td in row.find_all("td")] for row in tables[0].find_all("tr")])
    team_dict = {}
    with open("novacup.csv", encoding="utf-8", newline="") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            try:
                if row[1] != "Team Name" and row[1] != "" and row[1] not in team_dict:
                    team_dict[row[1]] = [row[2],row[3],row[4]]
            except Exception:
                continue
    newIndex = sorted(team_dict, key=lambda x: int(team_dict[x][2]), reverse=True)
    team_dict = {k: team_dict[k] for k in newIndex}
    month = datetime.now()
    output = str(month.strftime("%B")) + " Nova Cup Division 1:\n"
    output2 = str(month.strftime("%B")) + " Nova Cup Division 2:\n"
    count = 1
    for team in team_dict:
        if count < 9:
            output += str(count) +". **"+ team + "**: " + team_dict[team][0] + ", " + team_dict[team][1] + ", Seed Elo: " + team_dict[team][2] + "\n"
        if count >= 9:
            output2 += str(count-8) + ". **" + team + "**: " + team_dict[team][0] + ", " + team_dict[team][1] + ", Seed Elo: " + team_dict[team][2] + "\n"
        count +=1
        if count == 17:
            break
    if division == "1":
        return output
    elif division == "2":
        return output2

def matchhistory_viewer(playername:str):
    playerid = apicall_getid(playername)
    if playerid == 0:
        return playername + " player not found"
    elif playerid == 1:
        return "API error."
    profile = apicall_getprofile(playerid)
    avatar = "https://cdn.legiontd2.com/" + profile['avatarUrl']
    playername = profile["playerName"]
    history_raw = apicall_getmatchistory(playerid, 5, earlier_than_wave10=True)
    site_link = "https://overlay.drachbot.site/Images/"
    mod_date = datetime.fromtimestamp(time.mktime(time.strptime(history_raw[0]["date"].split(".")[0].replace("T", "-").replace(":", "-"), "%Y-%m-%d-%H-%M-%S")), tz=timezone.utc).timestamp()
    embed = discord.Embed(color=0x1cce3a, title="Match History\nLast game: "+discord_timestamps.format_timestamp(mod_date, TimestampType.RELATIVE))
    embed.set_author(name=playername, icon_url=avatar)
    for game in history_raw:
        per_game_list = []
        elo_prefix = ""
        emoji = wave_emotes.get("wave"+str(game["endingWave"]))
        for indx, player in enumerate(game["playersData"]):
            per_game_list.append(player["playerName"] + " " + get_ranked_emote(player["overallElo"]))
            if player["playerId"] != playerid: continue
            else:
                result = player["gameResult"].capitalize()
                if player["eloChange"] > 0:
                    elo_change = player["eloChange"]
                    elo_prefix = "+"
                else:
                    elo_change = player["eloChange"]
                    elo_prefix = ""
        embed.add_field(name="", value=emoji + " [" + result + " on Wave " + str(game["endingWave"]) +
                             "("+elo_prefix+str(elo_change)+" Elo)]("+apicall_gameid_visualizer(game["_id"], 0)+")\nWest: "+
                                per_game_list[0]+" "+per_game_list[1]+"\nEast: "+per_game_list[2]+" "+per_game_list[3], inline=False)
    return embed

def apicall_wave1tendency(playername, option, games, min_elo, patch, sort="date"):
    if playername.lower() == 'all':
        playerid = 'all'
        suffix = ''
    elif 'nova cup' in playername:
        suffix = ''
        playerid = playername
    else:
        suffix = "'s"
        playerid = apicall_getid(playername)
        if playerid == 0:
            return 'Player ' + playername + ' not found.'
        if playerid == 1:
            return 'API limit reached.'
    count = 0
    snail_count = 0
    kingup_atk_count = 0
    kingup_regen_count = 0
    kingup_spell_count = 0
    save_count = 0
    leaks_count = 0
    try:
        history_raw = apicall_getmatchistory(playerid, games, min_elo=min_elo, patch=patch, sort_by=sort, earlier_than_wave10=True)
    except TypeError as e:
        print(e)
        return playername + ' has not played enough games.'
    if type(history_raw) == str:
        return history_raw
    games = len(history_raw)
    if games == 0:
        return 'No games found.'
    if 'nova cup' in playerid:
        playerid = 'all'
    patches = []
    gameelo_list = []
    if option == "send":
        option_key = "mercenariesSentPerWave"
        option_key2 = "kingUpgradesPerWave"
    else:
        option_key = "mercenariesReceivedPerWave"
        option_key2 = "opponentKingUpgradesPerWave"
    for game in history_raw:
        patches.append(game["version"])
        gameelo_list.append(game["gameElo"])
        for i, player in enumerate(game["playersData"]):
            if player["playerId"] == playerid or playerid == 'all':
                if len(player[option_key][0]) > 0:
                    if player[option_key][0][0] == 'Snail':
                        snail_count = snail_count + 1
                        if option == 'send' and playerid != 'all':
                            if i == 0:
                                if len(game["playersData"][2]["leaksPerWave"][0]) != 0:
                                    leaks_count += 1
                            if i == 1:
                                if len(game["playersData"][3]["leaksPerWave"][0]) != 0:
                                    leaks_count += 1
                            if i == 2:
                                if len(game["playersData"][1]["leaksPerWave"][0]) != 0:
                                    leaks_count += 1
                            if i == 3:
                                if len(game["playersData"][0]["leaksPerWave"][0]) != 0:
                                    leaks_count += 1
                        if option == 'received' or playerid == 'all':
                            if len(player["leaksPerWave"][0]) != 0:
                                leaks_count += 1
                        continue
                elif len(player[option_key2][0]) > 0:
                    if str(player[option_key2][0][0]) == 'Upgrade King Attack':
                        kingup_atk_count = kingup_atk_count + 1
                        continue
                    if str(player[option_key2][0][0]) == 'Upgrade King Regen':
                        kingup_regen_count = kingup_regen_count + 1
                        continue
                    if str(player[option_key2][0][0]) == 'Upgrade King Spell':
                        kingup_spell_count = kingup_spell_count + 1
                        continue
                else:
                    save_count = save_count + 1
                    continue
    new_patches = []
    for x in patches:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches = list(dict.fromkeys(new_patches))
    patches = sorted(patches, key=lambda x: int(x.split(".")[0] + x.split(".")[1]), reverse=True)
    send_total = kingup_atk_count+kingup_regen_count+kingup_spell_count+snail_count+save_count
    kingup_total = kingup_atk_count+kingup_regen_count+kingup_spell_count
    avg_gameelo = round(sum(gameelo_list) / len(gameelo_list))
    if send_total == 0:
        return 'Not enough ranked data'
    if playerid == "all":
        playername = "All"
        avatar = "https://cdn.legiontd2.com/icons/Snail.png"
        option = ''
    else:
        profile = apicall_getprofile(playerid)
        avatar = "https://cdn.legiontd2.com/" + profile['avatarUrl']
        playername = profile["playerName"]
    embed = discord.Embed(color=0xE73333, description='(From ' + str(games) + ' ranked games, avg. elo: ' + str(avg_gameelo) + " " + get_ranked_emote(avg_gameelo) + ")\n\n"+
                          '**Kingup:** '+str(kingup_total) + ' | ' + str(round(kingup_total/send_total*100,1)) + '% (Attack: ' + str(kingup_atk_count) + ' Regen: ' + str(kingup_regen_count) + ' Spell: ' + str(kingup_spell_count) + ')\n'+
                          '**Snail:** ' + str(snail_count) + ' | ' + str(round(snail_count/send_total*100,1)) + '% (Leak count: ' + str(leaks_count) + ' (' + str(round(leaks_count/snail_count*100, 2)) + '%))\n'+
                          '**Save:** ' + str(save_count) + ' | '  + str(round(save_count/send_total*100,1)) + '%')
    embed.set_author(name=playername + suffix+" Wave 1 " + option + " stats", icon_url=avatar)
    embed.set_footer(text='Patches: ' + ', '.join(patches))
    return embed

def apicall_winrate(playername, playername2, option, games, patch, min_elo = 0, sort = "Count"):
    mmnames_list = ['LockIn', 'Greed', 'Redraw', 'Yolo', 'Fiesta', 'CashOut', 'Castle', 'Cartel', 'Chaos', 'Champion', 'DoubleLockIn', 'Kingsguard', "All"]
    mm1 = ""
    mm2 = ""
    if "," in playername:
        playername = playername.split(",")
        if playername[0].lower() != 'all':
            playerid = apicall_getid(playername[0])
        else:
            playerid = "all"
        for mm in mmnames_list:
            if mm.lower() == playername[1].replace(" ", "").lower() and mm.lower() != "all":
                mm1 = mm
                break
        else:
            return playername[1] + " mastermind not found."
    else:
        playerid = apicall_getid(playername)
    if playerid == 0:
        if type(playername) == list:
            playername = playername[0]
        return 'Player ' + playername + ' not found.'
    if playerid == 1:
        return 'API limit reached.'
    if "," in playername2:
        playername2 = playername2.split(",")
        if playername2[0].lower() != 'all':
            playerid2 = apicall_getid(playername2[0])
        else:
            playerid2 = "all"
        for mm in mmnames_list:
            if mm.lower() == playername2[1].replace(" ", "").lower():
                mm2 = mm
                break
        else:
            return playername2[1] + " mastermind not found."
    else:
        if playername2 != "all":
            playerid2 = apicall_getid(playername2)
        else:
            playerid2 = "all"
    if playerid2 == 0:
        if type(playername2) == list:
            playername2 = playername2[0]
        return 'Player ' + playername2 + ' not found.'
    if playerid2 == 1:
        return 'API limit reached.'
    win_count = 0
    game_count = 0
    queue_count = 0
    playerid2_list = []
    gameresults = []
    try:
        history_raw = apicall_getmatchistory(playerid, games, min_elo=min_elo, patch=patch, earlier_than_wave10=True)
    except TypeError as e:
        print(e)
        return playername + ' has not played enough games.'
    if type(history_raw) == str:
        return history_raw
    games = len(history_raw)
    if games == 0:
        return 'No games found.'
    gameelo_list = []
    patches_list = []
    all_dict = {}
    elo_change_list = []
    for game in history_raw:
        gameresult_ranked_west = game["playersData"][0]["gameResult"]
        gameresult_ranked_east = game["playersData"][2]["gameResult"]
        playerids_ranked_west = [game["playersData"][0]["playerId"], game["playersData"][1]["playerId"]]
        playerids_ranked_east = [game["playersData"][2]["playerId"], game["playersData"][3]["playerId"]]
        masterminds_ranked_west = [game["playersData"][0]["legion"], game["playersData"][1]["legion"]]
        masterminds_ranked_east = [game["playersData"][2]["legion"], game["playersData"][3]["legion"]]
        elo_change_ranked_west = game["playersData"][0]["eloChange"]
        elo_change_ranked_east = game["playersData"][2]["eloChange"]
        gameelo_list.append(game["gameElo"])
        if (playerid2 != 'all') or (playerid2 == "all" and mm2 != "" and mm2 != "All") or (playerid2 == "all" and mm1 != "" and mm2 == ""):
            for i, x in enumerate(playerids_ranked_west):
                if (x == playerid and (mm1 == masterminds_ranked_west[i] or mm1 == "")) or (playerid == "all" and x != playerid2 and (mm1 == masterminds_ranked_west[i] or mm1 == "")):
                    if option == 'against':
                        if (playerids_ranked_east[0] == playerid2 or playerid2 == 'all') and (mm2 == masterminds_ranked_east[0] or mm2 == ""):
                            patches_list.append(game["version"])
                            elo_change_list.append(elo_change_ranked_west)
                            game_count += 1
                            if gameresult_ranked_west == 'won':
                                win_count += 1
                        elif (playerids_ranked_east[1] == playerid2 or playerid2 == 'all') and (mm2 == masterminds_ranked_east[1] or mm2 == ""):
                            patches_list.append(game["version"])
                            elo_change_list.append(elo_change_ranked_west)
                            game_count += 1
                            if gameresult_ranked_west == 'won':
                                win_count += 1
                    elif option == 'with':
                        if i == 0:
                            teammate = 1
                        else:
                            teammate = 0
                        if type(playername) != list and type(playername2) != list and playername.lower() == playername2.lower():
                            if (playerids_ranked_west[0] == playerid2) and (mm2 == masterminds_ranked_west[0] or mm2 == ""):
                                patches_list.append(game["version"])
                                elo_change_list.append(elo_change_ranked_west)
                                game_count += 1
                                if gameresult_ranked_west == 'won':
                                    win_count += 1
                            elif (playerids_ranked_west[1] == playerid2) and (mm2 == masterminds_ranked_west[1] or mm2 == ""):
                                patches_list.append(game["version"])
                                elo_change_list.append(elo_change_ranked_west)
                                game_count += 1
                                if gameresult_ranked_west == 'won':
                                    win_count += 1
                        else:
                            if (playerids_ranked_west[teammate] == playerid2 or playerid2 == 'all') and (mm2 == masterminds_ranked_west[teammate] or mm2 == ""):
                                patches_list.append(game["version"])
                                elo_change_list.append(elo_change_ranked_west)
                                game_count += 1
                                if gameresult_ranked_west == 'won':
                                    win_count += 1
            for i, x in enumerate(playerids_ranked_east):
                if (x == playerid and (mm1 == masterminds_ranked_east[i] or mm1 == "")) or (playerid == "all" and x != playerid2 and (mm1 == masterminds_ranked_east[i] or mm1 == "")):
                    if option == 'against':
                        if (playerids_ranked_west[0] == playerid2 or playerid2 == 'all') and (mm2 == masterminds_ranked_west[0] or mm2 == ""):
                            patches_list.append(game["version"])
                            elo_change_list.append(elo_change_ranked_east)
                            game_count += 1
                            if gameresult_ranked_east == 'won':
                                win_count += 1
                        elif (playerids_ranked_west[1] == playerid2 or playerid2 == 'all') and (mm2 == masterminds_ranked_west[1] or mm2 == ""):
                            patches_list.append(game["version"])
                            elo_change_list.append(elo_change_ranked_east)
                            game_count += 1
                            if gameresult_ranked_east == 'won':
                                win_count += 1
                    elif option == 'with':
                        if i == 0:
                            teammate = 1
                        else:
                            teammate = 0
                        if type(playername) != list and type(playername2) != list and playername.lower() == playername2.lower():
                            if (playerids_ranked_east[0] == playerid2) and (mm2 == masterminds_ranked_east[0] or mm2 == ""):
                                patches_list.append(game["version"])
                                elo_change_list.append(elo_change_ranked_east)
                                game_count += 1
                                if gameresult_ranked_east == 'won':
                                    win_count += 1
                            elif (playerids_ranked_east[1] == playerid2) and (mm2 == masterminds_ranked_east[1] or mm2 == ""):
                                patches_list.append(game["version"])
                                elo_change_list.append(elo_change_ranked_east)
                                game_count += 1
                                if gameresult_ranked_east == 'won':
                                    win_count += 1
                        else:
                            if (playerids_ranked_east[teammate] == playerid2 or playerid2 == 'all') and (mm2 == masterminds_ranked_east[teammate] or mm2 == ""):
                                patches_list.append(game["version"])
                                elo_change_list.append(elo_change_ranked_east)
                                game_count += 1
                                if gameresult_ranked_east == 'won':
                                    win_count += 1
        elif playerid != "all" and playerid2 == "all" and mm1 == "" and mm2 == "":
            patches_list.append(game["version"])
            for i, x in enumerate(playerids_ranked_west):
                if x == playerid:
                    if option == 'against':
                        if playerids_ranked_east[0] in all_dict:
                            all_dict[playerids_ranked_east[0]]["Count"] += 1
                            all_dict[playerids_ranked_east[0]]["EloChange"] += elo_change_ranked_west
                            if gameresult_ranked_west == "won":
                                all_dict[playerids_ranked_east[0]]["Wins"] += 1
                        else:
                            all_dict[playerids_ranked_east[0]] = {"Count": 1, "Wins": 0, "EloChange": elo_change_ranked_west, "playername": game["playersData"][2]["playerName"]}
                            if gameresult_ranked_west == "won":
                                all_dict[playerids_ranked_east[0]]["Wins"] += 1
                        if playerids_ranked_east[1] in all_dict:
                            all_dict[playerids_ranked_east[1]]["Count"] += 1
                            all_dict[playerids_ranked_east[1]]["EloChange"] += elo_change_ranked_west
                            if gameresult_ranked_west == "won":
                                all_dict[playerids_ranked_east[1]]["Wins"] += 1
                        else:
                            all_dict[playerids_ranked_east[1]] = {"Count": 1, "Wins": 0, "EloChange": elo_change_ranked_west, "playername": game["playersData"][3]["playerName"]}
                            if gameresult_ranked_west == "won":
                                all_dict[playerids_ranked_east[1]]["Wins"] += 1
                    elif option == 'with':
                        if playerids_ranked_west[0] != playerid:
                            if playerids_ranked_west[0] in all_dict:
                                all_dict[playerids_ranked_west[0]]["Count"] += 1
                                all_dict[playerids_ranked_west[0]]["EloChange"] += elo_change_ranked_west
                                if gameresult_ranked_west == "won":
                                    all_dict[playerids_ranked_west[0]]["Wins"] += 1
                            else:
                                all_dict[playerids_ranked_west[0]] = {"Count": 1, "Wins": 0,"EloChange": elo_change_ranked_west, "playername": game["playersData"][0]["playerName"]}
                                if gameresult_ranked_west == "won":
                                    all_dict[playerids_ranked_west[0]]["Wins"] += 1
                        elif playerids_ranked_west[1] != playerid:
                            if playerids_ranked_west[1] in all_dict:
                                all_dict[playerids_ranked_west[1]]["Count"] += 1
                                all_dict[playerids_ranked_west[1]]["EloChange"] += elo_change_ranked_west
                                if gameresult_ranked_west == "won":
                                    all_dict[playerids_ranked_west[1]]["Wins"] += 1
                            else:
                                all_dict[playerids_ranked_west[1]] = {"Count": 1, "Wins": 0,"EloChange": elo_change_ranked_west, "playername": game["playersData"][1]["playerName"]}
                                if gameresult_ranked_west == "won":
                                    all_dict[playerids_ranked_west[1]]["Wins"] += 1
            for i, x in enumerate(playerids_ranked_east):
                if x == playerid:
                    if option == 'against':
                        if playerids_ranked_west[0] in all_dict:
                            all_dict[playerids_ranked_west[0]]["Count"] += 1
                            all_dict[playerids_ranked_west[0]]["EloChange"] += elo_change_ranked_east
                            if gameresult_ranked_east == "won":
                                all_dict[playerids_ranked_west[0]]["Wins"] += 1
                        else:
                            all_dict[playerids_ranked_west[0]] = {"Count": 1, "Wins": 0, "EloChange": elo_change_ranked_east, "playername": game["playersData"][0]["playerName"]}
                            if gameresult_ranked_east == "won":
                                all_dict[playerids_ranked_west[0]]["Wins"] += 1
                        if playerids_ranked_west[1] in all_dict:
                            all_dict[playerids_ranked_west[1]]["Count"] += 1
                            all_dict[playerids_ranked_west[1]]["EloChange"] += elo_change_ranked_east
                            if gameresult_ranked_east == "won":
                                all_dict[playerids_ranked_west[1]]["Wins"] += 1
                        else:
                            all_dict[playerids_ranked_west[1]] = {"Count": 1, "Wins": 0, "EloChange": elo_change_ranked_east, "playername": game["playersData"][1]["playerName"]}
                            if gameresult_ranked_east == "won":
                                all_dict[playerids_ranked_west[1]]["Wins"] += 1
                    elif option == 'with':
                        if playerids_ranked_east[0] != playerid:
                            if playerids_ranked_east[0] in all_dict:
                                all_dict[playerids_ranked_east[0]]["Count"] += 1
                                all_dict[playerids_ranked_east[0]]["EloChange"] += elo_change_ranked_east
                                if gameresult_ranked_east == "won":
                                    all_dict[playerids_ranked_east[0]]["Wins"] += 1
                            else:
                                all_dict[playerids_ranked_east[0]] = {"Count": 1, "Wins": 0,"EloChange": elo_change_ranked_east, "playername": game["playersData"][2]["playerName"]}
                                if gameresult_ranked_east == "won":
                                    all_dict[playerids_ranked_east[0]]["Wins"] += 1
                        elif playerids_ranked_east[1] != playerid:
                            if playerids_ranked_east[1] in all_dict:
                                all_dict[playerids_ranked_east[1]]["Count"] += 1
                                all_dict[playerids_ranked_east[1]]["EloChange"] += elo_change_ranked_east
                                if gameresult_ranked_east == "won":
                                    all_dict[playerids_ranked_east[1]]["Wins"] += 1
                            else:
                                all_dict[playerids_ranked_east[1]] = {"Count": 1, "Wins": 0,"EloChange": elo_change_ranked_east, "playername": game["playersData"][3]["playerName"]}
                                if gameresult_ranked_east == "won":
                                    all_dict[playerids_ranked_east[1]]["Wins"] += 1
        else:
            patches_list.append(game["version"])
            for i, x in enumerate(playerids_ranked_west):
                if (x == playerid or playerid == "all") and (masterminds_ranked_west[i] == mm1 or mm1 == "" or mm1 == "All"):
                    if option == 'against':
                        if masterminds_ranked_east[0] in all_dict:
                            all_dict[masterminds_ranked_east[0]]["Count"] += 1
                            all_dict[masterminds_ranked_east[0]]["EloChange"] += elo_change_ranked_west
                            if gameresult_ranked_west == "won":
                                all_dict[masterminds_ranked_east[0]]["Wins"] += 1
                        else:
                            all_dict[masterminds_ranked_east[0]] = {"Count": 1, "Wins": 0, "EloChange": elo_change_ranked_west}
                            if gameresult_ranked_west == "won":
                                all_dict[masterminds_ranked_east[0]]["Wins"] += 1
                        if masterminds_ranked_east[1] == masterminds_ranked_east[0]:
                            continue
                        if masterminds_ranked_east[1] in all_dict:
                            all_dict[masterminds_ranked_east[1]]["Count"] += 1
                            all_dict[masterminds_ranked_east[1]]["EloChange"] += elo_change_ranked_west
                            if gameresult_ranked_west == "won":
                                all_dict[masterminds_ranked_east[1]]["Wins"] += 1
                        else:
                            all_dict[masterminds_ranked_east[1]] = {"Count": 1, "Wins": 0, "EloChange": elo_change_ranked_west}
                            if gameresult_ranked_west == "won":
                                all_dict[masterminds_ranked_east[1]]["Wins"] += 1
                    elif option == 'with':
                        if i == 0: teammate = 1
                        else: teammate = 0
                        if masterminds_ranked_west[teammate] in all_dict:
                            all_dict[masterminds_ranked_west[teammate]]["Count"] += 1
                            all_dict[masterminds_ranked_west[teammate]]["EloChange"] += elo_change_ranked_west
                            if gameresult_ranked_west == "won":
                                all_dict[masterminds_ranked_west[teammate]]["Wins"] += 1
                        else:
                            all_dict[masterminds_ranked_west[teammate]] = {"Count": 1, "Wins": 0,"EloChange": elo_change_ranked_west}
                            if gameresult_ranked_west == "won":
                                all_dict[masterminds_ranked_west[teammate]]["Wins"] += 1
            for i, x in enumerate(playerids_ranked_east):
                if (x == playerid or playerid == "all") and (masterminds_ranked_east[i] == mm1 or mm1 == "" or mm1 == "All"):
                    if option == 'against':
                        if masterminds_ranked_west[0] in all_dict:
                            all_dict[masterminds_ranked_west[0]]["Count"] += 1
                            all_dict[masterminds_ranked_west[0]]["EloChange"] += elo_change_ranked_east
                            if gameresult_ranked_east == "won":
                                all_dict[masterminds_ranked_west[0]]["Wins"] += 1
                        else:
                            all_dict[masterminds_ranked_west[0]] = {"Count": 1, "Wins": 0, "EloChange": elo_change_ranked_east}
                            if gameresult_ranked_east == "won":
                                all_dict[masterminds_ranked_west[0]]["Wins"] += 1
                        if masterminds_ranked_west[1] == masterminds_ranked_west[0]:
                            continue
                        if masterminds_ranked_west[1] in all_dict:
                            all_dict[masterminds_ranked_west[1]]["Count"] += 1
                            all_dict[masterminds_ranked_west[1]]["EloChange"] += elo_change_ranked_east
                            if gameresult_ranked_east == "won":
                                all_dict[masterminds_ranked_west[1]]["Wins"] += 1
                        else:
                            all_dict[masterminds_ranked_west[1]] = {"Count": 1, "Wins": 0, "EloChange": elo_change_ranked_east}
                            if gameresult_ranked_east == "won":
                                all_dict[masterminds_ranked_west[1]]["Wins"] += 1
                    elif option == 'with':
                        if i == 0: teammate = 1
                        else: teammate = 0
                        if playerids_ranked_east[teammate] != playerid:
                            if masterminds_ranked_east[teammate] in all_dict:
                                all_dict[masterminds_ranked_east[teammate]]["Count"] += 1
                                all_dict[masterminds_ranked_east[teammate]]["EloChange"] += elo_change_ranked_east
                                if gameresult_ranked_east == "won":
                                    all_dict[masterminds_ranked_east[teammate]]["Wins"] += 1
                            else:
                                all_dict[masterminds_ranked_east[teammate]] = {"Count": 1, "Wins": 0,"EloChange": elo_change_ranked_east}
                                if gameresult_ranked_east == "won":
                                    all_dict[masterminds_ranked_east[teammate]]["Wins"] += 1
    patches = list(dict.fromkeys(patches_list))
    new_patches = []
    for x in patches:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches = list(dict.fromkeys(new_patches))
    patches = sorted(patches, key=lambda x: int(x.split(".")[0] + x.split(".")[1]), reverse=True)
    avg_gameelo = round(sum(gameelo_list) / len(gameelo_list))
    if type(playername) == list:
        if playername[0] != 'all':
            suffix = "'s"
        else:
            suffix = ""
        output_string_1 = playername[0].capitalize() + suffix + " " + mm1 + " winrate " + option + " "
    else:
        output_string_1 = playername.capitalize() + "'s winrate " + option + " "
    if type(playername2) == list:
        if playername2[0] != 'all':
            suffix = "'s"
        else:
            suffix = ""
        if mm2 == "All":
            mm2_str = "Masterminds"
        else:
            mm2_str = mm2
        output_string_2 = playername2[0].capitalize() + suffix + " " + mm2_str
    else:
        output_string_2 = playername2.capitalize()
    if playerid == "all":
        avatar = "https://cdn.legiontd2.com/icons/Items/"+mm1+".png"
    else:
        avatar = "https://cdn.legiontd2.com/" + apicall_getprofile(playerid)['avatarUrl']
    output = ""
    longest_text = 0
    if all_dict:
        reverse = True
        if sort == "EloChange+":
            sort = "EloChange"
            reverse = True
        elif sort == "EloChange-":
            sort = "EloChange"
            reverse = False
        newIndex = sorted(all_dict, key=lambda x: all_dict[x][sort], reverse=reverse)
        all_dict = {k: all_dict[k] for k in newIndex}
        final_output = ""
        for indx, player in enumerate(all_dict):
            if indx == 6: break
            if all_dict[player]["EloChange"] > 0:
                elo_prefix = "+"
            else:
                elo_prefix = ""
            if mm2 != "All":
                p_name = all_dict[player]["playername"]
            else:
                p_name = player
            win_lose_text = str(all_dict[player]["Wins"]) + 'W - ' + str(all_dict[player]["Count"] - all_dict[player]["Wins"]) + 'L**  ('
            output += "**"+p_name + ": " + win_lose_text + str(round(all_dict[player]["Wins"] / all_dict[player]["Count"] * 100, 1)) + '% ' + elo_prefix + str(all_dict[player]["EloChange"]) + " Elo)\n"
    else:
        if len(elo_change_list) > 0:
            sum_elo = sum(elo_change_list)
            if sum_elo > 0:
                string_pm = "+"
            else:
                string_pm = ""
            elo_change_sum = ", Elo change: " + string_pm + str(sum_elo)
        else:
            elo_change_sum = ""
        try:
            winrate = round(win_count / game_count * 100, 2)
        except ZeroDivisionError as e:
            print(e)
            return "No games found."
        output += "**"+str(win_count) + 'W - ' + str(game_count - win_count) + 'L (' + str(winrate) + '% winrate' + elo_change_sum + ')**'
    embed = discord.Embed(color=0x21eb1e)
    embed.add_field(name='(From ' + str(games) + ' ranked games, avg. elo: ' + str(avg_gameelo) + " " + get_ranked_emote(avg_gameelo) + ")", value=output)
    embed.set_author(name=output_string_1 + output_string_2, icon_url=avatar)
    embed.set_footer(text='Patches: ' + ', '.join(patches))
    return embed
        
def apicall_elcringo(playername, games, patch, min_elo, option, sort="date"):
    if playername.lower() == 'all':
        playerid = 'all'
        suffix = ''
    elif 'nova cup' in playername:
        suffix = ''
        playerid = playername
    else:
        playerid = apicall_getid(playername)
        if playerid == 0:
            return 'Player ' + playername + ' not found.'
        if playerid == 1:
            return 'API limit reached, you can still use "all" commands.'
        suffix = "'s"
    count = 0
    save_count_list = []
    save_count_pre10_list = []
    save_count = 0
    save_count_pre10 = 0
    ending_wave_list = []
    worker_10_list = []
    income_10_list = []
    mythium_list = []
    mythium_pre10_list = []
    mythium_list_pergame = []
    kinghp_list = []
    kinghp_enemy_list = []
    leaks_list = []
    leaks_pre10_list = []
    gameelo_list = []
    try:
        history_raw = apicall_getmatchistory(playerid, games, min_elo, patch, sort_by=sort, earlier_than_wave10=True)
    except TypeError as e:
        print(e)
        return playername + ' has not played enough games.'
    if type(history_raw) == str:
        return history_raw
    games = len(history_raw)
    if games == 0:
        return 'No games found.'
    if 'nova cup' in playerid:
        playerid = 'all'
    patches = []
    print('starting elcringo command...')
    for game in history_raw:
        patches.append(game["version"])
        ending_wave_list.append(game["endingWave"])
        gameelo_list.append(game["gameElo"])
        mythium_list_pergame.clear()
        for i, player in enumerate(game["playersData"]):
            if player["playerId"] == playerid or playerid == 'all':
                for n, s in enumerate(player["mercenariesSentPerWave"]):
                    small_send = 0
                    send = count_mythium(player["mercenariesSentPerWave"][n]) + len(player["kingUpgradesPerWave"][n]) * 20
                    mythium_list_pergame.append(send)
                    if n <= 9:
                        if player["workersPerWave"][n] > 5:
                            small_send = (player["workersPerWave"][n] - 5) / 4 * 20
                        if send <= small_send and option == "Yes":
                            save_count_pre10 += 1
                        elif send == 0 and option == "No":
                            save_count_pre10 += 1
                    elif n > 9:
                        if game["version"].startswith('v11') or game["version"].startswith('v9'):
                            worker_adjusted = player["workersPerWave"][n]
                        elif game["version"].startswith('v10'):
                            worker_adjusted = player["workersPerWave"][n] * (pow((1 + 6 / 100), n+1))
                        small_send = worker_adjusted / 4 * 20
                        if send <= small_send and option == "Yes":
                            save_count += 1
                        elif send == 0 and option == "No":
                            save_count += 1
                mythium_list.append(sum(mythium_list_pergame))
                mythium_pre10 = 0
                for counter, myth in enumerate(mythium_list_pergame):
                    mythium_pre10 += myth
                    if counter == 9:
                        break
                mythium_pre10_list.append(mythium_pre10)
                try:
                    worker_10_list.append(player["workersPerWave"][9])
                    income_10_list.append(player["incomePerWave"][9])
                except Exception:
                    pass
                leak_amount = 0
                leak_pre10_amount = 0
                for y in range(game["endingWave"]):
                    if len(player["leaksPerWave"][y]) > 0:
                        p = calc_leak(player["leaksPerWave"][y], y)
                        leak_amount += p
                        if y < 10:
                            leak_pre10_amount += p
                leaks_list.append(leak_amount/game["endingWave"])
                leaks_pre10_list.append(leak_pre10_amount/10)
                try:
                    if i == 0 or 1:
                        kinghp_list.append(game["leftKingPercentHp"][9])
                        kinghp_enemy_list.append(game["rightKingPercentHp"][9])
                    else:
                        kinghp_list.append(game["rightKingPercentHp"][9])
                        kinghp_enemy_list.append(game["leftKingPercentHp"][9])
                except Exception:
                    pass
            mythium_list_pergame.clear()
        save_count_pre10_list.append(save_count_pre10)
        save_count_list.append(save_count)
        save_count_pre10 = 0
        save_count = 0
    new_patches = []
    for x in patches:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches = list(dict.fromkeys(new_patches))
    patches = sorted(patches, key=lambda x: int(x.split(".")[0] + x.split(".")[1]), reverse=True)
    waves_post10 = round(sum(ending_wave_list) / len(ending_wave_list), 2) - 10
    if playerid == 'all':
        saves_pre10 = round(sum(save_count_pre10_list) / len(save_count_pre10_list)/4, 2)
        saves_post10 = round(sum(save_count_list) / len(save_count_list)/4, 2)
    else:
        saves_pre10 = round(sum(save_count_pre10_list) / len(save_count_pre10_list), 2)
        saves_post10 = round(sum(save_count_list) / len(save_count_list), 2)
    mythium_pre10 = round(sum(mythium_pre10_list) / len(mythium_pre10_list))
    mythium = round(sum(mythium_list) / len(mythium_list))
    leaks_total = round(sum(leaks_list) / len(leaks_list), 1)
    leaks_pre10_total = round(sum(leaks_pre10_list) / len(leaks_pre10_list), 1)
    king_hp_10 = sum(kinghp_list) / len(kinghp_list)
    king_hp_enemy_10 = sum(kinghp_enemy_list) / len(kinghp_enemy_list)
    if playername == "all" or "nova cup" in playername:
        king_hp_10 = (king_hp_10 + king_hp_enemy_10) / 2
        string2 = 'King hp on 10: ' + str(round(king_hp_10 * 100, 2))+'%\n'
    else:
        string2 = 'King hp on 10: ' + str(round(king_hp_10 * 100, 2)) + '%, Enemy King: '+str(round(king_hp_enemy_10*100,2))+'%\n'
    avg_gameelo = round(sum(gameelo_list) / len(gameelo_list))
    if playerid == "all":
        playername = "All"
        avatar = "https://cdn.legiontd2.com/icons/Ogre.png"
    else:
        profile = apicall_getprofile(playerid)
        avatar = "https://cdn.legiontd2.com/" + profile['avatarUrl']
        playername = profile["playerName"]
    embed = discord.Embed(color=0x4565d9, description='(From ' + str(games) + ' ranked games, avg. elo: ' + str(avg_gameelo) + " " + get_ranked_emote(avg_gameelo) + ")\n\n"+
                          '**Saves first 10:** ' + str(saves_pre10) + '/10 waves (' + str(round(saves_pre10 / 10 * 100, 2)) + '%)\n'+
                          '**Saves after 10:** ' + str(saves_post10)+'/' + str(round(waves_post10, 2)) + ' waves (' + str(round(saves_post10 / waves_post10 * 100, 2)) + '%)\n'+
                          '**Worker on 10:** ' + str(round(sum(worker_10_list) / len(worker_10_list), 2))+"\n"+
                          '**Leaks:** ' + str(leaks_total) + "% (First 10: "+str(leaks_pre10_total)+"%)\n"+
                          '**Income on 10:** ' + str(round(sum(income_10_list) / len(income_10_list), 1))+"\n"+
                          '**Mythium sent:** ' + str(mythium) + ' (Pre 10: '+str(mythium_pre10)+', Post 10: '+str(mythium-mythium_pre10)+')\n'+
                          '**Game elo:** ' + str(round(avg_gameelo)))
    embed.set_author(name=playername + suffix + " elcringo stats", icon_url=avatar)
    embed.set_footer(text='Patches: ' + ', '.join(patches))
    return embed

def apicall_jules(playername, unit, games, min_elo, patch, sort="date", mastermind = "all", spell = "all"):
    if "," in unit:
        unit = unit.split(",")
    else:
        unit = [unit]
    mms = ['LockIn', 'Greed', 'Redraw', 'Yolo', 'Fiesta', 'CashOut', 'Castle', 'Cartel', 'Chaos', 'Champion', 'DoubleLockIn', 'Kingsguard']
    if mastermind != "all":
        for x in mms:
            if mastermind.lower() == x.lower():
                mastermind = x
                break
        else:
            return "Mastermind not found."
    if spell != "all":
        spell_list = []
        with open('Files/spells.json', 'r') as f:
            spells_json = json.load(f)
        for s_js in spells_json:
            string = s_js["_id"]
            string = string.replace('_powerup_id', '')
            string = string.replace('_spell_damage', '')
            string = string.replace("_", " ")
            spell_list.append(string)
        spell_list.append("taxed allowance")
        if spell != "all":
            spell = spell.lower()
            if spell in slang:
                spell = slang.get(spell)
            if spell not in spell_list:
                close_matches = difflib.get_close_matches(spell, spell_list)
                if len(close_matches) > 0:
                    spell = close_matches[0]
                else:
                    return spell + " spell not found."
    unit_list = []
    with open('Files/units.json', 'r') as f:
        units_json = json.load(f)
    for u_js in units_json:
        if u_js["totalValue"] != '':
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
    novacup = False
    if playername == 'all':
        playerid = 'all'
    elif 'nova cup' in playername:
        novacup = True
        playerid = playername
    else:
        playerid = apicall_getid(playername)
        if playerid == 0:
            return 'Player ' + playername + ' not found.'
        if playerid == 1:
            return 'API limit reached, you can still use "all" commands.'
        avatar = apicall_getprofile(playerid)['avatarUrl']
    history_raw = apicall_getmatchistory(playerid, games, min_elo, patch, sort_by=sort, earlier_than_wave10=True)
    if type(history_raw) == str:
        return history_raw
    if len(history_raw) == 0:
        return 'No games found.'
    games = len(history_raw)
    if novacup:
        playerid = 'all'
    new_patches = []
    gameelo_list = []
    playerelo_list = []
    excluded_buffs = ["hero", "vampire", "magician", "protector"]
    count = 0
    occurrence_count = 0
    win_count = 0
    patches = []
    print('Starting jules command...')
    for game in history_raw:
        patches.append(game["version"])
        gameelo_list.append(game["gameElo"])
        for player in game["playersData"]:
            if player["playerId"] == playerid or playerid == "all":
                expected = len(unit)
                current = 0
                fighter_list = player["fighters"].lower()
                if mastermind != "all":
                    expected += 1
                    if mastermind == player["legion"]:
                        current += 1
                if spell != "all" and player["chosenSpellLocation"] != "-1|-1" and spell.lower() == player["chosenSpell"].lower() and spell.lower() not in excluded_buffs:
                    expected += 1
                    for pos in player["buildPerWave"][-1]:
                        if pos.split(":")[1] == player["chosenSpellLocation"] and pos.split(":")[0].replace("_unit_id", "").replace("_", " ") in unit:
                            spell = player["chosenSpell"]
                            current += 1
                            for un in unit:
                                if un.lower() in fighter_list:
                                    current += 1
                else:
                    if spell != "all":
                        expected += 1
                        if spell.lower() == player["chosenSpell"].lower():
                            spell = player["chosenSpell"]
                            current += 1
                    for un in unit:
                        if un.lower() in fighter_list:
                            current += 1
                if current == expected:
                    occurrence_count += 1
                    playerelo_list.append(player["overallElo"])
                    if player["gameResult"] == "won":
                        win_count += 1
        count += 1
    if occurrence_count == 0:
        return "No occurences found."
    for x in patches:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches = list(dict.fromkeys(new_patches))
    patches = sorted(patches, key=lambda x: int(x.split(".")[0] + x.split(".")[1]), reverse=True)
    avg_gameelo = round(sum(gameelo_list) / len(gameelo_list))
    mode = 'RGB'
    colors = (49, 51, 56)
    im = PIL.Image.new(mode=mode, size=(1000, 300), color=colors)
    I1 = ImageDraw.Draw(im)
    ttf = 'Files/RobotoCondensed-Regular.ttf'
    myFont_small = ImageFont.truetype(ttf, 20)
    myFont = ImageFont.truetype(ttf, 25)
    myFont_title = ImageFont.truetype(ttf, 30)
    jules_url = "https://overlay.drachbot.site/emotes/JULES.png"
    if playername == 'all' or 'nova cup' in playername:
        jules_response = requests.get(jules_url)
        jules_image = Image.open(BytesIO(jules_response.content))
        im.paste(jules_image.resize((64, 64)), (10, 10), mask=jules_image.resize((64, 64)))
        string = ''
    else:
        string = "'s"
        av_image = get_icons_image("avatar", avatar)
        gold_border = Image.open('Files/gold_64.png')
        if im_has_alpha(np.array(av_image)):
            im.paste(av_image, (10, 10), mask=av_image)
        else:
            im.paste(av_image, (10, 10))
        im.paste(gold_border, (10, 10), mask=gold_border)
    I1.text((80, 10), str(playername.capitalize()) + string + " JULES stats (From " + str(games) + " ranked games, Avg elo: " + str(avg_gameelo) + ")", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    I1.text((80, 50), 'Patches: ' + ', '.join(patches), font=myFont_small, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    jules_response = requests.get(jules_url)
    jules_image = Image.open(BytesIO(jules_response.content))
    im.paste(jules_image.resize((64,64)), (10, 80), mask=jules_image.resize((64,64)))
    offset = 80
    for i, x in enumerate(unit):
        I1.text((offset*(i+1)-5, 100), "+", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
        im.paste(get_icons_image("icon", x), (10+offset*(i+1), 80))
    if mastermind != "all":
        i += 1
        I1.text((offset * (i + 1) - 5, 100), "+", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
        im.paste(get_icons_image("legion", mastermind), (10 + offset * (i + 1), 80))
    if spell != "all":
        i += 1
        I1.text((offset * (i + 1) - 5, 100), "+", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
        im.paste(get_icons_image("icon", spell), (10 + offset * (i + 1), 80))
    I1.text((10, 160), 'Games: ' + str(occurrence_count) + ', Win: '+str(win_count)+', Lose: '+str(occurrence_count-win_count), font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    if round(win_count/occurrence_count*100,1) < 50:
        wr_rgb = (255,0,0)
    else: wr_rgb = (0,255,0)
    I1.text((10, 200),'Winrate: ', font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    I1.text((115, 200),str(round(win_count/occurrence_count*100,1))+"%", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=wr_rgb)
    I1.text((10, 240), 'Appearance rate: ' + str(round(occurrence_count / games * 100, 1)) + "%", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    image_id = id_generator()
    im.save(shared_folder + image_id + '.png')
    return site + image_id + '.png'

def apicall_mmstats(playername, games, min_elo, patch, mastermind = 'All', sort="date"):
    novacup = False
    if playername == 'all':
        playerid = 'all'
    elif 'nova cup' in playername:
        novacup = True
        playerid = playername
    else:
        playerid = apicall_getid(playername)
        if playerid == 0:
            return 'Player ' + playername + ' not found.'
        if playerid == 1:
            return 'API limit reached, you can still use "all" commands.'
    if mastermind == 'All':
        mmnames_list = ['LockIn', 'Greed', 'Redraw', 'Yolo', 'Fiesta', 'CashOut', 'Castle', 'Cartel', 'Chaos', 'Champion', 'DoubleLockIn', 'Kingsguard', 'Megamind']
    elif mastermind == 'Megamind':
        mmnames_list = ['LockIn', 'Greed', 'Redraw', 'Yolo', 'Fiesta', 'CashOut', 'Castle', 'Cartel', 'Chaos', 'Champion', 'DoubleLockIn', 'Kingsguard']
    else:
        mmnames_list = [mastermind]
    masterminds_dict = {}
    for x in mmnames_list:
        masterminds_dict[x] = {"Count": 0, "Wins": 0, "Worker": 0, "Opener": {}, "Spell": {}, "Elo": 0, "Leaks": [], "PlayerIds": [], "ChampionUnit": {}}
    gameelo_list = []
    history_raw = apicall_getmatchistory(playerid, games, min_elo, patch, sort_by=sort, earlier_than_wave10=True)
    if type(history_raw) == str:
        return history_raw
    if len(history_raw) == 0:
        return 'No games found.'
    games = len(history_raw)
    if 'nova cup' in playerid:
        playerid = 'all'
    case_list = ['LockIn', 'Greed', 'Redraw', 'Yolo', 'Fiesta', 'CashOut', 'Castle', 'Cartel', 'Chaos', 'Champion', 'DoubleLockIn', 'Kingsguard']
    patches = set()
    megamind_count = 0
    print('Starting mmstats command...')
    for game in history_raw:
        if (game["version"].startswith('v10') or game["version"].startswith('v9')) and (mastermind == 'Megamind' or mastermind == 'Champion'):
            continue
        patches.add(game["version"])
        gameelo_list.append(game["gameElo"])
        match mastermind:
            case 'All' | 'Megamind':
                for player in game["playersData"]:
                    if player["playerId"] == playerid or playerid == "all":
                        if (game["version"].startswith('v10') or game["version"].startswith('v9')):
                            player["megamind"] = False
                        if player["megamind"] == True:
                            megamind_count += 1
                            if mastermind != "Megamind":
                                mastermind_current = 'Megamind'
                            else:
                                if player["legion"] == "Megamind": continue
                                mastermind_current = player["legion"]
                        else:
                            if player["legion"] == "Mastermind":
                                continue
                            if mastermind == "Megamind":
                                continue
                            mastermind_current = player["legion"]
                        masterminds_dict[mastermind_current]["Count"] += 1
                        if player["gameResult"] == 'won':
                            masterminds_dict[mastermind_current]["Wins"] += 1
                        try:
                            masterminds_dict[mastermind_current]["Worker"] += player["workersPerWave"][9]
                        except IndexError:
                            pass
                        masterminds_dict[mastermind_current]['Elo'] += player["overallElo"]
                        if ',' in player["firstWaveFighters"]:
                            string = player["firstWaveFighters"]
                            commas = string.count(',')
                            opener = string.split(',', commas)[commas]
                        else:
                            opener = player["firstWaveFighters"]
                        if player["chosenSpell"] not in masterminds_dict[mastermind_current]['Spell']:
                            masterminds_dict[mastermind_current]['Spell'][player["chosenSpell"]] = {"Count": 1, "Wins": 0}
                            if player["gameResult"] == 'won':
                                masterminds_dict[mastermind_current]['Spell'][player["chosenSpell"]]["Wins"] += 1
                        else:
                            masterminds_dict[mastermind_current]['Spell'][player["chosenSpell"]]["Count"] += 1
                            if player["gameResult"] == 'won':
                                masterminds_dict[mastermind_current]['Spell'][player["chosenSpell"]]["Wins"] += 1
                        if opener not in masterminds_dict[mastermind_current]['Opener']:
                            masterminds_dict[mastermind_current]['Opener'][opener] = {"Count": 1, "Wins": 0}
                            if player["gameResult"] == 'won':
                                masterminds_dict[mastermind_current]['Opener'][opener]["Wins"] += 1
                        else:
                            masterminds_dict[mastermind_current]['Opener'][opener]["Count"] += 1
                            if player["gameResult"] == 'won':
                                masterminds_dict[mastermind_current]['Opener'][opener]["Wins"] += 1
            case mastermind if mastermind in case_list:
                for player in game["playersData"]:
                    if (playerid == 'all' or player["playerId"] == playerid) and (mastermind == player["legion"]):
                        mastermind_current = player["legion"]
                        masterminds_dict[mastermind_current]["Count"] += 1
                        if player["gameResult"] == 'won':
                            masterminds_dict[mastermind_current]["Wins"] += 1
                        try:
                            masterminds_dict[mastermind_current]["Worker"] += player["workersPerWave"][9]
                        except IndexError:
                            pass
                        masterminds_dict[mastermind_current]['Elo'] += player["overallElo"]
                        if ',' in player["firstWaveFighters"]:
                            string = player["firstWaveFighters"]
                            commas = string.count(',')
                            opener = string.split(',', commas)[commas]
                        else:
                            opener = player["firstWaveFighters"]
                        if player["chosenSpell"] not in masterminds_dict[mastermind_current]['Spell']:
                            masterminds_dict[mastermind_current]['Spell'][player["chosenSpell"]] = {"Count": 1, "Wins": 0}
                            if player["gameResult"] == 'won':
                                masterminds_dict[mastermind_current]['Spell'][player["chosenSpell"]]["Wins"] += 1
                        else:
                            masterminds_dict[mastermind_current]['Spell'][player["chosenSpell"]]["Count"] += 1
                            if player["gameResult"] == 'won':
                                masterminds_dict[mastermind_current]['Spell'][player["chosenSpell"]]["Wins"] += 1
                        if opener not in masterminds_dict[mastermind_current]['Opener']:
                            masterminds_dict[mastermind_current]['Opener'][opener] = {"Count": 1, "Wins": 0}
                            if player["gameResult"] == 'won':
                                masterminds_dict[mastermind_current]['Opener'][opener]["Wins"] += 1
                        else:
                            masterminds_dict[mastermind_current]['Opener'][opener]["Count"] += 1
                            if player["gameResult"] == 'won':
                                masterminds_dict[mastermind_current]['Opener'][opener]["Wins"] += 1
    new_patches = []
    for x in patches:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches = list(dict.fromkeys(new_patches))
    patches = sorted(patches, key=lambda x: int(x.split(".")[0] + x.split(".")[1]), reverse=True)
    newIndex = sorted(masterminds_dict, key=lambda x: masterminds_dict[x]['Count'], reverse=True)
    masterminds_dict = {k: masterminds_dict[k] for k in newIndex}
    avg_gameelo = round(sum(gameelo_list)/len(gameelo_list))
    if novacup:
        playerid = playername
    match mastermind:
        case 'All':
            return create_image_stats(masterminds_dict, games, playerid, avg_gameelo, patches, mode="Mastermind")
        case mastermind if mastermind in case_list:
            return create_image_stats_specific(masterminds_dict, games, playerid, avg_gameelo, patches, mode="Mastermind", specific_value=mastermind)
        case 'Megamind':
            return create_image_stats(masterminds_dict, games, playerid, avg_gameelo, patches, "Mastermind", True, megamind_count)

def apicall_openstats(playername, games, min_elo, patch, sort="date", unit = "all"):
    unit_dict = {}
    unit = unit.lower()
    with open('Files/units.json', 'r') as f:
        units_json = json.load(f)
    for u_js in units_json:
        if u_js["totalValue"] != '':
            if u_js["unitId"] and int(u_js["totalValue"]) > 0:
                string = u_js["unitId"]
                string = string.replace('_', ' ')
                string = string.replace(' unit id', '')
                unit_dict[string] = {'Count': 0, 'Wins': 0, 'Worker': 0, 'OpenWith': {}, 'MMs': {}, 'Spells': {}}
    unit_dict['pack rat nest'] = {'Count': 0, 'Wins': 0, 'Worker': 0, 'OpenWith': {}, 'MMs': {}, 'Spells': {}}
    if unit != "all":
        if unit in slang:
            unit = slang.get(unit)
        if unit not in unit_dict:
            close_matches = difflib.get_close_matches(unit, list(unit_dict.keys()))
            if len(close_matches) > 0:
                unit = close_matches[0]
            else:
                return unit + " unit not found."
    novacup = False
    if playername == 'all':
        playerid = 'all'
    elif 'nova cup' in playername:
        novacup = True
        playerid = playername
    else:
        playerid = apicall_getid(playername)
        if playerid == 0:
            return 'Player ' + playername + ' not found.'
        if playerid == 1:
            return 'API limit reached, you can still use "all" commands.'
    try:
        history_raw = apicall_getmatchistory(playerid, games, min_elo, patch, sort_by=sort, earlier_than_wave10=True)
    except TypeError as e:
        print(e)
        return playername + ' has not played enough games.'
    if type(history_raw) == str:
        return history_raw
    if len(history_raw) == 0:
        return 'No games found.'
    games = len(history_raw)
    if 'nova cup' in playerid:
        playerid = 'all'
    patches = []
    gameelo_list = []
    count = 0
    print("starting openstats...")
    for game in history_raw:
        if game["endingWave"] < 4: continue
        patches.append(game["version"])
        gameelo_list.append(game["gameElo"])
        if playerid.lower() != 'all' and 'nova cup' not in playerid:
            for player in game["playersData"]:
                if player["playerId"] == playerid:
                    opener_ranked_raw = player["buildPerWave"][:4]
                    break
        else:
            opener_ranked_raw = []
            for i in range(4):
                opener_ranked_raw.extend(game["playersData"][i]["buildPerWave"][:4])
        opener_ranked = []
        for i, x in enumerate(opener_ranked_raw):
            opener_ranked.extend([[]])
            for v, y in enumerate(x):
                string = y.split('_unit_id:')
                opener_ranked[i].append(string[0].replace('_', ' '))
        if playerid.lower() != 'all' and 'nova cup' not in playerid:
            for player in game["playersData"]:
                if player["playerId"] == playerid:
                    s = set()
                    for x in range(4):
                        for y in opener_ranked[x]:
                            s.add(y)
                    for y in s:
                        try:
                            if y != opener_ranked[0][0]:
                                if y in unit_dict[opener_ranked[0][0]]['OpenWith']:
                                    unit_dict[opener_ranked[0][0]]['OpenWith'][y]['Count'] += 1
                                    if player["gameResult"] == 'won':
                                        unit_dict[opener_ranked[0][0]]['OpenWith'][y]['Wins'] += 1
                                else:
                                    unit_dict[opener_ranked[0][0]]['OpenWith'][y] = {'Count': 1, 'Wins': 0}
                                    if player["gameResult"] == 'won':
                                        unit_dict[opener_ranked[0][0]]['OpenWith'][y]['Wins'] += 1
                            else:
                                unit_dict[opener_ranked[0][0]]['Count'] += 1
                                if player["legion"] not in unit_dict[opener_ranked[0][0]]['MMs']:
                                    unit_dict[opener_ranked[0][0]]['MMs'][player["legion"]] = {'Count': 1, 'Wins': 0}
                                else:
                                    unit_dict[opener_ranked[0][0]]['MMs'][player["legion"]]['Count'] += 1
                                if player["chosenSpell"] not in unit_dict[opener_ranked[0][0]]['Spells']:
                                    unit_dict[opener_ranked[0][0]]['Spells'][player["chosenSpell"]] = {'Count': 1, 'Wins': 0}
                                else:
                                    unit_dict[opener_ranked[0][0]]['Spells'][player["chosenSpell"]]['Count'] += 1
                                unit_dict[opener_ranked[0][0]]['Worker'] += player["workersPerWave"][3]
                                if player["gameResult"] == 'won':
                                    unit_dict[opener_ranked[0][0]]['Wins'] += 1
                                    unit_dict[opener_ranked[0][0]]['MMs'][player["legion"]]['Wins'] += 1
                                    unit_dict[opener_ranked[0][0]]['Spells'][player["chosenSpell"]]['Wins'] += 1
                        except IndexError:
                            continue
        else:
            counter = 0
            for player in game["playersData"]:
                s = set()
                for x in range(counter, counter+4):
                    for y in opener_ranked[x]:
                        s.add(y)
                for y in s:
                    try:
                        i = 0
                        if y != opener_ranked[counter][0]:
                            if y in unit_dict[opener_ranked[counter][0]]['OpenWith']:
                                unit_dict[opener_ranked[counter][0]]['OpenWith'][y]['Count'] += 1
                                if player["gameResult"] == 'won':
                                    unit_dict[opener_ranked[counter][0]]['OpenWith'][y]['Wins'] += 1
                            else:
                                unit_dict[opener_ranked[counter][0]]['OpenWith'][y] = {'Count': 1, 'Wins': 0}
                                if player["gameResult"] == 'won':
                                    unit_dict[opener_ranked[counter][0]]['OpenWith'][y]['Wins'] += 1
                        else:
                            unit_dict[opener_ranked[counter][0]]['Count'] += 1
                            if player["legion"] not in unit_dict[opener_ranked[counter][0]]['MMs']:
                                unit_dict[opener_ranked[counter][0]]['MMs'][player["legion"]] = {'Count': 1,'Wins': 0}
                            else:
                                unit_dict[opener_ranked[counter][0]]['MMs'][player["legion"]]['Count'] += 1
                            if player["chosenSpell"] not in unit_dict[opener_ranked[counter][0]]['Spells']:
                                unit_dict[opener_ranked[counter][0]]['Spells'][player["chosenSpell"]] = {'Count': 1, 'Wins': 0}
                            else:
                                unit_dict[opener_ranked[counter][0]]['Spells'][player["chosenSpell"]]['Count'] += 1
                            unit_dict[opener_ranked[counter][0]]['Worker'] += player["workersPerWave"][3]
                            if player["gameResult"] == 'won':
                                unit_dict[opener_ranked[counter][0]]['Wins'] += 1
                                unit_dict[opener_ranked[counter][0]]['MMs'][player["legion"]]['Wins'] += 1
                                unit_dict[opener_ranked[counter][0]]['Spells'][player["chosenSpell"]]['Wins'] += 1
                    except IndexError:
                        continue
                counter += 4
    new_patches = []
    for x in patches:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches = list(dict.fromkeys(new_patches))
    patches = sorted(patches, key=lambda x: int(x.split(".")[0] + x.split(".")[1]), reverse=True)
    newIndex = sorted(unit_dict, key=lambda x: unit_dict[x]['Count'], reverse=True)
    unit_dict = {k: unit_dict[k] for k in newIndex}
    avgelo = round(sum(gameelo_list)/len(gameelo_list))
    if novacup:
        playerid = playername
    if unit == "all":
        return create_image_stats(unit_dict, games, playerid, avgelo, patches, mode="Open")
    else:
        return create_image_stats_specific(unit_dict, games, playerid, avgelo, patches, mode="Open", specific_value=unit)

def apicall_spellstats(playername, games, min_elo, patch, sort="date", spellname = "all"):
    spell_dict = {}
    spellname = spellname.lower()
    with open('Files/spells.json', 'r') as f:
        spells_json = json.load(f)
    for s_js in spells_json:
        string = s_js["_id"]
        string = string.replace('_', ' ')
        string = string.replace(' powerup id', '')
        string = string.replace(' spell damage', '')
        spell_dict[string] = {'Count': 0, 'Wins': 0, 'Worker': 0, 'Opener': {}, 'MMs': {}}
    spell_dict["taxed allowance"] = {'Count': 0, 'Wins': 0, 'Worker': 0, 'Opener': {}, 'MMs': {}}
    if spellname != "all":
        if spellname in slang:
            spellname = slang.get(spellname)
        if spellname not in spell_dict:
            close_matches = difflib.get_close_matches(spellname, list(spell_dict.keys()))
            if len(close_matches) > 0:
                spellname = close_matches[0]
            else:
                return spellname + " spell not found."
    novacup = False
    if playername == 'all':
        playerid = 'all'
    elif 'nova cup' in playername:
        novacup = True
        playerid = playername
    else:
        playerid = apicall_getid(playername)
        if playerid == 0:
            return 'Player ' + playername + ' not found.'
        if playerid == 1:
            return 'API limit reached, you can still use "all" commands.'
    try:
        history_raw = apicall_getmatchistory(playerid, games, min_elo, patch, sort_by=sort)
    except TypeError as e:
        print(e)
        return playername + ' has not played enough games.'
    if type(history_raw) == str:
        return history_raw
    if len(history_raw) == 0:
        return 'No games found.'
    games = len(history_raw)
    if 'nova cup' in playerid:
        playerid = 'all'
    patches = []
    gameelo_list = []
    print('Starting spellstats command...')
    for game in history_raw:
        patches.append(game["version"])
        gameelo_list.append(game["gameElo"])
        for player in game["playersData"]:
            if (player["playerId"] == playerid) or (playerid.lower() == 'all' or 'nova cup' in playerid):
                spell_name = player["chosenSpell"].lower()
                spell_dict[spell_name]["Count"] += 1
                if player["gameResult"] == "won":
                    spell_dict[spell_name]["Wins"] += 1
                spell_dict[spell_name]["Worker"] += player["workersPerWave"][9]
                if "," in player["firstWaveFighters"]:
                    opener_current = player["firstWaveFighters"].split(",")[-1]
                else:
                    opener_current = player["firstWaveFighters"]
                if opener_current in spell_dict[spell_name]["Opener"]:
                    spell_dict[spell_name]["Opener"][opener_current]["Count"] += 1
                    if player["gameResult"] == "won":
                        spell_dict[spell_name]["Opener"][opener_current]["Wins"] += 1
                else:
                    spell_dict[spell_name]["Opener"][opener_current] = {"Count": 1, "Wins": 0}
                    if player["gameResult"] == "won":
                        spell_dict[spell_name]["Opener"][opener_current]["Wins"] += 1
                if player["legion"] in spell_dict[spell_name]["MMs"]:
                    spell_dict[spell_name]["MMs"][player["legion"]]["Count"] += 1
                    if player["gameResult"] == "won":
                        spell_dict[spell_name]["MMs"][player["legion"]]["Wins"] += 1
                else:
                    spell_dict[spell_name]["MMs"][player["legion"]] = {"Count": 1, "Wins": 0}
                    if player["gameResult"] == "won":
                        spell_dict[spell_name]["MMs"][player["legion"]]["Wins"] += 1
    new_patches = []
    for x in patches:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches = list(dict.fromkeys(new_patches))
    patches = sorted(patches, key=lambda x: int(x.split(".")[0] + x.split(".")[1]), reverse=True)
    newIndex = sorted(spell_dict, key=lambda x: spell_dict[x]['Count'], reverse=True)
    spell_dict = {k: spell_dict[k] for k in newIndex}
    avgelo = round(sum(gameelo_list)/len(gameelo_list))
    if novacup:
        playerid = playername
    if spellname == "all":
        return create_image_stats(spell_dict, games, playerid, avgelo, patches, mode="Spell")
    else:
        return create_image_stats_specific(spell_dict, games, playerid, avgelo, patches, mode="Spell", specific_value=spellname)

def apicall_unitstats(playername, games, min_elo, patch, sort="date", unit = "all", min_cost = 0):
    unit_dict = {}
    unit = unit.lower()
    with open('Files/units.json', 'r') as f:
        units_json = json.load(f)
    for u_js in units_json:
        if u_js["totalValue"] != '':
            if u_js["unitId"] and int(u_js["totalValue"]) > min_cost: #and (u_js["sortOrder"].split(".")[1].endswith("U") or u_js["sortOrder"].split(".")[1].endswith("U2") or "neko" in u_js["unitId"]):
                string = u_js["unitId"]
                string = string.replace('_', ' ')
                string = string.replace(' unit id', '')
                if u_js["upgradesFrom"]:
                    string2 = u_js["upgradesFrom"][0]
                    string2 = string2.replace('_', ' ').replace(' unit id', '').replace('units ', '')
                else:
                    string2 = ""
                unit_dict[string] = {'Count': 0, 'Wins': 0, 'ComboUnit': {}, 'MMs': {}, 'Spells': {}, "upgradesFrom": string2}
    if min_cost <= 75:
        unit_dict['pack rat (footprints)'] = {'Count': 0, 'Wins': 0, 'ComboUnit': {}, 'MMs': {}, 'Spells': {}, "upgradesFrom": "looter"}
    if not unit_dict:
        return "No units found"
    if unit != "all":
        if unit in slang:
            unit = slang.get(unit)
        if unit not in unit_dict:
            close_matches = difflib.get_close_matches(unit, list(unit_dict.keys()))
            if len(close_matches) > 0:
                unit = close_matches[0]
            else:
                return unit + " unit not found."
    novacup = False
    if playername == 'all':
        playerid = 'all'
    elif 'nova cup' in playername:
        novacup = True
        playerid = playername
    else:
        playerid = apicall_getid(playername)
        if playerid == 0:
            return 'Player ' + playername + ' not found.'
        if playerid == 1:
            return 'API limit reached, you can still use "all" commands.'
    history_raw = apicall_getmatchistory(playerid, games, min_elo, patch, sort_by=sort, earlier_than_wave10=True)
    if type(history_raw) == str:
        return history_raw
    if len(history_raw) == 0:
        return 'No games found.'
    games = len(history_raw)
    if 'nova cup' in playerid:
        playerid = 'all'
    patches = []
    gameelo_list = []
    count = 0
    print("starting unitstats...")
    for game in history_raw:
        patches.append(game["version"])
        gameelo_list.append(game["gameElo"])
        for player in game["playersData"]:
            if player["playerId"] != playerid and playerid != "all": continue
            fighter_set = set(player["fighters"].lower().split(","))
            for fighter in fighter_set:
                if fighter == "" or fighter not in unit_dict: continue
                unit_dict[fighter]["Count"] += 1
                if player["chosenSpell"] in unit_dict[fighter]["Spells"]:
                    unit_dict[fighter]["Spells"][player["chosenSpell"]]["Count"] += 1
                else:
                    unit_dict[fighter]["Spells"][player["chosenSpell"]] = {"Count": 1, "Wins": 0}
                if player["legion"] in unit_dict[fighter]["MMs"]:
                    unit_dict[fighter]["MMs"][player["legion"]]["Count"] += 1
                else:
                    unit_dict[fighter]["MMs"][player["legion"]] = {"Count": 1, "Wins": 0}
                if player["gameResult"] == "won":
                    unit_dict[fighter]["Wins"] += 1
                    unit_dict[fighter]["MMs"][player["legion"]]["Wins"] += 1
                    unit_dict[fighter]["Spells"][player["chosenSpell"]]["Wins"] += 1
                for combo_unit in fighter_set:
                    if combo_unit == fighter or combo_unit == unit_dict[fighter]["upgradesFrom"]: continue
                    if combo_unit in unit_dict[fighter]["ComboUnit"]:
                        unit_dict[fighter]["ComboUnit"][combo_unit]["Count"] += 1
                    else:
                        unit_dict[fighter]["ComboUnit"][combo_unit] = {"Count": 1, "Wins": 0}
                    if player["gameResult"] == "won":
                        unit_dict[fighter]["ComboUnit"][combo_unit]["Wins"] += 1
    new_patches = []
    for x in patches:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches = list(dict.fromkeys(new_patches))
    patches = sorted(patches, key=lambda x: int(x.split(".")[0] + x.split(".")[1]), reverse=True)
    newIndex = sorted(unit_dict, key=lambda x: unit_dict[x]['Count'], reverse=True)
    unit_dict = {k: unit_dict[k] for k in newIndex}
    avgelo = round(sum(gameelo_list)/len(gameelo_list))
    if novacup:
        playerid = playername
    if unit == "all":
        return create_image_stats(unit_dict, games, playerid, avgelo, patches, mode="Unit")
    else:
        return create_image_stats_specific(unit_dict, games, playerid, avgelo, patches, mode="Unit", specific_value=unit)

def apicall_gameid_visualizer(gameid, start_wave=0):
    if start_wave > 21:
        return "Invalid wave number."
    elif start_wave < 0:
        return "Invalid wave number."
    image_ids = []
    image_link = ""
    if not Path(Path(shared_folder + gameid + "/")).is_dir():
        url = 'https://apiv2.legiontd2.com/games/byId/' + gameid + '?includeDetails=true'
        api_response = requests.get(url, headers=header)
        gamedata = json.loads(api_response.text)
        units_dict = json.load(open("Files/units.json"))
        if (gamedata == {'message': 'Internal server error'}) or (gamedata == {'err': 'Entry not found.'}):
            return "GameID not found. (Games that are not concluded or older than 1 year are not available in the API)"
        player_dict = {}
        for player in gamedata["playersData"]:
            player_dict[player["playerName"]] = {"avatar_url": apicall_getprofile(player["playerId"])["avatarUrl"],
                                                 "roll": player["rolls"].replace(" ", "").split(","), "legion": player["legion"], "elo": player["overallElo"],
                                                 "elo_change": player["eloChange"]}
        if start_wave != 0:
            waves = [start_wave-1]
        elif start_wave > gamedata["endingWave"] and start_wave != 0:
            return "Game ended on Wave " + str(gamedata["endingWave"])
        else:
            waves = range(gamedata["endingWave"])
        first = True
        for wave in waves:
            mode = 'RGB'
            colors = (30, 30, 30)
            x = 10
            y = 350
            box_size = 64
            line_width = 3
            offset = box_size + line_width
            im = PIL.Image.new(mode=mode, size=(20+offset*39, 1750), color=colors)
            horz_line = PIL.Image.new(mode="RGB", size=(box_size*9+line_width*10, line_width), color=(155, 155, 155))
            vert_line = PIL.Image.new(mode="RGB", size=(line_width, box_size*14+line_width*15), color=(155, 155, 155))
            I1 = ImageDraw.Draw(im)
            ttf = 'Files/RobotoCondensed-Regular.ttf'
            myFont_small = ImageFont.truetype(ttf, 40)
            myFont = ImageFont.truetype(ttf, 50)
            myFont_title = ImageFont.truetype(ttf, 60)
            y2 = 125
            im.paste(Image.open(open("Files/Waves/Wave"+str(wave+1)+".png", "rb")), (10,10))
            I1.text((80, 10), "Wave "+str(wave+1), font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0),fill=(255, 255, 255))
            if wave == 0:
                left_kinghp_change = 0
            elif gamedata["leftKingPercentHp"][wave-1] > gamedata["leftKingPercentHp"][wave]:
                left_kinghp_change = "-"+str(round((gamedata["leftKingPercentHp"][wave-1]-gamedata["leftKingPercentHp"][wave])*100, 1))
            else:
                left_kinghp_change = "+"+str(round((gamedata["leftKingPercentHp"][wave] - gamedata["leftKingPercentHp"][wave-1]) * 100, 1))
            if wave == 0:
                right_kinghp_change = 0
            elif gamedata["rightKingPercentHp"][wave-1] > gamedata["rightKingPercentHp"][wave]:
                right_kinghp_change = "-"+str(round((gamedata["rightKingPercentHp"][wave-1]-gamedata["rightKingPercentHp"][wave])*100, 1))
            else:
                right_kinghp_change = "+" + str(round((gamedata["rightKingPercentHp"][wave] - gamedata["rightKingPercentHp"][wave-1]) * 100, 1))
            I1.text((400, 10), "King HP: "+str(round(gamedata["leftKingPercentHp"][wave]*100, 1))+"% ("+str(left_kinghp_change)+"%)", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0),fill=(255, 255, 255))
            I1.text((1650, 10), "King HP: " + str(round(gamedata["rightKingPercentHp"][wave] * 100, 1)) + "% (" + str(right_kinghp_change) + "%)", font=myFont_title,stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
            for player in gamedata["playersData"]:
                av_image = get_icons_image("avatar", player_dict[player["playerName"]]["avatar_url"])
                if im_has_alpha(np.array(av_image)):
                    im.paste(av_image, (x, y2), mask=av_image)
                else:
                    im.paste(av_image, (x, y2))
                I1.text((x+80, y2), str(player["playerName"]), font=myFont_title, stroke_width=2,stroke_fill=(0,0,0), fill=(255, 255, 255))
                if wave > 9:
                    im.paste(get_icons_image("icon_send", player["chosenSpell"].replace(" ", "")), (x+500, y2))
                try:
                    im.paste(get_icons_image("legion", player_dict[player["playerName"]]["legion"]), (x, y2+80))
                except FileNotFoundError:
                    im.paste(get_icons_image("icon", player_dict[player["playerName"]]["legion"]), (x, y2 + 80))
                if len(player_dict[player["playerName"]]["roll"]) > 1:
                    for c, unit in enumerate(player_dict[player["playerName"]]["roll"]):
                        im.paste(get_icons_image("icon", unit.replace("_unit_id", "")), (x+offset+16+(offset*c), y2 + 80))
                for i in range(15):
                    im.paste(horz_line, (x,y+offset*i))
                for i in range(10):
                    im.paste(vert_line, (x+offset*i,y))
                build_per_wave = player["buildPerWave"][wave]
                value = 0
                for unit2 in build_per_wave:
                    unit2_list = unit2.split(":")
                    unit2_name = unit2_list[0]
                    for unitjson in units_dict:
                        if unitjson["unitId"] == unit2_name:
                            value += int(unitjson["totalValue"])
                    unit2 = unit2.split("_unit_id:")
                    unit_x = float(unit2[1].split("|")[0])-0.5
                    unit_y = 14-float(unit2[1].split("|")[1].split(":")[0])-0.5
                    unit_stacks = unit2[1].split("|")[1].split(":")[1]
                    im.paste(get_icons_image("icon", unit2[0]), (int(x + line_width + offset * unit_x), int(y + line_width + offset * unit_y)))
                    if player["chosenSpellLocation"] != "-1|-1":
                        if unit2_list[1] == player["chosenSpellLocation"] and wave > 9:
                            im.paste(get_icons_image("icon", player["chosenSpell"]).resize((28,28)),(int(x + line_width + offset * unit_x), int(y + line_width + offset * unit_y)))
                im.paste(get_icons_image("icon", "Value32").resize((64,64)), (x, y2 + 150), mask=get_icons_image("icon", "Value32").resize((64,64)))
                I1.text((x + 70, y2 + 160), str(value), font=myFont_small, stroke_width=2,stroke_fill=(0,0,0), fill=(255, 255, 255))
                im.paste(get_icons_image("icon", "Worker"), (x+230, y2 + 150))
                I1.text((x + 300, y2 + 160), str(round(player["workersPerWave"][wave], 1)), font=myFont_small, stroke_width=2, stroke_fill=(0, 0, 0),fill=(255, 255, 255))
                im.paste(get_icons_image("icon", "Income").resize((64,64)), (x + 450, y2 + 150), mask=get_icons_image("icon", "Income").resize((64,64)))
                I1.text((x + 520, y2 + 160), str(round(player["incomePerWave"][wave], 1)), font=myFont_small,stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
                im.paste(get_icons_image("icon", "Mythium32").resize((64, 64)), (x, y+20+offset*14),mask=get_icons_image("icon", "Mythium32").resize((64, 64)))
                I1.text((x+70, y+20+offset*14), str(count_mythium(player["mercenariesReceivedPerWave"][wave])+len(player["opponentKingUpgradesPerWave"][wave])*20), font=myFont_small,stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
                send_count = 0
                for send in player["mercenariesReceivedPerWave"][wave]:
                    if send_count < 9:
                        im.paste(get_icons_image("icon_send", send.replace(" ", "")), (x+offset*send_count, y+20+offset*15))
                    elif send_count >= 9:
                        im.paste(get_icons_image("icon_send", send.replace(" ", "")),(x + offset * (send_count-9), y + 20 + offset * 16))
                    elif send_count >18:
                        break
                    send_count += 1
                for send in player["opponentKingUpgradesPerWave"][wave]:
                    if send_count < 9:
                        im.paste(get_icons_image("icon_send", send.replace(" ", "")), (x+offset*send_count, y+20+offset*15))
                    elif send_count >= 9:
                        im.paste(get_icons_image("icon_send", send.replace(" ", "")),(x + offset * (send_count-9), y + 20 + offset * 16))
                    elif send_count >18:
                        break
                    send_count += 1
                im.paste(get_icons_image("icon", "Leaked"), (x, y+220+offset*14))
                leak = calc_leak(player["leaksPerWave"][wave], wave)
                if leak > 0:
                    I1.text((x+offset, y+220+offset*14), str(leak)+"%", font=myFont_small, stroke_width=2, stroke_fill=(0, 0, 0),fill=(255, 255, 255))
                leak_count = 0
                for leak in player["leaksPerWave"][wave]:
                    if leak_count < 9:
                        im.paste(get_icons_image("icon_send", leak.replace(" ", "")),(x + offset * leak_count, y + 225 + offset * 15))
                    elif leak_count >= 9:
                        im.paste(get_icons_image("icon_send", leak.replace(" ", "")),(x + offset * (leak_count - 9), y + 225 + offset * 16))
                    elif leak_count > 18:
                        break
                    leak_count += 1
                x += offset * 10
            if first:
                first =  False
                os.umask(0)
                Path(shared_folder + gameid + "/").mkdir(parents=True, exist_ok=True)
            im = im.resize((int(20 + offset * 39 / 3), int(1750 / 3)))
            im.save(shared_folder + gameid + "/"+str(wave+1)+'.png')
            image_link = site+gameid+"/"+str(wave+1)+'.png'
    else:
        image_link = site + gameid + "/" + str(start_wave) + '.png'
    if start_wave != 0:
        return image_link
    else:
        if not Path(Path(shared_folder + gameid + "/index.php")).is_file():
            shutil.copy("Files/index.php", shared_folder + gameid + "/")
        return site+gameid

def apicall_elo(playername, rank):
    win_count = 0
    elo_change = 0
    history_list = []
    if playername != None:
        playerid = apicall_getid(playername)
        if playerid == 0:
            return 'Player ' + str(playername) + ' not found.'
        if playerid == 1:
            return 'API limit reached.'
        history_raw = apicall_getmatchistory(playerid, 10, earlier_than_wave10=True)
        for game in history_raw:
            for player2 in game["playersData"]:
                if player2["playerId"] == playerid:
                    playername = player2["playerName"]
                    if player2["gameResult"] == "won":
                        history_list.append("W")
                        win_count += 1
                    else:
                        history_list.append("L")
                    elo_change += player2["eloChange"]
    def elochange(elochange):
        if elo_change >=0:
            return "+" + str(elo_change)
        else:
            return str(elo_change)
    if rank == 0:
        url = 'https://apiv2.legiontd2.com/players/stats?limit=100&sortBy=overallElo&sortDirection=-1'
        api_response = requests.get(url, headers=header)
        leaderboard = json.loads(api_response.text)
        for i, player in enumerate(leaderboard):
            if player["_id"] == playerid:
                rank = i+1
                rank_emote = get_ranked_emote(player['overallElo'])
                peak_emote = get_ranked_emote(player['overallPeakEloThisSeason'])
                embed = discord.Embed(color=0xFFD136, description="**"+playername + '** is rank ' + str(i+1) + ' with ' + str(
                    player['overallElo']) + " " + rank_emote+' elo\nPeak: ' + str(player['overallPeakEloThisSeason']) + " " + peak_emote+' and ' + str(
                    round((player['secondsPlayed'] / 60)/60)) + ' hours.\n' + \
                    str(win_count) + ' Win - '+str(len(history_raw)-win_count)+' Lose (Elo change: ' + elochange(elo_change)+")\n"+"-".join(history_list))
                embed.set_thumbnail(url="https://cdn.legiontd2.com/" + apicall_getprofile(playerid)['avatarUrl'])
                return embed
        else:
            player = apicall_getstats(playerid)
            rank_emote = get_ranked_emote(player['overallElo'])
            peak_emote = get_ranked_emote(player['overallPeakEloThisSeason'])
            embed = discord.Embed(color=0xFFD136, description="**"+playername + '** has ' + str(player['overallElo']) + " " + rank_emote +
                ' elo\nPeak: ' + str(player['overallPeakEloThisSeason']) + " " + peak_emote + ' and ' +
                str(round((player['secondsPlayed'] / 60) / 60)) + ' hours.\n' + \
                str(win_count) + ' W - '+str(len(history_raw)-win_count)+' L (Elo change: ' + elochange(elo_change)+")\n"+"-".join(history_list))
            embed.set_thumbnail(url="https://cdn.legiontd2.com/" + apicall_getprofile(playerid)['avatarUrl'])
            return embed
    else:
        url = 'https://apiv2.legiontd2.com/players/stats?limit=1&offset=' + str(int(rank)-1) + '&sortBy=overallElo&sortDirection=-1'
        api_response = requests.get(url, headers=header)
        player = json.loads(api_response.text)[0]
        playerid = player["_id"]
        playername = apicall_getprofile(playerid)["playerName"]
        rank_emote = get_ranked_emote(player['overallElo'])
        peak_emote = get_ranked_emote(player['overallPeakEloThisSeason'])
        history_raw = apicall_getmatchistory(playerid, 10, earlier_than_wave10=True)
        for game in history_raw:
            for player2 in game["playersData"]:
                if player2["playerId"] == playerid:
                    if player2["gameResult"] == "won":
                        history_list.append("W")
                        win_count += 1
                    else:
                        history_list.append("L")
                    elo_change += player2["eloChange"]
        embed = discord.Embed(color=0xFFD136, description="**"+playername + '** is rank ' + str(rank) + ' with ' + str(
            player['overallElo']) + " " + rank_emote + ' elo\nPeak: ' + str(player['overallPeakEloThisSeason']) + " " + peak_emote + ' and ' + str(
            round((player['secondsPlayed'] / 60) / 60)) + ' hours.\n' + \
            str(win_count) + ' Win - ' + str(len(history_raw)-win_count) + ' Lose (Elo change: ' + elochange(elo_change) + ")\n"+"-".join(history_list))
        embed.set_thumbnail(url="https://cdn.legiontd2.com/" + apicall_getprofile(playerid)['avatarUrl'])
        return embed

def apicall_bestie(playername):
    playerid = apicall_getid(playername)
    if playerid == 0:
        return 'Player ' + str(playername) + ' not found.'
    if playerid == 1:
        return 'API limit reached.'
    else:
        request_type = 'players/bestFriends/' + playerid
        url = 'https://apiv2.legiontd2.com/' + request_type + '?limit=1&offset=0'
        api_response = requests.get(url, headers=header)
        bestie = json.loads(api_response.text)
        if not bestie:
            return 'no bestie :sob: (No data)'
        else:
            for bestie_new in bestie[0].values():
                print(bestie_new['playerName'])
                bestie_name = bestie_new['playerName']
                break
            print(bestie[0]['count'])

            return str(playername).capitalize() + "'s bestie is " + bestie_name + ' :heart: with ' + str(
                bestie[0]['count']) + ' games together.'

def apicall_showlove(playername, playername2):
    playerid = apicall_getid(playername)
    print(playername)
    print(playername2)
    if playerid == 0:
        return 'Player ' + str(playername) + ' not found.'
    if playerid == 1:
        return 'API limit reached.'
    request_type = 'players/bestFriends/' + playerid
    url = 'https://apiv2.legiontd2.com/' + request_type + '?limit=50&offset=0'
    api_response = requests.get(url, headers=header)
    bestie = json.loads(api_response.text)
    count = 0
    nextvaluesave = 0
    while count < len(bestie):
        for bestie_new in bestie[count].values():
            if isinstance(bestie_new, dict):
                name = bestie_new['playerName']
                if str(name).lower() == str(playername2).lower():
                    print('found target')
                    nextvaluesave = 1
                count = count + 1
            else:
                if nextvaluesave == 1:
                    love_count = bestie_new
                    print(love_count)
                    return playername.capitalize() + ' has played ' + str(
                        love_count) + ' games with ' + playername2.capitalize() + ' :heart:'
    return 'Not enough games played together'

def apicall_gamestats(playername):
    playerid = apicall_getid(playername)
    if playerid == 1:
        return 'API limit reached.'
    if playerid == 0:
        return playername + "not found."
    stats = apicall_getstats(playerid)
    try: wins = stats['rankedWinsThisSeason']
    except KeyError: wins = 0
    try: loses = stats['rankedLossesThisSeason']
    except KeyError: loses = 0
    try:
        winrate = wins / (wins + loses)
    except ZeroDivisionError:
        return str(playername).capitalize() +' has no ranked games played this season.'
    return str(playername).capitalize() + ("'s stats(Season 2024):\n"
        "Elo: ") + str(stats['overallElo']) + '(Peak: ' + str(stats['overallPeakEloThisSeason']) + (')\n'
        'Games played: ') + str(wins + loses) + ('\n'
        'Winrate: ') + str(round(winrate * 100)) + ('%\n'
        'Behavior score: ') + str(stats['behaviorScore'] / 10)
