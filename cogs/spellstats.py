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
import json_db
import util
import legion_api

def spellstats(playername, games, min_elo, patch, sort="date", spellname = "all"):
    spell_dict = {}
    spellname = spellname.lower()
    with open('Files/json/spells.json', 'r') as f:
        spells_json = json.load(f)
    for s_js in spells_json:
        string = s_js["_id"]
        string = string.replace('_', ' ')
        string = string.replace(' powerup id', '')
        string = string.replace(' spell damage', '')
        spell_dict[string] = {'Count': 0, 'Wins': 0, 'Worker': 0, 'Opener': {}, 'MMs': {}}
    spell_dict["taxed allowance"] = {'Count': 0, 'Wins': 0, 'Worker': 0, 'Opener': {}, 'MMs': {}}
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
    try:
        history_raw = json_db.get_matchistory(playerid, games, min_elo, patch, sort_by=sort)
    except TypeError as e:
        print(e)
        return playername + ' has not played enough games.'
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
        gameelo_list.append(game["gameElo"])
        for player in game["playersData"]:
            if (player["playerId"] == playerid) or (playerid.lower() == 'all' or 'nova cup' in playerid):
                spell_name = player["chosenSpell"].lower()
                spell_dict[spell_name]["Count"] += 1
                if player["gameResult"] == "won":
                    spell_dict[spell_name]["Wins"] += 1
                spell_dict[spell_name]["Worker"] += player["workersPerWave"][9]
                if "," in player["firstWaveFighters"]:
                    opener_current = player["firstWaveFighters"].split(",")[-1]
                else:
                    opener_current = player["firstWaveFighters"]
                if opener_current in spell_dict[spell_name]["Opener"]:
                    spell_dict[spell_name]["Opener"][opener_current]["Count"] += 1
                    if player["gameResult"] == "won":
                        spell_dict[spell_name]["Opener"][opener_current]["Wins"] += 1
                else:
                    spell_dict[spell_name]["Opener"][opener_current] = {"Count": 1, "Wins": 0}
                    if player["gameResult"] == "won":
                        spell_dict[spell_name]["Opener"][opener_current]["Wins"] += 1
                if player["legion"] in spell_dict[spell_name]["MMs"]:
                    spell_dict[spell_name]["MMs"][player["legion"]]["Count"] += 1
                    if player["gameResult"] == "won":
                        spell_dict[spell_name]["MMs"][player["legion"]]["Wins"] += 1
                else:
                    spell_dict[spell_name]["MMs"][player["legion"]] = {"Count": 1, "Wins": 0}
                    if player["gameResult"] == "won":
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
    if spellname == "all":
        return image_generators.create_image_stats(spell_dict, games, playerid, avgelo, patches, mode="Spell")
    else:
        return image_generators.create_image_stats_specific(spell_dict, games, playerid, avgelo, patches, mode="Spell", specific_value=spellname)

class Spellstats(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    @app_commands.command(name="spellstats", description="Spell stats.")
    @app_commands.describe(playername='Enter playername or "all" for all available data.',
                           games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           min_elo='Enter minium average game elo to include in the data set',
                           patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.',
                           sort="Sort by?", spell="Spell name for specific stats, or 'all' for all Spells.")
    @app_commands.choices(sort=[
        discord.app_commands.Choice(name='date', value="date"),
        discord.app_commands.Choice(name='elo', value="elo")
    ])
    @app_commands.autocomplete(spell=util.spell_autocomplete)
    async def spellstats(self, interaction: discord.Interaction, playername: str, games: int = 0, min_elo: int = 0, patch: str = util.current_season, sort: discord.app_commands.Choice[str] = "date", spell: str = "all"):
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
                response = await loop.run_in_executor(pool, functools.partial(spellstats, str(playername).lower(), games, min_elo, patch, sort=sort, spellname=spell))
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
    await bot.add_cog(Spellstats(bot))