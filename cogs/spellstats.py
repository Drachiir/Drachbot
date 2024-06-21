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

shifts = [
    (-1.0, -0.5), (0.0, -1.0), (1.0, -0.5),
    (1.0, 0.5), (0.0, 1.0), (-1.0, 0.5),
    (0.5, -1.0), (1.0, 0.0), (0.5, 1.0),
    (-0.5, 1.0), (-1.0, 0.0), (-0.5, -1.0)
]

calculate_positions = lambda x, z: [(x, z)] + [(x + dx, z + dz) for dx, dz in shifts]

if platform.system() == "Linux":
    shared_folder = "/shared/Images/"
    shared2_folder = "/shared2/"
else:
    shared_folder = "shared/Images/"
    shared2_folder = "shared2/"

def spellstats(playername, games, min_elo, patch, sort="date", spellname = "all", data_only = False, transparent = False):
    spell_dict = {}
    spellname = spellname.lower()
    with open('Files/json/spells.json', 'r') as f:
        spells_json = json.load(f)
    for s_js in spells_json:
        string = s_js["_id"]
        string = string.replace('_', ' ')
        string = string.replace(' powerup id', '')
        string = string.replace(' spell damage', '')
        spell_dict[string] = {'Count': 0, 'Wins': 0, 'Worker': 0, 'Elo': 0, 'Offered': 0, 'Opener': {}, 'MMs': {}, 'Targets': {}}
    spell_dict["taxed allowance"] = {'Count': 0, 'Wins': 0, 'Worker': 0, 'Elo': 0, 'Offered': 0, 'Opener': {}, 'MMs': {}, 'Targets': {}}
    if spellname != "all":
        if spellname in util.slang:
            spellname = util.slang.get(spellname)
        if spellname not in spell_dict:
            close_matches = difflib.get_close_matches(spellname, list(spell_dict.keys()))
            if len(close_matches) > 0:
                spellname = close_matches[0]
            else:
                return spellname + " spell not found."
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
    req_columns = [[GameData.game_id, GameData.queue, GameData.date, GameData.version, GameData.ending_wave, GameData.game_elo, GameData.player_ids, GameData.spell_choices,
                    PlayerData.player_id, PlayerData.player_slot, PlayerData.game_result, PlayerData.player_elo, PlayerData.legion,
                    PlayerData.opener, PlayerData.spell, PlayerData.workers_per_wave, PlayerData.spell_location, PlayerData.build_per_wave],
                   ["game_id", "date", "version", "ending_wave", "game_elo", "spell_choices"],
                   ["player_id", "player_slot", "game_result", "player_elo", "legion", "opener", "spell", "workers_per_wave", "spell_location", "build_per_wave"]]
    history_raw = drachbot_db.get_matchistory(playerid, games, min_elo, patch, sort_by=sort, req_columns=req_columns)
    if type(history_raw) == str:
        return history_raw
    if len(history_raw) == 0:
        return 'No games found.'
    games = len(history_raw)
    if 'nova cup' in playerid:
        playerid = 'all'
    patches = []
    gameelo_list = []
    print('Starting spellstats command...')
    for game in history_raw:
        patches.append(game["version"])
        gameelo_list.append(game["game_elo"])
        for player in game["players_data"]:
            if (player["player_id"] == playerid) or (playerid.lower() == 'all' or 'nova cup' in playerid):
                for offered_spell in game["spell_choices"]:
                    spell_dict[offered_spell.replace('_', ' ').replace(' powerup id', '').replace(' spell damage', '')]["Offered"] += 1
                if spellname != "all" and player["spell"].lower() != spellname:
                    continue
                spell_name = player["spell"].lower()
                spell_dict[spell_name]["Count"] += 1
                spell_dict[spell_name]["Elo"] += player["player_elo"]
                spell_dict[spell_name]["Worker"] += player["workers_per_wave"][9]
                if player["spell_location"] != "-1|-1":
                    spell_loc = player["spell_location"].split("|")
                    spell_loc = (float(spell_loc[0]), float(spell_loc[1]))
                    if spell_name in util.aura_spells:
                        target_locations = calculate_positions(spell_loc[0], spell_loc[1])
                    else:
                        target_locations = [spell_loc]
                    excluded_units = []
                    for unit in player["build_per_wave"][-1].split("!"):
                        unit_loc = unit.split(":")[1].split("|")
                        unit_loc = (float(unit_loc[0]), float(unit_loc[1]))
                        if unit_loc in target_locations:
                            unit_name = unit.split(":")[0].replace("_", " ").replace(" unit id", "")
                            if unit_name in excluded_units:
                                continue
                            excluded_units.append(unit_name)
                            if unit_name in spell_dict[spell_name]["Targets"]:
                                spell_dict[spell_name]["Targets"][unit_name]["Count"] += 1
                            else:
                                spell_dict[spell_name]["Targets"][unit_name] = {"Count": 1, "Wins": 0}
                            if player["game_result"] == "won":
                                spell_dict[spell_name]["Targets"][unit_name]["Wins"] += 1
                if player["game_result"] == "won":
                    spell_dict[spell_name]["Wins"] += 1
                if "," in player["opener"]:
                    opener_current = player["opener"].split(",")[-1]
                else:
                    opener_current = player["opener"]
                if opener_current in spell_dict[spell_name]["Opener"]:
                    spell_dict[spell_name]["Opener"][opener_current]["Count"] += 1
                    if player["game_result"] == "won":
                        spell_dict[spell_name]["Opener"][opener_current]["Wins"] += 1
                else:
                    spell_dict[spell_name]["Opener"][opener_current] = {"Count": 1, "Wins": 0}
                    if player["game_result"] == "won":
                        spell_dict[spell_name]["Opener"][opener_current]["Wins"] += 1
                if player["legion"] in spell_dict[spell_name]["MMs"]:
                    spell_dict[spell_name]["MMs"][player["legion"]]["Count"] += 1
                    if player["game_result"] == "won":
                        spell_dict[spell_name]["MMs"][player["legion"]]["Wins"] += 1
                else:
                    spell_dict[spell_name]["MMs"][player["legion"]] = {"Count": 1, "Wins": 0}
                    if player["game_result"] == "won":
                        spell_dict[spell_name]["MMs"][player["legion"]]["Wins"] += 1
                
    new_patches = []
    for x in patches:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches = list(dict.fromkeys(new_patches))
    patches = sorted(patches, key=lambda x: int(x.split(".")[0] + x.split(".")[1]), reverse=True)
    newIndex = sorted(spell_dict, key=lambda x: spell_dict[x]['Count'], reverse=True)
    spell_dict = {k: spell_dict[k] for k in newIndex}
    avgelo = round(sum(gameelo_list)/len(gameelo_list))
    if novacup:
        playerid = playername
    if data_only:
        return [spell_dict, games, avgelo]
    if spellname == "all":
        return image_generators.create_image_stats(spell_dict, games, playerid, avgelo, patches, mode="Spell", transparency=transparent)
    else:
        return image_generators.create_image_stats_specific(spell_dict, games, playerid, avgelo, patches, mode="Spell", specific_value=spellname, transparency=transparent)

