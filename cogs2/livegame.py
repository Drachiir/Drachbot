import asyncio
import concurrent.futures
import functools
import json
import os
import platform
import time
import traceback
from datetime import datetime
from discord.ext import commands
import legion_api
from streamoverlay import stream_overlay
import util

with open('Files/json/Secrets.json') as f:
    secret_file = json.load(f)
    f.close()

def save_live_game(gameid, playerlist):
    if len(playerlist) == 5:
        with open(util.shared_folder_livegames + str(gameid) + "_" + str(playerlist[4]) + ".txt", "w", encoding="utf_8") as f:
            f.write('\n'.join(playerlist))
            f.close()
    elif len(playerlist) == 3:
        with open(util.shared_folder_livegames1v1 + str(gameid) + "_" + str(playerlist[2]) + ".txt", "w", encoding="utf_8") as f:
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


def handler(message) -> None:
    if str(message.channel) == "game-starts":
        players = str(message.content).splitlines()[1:]
        gameid = str(message.author).split("#")[0].replace("Game started! ", "")
        if len(players) == 4 or len(players) == 2:
            players_new = get_game_elo(players)
            save_live_game(gameid, players_new)
            with open("Files/streamers.json", "r") as f:
                data = json.load(f)
            for entry in data:
                accounts = data[entry]["player_ids"]
                for i, acc in enumerate(accounts):
                    player_name = data[entry]["display_names"][i]
                    for p in players:
                        if p.split(":")[0] == player_name and os.path.isfile(f"sessions/session_{acc}.json"):
                            mod_date = datetime.utcfromtimestamp(os.path.getmtime(f'sessions/session_{acc}.json'))
                            date_diff = datetime.now() - mod_date
                            minutes_diff = date_diff.total_seconds() / 60
                            if minutes_diff > 2:
                                with open(f"sessions/session_{acc}.json", "r") as f:
                                    session = json.load(f)
                                if session["live"]:
                                    with concurrent.futures.ProcessPoolExecutor() as pool:
                                        pool.submit(functools.partial(stream_overlay, acc, True))
    elif str(message.channel) == "game-results":
        gameid_result = ""
        embeds = message.embeds
        for embed in embeds:
            embed_dict = embed.to_dict()
        for field in embed_dict["fields"]:
            if field["name"] == "Game ID":
                gameid_result = field["value"]
                break
        desc = embed_dict["description"].split(")")[0].split("(")[1]
        desc2 = embed_dict["description"].split("(")[0]
        desc3 = embed_dict["description"].split("Markdown")
        if "elo" in desc or "**TIED**" in desc2 or "Practice" in desc:
            path = util.shared_folder_livegames
            path2 = util.shared_folder_livegames1v1
            livegame_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.txt')]
            for game in livegame_files:
                if game.split("_")[0] == gameid_result:
                    os.remove(path + game)
            # Dirty copy for 1v1
            livegame_files1v1 = [pos_json for pos_json in os.listdir(path2) if pos_json.endswith('.txt')]
            for game in livegame_files1v1:
                if game.split("_")[0] == gameid_result:
                    os.remove(path2 + game)
        if "elo" in desc:
            with open("Files/streamers.json", "r") as f:
                data = json.load(f)
            for entry in data:
                accounts = data[entry]["player_ids"]
                for i, acc in enumerate(accounts):
                    player_name = data[entry]["display_names"][i]
                    if player_name in desc3[1]:
                        elo_change = int(desc3[0].split(" elo")[0].split("(")[1])
                        if os.path.isfile(f"sessions/session_{acc}.json"):
                            with open(f"sessions/session_{acc}.json", "r") as f:
                                session = json.load(f)
                            if session["live"]:
                                with concurrent.futures.ProcessPoolExecutor() as pool:
                                    pool.submit(functools.partial(stream_overlay, acc, elo_change=elo_change))
                                time.sleep(16)
                                with concurrent.futures.ProcessPoolExecutor() as pool:
                                    pool.submit(functools.partial(stream_overlay, acc, update=True, new_game=True))
                    elif player_name in desc3[2]:
                        elo_change = int(desc3[1].split(" elo")[0].split("(")[-1])
                        if os.path.isfile(f"sessions/session_{acc}.json"):
                            with open(f"sessions/session_{acc}.json", "r") as f:
                                session = json.load(f)
                            if session["live"]:
                                with concurrent.futures.ProcessPoolExecutor() as pool:
                                    pool.submit(functools.partial(stream_overlay, acc, elo_change=elo_change))
                                time.sleep(16)
                                with concurrent.futures.ProcessPoolExecutor() as pool:
                                    pool.submit(functools.partial(stream_overlay, acc, update=True, new_game=True))

class Livegame(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.pool = concurrent.futures.ThreadPoolExecutor(max_workers=100)

    @commands.Cog.listener()
    async def on_message(self, message):
        if str(message.channel) in ["game-starts", "game-results"]:
            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(self.pool, handler, message)
            except Exception:
                traceback.print_exc()

    def cog_unload(self):
        self.pool.shutdown(wait=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Livegame(bot))