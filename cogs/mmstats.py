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

def get_roll(unit_dict, unit_name):
    if unit_name == "kingpin":
        unit_name = "angler"
    elif unit_name == "sakura":
        unit_name = "seedling"
    elif unit_name == "iron maiden":
        unit_name = "cursed casket"
    elif unit_name == "hell raiser":
        unit_name = "masked spirit"
    elif unit_name == "hydra":
        unit_name = "eggsack"
    elif unit_name == "oathbreaker final form":
        unit_name = "chained fist"
    elif unit_dict[unit_name]["upgradesFrom"]:
        unit_name = unit_dict[unit_name]["upgradesFrom"]
    return unit_name

def mmstats(playername, games, min_elo, patch, mastermind = 'All', sort="date", data_only = False, transparent = False):
    if playername == 'all':
        playerid = 'all'
    else:
        playerid = legion_api.getid(playername)
        if playerid == 0:
            return 'Player ' + playername + ' not found.'
        if playerid == 1:
            return 'API limit reached, you can still use "all" commands.'
    if mastermind == 'All':
        mmnames_list = util.mm_list
    elif mastermind == 'Megamind':
        mmnames_list = util.mm_list[:]
        mmnames_list.remove("Megamind")
    else:
        mmnames_list = [mastermind]
    masterminds_dict = {}
    for x in mmnames_list:
        masterminds_dict[x] = {"Count": 0, "Wins": 0, "Worker": 0, "Opener": {}, "Spell": {}, "Elo": 0, "Targets": {}, "Rolls": {}}
    unit_dict = {}
    with open('Files/json/units.json', 'r') as f:
        units_json = json.load(f)
    for u_js in units_json:
        if u_js["totalValue"] != '':
            string = u_js["unitId"]
            string = string.replace('_', ' ')
            string = string.replace(' unit id', '')
            if u_js["upgradesFrom"]:
                string2 = u_js["upgradesFrom"][0]
                string2 = string2.replace('_', ' ').replace(' unit id', '').replace('units ', '')
            else:
                string2 = ""
            unit_dict[string] = {'Count': 0, 'Wins': 0, 'Elo': 0, 'ComboUnit': {}, 'MMs': {}, 'Spells': {}, "upgradesFrom": string2}
    gameelo_list = []
    req_columns = [[GameData.game_id, GameData.queue, GameData.date, GameData.version, GameData.ending_wave, GameData.game_elo, GameData.player_ids,
                    PlayerData.player_id, PlayerData.player_slot, PlayerData.game_result, PlayerData.player_elo, PlayerData.legion,
                    PlayerData.opener, PlayerData.spell, PlayerData.workers_per_wave, PlayerData.megamind, PlayerData.build_per_wave, PlayerData.champ_location],
                   ["game_id", "date", "version", "ending_wave", "game_elo"],
                   ["player_id", "player_slot", "game_result", "player_elo", "legion", "opener", "spell", "workers_per_wave", "megamind", "build_per_wave",
                    "champ_location"]]
    history_raw = drachbot_db.get_matchistory(playerid, games, min_elo, patch, sort_by=sort, earlier_than_wave10=True, req_columns=req_columns)
    if type(history_raw) == str:
        return history_raw
    if len(history_raw) == 0:
        return 'No games found.'
    games = len(history_raw)
    if 'nova cup' in playerid:
        playerid = 'all'
    case_list = util.mm_list
    patches = set()
    megamind_count = 0
    for game in history_raw:
        if (game["version"].startswith('v10') or game["version"].startswith('v9')) and (mastermind == 'Megamind' or mastermind == 'Champion'):
            continue
        patches.add(game["version"])
        gameelo_list.append(game["game_elo"])
        match mastermind:
            case 'All' | 'Megamind':
                for player in game["players_data"]:
                    if player["player_id"] == playerid or playerid == "all":
                        if game["version"].startswith('v10') or game["version"].startswith('v9'):
                            player["megamind"] = False
                        if player["megamind"]:
                            megamind_count += 1
                            if mastermind != "Megamind":
                                mastermind_current = 'Megamind'
                            else:
                                if player["legion"] == "Megamind": continue
                                mastermind_current = player["legion"]
                        else:
                            if player["legion"] == "Mastermind":
                                continue
                            if mastermind == "Megamind":
                                continue
                            mastermind_current = player["legion"]
                        masterminds_dict[mastermind_current]["Count"] += 1
                        if player["game_result"] == 'won':
                            masterminds_dict[mastermind_current]["Wins"] += 1
                        try:
                            masterminds_dict[mastermind_current]["Worker"] += player["workers_per_wave"][9]
                        except IndexError:
                            pass
                        masterminds_dict[mastermind_current]['Elo'] += player["player_elo"]
                        if ',' in player["opener"]:
                            string = player["opener"]
                            opener_list = set(string.split(','))
                        else:
                            opener_list = [player["opener"]]
                        if player["spell"] not in masterminds_dict[mastermind_current]['Spell']:
                            masterminds_dict[mastermind_current]['Spell'][player["spell"]] = {"Count": 1, "Wins": 0}
                            if player["game_result"] == 'won':
                                masterminds_dict[mastermind_current]['Spell'][player["spell"]]["Wins"] += 1
                        else:
                            masterminds_dict[mastermind_current]['Spell'][player["spell"]]["Count"] += 1
                            if player["game_result"] == 'won':
                                masterminds_dict[mastermind_current]['Spell'][player["spell"]]["Wins"] += 1
                        for opener in opener_list:
                            if opener not in masterminds_dict[mastermind_current]['Opener']:
                                masterminds_dict[mastermind_current]['Opener'][opener] = {"Count": 1, "Wins": 0}
                                if player["game_result"] == 'won':
                                    masterminds_dict[mastermind_current]['Opener'][opener]["Wins"] += 1
                            else:
                                masterminds_dict[mastermind_current]['Opener'][opener]["Count"] += 1
                                if player["game_result"] == 'won':
                                    masterminds_dict[mastermind_current]['Opener'][opener]["Wins"] += 1
                        if player["legion"] == "Champion":
                            champ_loc = player["champ_location"].split("|")
                            try:
                                champ_loc = (float(champ_loc[0]), float(champ_loc[1]))
                            except Exception:
                                continue
                        else:
                            champ_loc = None
                        for unit in player["build_per_wave"][-1].split("!"):
                            try:
                                unit_loc = unit.split(":")[1].split("|")
                            except IndexError:
                                continue
                            unit_loc = (float(unit_loc[0]), float(unit_loc[1]))
                            unit_name = unit.split(":")[0].replace("_", " ").replace(" unit id", "")
                            if unit_name == "" or unit_name not in unit_dict:
                                continue
                            unit_name = get_roll(unit_dict, unit_name)
                            if unit_loc == champ_loc:
                                if unit_name in masterminds_dict["Champion"]["Targets"]:
                                    masterminds_dict["Champion"]["Targets"][unit_name]["Count"] += 1
                                else:
                                    masterminds_dict["Champion"]["Targets"][unit_name] = {"Count": 1, "Wins": 0}
                                if player["game_result"] == "won":
                                    masterminds_dict["Champion"]["Targets"][unit_name]["Wins"] += 1
                        fighter_set = set()
                        for unit2 in player["build_per_wave"][-1].split("!"):
                            unit_name2 = unit2.split(":")[0].replace("_", " ").replace(" unit id", "")
                            if unit_name2 == "" or unit_name2 not in unit_dict:
                                continue
                            unit_name2 = get_roll(unit_dict, unit_name2)
                            fighter_set.add(unit_name2)
                        for fighter in fighter_set:
                            if fighter in masterminds_dict[mastermind_current]["Rolls"]:
                                masterminds_dict[mastermind_current]["Rolls"][fighter]["Count"] += 1
                            else:
                                masterminds_dict[mastermind_current]["Rolls"][fighter] = {"Count": 1, "Wins": 0}
                            if player["game_result"] == "won":
                                masterminds_dict[mastermind_current]["Rolls"][fighter]["Wins"] += 1
            case mastermind if mastermind in case_list:
                for player in game["players_data"]:
                    if (playerid == 'all' or player["player_id"] == playerid) and (mastermind == player["legion"]):
                        mastermind_current = player["legion"]
                        masterminds_dict[mastermind_current]["Count"] += 1
                        if player["game_result"] == 'won':
                            masterminds_dict[mastermind_current]["Wins"] += 1
                        try:
                            masterminds_dict[mastermind_current]["Worker"] += player["workers_per_wave"][9]
                        except IndexError:
                            pass
                        masterminds_dict[mastermind_current]['Elo'] += player["player_elo"]
                        if ',' in player["opener"]:
                            string = player["opener"]
                            opener_list = set(string.split(','))
                        else:
                            opener_list = [player["opener"]]
                        if player["spell"] not in masterminds_dict[mastermind_current]['Spell']:
                            masterminds_dict[mastermind_current]['Spell'][player["spell"]] = {"Count": 1, "Wins": 0}
                            if player["game_result"] == 'won':
                                masterminds_dict[mastermind_current]['Spell'][player["spell"]]["Wins"] += 1
                        else:
                            masterminds_dict[mastermind_current]['Spell'][player["spell"]]["Count"] += 1
                            if player["game_result"] == 'won':
                                masterminds_dict[mastermind_current]['Spell'][player["spell"]]["Wins"] += 1
                        for opener in opener_list:
                            if opener not in masterminds_dict[mastermind_current]['Opener']:
                                masterminds_dict[mastermind_current]['Opener'][opener] = {"Count": 1, "Wins": 0}
                                if player["game_result"] == 'won':
                                    masterminds_dict[mastermind_current]['Opener'][opener]["Wins"] += 1
                            else:
                                masterminds_dict[mastermind_current]['Opener'][opener]["Count"] += 1
                                if player["game_result"] == 'won':
                                    masterminds_dict[mastermind_current]['Opener'][opener]["Wins"] += 1
                        if player["legion"] == "Champion":
                            champ_loc = player["champ_location"].split("|")
                            try:
                                champ_loc = (float(champ_loc[0]), float(champ_loc[1]))
                            except Exception:
                                continue
                            for unit in player["build_per_wave"][-1].split("!"):
                                try:
                                    unit_loc = unit.split(":")[1].split("|")
                                except IndexError:
                                    continue
                                unit_loc = (float(unit_loc[0]), float(unit_loc[1]))
                                if unit_loc == champ_loc:
                                    unit_name = unit.split(":")[0].replace("_", " ").replace(" unit id", "")
                                    if unit_name == "" or unit_name not in unit_dict:
                                        continue
                                    unit_name = get_roll(unit_dict, unit_name)
                                    if unit_name in masterminds_dict["Champion"]["Targets"]:
                                        masterminds_dict["Champion"]["Targets"][unit_name]["Count"] += 1
                                    else:
                                        masterminds_dict["Champion"]["Targets"][unit_name] = {"Count": 1, "Wins": 0}
                                    if player["game_result"] == "won":
                                        masterminds_dict["Champion"]["Targets"][unit_name]["Wins"] += 1
    new_patches = []
    for x in patches:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches = list(dict.fromkeys(new_patches))
    patches = sorted(patches, key=lambda x: int(x.split(".")[0] + x.split(".")[1]), reverse=True)
    newIndex = sorted(masterminds_dict, key=lambda x: masterminds_dict[x]['Count'], reverse=True)
    masterminds_dict = {k: masterminds_dict[k] for k in newIndex}
    try:
        avg_gameelo = round(sum(gameelo_list)/len(gameelo_list))
    except ZeroDivisionError:
        avg_gameelo = 0
    if data_only:
        if mastermind == "Megamind":
            return [masterminds_dict, megamind_count, avg_gameelo]
        else:
            return [masterminds_dict, games, avg_gameelo]
    match mastermind:
        case 'All':
            return image_generators.create_image_stats(masterminds_dict, games, playerid, avg_gameelo, patches, mode="Mastermind", transparency=transparent)
        case mastermind if mastermind in case_list:
            return image_generators.create_image_stats_specific(masterminds_dict, games, playerid, avg_gameelo, patches, mode="Mastermind", specific_value=mastermind, transparency=transparent)
        case 'Megamind':
            return image_generators.create_image_stats(masterminds_dict, games, playerid, avg_gameelo, patches, "Mastermind", True, megamind_count, transparency=transparent)

