import asyncio
import json
import discord
import responses
from discord import app_commands

with open('Secrets.json') as f:
    secret_file = json.load(f)
serverid = secret_file.get('id')

async def send_message(message, user_message, is_private):
    try:
        response = responses.handle_response(user_message)
        await message.author.send(response) if is_private else await message.channel.send(response)

    except Exception as e:
        print(e)


def run_discord_bot():
    TOKEN = secret_file.get('token')
    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)
    tree = app_commands.CommandTree(client)

    @tree.command(name= "elo", description= "Shows rank, elo and playtime.", guild=discord.Object(id=serverid))
    @app_commands.describe(playername='Enter the playername.')
    async def elo(interaction: discord.Interaction, playername: str):
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.apicall_elo(playername, 0)
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
        except discord.NotFound as e:
            print(e)

    @tree.command(name="bestie", description="Shows your bestie.", guild=discord.Object(id=serverid))
    @app_commands.describe(playername='Enter the playername.')
    async def bestie(interaction: discord.Interaction, playername: str):
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.apicall_bestie(playername)
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
        except discord.NotFound as e:
            print(e)

    @tree.command(name="rank", description="Shows player info of a certain rank.", guild=discord.Object(id=serverid))
    @app_commands.describe(rank='Enter a rank(number).')
    async def rank(interaction: discord.Interaction, rank: int):
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.apicall_rank(rank)
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
        except discord.NotFound as e:
            print(e)

    @tree.command(name="gamestats", description="Shows player stats.", guild=discord.Object(id=serverid))
    @app_commands.describe(playername='Enter the playername.')
    async def gamestats(interaction: discord.Interaction, playername: str):
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.apicall_gamestats(playername)
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
        except discord.NotFound as e:
            print(e)

    @tree.command(name="showlove", description="Shows how many games both players have played together.", guild=discord.Object(id=serverid))
    @app_commands.describe(playername1='Enter playername 1.', playername2='Enter playername 2')
    async def showlove(interaction: discord.Interaction, playername1: str, playername2: str):
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.apicall_showlove(playername1, playername2)
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
        except discord.NotFound as e:
            print(e)

    @tree.command(name="wave1", description="Shows Wave 1 tendency",
                  guild=discord.Object(id=serverid))
    @app_commands.describe(playername='Enter playername.', option='Send or received?')
    @app_commands.choices(option=[
        discord.app_commands.Choice(name='send', value=0),
        discord.app_commands.Choice(name='received', value=1)
    ])
    async def wave1(interaction: discord.Interaction, playername: str, option: discord.app_commands.Choice[int]):
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.apicall_wave1tendency(playername, option.value)
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
        except discord.NotFound as e:
            print(e)
        except IndexError as e:
            print(e)
            await interaction.edit_original_response(content='Bot error. :sob:')


    @tree.command(name="elcringo", description="Shows how cringe someone is.",
                  guild=discord.Object(id=serverid))
    @app_commands.describe(playername='Enter playername.')
    async def elcringo(interaction: discord.Interaction, playername: str):
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.apicall_elcringo(playername)
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
        except discord.NotFound as e:
            print(e)
        except IndexError as e:
            print(e)
            await interaction.edit_original_response(content='Bot error. :sob:')

    @tree.command(name="mmstats", description="Mastermind stats.",
                  guild=discord.Object(id=serverid))
    @app_commands.describe(playername='Enter playername or "all" for all available data.')
    @app_commands.choices(page=[
        discord.app_commands.Choice(name='1', value=1),
        discord.app_commands.Choice(name='2', value=2),
        discord.app_commands.Choice(name='redraw', value=3)
    ])
    async def mmstats(interaction: discord.Interaction, playername: str, page: discord.app_commands.Choice[int]):
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.apicall_mmstats(str(playername).lower(), page.value)
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
        except discord.NotFound as e:
            print(e)
        # except IndexError as e:
        #     print(e)
        #     await interaction.edit_original_response(content='Bot error. :sob:')

    @tree.command(name="winrate", description="Shows player1's winrate against/with player2",
                  guild=discord.Object(id=serverid))
    @app_commands.describe(playername1='Enter playername1.', playername2= 'Enter playername2 or all for 6 most common players', option='Against or with?')
    @app_commands.choices(option=[
        discord.app_commands.Choice(name='against', value=0),
        discord.app_commands.Choice(name='with', value=1)
    ])
    async def winrate(interaction: discord.Interaction, playername1: str, playername2: str, option: discord.app_commands.Choice[int]):
        await interaction.response.send_message('Thinking... :robot:')
        try:
            response = responses.apicall_winrate(playername1, playername2, option.value)
            if len(response) > 0:
                await interaction.edit_original_response(content=response)
        except discord.NotFound as e:
            print(e)
        except IndexError as e:
            print(e)
            await interaction.edit_original_response(content='Bot error. :sob:')

    @client.event
    async def on_ready():
        await tree.sync(guild=discord.Object(id=serverid))
        print(f'{client.user} is now running!')

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return
        if '!' in message.content:
            username = str(message.author)
            user_message = str(message.content)
            channel = str(message.channel)

            print(f"{username} said: '{user_message}'({channel})")
        else: return

        if user_message[0] == '?':
            user_message = user_message[1:]
            await send_message(message, user_message, is_private=True)
        else:
            await send_message(message, user_message, is_private=False)

    client.run(TOKEN)

