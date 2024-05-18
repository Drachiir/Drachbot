import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import concurrent.futures
import traceback
import functools
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import csv

import util


def novacup(division):
    html = requests.get('https://docs.google.com/spreadsheets/u/3/d/e/2PACX-1vQKndupwCvJdwYYzSNIm-olob9k4JYK4wIoSDXlxiYr2h7DFlO7NgveneoFtlBlZaMvQUP6QT1eAYkN/pubhtml#', headers={'Cache-Control': 'no-cache'}).text
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("table")
    with open("novacup.csv", "w", encoding="utf-8") as f:
        wr = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
        wr.writerows([[td.text for td in row.find_all("td")] for row in tables[0].find_all("tr")])
    team_dict = {}
    with open("novacup.csv", encoding="utf-8", newline="") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            try:
                if row[1] != "Team Name" and row[1] != "" and row[1] not in team_dict:
                    team_dict[row[1]] = [row[2],row[3],row[4]]
            except Exception:
                continue
    newIndex = sorted(team_dict, key=lambda x: int(team_dict[x][2]), reverse=True)
    team_dict = {k: team_dict[k] for k in newIndex}
    month = datetime.now()
    if division == "1":
        elo = 0
        for i, t in enumerate(team_dict):
            elo += int(team_dict[t][2])
            if i == 7:
                break
        title = str(month.strftime("%B")) + " Nova Cup Division 1 ("+str(round(elo/8))+util.get_ranked_emote(round(elo/8))+")"
    else:
        elo = 0
        for i, t in enumerate(team_dict):
            if 7 < i < 16:
                elo += int(team_dict[t][2])
        title = str(month.strftime("%B")) + " Nova Cup Division 2 ("+str(round(elo/8))+util.get_ranked_emote(round(elo/8))+")"
    embed = discord.Embed(color=util.random_color(), title=title)
    embed.set_thumbnail(url="https://cdn.legiontd2.com/icons/Tournaments/NovaCup/NovaCup_00.png")
    count = 1
    for team in team_dict:
        if count < 9 and division == "1":
            embed.add_field(name=str(count) +". **"+ team + "**:", value=team_dict[team][0] + ", " + team_dict[team][1] + ", Elo: " + team_dict[team][2]+util.get_ranked_emote(int(team_dict[team][2])), inline=False)
        if count >= 9 and division == "2":
            embed.add_field(name=str(count-8) +". **"+ team + "**:", value=team_dict[team][0] + ", " + team_dict[team][1] + ", Elo: " + team_dict[team][2]+util.get_ranked_emote(int(team_dict[team][2])), inline=False)
        count +=1
        if count == 17:
            break
    return embed


class RefreshButtonDiv1(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cd_mapping = commands.CooldownMapping.from_cooldown(1.0, 10.0, commands.BucketType.member)
    
    @discord.ui.button(label='Refresh', style=discord.ButtonStyle.blurple, custom_id='persistent_view:refreshdiv1')
    async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
            bucket = self.cd_mapping.get_bucket(interaction.message)
            retry_after = bucket.update_rate_limit()
            if retry_after:
                return print(interaction.user.name + " likes to press buttons.")
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                response = await loop.run_in_executor(pool, functools.partial(novacup, "1"))
                pool.shutdown()
                await interaction.edit_original_response(embed=response)
        except Exception:
            traceback.print_exc()


class RefreshButtonDiv2(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cd_mapping = commands.CooldownMapping.from_cooldown(1.0, 10.0, commands.BucketType.member)
    
    @discord.ui.button(label='Refresh', style=discord.ButtonStyle.blurple, custom_id='persistent_view:refreshdiv2')
    async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
            bucket = self.cd_mapping.get_bucket(interaction.message)
            retry_after = bucket.update_rate_limit()
            if retry_after:
                return print(interaction.user.name + " likes to press buttons.")
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                response = await loop.run_in_executor(pool, functools.partial(novacup, "2"))
                pool.shutdown()
                await interaction.edit_original_response(embed=response)
        except Exception:
            traceback.print_exc()


class Novacup(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    @app_commands.command(name="novacup", description="Shows current teams in each novacup division 1 or 2.")
    @app_commands.describe(division='Enter division.')
    @app_commands.choices(division=[
        discord.app_commands.Choice(name='1', value='1'),
        discord.app_commands.Choice(name='2', value='2')
    ])
    async def novacup(self, interaction: discord.Interaction, division: discord.app_commands.Choice[str]):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ProcessPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(novacup, division.value))
                pool.shutdown()
                if type(response) == discord.Embed:
                    if division.value == "1":
                        await interaction.followup.send(embed=response, view=RefreshButtonDiv1())
                    else:
                        await interaction.followup.send(embed=response, view=RefreshButtonDiv2())
                else:
                    await interaction.followup.send(response)
            except Exception:
                print("/" + interaction.command.name + " failed. args: " + str(interaction.data.values()))
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

async def setup(bot:commands.Bot):
    await bot.add_cog(Novacup(bot))