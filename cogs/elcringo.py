import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import concurrent.futures
import traceback
import functools

import drachbot_db
import util
import legion_api
from peewee_pg import GameData, PlayerData

send_order = {0: 2, 1: 3, 2: 1, 3: 0}

def elcringo(playername, games, patch, min_elo, option, sort="date", saves = "Sent"):
    if playername.lower() == 'all':
        playerid = 'all'
        suffix = ''
    elif 'nova cup' in playername:
        suffix = ''
        playerid = playername
    else:
        playerid = legion_api.getid(playername)
        if playerid == 0:
            return 'Player ' + playername + ' not found.'
        if playerid == 1:
            return 'API limit reached, you can still use "all" commands.'
        suffix = "'s"
    save_count_list = []
    save_count_pre10_list = []
    save_count = 0
    save_count_pre10 = 0
    ending_wave_list = []
    worker_10_list = []
    income_10_list = []
    mythium_list = []
    mythium_pre10_list = []
    mythium_list_pergame = []
    kinghp_list = []
    kinghp_enemy_list = []
    leaks_list = []
    leaks_pre10_list = []
    gameelo_list = []
    mercs_pre10 = [0,0]
    req_columns = [[GameData.game_id, GameData.queue, GameData.date, GameData.version, GameData.ending_wave, GameData.game_elo, GameData.player_ids, GameData.left_king_hp, GameData.right_king_hp,
                    PlayerData.player_id, PlayerData.player_slot, PlayerData.workers_per_wave, PlayerData.leaks_per_wave, PlayerData.income_per_wave],
                   ["game_id", "date", "version", "ending_wave", "game_elo", "left_king_hp", "right_king_hp"],
                   ["player_id", "player_slot", "workers_per_wave", "leaks_per_wave", "income_per_wave"]]
    if saves == "Sent" or playerid == 'all':
        req_columns[0].append(PlayerData.mercs_sent_per_wave)
        req_columns[0].append(PlayerData.kingups_sent_per_wave)
        req_columns[2].append("mercs_sent_per_wave")
        req_columns[2].append("kingups_sent_per_wave")
        merc_field = "mercs_sent_per_wave"
        king_field = "kingups_sent_per_wave"
    else:
        req_columns[0].append(PlayerData.mercs_received_per_wave)
        req_columns[0].append(PlayerData.kingups_received_per_wave)
        req_columns[2].append("mercs_received_per_wave")
        req_columns[2].append("kingups_received_per_wave")
        merc_field = "mercs_received_per_wave"
        king_field = "kingups_received_per_wave"
    history_raw = drachbot_db.get_matchistory(playerid, games, min_elo, patch, sort_by=sort, earlier_than_wave10=True, req_columns=req_columns)
    if type(history_raw) == str:
        return history_raw
    games = len(history_raw)
    if games == 0:
        return 'No games found.'
    if 'nova cup' in playerid:
        playerid = 'all'
    patches = []
    print('starting elcringo command...')
    for game in history_raw:
        patches.append(game["version"])
        ending_wave_list.append(game["ending_wave"])
        gameelo_list.append(game["game_elo"])
        mythium_list_pergame.clear()
        for i, player in enumerate(game["players_data"]):
            if player["player_id"] == playerid or playerid == 'all':
                for n in range(game["ending_wave"]):
                    small_send = 0
                    try:
                        if player[king_field][n].split("!")[0] == "":
                            kingups = 0
                        else:
                            kingups = len(player[king_field][n].split("!")) * 20
                        send = util.count_mythium(player[merc_field][n]) + kingups
                        if n <= 9:
                            ip_myth = util.get_inc_power_myth(player[merc_field][n].split("!"))
                            mercs_pre10[0] += len(player[king_field][n].split("!")) * 20
                            mercs_pre10[0] += ip_myth[0]
                            mercs_pre10[1] += ip_myth[1]
                    except IndexError:
                        break
                    mythium_list_pergame.append(send)
                    if n <= 9:
                        if player["workers_per_wave"][n] > 5:
                            small_send = (player["workers_per_wave"][n] - 5) / 4 * 20
                        if send <= small_send and option == "Yes":
                            save_count_pre10 += 1
                        elif send == 0 and option == "No":
                            save_count_pre10 += 1
                    elif n > 9:
                        if game["version"].startswith('v11') or game["version"].startswith('v9'):
                            worker_adjusted = player["workers_per_wave"][n]
                        elif game["version"].startswith('v10'):
                            worker_adjusted = player["workers_per_wave"][n] * (pow((1 + 6 / 100), n + 1))
                        small_send = worker_adjusted / 4 * 20
                        if send <= small_send and option == "Yes":
                            save_count += 1
                        elif send == 0 and option == "No":
                            save_count += 1
                mythium_list.append(sum(mythium_list_pergame))
                mythium_pre10 = 0
                for counter, myth in enumerate(mythium_list_pergame):
                    mythium_pre10 += myth
                    if counter == 9:
                        break
                mythium_pre10_list.append(mythium_pre10)
                try:
                    worker_10_list.append(player["workers_per_wave"][9])
                    income_10_list.append(player["income_per_wave"][9])
                except Exception:
                    pass
                leak_amount = 0
                leak_pre10_amount = 0
                for y in range(game["ending_wave"]):
                    if saves == "Received":
                        try:
                            if len(player["leaks_per_wave"][y]) > 0:
                                p = util.calc_leak(player["leaks_per_wave"][y], y)
                                leak_amount += p
                                if y < 10:
                                    leak_pre10_amount += p
                        except IndexError:
                            break
                    else:
                        enemy_index = send_order.get(i)
                        try:
                            if len(game["players_data"][enemy_index]["leaks_per_wave"][y]) > 0:
                                p = util.calc_leak(game["players_data"][enemy_index]["leaks_per_wave"][y], y)
                                leak_amount += p
                                if y < 10:
                                    leak_pre10_amount += p
                        except IndexError:
                            break
                leaks_list.append(leak_amount / game["ending_wave"])
                leaks_pre10_list.append(leak_pre10_amount / 10)
                try:
                    if i == 0 or 1:
                        kinghp_list.append(game["left_king_hp"][9])
                        kinghp_enemy_list.append(game["right_king_hp"][9])
                    else:
                        kinghp_list.append(game["right_king_hp"][9])
                        kinghp_enemy_list.append(game["left_king_hp"][9])
                except Exception:
                    pass
            mythium_list_pergame.clear()
        save_count_pre10_list.append(save_count_pre10)
        save_count_list.append(save_count)
        save_count_pre10 = 0
        save_count = 0
    new_patches = []
    for x in patches:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches = list(dict.fromkeys(new_patches))
    patches = sorted(patches, key=lambda x: int(x.split(".")[0] + x.split(".")[1]), reverse=True)
    waves_post10 = round(sum(ending_wave_list) / len(ending_wave_list), 2) - 10
    if playerid == 'all':
        saves_pre10 = round(sum(save_count_pre10_list) / len(save_count_pre10_list) / 4, 2)
        saves_post10 = round(sum(save_count_list) / len(save_count_list) / 4, 2)
    else:
        saves_pre10 = round(sum(save_count_pre10_list) / len(save_count_pre10_list), 2)
        saves_post10 = round(sum(save_count_list) / len(save_count_list), 2)
    mythium_pre10 = round(sum(mythium_pre10_list) / len(mythium_pre10_list))
    mythium = round(sum(mythium_list) / len(mythium_list))
    leaks_total = round(sum(leaks_list) / len(leaks_list), 1)
    leaks_pre10_total = round(sum(leaks_pre10_list) / len(leaks_pre10_list), 1)
    king_hp_10 = sum(kinghp_list) / len(kinghp_list)
    king_hp_enemy_10 = sum(kinghp_enemy_list) / len(kinghp_enemy_list)
    mercs_pre10_percent = round(mercs_pre10[0] / (mercs_pre10[0] + mercs_pre10[1]) * 100)
    if playername == "all" or "nova cup" in playername:
        king_hp_10 = (king_hp_10 + king_hp_enemy_10) / 2
        string2 = '**King hp on 10:** ' + str(round(king_hp_10 * 100, 2)) + '%\n'
    else:
        string2 = '**King hp on 10:** ' + str(round(king_hp_10 * 100, 2)) + '%, Enemy King: ' + str(round(king_hp_enemy_10 * 100, 2)) + '%\n'
    avg_gameelo = round(sum(gameelo_list) / len(gameelo_list))
    if playerid == "all":
        playername = playername.capitalize()
        avatar = "https://cdn.legiontd2.com/icons/Ogre.png"
    else:
        profile = legion_api.getprofile(playerid)
        avatar = "https://cdn.legiontd2.com/" + profile['avatarUrl']
        playername = profile["playerName"]
    if playerid == 'all':
        saves = ''
    if saves == "Sent":
        leak_string = " Caused"
    else:
        leak_string = ""
    embed = discord.Embed(color=0x4565d9, description='(From ' + str(games) + ' ranked games, avg. elo: ' + str(avg_gameelo) + " " + util.get_ranked_emote(avg_gameelo) + ")\n\n" +
                                                      '**Saves first 10:** ' + str(saves_pre10) + '/10 waves (' + str(round(saves_pre10 / 10 * 100, 2)) + '%)\n' +
                                                      '**Saves after 10:** ' + str(saves_post10) + '/' + str(round(waves_post10, 2)) + ' waves (' + str(round(saves_post10 / waves_post10 * 100, 2)) + '%)\n' +
                                                      f'**Pre 10 Mercs:** Income: {mercs_pre10_percent}%, Power: {100-mercs_pre10_percent}%\n'+
                                                      '**Worker on 10:** ' + str(round(sum(worker_10_list) / len(worker_10_list), 2)) + "\n" +
                                                      f'**Leaks{leak_string}:** ' + str(leaks_total) + "% (First 10: " + str(leaks_pre10_total) + "%)\n" +
                                                      string2+
                                                      '**Income on 10:** ' + str(round(sum(income_10_list) / len(income_10_list), 1)) + "\n" +
                                                      f'**Myth {saves}:** Pre 10: ' + str(mythium_pre10) + ', Post 10: ' + str(mythium - mythium_pre10) + '\n')
    embed.set_author(name=playername + suffix +" " + saves +" elcringo stats", icon_url=avatar)
    embed.set_footer(text='Patches: ' + ', '.join(patches))
    return embed


