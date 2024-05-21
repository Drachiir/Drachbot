import os
import traceback
from datetime import datetime, timedelta, timezone, time
from discord.ext import commands, tasks
import json
import random
import legion_api
import concurrent.futures
import functools
import asyncio
import image_generators
import util

import cogs.elo as elo
import cogs.legiontdle as ltdle

utc = timezone.utc
task_time = time(hour=0, minute=0, second=1, tzinfo=utc)
#task_time = datetime.time(datetime.now(utc)+timedelta(seconds=5))
print(datetime.now().strftime("%m/%d/%Y, %H:%M:%S"))


def reset(self):
    with open("ltdle_data/ltdle.json", "r") as f:
        json_data = json.load(f)
        f.close()
        if datetime.strptime(json_data["next_reset"], "%m/%d/%Y") < datetime.now():
            json_data["next_reset"] = (datetime.now() + timedelta(days=1)).strftime("%m/%d/%Y")
            # legiondle
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
            # GuessTheLeak
            try:
                games_list = os.listdir("Games/")
                leak_found = False
                while leak_found == False:
                    random_game = random.choice(games_list)
                    if random_game.startswith("2023"):
                        continue
                    elif random_game.startswith("2022"):
                        continue
                    elif random_game.split("_")[1].split("-")[1] == "00":
                        continue
                    with open("Games/" + random_game, "r") as f:
                        game_data = json.load(f)
                        f.close()
                    leaks_list = []
                    for index, player in enumerate(game_data["playersData"]):
                        if player["leakValue"] > 0:
                            for wave, leak in enumerate(player["leaksPerWave"]):
                                if len(leak) > 0:
                                    if wave == 0 or wave == 9 or wave == 19:
                                        continue
                                    leaks_list.append([game_data["_id"], index, wave, util.calc_leak(leak, wave)])
                    if len(leaks_list) > 0:
                        leak_found = True
                random.shuffle(leaks_list)
                random_leak = [leaks_list[0]]
                for i, r in enumerate(random_leak):
                    random_leak[i].append(image_generators.gameid_visualizer_singleplayer(r[0], r[2], r[1]))
                with open("ltdle_data/ltdle.json", "r") as f2:
                    json_data = json.load(f2)
                    f2.close()
                json_data["game_2_selected_leak"] = random_leak
                with open("ltdle_data/ltdle.json", "w") as f3:
                    json.dump(json_data, f3)
                    f3.close()
            except Exception:
                traceback.print_exc()
            #Guess The Elo
            games = legion_api.get_random_games()
            random_game2 = random.choice(games)
            while random_game2[2] == "":
                random_game2 = random.choice(games)
            rand_wave = random.randint(4,random_game2[3]-1)
            im1 = elo.gameid_visualizer(random_game2[2], rand_wave, hide_names=True)
            im2 = elo.gameid_visualizer(random_game2[2], rand_wave)
            with open("ltdle_data/ltdle.json", "r") as f:
                json_data = json.load(f)
                f.close()
            json_data["game_3_selected_game"] = [im1,im2,random_game2[4]]
            with open("ltdle_data/ltdle.json", "w") as f:
                json.dump(json_data, f)
                f.close()
            return True
        else:
            return False

class ScheduledTasks(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.scheduled_reset.start()

    def cog_unload(self):
        self.scheduled_reset.cancel()

    @tasks.loop(time=task_time)
    async def scheduled_reset(self):
        try:
            print("Starting scheduled reset...")
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                update = await loop.run_in_executor(pool, functools.partial(reset, self))
                pool.shutdown()
            if update:
                with open("ltdle_data/ltdle.json", "r") as f:
                    json_data = json.load(f)
                    f.close()
                with open("Files/json/discord_channels.json", "r") as f:
                    discord_channels = json.load(f)
                    f.close()
                # notifications
                try:
                    guild = self.client.get_guild(discord_channels["drachbot_update"][0])
                    channel = guild.get_channel(discord_channels["drachbot_update"][1])
                    message = await channel.send("New Legiontdle is up! :brain: <a:dinkdonk:1120126536343896106>")
                    await message.publish()
                except Exception:
                    pass
                for player in os.listdir("ltdle_data"):
                    if player.endswith(".json"): continue
                    if os.path.isfile(f"ltdle_data/{player}/notify.txt"):
                        with open(f"ltdle_data/{player}/notify.txt", "r") as f:
                            lines = f.readlines()
                        try:
                            user = await self.client.fetch_user(int(lines[0]))
                            await user.send(embed=ltdle.ltdle({},{}, 0), view=ltdle.GameSelectionButtons())
                            await asyncio.sleep(1)
                        except Exception:
                            traceback.print_exc()
                # games update
                try:
                    loop = asyncio.get_running_loop()
                    with concurrent.futures.ProcessPoolExecutor() as pool:
                        ladder_update = await loop.run_in_executor(pool, functools.partial(legion_api.get_recent_games, 100))
                        pool.shutdown()
                    guild = self.client.get_guild(discord_channels["toikan_drachbot"][0])
                    channel = guild.get_channel(discord_channels["toikan_drachbot"][1])
                    message = await channel.send(embed=ladder_update)
                except Exception:
                    pass
            else:
                print("No reset required now.")
        except Exception:
            traceback.print_exc()
            
async def setup(bot: commands.Bot):
    await bot.add_cog(ScheduledTasks(bot))