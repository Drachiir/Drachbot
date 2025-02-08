import msgpack
import os
from datetime import datetime, timezone, timedelta

import discord
from discord import app_commands
from discord.ext import commands, tasks
import platform
import asyncio
import concurrent.futures
import traceback
import functools
import time
import image_generators
import drachbot_db
import util
import legion_api
from peewee_pg import GameData, PlayerData

def proleaks(games, min_elo, patch, sort="date"):
    gameelo_list = []
    playerid = "all"
    req_columns = [[GameData.game_id, GameData.queue, GameData.date, GameData.version, GameData.ending_wave, GameData.game_elo, GameData.player_ids,
                    PlayerData.player_id, PlayerData.player_name, PlayerData.player_slot, PlayerData.game_result, PlayerData.player_elo, PlayerData.workers_per_wave, PlayerData.mercs_received_per_wave,
                    PlayerData.build_per_wave, PlayerData.leaks_per_wave, PlayerData.fighter_value_per_wave, PlayerData.legion, PlayerData.champ_location, PlayerData.opener],
                   ["game_id", "date", "version", "ending_wave", "game_elo"],
                   ["player_id", "player_name", "player_slot", "game_result", "player_elo", "workers_per_wave", "mercs_received_per_wave", "build_per_wave",
                    "leaks_per_wave", "fighter_value_per_wave", "legion", "champ_location", "opener"]]
    history_raw = drachbot_db.get_matchistory(playerid, games, min_elo, patch, sort_by=sort, earlier_than_wave10=True, req_columns=req_columns)
    if type(history_raw) == str:
        return history_raw
    if len(history_raw) == 0:
        return 'No games found.'
    proleaks_dict = {"Wave1": [], "Wave2": [],"Wave3": []}
    opener_dict = {}
    games = len(history_raw)
    min_elo = util.get_current_minelo()
    for game in history_raw:
        gameelo_list.append(game["game_elo"])
        for player in game["players_data"]:
            for i in range(3):
                try:
                    if len(player["leaks_per_wave"][i]) > 0:
                        leak_percent = util.calc_leak(player["leaks_per_wave"][i], wave=i)
                        if leak_percent < 40:
                            if player["legion"] == "Champion":
                                champ_location = player["champ_location"]
                            else:
                                champ_location = None
                            proleaks_dict[f"Wave{i+1}"].append({"playername": player["player_name"],
                                                                "mastermind": player["legion"],
                                                                "game_id": game["game_id"],
                                                                "elo": player["player_elo"],
                                                                "build": player["build_per_wave"][i],
                                                                "champ": champ_location,
                                                                "leak": player["leaks_per_wave"][i],
                                                                "send": player["mercs_received_per_wave"][i],
                                                                "value": player["fighter_value_per_wave"][i]})
                except IndexError:
                    continue

            if len(player["leaks_per_wave"][0]) == 0:
                if player["player_elo"] < min_elo:
                    continue
                if player["legion"] == "Champion":
                    champ_location = player["champ_location"]
                else:
                    champ_location = None
                opener_key = player["opener"].replace(" ", "")
                if opener_key not in opener_dict:
                    opener_dict[opener_key] = {"Count": 0, "Data": []}
                opener_dict[opener_key]["Count"] += 1
                opener_dict[opener_key]["Data"].append({"playername": player["player_name"],
                                    "mastermind": player["legion"],
                                    "game_id": game["game_id"],
                                    "elo": player["player_elo"],
                                    "build": player["build_per_wave"][0],
                                    "champ": champ_location,
                                    "leak": player["leaks_per_wave"][0],
                                    "send": player["mercs_received_per_wave"][0],
                                    "value": player["fighter_value_per_wave"][0]})

    avg_gameelo = round(sum(gameelo_list) / len(gameelo_list))
    newIndex = sorted(opener_dict, key=lambda x: opener_dict[x]['Count'], reverse=True)
    opener_dict = {k: opener_dict[k] for k in newIndex}
    return [proleaks_dict, games, avg_gameelo, opener_dict]
    

class Proleaks(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.website_data.start()
    
    def cog_unload(self) -> None:
        self.website_data.cancel()
    
    @tasks.loop(time=datetime.time(datetime.now(timezone.utc)+timedelta(seconds=5))) #datetime.time(datetime.now(timezone.utc)+timedelta(seconds=5)) util.task_times4
    async def website_data(self):
        patches = util.get_current_patches(only_current=True)
        patches = ["12.00", "11.11", "11.10", "11.09", "11.08", "11.07", "11.06", "11.05", "11.04", "11.03", "11.02", "11.01", "11.00"]
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ProcessPoolExecutor() as pool:
                for patch in patches:
                    try:
                        data = await loop.run_in_executor(pool, functools.partial(proleaks, 0, 1600, patch))
                    except Exception:
                        print("Database error, stopping website update....")
                        traceback.print_exc()
                        break
                    # PROLEAKS
                    for file in os.listdir(f"{util.shared2_folder}data/proleaks/"):
                        if file.startswith(patch) and int(file.split("_")[1]) == 0:
                            os.remove(f"{util.shared2_folder}data/proleaks/{file}")
                    with open(f"{util.shared2_folder}data/proleaks/{patch}_{0}_{data[1]}_{data[2]}.msgpack", "wb") as f:
                        f.write(msgpack.packb(data[0], default=str))
                    # OPENERS
                    for file in os.listdir(f"{util.shared2_folder}data/openers/"):
                        if file.startswith(patch) and int(file.split("_")[1]) == 0:
                            os.remove(f"{util.shared2_folder}data/openers/{file}")
                    with open(f"{util.shared2_folder}data/openers/{patch}_{0}_{data[1]}_{data[2]}.msgpack", "wb") as f:
                        f.write(msgpack.packb(data[3], default=str))
            print("[WEBSITE]: Proleaks Website data update success!")
        except Exception:
            traceback.print_exc()

async def setup(bot:commands.Bot):
    await bot.add_cog(Proleaks(bot))