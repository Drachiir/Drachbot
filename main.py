import asyncio
import json
import os
import random
import traceback
from datetime import datetime, timedelta

import discord
from discord.ext import commands
from discord.ext.commands import Context, errors
from discord.ext.commands._types import BotT

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
        with open("ltdle_data/ltdle.json", "r") as f:
            json_data = json.load(f)
            f.close()
            if datetime.strptime(json_data["next_reset"], "%m/%d/%Y") < datetime.now():
                json_data["next_reset"] = (datetime.now() + timedelta(days=1)).strftime("%m/%d/%Y")
                try:
                    guild = client.get_guild(723645273661767721)
                    channel = guild.get_channel(1176596408300744814)
                    guild2 = client.get_guild(1196160767171510392)
                    channel2 = guild2.get_channel(1216887285325234207)
                    await channel.send("New Legiondle is up! :brain: <a:dinkdonk:1120126536343896106>")
                    await channel2.send("New Legiondle is up! :brain: <a:dinkdonk:1120126536343896106>")
                except:
                    pass
                with open("Files/json/units.json", "r") as f2:
                    unit_json_dict = json.load(f2)
                    f2.close()
                random_unit = unit_json_dict[random.randint(0, len(unit_json_dict) - 1)]
                while random_unit["categoryClass"] == "Special" or random_unit["categoryClass"] == "Passive":
                    random_unit = unit_json_dict[random.randint(0, len(unit_json_dict) - 1)]
                json_data["game_1_selected_unit"] = random_unit
                with open("ltdle_data/ltdle.json", "w") as f3:
                    json.dump(json_data, f3)
                    f3.close()
            else:
                pass
    
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
