import asyncio
import concurrent.futures
import datetime
import functools
import json
import os
import pathlib
import random
import traceback
from datetime import datetime, timedelta
from pathlib import Path
import discord
import discord_timestamps
from discord import app_commands, ui
from discord.ext import commands
from discord_timestamps import TimestampType
import util
import platform
import difflib


def random_color():
    return random.randrange(0, 2 ** 24)


if platform.system() == "Linux":
    shared_folder = "/shared/Images/"
else:
    shared_folder = "shared/Images/"


def update_user_data(session, name):
    with open("ltdle_data/" + name + "/data.json", "w") as f:
        json.dump(session, f)
        f.close()


def check_if_played_today(name: str, game: int):
    try:
        date_now = datetime.now()
        with open("ltdle_data/" + name + "/data.json", "r") as f:
            session = json.load(f)
            f.close()
        with open("ltdle_data/ltdle.json", "r") as f:
            ltdle_data = json.load(f)
            f.close()
        match game:
            case 1:
                playedstring = "You already played todays **Guess The Unit**:question:, next reset is "
            case 2:
                playedstring = "You already played todays **Guess The Leak**:grimacing:, next reset is "
            case 3:
                playedstring = "You already played todays **Guess The Elo**:gem:, next reset is "
            
        if datetime.strptime(session["game"+str(game)]["last_played"], "%m/%d/%Y") + timedelta(days=1) < datetime.strptime(ltdle_data["next_reset"], "%m/%d/%Y"):
            session["game"+str(game)]["last_played"] = date_now.strftime("%m/%d/%Y")
            session["game"+str(game)]["game_finished"] = False
            session["game"+str(game)]["guesses"] = []
            if game == 2 or game == 3:
                session["game"+str(game)]["image"] = 0
            update_user_data(session, session["name"])
            return session
        elif not session["game"+str(game)]["game_finished"]:
            return session
        else:
            mod_date = datetime.strptime(ltdle_data["next_reset"], "%m/%d/%Y").timestamp()
            timestamp = discord_timestamps.format_timestamp(mod_date, TimestampType.RELATIVE)
            return playedstring + timestamp
    except Exception:
        traceback.print_exc()


def ltdle(session: dict, ltdle_data: dict, game: int, input = ""):
    color = random_color()
    date_now = datetime.now()
    match game:
        case 0:
            embed = discord.Embed(color=color, title=":exploding_head: **LEGIONTDLE** :brain:", description="**Select a game!\nUsing the buttons below.**\n*Guess The Unit includes:\nFighters, Mercs and Waves*")
            embed.set_thumbnail(url="https://overlay.drachbot.site/ltdle/guesstheunit.png")
            embed.set_author(name="Drachbot presents", icon_url="https://overlay.drachbot.site/favicon.ico")
            return embed
        case 1:
            if "game2" not in session:
                session["game1"]["score"] = session["score"]
                session["game1"]["games_played"] = session["games_played"]
                session["game2"] = {"games_played": 0, "score": 0, "last_played": date_now.strftime("%m/%d/%Y"), "image": 0, "game_finished": False, "guesses": []}
                update_user_data(session, session["name"])
            return ltdle_game1(session, input, ltdle_data)
        case 2:
            if "game2" not in session:
                session["game1"]["score"] = session["score"]
                session["game1"]["games_played"] = session["games_played"]
                session["game2"] = {"games_played": 0, "score": 0, "last_played": date_now.strftime("%m/%d/%Y"), "image": 0, "game_finished": False, "guesses": []}
                update_user_data(session, session["name"])
            return ltdle_game2(session, input, ltdle_data)
        case 3:
            if "game3" not in session:
                session["game3"] = {"games_played": 0, "score": 0, "last_played": date_now.strftime("%m/%d/%Y"), "image": 0, "game_finished": False, "guesses": []}
                update_user_data(session, session["name"])
            return ltdle_game3(session, input, ltdle_data)
            

