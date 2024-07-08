import asyncio
import concurrent.futures
import functools
import json
import os
import os.path
import shutil
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
import platform

import PIL
import discord
import discord_timestamps
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont
from discord import app_commands
from discord.ext import commands
from discord_timestamps import TimestampType

import drachbot_db
import legion_api
import util
from peewee_pg import GameData, PlayerData

with open('Files/json/Secrets.json', 'r') as f:
    secret_file = json.load(f)
    f.close()

header = {'x-api-key': secret_file.get('apikey')}
site = "https://overlay.drachbot.site/Images/"
if platform.system() == "Linux":
    shared_folder = "/shared/Images/"
else:
    shared_folder = "shared/Images/"

def elo(playername, rank):
    win_count = 0
    elo_change = 0
    history_list = []
    req_columns = [[GameData.game_id, GameData.queue, GameData.date, GameData.version, GameData.ending_wave, GameData.game_elo, GameData.player_ids,
                    PlayerData.player_id, PlayerData.player_name, PlayerData.player_slot, PlayerData.game_result, PlayerData.elo_change],
                   ["game_id", "date", "version", "ending_wave", "game_elo"],
                   ["player_id", "player_name", "player_slot", "game_result", "elo_change"]]
    if playername != None:
        playerid = legion_api.getid(playername)
        if playerid == 0:
            return 'Player ' + str(playername) + ' not found.'
        if playerid == 1:
            return 'API limit reached.'
        history_raw = drachbot_db.get_matchistory(playerid, 10, earlier_than_wave10=True, req_columns=req_columns)
        for game in history_raw:
            for player2 in game["players_data"]:
                if player2["player_id"] == playerid:
                    playername = player2["player_name"]
                    if player2["game_result"] == "won":
                        history_list.append("W")
                        win_count += 1
                    else:
                        history_list.append("L")
                    elo_change += player2["elo_change"]
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
                rank_emote = util.get_ranked_emote(player['overallElo'])
                peak_emote = util.get_ranked_emote(player['overallPeakEloThisSeason'])
                embed = discord.Embed(color=0xFFD136, description="**"+playername + '** is rank ' + str(i+1) + ' with ' + str(
                    player['overallElo']) + " " + rank_emote+' elo\nPeak: ' + str(player['overallPeakEloThisSeason']) + " " + peak_emote+' and ' + str(
                    round((player['secondsPlayed'] / 60)/60)) + ' hours.\n' + \
                    str(win_count) + ' Win - '+str(len(history_raw)-win_count)+' Lose (Elo change: ' + elochange(elo_change)+")\n"+"-".join(history_list))
                embed.set_thumbnail(url="https://cdn.legiontd2.com/" + legion_api.getprofile(playerid)['avatarUrl'])
                return embed
        else:
            player = legion_api.getstats(playerid)
            rank_emote = util.get_ranked_emote(player['overallElo'])
            peak_emote = util.get_ranked_emote(player['overallPeakEloThisSeason'])
            embed = discord.Embed(color=0xFFD136, description="**"+playername + '** has ' + str(player['overallElo']) + " " + rank_emote +
                ' elo\nPeak: ' + str(player['overallPeakEloThisSeason']) + " " + peak_emote + ' and ' +
                str(round((player['secondsPlayed'] / 60) / 60)) + ' hours.\n' + \
                str(win_count) + ' W - '+str(len(history_raw)-win_count)+' L (Elo change: ' + elochange(elo_change)+")\n"+"-".join(history_list))
            embed.set_thumbnail(url="https://cdn.legiontd2.com/" + legion_api.getprofile(playerid)['avatarUrl'])
            return embed
    else:
        url = 'https://apiv2.legiontd2.com/players/stats?limit=1&offset=' + str(int(rank)-1) + '&sortBy=overallElo&sortDirection=-1'
        api_response = requests.get(url, headers=header)
        player = json.loads(api_response.text)[0]
        playerid = player["_id"]
        playername = legion_api.getprofile(playerid)["playerName"]
        rank_emote = util.get_ranked_emote(player['overallElo'])
        peak_emote = util.get_ranked_emote(player['overallPeakEloThisSeason'])
        history_raw = drachbot_db.get_matchistory(playerid, 10, earlier_than_wave10=True, req_columns=req_columns)
        for game in history_raw:
            for player2 in game["players_data"]:
                if player2["player_id"] == playerid:
                    playername = player2["player_name"]
                    if player2["game_result"] == "won":
                        history_list.append("W")
                        win_count += 1
                    else:
                        history_list.append("L")
                    elo_change += player2["elo_change"]
        embed = discord.Embed(color=0xFFD136, description="**"+playername + '** is rank ' + str(rank) + ' with ' + str(
            player['overallElo']) + " " + rank_emote + ' elo\nPeak: ' + str(player['overallPeakEloThisSeason']) + " " + peak_emote + ' and ' + str(
            round((player['secondsPlayed'] / 60) / 60)) + ' hours.\n' + \
            str(win_count) + ' Win - ' + str(len(history_raw)-win_count) + ' Lose (Elo change: ' + elochange(elo_change) + ")\n"+"-".join(history_list))
        embed.set_thumbnail(url="https://cdn.legiontd2.com/" + legion_api.getprofile(playerid)['avatarUrl'])
        return embed

