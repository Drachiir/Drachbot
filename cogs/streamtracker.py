import json

import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import concurrent.futures
import traceback
import functools

import legion_api
from streamoverlay import stream_overlay

class Streamtracker(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    @app_commands.command(name="streamtracker", description="Simple W/L and Elo tracker for your stream.")
    async def streamtracker(self, interaction: discord.Interaction, player_name: str):
        loop = asyncio.get_running_loop()
        await interaction.response.defer(ephemeral=False, thinking=True)
        with concurrent.futures.ThreadPoolExecutor() as pool:
            try:
                player_id = await loop.run_in_executor(pool, legion_api.getid, player_name)
                with open("Files/streamers.json", "r") as f:
                    data = json.load(f)
                for streamer in data:
                    if player_id in data[streamer]["player_ids"]:
                        await loop.run_in_executor(pool, functools.partial(stream_overlay, player_id, True))
                        pool.shutdown()
                        await interaction.followup.send(f"https://overlay.drachbot.site/{player_id}_output.html")
                        return
            except Exception:
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")
            await interaction.followup.send("Streamer not found, apply here https://forms.gle/ZJpjCC15dAXuAhF7A")

async def setup(bot:commands.Bot):
    await bot.add_cog(Streamtracker(bot))