def ltdle_leaderboard(daily, avg):
    color = random_color()
    player_data_list = os.listdir("ltdle_data")
    scores = []
    for player in player_data_list:
        if player.endswith(".json"): continue
        with open("ltdle_data/"+player+"/data.json", "r") as f:
            p_data = json.load(f)
            f.close()
        if daily:
            daily_score1 = 0
            daily_score2 = 0
            daily_score3 = 0
            with open("ltdle_data/ltdle.json", "r") as f:
                ltdle_data = json.load(f)
                f.close()
            if datetime.strptime(p_data["game1"]["last_played"], "%m/%d/%Y") < datetime.strptime(ltdle_data["next_reset"], "%m/%d/%Y"):
                if datetime.strptime(p_data["game1"]["last_played"], "%m/%d/%Y") == datetime.strptime(ltdle_data["next_reset"], "%m/%d/%Y")-timedelta(days=1):
                    if p_data["game1"]["game_finished"] == True:
                        daily_score1 = 11-len(p_data["game1"]["guesses"])
                    else:
                        daily_score1 = 0
            else:
                daily_score1 = 0
            try:
                if datetime.strptime(p_data["game2"]["last_played"], "%m/%d/%Y") < datetime.strptime(ltdle_data["next_reset"], "%m/%d/%Y"):
                    if datetime.strptime(p_data["game2"]["last_played"], "%m/%d/%Y") == datetime.strptime(ltdle_data["next_reset"], "%m/%d/%Y") - timedelta(days=1):
                            if p_data["game2"]["game_finished"] == True:
                                daily_score2 = round(10-abs(ltdle_data["game_2_selected_leak"][0][3]-p_data["game2"]["guesses"][0])/10)
                            else:
                                daily_score2 = 0
                else:
                    daily_score2 = 0
            except Exception:
                daily_score2 = 0
                pass
            try:
                if datetime.strptime(p_data["game3"]["last_played"], "%m/%d/%Y") < datetime.strptime(ltdle_data["next_reset"], "%m/%d/%Y"):
                    if datetime.strptime(p_data["game3"]["last_played"], "%m/%d/%Y") == datetime.strptime(ltdle_data["next_reset"], "%m/%d/%Y") - timedelta(days=1):
                            if p_data["game3"]["game_finished"] == True:
                                daily_score3 = round(10-abs(ltdle_data["game_3_selected_game"][2]-p_data["game3"]["guesses"][0])/75)
                            else:
                                daily_score3 = 0
                else:
                    daily_score3 = 0
            except Exception:
                daily_score3 = 0
                pass
            scores.append((p_data["name"].capitalize().replace("_", ""), daily_score1, daily_score2, daily_score3))
        else:
            try: avg_pts = p_data["score"]/p_data["games_played"]
            except ZeroDivisionError: avg_pts = 0
            scores.append((p_data["name"].capitalize().replace("_", ""), p_data["score"], p_data["games_played"], avg_pts))
            
    if avg:
        scores = sorted(scores, key=lambda x: x[3], reverse=True)
    elif daily:
        scores = sorted(scores, key=lambda x: x[1]+x[2]+x[3], reverse=True)
    else:
        scores = sorted(scores, key=lambda x: x[1], reverse=True)
    output = ""
    for index, pscore in enumerate(scores):
        ranked_emote = ""
        if index == 10: break
        if index == 0:
            ranked_emote = util.get_ranked_emote(2800)
        elif 1 <= index <= 3:
            ranked_emote = util.get_ranked_emote(2600)
        elif 4 <= index <= 6:
            ranked_emote = util.get_ranked_emote(2400)
        else:
            ranked_emote = util.get_ranked_emote(2200)
        if daily:
            output += ranked_emote+" "+pscore[0] + ": " + str(pscore[1]+pscore[2]+pscore[3]) + "pts ("+str(pscore[1])+", "+str(pscore[2]) +", "+str(pscore[3])+ ")\n"
        else:
            output += ranked_emote+" "+pscore[0] + ": " + str(pscore[1]) + "pts, Games: "+str(pscore[2])+" ("+str(round(pscore[1]/pscore[2],1))+"pts avg)\n"
    if daily:
        title = "Legiontdle Daily Leaderboard:"
    elif avg:
        title = "Legiontdle Avg Leaderboard:"
    else:
        title = "Legiontdle Leaderboard:"
    embed = discord.Embed(color=color, title=title, description="**"+output+"**")
    embed.set_author(name="Drachbot", icon_url="https://overlay.drachbot.site/favicon.ico")
    return embed


