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

import json_db
import util
import legion_api

output_folder = "Files/output/"

def elograph(playername, games, patch, transparency=False):
    playerid = legion_api.getid(playername)
    if playerid == 0:
        return 'Player ' + playername + ' not found.'
    if playerid == 1:
        return 'API limit reached.'
    try:
        history_raw = json_db.get_matchistory(playerid, games, 0, patch, earlier_than_wave10=True)
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
                elo_per_game.insert(0, player["overallElo"] + player["eloChange"])
                date_this = game["date"].replace("T", "-").replace(":", "-").split(".")[0]
                date_per_game.insert(0, datetime.strptime(date_this, "%Y-%m-%d-%H-%M-%S").strftime("%d/%m/%y"))
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
    # matplotlib graph
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
    locator = plt.MaxNLocator(nbins=len(ax.get_xticks()) - 1, min_n_ticks=1)
    ax2.xaxis.set_major_locator(locator)
    img_buf = io.BytesIO()
    fig.savefig(img_buf, transparent=True, format='png')
    plt.close()
    elo_graph = Image.open(img_buf)
    im.paste(elo_graph, (-100, 40), elo_graph)
    
    image_id = util.id_generator()
    im.save(output_folder + image_id + '.png')
    return output_folder + image_id + '.png'

def statsgraph(playernames: list, games, min_elo, patch, key, transparency=False, sort="date", waves=[1, 21]) -> str:
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
    for j, id in enumerate(playerids):
        history_raw = json_db.get_matchistory(id, games, min_elo, patch, sort_by=sort, earlier_than_wave10=True)
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
            players_dict[player]["Waves"].append([0, 0])
        for data in players_dict[player]["Data"]:
            for c, wave_data in enumerate(data):
                players_dict[player]["Waves"][c][0] += 1
                players_dict[player]["Waves"][c][1] += wave_data
        players_dict[player]["FinalData"] = []
        for index, wave in enumerate(players_dict[player]["Waves"]):
            if index + 1 >= waves[0] and index + 1 <= waves[1]:
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
    I1.text((10, 15), key + " Graph (From " + str(total_games) + " ranked games)", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
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
    ax.set_ylabel(key, weight='bold')
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
        last_game = json_db.get_matchistory(player["_id"], 1, earlier_than_wave10=True)
        game_date = datetime.strptime(last_game[0]["date"].split(".000Z")[0].replace("T", "-"), '%Y-%m-%d-%H:%M:%S')
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

def sendstats(playername, starting_wave, games, min_elo, patch, sort="date", transparency = False):
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
        playerid = legion_api.getid(playername)
        if playerid == 0:
            return 'Player ' + playername + ' not found.'
        if playerid == 1:
            return 'API limit reached.'
        profile = legion_api.getprofile(playerid)
        playername = profile['playerName']
        avatar = profile['avatarUrl']
    try:
        history_raw = json_db.get_matchistory(playerid, games, min_elo=min_elo, patch=patch, sort_by=sort, earlier_than_wave10=True)
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
                send = util.count_mythium(player["mercenariesSentPerWave"][starting_wave]) + len(player["kingUpgradesPerWave"][starting_wave]) * 20
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
                            send2 = util.count_mythium(player["mercenariesSentPerWave"][starting_wave+n+1]) + len(player["kingUpgradesPerWave"][starting_wave+n+1]) * 20
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
            if util.im_has_alpha(np.array(av_image)):
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
        discord.app_commands.Choice(name='Workers', value="workersPerWave"),
        discord.app_commands.Choice(name='Income', value="incomePerWave"),
        discord.app_commands.Choice(name='Fighter Value', value="valuePerWave")
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
                response = await loop.run_in_executor(pool, functools.partial(statsgraph, playernames=playernames, min_elo=min_elo, waves=waves_list, games=games, patch=patch, key=key.value, sort=sort))
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
                if response.endswith(".png"):
                    await interaction.followup.send(file=discord.File(response))
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
    
    @app_commands.command(name="sendstats", description="Send stats.")
    @app_commands.describe(playername='Enter playername or "all" for all available data.',
                           starting_wave='Enter wave to show next sends when there was a send on that wave, or 0 for first sends after saving on Wave 1',
                           games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           min_elo='Enter minium average game elo to include in the data set',
                           patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.',
                           sort="Sort by?")
    @app_commands.choices(sort=[
        discord.app_commands.Choice(name='date', value="date"),
        discord.app_commands.Choice(name='elo', value="elo")
    ])
    async def sendstats(self, interaction: discord.Interaction, playername: str, starting_wave: int, games: int = 0, min_elo: int = 0, patch: str = util.current_season, sort: discord.app_commands.Choice[str] = "date"):
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
                response = await loop.run_in_executor(pool, functools.partial(sendstats, str(playername).lower(), starting_wave, games, min_elo, patch, sort=sort))
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
    await bot.add_cog(Graphs(bot))