import asyncio
import concurrent.futures
import difflib
import functools
import json
import os
import os.path
import traceback
from io import BytesIO
import discord
import requests
from PIL import Image, ImageSequence
from discord import app_commands
from discord.ext import commands
import legion_api


def get_emote(emote_name):
    seventvapi = "https://7tv.io/v3/emote-sets/65a6d017888d90ac522693b8"
    response = json.loads(requests.get(seventvapi).text)
    for emote in response["emotes"]:
        if emote["data"]["name"] == emote_name:
            image_response = requests.get("https:"+emote["data"]["host"]["url"]+"/4x.webp")
            im = Image.open(BytesIO(image_response.content))
            im.info.pop('background', None)
            #if not os.path.isfile('/shared/emotes/'+emote["data"]["name"]+'.gif'):
            try:
                frame = ImageSequence.Iterator(im)[1]
                im.save('/shared/emotes/'+emote["data"]["name"]+'.gif', 'gif', save_all=True, disposal=2)
                return discord.File('/shared/emotes/'+emote["data"]["name"]+'.gif')
            except IndexError:
                im.save('/shared/emotes/' + emote["data"]["name"] + '.webp', 'webp', save_all=True)
                return discord.File('/shared/emotes/' + emote["data"]["name"] + '.webp')
    for emote in response["emotes"]:
        if emote["data"]["name"].casefold() == emote_name.casefold():
            image_response = requests.get("https:"+emote["data"]["host"]["url"]+"/4x.webp")
            im = Image.open(BytesIO(image_response.content))
            im.info.pop('background', None)
            #if not os.path.isfile('/shared/emotes/'+emote["data"]["name"]+'.gif'):
            try:
                frame = ImageSequence.Iterator(im)[1]
                im.save('/shared/emotes/' + emote["data"]["name"] + '.gif', 'gif', save_all=True, disposal=2)
                return discord.File('/shared/emotes/' + emote["data"]["name"] + '.gif')
            except IndexError:
                im.save('/shared/emotes/' + emote["data"]["name"] + '.webp', 'webp', save_all=True)
                return discord.File('/shared/emotes/' + emote["data"]["name"] + '.webp')
    else:
        emote_list = os.listdir("/shared/emotes")
        close_matches = difflib.get_close_matches(emote_name, emote_list, cutoff=0.3)
        if close_matches:
            if not close_matches[0].endswith(".gif"):
                im = Image.open("/shared/emotes/"+close_matches[0])
                im.resize((150, 150)).save("/shared/emotes/"+close_matches[0])
            return discord.File('/shared/emotes/'+close_matches[0])
        else:
            return "Emote not found."

def bestie(playername):
    playerid = legion_api.getid(playername)
    if playerid == 0:
        return 'Player ' + str(playername) + ' not found.'
    if playerid == 1:
        return 'API limit reached.'
    else:
        request_type = 'players/bestFriends/' + playerid
        url = 'https://apiv2.legiontd2.com/' + request_type + '?limit=1&offset=0'
        api_response = requests.get(url, headers=legion_api.header)
        bestie = json.loads(api_response.text)
        if not bestie:
            return 'no bestie :sob: (No data)'
        else:
            for bestie_new in bestie[0].values():
                print(bestie_new['playerName'])
                bestie_name = bestie_new['playerName']
                break
            print(bestie[0]['count'])

            return str(playername).capitalize() + "'s bestie is " + bestie_name + ' :heart: with ' + str(
                bestie[0]['count']) + ' games together.'

def showlove(playername, playername2):
    playerid = legion_api.getid(playername)
    print(playername)
    print(playername2)
    if playerid == 0:
        return 'Player ' + str(playername) + ' not found.'
    if playerid == 1:
        return 'API limit reached.'
    request_type = 'players/bestFriends/' + playerid
    url = 'https://apiv2.legiontd2.com/' + request_type + '?limit=50&offset=0'
    api_response = requests.get(url, headers=legion_api.header)
    bestie = json.loads(api_response.text)
    count = 0
    nextvaluesave = 0
    while count < len(bestie):
        for bestie_new in bestie[count].values():
            if isinstance(bestie_new, dict):
                name = bestie_new['playerName']
                if str(name).lower() == str(playername2).lower():
                    print('found target')
                    nextvaluesave = 1
                count = count + 1
            else:
                if nextvaluesave == 1:
                    love_count = bestie_new
                    print(love_count)
                    return playername.capitalize() + ' has played ' + str(
                        love_count) + ' games with ' + playername2.capitalize() + ' :heart:'
    return 'Not enough games played together'

class ForFun(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    @app_commands.command(name="emote", description="Shows a emote.")
    @app_commands.describe(emotename='Enter emote name.')
    async def emote(self, interaction: discord.Interaction, emotename: str):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(get_emote, emotename))
                pool.shutdown()
                if type(response) != str:
                    await interaction.followup.send(file=response)
                else:
                    await interaction.followup.send(response)
            except Exception:
                print("/" + interaction.command.name + " failed. args: " + str(interaction.data.values()))
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")
    
    @app_commands.command(name="bestie", description="Shows your bestie.")
    @app_commands.describe(playername='Enter the playername.')
    async def bestie(self, interaction: discord.Interaction, playername: str):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(bestie, playername))
                pool.shutdown()
                if len(response) > 0:
                    await interaction.followup.send(response)
            except Exception:
                print("/" + interaction.command.name + " failed. args: " + str(interaction.data.values()))
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")
    
    @app_commands.command(name="showlove", description="Shows how many games both players have played together.")
    @app_commands.describe(playername1='Enter playername 1.', playername2='Enter playername 2')
    async def showlove(self, interaction: discord.Interaction, playername1: str, playername2: str):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(showlove, playername1, playername2))
                pool.shutdown()
                if len(response) > 0:
                    await interaction.followup.send(response)
            except Exception:
                print("/" + interaction.command.name + " failed. args: " + str(interaction.data.values()))
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

async def setup(bot:commands.Bot):
    await bot.add_cog(ForFun(bot))
    