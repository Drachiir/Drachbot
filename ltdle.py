import json
import os

import responses
import random
import discord
import datetime
from datetime import datetime, timedelta, timezone
import discord_timestamps
from discord_timestamps import TimestampType
from difflib import SequenceMatcher

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def ltdle(session: int, input: str, ltdle_data: dict):
    date_now = datetime.now()
    if not session["game1"]["game_finished"]:
        return ltdle_game1(session, input, ltdle_data)
    elif datetime.strptime(session["game1"]["last_played"], "%m/%d/%Y")+timedelta(days=1) < datetime.strptime(ltdle_data["next_reset"], "%m/%d/%Y"):
        session["game1"]["last_played"] = date_now.strftime("%m/%d/%Y")
        session["game1"]["game_finished"] = False
        session["game1"]["game_state"] = 0
        session["game1"]["guesses"] = []
        with open("ltdle_data/"+session["name"]+"/data.json", "w") as f:
            json.dump(session, f)
            f.close()
        return ltdle_game1(session, input, ltdle_data)
    else:
        mod_date = datetime.strptime(ltdle_data["next_reset"], "%m/%d/%Y").timestamp()
        timestamp = discord_timestamps.format_timestamp(mod_date, TimestampType.RELATIVE)
        return "You already played todays Legiondle, next reset is "+timestamp+"."

def ltdle_leaderboard():
    color = random.randrange(0, 2 ** 24)
    player_data_list = os.listdir("ltdle_data")
    scores = []
    for player in player_data_list:
        if player.endswith(".json"): continue
        with open("ltdle_data/"+player+"/data.json", "r") as f:
            p_data = json.load(f)
            f.close()
        scores.append((p_data["name"].capitalize(), p_data["score"]))
    scores = sorted(scores, key=lambda x: x[1], reverse=True)
    output = ""
    for index, pscore in enumerate(scores):
        if index == 10: break
        output += pscore[0] + " " + str(pscore[1]) + "pts "
        if index == 0:
            output += responses.get_ranked_emote(2800) + "\n"
        elif 1 <= index <= 3:
            output += responses.get_ranked_emote(2600) + "\n"
        elif 4 <= index <= 6:
            output += responses.get_ranked_emote(2400) + "\n"
        else:
            output += responses.get_ranked_emote(2200) + "\n"
    embed = discord.Embed(color=color, title="Legiondle Leaderboard", description="**"+output+"**")
    embed.set_author(name="Drachbot", icon_url="https://overlay.drachbot.site/favicon.ico")
    return embed
        
