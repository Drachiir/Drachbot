import asyncio
import json
import os

import discord
from discord.ext import commands
from discord.ext.commands import Context, errors
from discord.ext.commands._types import BotT

import cogs.legiondle
import cogs.topgames

with open('Files/json/Secrets.json') as f:
    secret_file = json.load(f)
    f.close()

class Client(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=commands.when_mentioned_or("."), intents=intents)
        self.exts = []
        for e in os.listdir("cogs"):
            if "__pycache__" in e: continue
            elif "cog_template" in e: continue
            self.exts.append("cogs." + e.split(".")[0])
    
    async def on_command_error(self, context: Context[BotT], exception: errors.CommandError, /) -> None:
        print(exception)
    
    async def setup_hook(self) -> None:
        for extension in self.exts:
            await self.load_extension(extension)
        self.add_view(cogs.topgames.RefreshButton())
        self.add_view(cogs.legiondle.ModalButton())
        self.add_view(cogs.legiondle.GameSelectionButtons())
        self.add_view(cogs.legiondle.ModalLeakButton())
    
    async def on_ready(self):
        print(f'"{self.user.display_name}" is now running!')

class Client2(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=commands.when_mentioned_or("."), intents=intents)
        self.exts = []
        for e in os.listdir("cogs2"):
            if "__pycache__" in e:
                continue
            elif "cog_template" in e:
                continue
            self.exts.append("cogs2." + e.split(".")[0])
    
    async def setup_hook(self) -> None:
        for extension in self.exts:
            await self.load_extension(extension)
    
    async def on_ready(self):
        print(f'"{self.user.display_name}" is now running!')

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = Client()
    client2 = Client2()
    loop.create_task(client.start(secret_file["token"]))
    loop.create_task(client2.start(secret_file["livegametoken"]))
    loop.run_forever()
