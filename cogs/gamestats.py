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
import drachbot_db
import util
from peewee_pg import GameData, PlayerData
import msgpack

def gamestats(games, min_elo, patch, sort="date", playerid = "all", option = "send", max_elo=9001):
    gameelo_list = []
    if option == "send":
        col1 = PlayerData.mercs_sent_per_wave
        col2 = PlayerData.kingups_sent_per_wave
        option_key = "mercs_sent_per_wave"
        option_key2 = "kingups_sent_per_wave"
    else:
        col1 = PlayerData.mercs_received_per_wave
        col2 = PlayerData.kingups_received_per_wave
        option_key = "mercs_received_per_wave"
        option_key2 = "kingups_received_per_wave"
    req_columns = [[GameData.game_id, GameData.queue, GameData.date, GameData.version, GameData.ending_wave, GameData.game_elo, GameData.game_length, GameData.player_ids,
                    PlayerData.player_id, PlayerData.player_slot, PlayerData.game_result, PlayerData.player_elo, PlayerData.workers_per_wave, col1,
                    PlayerData.build_per_wave, PlayerData.leaks_per_wave, col2, PlayerData.fighter_value_per_wave, PlayerData.income_per_wave],
                   ["game_id", "date", "version", "ending_wave", "game_elo", "game_length"],
                   ["player_id", "player_slot", "game_result", "player_elo", "workers_per_wave", "mercs_sent_per_wave", "build_per_wave",
                    "leaks_per_wave", "kingups_sent_per_wave", "fighter_value_per_wave", "income_per_wave"]]
    history_raw = drachbot_db.get_matchistory(playerid, games, min_elo, patch, sort_by=sort, earlier_than_wave10=True, req_columns=req_columns, max_elo=max_elo)
    if type(history_raw) == str:
        return history_raw
    if len(history_raw) == 0:
        return 'No games found.'
    wave_dict = {}
    wave1_dict = {"Snail":0, "Save":0, "King": {"Upgrade King Attack": 0, "Upgrade King Spell": 0, "Upgrade King Regen": 0}}
    games = len(history_raw)
    game_length = 0
    for i in range(1, 22):
        wave_dict[f"wave{i}"] = {"Count": 0, "EndCount": 0, "SendCount": 0, "LeakedGold": 0,
                                 "PowerMerc": 0, "IncomeMerc": 0, "Value": 0, "Worker": 0, "Income": 0}
    for game in history_raw:
        gameelo_list.append(game["game_elo"])
        wave_dict[f"wave{game["ending_wave"]}"]["EndCount"] += 1
        game_length += game["game_length"]
        for player in game["players_data"]:
            if player["player_id"] != playerid and playerid != "all":
                continue
            for i in range(game["ending_wave"]):
                wave_dict[f"wave{i + 1}"]["Count"] += 1
                try:
                    wave_dict[f"wave{i + 1}"]["Worker"] += player["workers_per_wave"][i]
                    wave_dict[f"wave{i + 1}"]["Income"] += player["income_per_wave"][i]
                    wave_dict[f"wave{i + 1}"]["Value"] += player["fighter_value_per_wave"][i]
                    send_total = 0
                    if player["workers_per_wave"][i] > 5:
                        small_send = (player["workers_per_wave"][i] - 5) / 4 * 20
                    else:
                        small_send = 0
                    if player[option_key][i]:
                        send = util.count_mythium(player[option_key][i], seperate=True)
                        send_total = sum(send)
                        wave_dict[f"wave{i + 1}"]["IncomeMerc"] += send[0]
                        wave_dict[f"wave{i + 1}"]["PowerMerc"] += send[1]
                    if player[option_key2][i]:
                        send_total += len(player[option_key2][i].split("!")) * 20
                        wave_dict[f"wave{i + 1}"]["IncomeMerc"] += len(player[option_key2][i].split("!")) * 20
                    if send_total > small_send:
                        wave_dict[f"wave{i + 1}"]["SendCount"] += 1
                    if player["leaks_per_wave"][i]:
                        wave_dict[f"wave{i + 1}"]["LeakedGold"] += util.calc_leak(player["leaks_per_wave"][i], i, return_gold=True)
                except IndexError:
                    continue
            if len(player[option_key][0]) > 0:
                if player[option_key][0].split("!")[0] == 'Snail':
                    wave1_dict["Snail"] += 1
            elif len(player[option_key2][0]) > 0:
                wave1_dict["King"][str(player[option_key2][0].split("!")[0])] += 1
            else:
                wave1_dict["Save"] += 1
    avg_gameelo = round(sum(gameelo_list) / len(gameelo_list))
    return [wave_dict, wave1_dict, game_length, games, avg_gameelo]


class Gamestats(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.website_data.start()

    def cog_unload(self) -> None:
        self.website_data.cancel()

    @tasks.loop(time=util.task_times2) #datetime.time(datetime.now(timezone.utc)+timedelta(seconds=5)) util.task_times2
    async def website_data(self):
        patches = util.get_current_patches(only_current=True)
        elos = util.website_elos
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ProcessPoolExecutor() as pool:
                for patch in patches:
                    try:
                        _ = await loop.run_in_executor(pool, functools.partial(gamestats, 0, 1800, patch))
                    except Exception:
                        print("Database error, stopping website update....")
                        traceback.print_exc()
                        break
                    for file in os.listdir(f"{util.shared2_folder}data/gamestats/"):
                        if file.startswith(patch):
                            os.remove(f"{util.shared2_folder}data/gamestats/{file}")
                    for elo in elos:
                        max_elo = elo+199
                        if elo == 2800:
                            max_elo = 9001
                        data = await loop.run_in_executor(pool, functools.partial(gamestats, 0, elo, patch, max_elo=max_elo))
                        with open(f"{util.shared2_folder}data/gamestats/{patch}_{elo}_{data[3]}_{data[4]}.msgpack", "wb") as f:
                            f.write(msgpack.packb({"Wave1Stats": data[1], "GameLength": data[2], "WaveDict": data[0]}, default=str))
            print("[WEBSITE]: Game Stats Website data update success!")
        except Exception:
            traceback.print_exc()

async def setup(bot:commands.Bot):
    await bot.add_cog(Gamestats(bot))