from collections import Counter
import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import concurrent.futures
import traceback
import functools
import json
import difflib
from datetime import datetime, timedelta, timezone
import PIL
from PIL import Image, ImageDraw, ImageFont, ImageSequence
import matplotlib.pyplot as plt
import io
from io import BytesIO
import requests
import numpy as np
import bokeh
from bokeh.plotting import figure, show, output_notebook, output_file, save
from bokeh.models import LinearAxis, Range1d, SingleIntervalTicker
from bokeh.io import curdoc
import platform
import random

import drachbot_db
import util
import legion_api
from peewee_pg import GameData, PlayerData

output_folder = "Files/output/"
site = "https://overlay.drachbot.site/Images/"
site2 = "https://overlay.drachbot.site/Html/"
if platform.system() == "Linux":
    shared_folder = "/shared/Html/"
else:
    shared_folder = "shared/Html/"

def elograph(playername, games, patch, transparency=False):
    playerid = legion_api.getid(playername)
    if playerid == 0:
        return 'Player ' + playername + ' not found.'
    if playerid == 1:
        return 'API limit reached.'
    req_columns = [[GameData.game_id, GameData.queue, GameData.date, GameData.version, GameData.ending_wave, GameData.game_elo, GameData.player_ids,
                    PlayerData.player_id, PlayerData.player_slot, PlayerData.player_elo, PlayerData.elo_change],
                   ["game_id", "date", "version", "ending_wave", "game_elo"],
                   ["player_id", "player_slot" , "player_elo", "elo_change"]]
    history_raw = drachbot_db.get_matchistory(playerid, games, 0, patch, earlier_than_wave10=True, req_columns=req_columns)
    if type(history_raw) == str:
        return history_raw
    games = len(history_raw)
    if games == 0:
        return 'No games found.'
    patches = []
    elo_per_game = []
    date_per_game = []
    for game in history_raw:
        for player in game["players_data"]:
            if player["player_id"] == playerid:
                patches.append(game["version"])
                elo_per_game.insert(0, player["player_elo"] + player["elo_change"])
                date_per_game.insert(0, game["date"].strftime("%d/%m/%y"))
                break
        else:
            games -= 1
    new_patches = []
    for x in patches:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches = list(dict.fromkeys(new_patches))
    patches = sorted(patches, key=lambda x: int(x.split(".")[0] + x.split(".")[1]), reverse=True)
    # Image generation
    x = 126
    y = 160
    if transparency:
        mode = 'RGBA'
        colors = (0, 0, 0, 0)
    else:
        mode = 'RGB'
        colors = (49, 51, 56)
    im = PIL.Image.new(mode=mode, size=(1300, 810), color=colors)
    im2 = PIL.Image.new(mode="RGB", size=(88, 900), color=(25, 25, 25))
    im3 = PIL.Image.new(mode="RGB", size=(1676, 4), color=(169, 169, 169))
    I1 = ImageDraw.Draw(im)
    ttf = 'Files/RobotoCondensed-Regular.ttf'
    myFont_small = ImageFont.truetype(ttf, 20)
    myFont = ImageFont.truetype(ttf, 25)
    myFont_title = ImageFont.truetype(ttf, 30)
    I1.text((10, 15), playername.capitalize() + "'s Elo Graph (From " + str(games) + " ranked games)", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    I1.text((10, 55), 'Patches: ' + ', '.join(patches), font=myFont_small, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    #bokeh graph
    games_list = []
    for y in range(1, games + 1):
        games_list.append(y)
    curdoc().theme = "dark_minimal"
    p = figure(title=playername.capitalize()+"'s Elo Graph", x_axis_label="Games", y_axis_label="Elo", sizing_mode="stretch_both")
    p.line(games_list,elo_per_game, line_width=2, line_color="white")
    p.extra_x_ranges.update({'x_above': p.x_range})
    p.add_layout(LinearAxis(x_range_name='x_above'), 'above')
    p.above[0].major_label_overrides = {key: item for key, item in zip(range(1, games+1), date_per_game)}
    p.x_range.min_interval = 1
    p.x_range.max_interval = games
    p.xaxis.minor_tick_line_color = None
    p.yaxis.minor_tick_line_color = None
    b_rand_id = util.id_generator()
    p.title.text = playername.capitalize()+"'s Elo Graph"
    output_file(shared_folder+b_rand_id+".html")
    save(p)
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
    ax.grid(linewidth=1)
    ax.margins(x=0)
    ax.set_xlabel('Games', weight='bold')
    ax.set_ylabel('Elo', weight='bold')
    ax2.set_xlabel("Date d/m/y", weight='bold')
    ax.plot(range(1, games + 1), elo_per_game, color='red', marker=marker_plot, linewidth=1.5, label='Elo')
    ax2.set_xlim(ax.get_xlim())
    new_tick_locs = []
    for d in range(1, games+1):
        new_tick_locs.append(d)
    ax.set_xticks(new_tick_locs)
    ax.set_xticklabels(new_tick_locs)
    ax2.set_xticks(new_tick_locs)
    ax2.set_xticklabels(date_per_game)
    locator = plt.MaxNLocator()
    ax.xaxis.set_major_locator(locator)
    ax2.xaxis.set_major_locator(locator)
    img_buf = io.BytesIO()
    fig.savefig(img_buf, transparent=True, format='png')
    plt.close()
    elo_graph = Image.open(img_buf)
    im.paste(elo_graph, (-100, 40), elo_graph)

    image_id = util.id_generator()
    im.save(output_folder + image_id + '.png')
    return [playername, site2+b_rand_id+".html", output_folder + image_id + '.png', image_id + '.png']

def statsgraph(playernames: list, games, min_elo, patch, key: discord.app_commands.Choice, transparency=False, sort="date", waves=[1, 21]) -> str:
    playerids = set()
    total_games = 0
    for name in playernames:
        if name == "all":
            playerid = "all"
        else:
            playerid = legion_api.getid(name)
        if playerid == 0:
            return name + ' not found.'
        if playerid == 1:
            return 'API limit reached.'
        playerids.add(playerid)
    players_dict = dict()
    print("Starting stats graph command...")
    patches = []
    req_columns = [[GameData.game_id, GameData.queue, GameData.date, GameData.version, GameData.ending_wave, GameData.game_elo, GameData.player_ids,
                    PlayerData.player_id, PlayerData.player_slot, PlayerData.player_elo, PlayerData.elo_change, PlayerData.workers_per_wave,
                    PlayerData.income_per_wave, PlayerData.leaks_per_wave, PlayerData.fighter_value_per_wave],
                   ["game_id", "date", "version", "ending_wave", "game_elo"],
                   ["player_id", "player_slot", "player_elo", "elo_change", "workers_per_wave", "income_per_wave", "leaks_per_wave", "fighter_value_per_wave"]]
    for j, id in enumerate(playerids):
        history_raw = drachbot_db.get_matchistory(id, games, min_elo, patch, sort_by=sort, earlier_than_wave10=True, req_columns=req_columns)
        if type(history_raw) == str:
            return history_raw
        games2 = len(history_raw)
        total_games += games2
        if games2 == 0:
            return 'No games found for ' + playernames[j] + "."
        for game in history_raw:
            patches.append(game["version"])
            for player in game["players_data"]:
                if player["player_id"] == id or id == "all":
                    if key.value == "leaks_per_wave":
                        leaks_per_wave = []
                        for wave_num, leak in enumerate(player[key.value]):
                            leaks_per_wave.append(util.calc_leak(leak, wave_num))
                    if id in players_dict:
                        if key.value == "leaks_per_wave":
                            players_dict[id]["Data"].append(leaks_per_wave)
                        else:
                            players_dict[id]["Data"].append(player[key.value])
                    else:
                        if key.value == "leaks_per_wave":
                            players_dict[id] = {"Data": [leaks_per_wave]}
                        else:
                            players_dict[id] = {"Data": [player[key.value]]}
    for player in players_dict:
        players_dict[player]["Waves"] = []
        for w in range(21):
            players_dict[player]["Waves"].append([0, 0])
        for data in players_dict[player]["Data"]:
            for c, wave_data in enumerate(data):
                players_dict[player]["Waves"][c][0] += 1
                players_dict[player]["Waves"][c][1] += wave_data
        players_dict[player]["FinalData"] = []
        for index, wave in enumerate(players_dict[player]["Waves"]):
            if waves[0] <= index + 1 <= waves[1]:
                try:
                    players_dict[player]["FinalData"].append(round(wave[1] / wave[0], 1))
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
    # Image generation
    x = 126
    y = 160
    if transparency:
        mode = 'RGBA'
        colors = (0, 0, 0, 0)
    else:
        mode = 'RGB'
        colors = (49, 51, 56)
    im = PIL.Image.new(mode=mode, size=(1300, 800), color=colors)
    I1 = ImageDraw.Draw(im)
    ttf = 'Files/RobotoCondensed-Regular.ttf'
    myFont_small = ImageFont.truetype(ttf, 20)
    myFont = ImageFont.truetype(ttf, 25)
    myFont_title = ImageFont.truetype(ttf, 30)
    I1.text((10, 15), key.name + " Graph (From " + str(total_games) + " ranked games)", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    I1.text((10, 55), 'Patches: ' + ', '.join(patches), font=myFont_small, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    # matplotlib graph
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
    if key.value == "leaksPerWave":
        key_string = "%"
    else:
        key_string = ""
    ax.set_ylabel(key.value+key_string, weight='bold')
    colors = ["red", "deepskyblue", "green"]
    waves_list = []
    for v in range(waves[0], waves[1] + 1):
        waves_list.append(str(v))
    for index, player in enumerate(players_dict):
        if player == "all":
            label_string = "All"
        else:
            label_string = legion_api.getprofile(player)["playerName"]
        ax.plot(waves_list, players_dict[player]["FinalData"], color=colors[index], marker=marker_plot, linewidth=2, label=label_string)
    ax.legend(bbox_to_anchor=(0.57, 1.07), prop={'size': 13})
    img_buf = io.BytesIO()
    fig.savefig(img_buf, transparent=True, format='png')
    plt.close()
    elo_graph = Image.open(img_buf)
    im.paste(elo_graph, (-100, 30), elo_graph)
    image_id = util.id_generator()
    im.save(output_folder + image_id + '.png')
    return output_folder + image_id + '.png'

def leaderboard(ranks=10, transparency=False):
    url = 'https://apiv2.legiontd2.com/players/stats?limit=' + str(ranks) + '&sortBy=overallElo&sortDirection=-1'
    api_response = requests.get(url, headers=legion_api.header)
    legion_api.api_call_logger("players/stats")
    leaderboard = json.loads(api_response.text)
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
    x = 24
    y = 24
    offset = 80
    for i, player in enumerate(leaderboard):
        im.paste(im2, (x-6,y-6))
        avatar_url = 'https://cdn.legiontd2.com/' + player["profile"][0]["avatarUrl"]
        avatar_response = requests.get(avatar_url)
        av_image = Image.open(BytesIO(avatar_response.content))
        gold_border = Image.open('Files/gold_64.png')
        if util.im_has_alpha(np.array(av_image)):
            im.paste(av_image, (x, y), mask=av_image)
        else:
            im.paste(av_image, (x, y))
        im.paste(gold_border, (x, y), mask=gold_border)
        req_columns = [[GameData.game_id, GameData.queue, GameData.date, GameData.version, GameData.ending_wave, GameData.game_elo, GameData.player_ids,
                        PlayerData.player_id, PlayerData.player_slot],
                       ["game_id", "date", "version", "ending_wave", "game_elo"],
                       ["player_id", "player_slot"]]
        last_game = drachbot_db.get_matchistory(player["_id"], 1, earlier_than_wave10=True, req_columns=req_columns)
        game_date = last_game[0]["date"]
        if game_date < datetime.now() - timedelta(days=2):
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
    image_id = util.id_generator()
    im.save(output_folder + image_id + '.png')
    return output_folder + image_id + '.png'

class Graphs(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    @app_commands.command(name="statsgraph", description="Stats graph.")
    @app_commands.describe(playernames='Enter playername or up to 3 playernames separated by commas.',
                           key='Select which stat to display in the graph.',
                           waves='Enter min and max wave separated by a hyphen, e.g "1-3" for Wave 1, Wave 2 and Wave 3',
                           games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           min_elo='Enter minium average game elo to include in the data set',
                           patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.',
                           sort="Sort by?")
    @app_commands.choices(key=[
        discord.app_commands.Choice(name='Workers', value="workers_per_wave"),
        discord.app_commands.Choice(name='Income', value="income_per_wave"),
        discord.app_commands.Choice(name='Leaks', value="leaks_per_wave"),
        discord.app_commands.Choice(name='Fighter Value', value="fighter_value_per_wave")
    ])
    @app_commands.choices(sort=[
        discord.app_commands.Choice(name='date', value="date"),
        discord.app_commands.Choice(name='elo', value="elo")
    ])
    async def statsgraph(self, interaction: discord.Interaction, playernames: str, key: discord.app_commands.Choice[str], waves: str = "1-5", games: int = 0, min_elo: int = 0, patch: str = util.current_season, sort: discord.app_commands.Choice[str] = "date"):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            if "," in playernames:
                playernames = playernames.split(",")
                for i, name in enumerate(playernames):
                    if name.startswith(" "):
                        playernames[i] = name[1:]
                if len(playernames) > 3:
                    await interaction.followup.send("Only enter 3 playernames at a time.")
                    return
            else:
                playernames = [playernames]
            if "-" in waves:
                waves_list = [int(waves.split("-")[0]), int(waves.split("-")[1])]
                if waves_list[0] > waves_list[1] or waves_list[0] < 1 or waves_list[1] > 21:
                    await interaction.followup.send("Invalid waves input.")
            else:
                await interaction.followup.send("Invalid waves input.")
                return
            try:
                sort = sort.value
            except AttributeError:
                pass
            try:
                response = await loop.run_in_executor(pool, functools.partial(statsgraph, playernames=playernames, min_elo=min_elo, waves=waves_list, games=games, patch=patch, key=key, sort=sort))
                pool.shutdown()
                if response.endswith(".png"):
                    await interaction.followup.send(file=discord.File(response))
                else:
                    await interaction.followup.send(response)
            except Exception:
                print("/" + interaction.command.name + " failed. args: " + str(interaction.data.values()))
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")
    
    @app_commands.command(name="elograph", description="Shows elo graph of player.")
    @app_commands.describe(playername='Enter playername.',
                           games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.')
    async def elo_graph(self, interaction: discord.Interaction, playername: str, games: int = 0, patch: str = util.current_season):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(elograph, playername, games, patch))
                pool.shutdown()
                if type(response) == list:
                    embed = discord.Embed(color=0xb7d715, title=response[0].capitalize() + "'s Elo Graph", url=response[1])
                    file = discord.File(response[2], filename=response[3])
                    embed.set_image(url="attachment://" + response[3])
                    await interaction.followup.send(file=file, embed=embed)
                else:
                    await interaction.followup.send(response)
            except Exception:
                print("/" + interaction.command.name + " failed. args: " + str(interaction.data.values()))
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")
    
    @app_commands.command(name="leaderboard", description="Shows current top 10 ranked leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(leaderboard))
                pool.shutdown()
                if response.endswith(".png"):
                    await interaction.followup.send(file=discord.File(response))
                else:
                    await interaction.followup.send(response)
            except Exception:
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

async def setup(bot:commands.Bot):
    await bot.add_cog(Graphs(bot))