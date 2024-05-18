import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import concurrent.futures
import traceback
import functools
import json
import difflib

import drachbot_db
import util
import legion_api
from peewee_pg import GameData, PlayerData


def winrate(playername, playername2, option, games, patch, min_elo = 0, sort = "Count"):
    mmnames_list = ['LockIn', 'Greed', 'Redraw', 'Yolo', 'Fiesta', 'CashOut', 'Castle', 'Cartel', 'Chaos', 'Champion', 'DoubleLockIn', 'Kingsguard', "All"]
    mm1 = ""
    mm2 = ""
    if "," in playername:
        playername = playername.split(",")
        if playername[0].lower() != 'all':
            playerid = legion_api.getid(playername[0])
        else:
            playerid = "all"
        for mm in mmnames_list:
            if mm.lower() == playername[1].replace(" ", "").lower() and mm.lower() != "all":
                mm1 = mm
                break
        else:
            return playername[1] + " mastermind not found."
    else:
        playerid = legion_api.getid(playername)
    if playerid == 0:
        if type(playername) == list:
            playername = playername[0]
        return 'Player ' + playername + ' not found.'
    if playerid == 1:
        return 'API limit reached.'
    if "," in playername2:
        playername2 = playername2.split(",")
        if playername2[0].lower() != 'all':
            playerid2 = legion_api.getid(playername2[0])
        else:
            playerid2 = "all"
        for mm in mmnames_list:
            if mm.lower() == playername2[1].replace(" ", "").lower():
                mm2 = mm
                break
        else:
            return playername2[1] + " mastermind not found."
    else:
        if playername2 != "all":
            playerid2 = legion_api.getid(playername2)
        else:
            playerid2 = "all"
    if playerid2 == 0:
        if type(playername2) == list:
            playername2 = playername2[0]
        return 'Player ' + playername2 + ' not found.'
    if playerid2 == 1:
        return 'API limit reached.'
    win_count = 0
    game_count = 0
    req_columns = [[GameData.game_id, GameData.queue, GameData.date, GameData.version, GameData.ending_wave, GameData.game_elo, GameData.player_ids,
                    PlayerData.player_id, PlayerData.player_name, PlayerData.player_slot, PlayerData.game_result, PlayerData.legion, PlayerData.elo_change],
                   ["game_id", "date", "version", "ending_wave", "game_elo"],
                   ["player_id", "player_name", "player_slot", "game_result", "legion", "elo_change"]]
    history_raw = drachbot_db.get_matchistory(playerid, games, min_elo=min_elo, patch=patch, earlier_than_wave10=True, req_columns=req_columns)
    if type(history_raw) == str:
        return history_raw
    games = len(history_raw)
    if games == 0:
        return 'No games found.'
    gameelo_list = []
    patches_list = []
    all_dict = {}
    elo_change_list = []
    for game in history_raw:
        gameresult_ranked_west = game["players_data"][0]["game_result"]
        gameresult_ranked_east = game["players_data"][2]["game_result"]
        playerids_ranked_west = [game["players_data"][0]["player_id"], game["players_data"][1]["player_id"]]
        playerids_ranked_east = [game["players_data"][2]["player_id"], game["players_data"][3]["player_id"]]
        masterminds_ranked_west = [game["players_data"][0]["legion"], game["players_data"][1]["legion"]]
        masterminds_ranked_east = [game["players_data"][2]["legion"], game["players_data"][3]["legion"]]
        elo_change_ranked_west = game["players_data"][0]["elo_change"]
        elo_change_ranked_east = game["players_data"][2]["elo_change"]
        gameelo_list.append(game["game_elo"])
        if (playerid2 != 'all') or (playerid2 == "all" and mm2 != "" and mm2 != "All") or (playerid2 == "all" and mm1 != "" and mm2 == ""):
            for i, x in enumerate(playerids_ranked_west):
                if (x == playerid and (mm1 == masterminds_ranked_west[i] or mm1 == "")) or (playerid == "all" and x != playerid2 and (mm1 == masterminds_ranked_west[i] or mm1 == "")):
                    if option == 'against':
                        if (playerids_ranked_east[0] == playerid2 or playerid2 == 'all') and (mm2 == masterminds_ranked_east[0] or mm2 == ""):
                            patches_list.append(game["version"])
                            elo_change_list.append(elo_change_ranked_west)
                            game_count += 1
                            if gameresult_ranked_west == 'won':
                                win_count += 1
                        elif (playerids_ranked_east[1] == playerid2 or playerid2 == 'all') and (mm2 == masterminds_ranked_east[1] or mm2 == ""):
                            patches_list.append(game["version"])
                            elo_change_list.append(elo_change_ranked_west)
                            game_count += 1
                            if gameresult_ranked_west == 'won':
                                win_count += 1
                    elif option == 'with':
                        if i == 0:
                            teammate = 1
                        else:
                            teammate = 0
                        if type(playername) != list and type(playername2) != list and playername.lower() == playername2.lower():
                            if (playerids_ranked_west[0] == playerid2) and (mm2 == masterminds_ranked_west[0] or mm2 == ""):
                                patches_list.append(game["version"])
                                elo_change_list.append(elo_change_ranked_west)
                                game_count += 1
                                if gameresult_ranked_west == 'won':
                                    win_count += 1
                            elif (playerids_ranked_west[1] == playerid2) and (mm2 == masterminds_ranked_west[1] or mm2 == ""):
                                patches_list.append(game["version"])
                                elo_change_list.append(elo_change_ranked_west)
                                game_count += 1
                                if gameresult_ranked_west == 'won':
                                    win_count += 1
                        else:
                            if (playerids_ranked_west[teammate] == playerid2 or playerid2 == 'all') and (mm2 == masterminds_ranked_west[teammate] or mm2 == ""):
                                patches_list.append(game["version"])
                                elo_change_list.append(elo_change_ranked_west)
                                game_count += 1
                                if gameresult_ranked_west == 'won':
                                    win_count += 1
            for i, x in enumerate(playerids_ranked_east):
                if (x == playerid and (mm1 == masterminds_ranked_east[i] or mm1 == "")) or (playerid == "all" and x != playerid2 and (mm1 == masterminds_ranked_east[i] or mm1 == "")):
                    if option == 'against':
                        if (playerids_ranked_west[0] == playerid2 or playerid2 == 'all') and (mm2 == masterminds_ranked_west[0] or mm2 == ""):
                            patches_list.append(game["version"])
                            elo_change_list.append(elo_change_ranked_east)
                            game_count += 1
                            if gameresult_ranked_east == 'won':
                                win_count += 1
                        elif (playerids_ranked_west[1] == playerid2 or playerid2 == 'all') and (mm2 == masterminds_ranked_west[1] or mm2 == ""):
                            patches_list.append(game["version"])
                            elo_change_list.append(elo_change_ranked_east)
                            game_count += 1
                            if gameresult_ranked_east == 'won':
                                win_count += 1
                    elif option == 'with':
                        if i == 0:
                            teammate = 1
                        else:
                            teammate = 0
                        if type(playername) != list and type(playername2) != list and playername.lower() == playername2.lower():
                            if (playerids_ranked_east[0] == playerid2) and (mm2 == masterminds_ranked_east[0] or mm2 == ""):
                                patches_list.append(game["version"])
                                elo_change_list.append(elo_change_ranked_east)
                                game_count += 1
                                if gameresult_ranked_east == 'won':
                                    win_count += 1
                            elif (playerids_ranked_east[1] == playerid2) and (mm2 == masterminds_ranked_east[1] or mm2 == ""):
                                patches_list.append(game["version"])
                                elo_change_list.append(elo_change_ranked_east)
                                game_count += 1
                                if gameresult_ranked_east == 'won':
                                    win_count += 1
                        else:
                            if (playerids_ranked_east[teammate] == playerid2 or playerid2 == 'all') and (mm2 == masterminds_ranked_east[teammate] or mm2 == ""):
                                patches_list.append(game["version"])
                                elo_change_list.append(elo_change_ranked_east)
                                game_count += 1
                                if gameresult_ranked_east == 'won':
                                    win_count += 1
        elif playerid != "all" and playerid2 == "all" and mm1 == "" and mm2 == "":
            patches_list.append(game["version"])
            for i, x in enumerate(playerids_ranked_west):
                if x == playerid:
                    if option == 'against':
                        if playerids_ranked_east[0] in all_dict:
                            all_dict[playerids_ranked_east[0]]["Count"] += 1
                            all_dict[playerids_ranked_east[0]]["EloChange"] += elo_change_ranked_west
                            if gameresult_ranked_west == "won":
                                all_dict[playerids_ranked_east[0]]["Wins"] += 1
                        else:
                            all_dict[playerids_ranked_east[0]] = {"Count": 1, "Wins": 0, "EloChange": elo_change_ranked_west, "playername": game["players_data"][2]["player_name"]}
                            if gameresult_ranked_west == "won":
                                all_dict[playerids_ranked_east[0]]["Wins"] += 1
                        if playerids_ranked_east[1] in all_dict:
                            all_dict[playerids_ranked_east[1]]["Count"] += 1
                            all_dict[playerids_ranked_east[1]]["EloChange"] += elo_change_ranked_west
                            if gameresult_ranked_west == "won":
                                all_dict[playerids_ranked_east[1]]["Wins"] += 1
                        else:
                            all_dict[playerids_ranked_east[1]] = {"Count": 1, "Wins": 0, "EloChange": elo_change_ranked_west, "playername": game["players_data"][3]["player_name"]}
                            if gameresult_ranked_west == "won":
                                all_dict[playerids_ranked_east[1]]["Wins"] += 1
                    elif option == 'with':
                        if playerids_ranked_west[0] != playerid:
                            if playerids_ranked_west[0] in all_dict:
                                all_dict[playerids_ranked_west[0]]["Count"] += 1
                                all_dict[playerids_ranked_west[0]]["EloChange"] += elo_change_ranked_west
                                if gameresult_ranked_west == "won":
                                    all_dict[playerids_ranked_west[0]]["Wins"] += 1
                            else:
                                all_dict[playerids_ranked_west[0]] = {"Count": 1, "Wins": 0,"EloChange": elo_change_ranked_west, "playername": game["players_data"][0]["player_name"]}
                                if gameresult_ranked_west == "won":
                                    all_dict[playerids_ranked_west[0]]["Wins"] += 1
                        elif playerids_ranked_west[1] != playerid:
                            if playerids_ranked_west[1] in all_dict:
                                all_dict[playerids_ranked_west[1]]["Count"] += 1
                                all_dict[playerids_ranked_west[1]]["EloChange"] += elo_change_ranked_west
                                if gameresult_ranked_west == "won":
                                    all_dict[playerids_ranked_west[1]]["Wins"] += 1
                            else:
                                all_dict[playerids_ranked_west[1]] = {"Count": 1, "Wins": 0,"EloChange": elo_change_ranked_west, "playername": game["players_data"][1]["player_name"]}
                                if gameresult_ranked_west == "won":
                                    all_dict[playerids_ranked_west[1]]["Wins"] += 1
            for i, x in enumerate(playerids_ranked_east):
                if x == playerid:
                    if option == 'against':
                        if playerids_ranked_west[0] in all_dict:
                            all_dict[playerids_ranked_west[0]]["Count"] += 1
                            all_dict[playerids_ranked_west[0]]["EloChange"] += elo_change_ranked_east
                            if gameresult_ranked_east == "won":
                                all_dict[playerids_ranked_west[0]]["Wins"] += 1
                        else:
                            all_dict[playerids_ranked_west[0]] = {"Count": 1, "Wins": 0, "EloChange": elo_change_ranked_east, "playername": game["players_data"][0]["player_name"]}
                            if gameresult_ranked_east == "won":
                                all_dict[playerids_ranked_west[0]]["Wins"] += 1
                        if playerids_ranked_west[1] in all_dict:
                            all_dict[playerids_ranked_west[1]]["Count"] += 1
                            all_dict[playerids_ranked_west[1]]["EloChange"] += elo_change_ranked_east
                            if gameresult_ranked_east == "won":
                                all_dict[playerids_ranked_west[1]]["Wins"] += 1
                        else:
                            all_dict[playerids_ranked_west[1]] = {"Count": 1, "Wins": 0, "EloChange": elo_change_ranked_east, "playername": game["players_data"][1]["player_name"]}
                            if gameresult_ranked_east == "won":
                                all_dict[playerids_ranked_west[1]]["Wins"] += 1
                    elif option == 'with':
                        if playerids_ranked_east[0] != playerid:
                            if playerids_ranked_east[0] in all_dict:
                                all_dict[playerids_ranked_east[0]]["Count"] += 1
                                all_dict[playerids_ranked_east[0]]["EloChange"] += elo_change_ranked_east
                                if gameresult_ranked_east == "won":
                                    all_dict[playerids_ranked_east[0]]["Wins"] += 1
                            else:
                                all_dict[playerids_ranked_east[0]] = {"Count": 1, "Wins": 0,"EloChange": elo_change_ranked_east, "playername": game["players_data"][2]["player_name"]}
                                if gameresult_ranked_east == "won":
                                    all_dict[playerids_ranked_east[0]]["Wins"] += 1
                        elif playerids_ranked_east[1] != playerid:
                            if playerids_ranked_east[1] in all_dict:
                                all_dict[playerids_ranked_east[1]]["Count"] += 1
                                all_dict[playerids_ranked_east[1]]["EloChange"] += elo_change_ranked_east
                                if gameresult_ranked_east == "won":
                                    all_dict[playerids_ranked_east[1]]["Wins"] += 1
                            else:
                                all_dict[playerids_ranked_east[1]] = {"Count": 1, "Wins": 0,"EloChange": elo_change_ranked_east, "playername": game["players_data"][3]["player_name"]}
                                if gameresult_ranked_east == "won":
                                    all_dict[playerids_ranked_east[1]]["Wins"] += 1
        else:
            patches_list.append(game["version"])
            for i, x in enumerate(playerids_ranked_west):
                if (x == playerid or playerid == "all") and (masterminds_ranked_west[i] == mm1 or mm1 == "" or mm1 == "All"):
                    if option == 'against':
                        if masterminds_ranked_east[0] in all_dict:
                            all_dict[masterminds_ranked_east[0]]["Count"] += 1
                            all_dict[masterminds_ranked_east[0]]["EloChange"] += elo_change_ranked_west
                            if gameresult_ranked_west == "won":
                                all_dict[masterminds_ranked_east[0]]["Wins"] += 1
                        else:
                            all_dict[masterminds_ranked_east[0]] = {"Count": 1, "Wins": 0, "EloChange": elo_change_ranked_west}
                            if gameresult_ranked_west == "won":
                                all_dict[masterminds_ranked_east[0]]["Wins"] += 1
                        if masterminds_ranked_east[1] == masterminds_ranked_east[0]:
                            continue
                        if masterminds_ranked_east[1] in all_dict:
                            all_dict[masterminds_ranked_east[1]]["Count"] += 1
                            all_dict[masterminds_ranked_east[1]]["EloChange"] += elo_change_ranked_west
                            if gameresult_ranked_west == "won":
                                all_dict[masterminds_ranked_east[1]]["Wins"] += 1
                        else:
                            all_dict[masterminds_ranked_east[1]] = {"Count": 1, "Wins": 0, "EloChange": elo_change_ranked_west}
                            if gameresult_ranked_west == "won":
                                all_dict[masterminds_ranked_east[1]]["Wins"] += 1
                    elif option == 'with':
                        if i == 0: teammate = 1
                        else: teammate = 0
                        if masterminds_ranked_west[teammate] in all_dict:
                            all_dict[masterminds_ranked_west[teammate]]["Count"] += 1
                            all_dict[masterminds_ranked_west[teammate]]["EloChange"] += elo_change_ranked_west
                            if gameresult_ranked_west == "won":
                                all_dict[masterminds_ranked_west[teammate]]["Wins"] += 1
                        else:
                            all_dict[masterminds_ranked_west[teammate]] = {"Count": 1, "Wins": 0,"EloChange": elo_change_ranked_west}
                            if gameresult_ranked_west == "won":
                                all_dict[masterminds_ranked_west[teammate]]["Wins"] += 1
            for i, x in enumerate(playerids_ranked_east):
                if (x == playerid or playerid == "all") and (masterminds_ranked_east[i] == mm1 or mm1 == "" or mm1 == "All"):
                    if option == 'against':
                        if masterminds_ranked_west[0] in all_dict:
                            all_dict[masterminds_ranked_west[0]]["Count"] += 1
                            all_dict[masterminds_ranked_west[0]]["EloChange"] += elo_change_ranked_east
                            if gameresult_ranked_east == "won":
                                all_dict[masterminds_ranked_west[0]]["Wins"] += 1
                        else:
                            all_dict[masterminds_ranked_west[0]] = {"Count": 1, "Wins": 0, "EloChange": elo_change_ranked_east}
                            if gameresult_ranked_east == "won":
                                all_dict[masterminds_ranked_west[0]]["Wins"] += 1
                        if masterminds_ranked_west[1] == masterminds_ranked_west[0]:
                            continue
                        if masterminds_ranked_west[1] in all_dict:
                            all_dict[masterminds_ranked_west[1]]["Count"] += 1
                            all_dict[masterminds_ranked_west[1]]["EloChange"] += elo_change_ranked_east
                            if gameresult_ranked_east == "won":
                                all_dict[masterminds_ranked_west[1]]["Wins"] += 1
                        else:
                            all_dict[masterminds_ranked_west[1]] = {"Count": 1, "Wins": 0, "EloChange": elo_change_ranked_east}
                            if gameresult_ranked_east == "won":
                                all_dict[masterminds_ranked_west[1]]["Wins"] += 1
                    elif option == 'with':
                        if i == 0: teammate = 1
                        else: teammate = 0
                        if playerids_ranked_east[teammate] != playerid:
                            if masterminds_ranked_east[teammate] in all_dict:
                                all_dict[masterminds_ranked_east[teammate]]["Count"] += 1
                                all_dict[masterminds_ranked_east[teammate]]["EloChange"] += elo_change_ranked_east
                                if gameresult_ranked_east == "won":
                                    all_dict[masterminds_ranked_east[teammate]]["Wins"] += 1
                            else:
                                all_dict[masterminds_ranked_east[teammate]] = {"Count": 1, "Wins": 0,"EloChange": elo_change_ranked_east}
                                if gameresult_ranked_east == "won":
                                    all_dict[masterminds_ranked_east[teammate]]["Wins"] += 1
    patches = list(dict.fromkeys(patches_list))
    new_patches = []
    for x in patches:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches = list(dict.fromkeys(new_patches))
    patches = sorted(patches, key=lambda x: int(x.split(".")[0] + x.split(".")[1]), reverse=True)
    avg_gameelo = round(sum(gameelo_list) / len(gameelo_list))
    if type(playername) == list:
        if playername[0] != 'all':
            suffix = "'s"
        else:
            suffix = ""
        output_string_1 = playername[0].capitalize() + suffix + " " + mm1 + " winrate " + option + " "
    else:
        output_string_1 = playername.capitalize() + "'s winrate " + option + " "
    if type(playername2) == list:
        if playername2[0] != 'all':
            suffix = "'s"
        else:
            suffix = ""
        if mm2 == "All":
            mm2_str = "Masterminds"
        else:
            mm2_str = mm2
        output_string_2 = playername2[0].capitalize() + suffix + " " + mm2_str
    else:
        output_string_2 = playername2.capitalize()
    if playerid == "all":
        avatar = "https://cdn.legiontd2.com/icons/Items/"+mm1+".png"
    else:
        avatar = "https://cdn.legiontd2.com/" + legion_api.getprofile(playerid)['avatarUrl']
    output = ""
    longest_text = 0
    if all_dict:
        reverse = True
        if sort == "EloChange+":
            sort = "EloChange"
            reverse = True
        elif sort == "EloChange-":
            sort = "EloChange"
            reverse = False
        newIndex = sorted(all_dict, key=lambda x: all_dict[x][sort], reverse=reverse)
        all_dict = {k: all_dict[k] for k in newIndex}
        final_output = ""
        for indx, player in enumerate(all_dict):
            if indx == 6: break
            if all_dict[player]["EloChange"] > 0:
                elo_prefix = "+"
            else:
                elo_prefix = ""
            if mm2 != "All":
                p_name = all_dict[player]["playername"]
            else:
                p_name = player
            win_lose_text = str(all_dict[player]["Wins"]) + 'W - ' + str(all_dict[player]["Count"] - all_dict[player]["Wins"]) + 'L**  ('
            output += "**"+p_name + ": " + win_lose_text + str(round(all_dict[player]["Wins"] / all_dict[player]["Count"] * 100, 1)) + '% ' + elo_prefix + str(all_dict[player]["EloChange"]) + " Elo)\n"
    else:
        if len(elo_change_list) > 0:
            sum_elo = sum(elo_change_list)
            if sum_elo > 0:
                string_pm = "+"
            else:
                string_pm = ""
            elo_change_sum = ", Elo change: " + string_pm + str(sum_elo)
        else:
            elo_change_sum = ""
        try:
            winrate = round(win_count / game_count * 100, 2)
        except ZeroDivisionError as e:
            print(e)
            return "No games found."
        output += "**"+str(win_count) + 'W - ' + str(game_count - win_count) + 'L (' + str(winrate) + '% winrate' + elo_change_sum + ')**'
    embed = discord.Embed(color=0x21eb1e)
    embed.add_field(name='(From ' + str(games) + ' ranked games, avg. elo: ' + str(avg_gameelo) + " " + util.get_ranked_emote(avg_gameelo) + ")", value=output)
    embed.set_author(name=output_string_1 + output_string_2, icon_url=avatar)
    embed.set_footer(text='Patches: ' + ', '.join(patches))
    return embed