def ltdle_profile(player, avatar):
    color = random_color()
    try:
        with open("ltdle_data/" + player + "/data.json", "r") as f:
            p_data = json.load(f)
            f.close()
    except FileNotFoundError:
        return "No Legiontdle profile found for "+player
    if p_data["games_played"] == 0:
        return "No games played."
    embed = discord.Embed(color=color, title="Legiontdle Profile")
    embed.add_field(name="Total stats:", value="Games played: " +str(p_data["games_played"])+
                                            "\nPoints: "+str(p_data["score"])+
                                            "\nAvg: "+str(round(p_data["score"]/p_data["games_played"],1))+" points", inline=True)
    try:
        embed.add_field(name="Guess The Unit:question:", value="Games played: " +str(p_data["game1"]["games_played"])+
                                                    "\nPoints: "+str(p_data["game1"]["score"])+
                                                    "\nAvg: "+str(round(p_data["game1"]["score"]/p_data["game1"]["games_played"],1))+" points", inline=True)
    except Exception:
        pass
    try:
        embed.add_field(name="Guess The Leak:grimacing:", value="Games played: " + str(p_data["game2"]["games_played"]) +
                                                      "\nPoints: " + str(p_data["game2"]["score"]) +
                                                      "\nAvg: " + str(round(p_data["game2"]["score"] / p_data["game2"]["games_played"], 1)) + " points", inline=True)
    except Exception:
        pass
    try:
        embed.add_field(name="Guess The Elo:gem:", value="Games played: " + str(p_data["game3"]["games_played"]) +
                                                                "\nPoints: " + str(p_data["game3"]["score"]) +
                                                                "\nAvg: " + str(round(p_data["game3"]["score"] / p_data["game3"]["games_played"], 1)) + " points", inline=True)
    except Exception:
        pass
    embed.set_author(name=player.capitalize()+"'s", icon_url=avatar)
    return embed


