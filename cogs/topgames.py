import asyncio
import concurrent.futures
import os
import platform
import traceback
from datetime import datetime, timezone

import discord
import discord_timestamps
from discord import app_commands
from discord.ext import commands
from discord_timestamps import TimestampType

import util


def get_top_games():
    path = "Livegame/Ranked/"
    livegame_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.txt')]
    livegame_files = sorted(livegame_files, key=lambda x: int(x.split("_")[1].split(".")[0]), reverse=True)
    topgames = []
    for game in livegame_files:
        path2 = path + game
        mod_date = datetime.utcfromtimestamp(os.path.getmtime(path2))
        date_diff = datetime.now() - mod_date
        if platform.system() == "Linux":
            minutes_diff = date_diff.total_seconds() / 60
        elif platform.system() == "Windows":
            minutes_diff = date_diff.total_seconds() / 60 - 120
        if minutes_diff > 35:
            os.remove(path2)
            continue
        if len(topgames) < 4:
            topgames.append(game)
        else:
            break
    if len(topgames) == 0:
        return "No games found."
    embed = discord.Embed(color=0x8c00ff)
    for idx, game2 in enumerate(topgames):
        with open(path + game2, "r", encoding="utf_8") as f2:
            txt = f2.readlines()
            f2.close()
        path2 = path + game2
        mod_date = datetime.fromtimestamp(os.path.getmtime(path2), tz=timezone.utc).timestamp()
        timestamp = discord_timestamps.format_timestamp(mod_date, TimestampType.RELATIVE)
        def normalize_string(string1: str, string2: str):
            string1 = string1.split(":")
            string2 = string2.split(":")
            max_char = 14
            if len(string1[0]) > max_char:
                string1[0] = string1[0][:max_char-2]+".."
            else:
                string1[0] = string1[0] + " " * (max_char-len(string1[0]))
            if len(string2[0]) > max_char:
                string2[0] = string2[0][:max_char-2]+".."
            else:
                string2[0] = string2[0] + " " * (max_char-len(string2[0]))
            string1 = f"{string1[1]}:{string1[0]}"
            string2 = f"{string2[1]}:{string2[0]}"
            return [string1, string2]
        west_players = normalize_string(txt[0].replace("\n", ""), txt[1].replace("\n", ""))
        east_players = normalize_string(txt[2].replace("\n", ""), txt[3].replace("\n", ""))
        output = (f"{util.get_ranked_emote(int(west_players[0].split(":")[0]))}`{west_players[0].split(":")[1]}`{util.get_ranked_emote(int(east_players[0].split(":")[0]))}`{east_players[0].split(":")[1]}`\n"
                  f"{util.get_ranked_emote(int(west_players[1].split(":")[0]))}`{west_players[1].split(":")[1]}`{util.get_ranked_emote(int(east_players[1].split(":")[0]))}`{east_players[1].split(":")[1]}`")
        embed.add_field(name="**Game " + str(idx + 1) + "**, " + txt[-1] + " " + util.get_ranked_emote(int(txt[-1])) + " Started " + str(timestamp), value=output, inline=False)
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

class Topgames(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    @app_commands.command(name="topgames", description="Shows the 4 highest elo games in Ranked.")
    async def topgames(self, interaction: discord.Interaction):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            await interaction.response.defer(ephemeral=False, thinking=True)
            try:
                response = await loop.run_in_executor(pool, get_top_games)
                pool.shutdown()
                if type(response) == discord.Embed:
                    await interaction.followup.send(embed=response, view=RefreshButton())
                else:
                    await interaction.followup.send(response)
            except Exception:
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

async def setup(bot:commands.Bot):
    await bot.add_cog(Topgames(bot))