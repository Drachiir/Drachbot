import asyncio
import concurrent.futures
import difflib
import functools
import json
import traceback
from io import BytesIO
import PIL
import discord
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont
from discord import app_commands
from discord.ext import commands

import util
import json_db
import legion_api

output_folder = "Files/output/"

def jules(playername, unit, games, min_elo, patch, sort="date", mastermind = "all", spell = "all"):
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
        with open('Files/json/spells.json', 'r') as f:
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
            if spell in util.slang:
                spell = util.slang.get(spell)
            if spell not in spell_list:
                close_matches = difflib.get_close_matches(spell, spell_list)
                if len(close_matches) > 0:
                    spell = close_matches[0]
                else:
                    return spell + " spell not found."
    unit_list = []
    with open('Files/json/units.json', 'r') as f:
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
        if unit_name in util.slang:
            unit_name = util.slang.get(unit_name)
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
        playerid = legion_api.getid(playername)
        if playerid == 0:
            return 'Player ' + playername + ' not found.'
        if playerid == 1:
            return 'API limit reached, you can still use "all" commands.'
        avatar = legion_api.getprofile(playerid)['avatarUrl']
    history_raw = json_db.get_matchistory(playerid, games, min_elo, patch, sort_by=sort, earlier_than_wave10=True)
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
        av_image = util.get_icons_image("avatar", avatar)
        gold_border = Image.open('Files/gold_64.png')
        if util.im_has_alpha(np.array(av_image)):
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
        im.paste(util.get_icons_image("icon", x), (10+offset*(i+1), 80))
    if mastermind != "all":
        i += 1
        I1.text((offset * (i + 1) - 5, 100), "+", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
        im.paste(util.get_icons_image("legion", mastermind), (10 + offset * (i + 1), 80))
    if spell != "all":
        i += 1
        I1.text((offset * (i + 1) - 5, 100), "+", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
        im.paste(util.get_icons_image("icon", spell), (10 + offset * (i + 1), 80))
    I1.text((10, 160), 'Games: ' + str(occurrence_count) + ', Win: '+str(win_count)+', Lose: '+str(occurrence_count-win_count), font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    if round(win_count/occurrence_count*100,1) < 50:
        wr_rgb = (255,0,0)
    else: wr_rgb = (0,255,0)
    I1.text((10, 200),'Winrate: ', font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    I1.text((115, 200),str(round(win_count/occurrence_count*100,1))+"%", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=wr_rgb)
    I1.text((10, 240), 'Appearance rate: ' + str(round(occurrence_count / games * 100, 1)) + "%", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    image_id = util.id_generator()
    im.save(output_folder + image_id + '.png')
    return output_folder + image_id + '.png'

class Jules(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    @app_commands.command(name="jules", description="Unit synergy stats.")
    @app_commands.describe(playername='Enter playername or "all" for all available data.',
                           mastermind="Enter mastermind name.",
                           spell="Enter legion spell name.",
                           games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           min_elo='Enter minium average game elo to include in the data set',
                           patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.',
                           sort="Sort by?")
    @app_commands.choices(mastermind=util.mm_choices)
    @app_commands.choices(sort=[
        discord.app_commands.Choice(name='date', value="date"),
        discord.app_commands.Choice(name='elo', value="elo")
    ])
    @app_commands.autocomplete(unit1=util.unit_autocomplete, unit2=util.unit_autocomplete,
                               unit3=util.unit_autocomplete, unit4=util.unit_autocomplete,
                               spell=util.spell_autocomplete)
    async def jules(self, interaction: discord.Interaction, playername: str, unit1: str, unit2: str="", unit3: str="", unit4: str="",
                    mastermind: discord.app_commands.Choice[str] = "all", spell: str = "all", games: int = 0, min_elo: int = 0,
                    patch: str = util.current_season, sort: discord.app_commands.Choice[str] = "date"
                    ):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            if playername.lower() == "all" and games == 0 and min_elo == 0 and patch == util.current_season:
                min_elo = util.current_minelo
            try:
                sort = sort.value
            except AttributeError:
                pass
            try:
                mastermind = mastermind.value
            except AttributeError:
                pass
            try:
                unit = []
                for i in [unit1,unit2,unit3,unit4]:
                    if i != "":
                        unit.append(i)
                unit = ",".join(unit)
                response = await loop.run_in_executor(pool, functools.partial(jules, str(playername).lower(), unit, games, min_elo, patch, sort=sort, mastermind=mastermind, spell=spell))
                pool.shutdown()
                if response.endswith(".png"):
                    await interaction.followup.send(file=discord.File(response))
                else:
                    await interaction.followup.send(response)
            except Exception:
                print("/" + interaction.command.name + " failed. args: " + str(interaction.data.values()))
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

async def setup(bot:commands.Bot):
    await bot.add_cog(Jules(bot))