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
import msgpack

def wavestats(games, min_elo, patch, sort="date", max_elo=9001):
    gameelo_list = []
    playerid = "all"
    req_columns = [[GameData.game_id, GameData.queue, GameData.date, GameData.version, GameData.ending_wave, GameData.game_elo, GameData.player_ids,
                    PlayerData.player_id, PlayerData.player_slot, PlayerData.game_result, PlayerData.player_elo, PlayerData.workers_per_wave, PlayerData.mercs_sent_per_wave,
                    PlayerData.build_per_wave, PlayerData.leaks_per_wave, PlayerData.kingups_sent_per_wave, PlayerData.fighter_value_per_wave],
                   ["game_id", "date", "version", "ending_wave", "game_elo"],
                   ["player_id", "player_slot", "game_result", "player_elo", "workers_per_wave", "mercs_sent_per_wave", "build_per_wave",
                    "leaks_per_wave", "kingups_sent_per_wave", "fighter_value_per_wave"]]
    history_raw = drachbot_db.get_matchistory(playerid, games, min_elo, patch, sort_by=sort, earlier_than_wave10=True, req_columns=req_columns, max_elo=max_elo)
    if type(history_raw) == str:
        return history_raw
    if len(history_raw) == 0:
        return 'No games found.'
    wave_dict = {}
    games = len(history_raw)
    for i in range(1,22):
        wave_dict[f"wave{i}"] = {"Count": 0, "EndCount": 0, "SendCount": 0, "LeakedGold": 0, "Mercs": {}, "Units": {}}
    for game in history_raw:
        gameelo_list.append(game["game_elo"])
        wave_dict[f"wave{game["ending_wave"]}"]["EndCount"] += 1
        for i in range(game["ending_wave"]):
            wave_dict[f"wave{i+1}"]["Count"] += 1
            for player in game["players_data"]:
                try:
                    if player["player_id"] != playerid and playerid != "all":
                        continue
                    #FIGURE OUT IF THERE WAS A SEND ON THIS WAVE
                    if player["mercs_sent_per_wave"][i]:
                        wave_dict[f"wave{i+1}"]["SendCount"] += 1
                        #ITERATE THROUGH MERCS SENT IF THERE WAS A SEND
                        merc_wave_temp = player["mercs_sent_per_wave"][i].split("!")
                        merc_wave = set()
                        for merc in merc_wave_temp:
                            merc = merc.split("_unit_")[0].replace("_", " ")
                            merc_wave.add(merc)
                        for merc in merc_wave:
                            if merc not in wave_dict[f"wave{i+1}"]["Mercs"]:
                                wave_dict[f"wave{i+1}"]["Mercs"][merc] = {"Count": 1, "Wins": 0}
                            else:
                                wave_dict[f"wave{i+1}"]["Mercs"][merc]["Count"] += 1
                            if player["game_result"] == "won":
                                wave_dict[f"wave{i+1}"]["Mercs"][merc]["Wins"] += 1
                    elif player["kingups_sent_per_wave"][i]:
                        wave_dict[f"wave{i+1}"]["SendCount"] += 1
                        kingups_list = player["kingups_sent_per_wave"][i].split("!")
                        for kingup in kingups_list:
                            if kingup not in wave_dict[f"wave{i+1}"]["Mercs"]:
                                wave_dict[f"wave{i+1}"]["Mercs"][kingup] = {"Count": 1, "Wins": 0}
                            else:
                                wave_dict[f"wave{i+1}"]["Mercs"][kingup]["Count"] += 1
                            if player["game_result"] == "won":
                                wave_dict[f"wave{i+1}"]["Mercs"][kingup]["Wins"] += 1
                    else:
                        if "Save" not in wave_dict[f"wave{i + 1}"]["Mercs"]:
                            wave_dict[f"wave{i + 1}"]["Mercs"]["Save"] = {"Count": 1, "Wins": 0}
                        else:
                            wave_dict[f"wave{i + 1}"]["Mercs"]["Save"]["Count"] += 1
                        if player["game_result"] == "won":
                            wave_dict[f"wave{i + 1}"]["Mercs"]["Save"]["Wins"] += 1
                    #ITERATE THROUGH UNITS BUILT
                    unit_wave_temp = player["build_per_wave"][i].split("!")
                    unit_wave = set()
                    for unit in unit_wave_temp:
                        unit = unit.split("_unit_")[0].replace("_", " ")
                        unit_wave.add(unit)
                    for unit in unit_wave:
                        if unit not in wave_dict[f"wave{i+1}"]["Units"]:
                            wave_dict[f"wave{i+1}"]["Units"][unit] = {"Count": 1, "Wins": 0}
                        else:
                            wave_dict[f"wave{i+1}"]["Units"][unit]["Count"] += 1
                        if player["game_result"] == "won":
                            wave_dict[f"wave{i+1}"]["Units"][unit]["Wins"] += 1
                    #ITERATE THROUGH LEAKED UNITS IF THERE ARE ANY
                    if player["leaks_per_wave"][i]:
                        wave_dict[f"wave{i+1}"]["LeakedGold"] += util.calc_leak(player["leaks_per_wave"][i], i, return_gold=True)
                except IndexError:
                    continue
    avg_gameelo = round(sum(gameelo_list) / len(gameelo_list))
    return [wave_dict, games, avg_gameelo]
    

class Wavestats(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.website_data.start()
    
    def cog_unload(self) -> None:
        self.website_data.cancel()
    
    @tasks.loop(time=util.task_times4) #datetime.time(datetime.now(timezone.utc)+timedelta(seconds=5)) util.task_times2
    async def website_data(self):
        patches = util.get_current_patches(only_current=True)
        elos = util.website_elos
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ProcessPoolExecutor() as pool:
                for patch in patches:
                    try:
                        _ = await loop.run_in_executor(pool, functools.partial(wavestats, 0, 1800, patch))
                    except Exception:
                        print("Database error, stopping website update....")
                        traceback.print_exc()
                        break
                    for elo in elos:
                        max_elo = elo+199
                        if elo == 2800:
                            max_elo = 9001
                        data = await loop.run_in_executor(pool, functools.partial(wavestats, 0, elo, patch, max_elo=max_elo))
                        for file in os.listdir(f"{util.shared2_folder}data/wavestats/"):
                            if file.startswith(patch) and int(file.split("_")[1]) == elo:
                                os.remove(f"{util.shared2_folder}data/wavestats/{file}")
                        with open(f"{util.shared2_folder}data/wavestats/{patch}_{elo}_{data[1]}_{data[2]}.msgpack", "wb") as f:
                            f.write(msgpack.packb(data[0], default=str))
            print("[WEBSITE]: Wave Stats Website data update success!")
        except Exception:
            traceback.print_exc()

async def setup(bot:commands.Bot):
    await bot.add_cog(Wavestats(bot))