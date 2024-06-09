import os
import platform

import discord
from discord import app_commands
from discord.ext import commands, tasks
import asyncio
import concurrent.futures
import traceback
import functools
import json
import difflib

import image_generators
import drachbot_db
import util
import legion_api
from peewee_pg import GameData, PlayerData

if platform.system() == "Linux":
    shared_folder = "/shared/Images/"
    shared2_folder = "/shared2/"
else:
    shared_folder = "shared/Images/"
    shared2_folder = "shared2/"

def openstats(playername, games, min_elo, patch, sort="date", unit = "all", data_only = False, transparent = False):
    unit_dict = {}
    unit = unit.lower()
    with open('Files/json/units.json', 'r') as f:
        units_json = json.load(f)
    for u_js in units_json:
        if u_js["totalValue"] != '':
            if u_js["unitId"] and 270 > int(u_js["totalValue"]) > 0:
                string = u_js["unitId"]
                string = string.replace('_', ' ')
                string = string.replace(' unit id', '')
                unit_dict[string] = {'Count': 0, 'Wins': 0, 'Worker': 0, 'Elo': 0, 'OpenWith': {}, 'MMs': {}, 'Spells': {}}
    unit_dict['pack rat nest'] = {'Count': 0, 'Wins': 0, 'Worker': 0, 'Elo': 0, 'OpenWith': {}, 'MMs': {}, 'Spells': {}}
    if unit != "all":
        if unit in util.slang:
            unit = util.slang.get(unit)
        if unit not in unit_dict:
            close_matches = difflib.get_close_matches(unit, list(unit_dict.keys()))
            if len(close_matches) > 0:
                unit = close_matches[0]
            else:
                return unit + " unit not found."
    novacup = False
    if playername == 'all':
        playerid = 'all'
    elif 'nova cup' in playername:
        novacup = True
        playerid = playername
    else:
        playerid = legion_api.getid(playername)
        if playerid == 0:
            return 'Player ' + playername + ' not found.'
        if playerid == 1:
            return 'API limit reached, you can still use "all" commands.'
    req_columns = [[GameData.game_id, GameData.queue, GameData.date, GameData.version, GameData.ending_wave, GameData.game_elo, GameData.player_ids,
                    PlayerData.player_id, PlayerData.player_slot, PlayerData.game_result, PlayerData.player_elo, PlayerData.legion,
                    PlayerData.spell, PlayerData.workers_per_wave, PlayerData.build_per_wave],
                   ["game_id", "date", "version", "ending_wave", "game_elo"],
                   ["player_id", "player_slot", "game_result", "player_elo", "legion", "spell", "workers_per_wave", "build_per_wave"]]
    history_raw = drachbot_db.get_matchistory(playerid, games, min_elo, patch, sort_by=sort, earlier_than_wave10=True, req_columns=req_columns)
    if type(history_raw) == str:
        return history_raw
    if len(history_raw) == 0:
        return 'No games found.'
    games = len(history_raw)
    if 'nova cup' in playerid:
        playerid = 'all'
    patches = set()
    gameelo_list = []
    print("starting openstats...")
    for game in history_raw:
        if game["ending_wave"] < 4: continue
        patches.add(game["version"])
        gameelo_list.append(game["game_elo"])
        if playerid.lower() != 'all' and 'nova cup' not in playerid:
            for player in game["players_data"]:
                if player["player_id"] == playerid:
                    opener_ranked_raw = player["build_per_wave"][:4]
                    break
        else:
            opener_ranked_raw = []
            for i in range(4):
                opener_ranked_raw.extend(game["players_data"][i]["build_per_wave"][:4])
        opener_ranked = []
        for i, x in enumerate(opener_ranked_raw):
            opener_ranked.extend([[]])
            x = x.split("!")
            for y in x:
                string = y.split('_unit_id:')
                opener_ranked[i].append(string[0].replace('_', ' '))
        if playerid.lower() != 'all' and 'nova cup' not in playerid:
            for player in game["players_data"]:
                if player["player_id"] == playerid:
                    s = set()
                    try:
                        for x in range(4):
                            for y in opener_ranked[x]:
                                s.add(y)
                    except IndexError:
                        continue
                    for y in s:
                        try:
                            if y != opener_ranked[0][0]:
                                if y in unit_dict[opener_ranked[0][0]]['OpenWith']:
                                    unit_dict[opener_ranked[0][0]]['OpenWith'][y]['Count'] += 1
                                    if player["game_result"] == 'won':
                                        unit_dict[opener_ranked[0][0]]['OpenWith'][y]['Wins'] += 1
                                else:
                                    unit_dict[opener_ranked[0][0]]['OpenWith'][y] = {'Count': 1, 'Wins': 0}
                                    if player["game_result"] == 'won':
                                        unit_dict[opener_ranked[0][0]]['OpenWith'][y]['Wins'] += 1
                            else:
                                unit_dict[opener_ranked[0][0]]['Count'] += 1
                                if player["legion"] not in unit_dict[opener_ranked[0][0]]['MMs']:
                                    unit_dict[opener_ranked[0][0]]['MMs'][player["legion"]] = {'Count': 1, 'Wins': 0}
                                else:
                                    unit_dict[opener_ranked[0][0]]['MMs'][player["legion"]]['Count'] += 1
                                if player["spell"] not in unit_dict[opener_ranked[0][0]]['Spells']:
                                    unit_dict[opener_ranked[0][0]]['Spells'][player["spell"]] = {'Count': 1, 'Wins': 0}
                                else:
                                    unit_dict[opener_ranked[0][0]]['Spells'][player["spell"]]['Count'] += 1
                                unit_dict[opener_ranked[0][0]]['Worker'] += player["workers_per_wave"][3]
                                unit_dict[opener_ranked[0][0]]['Elo'] += player["player_elo"]
                                if player["game_result"] == 'won':
                                    unit_dict[opener_ranked[0][0]]['Wins'] += 1
                                    unit_dict[opener_ranked[0][0]]['MMs'][player["legion"]]['Wins'] += 1
                                    unit_dict[opener_ranked[0][0]]['Spells'][player["spell"]]['Wins'] += 1
                        except IndexError:
                            continue
                        except KeyError:
                            continue
        else:
            counter = 0
            for player in game["players_data"]:
                s = set()
                try:
                    for x in range(counter, counter+4):
                        for y in opener_ranked[x]:
                            s.add(y)
                except IndexError:
                    continue
                for y in s:
                    try:
                        i = 0
                        if y != opener_ranked[counter][0]:
                            if y in unit_dict[opener_ranked[counter][0]]['OpenWith']:
                                unit_dict[opener_ranked[counter][0]]['OpenWith'][y]['Count'] += 1
                                if player["game_result"] == 'won':
                                    unit_dict[opener_ranked[counter][0]]['OpenWith'][y]['Wins'] += 1
                            else:
                                unit_dict[opener_ranked[counter][0]]['OpenWith'][y] = {'Count': 1, 'Wins': 0}
                                if player["game_result"] == 'won':
                                    unit_dict[opener_ranked[counter][0]]['OpenWith'][y]['Wins'] += 1
                        else:
                            unit_dict[opener_ranked[counter][0]]['Count'] += 1
                            if player["legion"] not in unit_dict[opener_ranked[counter][0]]['MMs']:
                                unit_dict[opener_ranked[counter][0]]['MMs'][player["legion"]] = {'Count': 1,'Wins': 0}
                            else:
                                unit_dict[opener_ranked[counter][0]]['MMs'][player["legion"]]['Count'] += 1
                            if player["spell"] not in unit_dict[opener_ranked[counter][0]]['Spells']:
                                unit_dict[opener_ranked[counter][0]]['Spells'][player["spell"]] = {'Count': 1, 'Wins': 0}
                            else:
                                unit_dict[opener_ranked[counter][0]]['Spells'][player["spell"]]['Count'] += 1
                            unit_dict[opener_ranked[counter][0]]['Worker'] += player["workers_per_wave"][3]
                            unit_dict[opener_ranked[counter][0]]['Elo'] += player["player_elo"]
                            if player["game_result"] == 'won':
                                unit_dict[opener_ranked[counter][0]]['Wins'] += 1
                                unit_dict[opener_ranked[counter][0]]['MMs'][player["legion"]]['Wins'] += 1
                                unit_dict[opener_ranked[counter][0]]['Spells'][player["spell"]]['Wins'] += 1
                    except IndexError:
                        continue
                    except KeyError:
                        continue
                counter += 4
    new_patches = []
    for x in patches:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches = list(dict.fromkeys(new_patches))
    patches = sorted(patches, key=lambda x: int(x.split(".")[0] + x.split(".")[1]), reverse=True)
    newIndex = sorted(unit_dict, key=lambda x: unit_dict[x]['Count'], reverse=True)
    unit_dict = {k: unit_dict[k] for k in newIndex}
    avgelo = round(sum(gameelo_list)/len(gameelo_list))
    if novacup:
        playerid = playername
    if data_only:
        return [unit_dict, games, avgelo]
    if unit == "all":
        return image_generators.create_image_stats(unit_dict, games, playerid, avgelo, patches, mode="Open", transparency=transparent)
    else:
        return image_generators.create_image_stats_specific(unit_dict, games, playerid, avgelo, patches, mode="Open", specific_value=unit, transparency=transparent)

