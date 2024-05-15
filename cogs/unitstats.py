import discord
from discord import app_commands
from discord.ext import commands
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

def unitstats(playername, games, min_elo, patch, sort="date", unit = "all", min_cost = 0, max_cost = 2000):
    unit_dict = {}
    unit = unit.lower()
    with open('Files/json/units.json', 'r') as f:
        units_json = json.load(f)
    for u_js in units_json:
        if u_js["totalValue"] != '':
            if u_js["unitId"] and min_cost <= int(u_js["totalValue"]) <= max_cost: #and (u_js["sortOrder"].split(".")[1].endswith("U") or u_js["sortOrder"].split(".")[1].endswith("U2") or "neko" in u_js["unitId"]):
                string = u_js["unitId"]
                string = string.replace('_', ' ')
                string = string.replace(' unit id', '')
                if u_js["upgradesFrom"]:
                    string2 = u_js["upgradesFrom"][0]
                    string2 = string2.replace('_', ' ').replace(' unit id', '').replace('units ', '')
                else:
                    string2 = ""
                unit_dict[string] = {'Count': 0, 'Wins': 0, 'ComboUnit': {}, 'MMs': {}, 'Spells': {}, "upgradesFrom": string2}
    if min_cost <= 75:
        unit_dict['pack rat (footprints)'] = {'Count': 0, 'Wins': 0, 'ComboUnit': {}, 'MMs': {}, 'Spells': {}, "upgradesFrom": "looter"}
    if not unit_dict:
        return "No units found"
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
    history_raw = drachbot_db.get_matchistory(playerid, games, min_elo, patch, sort_by=sort, earlier_than_wave10=True)
    if type(history_raw) == str:
        return history_raw
    if len(history_raw) == 0:
        return 'No games found.'
    games = len(history_raw)
    if 'nova cup' in playerid:
        playerid = 'all'
    patches = []
    gameelo_list = []
    count = 0
    print("starting unitstats...")
    for game in history_raw:
        patches.append(game["version"])
        gameelo_list.append(game["gameElo"])
        for player in game["playersData"]:
            if player["playerId"] != playerid and playerid != "all": continue
            fighter_set = set(player["fighters"].lower().split(","))
            for fighter in fighter_set:
                if fighter == "" or fighter not in unit_dict: continue
                unit_dict[fighter]["Count"] += 1
                if player["chosenSpell"] in unit_dict[fighter]["Spells"]:
                    unit_dict[fighter]["Spells"][player["chosenSpell"]]["Count"] += 1
                else:
                    unit_dict[fighter]["Spells"][player["chosenSpell"]] = {"Count": 1, "Wins": 0}
                if player["legion"] in unit_dict[fighter]["MMs"]:
                    unit_dict[fighter]["MMs"][player["legion"]]["Count"] += 1
                else:
                    unit_dict[fighter]["MMs"][player["legion"]] = {"Count": 1, "Wins": 0}
                if player["gameResult"] == "won":
                    unit_dict[fighter]["Wins"] += 1
                    unit_dict[fighter]["MMs"][player["legion"]]["Wins"] += 1
                    unit_dict[fighter]["Spells"][player["chosenSpell"]]["Wins"] += 1
                for combo_unit in fighter_set:
                    if combo_unit == fighter or combo_unit == unit_dict[fighter]["upgradesFrom"]: continue
                    if combo_unit in unit_dict[fighter]["ComboUnit"]:
                        unit_dict[fighter]["ComboUnit"][combo_unit]["Count"] += 1
                    else:
                        unit_dict[fighter]["ComboUnit"][combo_unit] = {"Count": 1, "Wins": 0}
                    if player["gameResult"] == "won":
                        unit_dict[fighter]["ComboUnit"][combo_unit]["Wins"] += 1
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
    if unit == "all":
        return image_generators.create_image_stats(unit_dict, games, playerid, avgelo, patches, mode="Unit")
    else:
        return image_generators.create_image_stats_specific(unit_dict, games, playerid, avgelo, patches, mode="Unit", specific_value=unit)

class Unitstats(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    @app_commands.command(name="unitstats", description="Fighter stats.")
    @app_commands.describe(playername='Enter playername or "all" for all available data.',
                           games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           min_elo='Enter minium average game elo to include in the data set',
                           patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.',
                           sort="Sort by?", unit="Fighter name for specific stats, or 'all' for all Spells.",
                           min_cost="Min Gold cost of a unit.", max_cost="Max Gold cost of a unit.")
    @app_commands.choices(sort=[
        discord.app_commands.Choice(name='date', value="date"),
        discord.app_commands.Choice(name='elo', value="elo")
    ])
    @app_commands.autocomplete(unit=util.unit_autocomplete)
    async def unitstats(self, interaction: discord.Interaction, playername: str, games: int = 0, min_elo: int = 0, patch: str = util.current_season, sort: discord.app_commands.Choice[str] = "date", unit: str = "all", min_cost: int = 0, max_cost: int = 2000):
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
                response = await loop.run_in_executor(pool, functools.partial(unitstats, str(playername).lower(), games, min_elo, patch, sort=sort, unit=unit, min_cost=min_cost, max_cost=max_cost))
                pool.shutdown()
                if response.endswith(".png"):
                    await interaction.followup.send(file=discord.File(response))
                else:
                    await interaction.followup.send(response)
            except Exception:
                print("/" + interaction.command.name + " failed. args: " + str(interaction.data.values()))
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

async def setup(bot:commands.Bot):
    await bot.add_cog(Unitstats(bot))