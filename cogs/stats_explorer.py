import asyncio
import concurrent.futures
import functools
import traceback
import discord
from discord import app_commands
from discord.ext import commands
import PIL
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import requests
from io import BytesIO
import util
import drachbot_db
import legion_api
from peewee_pg import GameData, PlayerData


output_folder = "Files/output/"

def stats_explorer(playername, unit: list, games, min_elo, patch, sort="date", mastermind = "all", spell = "all"):
    if spell != "all":
        if util.validate_spell_input(spell) is None:
            return spell + " spell not found."
    unit = util.validate_unit_list_input(unit)
    if type(unit) == type(str()):
        return unit
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
    req_columns = [[GameData.game_id, GameData.queue, GameData.date, GameData.version, GameData.ending_wave, GameData.game_elo, GameData.player_ids,
                    PlayerData.player_id, PlayerData.player_slot, PlayerData.game_result, PlayerData.player_elo, PlayerData.legion,
                    PlayerData.opener, PlayerData.spell, PlayerData.spell_location, PlayerData.fighters, PlayerData.build_per_wave],
                   ["game_id", "date", "version", "ending_wave", "game_elo"],
                   ["player_id", "player_slot", "game_result", "player_elo", "legion", "opener", "spell", "spell_location", "fighters", "build_per_wave"]]
    history_raw = drachbot_db.get_matchistory(playerid, games, min_elo, patch, sort_by=sort, earlier_than_wave10=True, req_columns=req_columns)
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
    print('Starting stats-explorer command...')
    for game in history_raw:
        patches.append(game["version"])
        gameelo_list.append(game["game_elo"])
        for player in game["players_data"]:
            if player["player_id"] != playerid and playerid != "all":
                continue
            expected = len(unit)
            current = 0
            fighter_list = player["fighters"].lower()
            if mastermind != "all":
                expected += 1
                if mastermind == player["legion"]:
                    current += 1
            if spell != "all" and player["spell_location"] != "-1|-1" and spell.lower() == player["spell"].lower() and spell.lower() not in excluded_buffs:
                expected += 1
                for pos in player["build_per_wave"][-1].split("!"):
                    if pos.split(":")[1] == player["spell_location"] and pos.split(":")[0].replace("_unit_id", "").replace("_", " ") in unit:
                        spell = player["spell"]
                        current += 1
                        for un in unit:
                            if un.lower() in fighter_list:
                                current += 1
            else:
                if spell != "all":
                    expected += 1
                    if spell.lower() == player["spell"].lower():
                        spell = player["spell"]
                        current += 1
                for un in unit:
                    if un.lower() in fighter_list:
                        current += 1
            if current == expected:
                occurrence_count += 1
                playerelo_list.append(player["player_elo"])
                if player["game_result"] == "won":
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
    myFont_title = ImageFont.truetype(ttf, 30)
    if playername != 'all' and 'nova cup' not in playername:
        string = f"{playername.capitalize()}'s "
    else:
        string = ""
    I1.text((10, 10),string+"Stats Explorer (From " + str(games) + " ranked games, Avg elo: " + str(avg_gameelo) + ")", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    I1.text((10, 50), 'Patches: ' + ', '.join(patches), font=myFont_small, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    offset = 80
    for i, x in enumerate(unit):
        im.paste(util.get_icons_image("icon", x), (10 + offset * i, 80))
    if mastermind != "all":
        i += 1
        im.paste(util.get_icons_image("legion", mastermind), (10 + offset * i, 80))
    if spell != "all":
        i += 1
        im.paste(util.get_icons_image("icon", spell), (10 + offset * i, 80))
    I1.text((10, 160), 'Games: ' + str(occurrence_count) + ', Win: ' + str(win_count) + ', Lose: ' + str(occurrence_count - win_count), font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    if round(win_count / occurrence_count * 100, 1) < 50:
        wr_rgb = (255, 0, 0)
    else:
        wr_rgb = (0, 255, 0)
    I1.text((10, 200), 'Winrate: ', font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    I1.text((115, 200), str(round(win_count / occurrence_count * 100, 1)) + "%", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=wr_rgb)
    I1.text((10, 240), 'Appearance rate: ' + str(round(occurrence_count / games * 100, 1)) + "%", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    image_id = util.id_generator()
    im.save(output_folder + image_id + '.png')
    return output_folder + image_id + '.png'

class StatsExplorer(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    @app_commands.command(name="stats-explorer", description="Shows statistics based on various filters.")
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
    async def stats_explorer(self, interaction: discord.Interaction, playername: str, unit1: str, unit2: str="", unit3: str="", unit4: str="",
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
                response = await loop.run_in_executor(pool, functools.partial(stats_explorer, str(playername).lower(), unit, games, min_elo, patch, sort=sort, mastermind=mastermind, spell=spell))
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
    await bot.add_cog(StatsExplorer(bot))