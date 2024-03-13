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

with open('Files/Secrets.json') as f:
    secret_file = json.load(f)
serverid = secret_file.get('id')

async def send_message(message, user_message, is_private, username):
    #try:
    loop = asyncio.get_running_loop()
    with concurrent.futures.ProcessPoolExecutor() as pool:
        response = await loop.run_in_executor(pool, functools.partial(responses.handle_response, user_message, username))
        await message.author.send(response) if is_private else await message.channel.send(response)
    # except Exception as e:
    #     print(e)

def get_game_elo(playerlist):
    elo = 0
    for player in playerlist:
        elo += int(player.split(":")[1])
    return round(elo / len(playerlist))

def save_live_game(gameid, playerlist):
    if len(playerlist) == 5:
        with open("Livegame/Ranked/" + str(gameid)+"_"+str(playerlist[4])+".txt", "w", encoding="utf_8") as f:
            f.write('\n'.join(playerlist))
            f.close()
    else:
        with open("Livegame/Classic/" + str(gameid) + "_"+str(playerlist[8])+".txt", "w", encoding="utf_8") as f:
            f.write('\n'.join(playerlist))
            f.close()

def get_top_games(queue):
    if queue == "Ranked":
        path = "Livegame/Ranked/"
    else:
        path = "Livegame/Classic/"
    livegame_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.txt')]
    topgames = []
    for game in livegame_files:
        if len(topgames) < 3:
            topgames.append(game)
        else:
            for i, topgame in enumerate(topgames):
                if int(game.split("_")[1].split(".")[0]) > int(topgame.split("_")[1].split(".")[0]):
                    topgames[i] = game
                    break
    output = ""
    for idx, game2 in enumerate(topgames):
        path2 = path+game2
        mod_date = datetime.utcfromtimestamp(os.path.getmtime(path2))
        date_diff = datetime.now() - mod_date
        minutes_diff = date_diff.total_seconds() / 60 - 60
        with open(path+game2, "r", encoding="utf_8") as f:
            txt = f.readlines()
            f.close()
        output += "**Top Game "+str(idx+1)+ ", Game Elo: " +txt[-1]+",  Started "+str(round(minutes_diff))+" minute(s) ago.**\n"
        for c, data in enumerate(txt):
            if c == len(txt)-1:
                output += "\n"
                break
            data = data.replace("\n", "")
            if c == (len(txt)-1)/2:
                output += "\n"
            output += data + " "
    return output

def run_discord_bot():
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
            except discord.NotFound as e:
                print(e)

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
            except discord.NotFound as e:
                print(e)

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
            except discord.NotFound as e:
                print(e)

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
            except discord.NotFound as e:
                print(e)

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
            except discord.NotFound as e:
                print(e)

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
            except discord.NotFound as e:
                print(e)

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
            except discord.NotFound as e:
                print(e)

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
            except discord.NotFound as e:
                print(e)
            except IndexError as e:
                print(e)
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
            except discord.NotFound as e:
                print(e)
            except IndexError as e:
                print(e)
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
            except discord.NotFound as e:
                print(e)
            except IndexError as e:
                print(e)
                await interaction.followup.send("Bot error :sob:")

    @tree.command(name="openstats", description="Opener stats.")
    @app_commands.describe(playername='Enter playername or "all" for all available data.',
                           games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           min_elo='Enter minium average game elo to include in the data set',
                           patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.',
                           sort="Sort by?")
    @app_commands.choices(sort=[
        discord.app_commands.Choice(name='date', value="date"),
        discord.app_commands.Choice(name='elo', value="elo")
    ])
    async def openstats(interaction: discord.Interaction, playername: str, games: int, min_elo: int, patch: str, sort: discord.app_commands.Choice[str]):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(responses.apicall_openstats, str(playername).lower(), games, min_elo, patch, sort = sort.value))
                if len(response) > 0:
                    await interaction.followup.send(response)
            except discord.NotFound as e:
                print(e)
            except IndexError as e:
                print(e)
                await interaction.followup.send("Bot error :sob:")

    @tree.command(name="winrate", description="Shows player1's winrate against/with player2.")
    @app_commands.describe(playername1='Enter playername1.', playername2= 'Enter playername2 or all for 6 most common players', option='Against or with?', games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           min_elo='Enter minium average game elo to include in the data set', patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.')
    @app_commands.choices(option=[
        discord.app_commands.Choice(name='against', value='against'),
        discord.app_commands.Choice(name='with', value='with')
    ])
    async def winrate(interaction: discord.Interaction, playername1: str, playername2: str, option: discord.app_commands.Choice[str], games: int, min_elo: int, patch: str):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(responses.apicall_winrate, playername1, playername2, option.value, games, patch, min_elo = min_elo))
                if len(response) > 0:
                    await interaction.followup.send(response)
            except discord.NotFound as e:
                print(e)
            except IndexError as e:
                print(e)
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
            except discord.NotFound as e:
                print(e)
            except IndexError as e:
                print(e)
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
            except discord.NotFound as e:
                print(e)
            except IndexError as e:
                print(e)
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
            except discord.NotFound as e:
                print(e)
            except IndexError as e:
                print(e)
                await interaction.followup.send("Bot error :sob:")

    @tree.command(name="topgames", description="Shows the 3 highest elo game in Ranked or Classic.")
    @app_commands.describe(queue="Select a queue type.")
    @app_commands.choices(queue=[
        discord.app_commands.Choice(name='Ranked', value='Ranked'),
        discord.app_commands.Choice(name='Classic', value='Classic')
    ])
    async def topgames(interaction: discord.Interaction, queue: discord.app_commands.Choice[str]):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(get_top_games, queue.value))
                if len(response) > 0:
                    await interaction.followup.send(response)
            except discord.NotFound as e:
                print(e)
            except Exception:
                traceback.print_exc()
            except IndexError as e:
                print(e)
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
            if str(message.channel) == "game-starts":
                players = str(message.content).splitlines()[1:]
                gameid = str(message.author).split("#")[0].replace("Game started! ", "")
                if len(players) == 4:
                    gameelo = get_game_elo(players)
                    players.append(str(gameelo))
                    save_live_game(gameid, players)
                elif len(players) == 8:
                    gameelo = get_game_elo(players)
                    players.append(str(gameelo))
                    save_live_game(gameid, players)
            elif str(message.channel) == "game-results":
                embeds = message.embeds
                for embed in embeds:
                    embed_dict = embed.to_dict()
                for field in embed_dict["fields"]:
                    if field["name"] == "Game ID":
                        gameid_result = field["value"]
                desc = embed_dict["description"].split(")")[0].split("(")[1]
                if "elo" in desc:
                    path = 'Livegame/Ranked/'
                    livegame_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.txt')]
                else:
                    path = 'Livegame/Classic/'
                    livegame_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.txt')]
                for game in livegame_files:
                    if game.split("_")[0] == gameid_result:
                        print("Game finished. (" + str(gameid_result) + ")")
                        os.remove(path+game)
        except Exception:
            traceback.print_exc()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(client.start(TOKEN))
    loop.create_task(client2.start(TOKEN2))
    loop.run_forever()

