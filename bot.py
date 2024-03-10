import asyncio
import json
import discord
import responses
from discord import app_commands

with open('Files/Secrets.json') as f:
    secret_file = json.load(f)
serverid = secret_file.get('id')


async def send_message(message, user_message, is_private, username):
    #try:
    response = responses.handle_response(user_message, username)
    await message.author.send(response) if is_private else await message.channel.send(response)
    # except Exception as e:
    #     print(e)

def run_discord_bot():
    TOKEN = secret_file.get('token')
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    tree = app_commands.CommandTree(client)

    @tree.command(name= "elo", description= "Shows rank, elo and playtime.")
    @app_commands.describe(playername='Enter the playername.')
    async def elo(interaction: discord.Interaction, playername: str):
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.apicall_elo(playername, 0)
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
        except discord.NotFound as e:
            print(e)

    @tree.command(name="bestie", description="Shows your bestie.")
    @app_commands.describe(playername='Enter the playername.')
    async def bestie(interaction: discord.Interaction, playername: str):
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.apicall_bestie(playername)
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
        except discord.NotFound as e:
            print(e)

    @tree.command(name="rank", description="Shows player info of a certain rank.")
    @app_commands.describe(rank='Enter a rank(number).')
    async def rank(interaction: discord.Interaction, rank: int):
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.apicall_rank(rank)
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
        except discord.NotFound as e:
            print(e)

    @tree.command(name="gamestats", description="Shows player stats.")
    @app_commands.describe(playername='Enter the playername.')
    async def gamestats(interaction: discord.Interaction, playername: str):
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.apicall_gamestats(playername)
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
        except discord.NotFound as e:
            print(e)

    @tree.command(name="gameid_viewer", description="Outputs image(s) of the gameid provided.")
    @app_commands.describe(game_id= "Enter the GameID.",wave='Enter a specific wave to output, or just 0 for an Album of every wave.')
    async def gameid_viewer(interaction: discord.Interaction, game_id: str, wave: int):
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.apicall_gameid_visualizer(game_id, wave)
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
        except discord.NotFound as e:
            print(e)

    @tree.command(name="novacup", description="Shows current teams in each novacup division 1 or 2.")
    @app_commands.describe(division='Enter division.')
    @app_commands.choices(division=[
        discord.app_commands.Choice(name='1', value='1'),
        discord.app_commands.Choice(name='2', value='2')
    ])
    async def gamestats(interaction: discord.Interaction, division: discord.app_commands.Choice[str]):
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.novacup(division.value)
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
        except discord.NotFound as e:
            print(e)

    @tree.command(name="showlove", description="Shows how many games both players have played together.")
    @app_commands.describe(playername1='Enter playername 1.', playername2='Enter playername 2')
    async def showlove(interaction: discord.Interaction, playername1: str, playername2: str):
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.apicall_showlove(playername1, playername2)
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
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
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.apicall_wave1tendency(playername, option.value, games, min_elo, patch, sort=sort.value)
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
        except discord.NotFound as e:
            print(e)
        except IndexError as e:
            print(e)
            await interaction.edit_original_response(content='Bot error. :sob:')


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
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.apicall_elcringo(playername, games, patch, min_elo, option, sort=sort.value)
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
        except discord.NotFound as e:
            print(e)
        except IndexError as e:
            print(e)
            await interaction.edit_original_response(content='Bot error. :sob:')

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
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.apicall_mmstats(str(playername).lower(), games, min_elo, patch, mastermind, sort=sort.value)
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
        except discord.NotFound as e:
            print(e)
        except IndexError as e:
            print(e)
            await interaction.edit_original_response(content='Bot error. :sob:')

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
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.apicall_openstats(str(playername).lower(), games, min_elo, patch, sort=sort.value)
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
        except discord.NotFound as e:
            print(e)
        except IndexError as e:
            print(e)
            await interaction.edit_original_response(content='Bot error. :sob:')

    @tree.command(name="winrate", description="Shows player1's winrate against/with player2.")
    @app_commands.describe(playername1='Enter playername1.', playername2= 'Enter playername2 or all for 6 most common players', option='Against or with?', games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           min_elo='Enter minium average game elo to include in the data set', patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.')
    @app_commands.choices(option=[
        discord.app_commands.Choice(name='against', value='against'),
        discord.app_commands.Choice(name='with', value='with')
    ])
    async def winrate(interaction: discord.Interaction, playername1: str, playername2: str, option: discord.app_commands.Choice[str], games: int, min_elo: int, patch: str):
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.apicall_winrate(playername1, playername2, option.value, games, patch, min_elo=min_elo)
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
        except discord.NotFound as e:
            print(e)
        except IndexError as e:
            print(e)
            await interaction.edit_original_response(content='Bot error. :sob:')

    @tree.command(name="elograph", description="Shows elo graph of player.")
    @app_commands.describe(playername='Enter playername.',
                           games='Enter amount of games or "0" for all available games on the DB(Default = 200 when no DB entry yet.)',
                           patch='Enter patch e.g 10.01, multiple patches e.g 10.01,10.02,10.03.. or just "0" to include any patch.')
    async def elo_graph(interaction: discord.Interaction, playername: str, games: int, patch: str):
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.apicall_elograph(playername, games, patch)
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
        except discord.NotFound as e:
            print(e)
        except IndexError as e:
            print(e)
            await interaction.edit_original_response(content='Bot error. :sob:')

    @tree.command(name="leaderboard", description="Shows current top 10 ranked leaderboard")
    async def leaderboard(interaction: discord.Interaction):
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.apicall_leaderboard()
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
        except discord.NotFound as e:
            print(e)
        except IndexError as e:
            print(e)
            await interaction.edit_original_response(content='Bot error. :sob:')

    @tree.command(name="help", description="Gives some info on how to use all the commands.")
    async def help(interaction: discord.Interaction):
        try:
            await interaction.response.send_message('todo')
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
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.apicall_sendstats(str(playername).lower(), starting_wave, games, min_elo, patch, sort=sort.value)
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
        except discord.NotFound as e:
            print(e)
        except IndexError as e:
            print(e)
            await interaction.edit_original_response(content='Bot error. :sob:')

    @client.event
    async def on_ready():
        print(f'{client.user} is now running!')

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

    client.run(TOKEN)

