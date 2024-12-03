import json
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
                    PlayerData.build_per_wave, PlayerData.leaks_per_wave, PlayerData.fighter_value_per_wave, PlayerData.legion, PlayerData.champ_location],
                   ["game_id", "date", "version", "ending_wave", "game_elo"],
                   ["player_id", "player_name", "player_slot", "game_result", "player_elo", "workers_per_wave", "mercs_received_per_wave", "build_per_wave",
                    "leaks_per_wave", "fighter_value_per_wave", "legion", "champ_location"]]
    history_raw = drachbot_db.get_matchistory(playerid, games, min_elo, patch, sort_by=sort, earlier_than_wave10=True, req_columns=req_columns)
    if type(history_raw) == str:
        return history_raw
    if len(history_raw) == 0:
        return 'No games found.'
    proleaks_dict = {"Wave1": [], "Wave2": [],"Wave3": []}
    games = len(history_raw)
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
    avg_gameelo = round(sum(gameelo_list) / len(gameelo_list))
    return [proleaks_dict, games, avg_gameelo]
    

class Proleaks(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.website_data.start()
    
    def cog_unload(self) -> None:
        self.website_data.cancel()
    
    @tasks.loop(time=util.task_times4) #datetime.time(datetime.now(timezone.utc)+timedelta(seconds=5)) util.task_times2
    async def website_data(self):
        patches = util.website_patches
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ProcessPoolExecutor() as pool:
                for patch in patches:
                    try:
                        data = await loop.run_in_executor(pool, functools.partial(proleaks, 0, 2000, patch))
                    except Exception:
                        print("Database error, stopping website update....")
                        traceback.print_exc()
                        break
                    for file in os.listdir(f"{util.shared2_folder}data/proleaks/"):
                        if file.startswith(patch) and int(file.split("_")[1]) == 0:
                            os.remove(f"{util.shared2_folder}data/proleaks/{file}")
                    with open(f"{util.shared2_folder}data/proleaks/{patch}_{0}_{data[1]}_{data[2]}.json", "w") as f:
                        json.dump(data[0], f)
                        f.close()
            print("[WEBSITE]: Proleaks Website data update success!")
        except Exception:
            traceback.print_exc()

async def setup(bot:commands.Bot):
    await bot.add_cog(Proleaks(bot))