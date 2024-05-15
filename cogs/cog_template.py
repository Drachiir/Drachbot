import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import concurrent.futures
import traceback
import functools
import json
import difflib

import drachbot_db
import util
import legion_api

class CogName(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

async def setup(bot:commands.Bot):
    await bot.add_cog(CogName(bot))