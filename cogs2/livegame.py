import asyncio
import concurrent.futures
import functools
import json
import os
import platform
import traceback
from datetime import datetime
from discord.ext import commands
from twitchAPI.helper import first
from twitchAPI.twitch import Twitch
import legion_api

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

def stream_overlay(playername, stream_started_at="", elo_change=0, update = False):
    if not os.path.isfile("sessions/session_" + playername + ".json"):
        playerid = legion_api.getid(playername)
        stats = legion_api.getstats(playerid)
        initial_elo = stats["overallElo"]
        current_elo = stats["overallElo"]
        initial_wins = stats["rankedWinsThisSeason"]
        current_wins = stats["rankedWinsThisSeason"]
        initial_losses = stats["rankedLossesThisSeason"]
        current_losses = stats["rankedLossesThisSeason"]
        with open("sessions/session_" + playername + ".json", "w") as f:
            session_dict = {"started_at": stream_started_at, "int_elo": initial_elo, "current_elo": current_elo, "int_wins": initial_wins, "current_wins": current_wins, "int_losses": initial_losses, "current_losses": current_losses}
            json.dump(session_dict, f, default=str)
    else:
        with open("sessions/session_" + playername + ".json", "r") as f:
            session_dict = json.load(f)
            initial_elo = session_dict["int_elo"]
            initial_wins = session_dict["int_wins"]
            initial_losses = session_dict["int_losses"]
            if update:
                playerid = legion_api.getid(playername)
                stats = legion_api.getstats(playerid)
                current_elo = stats["overallElo"]
                current_wins = stats["rankedWinsThisSeason"]
                current_losses = stats["rankedLossesThisSeason"]
            else:
                current_elo = session_dict["current_elo"] + elo_change
                if elo_change > 0:
                    current_wins = session_dict["current_wins"] + 1
                else:
                    current_wins = session_dict["current_wins"]
                if elo_change < 0:
                    current_losses = session_dict["current_losses"] + 1
                else:
                    current_losses = session_dict["current_losses"]
        with open("sessions/session_" + playername + ".json", "w") as f:
            session_dict = {"started_at": session_dict["started_at"], "int_elo": initial_elo, "current_elo": current_elo, "int_wins": initial_wins, "current_wins": current_wins, "int_losses": initial_losses, "current_losses": current_losses}
            json.dump(session_dict, f, default=str)
    wins = current_wins-initial_wins
    losses = current_losses-initial_losses
    try:
        winrate = round(wins/(wins+losses)*100)
    except ZeroDivisionError:
        winrate = 0
    rgb = ""
    rgb2 = ""
    if winrate < 50:
        rgb = 'class="redText"'
    else:
        rgb = 'class="greenText"'
    elo_diff = current_elo-initial_elo
    if elo_diff >= 0:
        elo_str = "+"
        rgb2 = 'class="greenText"'
    else:
        elo_str = ""
        rgb2 = 'class="redText"'
    def get_rank_url(elo):
        if elo >= 2800:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Legend.png'
        elif elo >= 2600:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Grandmaster.png'
        elif elo >= 2400:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/SeniorMaster.png'
        elif elo >= 2200:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Master.png'
        elif elo >= 2000:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Expert.png'
        elif elo >= 1800:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Diamond.png'
        elif elo >= 1600:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Platinum.png'
        elif elo >= 1400:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Gold.png'
        elif elo >= 1200:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Silver.png'
        else:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Bronze.png'
        return rank_url
    html_file = """
    <!doctype html><html><head>
          <meta http-equiv="refresh" content="5">
          <link rel="preconnect" href="https://fonts.googleapis.com">
          <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
          <link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100;0,300;0,400;0,500;0,700;0,900;1,100;1,300;1,400;1,500;1,700;1,900&display=swap" rel="stylesheet">
        <style>
          .container {
            min-height: 0px;
            max-height: 120px;
            max-width: 700px;
            display: flex;
            flex-direction: right;
            align-items: center;
          }
          r {
            font-family: "Roboto", sans-serif;
            font-weight: 700;
            font-style: normal;
            font-size: 220%;
            padding-left: 10px;
            color: white;
            letter-spacing: 1px;
            text-shadow:
            /* Outline */
            -1px -1px 0 #000000,
            1px -1px 0 #000000,
            -1px 1px 0 #000000,
            1px 1px 0 #000000,
            -2px 0 0 #000000,
            2px 0 0 #000000,
            0 2px 0 #000000,
            0 -2px 0 #000000;
          }
          .redText
          {
            color:rgb(219, 0, 0);
          }
          .greenText
          {
            color:rgb(0, 153, 0);
          }
        </style>
        <title>"""+playername+"""</title>
        </head>
        <body>
        <div class="container">
              <r><b>Starting elo:</b></r>
              <img src="""+get_rank_url(initial_elo)+""">
              <r><b>"""+str(initial_elo)+"""</b></r>
            </div>
        <div class="container">
              <r><b>Current elo:&nbsp;</b></r>
              <img src="""+get_rank_url(current_elo)+""">
              <r><b>"""+str(current_elo)+"""</b></r><r """+rgb2+""" ><b>("""+elo_str+str(elo_diff)+""")</b></r>
            </div>
        <div class="container">
              <r><b>Win:"""+str(wins)+""",&thinsp;Lose:"""+str(losses)+""",&thinsp;Winrate:</b></r><r """+rgb+""" ><b>"""+str(winrate)+"""%</b></r>
            </div>
        </body>
    </html>"""
    with open('/shared/'+playername+'_output.html', "w") as f:
        f.write(html_file)
    return playername+'_output.html'

async def handler(message) -> None:
    if str(message.channel) == "game-starts":
        players = str(message.content).splitlines()[1:]
        gameid = str(message.author).split("#")[0].replace("Game started! ", "")
        if len(players) == 4:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ProcessPoolExecutor() as pool:
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
                                    with concurrent.futures.ProcessPoolExecutor() as pool:
                                        await loop.run_in_executor(pool, functools.partial(stream_overlay, playername, update=True))
                                        pool.shutdown()
            if len(twitch_list) > 0:
                twitch_dict = await twitch_get_streams(twitch_list, playernames=playernames_list)
                for streamer in twitch_dict:
                    if twitch_dict[streamer]["live"] == True:
                        loop = asyncio.get_running_loop()
                        with concurrent.futures.ProcessPoolExecutor() as pool:
                            print(await loop.run_in_executor(pool, functools.partial(stream_overlay, twitch_dict[streamer]["playername"], stream_started_at=str(twitch_dict[streamer]["started_at"]))) + " session started.")
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
                                await loop.run_in_executor(pool, functools.partial(stream_overlay, playername, elo_change=elo_change))
                                pool.shutdown()
                    elif playername in desc3[2]:
                        elo_change = int(desc3[1].split(" elo")[0].split("(")[-1])
                        if os.path.isfile("sessions/session_" + playername + ".json"):
                            loop = asyncio.get_running_loop()
                            with concurrent.futures.ProcessPoolExecutor() as pool:
                                await loop.run_in_executor(pool, functools.partial(stream_overlay, playername, elo_change=elo_change))
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