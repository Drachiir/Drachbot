import asyncio
import json
import os
import platform
import discord
from discord.ext import commands
import cogs.legiontdle
import cogs.topgames
import cogs.novacup
import logging

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
discord.utils.setup_logging(handler=handler, level=logging.INFO, root=False)

with open('Files/json/Secrets.json') as f:
    secret_file = json.load(f)
    f.close()

class Drachbot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(command_prefix=commands.when_mentioned_or("."), intents=intents)
        self.exts = []
        for e in os.listdir("cogs"):
            if "__pycache__" in e:
                continue
            elif "cog_template" in e:
                continue
            elif "wavestats" in e:
                continue
            elif platform.system() == "Windows" and "twitch" in e:
                continue
            self.exts.append("cogs." + e.split(".")[0])
    
    async def setup_hook(self) -> None:
        for extension in self.exts:
            await self.load_extension(extension)
        self.add_view(cogs.topgames.RefreshButton())
        self.add_view(cogs.legiontdle.ModalButton())
        self.add_view(cogs.legiontdle.GameSelectionButtons())
        self.add_view(cogs.legiontdle.ModalLeakButton())
        self.add_view(cogs.legiontdle.ModalEloButton())
        self.add_view(cogs.legiontdle.ModalButton2())
        self.add_view(cogs.legiontdle.RefreshButtonLtdleTotal())
        self.add_view(cogs.legiontdle.RefreshButtonLtdleDaily())
        self.add_view(cogs.legiontdle.RefreshButtonLtdleAvg())
        self.add_view(cogs.legiontdle.RefreshButtonLtdleDailyAsc())
        self.add_view(cogs.novacup.RefreshButtonDiv1())
        self.add_view(cogs.novacup.RefreshButtonDiv2())
    
    async def on_ready(self):
        print(f'"{self.user.display_name}" is now running!')

class Livegame(commands.Bot):
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
            elif "wavestats" in e:
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
    client = Drachbot()
    loop.create_task(client.start(secret_file["token"]))
    try:
        client2 = Livegame()
        loop.create_task(client2.start(secret_file["livegametoken"]))
    except Exception:
        pass
    loop.run_forever()
