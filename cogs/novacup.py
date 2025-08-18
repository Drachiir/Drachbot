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


def novacup(division: str):
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQKndupwCvJdwYYzSNIm-olob9k4JYK4wIoSDXlxiYr2h7DFlO7NgveneoFtlBlZaMvQUP6QT1eAYkN/pub?gid=1138847821&single=true&output=csv"
    response = requests.get(url, headers={'Cache-Control': 'no-cache'})
    response.raise_for_status()

    team_dict = {}
    reader = csv.reader(response.text.splitlines())
    for row in reader:
        try:
            if row[1] != "Team Name" and row[1] != "" and row[1] not in team_dict:
                team_dict[row[1]] = [row[2], row[3], int(float(row[4]))]
        except Exception:
            continue

    # Sort by Elo descending
    newIndex = sorted(team_dict, key=lambda x: team_dict[x][2], reverse=True)
    team_dict = {k: team_dict[k] for k in newIndex}
    month = datetime.now()

    # Division setup
    if division == "1":
        start, end, div_size = 0, 8, 8
    elif division == "2":
        start, end, div_size = 8, 16, 8
    elif division == "3":
        start, end, div_size = 16, 32, 16
    else:
        return None

    # Average Elo for title
    elo = sum([team_dict[t][2] for i, t in enumerate(team_dict) if start <= i < end])
    avg_elo = round(elo / div_size)
    title = f"{month.strftime('%B')} Nova Cup Division {division} ({avg_elo}{util.get_ranked_emote(avg_elo)})"

    # Embed formatting
    if division == "3":
        # Division 3: single block
        team_lines = []
        for i, (team, data) in enumerate(list(team_dict.items())[start:end]):
            elo = data[2]
            teamname_fmt = team[:14].ljust(14)
            team_line = f"`{i+1:>2}. {teamname_fmt}: {elo}`{util.get_ranked_emote(elo)}{data[0]}, {data[1]}"
            team_lines.append(team_line)
        embed = discord.Embed(color=util.random_color(), title=title, description="\n".join(team_lines))
        embed.set_thumbnail(url="https://cdn.legiontd2.com/icons/Tournaments/NovaCup/NovaCup_00.png")
    else:
        # Div 1 & 2: one field per team
        embed = discord.Embed(color=util.random_color(), title=title)
        embed.set_thumbnail(url="https://cdn.legiontd2.com/icons/Tournaments/NovaCup/NovaCup_00.png")
        for i, (team, data) in enumerate(list(team_dict.items())[start:end]):
            elo = data[2]
            value = f"{data[0]}, {data[1]}, Elo: {elo}{util.get_ranked_emote(elo)}"
            embed.add_field(name=f"{i+1}. **{team}**:", value=value, inline=False)

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
                return
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
                return
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                response = await loop.run_in_executor(pool, functools.partial(novacup, "2"))
                pool.shutdown()
                await interaction.edit_original_response(embed=response)
        except Exception:
            traceback.print_exc()


class RefreshButtonDiv3(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cd_mapping = commands.CooldownMapping.from_cooldown(1.0, 10.0, commands.BucketType.member)

    @discord.ui.button(label='Refresh', style=discord.ButtonStyle.blurple, custom_id='persistent_view:refreshdiv3')
    async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
            bucket = self.cd_mapping.get_bucket(interaction.message)
            retry_after = bucket.update_rate_limit()
            if retry_after:
                return
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                response = await loop.run_in_executor(pool, functools.partial(novacup, "3"))
                pool.shutdown()
                await interaction.edit_original_response(embed=response)
        except Exception:
            traceback.print_exc()


class Novacup(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    @app_commands.command(name="novacup", description="Shows current teams in each novacup division 1, 2 or 3.")
    @app_commands.describe(division='Enter division.')
    @app_commands.choices(division=[
        discord.app_commands.Choice(name='1', value='1'),
        discord.app_commands.Choice(name='2', value='2'),
        discord.app_commands.Choice(name='3', value='3'),
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
                    elif division.value == "2":
                        await interaction.followup.send(embed=response, view=RefreshButtonDiv2())
                    else:
                        await interaction.followup.send(embed=response, view=RefreshButtonDiv3())
                else:
                    await interaction.followup.send(response)
            except Exception:
                print("/" + interaction.command.name + " failed. args: " + str(interaction.data.values()))
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

async def setup(bot:commands.Bot):
    await bot.add_cog(Novacup(bot))