def ltdle_game1(session: int, text_input: str, ltdle_data: dict):
    color = random.randrange(0, 2 ** 24)
    def update_user_data():
        with open("ltdle_data/" + session["name"] + "/data.json", "w") as f:
            json.dump(session, f)
            f.close()
    match session["game1"]["game_state"]:
        case 0:
            embed = discord.Embed(color=color, description=":exploding_head: **LEGIONDLE** :brain:\n**Standard mode!**")
            embed.set_thumbnail(url="https://overlay.drachbot.site/ltdle/guesstheunit.png")
            embed.set_author(name="Drachbot presents", icon_url="https://overlay.drachbot.site/favicon.ico")
            embed.add_field(name="", value="**Enter any unit! (Including waves and mercs!)**\nUsing the /legiondle input")
            date_now = datetime.now()
            session["game1"]["last_played"] = date_now.strftime("%m/%d/%Y")
            session["game1"]["game_state"] = 1
            update_user_data()
            return embed
        case 1:
            with open('Files/units.json', 'r') as f:
                units_json = json.load(f)
                f.close()
            if text_input in responses.slang:
                text_input = responses.slang.get(text_input)
            for u_js in units_json:
                string = u_js["unitId"]
                string = string.replace('_', ' ')
                string = string.replace(' unit id', '')
                if string == "skyfish": string = "metaldragon"
                if string == text_input or similar(string, text_input) > 0.8:
                    text_input = string
                    unit_data = u_js
                    break
            else:
                return "Unit " + text_input + " not found."
            if " " in text_input:
                text_input = text_input.split(" ")
                new_name = ""
                for icon_string in text_input:
                    new_name += icon_string.capitalize()
            else:
                new_name = text_input.capitalize()
            output = ""
            output2 = ""
            correct_count = 0
            # name
            if unit_data["unitId"] == ltdle_data["game_1_selected_unit"]["unitId"]:
                embed = discord.Embed(color=color, title="Guess "+str(len(session["game1"]["guesses"])+1)+": "+new_name + " :green_square:")
                correct_count += 1
            else:
                embed = discord.Embed(color=color, title="Guess "+str(len(session["game1"]["guesses"])+1)+": "+new_name+ " :red_square:")
            embed.set_thumbnail(url="https://cdn.legiontd2.com/splashes/" + new_name + ".png")
            # attack
            if unit_data["attackType"] == ltdle_data["game_1_selected_unit"]["attackType"]:
                output += unit_data["attackType"] + ":green_square:"
                output2 += ":green_square:"
                correct_count += 1
            else:
                output += unit_data["attackType"] + ":red_square:"
                output2 += ":red_square:"
            #armor
            if unit_data["armorType"] == ltdle_data["game_1_selected_unit"]["armorType"]:
                output += unit_data["armorType"] + ":green_square:"
                output2 += ":green_square:"
                correct_count += 1
            else:
                output += unit_data["armorType"] + ":red_square:"
                output2 += ":red_square:"
            #range
            if unit_data["attackMode"] == ltdle_data["game_1_selected_unit"]["attackMode"]:
                output += unit_data["attackMode"] + ":green_square:"
                output2 += ":green_square:"
                correct_count += 1
            else:
                output += unit_data["attackMode"] + ":red_square:"
                output2 += ":red_square:"
            #legion
            if unit_data["legionId"].split("_")[0] == "nether":
                lstring = "Merc"
            elif unit_data["legionId"].split("_")[0] == "creature":
                lstring = "Wave"
            else:
                lstring = unit_data["legionId"].split("_")[0].capitalize()
            if unit_data["legionId"] == ltdle_data["game_1_selected_unit"]["legionId"]:
                output += lstring + ":green_square:"
                output2 += ":green_square:"
                correct_count += 1
            else:
                output += lstring + ":red_square:"
                output2 += ":red_square:"
            #upgraded
            if lstring == "Merc":
                ustring = "Merc unit"
            elif lstring == "Wave":
                ustring = "Wave unit"
            elif len(unit_data["upgradesFrom"]) == 0:
                ustring = "Base unit"
            else:
                ustring = "Upgraded unit"
            unit_type = ltdle_data["game_1_selected_unit"]["legionId"].split("_")[0]
            match ustring:
                case "Base unit" | "Upgraded unit":
                    if len(unit_data["upgradesFrom"]) == len(ltdle_data["game_1_selected_unit"]["upgradesFrom"]) and (unit_type != "creature" and unit_type != "nether"):
                        output += ustring + ":green_square:"
                        output2 += ":green_square:"
                        correct_count += 1
                    else:
                        output += ustring + ":red_square:"
                        output2 += ":red_square:"
                case "Merc unit":
                    if unit_type == "nether":
                        output += ustring + ":green_square:"
                        output2 += ":green_square:"
                        correct_count += 1
                    else:
                        output += ustring + ":red_square:"
                        output2 += ":red_square:"
                case "Wave unit":
                    if unit_type == "creature":
                        output += ustring + ":green_square:"
                        output2 += ":green_square:"
                        correct_count += 1
                    else:
                        output += ustring + ":red_square:"
                        output2 += ":red_square:"
            embed.add_field(name=output,value="",inline=False)
            session["game1"]["guesses"].append(output2)
            if len(session["game1"]["guesses"]) == 10:
                session["game1"]["game_finished"] = True
                if correct_count < 6:
                    mod_date = datetime.strptime(ltdle_data["next_reset"], "%m/%d/%Y").timestamp()
                    timestamp = discord_timestamps.format_timestamp(mod_date, TimestampType.RELATIVE)
                    embed.add_field(name="You lost :frowning:. Try again next time in "+timestamp, value="Your guess history:\n" + "\n".join(session["game1"]["guesses"]),inline=False)
                    update_user_data()
                    return embed
            if correct_count == 6:
                session["game1"]["game_finished"] = True
                session["score"] += 11 - len(session["game1"]["guesses"])
                embed.add_field(name="You guessed the correct unit! Yay!", value="Your guess history:\n"+"\n".join(session["game1"]["guesses"]),inline=False)
                update_user_data()
                return embed
            else:
                embed.add_field(name="Try another unit.", value="",inline=False)
                update_user_data()
                return embed
            