def gamestats(playername):
    playerid = legion_api.getid(playername)
    if playerid == 1:
        return 'API limit reached.'
    if playerid == 0:
        return playername + "not found."
    stats = legion_api.getstats(playerid)
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

def gameid_visualizer(gameid, start_wave=0, hide_names = False):
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
        units_dict = json.load(open("Files/json/units.json"))
        if (gamedata == {'message': 'Internal server error'}) or (gamedata == {'err': 'Entry not found.'}):
            return "GameID not found. (Games that are not concluded or older than 1 year are not available in the API)"
        player_dict = {}
        for player in gamedata["playersData"]:
            player_dict[player["playerName"]] = {"avatar_url": legion_api.getprofile(player["playerId"])["avatarUrl"],
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
            if gamedata["humanCount"] == 8:
                im = PIL.Image.new(mode=mode, size=((20 + offset * 39)*2, 1750), color=colors)
            else:
                im = PIL.Image.new(mode=mode, size=(20+offset*39, 1750), color=colors)
            horz_line = PIL.Image.new(mode="RGB", size=(box_size*9+line_width*10, line_width), color=(155, 155, 155))
            vert_line = PIL.Image.new(mode="RGB", size=(line_width, box_size*14+line_width*15), color=(155, 155, 155))
            I1 = ImageDraw.Draw(im)
            ttf = 'Files/RobotoCondensed-Regular.ttf'
            myFont_tiny = ImageFont.truetype(ttf, 30)
            myFont_small = ImageFont.truetype(ttf, 40)
            myFont = ImageFont.truetype(ttf, 50)
            myFont_title = ImageFont.truetype(ttf, 60)
            y2 = 125
            im.paste(Image.open(open("Files/Waves/Wave"+str(wave+1)+".png", "rb")), (10,10))
            I1.text((80, 10), "Wave "+str(wave+1), font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0),fill=(255, 255, 255))
            I1.text((80, 75), "Patch: " + gamedata["version"], font=myFont_small, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
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
                if not hide_names:
                    av_image = util.get_icons_image("avatar", player_dict[player["playerName"]]["avatar_url"])
                    if util.im_has_alpha(np.array(av_image)):
                        im.paste(av_image, (x, y2), mask=av_image)
                    else:
                        im.paste(av_image, (x, y2))
                    I1.text((x+80, y2), str(player["playerName"]), font=myFont_title, stroke_width=2,stroke_fill=(0,0,0), fill=(255, 255, 255))
                if wave > 9:
                    im.paste(util.get_icons_image("icon_send", player["chosenSpell"].replace(" ", "")), (x+500, y2))
                try:
                    im.paste(util.get_icons_image("legion", player_dict[player["playerName"]]["legion"]), (x, y2+80))
                except FileNotFoundError:
                    im.paste(util.get_icons_image("icon", player_dict[player["playerName"]]["legion"]), (x, y2 + 80))
                if len(player_dict[player["playerName"]]["roll"]) > 1:
                    for c, unit in enumerate(player_dict[player["playerName"]]["roll"]):
                        im.paste(util.get_icons_image("icon", unit.replace("_unit_id", "")), (x+offset+16+(offset*c), y2 + 80))
                for i in range(15):
                    im.paste(horz_line, (x,y+offset*i))
                for i in range(10):
                    im.paste(vert_line, (x+offset*i,y))
                build_per_wave = player["buildPerWave"][wave]
                value = 0
                for w_index, unit2 in enumerate(build_per_wave):
                    unit2_list = unit2.split(":")
                    unit2_name = unit2_list[0]
                    unit_stacks = int(unit2_list[2])
                    for unitjson in units_dict:
                        if unit2_name == "hell_raiser_buffed_unit_id":
                            unit2_name = "hell_raiser_unit_id"
                        if unitjson["unitId"] == unit2_name:
                            if unit_stacks > 0:
                                value += util.get_unit_stacks_value(unit2_name, unit_stacks, w_index)
                            value += int(unitjson["totalValue"])
                    unit2 = unit2.split("_unit_id:")
                    unit_x = float(unit2[1].split("|")[0]) - 0.5
                    unit_y = 14 - float(unit2[1].split("|")[1].split(":")[0]) - 0.5
                    im.paste(util.get_icons_image("icon", unit2[0]), (int(x + line_width + offset * unit_x), int(y + line_width + offset * unit_y)))
                    if player["chosenSpellLocation"] != "-1|-1":
                        if unit2_list[1] == player["chosenSpellLocation"] and wave > 9:
                            im.paste(util.get_icons_image("icon", player["chosenSpell"]).resize((32, 32)), (int(x + line_width + offset * unit_x), int(y + line_width + offset * unit_y)))
                    try:
                        if player["chosenChampionLocation"] != "-1|-1":
                            if unit2_list[1] == player["chosenChampionLocation"]:
                                im.paste(util.get_icons_image("legion", "Champion").resize((32, 32)), (int(x + 32 + line_width + offset * unit_x), int(y + line_width + offset * unit_y)))
                    except Exception:
                        pass
                    if unit_stacks != 0:
                        I1.text((int(x + line_width + offset * unit_x), int(y + 32 + line_width + offset * unit_y)), str(unit_stacks), font=myFont_tiny, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
                im.paste(util.get_icons_image("icon", "Value32").resize((64,64)), (x, y2 + 150), mask=util.get_icons_image("icon", "Value32").resize((64,64)))
                I1.text((x + 70, y2 + 160), str(value), font=myFont_small, stroke_width=2,stroke_fill=(0,0,0), fill=(255, 255, 255))
                im.paste(util.get_icons_image("icon", "Worker"), (x+230, y2 + 150))
                I1.text((x + 300, y2 + 160), str(round(player["workersPerWave"][wave], 1)), font=myFont_small, stroke_width=2, stroke_fill=(0, 0, 0),fill=(255, 255, 255))
                im.paste(util.get_icons_image("icon", "Income").resize((64,64)), (x + 450, y2 + 150), mask=util.get_icons_image("icon", "Income").resize((64,64)))
                I1.text((x + 520, y2 + 160), str(round(player["incomePerWave"][wave], 1)), font=myFont_small,stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
                im.paste(util.get_icons_image("icon", "Mythium32").resize((64, 64)), (x, y+20+offset*14),mask=util.get_icons_image("icon", "Mythium32").resize((64, 64)))
                I1.text((x+70, y+20+offset*14), str(util.count_mythium(player["mercenariesReceivedPerWave"][wave])+len(player["opponentKingUpgradesPerWave"][wave])*20), font=myFont_small,stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
                send_count = 0
                for send in player["mercenariesReceivedPerWave"][wave]:
                    if send_count < 9:
                        im.paste(util.get_icons_image("icon_send", send.replace(" ", "")), (x+offset*send_count, y+20+offset*15))
                    elif send_count >= 9:
                        im.paste(util.get_icons_image("icon_send", send.replace(" ", "")),(x + offset * (send_count-9), y + 20 + offset * 16))
                    elif send_count >18:
                        break
                    send_count += 1
                for send in player["opponentKingUpgradesPerWave"][wave]:
                    if send_count < 9:
                        im.paste(util.get_icons_image("icon_send", send.replace(" ", "")), (x+offset*send_count, y+20+offset*15))
                    elif send_count >= 9:
                        im.paste(util.get_icons_image("icon_send", send.replace(" ", "")),(x + offset * (send_count-9), y + 20 + offset * 16))
                    elif send_count >18:
                        break
                    send_count += 1
                im.paste(util.get_icons_image("icon", "Leaked"), (x, y+220+offset*14))
                leak = util.calc_leak(player["leaksPerWave"][wave], wave)
                if leak > 0:
                    I1.text((x+offset, y+220+offset*14), str(leak)+"%", font=myFont_small, stroke_width=2, stroke_fill=(0, 0, 0),fill=(255, 255, 255))
                leak_count = 0
                for leak in player["leaksPerWave"][wave]:
                    if leak_count < 9:
                        im.paste(util.get_icons_image("icon_send", leak.replace(" ", "")),(x + offset * leak_count, y + 225 + offset * 15))
                    elif leak_count >= 9:
                        im.paste(util.get_icons_image("icon_send", leak.replace(" ", "")),(x + offset * (leak_count - 9), y + 225 + offset * 16))
                    elif leak_count > 18:
                        break
                    leak_count += 1
                x += offset * 10
            if first and start_wave == 0:
                first =  False
                os.umask(0)
                Path(shared_folder + gameid + "/").mkdir(parents=True, exist_ok=True)
            if start_wave != 0:
                random_id = util.id_generator()
                im.save(shared_folder+random_id+'.png')
                image_link = site + random_id+'.png'
            else:
                im.save(shared_folder + gameid + "/" + str(wave + 1) + '.jpg')
                image_link = site+gameid+"/"+str(wave+1)+'.jpg'
    else:
        image_link = site + gameid + "/" + str(start_wave) + '.jpg'
    if start_wave != 0:
        return image_link
    else:
        if not Path(Path(shared_folder + gameid + "/index.php")).is_file():
            shutil.copy("Files/index.php", shared_folder + gameid + "/")
        return site+gameid

def matchhistory_viewer(playername:str):
    playerid = legion_api.getid(playername)
    if playerid == 0:
        return playername + " player not found"
    elif playerid == 1:
        return "API error."
    profile = legion_api.getprofile(playerid)
    avatar = "https://cdn.legiontd2.com/" + profile['avatarUrl']
    playername = profile["playerName"]
    req_columns = [[GameData.game_id, GameData.queue, GameData.date, GameData.version, GameData.ending_wave, GameData.game_elo, GameData.player_ids,
                    PlayerData.player_id, PlayerData.player_name, PlayerData.player_elo, PlayerData.player_slot, PlayerData.game_result, PlayerData.elo_change],
                   ["game_id", "date", "version", "ending_wave", "game_elo"],
                   ["player_id", "player_name", "player_elo", "player_slot", "game_result", "elo_change"]]
    history_raw = drachbot_db.get_matchistory(playerid, 5, earlier_than_wave10=True, req_columns=req_columns)
    if len(history_raw) == 0:
        return "No games found."
    embed = discord.Embed(color=0x1cce3a, title="Match History")
    embed.set_author(name=playername, icon_url=avatar)
    def normalize_string(string1: str, string2: str):
        max_char = 14
        if len(string1) > max_char:
            string1 = string1[:max_char - 2] + ".."
        else:
            string1 = string1 + " " * (max_char - len(string1))
        if len(string2) > max_char:
            string2 = string2[:max_char - 2] + ".."
        else:
            string2 = string2 + " " * (max_char - len(string2))
        return [string1, string2]
    for game in history_raw:
        per_game_list = []
        elo_prefix = ""
        emoji = util.wave_emotes.get("wave"+str(game["ending_wave"]))
        for indx, player in enumerate(game["players_data"]):
            per_game_list.append([player["player_name"], util.get_ranked_emote(player["player_elo"])])
            if player["player_id"] != playerid: continue
            else:
                result = player["game_result"].capitalize()
                if player["elo_change"] > 0:
                    elo_change = player["elo_change"]
                    elo_prefix = "+"
                else:
                    elo_change = player["elo_change"]
                    elo_prefix = ""
        mod_date = game["date"].timestamp()
        game_timestamp = discord_timestamps.format_timestamp(mod_date, TimestampType.RELATIVE)
        west_players = normalize_string(per_game_list[0][0].replace("\n", ""), per_game_list[1][0].replace("\n", ""))
        east_players = normalize_string(per_game_list[2][0].replace("\n", ""), per_game_list[3][0].replace("\n", ""))
        embed.add_field(name="", value=(f"{emoji} [{result} on Wave {game["ending_wave"]} "
                                     f"({elo_prefix}{elo_change} Elo)](https://ltd2.pro/game/{game["game_id"]})"
                                     f" {game_timestamp}\n"
                                     f"{per_game_list[0][1]}`{west_players[0]}` {per_game_list[2][1]}`{east_players[0]}`\n"
                                     f"{per_game_list[1][1]}`{west_players[1]}` {per_game_list[3][1]}`{east_players[1]}`"),inline=False)
    return embed

class Elo(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    @app_commands.command(name="elo", description="Shows rank, elo and playtime.")
    @app_commands.describe(playername='Enter the playername.')
    async def elo(self, interaction: discord.Interaction, playername: str):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(elo, playername, 0))
                pool.shutdown()
                if type(response) == discord.Embed:
                    await interaction.followup.send(embed=response)
                else:
                    await interaction.followup.send(response)
            except Exception:
                print("/" + interaction.command.name + " failed. args: " + str(interaction.data.values()))
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")
    
    @app_commands.command(name="rank", description="Shows player info of a certain rank.")
    @app_commands.describe(rank='Enter a rank(number).')
    async def rank(self, interaction: discord.Interaction, rank: int):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(elo, None, rank))
                pool.shutdown()
                if type(response) == discord.Embed:
                    await interaction.followup.send(embed=response)
                else:
                    await interaction.followup.send(response)
            except Exception:
                print("/" + interaction.command.name + " failed. args: " + str(interaction.data.values()))
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")
    
    @app_commands.command(name="gamestats", description="Shows player stats.")
    @app_commands.describe(playername='Enter the playername.')
    async def gamestats(self, interaction: discord.Interaction, playername: str):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(gamestats, playername))
                pool.shutdown()
                if len(response) > 0:
                    await interaction.followup.send(response)
            except Exception:
                print("/" + interaction.command.name + " failed. args: " + str(interaction.data.values()))
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")
    
    @app_commands.command(name="matchhistory", description="Shows Match History of a player.")
    @app_commands.describe(playername="Enter playername.")
    async def matchhistory(self, interaction: discord.Interaction, playername: str):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(matchhistory_viewer, playername))
                pool.shutdown()
                if type(response) == discord.Embed:
                    await interaction.followup.send(embed=response)
                else:
                    await interaction.followup.send(response)
            except Exception:
                print("/" + interaction.command.name + " failed. args: " + str(interaction.data.values()))
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")
    
    @app_commands.command(name="gameid_viewer", description="Outputs image(s) of the gameid provided.")
    @app_commands.describe(game_id="Enter the GameID.", wave='Enter a specific wave to output, or just 0 for an Album of every wave.')
    async def gameid_viewer(self, interaction: discord.Interaction, game_id: str, wave: int):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                if len(game_id) != len("a3bcd7578727fa2f229e06d10d367d9d58ec94adaf13c955ba8872e9da46aaab"):
                    await interaction.followup.send("Invalid GameID format.")
                response = await loop.run_in_executor(pool, functools.partial(gameid_visualizer, game_id, wave))
                pool.shutdown()
                if len(response) > 0:
                    await interaction.followup.send(response)
            except Exception:
                print("/" + interaction.command.name + " failed. args: " + str(interaction.data.values()))
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")
    
    @app_commands.command(name="help", description="Gives some info on how to use all the commands.")
    async def help(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False, thinking=True)
        await interaction.followup.send("Common Inputs:\n"
                                        "**'playername'**: Needs to be a playername currently in use, or 'all' to retrieve data from any player in the Database if the command supports it\n"
                                        "**'games'**: Any integer, or 0 to get all games available based on the other inputs.\n"
                                        "**'min_elo'**: Any integer, defines minimum avg game elo that a game needs to be included into the set of games.\n"
                                        "**'patch'**: Any patch in XX.XX format. Appending multiple patches with comas as delimiter is possible.\n"
                                        "           -Also using a '+' infront of a single patch, counts as any all the patches that come after(including the initial one, works only within the same season version.)\n"
                                        "           -Using a '-' between 2 patches takes the entire range from those patches.")

async def setup(bot:commands.Bot):
    await bot.add_cog(Elo(bot))