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
        if len(txt[0]) < len(txt[2]):
            longest_str_left = len(txt[2])
        else:
            longest_str_left = len(txt[0])
        if len(txt[1]) < len(txt[3]):
            longest_str_right = len(txt[3])
        else:
            longest_str_right = len(txt[1])
        output = "`West:`"
        for c, data in enumerate(txt[:4]):
            data = data.replace("\n", "")
            if c == (len(txt) - 1) / 2:
                output += "\n`East:`"
            string_out = data
            if len(data) < longest_str_left and (c == 0 or c == 2):
                for i in range(longest_str_left-len(data)-1):
                    string_out += " "
            elif len(data) < longest_str_right and (c == 1 or c == 3):
                for i in range(longest_str_right-len(data)-1):
                    string_out += " "
                    
            output += util.get_ranked_emote(int(data.split(":")[1])) + "`" + string_out + "`"
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