def ltdle_game1(session: dict, text_input: str, ltdle_data: dict):
    color = random_color()
    date_now = datetime.now()
    session["game1"]["last_played"] = date_now.strftime("%m/%d/%Y")
    with open('Files/json/units.json', 'r') as f:
        units_json = json.load(f)
        f.close()
    if text_input in util.slang:
        text_input = util.slang.get(text_input)
    unit_dict = {}
    for u_js in units_json:
        if u_js["categoryClass"] == "Special" or u_js["categoryClass"] == "Passive":
            continue
        string = u_js["unitId"]
        string = string.replace('_', ' ')
        string = string.replace(' unit id', '')
        if string == "skyfish": string = "metaldragon"
        unit_dict[string] = u_js
    if text_input.lower() not in unit_dict:
        close_matches = difflib.get_close_matches(text_input.lower(), list(unit_dict.keys()), cutoff=0.8)
        print(close_matches)
        if len(close_matches) > 0:
            text_input = close_matches[0]
            unit_data = unit_dict[close_matches[0]]
        else:
            return text_input + " unit not found."
    else:
        unit_data = unit_dict[text_input]

    if " " in text_input:
        text_input = text_input.split(" ")
        new_name = ""
        for icon_string in text_input:
            new_name += icon_string.capitalize()
    else:
        new_name = text_input.capitalize()
    output = []
    output2 = ""
    correct_count = 0
    def correct_output(input):
        return ":green_square:**" + input + "** "
    def false_output(input):
        return ":red_square:" + input + " "
    #attack
    if unit_data["attackType"] == ltdle_data["game_1_selected_unit"]["attackType"]:
        output.append(correct_output(unit_data["attackType"]))
        output2 += ":green_square:"
        correct_count += 1
    else:
        output.append(false_output(unit_data["attackType"]))
        output2 += ":red_square:"
    #armor
    if unit_data["armorType"] == ltdle_data["game_1_selected_unit"]["armorType"]:
        output.append(correct_output(unit_data["armorType"]))
        output2 += ":green_square:"
        correct_count += 1
    else:
        output.append(false_output(unit_data["armorType"]))
        output2 += ":red_square:"
    #range
    if unit_data["attackMode"] == ltdle_data["game_1_selected_unit"]["attackMode"]:
        output.append(correct_output(unit_data["attackMode"]))
        output2 += ":green_square:"
        correct_count += 1
    else:
        output.append(false_output(unit_data["attackMode"]))
        output2 += ":red_square:"
    #legion
    if unit_data["legionId"].split("_")[0] == "nether":
        lstring = "Merc"
    elif unit_data["legionId"].split("_")[0] == "creature":
        lstring = "Wave"
    else:
        lstring = unit_data["legionId"].split("_")[0].capitalize()
    if unit_data["legionId"] == ltdle_data["game_1_selected_unit"]["legionId"]:
        output.append(correct_output(lstring))
        output2 += ":green_square:"
        correct_count += 1
    else:
        output.append(false_output(lstring))
        output2 += ":red_square:"
    #upgraded
    unit_upgraded = unit_data["sortOrder"].split(".")[1].endswith("U")
    ltdle_unit_upgraded = ltdle_data["game_1_selected_unit"]["sortOrder"].split(".")[1].endswith("U")
    if lstring == "Merc":
        ustring = "Merc unit"
    elif lstring == "Wave":
        ustring = "Wave unit"
    elif unit_upgraded:
        ustring = "Upgraded unit"
    else:
        ustring = "Base unit"
    unit_type = ltdle_data["game_1_selected_unit"]["legionId"].split("_")[0]
    match ustring:
        case "Base unit" | "Upgraded unit":
            if (unit_upgraded == ltdle_unit_upgraded) and (unit_type != "creature" and unit_type != "nether"):
                output.append(correct_output(ustring))
                output2 += ":green_square:"
                correct_count += 1
            else:
                output.append(false_output(ustring))
                output2 += ":red_square:"
        case "Merc unit":
            if unit_type == "nether":
                output.append(correct_output(ustring))
                output2 += ":green_square:"
                correct_count += 1
            else:
                output.append(false_output(ustring))
                output2 += ":red_square:"
        case "Wave unit":
            if unit_type == "creature":
                output.append(correct_output(ustring))
                output2 += ":green_square:"
                correct_count += 1
            else:
                output.append(false_output(ustring))
                output2 += ":red_square:"
    if unit_data["unitId"] == ltdle_data["game_1_selected_unit"]["unitId"]:
        unit_name_string = " :green_square:"
        correct_count += 1
    else:
        unit_name_string = " :red_square:"
    def create_embed(end_string):
        embed = discord.Embed(color=color, title="Guess " + str(len(session["game1"]["guesses"])) + ": " + new_name+unit_name_string, description="\n".join(output)+"\n\n"+end_string)
        embed.set_thumbnail(url="https://cdn.legiontd2.com/icons/" + new_name + ".png")
        return embed
    session["game1"]["guesses"].append(output2+" "+new_name.replace("PriestessOfTheAbyss", "PotA"))
    if len(session["game1"]["guesses"]) == 10:
        session["game1"]["game_finished"] = True
        session["games_played"] += 1
        session["game1"]["games_played"] += 1
        if correct_count < 6:
            mod_date = datetime.strptime(ltdle_data["next_reset"], "%m/%d/%Y").timestamp()
            timestamp = discord_timestamps.format_timestamp(mod_date, TimestampType.RELATIVE)
            embed = create_embed("You lost :frowning:. Try again next time "+timestamp+"\nYour guess history:\n" + "\n".join(session["game1"]["guesses"]))
            update_user_data(session, session["name"])
            return embed
    if correct_count == 6:
        print(session["name"]+ " found the right unit!")
        session["game1"]["game_finished"] = True
        session["game1"]["score"] += 11 - len(session["game1"]["guesses"])
        session["score"] += 11 - len(session["game1"]["guesses"])
        embed = create_embed("**You guessed the correct unit! Yay!**(+"+str(11 - len(session["game1"]["guesses"]))+" points)\nYour guess history:\n"+"\n".join(session["game1"]["guesses"]))
        session["games_played"] += 1
        session["game1"]["games_played"] += 1
        update_user_data(session, session["name"])
        return [embed]
    else:
        embed = create_embed("**Try another unit**")
        update_user_data(session, session["name"])
        return embed