class MMstats(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.website_data.start()
    
    def cog_unload(self) -> None:
        self.website_data.cancel()
    
    @app_commands.command(name="mmstats", description="Mastermind stats.")
    @app_commands.describe(playername='Enter playername or "all" for all available data.', games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           min_elo='Enter minium average game elo to include in the data set',
                           patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.',
                           mastermind='Select a Mastermind for specific stats, or All for a general overview.', sort="Sort by?",
                           transparency="Transparent Background?")
    @app_commands.choices(mastermind=util.mm_choices)
    @app_commands.choices(sort=[
        discord.app_commands.Choice(name='date', value="date"),
        discord.app_commands.Choice(name='elo', value="elo")
    ])
    async def mmstats(self, interaction: discord.Interaction, playername: str, games: int = 0, min_elo: int = 0, patch: str = "",
                      mastermind: discord.app_commands.Choice[str] = "All", sort: discord.app_commands.Choice[str] = "date", transparency: bool = False):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            if playername.lower() == "all" and games == 0 and min_elo == 0 and not patch:
                min_elo = util.get_current_minelo()
            try:
                mastermind = mastermind.value
            except AttributeError:
                pass
            try:
                sort = sort.value
            except AttributeError:
                pass
            if not patch:
                patch = util.get_current_patches()
            try:
                response = await loop.run_in_executor(pool, functools.partial(mmstats, str(playername).lower(), games, min_elo, patch, mastermind, sort=sort, transparent=transparency))
                pool.shutdown()
                if response.endswith(".png"):
                    await interaction.followup.send(file=discord.File(response))
                else:
                    await interaction.followup.send(response)
            except Exception:
                print("/" + interaction.command.name + " failed. args: " + str(interaction.data.values()))
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")
    
    @tasks.loop(time=util.task_times2) #datetime.time(datetime.now(timezone.utc)+timedelta(seconds=5)) util.task_times2
    async def website_data(self):
        print("Starting Website Update")
        patches = util.get_current_patches(only_current=True)
        elos = util.website_elos
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ProcessPoolExecutor() as pool:
                for patch in patches:
                    try:
                        _ = await loop.run_in_executor(pool, functools.partial(mmstats, "all", 0, 1800, patch, data_only=True))
                    except Exception:
                        print("Database error, stopping website update....")
                        traceback.print_exc()
                        break
                    for elo in elos:
                        data = await loop.run_in_executor(pool, functools.partial(mmstats, "all", 0, elo, patch, data_only=True))
                        for file in os.listdir(f"{util.shared2_folder}data/mmstats/"):
                            if file.startswith(patch) and int(file.split("_")[1]) == elo:
                                os.remove(f"{util.shared2_folder}data/mmstats/{file}")
                        with open(f"{util.shared2_folder}data/mmstats/{patch}_{elo}_{data[1]}_{data[2]}.json", "w") as f:
                            json.dump(data[0], f)
                            f.close()
                        data = await loop.run_in_executor(pool, functools.partial(mmstats, "all", 0, elo, patch, mastermind="Megamind", data_only=True))
                        for file in os.listdir(f"{util.shared2_folder}data/megamindstats/"):
                            if file.startswith(patch) and int(file.split("_")[1]) == elo:
                                os.remove(f"{util.shared2_folder}data/megamindstats/{file}")
                        with open(f"{util.shared2_folder}data/megamindstats/{patch}_{elo}_{data[1]}_{data[2]}.json", "w") as f:
                            json.dump(data[0], f)
                            f.close()
            print("[WEBSITE]: MM Stats Website data update success!")
        except Exception:
            traceback.print_exc()

async def setup(bot:commands.Bot):
    await bot.add_cog(MMstats(bot))