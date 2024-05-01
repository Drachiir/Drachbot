import discord
from discord.ext import commands
import os
from datetime import datetime, timedelta, timezone, time

import legion_api


class ManageCommands(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @commands.command()
    async def reload(self, ctx:commands.Context):
        if ctx.author.name == "drachir_":
            content = ctx.message.content[8:]
            if content.casefold() == "all":
                new_exts = []
                for e in os.listdir("cogs"):
                    if "__pycache__" in e: continue
                    elif "cog_template" in e: continue
                    new_exts.append("cogs." + e.split(".")[0])
                for extension in new_exts:
                    await self.client.reload_extension(extension)
                await self.client.tree.sync(guild=None)
                print("Reloaded: "+",".join(new_exts))
            else:
                await self.client.reload_extension("cogs."+content.lower())
                await self.client.tree.sync(guild=None)
                print("Reloaded: "+ content)
        else:
            await ctx.channel.send("No permission to use this command.")
            return
        await ctx.message.add_reaction("✅")
    
    @commands.command()
    async def sync(self, ctx:commands.Context):
        if ctx.author.name == "drachir_":
            print(await self.client.tree.sync(guild=None))
        else:
            await ctx.channel.send("No permission to use this command.")
    @commands.command()
    async def test(self, ctx:commands.Context):
        if ctx.author.name == "drachir_":
            print(legion_api.get_random_games())
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