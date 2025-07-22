import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import concurrent.futures
import traceback
import functools
import json
import difflib
import re
import drachbot_db
import util
import legion_api
from peewee_pg import GameData, PlayerData

player_map = {1:[0,1],2:[1,0],5:[2,3],6:[3,2]}

def winrate(playername1, playername2, option, mm1, mm2, games, patch, min_elo = 0, sort = "Count", text_output = False, soloq = False):
    if playername1.casefold() != "all":
        try:
            playerid1 = util.validate_playername(playername1)
        except Exception as e:
            return e
    else:
        playerid1 = "all"
    if mm2 == "all" and playerid1 == "all":
        playerid2 = "all"
    elif playername2.casefold() != "all":
        try:
            playerid2 = util.validate_playername(playername2)
        except Exception as e:
            return e
    else:
        playerid2 = "all"
    if playerid1 == "all":
        if not mm1:
            return "You need to select a `mm1` when using `playername1:all`"
        avatar = "https://cdn.legiontd2.com/icons/Items/"+mm1+".png"
        playername1 = "All"
    else:
        profile = legion_api.getprofile(playerid1)
        try:
            avatar = "https://cdn.legiontd2.com/" + profile['avatarUrl']
        except KeyError:
            avatar = "https://cdn.legiontd2.com/icons/DefaultAvatar.png"
        playername1 = profile["playerName"]
    req_columns = [[GameData.game_id, GameData.queue, GameData.date, GameData.version, GameData.ending_wave, GameData.game_elo, GameData.player_ids,
                    PlayerData.player_id, PlayerData.player_name, PlayerData.player_slot, PlayerData.game_result, PlayerData.legion, PlayerData.elo_change, PlayerData.party_size],
                   ["game_id", "date", "version", "ending_wave", "game_elo"],
                   ["player_id", "player_name", "player_slot", "game_result", "legion", "elo_change", "party_size"]]
    history_raw = drachbot_db.get_matchistory(playerid1, games, min_elo=min_elo, patch=patch, earlier_than_wave10=True, req_columns=req_columns)
    if type(history_raw) == str:
        return history_raw
    games = len(history_raw)
    if games == 0:
        return 'No games found.'
    gameelo_list = []
    patches = set()
    winrate_dict = {"Count": 0, "Wins": 0, "EloChange": 0, "Teammates":{}, "Enemies":{}, "Masterminds":{}}
    for game in history_raw:
        for player in game["players_data"]:
            if (playerid1 == player["player_id"] and not mm1) or (playerid1 == "all" and mm1 == player["legion"])\
                    or (playerid1 == player["player_id"] and mm1 and mm1 == player["legion"]):
                if soloq and player["party_size"] == 2:
                    continue
                if playerid2 == "all":
                    gameelo_list.append(game["game_elo"])
                    patches.add(util.cleanup_version_string(game["version"]))
                winrate_dict["Count"] += 1
                winrate_dict["EloChange"] += player["elo_change"]
                if player["game_result"] == "won":
                    winrate_dict["Wins"] += 1
                for player_slot in player_map:
                    if player["player_slot"] == player_slot:
                        continue
                    if player_map[player_slot][0] == player_map[player["player_slot"]][1]:
                        if option == "against":
                            continue
                        player_type = "Teammates"
                    else:
                        if option == "with":
                            continue
                        player_type = "Enemies"
                    if (mm2 == "all" and (playerid1 == "all" or playerid2 == "all")) or (playerid2 == "all" and mm2 != "all" and mm2):
                        temp_pid = game["players_data"][player_map[player_slot][0]]["legion"]
                        temp_legion = None
                    else:
                        temp_pid = game["players_data"][player_map[player_slot][0]]["player_id"]
                        if playerid2 == temp_pid:
                            gameelo_list.append(game["game_elo"])
                            patches.add(util.cleanup_version_string(game["version"]))
                        temp_legion = game["players_data"][player_map[player_slot][0]]["legion"]
                    target_dict = winrate_dict[player_type]
                    if temp_pid not in target_dict:
                        target_dict[temp_pid] = {"Count": 1, "Wins": 0, "EloChange": 0, "Masterminds": {}, "PlayerName": game["players_data"][player_map[player_slot][0]]["player_name"]}
                    else:
                        target_dict[temp_pid]["Count"] += 1
                    target_dict[temp_pid]["EloChange"] += player["elo_change"]
                    if player["game_result"] == "won":
                        target_dict[temp_pid]["Wins"] += 1
                    if mm2 != "all" or playerid1 != "all":
                        if temp_legion not in target_dict[temp_pid]["Masterminds"]:
                            target_dict[temp_pid]["Masterminds"][temp_legion] = {"Count": 1, "Wins": 0, "EloChange": 0}
                        else:
                            target_dict[temp_pid]["Masterminds"][temp_legion]["Count"] += 1
                        target_dict[temp_pid]["Masterminds"][temp_legion]["EloChange"] += player["elo_change"]
                        if player["game_result"] == "won":
                            target_dict[temp_pid]["Masterminds"][temp_legion]["Wins"] += 1
    #SOME SETUP BEFORE CREATING THE EMBED
    patches = sorted(patches, key=lambda x: int(x.split(".")[0] + x.split(".")[1]), reverse=True)
    try:
        avg_gameelo = round(sum(gameelo_list) / len(gameelo_list))
    except ZeroDivisionError:
        avg_gameelo = 0
    output_string = ""
    reverse = True
    if playerid1 != "all":
        if sort == "EloChange+":
            sort = "EloChange"
            reverse = True
        elif sort == "EloChange-":
            sort = "EloChange"
            reverse = False
    else:
        sort = "Count"
    if option == "against":
        player_type = "Enemies"
    else:
        player_type = "Teammates"
    if (playerid2 != "all" and mm2 != "all") or (playerid2 == "all" and mm2 != "all" and mm2):
        try:
            if not mm2 or (playerid2 == "all" and mm2 != "all" and mm2):
                if playerid2 == "all" and mm2 != "all" and mm2:
                    playerid2 = mm2
                games = winrate_dict[player_type][playerid2]["Count"]
                wins = winrate_dict[player_type][playerid2]["Wins"]
                losses = games-wins
                elo_change = winrate_dict[player_type][playerid2]["EloChange"]
            else:
                games = winrate_dict[player_type][playerid2]["Masterminds"][mm2]["Count"]
                wins = winrate_dict[player_type][playerid2]["Masterminds"][mm2]["Wins"]
                losses = games-wins
                elo_change = winrate_dict[player_type][playerid2]["Masterminds"][mm2]["EloChange"]
            try:
                winrate = round(wins / games * 100, 1)
            except ZeroDivisionError:
                winrate = 0
        except KeyError:
            return f"No games {option} {playername2, mm2} found."
        output_string = f"**{wins}W - {losses}L, {winrate}%WR, {elo_change:+} Elo**"
    else:
        if playerid2 == "all":
            target_dict = winrate_dict
        else:
            target_dict = winrate_dict[player_type][playerid2]
        games = target_dict["Count"]
        wins = target_dict["Wins"]
        try:
            winrate = round(wins / games * 100, 1)
        except ZeroDivisionError:
            winrate = 0
        losses = games - wins
        elo_change = target_dict["EloChange"]
        if text_output:
            output_string = '(From ' + str(games) + ' ranked games, avg. elo: ' + str(avg_gameelo) + ")\n"
            output_string += f"Total Stats: {wins}W - {losses}L, {winrate}% Winrate, {elo_change:+} Elo\n"
        else:
            output_string = f"**Total Stats:** {wins}W - {losses}L, {winrate}% Winrate, {elo_change:+} Elo\n"
        if playerid2 == "all":
            target_dict = winrate_dict[player_type]
        else:
            target_dict = winrate_dict[player_type][playerid2]["Masterminds"]
        newIndex = sorted(target_dict, key=lambda x: target_dict[x][sort], reverse=reverse)
        target_dict = {k: target_dict[k] for k in newIndex}
        for i, x in enumerate(target_dict):
            games2 = target_dict[x]["Count"]
            wins2 = target_dict[x]["Wins"]
            losses2 = games2 - wins2
            elo_change2 = target_dict[x]["EloChange"]
            if elo_change2 >= 0:
                elo_change2 = "+"+str(elo_change2)
            if mm2 == "all":
                if len(x) > 10:
                    x_string = x[:10]
                else:
                    x_string = x
                x_string = x_string + " " * (10 - len(x))
                try:
                    emoji = util.mm_emotes[x]
                except KeyError:
                    emoji = "?"
            else:
                if i == 10 and not text_output:
                    break
                x_string = target_dict[x]["PlayerName"]
                if re.search(u'[\u4e00-\u9fff]', x_string):
                    max_char = 7
                else:
                    max_char = 11
                if text_output:
                    max_char = 16
                if len(x_string) > max_char:
                    x_string = x_string[:max_char]
                else:
                    x_string = x_string
                x_string = x_string + " " * (max_char - len(x_string))
                emoji = ""
            output_string += (f"{emoji}`{x_string}: {wins2}W{" "*(3-len(str(wins2)))} {losses2}L,{" "*(3-len(str(losses2)))}"
                              f" {round(wins2 / games2 * 100, 1)}%,{" "*(4-len(str(round(wins2 / games2 * 100, 1))))} "
                              f"{elo_change2}{" "*(4-len(str(elo_change2)))} Elo`\n")
    if text_output:
        with open("Files/temp.txt", "w", encoding="utf-8") as f:
            f.write(output_string.replace("`", ""))
            f.close()
        return "Files/temp.txt"
    embed = discord.Embed(color=0x21eb1e, description='**(From ' + str(games) + ' ranked games, avg. elo: ' +
                                                      str(avg_gameelo) + " " + util.get_ranked_emote(avg_gameelo) + ")**\n"+output_string)
    if not mm1:
        mm1 = ""
    else:
        mm1 = "-"+mm1
    if not mm2:
        mm2 = ""
    elif mm2 == "all":
        mm2 = " Masterminds"
    else:
        mm2 = "-"+mm2
    embed.set_author(name=f"{playername1}{mm1} {option} {playername2.capitalize()}{mm2}", icon_url=avatar)
    if len(patches) > 9:
        patches = patches[:9]
        patches.append("...")
    embed.set_footer(text='Patches: ' + ', '.join(patches))
    return embed

