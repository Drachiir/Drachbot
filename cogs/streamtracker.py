import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import concurrent.futures
import traceback
import functools
from streamoverlay import stream_overlay

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
                await loop.run_in_executor(pool, functools.partial(stream_overlay, playername, True))
                pool.shutdown()
                await interaction.followup.send("Use https://overlay.drachbot.site/" + playername + '_output.html as a OBS browser source.')
            except Exception:
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")

async def setup(bot:commands.Bot):
    await bot.add_cog(Streamtracker(bot))