def ltdle_game2(session: dict, input: int, ltdle_data: dict):
    color = random_color()
    image_index = session["game2"]["image"]
    def embed1(image):
        embed = discord.Embed(color=color, title="Guess The Leak :grimacing:", description="Enter a leak amount. (Whole Number)", url="https://overlay.drachbot.site"+image.replace("shared", ""))
        file = discord.File(image, filename=image.split("/")[-1])
        embed.set_image(url="attachment://"+image.split("/")[-1])
        return [file, embed]
    def embed2(image, points):
        embed = discord.Embed(color=color, title="Your guess: "+str(input)+"%", url="https://overlay.drachbot.site"+image.replace("shared", ""))
        file = discord.File(image, filename=image.split("/")[-1])
        embed.set_image(url="attachment://"+image.split("/")[-1])
        embed.add_field(name="You got "+str(points)+" points!", value="")
        return [file, embed, ""]
    if image_index == 0:
        return embed1(ltdle_data["game_2_selected_leak"][0][4])
    else:
        points = round(10-abs(ltdle_data["game_2_selected_leak"][0][3]-input)/10)
        if points < 0: points = 0
        session["game2"]["image"] += 1
        session["score"] += points
        session["game2"]["score"] += points
        session["games_played"] += 1
        session["game2"]["games_played"] += 1
        session["game2"]["game_finished"] = True
        session["game2"]["guesses"].append(input)
        update_user_data(session, session["name"])
        print(session["name"]+ " played guess the leak.")
        return embed2(ltdle_data["game_2_selected_leak"][0][4].replace(".png", "_covered.png"), points)


def ltdle_game3(session: dict, input: int, ltdle_data: dict):
    color = random_color()
    image_index = session["game3"]["image"]
    def embed1(image):
        embed = discord.Embed(color=color, title="Guess The Elo :gem:", description="Guess the average elo of this game. (1600-2800 range:bangbang:)", url=ltdle_data["game_3_selected_game"][0])
        file = discord.File(image, filename=image.split("/")[-1])
        embed.set_image(url="attachment://"+image.split("/")[-1])
        return [file, embed]
    def embed2(image, points):
        embed = discord.Embed(color=color, title="Guessed elo: "+str(input)+util.get_ranked_emote(input)+"\nActual elo: "+str(ltdle_data["game_3_selected_game"][2])+util.get_ranked_emote(ltdle_data["game_3_selected_game"][2]), url=ltdle_data["game_3_selected_game"][1])
        file = discord.File(image, filename=image.split("/")[-1])
        embed.set_image(url="attachment://"+image.split("/")[-1])
        embed.add_field(name="You got "+str(points)+" points!", value="")
        return [file, embed, ""]
    if image_index == 0:
        return embed1(shared_folder+ltdle_data["game_3_selected_game"][0].split("/")[-1])
    else:
        points = round(10-abs(ltdle_data["game_3_selected_game"][2]-input)/75)
        if points < 0: points = 0
        session["game3"]["image"] += 1
        session["score"] += points
        session["game3"]["score"] += points
        session["games_played"] += 1
        session["game3"]["games_played"] += 1
        session["game3"]["game_finished"] = True
        session["game3"]["guesses"].append(input)
        update_user_data(session, session["name"])
        print(session["name"]+ " played guess the elo.")
        return embed2(shared_folder+ltdle_data["game_3_selected_game"][1].split("/")[-1], points)
        

