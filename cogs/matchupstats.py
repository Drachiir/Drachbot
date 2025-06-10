import os
from datetime import datetime, timezone, timedelta

import discord
import msgpack
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import concurrent.futures
import traceback
import functools
import json
import difflib
import re
import drachbot_db
import util
import legion_api
from peewee_pg import GameData, PlayerData

player_map = {1:[1,2,3],2:[0,3,2],5:[3,1,0],6:[2,0,1]}

def matchupstats(playerid, games, patch, min_elo = 0, max_elo = 9001):
    req_columns = [[GameData.game_id, GameData.queue, GameData.date, GameData.version, GameData.ending_wave, GameData.game_elo, GameData.player_ids,
                    PlayerData.player_id, PlayerData.player_name, PlayerData.player_slot, PlayerData.game_result, PlayerData.legion, PlayerData.elo_change,
                    PlayerData.party_size, PlayerData.player_elo],
                   ["game_id", "date", "version", "ending_wave", "game_elo"],
                   ["player_id", "player_name", "player_slot", "game_result", "legion", "elo_change", "party_size", "player_elo"]]
    history_raw = drachbot_db.get_matchistory(playerid, games, min_elo=min_elo, max_elo=max_elo, patch=patch, earlier_than_wave10=True, req_columns=req_columns)
    if type(history_raw) == str:
        return history_raw
    games = len(history_raw)
    if games == 0:
        return 'No games found.'
    gameelo_list = []
    mmnames_list = util.mm_list[:]
    mmnames_list.remove("Megamind")
    masterminds_dict = {}
    for x in mmnames_list:
        masterminds_dict[x] = {"Count": 0, "Wins": 0, "Elo": 0, "Teammates": {}, "Enemies1": {}, "Enemies2": {}}
    for game in history_raw:
        for player in game["players_data"]:
            if playerid != "all" and playerid != player["player_id"]:
                continue

            teammate = game["players_data"][player_map[player["player_slot"]][0]]
            enemy1 = game["players_data"][player_map[player["player_slot"]][1]]
            enemy2 = game["players_data"][player_map[player["player_slot"]][2]]

            masterminds_dict[player["legion"]]["Count"] += 1
            masterminds_dict[player["legion"]]["Elo"] += player["player_elo"]

            if not teammate["legion"] in masterminds_dict[player["legion"]]["Teammates"]:
                masterminds_dict[player["legion"]]["Teammates"][teammate["legion"]] = {"Wins": 0, "Count": 0}
            if not enemy1["legion"] in masterminds_dict[player["legion"]]["Enemies1"]:
                masterminds_dict[player["legion"]]["Enemies1"][enemy1["legion"]] = {"Wins": 0, "Count": 0}
            if not enemy2["legion"] in masterminds_dict[player["legion"]]["Enemies2"]:
                masterminds_dict[player["legion"]]["Enemies2"][enemy2["legion"]] = {"Wins": 0, "Count": 0}

            masterminds_dict[player["legion"]]["Teammates"][teammate["legion"]]["Count"] += 1
            masterminds_dict[player["legion"]]["Enemies1"][enemy1["legion"]]["Count"] += 1
            masterminds_dict[player["legion"]]["Enemies2"][enemy2["legion"]]["Count"] += 1

            if player["game_result"] == "won":
                masterminds_dict[player["legion"]]["Wins"] += 1
                masterminds_dict[player["legion"]]["Teammates"][teammate["legion"]]["Wins"] += 1
                masterminds_dict[player["legion"]]["Enemies1"][enemy1["legion"]]["Wins"] += 1
                masterminds_dict[player["legion"]]["Enemies2"][enemy2["legion"]]["Wins"] += 1

    try:
        avg_gameelo = round(sum(gameelo_list) / len(gameelo_list))
    except ZeroDivisionError:
        avg_gameelo = 0

    # After iterating through all games, merge Enemies1 and Enemies2 into Enemies
    for mmname in masterminds_dict:
        merged_enemies = {}
        enemies1 = masterminds_dict[mmname]["Enemies1"]
        enemies2 = masterminds_dict[mmname]["Enemies2"]

        # Add enemies from Enemies1
        for legion, data in enemies1.items():
            merged_enemies[legion] = {"Wins": data["Wins"], "Count": data["Count"]}

        # Merge in enemies from Enemies2
        for legion, data in enemies2.items():
            if legion not in merged_enemies:
                merged_enemies[legion] = {"Wins": data["Wins"], "Count": data["Count"]}
            else:
                merged_enemies[legion]["Wins"] += data["Wins"]
                merged_enemies[legion]["Count"] += data["Count"]

        masterminds_dict[mmname]["Enemies"] = merged_enemies

    return [masterminds_dict, games, avg_gameelo]

class MatchupStats(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.website_data.start()

    def cog_unload(self) -> None:
        self.website_data.cancel()

    @tasks.loop(time=datetime.time(datetime.now(timezone.utc)+timedelta(seconds=5))) #datetime.time(datetime.now(timezone.utc)+timedelta(seconds=5)) util.task_times2
    async def website_data(self):
        patches = util.get_current_patches(only_current=True)
        elos = util.website_elos
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ProcessPoolExecutor() as pool:
                for patch in patches:
                    for elo in elos:
                        max_elo = elo+199
                        if elo == 2800:
                            max_elo = 9001
                        data = await loop.run_in_executor(pool, functools.partial(matchupstats, "all", 0, patch, min_elo = elo, max_elo=max_elo))
                        for file in os.listdir(f"{util.shared2_folder}data/matchupstats/"):
                            if file.startswith(patch) and int(file.split("_")[1]) == elo:
                                os.remove(f"{util.shared2_folder}data/matchupstats/{file}")
                        with open(f"{util.shared2_folder}data/matchupstats/{patch}_{elo}_{data[1]}_{data[2]}.msgpack", "wb") as f:
                            f.write(msgpack.packb(data[0], default=str))
            print("[WEBSITE]: Matchup Stats Website data update success!")
        except Exception:
            traceback.print_exc()
    


async def setup(bot:commands.Bot):
    await bot.add_cog(MatchupStats(bot))