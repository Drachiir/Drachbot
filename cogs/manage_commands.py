import random
import sys
import traceback
import concurrent.futures
import functools
import asyncio
import discord
from discord.ext import commands
import os
from datetime import datetime, timedelta, timezone, time

import cogs.streamtracker
import cogs.scheduled_tasks
import legion_api
import cogs.scheduled_tasks as s_tasks
import util
import platform
from PIL import Image, ImageOps

class ManageCommands(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.command()
    async def reload(self, ctx:commands.Context):
        if ctx.author.name == "drachir_":
            try:
                content = ctx.message.content[8:]
                if content.casefold() == "all":
                    new_exts = []
                    for e in os.listdir("cogs"):
                        if "__pycache__" in e:
                            continue
                        elif "cog_template" in e:
                            continue
                        elif "twitch" in e:
                            continue
                        new_exts.append("cogs." + e.split(".")[0])
                    for extension in new_exts:
                        await self.client.reload_extension(extension)
                    print("Reloaded: "+",".join(new_exts))
                else:
                    await self.client.reload_extension("cogs."+content.lower())
                    print("Reloaded: "+ content)
            except Exception:
                traceback.print_exc()
        else:
            await ctx.channel.send("No permission to use this command.")
            return
        await ctx.message.add_reaction("✅")
    
    @commands.command()
    async def ladder_update(self, ctx: commands.Context):
        if ctx.author.name == "drachir_":
            try:
                loop = asyncio.get_running_loop()
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    ladder_update = await loop.run_in_executor(pool, functools.partial(legion_api.ladder_update, 100))
                    pool.shutdown()
            except Exception:
                traceback.print_exc()
        else:
            await ctx.channel.send("No permission to use this command.")
    
    @commands.command()
    async def update(self, ctx: commands.Context):
        if ctx.author.name == "drachir_":
            content = ctx.message.content[8:]
            try:
                loop = asyncio.get_running_loop()
                with concurrent.futures.ProcessPoolExecutor() as pool:
                    ladder_update = await loop.run_in_executor(pool, functools.partial(legion_api.get_recent_games, int(content)))
                    pool.shutdown()
                await ctx.send(embed=ladder_update)
            except Exception:
                traceback.print_exc()
        else:
            await ctx.channel.send("No permission to use this command.")
    
    @commands.command()
    async def notify(self, ctx: commands.Context):
        if ctx.author.name == "drachir_":
            try:
                await s_tasks.ltdle_notify(self, 1)
            except Exception:
                traceback.print_exc()
        else:
            await ctx.channel.send("No permission to use this command.")
    
    @commands.command()
    async def reset_ltdle(self, ctx: commands.Context):
        if ctx.author.name == "drachir_":
            cogs.scheduled_tasks.reset()
        else:
            await ctx.channel.send("No permission to use this command.")
    
    @commands.command()
    async def overlay(self, ctx: commands.Context):
        if ctx.author.name == "drachir_":
            try:
                cogs.streamtracker.stream_overlay("drachir")
            except Exception:
                traceback.print_exc()
        else:
            await ctx.channel.send("No permission to use this command.")
    
    @commands.command()
    async def sync(self, ctx:commands.Context):
        if ctx.author.name == "drachir_":
            print(await self.client.tree.sync(guild=None))
        else:
            await ctx.channel.send("No permission to use this command.")
    
    @commands.command()
    async def kill(self, ctx:commands.Context):
        if ctx.author.name == "drachir_":
            await self.client.close()
            loop = asyncio.get_running_loop()
            loop.stop()
        else:
            await ctx.channel.send("No permission to use this command.")
    
    @commands.command()
    async def test(self, ctx:commands.Context):
        if ctx.author.name == "drachir_":
            try:
                if platform.system() == "Linux":
                    shared_folder = "/shared/Images/"
                    shared2_folder = "/shared2/"
                else:
                    shared_folder = "shared/Images/"
                    shared2_folder = "shared2/"
                name = "elite_archer"
                rand_x = 300
                rand_y = 69
                content = ctx.message.content[6:]
                for i in range(5):
                    random_id = util.id_generator()
                    im = util.get_icons_image("splashes", name)
                    im = util.zoom_at(im, rand_x, rand_y, zoom=i + float(content))
                    if i == 4:
                        im = ImageOps.grayscale(im)
                    im.save(f"{shared_folder}{random_id}_{i + 1}.png")
                random_id = util.id_generator()
                im = util.get_icons_image("splashes", name)
                im.save(f"{shared_folder}{random_id}.png")
                await ctx.send("done")
            except Exception:
                traceback.print_exc()
        else:
            await ctx.channel.send("No permission to use this command.")
    
    @commands.command()
    async def time(self, ctx:commands.Context):
        await ctx.channel.send(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))
    
    @commands.command()
    async def ping(self, ctx:commands.Context):
        await ctx.send(f"pong\n`{round(self.client.latency * 1000)} ms latency`")
        
        
async def setup(bot:commands.Bot):
    await bot.add_cog(ManageCommands(bot))