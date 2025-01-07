import asyncio
import concurrent.futures
import functools
import os
import platform
import traceback
from datetime import datetime, timezone
import re

import discord
import discord_timestamps
from discord import app_commands
from discord.ext import commands, tasks
from discord_timestamps import TimestampType

import util

def clean_top_games():
    path = util.shared_folder_livegames
    livegame_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.txt')]
    livegame_files = sorted(livegame_files, key=lambda x: int(x.split("_")[1].split(".")[0]), reverse=True)
    for game in livegame_files:
        path2 = path + game
        mod_date = datetime.fromtimestamp(os.path.getmtime(path2), tz=timezone.utc)
        date_diff = datetime.now(tz=timezone.utc) - mod_date
        minutes_diff = date_diff.total_seconds() / 60
        if minutes_diff > 35:
            os.remove(path2)


def get_top_games(oneversusone=False):
    games_num = 6 if oneversusone else 4
    path = util.shared_folder_livegames1v1 if oneversusone else util.shared_folder_livegames

    # Get list of game files and sort by timestamp in descending order
    livegame_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.txt')]
    livegame_files = sorted(livegame_files, key=lambda x: int(x.split("_")[1].split(".")[0]), reverse=True)

    topgames = []
    for game in livegame_files:
        path2 = os.path.join(path, game)
        mod_date = datetime.fromtimestamp(os.path.getmtime(path2), tz=timezone.utc)
        date_diff = datetime.now(tz=timezone.utc) - mod_date
        minutes_diff = date_diff.total_seconds() / 60

        if minutes_diff > 35:
            os.remove(path2)
            continue

        if len(topgames) < games_num:
            topgames.append(game)
        else:
            break

    if not topgames:
        embed = discord.Embed(color=0x8c00ff, description="No ongoing games found")
        return embed

    embed = discord.Embed(color=0x8c00ff)

    for idx, game2 in enumerate(topgames):
        with open(os.path.join(path, game2), "r", encoding="utf_8") as f2:
            txt = f2.readlines()

        mod_date = datetime.fromtimestamp(os.path.getmtime(os.path.join(path, game2)), tz=timezone.utc).timestamp()
        timestamp = discord_timestamps.format_timestamp(mod_date, TimestampType.RELATIVE)

        max_char = 14
        if oneversusone:
            west_player = txt[0].split(":")
            east_player = txt[1].split(":")
            west_display = [west_player[1], west_player[0].ljust(max_char)]
            east_display = [east_player[1], east_player[0].ljust(max_char)]
        else:
            west_players = [p.split(":") for p in txt[:2]]
            east_players = [p.split(":") for p in txt[2:4]]
            west_display = [[p[1], p[0].ljust(max_char)] for p in west_players]
            east_display = [[p[1], p[0].ljust(max_char)] for p in east_players]

        if oneversusone:
            output = (f"{util.get_ranked_emote(int(west_display[0]))}`{west_display[1]}`"
                      f"{util.get_ranked_emote(int(east_display[0]))}`{east_display[1]}`\n")
        else:
            output = (f"{util.get_ranked_emote(int(west_display[0][0]))}`{west_display[0][1]}`  "
                      f"{util.get_ranked_emote(int(east_display[0][0]))}`{east_display[0][1]}`\n"
                      f"{util.get_ranked_emote(int(west_display[1][0]))}`{west_display[1][1]}`  "
                      f"{util.get_ranked_emote(int(east_display[1][0]))}`{east_display[1][1]}`")

        embed.add_field(
            name=f"**Game {idx + 1}**, {txt[-1].strip()} {util.get_ranked_emote(int(txt[-1].strip()))} Started {timestamp}",
            value=output,
            inline=False)
    return embed

class RefreshButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cd_mapping = commands.CooldownMapping.from_cooldown(1.0, 10.0, commands.BucketType.member)
    
    @discord.ui.button(label='Refresh', style=discord.ButtonStyle.blurple, custom_id='persistent_view:refresh')
    async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
            bucket = self.cd_mapping.get_bucket(interaction.message)
            retry_after = bucket.update_rate_limit()
            if retry_after:
                return print(interaction.user.name + " likes to press buttons.")
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                response = await loop.run_in_executor(pool, get_top_games)
                pool.shutdown()
            await interaction.edit_original_response(embed=response)
        except Exception:
            traceback.print_exc()


class RefreshButton2(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.cd_mapping = commands.CooldownMapping.from_cooldown(1.0, 10.0, commands.BucketType.member)

    @discord.ui.button(label='Refresh', style=discord.ButtonStyle.blurple, custom_id='persistent_view:refresh2')
    async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.defer()
            bucket = self.cd_mapping.get_bucket(interaction.message)
            retry_after = bucket.update_rate_limit()
            if retry_after:
                return print(interaction.user.name + " likes to press buttons.")
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                response = await loop.run_in_executor(pool, functools.partial(get_top_games, oneversusone=True))
                pool.shutdown()
            await interaction.edit_original_response(embed=response)
        except Exception:
            traceback.print_exc()

class Topgames(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.clean.start()
        
    def cog_unload(self) -> None:
        self.clean.cancel()
        
    @app_commands.command(name="topgames", description="Shows the 4 highest elo games in Ranked.")
    async def topgames(self, interaction: discord.Interaction, oneversusone: bool = False):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, functools.partial(get_top_games, oneversusone=oneversusone))
                pool.shutdown()
                if type(response) == discord.Embed:
                    if oneversusone:
                        await interaction.followup.send(embed=response, view=RefreshButton2())
                    else:
                        await interaction.followup.send(embed=response, view=RefreshButton())
                else:
                    await interaction.followup.send(response)
            except Exception:
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")
    
    @tasks.loop(minutes=3)
    async def clean(self):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            await loop.run_in_executor(pool, clean_top_games)
            pool.shutdown()

async def setup(bot:commands.Bot):
    await bot.add_cog(Topgames(bot))