import asyncio
import functools
import json
import traceback
from datetime import datetime
import discord
import responses
from discord import app_commands
import os
import concurrent.futures
import platform
from twitchAPI.twitch import Twitch
from twitchAPI.helper import first
import discord_timestamps
from discord_timestamps import TimestampType

with open('Files/Secrets.json') as f:
    secret_file = json.load(f)

async def twitch_get_streams(names: list, playernames: list = []) -> dict:
    twitch = await Twitch(secret_file.get("twitchappid"), secret_file.get("twitchsecret"))
    streams_dict = {}
    for i, name in enumerate(names):
        user = await first(twitch.get_users(logins=name))
        stream = await first(twitch.get_streams(user_id=user.id))
        if type(stream) == type(None):
            try:
                streams_dict[user.display_name] = {"live": False, "started_at": "", "playername": playernames[i]}
            except IndexError:
                streams_dict[user.display_name] = {"live": False, "started_at": "", "playername": ""}
        else:
            try:
                streams_dict[user.display_name] = {"live": True, "started_at": str(stream.started_at), "playername": playernames[i]}
            except IndexError:
                streams_dict[user.display_name] = {"live": True, "started_at": str(stream.started_at), "playername": ""}
    await  twitch.close()
    return streams_dict

async def send_message(message, user_message, is_private, username):
    #try:
    loop = asyncio.get_running_loop()
    with concurrent.futures.ProcessPoolExecutor() as pool:
        response = await loop.run_in_executor(pool, functools.partial(responses.handle_response, user_message, username))
        await message.author.send(response) if is_private else await message.channel.send(response)
    # except Exception as e:
    #     print(e)

def custom_exception_handler(loop, context):
    loop.default_exception_handler(context)

    exception = context.get('exception')
    if isinstance(exception, Exception):
        print(context)

def get_game_elo(playerlist, classic):
    elo = 0
    new_list = []
    # if classic == True:
    #     for player in playerlist:
    #         try:
    #             classic_elo = int(responses.apicall_getstats(responses.apicall_getid(player.split(":")[0]))["classicElo"])
    #         except KeyError:
    #             classic_elo = 0
    #         new_list.append(player.split(":")[0]+":"+str(classic_elo))
    #         elo += classic_elo
    for player in playerlist:
        ranked_elo = int(player.split(":")[1])
        new_list.append(player.split(":")[0]+":"+str(ranked_elo))
        elo += ranked_elo
    new_list.append(str(round(elo/len(playerlist))))
    return new_list

def save_live_game(gameid, playerlist):
    if len(playerlist) == 5:
        with open("Livegame/Ranked/" + str(gameid)+"_"+str(playerlist[4])+".txt", "w", encoding="utf_8") as f:
            f.write('\n'.join(playerlist))
            f.close()
    # else:
    #     with open("Livegame/Classic/" + str(gameid) + "_"+str(playerlist[8])+".txt", "w", encoding="utf_8") as f:
    #         f.write('\n'.join(playerlist))
    #         f.close()

def get_top_games(queue):
    if queue == "Ranked":
        path = "Livegame/Ranked/"
    else:
        path = "Livegame/Classic/"
    livegame_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.txt')]
    livegame_files = sorted(livegame_files, key=lambda x: int(x.split("_")[1].split(".")[0]), reverse=True)
    topgames = []
    for game in livegame_files:
        path2 = path + game
        mod_date = datetime.utcfromtimestamp(os.path.getmtime(path2))
        date_diff = datetime.now() - mod_date
        if platform.system() == "Linux":
            minutes_diff = date_diff.total_seconds() / 60
        elif platform.system() == "Windows":
            minutes_diff = date_diff.total_seconds() / 60 - 60
        if minutes_diff > 35:
            os.remove(path2)
            continue
        if len(topgames) < 3:
            topgames.append(game)
    output = ""
    if len(topgames) == 0:
        return "No games found."
    for idx, game2 in enumerate(topgames):
        path2 = path+game2
        mod_date = datetime.utcfromtimestamp(os.path.getmtime(path2)).timestamp()
        #date_diff = datetime.now() - mod_date
        timestamp = discord_timestamps.format_timestamp(mod_date, TimestampType.RELATIVE)
        # if platform.system() == "Linux":
        #     minutes_diff = date_diff.total_seconds() / 60
        # elif platform.system() == "Windows":
        #     minutes_diff = date_diff.total_seconds() / 60 - 60
        with open(path+game2, "r", encoding="utf_8") as f:
            txt = f.readlines()
            f.close()
        output += "**Top Game "+str(idx+1)+ ", Game Elo: " +txt[-1]+responses.get_ranked_emote(int(txt[-1]))+",  Started "+str(timestamp)+".**\n"
        for c, data in enumerate(txt):
            if c == len(txt)-1:
                output += "\n"
                break
            data = data.replace("\n", "")
            if c == (len(txt)-1)/2:
                output += "\n"
            output += data + responses.get_ranked_emote(int(data.split(":")[1]))+ " "
    return output

