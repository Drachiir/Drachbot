import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import concurrent.futures
import traceback
import functools
import json
import os
import legion_api

def stream_overlay(playername, stream_started_at="", elo_change=0, update = False):
    if not os.path.isfile("sessions/session_" + playername + ".json"):
        leaderboard = legion_api.get_leaderboard(200)
        for i, player in enumerate(leaderboard):
            if player["profile"][0]["playerName"].casefold() == playername.casefold():
                initial_rank = "#"+str(i+1)
                current_rank = "#"+str(i + 1)
                initial_elo = player["overallElo"]
                current_elo = player["overallElo"]
                initial_wins = player["rankedWinsThisSeason"]
                current_wins = player["rankedWinsThisSeason"]
                initial_losses = player["rankedLossesThisSeason"]
                current_losses = player["rankedLossesThisSeason"]
                break
        else:
            initial_rank = ""
            current_rank = ""
            playerid = legion_api.getid(playername)
            stats = legion_api.getstats(playerid)
            initial_elo = stats["overallElo"]
            current_elo = stats["overallElo"]
            initial_wins = stats["rankedWinsThisSeason"]
            current_wins = stats["rankedWinsThisSeason"]
            initial_losses = stats["rankedLossesThisSeason"]
            current_losses = stats["rankedLossesThisSeason"]
        with open("sessions/session_" + playername + ".json", "w") as f:
            session_dict = {"started_at": stream_started_at, "int_rank": initial_rank, "current_rank": current_rank, "int_elo": initial_elo, "current_elo": current_elo, "int_wins": initial_wins, "current_wins": current_wins, "int_losses": initial_losses, "current_losses": current_losses}
            json.dump(session_dict, f, default=str)
    else:
        with open("sessions/session_" + playername + ".json", "r") as f:
            session_dict = json.load(f)
            try:
                initial_rank = session_dict["int_rank"]
                leaderboard = legion_api.get_leaderboard(200)
                for i, player in enumerate(leaderboard):
                    if player["profile"][0]["playerName"].casefold() == playername.casefold():
                        current_rank = "#"+str(i + 1)
                        break
                else:
                    current_rank = ""
            except Exception:
                initial_rank = ""
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
            session_dict = {"started_at": session_dict["started_at"], "int_rank": initial_rank, "current_rank": current_rank, "int_elo": initial_elo, "current_elo": current_elo, "int_wins": initial_wins, "current_wins": current_wins, "int_losses": initial_losses, "current_losses": current_losses}
            json.dump(session_dict, f, default=str)
    wins = current_wins-initial_wins
    losses = current_losses-initial_losses
    try:
        winrate = round(wins/(wins+losses)*100)
    except ZeroDivisionError:
        winrate = 0
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
    <!doctype html>
    <html>
    <head>
      <meta http-equiv="refresh" content="5">
      <link rel="preconnect" href="https://fonts.googleapis.com">
      <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
      <link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100;0,300;0,400;0,500;0,700;0,900;1,100;1,300;1,400;1,500;1,700;1,900&display=swap" rel="stylesheet">
    <style>
      .container {
        min-height: 0px;
        max-height: 120px;
        display: flex;
        flex-direction: right;
        align-items: center;
		padding-left: 10px;
        overflow: hidden;
      }
      r {
        font-family: "Roboto", sans-serif;
        font-weight: 700;
        font-style: normal;
        font-size: 190%;
        padding-left: 10px;
        color: white;
        white-space: nowrap;
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
    <title>Streamtracker by Drachbot</title>
    </head>
    <body>
    <div class="container">
          <img src="""+get_rank_url(initial_elo)+""">
          <r><b>"""+str(initial_elo)+" "+f"{initial_rank}"+"""</b></r>
        </div>
    <div class="container">
		  <img src="""+get_rank_url(current_elo)+""">
          <r><b>"""+str(current_elo)+" "+f"{current_rank}"+"""</b></r><r """+rgb2+"""><b>("""+elo_str+str(elo_diff)+""")</b></r>
        </div>
    <div class="container">
          <r><b>"""+str(wins)+"""W-"""+str(losses)+"""L,&thinsp;WR:</b></r><r """+rgb+"""><b>"""+str(winrate)+"""%</b></r>
        </div>
    </body>
    </html>"""
    with open('/shared/'+playername+'_output.html', "w") as f:
        f.write(html_file)
    return playername+'_output.html'

class Streamtracker(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    @app_commands.command(name="streamtracker", description="Simple W/L and Elo tracker for your stream.")
    async def streamtracker(self, interaction: discord.Interaction):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
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
                await interaction.response.defer(ephemeral=False, thinking=True)
                await loop.run_in_executor(pool, functools.partial(stream_overlay, playername, update=True))
                pool.shutdown()
                await interaction.followup.send("Use https://overlay.drachbot.site/" + playername + '_output.html as a OBS browser source.')
            except Exception:
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

async def setup(bot:commands.Bot):
    await bot.add_cog(Streamtracker(bot))