class Spellstats(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.website_data.start()
    
    def cog_unload(self) -> None:
        self.website_data.cancel()
    
    @app_commands.command(name="spellstats", description="Spell stats.")
    @app_commands.describe(playername='Enter playername or "all" for all available data.',
                           games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           min_elo='Enter minium average game elo to include in the data set',
                           patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.',
                           sort="Sort by?", spell="Spell name for specific stats, or 'all' for all Spells.",
                           transparency="Transparent Background?")
    @app_commands.choices(sort=[
        discord.app_commands.Choice(name='date', value="date"),
        discord.app_commands.Choice(name='elo', value="elo")
    ])
    @app_commands.autocomplete(spell=util.spell_autocomplete)
    async def spellstats(self, interaction: discord.Interaction, playername: str, games: int = 0, min_elo: int = 0, patch: str = util.current_season,
                         sort: discord.app_commands.Choice[str] = "date", spell: str = "all", transparency: bool = False):
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
                response = await loop.run_in_executor(pool, functools.partial(spellstats, str(playername).lower(), games, min_elo, patch, sort=sort, spellname=spell, transparent=transparency))
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
                    for file in os.listdir(f"{shared2_folder}data/spellstats/"):
                        if file.startswith(patch):
                            os.remove(f"{shared2_folder}data/spellstats/{file}")
                    for elo in elos:
                        data = await loop.run_in_executor(pool, functools.partial(spellstats, "all", 0, elo, patch, data_only=True))
                        with open(f"{shared2_folder}data/spellstats/{patch}_{elo}_{data[1]}_{data[2]}.json", "w") as f:
                            json.dump(data[0], f)
                            f.close()
            print("Website data update success!")
        except Exception:
            traceback.print_exc()
    
async def setup(bot:commands.Bot):
    await bot.add_cog(Spellstats(bot))