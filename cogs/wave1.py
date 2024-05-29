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


def wave1tendency(playername, option, games, min_elo, patch, sort="date"):
    if playername.lower() == 'all':
        playerid = 'all'
        suffix = ''
    elif 'nova cup' in playername:
        suffix = ''
        playerid = playername
    else:
        suffix = "'s"
        playerid = legion_api.getid(playername)
        if playerid == 0:
            return 'Player ' + playername + ' not found.'
        if playerid == 1:
            return 'API limit reached.'
    snail_count = 0
    kingup_atk_count = 0
    kingup_regen_count = 0
    kingup_spell_count = 0
    save_count = 0
    leaks_count = 0
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
    req_columns = [[GameData.game_id, GameData.queue, GameData.date, GameData.version, GameData.ending_wave, GameData.game_elo, GameData.player_ids,
                    PlayerData.player_id, PlayerData.player_slot, PlayerData.game_result, col1, col2, PlayerData.leaks_per_wave],
                   ["game_id", "date", "version", "ending_wave", "game_elo"],
                   ["player_id", "player_slot", "game_result", option_key, option_key2, "leaks_per_wave"]]
    history_raw = drachbot_db.get_matchistory(playerid, games, min_elo=min_elo, patch=patch, sort_by=sort, earlier_than_wave10=True, req_columns=req_columns)
    if type(history_raw) == str:
        return history_raw
    games = len(history_raw)
    if games == 0:
        return 'No games found.'
    if 'nova cup' in playerid:
        playerid = 'all'
    patches = []
    gameelo_list = []
    for game in history_raw:
        patches.append(game["version"])
        gameelo_list.append(game["game_elo"])
        for i, player in enumerate(game["players_data"]):
            if player["player_id"] == playerid or playerid == 'all':
                if len(player[option_key][0]) > 0:
                    if player[option_key][0].split("!")[0] == 'Snail':
                        snail_count = snail_count + 1
                        if option == 'send' and playerid != 'all':
                            if i == 0:
                                if len(game["players_data"][2]["leaks_per_wave"][0]) != 0:
                                    leaks_count += 1
                            if i == 1:
                                if len(game["players_data"][3]["leaks_per_wave"][0]) != 0:
                                    leaks_count += 1
                            if i == 2:
                                if len(game["players_data"][1]["leaks_per_wave"][0]) != 0:
                                    leaks_count += 1
                            if i == 3:
                                if len(game["players_data"][0]["leaks_per_wave"][0]) != 0:
                                    leaks_count += 1
                        if option == 'received' or playerid == 'all':
                            if len(player["leaks_per_wave"][0]) != 0:
                                leaks_count += 1
                        continue
                elif len(player[option_key2][0]) > 0:
                    if str(player[option_key2][0].split("!")[0]) == 'Upgrade King Attack':
                        kingup_atk_count = kingup_atk_count + 1
                        continue
                    if str(player[option_key2][0].split("!")[0]) == 'Upgrade King Regen':
                        kingup_regen_count = kingup_regen_count + 1
                        continue
                    if str(player[option_key2][0].split("!")[0]) == 'Upgrade King Spell':
                        kingup_spell_count = kingup_spell_count + 1
                        continue
                else:
                    save_count = save_count + 1
                    continue
    new_patches = []
    for x in patches:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches = list(dict.fromkeys(new_patches))
    patches = sorted(patches, key=lambda x: int(x.split(".")[0] + x.split(".")[1]), reverse=True)
    send_total = kingup_atk_count+kingup_regen_count+kingup_spell_count+snail_count+save_count
    kingup_total = kingup_atk_count+kingup_regen_count+kingup_spell_count
    avg_gameelo = round(sum(gameelo_list) / len(gameelo_list))
    if send_total == 0:
        return 'Not enough ranked data'
    if playerid == "all":
        playername = "All"
        avatar = "https://cdn.legiontd2.com/icons/Snail.png"
        option = ''
    else:
        profile = legion_api.getprofile(playerid)
        avatar = "https://cdn.legiontd2.com/" + profile['avatarUrl']
        playername = profile["playerName"]
    embed = discord.Embed(color=0xE73333, description='(From ' + str(games) + ' ranked games, avg. elo: ' + str(avg_gameelo) + " " + util.get_ranked_emote(avg_gameelo) + ")\n\n"+
                          '**Kingup:** '+str(kingup_total) + ' | ' + str(round(util.division_by_zero(kingup_total, send_total)*100,1)) + '% (Attack: ' + str(kingup_atk_count) + ' Regen: ' + str(kingup_regen_count) + ' Spell: ' + str(kingup_spell_count) + ')\n'+
                          '**Snail:** ' + str(snail_count) + ' | ' + str(round(util.division_by_zero(snail_count, send_total)*100,1)) + '% (Leak count: ' + str(leaks_count) + ' (' + str(round(util.division_by_zero(leaks_count, snail_count)*100, 2)) + '%))\n'+
                          '**Save:** ' + str(save_count) + ' | '  + str(round(util.division_by_zero(save_count, send_total)*100,1)) + '%')
    embed.set_author(name=playername + suffix+" Wave 1 " + option + " stats", icon_url=avatar)
    embed.set_footer(text='Patches: ' + ', '.join(patches))
    return embed

class Wave1(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    @app_commands.command(name="wave1", description="Shows Wave 1 tendency.")
    @app_commands.describe(playername='Enter playername or "all" for all available data.',
                           games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           min_elo='Enter minium average game elo to include in the data set',
                           patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.',
                           option='Send or received?', sort="Sort by?")
    @app_commands.choices(option=[
        discord.app_commands.Choice(name='send', value='send'),
        discord.app_commands.Choice(name='received', value='received')
    ])
    @app_commands.choices(sort=[
        discord.app_commands.Choice(name='date', value="date"),
        discord.app_commands.Choice(name='elo', value="elo")
    ])
    async def wave1(self, interaction: discord.Interaction, playername: str, games: int = 0, min_elo: int = 0, patch: str = util.current_season, option: discord.app_commands.Choice[str] = "send", sort: discord.app_commands.Choice[str] = "date"):
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
                response = await loop.run_in_executor(pool, functools.partial(wave1tendency, playername, option, games, min_elo, patch, sort))
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
    await bot.add_cog(Wave1(bot))