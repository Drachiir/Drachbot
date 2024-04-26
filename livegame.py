import asyncio
import concurrent.futures
import functools
import json
import os
import platform
from datetime import datetime
import cogs.streamtracker
from twitchAPI.helper import first
from twitchAPI.twitch import Twitch

with open('Files/json/Secrets.json') as f:
    secret_file = json.load(f)
    f.close()

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
                            else:
                                mod_date = datetime.utcfromtimestamp(os.path.getmtime("sessions/session_" + playername + ".json"))
                                date_diff = datetime.now() - mod_date
                                if platform.system() == "Linux":
                                    minutes_diff = date_diff.total_seconds() / 60
                                elif platform.system() == "Windows":
                                    minutes_diff = date_diff.total_seconds() / 60 - 60
                                if minutes_diff > 10:
                                    loop = asyncio.get_running_loop()
                                    with concurrent.futures.ThreadPoolExecutor() as pool:
                                        await loop.run_in_executor(pool, functools.partial(cogs.streamtracker.stream_overlay, playername, update=True))
                                        pool.shutdown()
            if len(twitch_list) > 0:
                twitch_dict = await twitch_get_streams(twitch_list, playernames=playernames_list)
                for streamer in twitch_dict:
                    if twitch_dict[streamer]["live"] == True:
                        loop = asyncio.get_running_loop()
                        with concurrent.futures.ThreadPoolExecutor() as pool:
                            print(await loop.run_in_executor(pool, functools.partial(cogs.streamtracker.stream_overlay, twitch_dict[streamer]["playername"], stream_started_at=str(twitch_dict[streamer]["started_at"]))) + " session started.")
                            pool.shutdown()
                    else:
                        print(streamer + " is not live.")
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
                            loop = asyncio.get_running_loop()
                            with concurrent.futures.ProcessPoolExecutor() as pool:
                                await loop.run_in_executor(pool, functools.partial(cogs.streamtracker.stream_overlay, playername, elo_change=elo_change))
                                pool.shutdown()
                    elif playername in desc3[2]:
                        elo_change = int(desc3[1].split(" elo")[0].split("(")[-1])
                        if os.path.isfile("sessions/session_" + playername + ".json"):
                            loop = asyncio.get_running_loop()
                            with concurrent.futures.ProcessPoolExecutor() as pool:
                                await loop.run_in_executor(pool, functools.partial(cogs.streamtracker.stream_overlay, playername, elo_change=elo_change))
                                pool.shutdown()
        if "elo" in desc or "**TIED**" in desc2:
            path = 'Livegame/Ranked/'
            livegame_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.txt')]
            for game in livegame_files:
                if game.split("_")[0] == gameid_result:
                    os.remove(path + game)
                    