class Elcringo(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    @app_commands.command(name="elcringo", description="Shows how cringe someone is.")
    @app_commands.describe(playername='Enter playername or "all" for all available data.', games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.', min_elo='Enter minium average game elo to include in the data set',
                           option='Count small sends as save?', sort='Sort by?', saves="Sent or received")
    @app_commands.choices(option=[
        discord.app_commands.Choice(name='Yes', value="Yes"),
        discord.app_commands.Choice(name='No', value="No")
    ])
    @app_commands.choices(sort=[
        discord.app_commands.Choice(name='date', value="date"),
        discord.app_commands.Choice(name='elo', value="elo")
    ])
    @app_commands.choices(saves=[
        discord.app_commands.Choice(name='Sent', value='Sent'),
        discord.app_commands.Choice(name='Received', value='Received')
    ])
    async def elcringo(self, interaction: discord.Interaction, playername: str, games: int = 0, min_elo: int = 0, patch: str = util.current_season, option: discord.app_commands.Choice[str] = "Yes", sort: discord.app_commands.Choice[str] = "date", saves: discord.app_commands.Choice[str] = 'Sent'):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            if playername.lower() == "all" and games == 0 and min_elo == 0 and patch == util.current_season:
                min_elo = util.current_minelo
            try:
                option = option.value
            except AttributeError:
                pass
            try:
                sort = sort.value
            except AttributeError:
                pass
            try:
                saves = saves.value
            except AttributeError:
                pass
            try:
                response = await loop.run_in_executor(pool, functools.partial(elcringo, playername, games, patch, min_elo, option, sort=sort, saves=saves))
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
    await bot.add_cog(Elcringo(bot))