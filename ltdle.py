import datetime
import json
import os
import random
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import discord
import discord_timestamps
from discord_timestamps import TimestampType

import responses


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def ltdle(session: dict, ltdle_data: dict, input: str=""):
    date_now = datetime.now()
    if datetime.strptime(session["game1"]["last_played"], "%m/%d/%Y")+timedelta(days=1) < datetime.strptime(ltdle_data["next_reset"], "%m/%d/%Y"):
        session["game1"]["last_played"] = date_now.strftime("%m/%d/%Y")
        session["game1"]["game_finished"] = False
        session["game1"]["game_state"] = 0
        session["game1"]["guesses"] = []
        with open("ltdle_data/"+session["name"]+"/data.json", "w") as f:
            json.dump(session, f)
            f.close()
        return ltdle_game1(session, input, ltdle_data)
    elif not session["game1"]["game_finished"]:
        return ltdle_game1(session, input, ltdle_data)
    else:
        mod_date = datetime.strptime(ltdle_data["next_reset"], "%m/%d/%Y").timestamp()
        timestamp = discord_timestamps.format_timestamp(mod_date, TimestampType.RELATIVE)
        return "You already played todays Legiondle, next reset is "+timestamp+"."

def ltdle_leaderboard(daily, avg):
    color = random.randrange(0, 2 ** 24)
    player_data_list = os.listdir("ltdle_data")
    scores = []
    for player in player_data_list:
        if player.endswith(".json"): continue
        with open("ltdle_data/"+player+"/data.json", "r") as f:
            p_data = json.load(f)
            f.close()
        if daily:
            with open("ltdle_data/ltdle.json", "r") as f:
                ltdle_data = json.load(f)
                f.close()
            if datetime.strptime(p_data["game1"]["last_played"], "%m/%d/%Y") < datetime.strptime(ltdle_data["next_reset"], "%m/%d/%Y"):
                if datetime.strptime(p_data["game1"]["last_played"], "%m/%d/%Y") == datetime.strptime(ltdle_data["next_reset"], "%m/%d/%Y")-timedelta(days=1):
                    if p_data["game1"]["game_finished"] == True:
                        daily_score = 11-len(p_data["game1"]["guesses"])
                        scores.append((p_data["name"].capitalize().replace("_", ""), daily_score))
        else:
            try: avg_pts = p_data["score"]/p_data["games_played"]
            except ZeroDivisionError: avg_pts = 0
            scores.append((p_data["name"].capitalize().replace("_", ""), p_data["score"], p_data["games_played"], avg_pts))
    if avg:
        scores = sorted(scores, key=lambda x: x[3], reverse=True)
    else:
        scores = sorted(scores, key=lambda x: x[1], reverse=True)
    output = ""
    for index, pscore in enumerate(scores):
        ranked_emote = ""
        if index == 10: break
        if index == 0:
            ranked_emote = responses.get_ranked_emote(2800)
        elif 1 <= index <= 3:
            ranked_emote = responses.get_ranked_emote(2600)
        elif 4 <= index <= 6:
            ranked_emote = responses.get_ranked_emote(2400)
        else:
            ranked_emote = responses.get_ranked_emote(2200)
        if daily:
            output += ranked_emote+" "+pscore[0] + ": " + str(pscore[1]) + "pts " + "\n"
        else:
            output += ranked_emote+" "+pscore[0] + ": " + str(pscore[1]) + "pts, Games: "+str(pscore[2])+" ("+str(round(pscore[1]/pscore[2],1))+"pts avg)\n"
    if daily:
        title = "Legiondle Daily Leaderboard"
    elif avg:
        title = "Legiondle Avg Leaderboard"
    else:
        title = "Legiondle Leaderboard"
    embed = discord.Embed(color=color, title=title, description="**"+output+"**")
    embed.set_author(name="Drachbot", icon_url="https://overlay.drachbot.site/favicon.ico")
    return embed

def ltdle_profile(player, avatar):
    color = random.randrange(0, 2 ** 24)
    try:
        with open("ltdle_data/" + player + "/data.json", "r") as f:
            p_data = json.load(f)
            f.close()
    except FileNotFoundError:
        return "No Legiondle profile found for "+player
    if p_data["games_played"] == 0:
        return "No games played."
    embed = discord.Embed(color=color, title="Legiondle Profile", description="**Games played: " +str(p_data["games_played"])+
                                                                              "\nPoints: "+str(p_data["score"])+
                                                                              "\nAvg: "+str(round(p_data["score"]/p_data["games_played"],1))+" points**")
    embed.set_author(name=player.capitalize(), icon_url=avatar)
    return embed