def run_discord_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.set_exception_handler(custom_exception_handler)
    TOKEN = secret_file.get('token')
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    tree = app_commands.CommandTree(client)

    TOKEN2 = secret_file.get('livegametoken')
    intents2 = discord.Intents.default()
    intents2.message_content = True
    client2 = discord.Client(intents=intents)

    @tree.command(name= "elo", description= "Shows rank, elo and playtime.")
    @app_commands.describe(playername='Enter the playername.')
    async def elo(interaction: discord.Interaction, playername: str):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(responses.apicall_elo, playername, 0))
                if len(response) > 0:
                    await interaction.followup.send(response)
            except Exception:
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

    @tree.command(name="bestie", description="Shows your bestie.")
    @app_commands.describe(playername='Enter the playername.')
    async def bestie(interaction: discord.Interaction, playername: str):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(responses.apicall_bestie, playername))
                if len(response) > 0:
                    await interaction.followup.send(response)
            except Exception:
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

    @tree.command(name="rank", description="Shows player info of a certain rank.")
    @app_commands.describe(rank='Enter a rank(number).')
    async def rank(interaction: discord.Interaction, rank: int):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(responses.apicall_rank, rank))
                if len(response) > 0:
                    await interaction.followup.send(response)
            except Exception:
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

    @tree.command(name="gamestats", description="Shows player stats.")
    @app_commands.describe(playername='Enter the playername.')
    async def gamestats(interaction: discord.Interaction, playername: str):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(responses.apicall_gamestats, playername))
                if len(response) > 0:
                    await interaction.followup.send(response)
            except Exception:
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

    @tree.command(name="gameid_viewer", description="Outputs image(s) of the gameid provided.")
    @app_commands.describe(game_id= "Enter the GameID.",wave='Enter a specific wave to output, or just 0 for an Album of every wave.')
    async def gameid_viewer(interaction: discord.Interaction, game_id: str, wave: int):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(responses.apicall_gameid_visualizer, game_id, wave))
                if len(response) > 0:
                    await interaction.followup.send(response)
            except Exception:
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

    @tree.command(name="novacup", description="Shows current teams in each novacup division 1 or 2.")
    @app_commands.describe(division='Enter division.')
    @app_commands.choices(division=[
        discord.app_commands.Choice(name='1', value='1'),
        discord.app_commands.Choice(name='2', value='2')
    ])
    async def novacup(interaction: discord.Interaction, division: discord.app_commands.Choice[str]):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(responses.novacup, division.value))
                if len(response) > 0:
                    await interaction.followup.send(response)
            except Exception:
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

    @tree.command(name="showlove", description="Shows how many games both players have played together.")
    @app_commands.describe(playername1='Enter playername 1.', playername2='Enter playername 2')
    async def showlove(interaction: discord.Interaction, playername1: str, playername2: str):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(responses.apicall_showlove, playername1, playername2))
                if len(response) > 0:
                    await interaction.followup.send(response)
            except Exception:
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

    @tree.command(name="wave1", description="Shows Wave 1 tendency.")
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
    async def wave1(interaction: discord.Interaction, playername: str, games: int, min_elo: int, patch: str, option: discord.app_commands.Choice[str], sort: discord.app_commands.Choice[str]):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(responses.apicall_wave1tendency, playername, option.value, games, min_elo, patch, sort.value))
                if len(response) > 0:
                    await interaction.followup.send(response)
            except Exception:
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

    @tree.command(name="elcringo", description="Shows how cringe someone is.")
    @app_commands.describe(playername='Enter playername or "all" for all available data.', games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.', min_elo='Enter minium average game elo to include in the data set',
                           option='Count small sends as save?', sort='Sort by?')
    @app_commands.choices(option=[
        discord.app_commands.Choice(name='Yes', value="Yes"),
        discord.app_commands.Choice(name='No', value="No")
    ])
    @app_commands.choices(sort=[
        discord.app_commands.Choice(name='date', value="date"),
        discord.app_commands.Choice(name='elo', value="elo")
    ])
    async def elcringo(interaction: discord.Interaction, playername: str, games: int, min_elo: int, patch: str, option: discord.app_commands.Choice[str], sort: discord.app_commands.Choice[str]):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool,functools.partial(responses.apicall_elcringo, playername, games, patch, min_elo, option, sort = sort.value))
                if len(response) > 0:
                    await interaction.followup.send(response)
            except Exception:
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

    @tree.command(name="mmstats", description="Mastermind stats.")
    @app_commands.describe(playername='Enter playername or "all" for all available data.', games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           min_elo='Enter minium average game elo to include in the data set',
                           patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.',
                           mastermind= 'Select a Mastermind for specific stats, or All for a general overview.', sort="Sort by?")
    @app_commands.choices(mastermind=[
        discord.app_commands.Choice(name='All', value="All"),
        discord.app_commands.Choice(name='Fiesta', value="Fiesta"),
        discord.app_commands.Choice(name='Megamind', value="Megamind"),
        discord.app_commands.Choice(name='Champion', value="Champion")
    ])
    @app_commands.choices(sort=[
        discord.app_commands.Choice(name='date', value="date"),
        discord.app_commands.Choice(name='elo', value="elo")
    ])
    async def mmstats(interaction: discord.Interaction, playername: str, games: int, min_elo: int, patch: str, mastermind: discord.app_commands.Choice[str], sort: discord.app_commands.Choice[str]):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool,functools.partial(responses.apicall_mmstats, str(playername).lower(), games, min_elo, patch, mastermind, sort = sort.value))
                if len(response) > 0:
                    await interaction.followup.send(response)
            except Exception:
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

    @tree.command(name="openstats", description="Opener stats.")
    @app_commands.describe(playername='Enter playername or "all" for all available data.',
                           games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           min_elo='Enter minium average game elo to include in the data set',
                           patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.',
                           sort="Sort by?", unit= "Unit name for specific stats, or 'all' for all openers.")
    @app_commands.choices(sort=[
        discord.app_commands.Choice(name='date', value="date"),
        discord.app_commands.Choice(name='elo', value="elo")
    ])
    async def openstats(interaction: discord.Interaction, playername: str, games: int = 0, min_elo: int = 0, patch: str = "0", sort: discord.app_commands.Choice[str] = "date", unit: str = "all"):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                sort = sort.value
            except AttributeError:
                pass
            try:
                response = await loop.run_in_executor(pool, functools.partial(responses.apicall_openstats, str(playername).lower(), games, min_elo, patch, sort = sort, unit= unit))
                if len(response) > 0:
                    await interaction.followup.send(response)
            except Exception:
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

    @tree.command(name="winrate", description="Shows player1's winrate against/with player2.")
    @app_commands.describe(playername1='Enter playername1.', playername2= 'Enter playername2 or all for 6 most common players', option='Against or with?', games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           min_elo='Enter minium average game elo to include in the data set', patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.',
                           sort= "Sort by? (Only for playername2 = all)")
    @app_commands.choices(option=[
        discord.app_commands.Choice(name='against', value='against'),
        discord.app_commands.Choice(name='with', value='with')
    ])
    @app_commands.choices(sort=[
        discord.app_commands.Choice(name='Count', value='Count'),
        discord.app_commands.Choice(name='EloChange+', value='EloChange+'),
        discord.app_commands.Choice(name='EloChange-', value='EloChange-')
    ])
    async def winrate(interaction: discord.Interaction, playername1: str, playername2: str, option: discord.app_commands.Choice[str], games: int=0, min_elo: int=0, patch: str="0", sort: discord.app_commands.Choice[str]="Count"):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                try: sort = sort.value
                except AttributeError: pass
                response = await loop.run_in_executor(pool, functools.partial(responses.apicall_winrate, playername1, playername2, option.value, games, patch, min_elo = min_elo, sort=sort))
                if len(response) > 0:
                    await interaction.followup.send(response)
            except Exception:
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

    @tree.command(name="elograph", description="Shows elo graph of player.")
    @app_commands.describe(playername='Enter playername.',
                           games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.')
    async def elo_graph(interaction: discord.Interaction, playername: str, games: int, patch: str):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(responses.apicall_elograph,playername, games, patch))
                if len(response) > 0:
                    await interaction.followup.send(response)
            except Exception:
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

    @tree.command(name="leaderboard", description="Shows current top 10 ranked leaderboard")
    async def leaderboard(interaction: discord.Interaction):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool,functools.partial(responses.apicall_leaderboard))
                if len(response) > 0:
                    await interaction.followup.send(response)
            except Exception:
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

    @tree.command(name="help", description="Gives some info on how to use all the commands.")
    async def help(interaction: discord.Interaction):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                await interaction.followup.send("Common Inputs:\n"
                                                "**'playername'**: Needs to be a playername currently in use, or 'all' to retrieve data from any player if the command supports it\n"
                                                "**'games'**: Any integer, or 0 to get all games available based on the other inputs.\n"
                                                "**'min_elo'**: Any integer, defines minimum avg game elo that a game needs to be included into the set of games.\n"
                                                "**'patch'**: Any patch in XX.XX format. Appending multiple patches with comas as delimiter is possible.\n"
                                                "           -Also using a '+' infront of a single patch, counts as any all the patches that come after(including the initial one, works only within the same season version.)\n"
                                                "           -Using a '-' between 2 patches takes the entire range from those patches.")
            except discord.NotFound as e:
                print(e)

    @tree.command(name="sendstats", description="Send stats.")
    @app_commands.describe(playername='Enter playername or "all" for all available data.',
                           starting_wave='Enter wave to show next sends when there was a send on that wave, or 0 for first sends after saving on Wave 1',
                           games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           min_elo='Enter minium average game elo to include in the data set',
                           patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.',
                           sort="Sort by?")
    @app_commands.choices(sort=[
        discord.app_commands.Choice(name='date', value="date"),
        discord.app_commands.Choice(name='elo', value="elo")
    ])
    async def sendstats(interaction: discord.Interaction, playername: str, starting_wave: int, games: int, min_elo: int, patch: str, sort: discord.app_commands.Choice[str]):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(responses.apicall_sendstats, str(playername).lower(), starting_wave, games, min_elo, patch, sort = sort.value))
                if len(response) > 0:
                    await interaction.followup.send(response)
            except Exception:
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

    @tree.command(name="topgames", description="Shows the 3 highest elo game in Ranked.")
    # @app_commands.describe(queue="Select a queue type.")
    # @app_commands.choices(queue=[
    #     discord.app_commands.Choice(name='Ranked', value='Ranked'),
    #     #discord.app_commands.Choice(name='Classic', value='Classic')
    # ])
    async def topgames(interaction: discord.Interaction):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(get_top_games, "Ranked"))
                if len(response) > 0:
                    await interaction.followup.send(response)
            except Exception:
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

    @tree.command(name="streamtracker", description="Simple W/L and Elo tracker for your stream.")
    # @app_commands.describe(action="Select an action.")
    # @app_commands.choices(action=[
    #     discord.app_commands.Choice(name='Start Session', value='Start'),
    #     discord.app_commands.Choice(name='End Session', value='End')
    # ])
    async def streamtracker(interaction: discord.Interaction): #, action: discord.app_commands.Choice[str] = "Start"
        try:
            if interaction.guild != None:
                await interaction.response.send_message("This command only works in DMs.", ephemeral=True)
                return
            with open("Files/whitelist.txt", "r") as f:
                data = f.readlines()
                for entry in data:
                    if interaction.user.name == entry.split("|")[0]:
                        playername = entry.split("|")[1].replace("\n", "")
                        break
                else:
                    await interaction.response.send_message("You are not whitelisted to be able to use this command. Message drachir_ to get access")
                    return
            # try:
            #     action = action.value
            # except AttributeError: pass
            # if action == "End":
            #     if os.path.isfile('/shared/' + playername + '_output.html'):
            #         os.remove('/shared/' + playername + '_output.html')
            #     if os.path.isfile("sessions/session_" + playername + ".json"):
            #         os.remove("sessions/session_" + playername + ".json")
            #         await interaction.response.send_message("Session ended.")
            #         return
            #     else:
            #         await interaction.response.send_message("No active session found.")
            #         return
            # elif action == "Start":
            await interaction.response.send_message("Use http://overlay.drachbot.site/"+playername+'_output.html as a OBS browser source.')
        except Exception:
            traceback.print_exc()
            await interaction.followup.send("Bot error :sob:")

    @client.event
    async def on_ready():
        print(f'{client.user} is now running!')

    @client2.event
    async def on_ready():
        # ranked_dir = "Livegame/Ranked/"
        # classic_dir = "Livegame/Classic/"
        # filelist_ranked = [f for f in os.listdir(ranked_dir) if f.endswith(".txt")]
        # filelist_classic = [f for f in os.listdir(classic_dir) if f.endswith(".txt")]
        # for f in filelist_ranked:
        #     os.remove(os.path.join(ranked_dir, f))
        # for f in filelist_classic:
        #     os.remove(os.path.join(classic_dir, f))
        # print("Livegame cache cleared.")
        print(f'{client2.user} is now running!')

    @client.event
    async def on_message(message):
        if '!' in message.content:
            if "!sync" == message.content and "drachir_" == str(message.author):
                print(await tree.sync(guild=None))
            username = str(message.author)
            user_message = str(message.content)
            channel = str(message.channel)
            print(f"{username} said: '{user_message}'({channel})")
        else: return

        if user_message[0] == '?':
            user_message = user_message[1:]
            await send_message(message, user_message, is_private=True)
        else:
            await send_message(message, user_message, False, username)

    @client2.event
    async def on_message(message):
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ProcessPoolExecutor() as pool:
                if str(message.channel) == "game-starts":
                    players = str(message.content).splitlines()[1:]
                    gameid = str(message.author).split("#")[0].replace("Game started! ", "")
                    if len(players) == 4:
                        players_new = await loop.run_in_executor(pool, functools.partial(get_game_elo, players, False))
                        save_live_game(gameid, players_new)
                        twitch_list = []
                        playernames_list = []
                        with open("Files/whitelist.txt", "r") as f:
                            data = f.readlines()
                            f.close()
                        for entry in data:
                            playername = entry.split("|")[1].replace("\n", "")
                            twitch_name = entry.split("|")[2].replace("\n", "")
                            for p in players:
                                if p.split(":")[0] == playername and os.path.isfile("sessions/session_" + playername + ".json") == False:
                                        twitch_list.append(twitch_name)
                                        playernames_list.append(playername)
                                elif p.split(":")[0] == playername and os.path.isfile("sessions/session_" + playername + ".json") == True:
                                    with open("sessions/session_" + playername + ".json", "r") as f2:
                                        temp_dict = json.load(f2)
                                        f2.close()
                                        twitch_dict = await twitch_get_streams([twitch_name])
                                        if str(temp_dict["started_at"]) != str(twitch_dict[twitch_name]["started_at"]):
                                            os.remove("sessions/session_" + playername + ".json")
                                            twitch_list.append(twitch_name)
                                            playernames_list.append(playername)
                        if len(twitch_list) > 0:
                            twitch_dict = await twitch_get_streams(twitch_list, playernames=playernames_list)
                            for streamer in twitch_dict:
                                if twitch_dict[streamer]["live"] == True:
                                    print(await loop.run_in_executor(pool,functools.partial(responses.stream_overlay,twitch_dict[streamer]["playername"], stream_started_at=str(twitch_dict[streamer]["started_at"])))+ " session started.")
                                else:
                                    print(streamer + " is not live.")
                    # elif len(players) == 8:
                    #     players_new = await loop.run_in_executor(pool, functools.partial(get_game_elo, players, True))
                    #     save_live_game(gameid, players_new)
                elif str(message.channel) == "game-results":
                    embeds = message.embeds
                    for embed in embeds:
                        embed_dict = embed.to_dict()
                    for field in embed_dict["fields"]:
                        if field["name"] == "Game ID":
                            gameid_result = field["value"]
                    desc = embed_dict["description"].split(")")[0].split("(")[1]
                    desc2 = embed_dict["description"].split("(")[0]
                    desc3 = embed_dict["description"].split("Markdown")
                    if "elo" in desc:
                        with open("Files/whitelist.txt", "r") as f:
                            data = f.readlines()
                            for entry in data:
                                playername = entry.split("|")[1].replace("\n", "")
                                if playername in desc3[1]:
                                    elo_change = int(desc3[0].split(" elo")[0].split("(")[1])
                                    if os.path.isfile("sessions/session_" + playername + ".json"):
                                        await loop.run_in_executor(pool, functools.partial(responses.stream_overlay, playername, elo_change=elo_change))
                                elif playername in desc3[2]:
                                    elo_change = int(desc3[1].split(" elo")[0].split("(")[-1])
                                    if os.path.isfile("sessions/session_" + playername + ".json"):
                                        await loop.run_in_executor(pool,functools.partial(responses.stream_overlay, playername,elo_change=elo_change))
                    if "elo" in desc or "**TIED**" in desc2:
                        path = 'Livegame/Ranked/'
                        livegame_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.txt')]
                        for game in livegame_files:
                            if game.split("_")[0] == gameid_result:
                                os.remove(path + game)
                    # else:
                    #     path = 'Livegame/Classic/'
                    #     livegame_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.txt')]
        except Exception:
            traceback.print_exc()
    
    loop.create_task(client.start(TOKEN))
    loop.create_task(client2.start(TOKEN2))
    loop.create_task(twitch_get_streams(["Lwon"]))
    loop.run_forever()

