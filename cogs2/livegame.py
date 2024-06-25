import asyncio
import concurrent.futures
import functools
import json
import os
import platform
import traceback
from datetime import datetime
from discord.ext import commands
import legion_api
import cogs.streamtracker

with open('Files/json/Secrets.json') as f:
    secret_file = json.load(f)
    f.close()

def save_live_game(gameid, playerlist):
    if len(playerlist) == 5:
        with open("Livegame/Ranked/" + str(gameid) + "_" + str(playerlist[4]) + ".txt", "w", encoding="utf_8") as f:
            f.write('\n'.join(playerlist))
            f.close()

def get_game_elo(playerlist):
    elo = 0
    new_list = []
    for player in playerlist:
        ranked_elo = int(player.split(":")[1])
        new_list.append(player.split(":")[0] + ":" + str(ranked_elo))
        elo += ranked_elo
    new_list.append(str(round(elo / len(playerlist))))
    return new_list

async def handler(message) -> None:
    if str(message.channel) == "game-starts":
        players = str(message.content).splitlines()[1:]
        gameid = str(message.author).split("#")[0].replace("Game started! ", "")
        if len(players) == 4:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                players_new = await loop.run_in_executor(pool, functools.partial(get_game_elo, players))
                pool.shutdown()
            save_live_game(gameid, players_new)
            with open("Files/whitelist.txt", "r") as f:
                data = f.readlines()
                f.close()
            for entry in data:
                playername = entry.split("|")[1].replace("\n", "")
                if "," in playername:
                    accounts = playername.split(",")
                else:
                    accounts = [playername]
                for acc in accounts:
                    for p in players:
                        if p.split(":")[0] == acc and os.path.isfile("sessions/session_" + acc + ".json") == True:
                            with open("sessions/session_" + acc + ".json", "r") as f:
                                session = json.load(f)
                                f.close()
                            if session["live"]:
                                loop = asyncio.get_running_loop()
                                with concurrent.futures.ThreadPoolExecutor() as pool:
                                    await loop.run_in_executor(pool, functools.partial(cogs.streamtracker.stream_overlay, acc, update=True))
                                    pool.shutdown()
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
                    if "," in playername:
                        accounts = playername.split(",")
                    else:
                        accounts = [playername]
                    for acc in accounts:
                        if acc in desc3[1]:
                            elo_change = int(desc3[0].split(" elo")[0].split("(")[1])
                            if os.path.isfile("sessions/session_" + acc + ".json"):
                                with open("sessions/session_" + acc + ".json", "r") as f:
                                    session = json.load(f)
                                    f.close()
                                if session["live"]:
                                    loop = asyncio.get_running_loop()
                                    with concurrent.futures.ThreadPoolExecutor() as pool:
                                        await loop.run_in_executor(pool, functools.partial(cogs.streamtracker.stream_overlay, acc, elo_change=elo_change))
                                        pool.shutdown()
                        elif acc in desc3[2]:
                            elo_change = int(desc3[1].split(" elo")[0].split("(")[-1])
                            if os.path.isfile("sessions/session_" + acc + ".json"):
                                with open("sessions/session_" + acc + ".json", "r") as f:
                                    session = json.load(f)
                                    f.close()
                                if session["live"]:
                                    loop = asyncio.get_running_loop()
                                    with concurrent.futures.ThreadPoolExecutor() as pool:
                                        await loop.run_in_executor(pool, functools.partial(cogs.streamtracker.stream_overlay, acc, elo_change=elo_change))
                                        pool.shutdown()
        if "elo" in desc or "**TIED**" in desc2:
            path = 'Livegame/Ranked/'
            livegame_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.txt')]
            for game in livegame_files:
                if game.split("_")[0] == gameid_result:
                    os.remove(path + game)

class Livegame(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
                
    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            await handler(message)
        except Exception:
            traceback.print_exc()

async def setup(bot:commands.Bot):
    await bot.add_cog(Livegame(bot))