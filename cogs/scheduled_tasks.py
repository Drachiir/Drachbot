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
from peewee import fn
from peewee_pg import PlayerData, GameData
import cogs.elo as elo
import cogs.legiontdle as ltdle
from PIL import Image, ImageOps
import PIL
import platform

current_patch = "v11.05"
current_min_elo = 2500

if platform.system() == "Linux":
    shared_folder = "/shared/Images/"
    shared2_folder = "/shared2/"
else:
    shared_folder = "shared/Images/"
    shared2_folder = "shared2/"
site = "https://overlay.drachbot.site/Images/"

utc = timezone.utc
task_time = time(hour=0, minute=0, second=3, tzinfo=utc)
#task_time = datetime.time(datetime.now(utc)+timedelta(seconds=5))

def reset_game1(json_data):
    with open("Files/json/units.json", "r") as f2:
        unit_json_dict = json.load(f2)
        f2.close()
    random_unit = unit_json_dict[random.randint(0, len(unit_json_dict) - 1)]
    while (random_unit["categoryClass"] == "Special" or
           random_unit["categoryClass"] == "Passive" or
           "hybrid" in random_unit["unitId"]):
        random_unit = unit_json_dict[random.randint(0, len(unit_json_dict) - 1)]
    json_data["game_1_selected_unit"] = random_unit
    return json_data

def reset_game2(json_data):
    query = (PlayerData
             .select(GameData.queue, GameData.game_id, GameData.game_elo, GameData.version, PlayerData.player_slot, PlayerData.leaks_per_wave)
             .join(GameData)
             .where((GameData.queue == "Normal") & (GameData.game_elo > current_min_elo) & GameData.version.startswith(current_patch))
             .order_by(fn.Random())
             ).dicts()
    leaks_list = []
    for row in query.iterator():
        if row["leaks_per_wave"] != [""]:
            for wave, leak in enumerate(row["leaks_per_wave"]):
                if len(leak) > 0:
                    if wave in [0, 1, 9, 19]:
                        continue
                    match row["player_slot"]:
                        case 1:
                            index = 0
                        case 2:
                            index = 1
                        case 5:
                            index = 2
                        case 6:
                            index = 3
                    leaks_list.append([row["game_id"], index, wave, util.calc_leak(leak, wave)])
        if len(leaks_list) > 10:
            print("Found leaks for guess the leak")
            break
    random_leak = random.choice(leaks_list)
    random_leak.append(image_generators.gameid_visualizer_singleplayer(random_leak[0], random_leak[2], random_leak[1]))
    json_data["game_2_selected_leak"] = random_leak
    return json_data

def reset_game3(json_data):
    games = legion_api.get_random_games()
    random_game2 = random.choice(games)
    while random_game2[2] == "":
        random_game2 = random.choice(games)
    rand_wave = random.randint(4, random_game2[3] - 1)
    im1 = elo.gameid_visualizer(random_game2[2], rand_wave, hide_names=True)
    im2 = elo.gameid_visualizer(random_game2[2], rand_wave)
    json_data["game_3_selected_game"] = [im1, im2, random_game2[4]]
    return json_data

def reset_game4(json_data):
    with open("Files/json/units.json", "r") as f2:
        unit_json_dict = json.load(f2)
        f2.close()
    random_unit = unit_json_dict[random.randint(0, len(unit_json_dict) - 1)]
    while (random_unit["categoryClass"] == "Special" or
           random_unit["categoryClass"] == "Passive" or
           "hybrid" in random_unit["unitId"]):
        random_unit = unit_json_dict[random.randint(0, len(unit_json_dict) - 1)]
    name = random_unit["unitId"].replace("_unit_id", "")
    new_name = ""
    for icon_string in name.split("_"):
        new_name += icon_string.capitalize()
    json_data["game_4_selected_unit"] = [new_name, []]
    rand_x = random.randint(50,450)
    rand_y = random.randint(50, 450)
    for i in range(5):
        random_id = util.id_generator()
        im = util.get_icons_image("splashes", name)
        im = util.zoom_at(im, rand_x, rand_y, zoom=i+0.4)
        if i == 4:
            im = ImageOps.grayscale(im)
        im.save(f"{shared_folder}{random_id}_{i+1}.png")
        json_data["game_4_selected_unit"][1].insert(0, f"{random_id}_{i+1}.png")
    random_id = util.id_generator()
    im = util.get_icons_image("splashes", name)
    im.save(f"{shared_folder}{random_id}.png")
    json_data["game_4_selected_unit"][1].append(f"{random_id}.png")
    return json_data

def reset_game5(json_data):
    query = (GameData
             .select(GameData.queue, GameData.game_id, GameData.game_elo, GameData.version, GameData.ending_wave)
             .where((GameData.queue == "Normal") & (GameData.game_elo > current_min_elo) & GameData.version.startswith(current_patch) & (GameData.ending_wave > 12))
             .order_by(fn.Random())
             ).limit(5).dicts()
    games = []
    for row in query.iterator():
        query2 = (PlayerData
                  .select(PlayerData.game_result, PlayerData.player_slot)
                  .where(PlayerData.game_id == row["game_id"])).dicts()
        winner = ""
        for row2 in query2:
            if row2["player_slot"] == 1 and row2["game_result"] == "won":
                winner = "West"
                break
            if row2["player_slot"] == 5 and row2["game_result"] == "won":
                winner = "East"
                break
        if winner in ["West", "East"]:
            im1 = elo.gameid_visualizer(row["game_id"], random.randint(11, row["ending_wave"]-1), hide_names=True)
            im2 = elo.gameid_visualizer(row["game_id"], row["ending_wave"])
            games.append([im1, im2, winner, row["game_elo"], row["ending_wave"]])
    json_data["game_5_games"] = games
    return json_data