class UnitInput(ui.Modal, title='Enter a unit!'):
    answer = ui.TextInput(label='Unit', style=discord.TextStyle.short)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                path = str(pathlib.Path(__file__).parent.parent.resolve()) + "/ltdle_data/" + interaction.user.name
                with open(path + "/data.json", "r") as f:
                    data = json.load(f)
                    f.close()
                with open("ltdle_data/ltdle.json", "r") as f:
                    ltdle_data = json.load(f)
                    f.close()
                response = await loop.run_in_executor(pool, functools.partial(ltdle, data, ltdle_data, 1, input=self.answer.value))
                pool.shutdown()
                if type(response) == discord.Embed:
                    await interaction.channel.send(embed=response, view=ModalButton())
                elif type(response) == list:
                    await interaction.channel.send(embed=response[0])
                else:
                    await interaction.channel.send(response)
        except Exception:
            traceback.print_exc()


class LeakInput(ui.Modal, title='Enter a Leak!'):
    answer = ui.TextInput(label='Leak (Whole Number without %)', style=discord.TextStyle.short, max_length=3)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            input = int(self.answer.value)
        except Exception:
            await interaction.followup.send("Invalid input, try again.")
            return
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                path = str(pathlib.Path(__file__).parent.parent.resolve()) + "/ltdle_data/" + interaction.user.name
                with open(path + "/data.json", "r") as f:
                    data = json.load(f)
                    f.close()
                with open("ltdle_data/ltdle.json", "r") as f:
                    ltdle_data = json.load(f)
                    f.close()
                data["game2"]["image"] += 1
                response = await loop.run_in_executor(pool, functools.partial(ltdle, data, ltdle_data, 2, input=input))
                pool.shutdown()
                if type(response) == list:
                    await interaction.channel.send(file=response[0], embed=response[1])
                else:
                    await interaction.channel.send(response)
        except Exception:
            traceback.print_exc()


class EloInput(ui.Modal, title='Enter a Elo!'):
    answer = ui.TextInput(label='Elo (1600-2800)', style=discord.TextStyle.short, max_length=4)
    
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        try:
            input = int(self.answer.value)
            if input<1600 or input>2800:
                await interaction.followup.send("Elo range is **1600-2800**, try again.")
                return
        except Exception:
            await interaction.followup.send("Invalid input, try again.")
            return
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                path = str(pathlib.Path(__file__).parent.parent.resolve()) + "/ltdle_data/" + interaction.user.name
                with open(path + "/data.json", "r") as f:
                    data = json.load(f)
                    f.close()
                with open("ltdle_data/ltdle.json", "r") as f:
                    ltdle_data = json.load(f)
                    f.close()
                data["game3"]["image"] += 1
                response = await loop.run_in_executor(pool, functools.partial(ltdle, data, ltdle_data, 3, input=input))
                pool.shutdown()
                if type(response) == list:
                    await interaction.channel.send(file=response[0], embed=response[1])
                else:
                    await interaction.channel.send(response)
        except Exception:
            traceback.print_exc()


class ModalButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label='Enter unit', style=discord.ButtonStyle.green, custom_id='persistent_view:modal')
    async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        played_check = check_if_played_today(interaction.user.name, 1)
        if type(played_check) == type(dict()):
            try:
                await interaction.response.send_modal(UnitInput())
            except Exception:
                traceback.print_exc()
        else:
            await interaction.response.defer()
            await interaction.channel.send(played_check)
            return
            
            
class ModalLeakButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label='Enter Leak', style=discord.ButtonStyle.green, custom_id='persistent_view:modalLeak')
    async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        played_check = check_if_played_today(interaction.user.name, 2)
        if type(played_check) == type(dict()):
            try:
                await interaction.response.send_modal(LeakInput())
            except Exception:
                traceback.print_exc()
        else:
            await interaction.response.defer()
            await interaction.channel.send(played_check)
            return


class ModalEloButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label='Enter Elo', style=discord.ButtonStyle.green, custom_id='persistent_view:modalelo')
    async def callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        played_check = check_if_played_today(interaction.user.name, 3)
        if type(played_check) == type(dict()):
            try:
                await interaction.response.send_modal(EloInput())
            except Exception:
                traceback.print_exc()
        else:
            await interaction.response.defer()
            await interaction.channel.send(played_check)
            return
            

class GameSelectionButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Guess The Unit', style=discord.ButtonStyle.grey, custom_id='persistent_view:Game1', emoji="❓", row=1)
    async def callback1(self, interaction: discord.Interaction, button: discord.ui.Button):
        with open("ltdle_data/ltdle.json", "r") as f:
            ltdle_data = json.load(f)
            f.close()
        if not ltdle_data["game_1_selected_unit"]:
            await interaction.response.defer()
            await interaction.channel.send("This game is currently disabled.")
            return
        played_check = check_if_played_today(interaction.user.name, 1)
        if type(played_check) == type(dict()):
            try:
                await interaction.response.send_modal(UnitInput())
            except Exception:
                traceback.print_exc()
        else:
            await interaction.response.defer()
            await interaction.channel.send(played_check)
            return
    
    @discord.ui.button(label='Guess The Leak', style=discord.ButtonStyle.grey, custom_id='persistent_view:Game2', emoji="😬",row=1)
    async def callback2(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                path = str(pathlib.Path(__file__).parent.parent.resolve()) + "/ltdle_data/" + interaction.user.name
                with open(path + "/data.json", "r") as f:
                    data = json.load(f)
                    f.close()
                with open("ltdle_data/ltdle.json", "r") as f:
                    ltdle_data = json.load(f)
                    f.close()
                if not ltdle_data["game_2_selected_leak"]:
                    await interaction.channel.send("This game is currently disabled.")
                    return
                played_check = check_if_played_today(interaction.user.name, 2)
                if type(played_check) == type(dict()):
                    data = played_check
                    pass
                else:
                    await interaction.channel.send(played_check)
                    return
                response = await loop.run_in_executor(pool, functools.partial(ltdle, data, ltdle_data, 2))
                pool.shutdown()
                if type(response) == list:
                    if len(response) == 2:
                        await interaction.channel.send(file=response[0], embed=response[1], view=ModalLeakButton())
                    else:
                        await interaction.channel.send(file=response[0], embed=response[1])
                else:
                    await interaction.channel.send(response)
        except Exception:
            traceback.print_exc()
    
    @discord.ui.button(label='Guess The Elo', style=discord.ButtonStyle.grey, custom_id='persistent_view:Game3', emoji="💎",row=2)
    async def callback3(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        try:
            loop = asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                path = str(pathlib.Path(__file__).parent.parent.resolve()) + "/ltdle_data/" + interaction.user.name
                with open(path + "/data.json", "r") as f:
                    data = json.load(f)
                    f.close()
                with open("ltdle_data/ltdle.json", "r") as f:
                    ltdle_data = json.load(f)
                    f.close()
                if not ltdle_data["game_3_selected_game"]:
                    await interaction.channel.send("This game is currently disabled.")
                    return
                else:
                    played_check = check_if_played_today(interaction.user.name, 3)
                    if type(played_check) == type(dict()):
                        data = played_check
                    else:
                        await interaction.channel.send(played_check)
                        return
                    response = await loop.run_in_executor(pool, functools.partial(ltdle, data, ltdle_data, 3))
                    pool.shutdown()
                    if type(response) == list:
                        if len(response) == 2:
                            await interaction.channel.send(file=response[0], embed=response[1], view=ModalEloButton())
                        else:
                            await interaction.channel.send(file=response[0], embed=response[1])
                    else:
                        await interaction.channel.send(response)
        except Exception:
            traceback.print_exc()


class Legiontdle(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
    
    @app_commands.command(name="legiontdle", description="Legion themed Wordle-type game.")
    async def legiontdle(self, interaction: discord.Interaction):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            try:
                if interaction.guild != None:
                    await interaction.response.send_message("This command only works in DMs with Drachbot.", ephemeral=True)
                    return
                await interaction.response.defer(ephemeral=False, thinking=True)
                path = str(pathlib.Path(__file__).parent.parent.resolve()) + "/ltdle_data/" + interaction.user.name
                if not Path(Path(str(path))).is_dir():
                    print(interaction.user.name + ' ltdle profile not found, creating new folder...')
                    Path(str(path)).mkdir(parents=True, exist_ok=True)
                    with open(path + "/data.json", "w") as f:
                        date_now = datetime.now()
                        data = {"name": interaction.user.name, "score": 0, "games_played": 0, "game1": {"games_played": 0, "score": 0, "last_played": date_now.strftime("%m/%d/%Y"), "game_finished": False, "guesses": []},
                                "game2": {"games_played": 0, "score": 0, "last_played": date_now.strftime("%m/%d/%Y"), "image": 0, "game_finished": False, "guesses": []},
                                "game3": {"games_played": 0, "score": 0, "last_played": date_now.strftime("%m/%d/%Y"), "image": 0, "game_finished": False, "guesses": []}}
                        json.dump(data, f)
                        f.close()
                else:
                    with open(path + "/data.json", "r") as f:
                        data = json.load(f)
                        f.close()
                with open("ltdle_data/ltdle.json", "r") as f:
                    ltdle_data = json.load(f)
                    f.close()
                response = await loop.run_in_executor(pool, functools.partial(ltdle, data, ltdle_data, 0))
                pool.shutdown()
                if type(response) == discord.Embed:
                    await interaction.followup.send(embed=response, view=GameSelectionButtons())
                else:
                    await interaction.followup.send(response)
            except Exception:
                print("/" + interaction.command.name + " failed. args: " + str(interaction.data.values()))
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")
    
    @app_commands.command(name="ltdle-stats", description="Stats for Legiontdle.")
    @app_commands.describe(option="Select an option.", name="Only for profile, has to be actual discord name, not display name.")
    @app_commands.choices(option=[
        discord.app_commands.Choice(name='Leaderboard', value='Leaderboard'),
        discord.app_commands.Choice(name='Avg Leaderboard', value='Avg Leaderboard'),
        discord.app_commands.Choice(name='Daily Leaderboard', value='Daily Leaderboard'),
        discord.app_commands.Choice(name='Profile', value='Profile')
    ])
    async def legiontdle_stats(self, interaction: discord.Interaction, option: discord.app_commands.Choice[str], name: discord.User=None):
        loop = asyncio.get_running_loop()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            try:
                await interaction.response.defer(ephemeral=False, thinking=True)
                try:
                    option = option.value
                except AttributeError:
                    pass
                match option:
                    case "Leaderboard":
                        response = await loop.run_in_executor(pool, functools.partial(ltdle_leaderboard, False, False))
                        pool.shutdown()
                        if type(response) == discord.Embed:
                            await interaction.followup.send(embed=response)
                        else:
                            await interaction.followup.send(response)
                        return
                    case "Avg Leaderboard":
                        response = await loop.run_in_executor(pool, functools.partial(ltdle_leaderboard, False, True))
                        pool.shutdown()
                        if type(response) == discord.Embed:
                            await interaction.followup.send(embed=response)
                        else:
                            await interaction.followup.send(response)
                        return
                    case "Daily Leaderboard":
                        response = await loop.run_in_executor(pool, functools.partial(ltdle_leaderboard, True, False))
                        pool.shutdown()
                        if type(response) == discord.Embed:
                            await interaction.followup.send(embed=response)
                        else:
                            await interaction.followup.send(response)
                        return
                    case "Profile":
                        if name != None and name.name != interaction.user.name:
                            avatar = name.avatar
                            username = name.name
                        else:
                            username = interaction.user.name
                            avatar = interaction.user.avatar
                        if avatar != None:
                            avatar = avatar.url
                        else:
                            avatar = "https://cdn.discordapp.com/embed/avatars/0.png"
                        response = await loop.run_in_executor(pool, functools.partial(ltdle_profile, username, avatar))
                        pool.shutdown()
                        if type(response) == discord.Embed:
                            await interaction.followup.send(embed=response)
                        else:
                            await interaction.followup.send(response)
                        return
            except Exception:
                print("/" + interaction.command.name + " failed. args: " + str(interaction.data.values()))
                traceback.print_exc()
                await interaction.followup.send("Bot error :sob:")


async def setup(bot: commands.Bot):
    await bot.add_cog(Legiontdle(bot))
    