class Winrate(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    @app_commands.command(name="winrate", description="Shows player1's winrate against/with player2.")
    @app_commands.describe(playername1='Enter playername1.', playername2='Enter playername2 or all for 6 most common players', option='Against or with?', games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           min_elo='Enter minium average game elo to include in the data set', patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.',
                           sort="Sort by? (Only for playername2 = all)")
    @app_commands.choices(option=[
        discord.app_commands.Choice(name='against', value='against'),
        discord.app_commands.Choice(name='with', value='with')
    ])
    @app_commands.choices(sort=[
        discord.app_commands.Choice(name='Count', value='Count'),
        discord.app_commands.Choice(name='EloChange+', value='EloChange+'),
        discord.app_commands.Choice(name='EloChange-', value='EloChange-')
    ])
    async def winrate(self, interaction: discord.Interaction, playername1: str, playername2: str, option: discord.app_commands.Choice[str], games: int = 0, min_elo: int = 0, patch: str = util.current_season, sort: discord.app_commands.Choice[str] = "Count"):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            if "," in playername1:
                if playername1.split(",")[0].lower() == "all" and games == 0 and min_elo == 0 and patch == util.current_season:
                    min_elo = util.current_minelo
            try:
                sort = sort.value
            except AttributeError:
                pass
            try:
                response = await loop.run_in_executor(pool, functools.partial(winrate, playername1, playername2, option.value, games, patch, min_elo=min_elo, sort=sort))
                pool.shutdown()
                if type(response) == discord.Embed:
                    await interaction.followup.send(embed=response)
                else:
                    await interaction.followup.send(response)
            except Exception:
                print("/" + interaction.command.name + " failed. args: " + str(interaction.data.values()))
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

async def setup(bot:commands.Bot):
    await bot.add_cog(Winrate(bot))