class Winrate(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    @app_commands.command(name="winrate", description="Shows player1's winrate against/with player2.")
    @app_commands.describe(playername1='Enter playername1.', playername2='Enter playername2 or all for 6 most common players', option='Against or with?', games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           min_elo='Enter minium average game elo to include in the data set', patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.',
                           sort="Sort by? (Only for playername2 = all)", text_output = "Output all the data into a text file.", soloq_only = "Only consider soloq games from player1. (Default = False)")
    @app_commands.choices(option=[
        discord.app_commands.Choice(name='against', value='against'),
        discord.app_commands.Choice(name='with', value='with')
    ])
    @app_commands.choices(mm1=util.mm_choices)
    @app_commands.choices(mm2=[discord.app_commands.Choice(name="All", value="all")]+util.mm_choices)
    @app_commands.choices(sort=[
        discord.app_commands.Choice(name='Count', value='Count'),
        discord.app_commands.Choice(name='EloChange+', value='EloChange+'),
        discord.app_commands.Choice(name='EloChange-', value='EloChange-')
    ])
    async def winrate(self, interaction: discord.Interaction, playername1: str, playername2: str, option: discord.app_commands.Choice[str],
                      mm1: discord.app_commands.Choice[str] = None, mm2: discord.app_commands.Choice[str] = None, games: int = 0, min_elo: int = 0,
                      patch: str = "", sort: discord.app_commands.Choice[str] = "Count", text_output: bool = False, soloq_only: bool = False):
        await interaction.response.defer(ephemeral=False, thinking=True)
        if playername1.split(",")[0].lower() == "all" and games == 0 and min_elo == 0 and not patch:
            min_elo = util.get_current_minelo()
        try:
            sort = sort.value
        except AttributeError:
            pass
        try:
            mm1 = mm1.value
        except AttributeError:
            pass
        try:
            mm2 = mm2.value
        except AttributeError:
            pass
        if not patch:
            player_patches = playername1.lower() != "all"
            patch = util.get_current_patches(player_patches=player_patches)
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ProcessPoolExecutor() as pool:
                response = await loop.run_in_executor(pool, functools.partial(winrate, playername1, playername2, option.value, mm1, mm2, games, patch, min_elo=min_elo, sort=sort, text_output=text_output, soloq=soloq_only))
                pool.shutdown()
                if text_output:
                    await interaction.followup.send(file=discord.File(response, filename="temp.txt"))
                elif type(response) == discord.Embed:
                    await interaction.followup.send(embed=response)
                else:
                    await interaction.followup.send(response)
        except Exception:
            print("/" + interaction.command.name + " failed. args: " + str(interaction.data.values()))
            traceback.print_exc()
            await interaction.followup.send("Bot error :sob:")

async def setup(bot:commands.Bot):
    await bot.add_cog(Winrate(bot))