def season_reset(json_data):
    print("Starting Season Reset...")
    for player in os.listdir("ltdle_data/"):
        if os.path.isfile(f"ltdle_data/{player}/data.json"):
            os.rename(f"ltdle_data/{player}/data.json", f"ltdle_data/{player}/data_season{json_data["season"][0]}.json")
            with open(f"ltdle_data/{player}/data.json", "w") as f:
                date_now = datetime.now()
                data = {"name": player, "score": 0, "scores_dict": {}, "games_played": 0,
                        "game1": {"games_played": 0, "score": 0, "last_played": date_now.strftime("%m/%d/%Y"), "game_finished": False, "guesses": []},
                        "game2": {"games_played": 0, "score": 0, "last_played": date_now.strftime("%m/%d/%Y"), "image": 0, "game_finished": False, "guesses": []},
                        "game3": {"games_played": 0, "score": 0, "last_played": date_now.strftime("%m/%d/%Y"), "image": 0, "game_finished": False, "guesses": []},
                        "game4": {"games_played": 0, "score": 0, "last_played": date_now.strftime("%m/%d/%Y"), "image": 0, "game_finished": False, "guesses": []},
                        "game5": {"games_played": 0, "score": 0, "last_played": date_now.strftime("%m/%d/%Y"), "image": 0, "game_finished": False, "guesses": []}}
                json.dump(data, f, indent=2)
                f.close()
    json_data["season"][0] += 1
    print("Success!")
    return json_data

async def ltdle_notify(self, update):
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
        if update == 1:
            message = await channel.send("New Legiontdle is up! :brain: <a:dinkdonk:1120126536343896106>")
        else:
            message = await channel.send(f"Legiontdle Season {json_data["season"][0]} is up! :brain: <a:dinkdonk:1120126536343896106>")
        await message.publish()
    except Exception:
        pass
    count = 0
    for player in os.listdir("ltdle_data"):
        if player.endswith(".json"): continue
        if os.path.isfile(f"ltdle_data/{player}/notify.txt"):
            with open(f"ltdle_data/{player}/notify.txt", "r") as f:
                lines = f.readlines()
            try:
                user = await self.client.fetch_user(int(lines[0]))
                await user.send(content=f"New Legiontdle is up {user.mention}!", embed=ltdle.ltdle({}, json_data, 0), view=ltdle.GameSelectionButtons())
                count += 1
                await asyncio.sleep(0.5)
            except Exception:
                traceback.print_exc()
    print(f"Successfully sent {count} DM notis")

def reset():
    with open("ltdle_data/ltdle.json", "r") as f:
        json_data = json.load(f)
        f.close()
    if datetime.strptime(json_data["next_reset"], "%m/%d/%Y") < datetime.now():
        new_season = 1
        if json_data["next_reset"].split("/")[1] == "01":
            new_season = 2
            json_data = season_reset(json_data)
        json_data["next_reset"] = (datetime.now() + timedelta(days=1)).strftime("%m/%d/%Y")
        json_data = reset_game1(json_data)
        #json_data = reset_game2(json_data)
        json_data = reset_game3(json_data)
        json_data = reset_game4(json_data)
        json_data = reset_game5(json_data)
        with open("ltdle_data/ltdle.json", "w") as f:
            json.dump(json_data, f, indent=2)
            f.close()
        return new_season
    else:
        return False

class ScheduledTasks(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.scheduled_reset.start()
        self.game_update.start()

    def cog_unload(self):
        self.scheduled_reset.cancel()
        self.game_update.cancel()

    @tasks.loop(time=task_time)
    async def scheduled_reset(self):
        try:
            print("Starting scheduled reset...")
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                update = await loop.run_in_executor(pool, reset)
                pool.shutdown()
            if not update:
                print("No reset required now.")
                return
            await ltdle_notify(self, update)
        except Exception:
            traceback.print_exc()
    
    @tasks.loop(time=util.task_times1)
    async def game_update(self):
        try:
            # games update
            if platform.system() != "Windows":
                with open("Files/json/discord_channels.json", "r") as f:
                    discord_channels = json.load(f)
                    f.close()
                loop = asyncio.get_running_loop()
                with concurrent.futures.ProcessPoolExecutor() as pool:
                    ladder_update = await loop.run_in_executor(pool, functools.partial(legion_api.get_recent_games, 100))
                    pool.shutdown()
                guild = self.client.get_guild(discord_channels["drachbot_game"][0])
                channel = guild.get_channel(discord_channels["drachbot_game"][1])
                message = await channel.send(embed=ladder_update)
        except Exception:
            traceback.print_exc()
        
async def setup(bot: commands.Bot):
    await bot.add_cog(ScheduledTasks(bot))