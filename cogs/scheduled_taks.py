import traceback
from datetime import datetime, timedelta, timezone, time
from discord.ext import commands, tasks
import json
import random
import legion_api
import concurrent.futures
import functools
import asyncio

utc = timezone.utc

# If no tzinfo is given then UTC is assumed.
task_time = time(hour=0, minute=0, second=5, tzinfo=utc)
#task_time = datetime.time(datetime.now(utc)+timedelta(seconds=5))

class ScheduledTasks(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.reset.start()

    def cog_unload(self):
        self.reset.cancel()

    @tasks.loop(time=task_time)
    async def reset(self):
        with open("ltdle_data/ltdle.json", "r") as f:
            json_data = json.load(f)
            f.close()
            if datetime.strptime(json_data["next_reset"], "%m/%d/%Y") < datetime.now():
                json_data["next_reset"] = (datetime.now() + timedelta(days=1)).strftime("%m/%d/%Y")
                for noti_channel in json_data["notify_channels"]:
                    try:
                        guild = self.client.get_guild(noti_channel[0])
                        channel = guild.get_channel(noti_channel[1])
                        await channel.send("New Legiondle is up! :brain: <a:dinkdonk:1120126536343896106>")
                    except Exception:
                        continue
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
        try:
            print("Starting scheduled ladder update...")
            loop = asyncio.get_running_loop()
            with concurrent.futures.ProcessPoolExecutor() as pool:
                update_string = await loop.run_in_executor(pool, functools.partial(legion_api.ladder_update, 100))
                guild = self.client.get_guild(json_data["notify_channels"][0][0])
                channel = guild.get_channel(json_data["notify_channels"][0][1])
                await channel.send(update_string)
        except Exception:
            traceback.print_exc()
            
async def setup(bot: commands.Bot):
    await bot.add_cog(ScheduledTasks(bot))