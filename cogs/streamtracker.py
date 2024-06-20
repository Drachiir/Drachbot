import platform
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
import jinja2
from jinja2 import Environment, FileSystemLoader

if platform.system() == "Linux":
    shared_folder = "/shared/"
else:
    shared_folder = "shared/"

def stream_overlay(playername, stream_started_at="", elo_change=0, update = False):
    if not os.path.isfile("sessions/session_" + playername + ".json"):
        leaderboard = legion_api.get_leaderboard(100)
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
                live = False
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
            live = False
        with open("sessions/session_" + playername + ".json", "w") as f:
            session_dict = {"started_at": stream_started_at, "int_rank": initial_rank, "current_rank": current_rank,
                            "int_elo": initial_elo, "current_elo": current_elo, "int_wins": initial_wins, "current_wins": current_wins,
                            "int_losses": initial_losses, "current_losses": current_losses, "live": live}
            json.dump(session_dict, f, default=str)
    else:
        with open("sessions/session_" + playername + ".json", "r") as f:
            session_dict = json.load(f)
            try:
                initial_rank = session_dict["int_rank"]
                leaderboard = legion_api.get_leaderboard(100)
                for i, player in enumerate(leaderboard):
                    if player["profile"][0]["playerName"].casefold() == playername.casefold():
                        current_rank = "#"+str(i + 1)
                        break
                else:
                    current_rank = ""
            except Exception:
                initial_rank = ""
            live = session_dict["live"]
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
        if live:
            with open("sessions/session_" + playername + ".json", "w") as f:
                session_dict = {"started_at": session_dict["started_at"], "int_rank": initial_rank, "current_rank": current_rank, "int_elo": initial_elo, "current_elo": current_elo,
                                "int_wins": initial_wins, "current_wins": current_wins, "int_losses": initial_losses, "current_losses": current_losses, "live": live}
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
    simple = "Simple/"
    def get_rank_url(elo):
        if elo >= 2800:
            rank_url = f'https://cdn.legiontd2.com/icons/Ranks/{simple}Legend.png'
        elif elo >= 2600:
            rank_url = f'https://cdn.legiontd2.com/icons/Ranks/{simple}GrandMaster.png'
        elif elo >= 2400:
            rank_url = f'https://cdn.legiontd2.com/icons/Ranks/{simple}SeniorMaster.png'
        elif elo >= 2200:
            rank_url = f'https://cdn.legiontd2.com/icons/Ranks/{simple}Master.png'
        elif elo >= 2000:
            rank_url = f'https://cdn.legiontd2.com/icons/Ranks/{simple}Expert.png'
        elif elo >= 1800:
            rank_url = f'https://cdn.legiontd2.com/icons/Ranks/{simple}Diamond.png'
        elif elo >= 1600:
            rank_url = f'https://cdn.legiontd2.com/icons/Ranks/{simple}Platinum.png'
        elif elo >= 1400:
            rank_url = f'https://cdn.legiontd2.com/icons/Ranks/{simple}Gold.png'
        elif elo >= 1200:
            rank_url = f'https://cdn.legiontd2.com/icons/Ranks/{simple}Silver.png'
        else:
            rank_url = f'https://cdn.legiontd2.com/icons/Ranks/{simple}Bronze.png'
        return rank_url
    rank_url_int = get_rank_url(initial_elo)
    rank_url_current = get_rank_url(current_elo)
    enviorment = jinja2.Environment(loader=FileSystemLoader("templates/"))
    template = enviorment.get_template("streamoverlay.html")
    html_file = template.render(rank_url_int=rank_url_int, rank_url_current=rank_url_current,
                                initial_elo=initial_elo, initial_rank=initial_rank, current_rank=current_rank,
                                wins=wins, losses=losses, current_elo=current_elo, winrate=winrate,
                                elo_diff=elo_diff, elo_str=elo_str, rgb=rgb, rgb2=rgb2)
    with open(shared_folder+playername+'_output.html', "w") as f:
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