class Openstats(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.website_data.start()
    
    def cog_unload(self) -> None:
        self.website_data.cancel()
    
    @app_commands.command(name="openstats", description="Opener stats.")
    @app_commands.describe(playername='Enter playername or "all" for all available data.',
                           games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           min_elo='Enter minium average game elo to include in the data set',
                           patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.',
                           sort="Sort by?", unit="Unit name for specific stats, or 'all' for all openers.",
                           transparency="Transparent Background?")
    @app_commands.choices(sort=[
        discord.app_commands.Choice(name='date', value="date"),
        discord.app_commands.Choice(name='elo', value="elo")
    ])
    @app_commands.autocomplete(unit=util.unit_autocomplete)
    async def openstats(self, interaction: discord.Interaction, playername: str, games: int = 0, min_elo: int = 0,
                        patch: str = util.current_season, sort: discord.app_commands.Choice[str] = "date", unit: str = "all", transparency: bool = False):
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
                response = await loop.run_in_executor(pool, functools.partial(openstats, str(playername).lower(), games, min_elo, patch,
                                                                              sort=sort, unit=unit, transparent=transparency))
                pool.shutdown()
                if response.endswith(".png"):
                    await interaction.followup.send(file=discord.File(response))
                else:
                    await interaction.followup.send(response)
            except Exception:
                print("/" + interaction.command.name + " failed. args: " + str(interaction.data.values()))
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")
    
    @tasks.loop(time=util.task_times2)
    async def website_data(self):
        patches = util.website_patches
        elos = [1800, 2000, 2200, 2400, 2600, 2800]
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ProcessPoolExecutor() as pool:
                for patch in patches:
                    for file in os.listdir(f"{shared2_folder}data/openstats/"):
                        if file.startswith(patch):
                            os.remove(f"{shared2_folder}data/openstats/{file}")
                    for elo in elos:
                        data = await loop.run_in_executor(pool, functools.partial(openstats, "all", 0, elo, patch, data_only=True))
                        with open(f"{shared2_folder}data/openstats/{patch}_{elo}_{data[1]}_{data[2]}.json", "w") as f:
                            json.dump(data[0], f)
                            f.close()
            print("Website data update success!")
        except Exception:
            traceback.print_exc()

async def setup(bot:commands.Bot):
    await bot.add_cog(Openstats(bot))