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

def sendstats(games, min_elo, patch, sort="date", max_elo=9001):
    gameelo_list = []
    playerid = "all"
    req_columns = [[GameData.game_id, GameData.queue, GameData.date, GameData.version, GameData.ending_wave, GameData.game_elo, GameData.player_ids,
                    PlayerData.player_id, PlayerData.player_slot, PlayerData.game_result, PlayerData.player_elo, PlayerData.mercs_sent_per_wave,
                    PlayerData.build_per_wave, PlayerData.leaks_per_wave, PlayerData.kingups_sent_per_wave, PlayerData.fighter_value_per_wave],
                   ["game_id", "date", "version", "ending_wave", "game_elo"],
                   ["player_id", "player_slot", "game_result", "player_elo", "mercs_sent_per_wave", "build_per_wave",
                    "leaks_per_wave", "kingups_sent_per_wave", "fighter_value_per_wave"]]
    history_raw = drachbot_db.get_matchistory(playerid, games, min_elo, patch, sort_by=sort, earlier_than_wave10=True, req_columns=req_columns, max_elo=max_elo)
    if type(history_raw) == str:
        return history_raw
    if len(history_raw) == 0:
        return 'No games found.'
    send_dict = {}
    games = len(history_raw)
    for incmerc in util.incmercs:
        send_dict[incmerc.lower()] = {"Count": 0, "Wins": 0, "WaveCount": 0, "MercsCombo": {}, "Units": {}, "Waves": {}}

    for powermerc in util.powermercs:
        send_dict[powermerc.lower()] = {"Count": 0, "Wins": 0, "WaveCount": 0, "MercsCombo": {}, "Units": {}, "Waves": {}}

    send_to_map = {0: 2, 1: 3, 2: 1, 3: 0}

    total_waves = 0

    for game in history_raw:
        gameelo_list.append(game["game_elo"])
        players_data = game["players_data"]

        for player_index, player in enumerate(players_data):
            if playerid != "all" and player["player_id"] != playerid:
                continue

            total_waves += game["ending_wave"]

            for wave_index in range(game["ending_wave"]):
                mercs_wave_raw = player["mercs_sent_per_wave"][wave_index]
                if not mercs_wave_raw:
                    continue  # No mercs sent this wave

                # Unique mercs sent this wave (normalize)
                merc_names = set()
                for merc_str in mercs_wave_raw.split("!"):
                    merc = merc_str.split("_unit_")[0].replace("_", " ").lower()
                    merc_names.add(merc)

                # Enemy player board
                enemy_index = send_to_map.get(player_index)
                enemy_units = set()
                if enemy_index is not None and enemy_index < len(players_data):
                    enemy_player = players_data[enemy_index]
                    units_raw = enemy_player["build_per_wave"][wave_index]
                    if units_raw:
                        for unit_str in units_raw.split("!"):
                            unit = unit_str.split("_unit_")[0].replace("_", " ").lower()
                            enemy_units.add(unit)

                player_won = player["game_result"] == "won"

                for merc in merc_names:
                    if merc not in send_dict:
                        continue

                    # Count & Win
                    send_dict[merc]["Count"] += 1
                    if player_won:
                        send_dict[merc]["Wins"] += 1

                    # Combos: key by other mercs sent with it
                    for other_merc in merc_names:
                        if other_merc == merc:
                            continue
                        if other_merc not in send_dict[merc]["MercsCombo"]:
                            send_dict[merc]["MercsCombo"][other_merc] = {"Count": 0, "Wins": 0}
                        send_dict[merc]["MercsCombo"][other_merc]["Count"] += 1
                        if player_won:
                            send_dict[merc]["MercsCombo"][other_merc]["Wins"] += 1

                    # Units: enemy board units on that wave
                    for unit in enemy_units:
                        if unit not in send_dict[merc]["Units"]:
                            send_dict[merc]["Units"][unit] = {"Count": 0, "Wins": 0}
                        send_dict[merc]["Units"][unit]["Count"] += 1
                        if player_won:
                            send_dict[merc]["Units"][unit]["Wins"] += 1

                    # Waves: Count & Win for this wave
                    wave_key = f"Wave{wave_index + 1}"
                    if wave_key not in send_dict[merc]["Waves"]:
                        send_dict[merc]["Waves"][wave_key] = {"Count": 0, "Wins": 0}
                    send_dict[merc]["Waves"][wave_key]["Count"] += 1
                    if player_won:
                        send_dict[merc]["Waves"][wave_key]["Wins"] += 1

    avg_gameelo = round(sum(gameelo_list) / len(gameelo_list))

    for send in send_dict:
        send_dict[send]["WaveCount"] = total_waves

    return [send_dict, games, avg_gameelo]
    

class Sendstats(commands.Cog):
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
                    try:
                        _ = await loop.run_in_executor(pool, functools.partial(sendstats, 0, 1800, patch))
                    except Exception:
                        print("Database error, stopping website update....")
                        traceback.print_exc()
                        break
                    for elo in elos:
                        max_elo = elo+199
                        if elo == 2800:
                            max_elo = 9001
                        data = await loop.run_in_executor(pool, functools.partial(sendstats, 0, elo, patch, max_elo=max_elo))
                        for file in os.listdir(f"{util.shared2_folder}data/sendstats/"):
                            if file.startswith(patch) and int(file.split("_")[1]) == elo:
                                os.remove(f"{util.shared2_folder}data/sendstats/{file}")
                        with open(f"{util.shared2_folder}data/sendstats/{patch}_{elo}_{data[1]}_{data[2]}.msgpack", "wb") as f:
                            f.write(msgpack.packb(data[0], default=str))
            print("[WEBSITE]: Send Stats Website data update success!")
        except Exception:
            traceback.print_exc()

async def setup(bot:commands.Bot):
    await bot.add_cog(Sendstats(bot))