def ltdle_game1(session: dict, text_input: str, ltdle_data: dict):
    color = random.randrange(0, 2 ** 24)
    def update_user_data():
        with open("ltdle_data/" + session["name"] + "/data.json", "w") as f:
            json.dump(session, f)
            f.close()
    match session["game1"]["game_state"]:
        case 0:
            embed = discord.Embed(color=color, description=":exploding_head: **LEGIONDLE** :brain:\n**Enter any unit\nUsing the button below\n:bangbang: Including waves/mercs :bangbang:**")
            embed.set_thumbnail(url="https://overlay.drachbot.site/ltdle/guesstheunit.png")
            embed.set_author(name="Drachbot presents", icon_url="https://overlay.drachbot.site/favicon.ico")
            date_now = datetime.now()
            session["game1"]["last_played"] = date_now.strftime("%m/%d/%Y")
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
                if string.casefold() == text_input.casefold() or similar(string, text_input) > 0.8:
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
            def correct_output(input):
                return ":green_square:**" + input + "** "
            def false_output(input):
                return ":red_square:" + input + " "
            #attack
            if unit_data["attackType"] == ltdle_data["game_1_selected_unit"]["attackType"]:
                output += correct_output(unit_data["attackType"])
                output2 += ":green_square:"
                correct_count += 1
            else:
                output += false_output(unit_data["attackType"])
                output2 += ":red_square:"
            #armor
            if unit_data["armorType"] == ltdle_data["game_1_selected_unit"]["armorType"]:
                output += correct_output(unit_data["armorType"])
                output2 += ":green_square:"
                correct_count += 1
            else:
                output += false_output(unit_data["armorType"])
                output2 += ":red_square:"
            #range
            if unit_data["attackMode"] == ltdle_data["game_1_selected_unit"]["attackMode"]:
                output += correct_output(unit_data["attackMode"])
                output2 += ":green_square:"
                correct_count += 1
            else:
                output += false_output(unit_data["attackMode"])
                output2 += ":red_square:"
            #legion
            if unit_data["legionId"].split("_")[0] == "nether":
                lstring = "Merc"
            elif unit_data["legionId"].split("_")[0] == "creature":
                lstring = "Wave"
            else:
                lstring = unit_data["legionId"].split("_")[0].capitalize()
            if unit_data["legionId"] == ltdle_data["game_1_selected_unit"]["legionId"]:
                output += correct_output(lstring)
                output2 += ":green_square:"
                correct_count += 1
            else:
                output += false_output(lstring)
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
                        output += correct_output(ustring)
                        output2 += ":green_square:"
                        correct_count += 1
                    else:
                        output += false_output(ustring)
                        output2 += ":red_square:"
                case "Merc unit":
                    if unit_type == "nether":
                        output += correct_output(ustring)
                        output2 += ":green_square:"
                        correct_count += 1
                    else:
                        output += false_output(ustring)
                        output2 += ":red_square:"
                case "Wave unit":
                    if unit_type == "creature":
                        output += correct_output(ustring)
                        output2 += ":green_square:"
                        correct_count += 1
                    else:
                        output += false_output(ustring)
                        output2 += ":red_square:"
            if unit_data["unitId"] == ltdle_data["game_1_selected_unit"]["unitId"]:
                correct_count += 1
            def create_embed(end_string):
                if unit_data["unitId"] == ltdle_data["game_1_selected_unit"]["unitId"]:
                    embed = discord.Embed(color=color, title="Guess " + str(len(session["game1"]["guesses"])) + ": " + new_name + " :green_square:",description="*Bold text = correct*\n\n"+output+"\n\n"+end_string)
                else:
                    embed = discord.Embed(color=color, title="Guess " + str(len(session["game1"]["guesses"])) + ": " + new_name + " :red_square:",description="*Bold text = correct*\n\n"+output+"\n\n"+end_string)
                embed.set_thumbnail(url="https://cdn.legiontd2.com/icons/" + new_name + ".png")
                return embed
            session["game1"]["guesses"].append(output2+" "+new_name)
            if len(session["game1"]["guesses"]) == 10:
                session["game1"]["game_finished"] = True
                session["games_played"] += 1
                if correct_count < 6:
                    mod_date = datetime.strptime(ltdle_data["next_reset"], "%m/%d/%Y").timestamp()
                    timestamp = discord_timestamps.format_timestamp(mod_date, TimestampType.RELATIVE)
                    embed = create_embed("You lost :frowning:. Try again next time "+timestamp+"\nYour guess history:\n" + "\n".join(session["game1"]["guesses"]))
                    session["game1"]["game_state"] = 0
                    update_user_data()
                    return embed
            if correct_count == 6:
                print(session["name"]+ " found the right unit!")
                session["game1"]["game_finished"] = True
                session["score"] += 11 - len(session["game1"]["guesses"])
                embed = create_embed("**You guessed the correct unit! Yay!**(+"+str(11 - len(session["game1"]["guesses"]))+" points)\nYour guess history:\n"+"\n".join(session["game1"]["guesses"]))
                session["games_played"] += 1
                session["game1"]["game_state"] = 0
                update_user_data()
                return [embed]
            else:
                embed = create_embed("**Try another unit.**")
                session["game1"]["game_state"] = 0
                update_user_data()
                return embed
            