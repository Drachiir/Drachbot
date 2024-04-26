import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import concurrent.futures
import traceback
import functools

import image_generators
import json_db
import util
import legion_api

def mmstats(playername, games, min_elo, patch, mastermind = 'All', sort="date"):
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
    if mastermind == 'All':
        mmnames_list = ['LockIn', 'Greed', 'Redraw', 'Yolo', 'Fiesta', 'CashOut', 'Castle', 'Cartel', 'Chaos', 'Champion', 'DoubleLockIn', 'Kingsguard', 'Megamind']
    elif mastermind == 'Megamind':
        mmnames_list = ['LockIn', 'Greed', 'Redraw', 'Yolo', 'Fiesta', 'CashOut', 'Castle', 'Cartel', 'Chaos', 'Champion', 'DoubleLockIn', 'Kingsguard']
    else:
        mmnames_list = [mastermind]
    masterminds_dict = {}
    for x in mmnames_list:
        masterminds_dict[x] = {"Count": 0, "Wins": 0, "Worker": 0, "Opener": {}, "Spell": {}, "Elo": 0, "Leaks": [], "PlayerIds": [], "ChampionUnit": {}}
    gameelo_list = []
    history_raw = json_db.get_matchistory(playerid, games, min_elo, patch, sort_by=sort, earlier_than_wave10=True)
    if type(history_raw) == str:
        return history_raw
    if len(history_raw) == 0:
        return 'No games found.'
    games = len(history_raw)
    if 'nova cup' in playerid:
        playerid = 'all'
    case_list = ['LockIn', 'Greed', 'Redraw', 'Yolo', 'Fiesta', 'CashOut', 'Castle', 'Cartel', 'Chaos', 'Champion', 'DoubleLockIn', 'Kingsguard']
    patches = set()
    megamind_count = 0
    print('Starting mmstats command...')
    for game in history_raw:
        if (game["version"].startswith('v10') or game["version"].startswith('v9')) and (mastermind == 'Megamind' or mastermind == 'Champion'):
            continue
        patches.add(game["version"])
        gameelo_list.append(game["gameElo"])
        match mastermind:
            case 'All' | 'Megamind':
                for player in game["playersData"]:
                    if player["playerId"] == playerid or playerid == "all":
                        if (game["version"].startswith('v10') or game["version"].startswith('v9')):
                            player["megamind"] = False
                        if player["megamind"] == True:
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
                        if player["gameResult"] == 'won':
                            masterminds_dict[mastermind_current]["Wins"] += 1
                        try:
                            masterminds_dict[mastermind_current]["Worker"] += player["workersPerWave"][9]
                        except IndexError:
                            pass
                        masterminds_dict[mastermind_current]['Elo'] += player["overallElo"]
                        if ',' in player["firstWaveFighters"]:
                            string = player["firstWaveFighters"]
                            commas = string.count(',')
                            opener = string.split(',', commas)[commas]
                        else:
                            opener = player["firstWaveFighters"]
                        if player["chosenSpell"] not in masterminds_dict[mastermind_current]['Spell']:
                            masterminds_dict[mastermind_current]['Spell'][player["chosenSpell"]] = {"Count": 1, "Wins": 0}
                            if player["gameResult"] == 'won':
                                masterminds_dict[mastermind_current]['Spell'][player["chosenSpell"]]["Wins"] += 1
                        else:
                            masterminds_dict[mastermind_current]['Spell'][player["chosenSpell"]]["Count"] += 1
                            if player["gameResult"] == 'won':
                                masterminds_dict[mastermind_current]['Spell'][player["chosenSpell"]]["Wins"] += 1
                        if opener not in masterminds_dict[mastermind_current]['Opener']:
                            masterminds_dict[mastermind_current]['Opener'][opener] = {"Count": 1, "Wins": 0}
                            if player["gameResult"] == 'won':
                                masterminds_dict[mastermind_current]['Opener'][opener]["Wins"] += 1
                        else:
                            masterminds_dict[mastermind_current]['Opener'][opener]["Count"] += 1
                            if player["gameResult"] == 'won':
                                masterminds_dict[mastermind_current]['Opener'][opener]["Wins"] += 1
            case mastermind if mastermind in case_list:
                for player in game["playersData"]:
                    if (playerid == 'all' or player["playerId"] == playerid) and (mastermind == player["legion"]):
                        mastermind_current = player["legion"]
                        masterminds_dict[mastermind_current]["Count"] += 1
                        if player["gameResult"] == 'won':
                            masterminds_dict[mastermind_current]["Wins"] += 1
                        try:
                            masterminds_dict[mastermind_current]["Worker"] += player["workersPerWave"][9]
                        except IndexError:
                            pass
                        masterminds_dict[mastermind_current]['Elo'] += player["overallElo"]
                        if ',' in player["firstWaveFighters"]:
                            string = player["firstWaveFighters"]
                            commas = string.count(',')
                            opener = string.split(',', commas)[commas]
                        else:
                            opener = player["firstWaveFighters"]
                        if player["chosenSpell"] not in masterminds_dict[mastermind_current]['Spell']:
                            masterminds_dict[mastermind_current]['Spell'][player["chosenSpell"]] = {"Count": 1, "Wins": 0}
                            if player["gameResult"] == 'won':
                                masterminds_dict[mastermind_current]['Spell'][player["chosenSpell"]]["Wins"] += 1
                        else:
                            masterminds_dict[mastermind_current]['Spell'][player["chosenSpell"]]["Count"] += 1
                            if player["gameResult"] == 'won':
                                masterminds_dict[mastermind_current]['Spell'][player["chosenSpell"]]["Wins"] += 1
                        if opener not in masterminds_dict[mastermind_current]['Opener']:
                            masterminds_dict[mastermind_current]['Opener'][opener] = {"Count": 1, "Wins": 0}
                            if player["gameResult"] == 'won':
                                masterminds_dict[mastermind_current]['Opener'][opener]["Wins"] += 1
                        else:
                            masterminds_dict[mastermind_current]['Opener'][opener]["Count"] += 1
                            if player["gameResult"] == 'won':
                                masterminds_dict[mastermind_current]['Opener'][opener]["Wins"] += 1
    new_patches = []
    for x in patches:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches = list(dict.fromkeys(new_patches))
    patches = sorted(patches, key=lambda x: int(x.split(".")[0] + x.split(".")[1]), reverse=True)
    newIndex = sorted(masterminds_dict, key=lambda x: masterminds_dict[x]['Count'], reverse=True)
    masterminds_dict = {k: masterminds_dict[k] for k in newIndex}
    avg_gameelo = round(sum(gameelo_list)/len(gameelo_list))
    if novacup:
        playerid = playername
    match mastermind:
        case 'All':
            return image_generators.create_image_stats(masterminds_dict, games, playerid, avg_gameelo, patches, mode="Mastermind")
        case mastermind if mastermind in case_list:
            return image_generators.create_image_stats_specific(masterminds_dict, games, playerid, avg_gameelo, patches, mode="Mastermind", specific_value=mastermind)
        case 'Megamind':
            return image_generators.create_image_stats(masterminds_dict, games, playerid, avg_gameelo, patches, "Mastermind", True, megamind_count)

class MMstats(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    @app_commands.command(name="mmstats", description="Mastermind stats.")
    @app_commands.describe(playername='Enter playername or "all" for all available data.', games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           min_elo='Enter minium average game elo to include in the data set',
                           patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.',
                           mastermind='Select a Mastermind for specific stats, or All for a general overview.', sort="Sort by?")
    @app_commands.choices(mastermind=util.mm_choices)
    @app_commands.choices(sort=[
        discord.app_commands.Choice(name='date', value="date"),
        discord.app_commands.Choice(name='elo', value="elo")
    ])
    async def mmstats(self, interaction: discord.Interaction, playername: str, games: int = 0, min_elo: int = 0, patch: str = util.current_season, mastermind: discord.app_commands.Choice[str] = "All", sort: discord.app_commands.Choice[str] = "date"):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            if playername.lower() == "all" and games == 0 and min_elo == 0 and patch == util.current_season:
                min_elo = util.current_minelo
            try:
                mastermind = mastermind.value
            except AttributeError:
                pass
            try:
                sort = sort.value
            except AttributeError:
                pass
            try:
                response = await loop.run_in_executor(pool, functools.partial(mmstats, str(playername).lower(), games, min_elo, patch, mastermind, sort=sort))
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
    await bot.add_cog(MMstats(bot))