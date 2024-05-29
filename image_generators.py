import PIL
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import legion_api
import util
import requests
import json
import platform

with open('Files/json/Secrets.json', 'r') as f:
    secret_file = json.load(f)
    f.close()

header = {'x-api-key': secret_file.get('apikey')}

output_folder = "Files/output/"
if platform.system() == "Linux":
    shared_folder = "/shared/Images/"
else:
    shared_folder = "shared/Images/"
site = "https://overlay.drachbot.site/Images/"

def create_image_stats(dict, games, playerid, avgelo, patch, mode, megamind = False, megamind_count = 0, transparency = False):
    if playerid != 'all' and 'nova cup' not in playerid:
        playername = legion_api.getprofile(playerid)['playerName']
        avatar = legion_api.getprofile(playerid)['avatarUrl']
    else:
        playername = playerid.capitalize()
    def calc_pr(dict, mm):
        if megamind: games2 = megamind_count
        else: games2 = games
        return str(round(dict[mm]['Count'] / games2 * 100, 1))
    def get_perf_score(dict2, key):
        new_dict = {}
        for xy in dict2[key]:
            if dict2[key][xy]['Wins'] / dict2[key][xy]['Count'] < dict2['Wins'] / dict2['Count']:
                continue
            new_dict[xy] = dict2[key][xy]['Wins'] / dict2[key][xy]['Count'] * (dict2[key][xy]['Count'] / dict2['Count'])
        newIndex = sorted(new_dict, key=lambda k: new_dict[k], reverse=True)
        return newIndex
    if transparency: config = ['RGBA', (0,0,0,0)]
    else: config = ['RGB', (49,51,56)]
    match mode:
        case "Mastermind":
            if megamind: im = PIL.Image.new(mode=config[0], size=(1380, 810), color=config[1])
            else: im = PIL.Image.new(mode=config[0], size=(1485, 810), color=config[1])
            keys = ['Games:', 'Winrate:', 'Pickrate:', 'Player Elo:', 'W on 10:', 'Best Open:', '', 'Games:', 'Winrate:', 'Playrate:','Best Spell:', '', 'Games:', 'Winrate:', 'Playrate:']
            dict_values = ["Opener", "Spell"]
            icon_type = "legion"
        case "Open":
            im = PIL.Image.new(mode=config[0], size=(1700, 1015), color=config[1])
            keys = ['Games:', 'Winrate:', 'Playrate:', 'Player Elo:', 'W on 4:', 'Best Add:', '', 'Games:', 'Winrate:', 'Playrate:', 'Best MMs:', '', 'Games:', 'Winrate:', 'Playrate:', 'Best Spell:', '', 'Games:', 'Winrate:', 'Playrate:']
            dict_values = ["OpenWith", "MMs", "Spells"]
            icon_type = "icon"
        case "Spell":
            im = PIL.Image.new(mode=config[0], size=(1700, 810), color=config[1])
            keys = ['Games:', 'Winrate:', 'Pickrate:', 'Player Elo:', 'W on 10:', 'Best Open:', '', 'Games:', 'Winrate:', 'Playrate:', 'Best MMs:', '', 'Games:', 'Winrate:', 'Playrate:']
            dict_values = ["Opener", "MMs"]
            icon_type = "icon"
        case "Unit":
            im = PIL.Image.new(mode=config[0], size=(1700, 970), color=config[1])
            keys = ['Games:', 'Winrate:', 'Playrate:', 'Player Elo:', 'Best\nCombo:', '', 'Games:', 'Winrate:', 'Playrate:', 'Best MM:', '', 'Games:', 'Winrate:', 'Playrate:', 'Best Spell:', '', 'Games:', 'Winrate:', 'Playrate:']
            dict_values = ["ComboUnit", "MMs", "Spells"]
            icon_type = "icon"
    im2 = PIL.Image.new(mode="RGB", size=(88, 1200), color=(25,25,25))
    I1 = ImageDraw.Draw(im)
    ttf = 'Files/RobotoCondensed-Regular.ttf'
    myFont_small = ImageFont.truetype(ttf, 20)
    myFont = ImageFont.truetype(ttf, 25)
    myFont_title = ImageFont.truetype(ttf, 30)
    if playername == 'All' or 'Nova cup' in playername:
        string = ''
    else:
        string = "'s"
        av_image = util.get_icons_image("avatar", avatar)
        gold_border = Image.open('Files/gold_64.png')
        if util.im_has_alpha(np.array(av_image)):
            im.paste(av_image, (24, 100), mask=av_image)
        else:
            im.paste(av_image, (24, 100))
        im.paste(gold_border, (24, 100), mask=gold_border)
    if megamind: I1.text((10, 15), str(playername)+string+" Megamind stats (From "+str(games)+" ranked games, Avg elo: "+str(avgelo)+")", font=myFont_title, stroke_width=2, stroke_fill=(0,0,0), fill=(255, 255, 255))
    else: I1.text((10, 15), str(playername) + string + " "+mode+" stats (From " + str(games) + " ranked games, Avg elo: " + str(avgelo) + ")", font=myFont_title, stroke_width=2,stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    I1.text((10, 55), 'Patches: ' + ', '.join(patch), font=myFont_small, stroke_width=2, stroke_fill=(0,0,0), fill=(255, 255, 255))
    x = 126
    y = 175
    offset = 45
    offset2 = 25
    offset3 = 0
    offset_counter = 5
    for i, dict_key in enumerate(dict):
        if dict[dict_key]["Count"] == 0 or i == 15:
            break
        im.paste(im2, (x - 12, 88))
        im.paste(util.get_icons_image(icon_type, dict_key), (x, 100))
        I1.text((x, y), str(dict[dict_key]['Count']), font=myFont, fill=(255, 255, 255))
        I1.text((x, y + offset), str(round(dict[dict_key]['Wins']/dict[dict_key]['Count'] * 100, 1)) + '%', font=myFont, fill=(255, 255, 255))
        if mode == "Spell":
            try:
                I1.text((x, y + offset * 2), str(round(dict[dict_key]['Count']/dict[dict_key]['Offered'] * 100, 1))+"%", font=myFont, fill=(255, 255, 255))
            except ZeroDivisionError:
                I1.text((x, y + offset * 2), str(round(dict[dict_key]['Count']/games * 100, 1))+"%", font=myFont, fill=(255, 255, 255))
        else:
            I1.text((x, y + offset * 2), str(calc_pr(dict, dict_key)) + '%', font=myFont, fill=(255, 255, 255))
        I1.text((x, y + offset * 3), str(round(dict[dict_key]['Elo'] / dict[dict_key]['Count'])), font=myFont, fill=(255, 255, 255))
        try:
            I1.text((x, y + offset * 4), str(round(dict[dict_key]['Worker'] / dict[dict_key]['Count'], 1)), font=myFont, fill=(255, 255, 255))
        except KeyError: offset_counter = 4
        for val in dict_values:
            newIndex = get_perf_score(dict[dict_key], val)
            if newIndex:
                if newIndex[0] == "none":
                    try:
                        index = newIndex[1]
                    except IndexError:
                        index = newIndex[0]
                else:
                    index = newIndex[0]
                if val != "MMs": type = "icon"
                else: type = "legion"
                im.paste(util.get_icons_image(type, index), (x, y + offset3 + offset * offset_counter))
                I1.text((x, y + offset2 + offset * (offset_counter+1)), str(dict[dict_key][val][index]['Count']), font=myFont, fill=(255, 255, 255))
                I1.text((x, y + offset2 + offset * (offset_counter+2)), str(round(dict[dict_key][val][index]['Wins'] / dict[dict_key][val][index]['Count'] * 100, 1)) + '%', font=myFont, fill=(255, 255, 255))
                I1.text((x, y + offset2 + offset * (offset_counter+3)), str(round(dict[dict_key][val][index]['Count'] / dict[dict_key]['Count'] * 100, 1)) + '%', font=myFont, fill=(255, 255, 255))
            offset2 += 25
            offset3 += 25
            offset_counter += 4
        offset2 = 25
        offset3 = 0
        offset_counter = 5
        x += 106
    im3 = PIL.Image.new(mode="RGB", size=(x-38, 4), color=(169, 169, 169))
    for k in keys:
        I1.text((8, y), k, font=myFont, stroke_width=2, stroke_fill=(0,0,0), fill=(255, 255, 255))
        if k.startswith("Best") == False and (k != ''):
            im.paste(im3, (8, y + 30))
            y += offset
        else:
            y += offset-10
    image_id = util.id_generator()
    im.save(output_folder + image_id + '.png')
    return output_folder + image_id + '.png'

def create_image_stats_specific(dict, games, playerid, avgelo, patch, mode, specific_value, transparency = False):
    if playerid != 'all' and 'nova cup' not in playerid:
        playername = legion_api.getprofile(playerid)['playerName']
    else:
        playername = playerid.capitalize()
    if transparency:
        config = ['RGBA', (0, 0, 0, 0)]
    else:
        config = ['RGB', (49, 51, 56)]
    match mode:
        case "Mastermind":
            im = PIL.Image.new(mode=config[0], size=(1700, 545), color=config[1])
            keys = ['Open:', '', 'Games:', 'Winrate:', 'Playrate:', 'Spell:', '', 'Games:', 'Winrate:', 'Playrate:']
            dict_values = ["Opener", "Spell"]
            icon_type = "legion"
        case "Open":
            im = PIL.Image.new(mode=config[0], size=(1700, 745), color=config[1])
            keys = ['Adds:', '', 'Games:', 'Winrate:', 'Playrate:', 'MMs:','', 'Games:', 'Winrate:', 'Playrate:', 'Spell:','', 'Games:', 'Winrate:', 'Playrate:']
            dict_values = ["OpenWith", "MMs", "Spells"]
            icon_type = "icon"
        case "Spell":
            if specific_value in util.buff_spells:
                im = PIL.Image.new(mode=config[0], size=(1700, 745), color=config[1])
                keys = ['Targets:', '', 'Games:', 'Winrate:', 'Playrate:', 'Open:', '', 'Games:', 'Winrate:', 'Playrate:', 'MMs:', '', 'Games:', 'Winrate:', 'Playrate:']
                dict_values = ["Targets", "Opener", "MMs"]
                icon_type = "icon"
            else:
                im = PIL.Image.new(mode=config[0], size=(1700, 545), color=config[1])
                keys = ['Open:', '', 'Games:', 'Winrate:', 'Playrate:', 'MMs:','', 'Games:', 'Winrate:', 'Playrate:']
                dict_values = ["Opener", "MMs"]
                icon_type = "icon"
        case "Unit":
            im = PIL.Image.new(mode=config[0], size=(1700, 745), color=config[1])
            keys = ['Combo:', '', 'Games:', 'Winrate:', 'Playrate:', 'MMs:', '', 'Games:', 'Winrate:', 'Playrate:', 'Spell:', '', 'Games:', 'Winrate:', 'Playrate:']
            dict_values = ["ComboUnit", "MMs", "Spells"]
            icon_type = "icon"
    im2 = PIL.Image.new(mode="RGB", size=(88, 205), color=(25, 25, 25))
    I1 = ImageDraw.Draw(im)
    ttf = 'Files/RobotoCondensed-Regular.ttf'
    myFont_small = ImageFont.truetype(ttf, 20)
    myFont = ImageFont.truetype(ttf, 25)
    myFont_title = ImageFont.truetype(ttf, 30)
    unit_name = ""
    if playername == 'All' or 'Nova cup' in playername:
        suffix = ''
    else:
        suffix = "'s"
    im.paste(util.get_icons_image(icon_type, specific_value), (10, 10))
    if dict[specific_value]["Count"] == 0:
        return "No " + specific_value + " games found."
    I1.text((82, 10), str(playername) + suffix + " " + specific_value.capitalize() + " stats (From " + str(games) + " ranked games, Avg elo: " + str(avgelo) + ")", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    I1.text((82, 55), 'Patches: ' + ', '.join(patch), font=myFont_small, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    try:
        winrate = str(round(dict[specific_value]["Wins"] / dict[specific_value]["Count"] * 100, 1))
    except ZeroDivisionError:
        winrate = "0"
    overall_string = ("Games: " + str(dict[specific_value]["Count"]) +
            " | Wins: " + str(dict[specific_value]["Wins"]) +
            " | Losses: " + str(dict[specific_value]["Count"] - dict[specific_value]["Wins"]) +
            " | Winrate: " + winrate + "%")
    try:
        if mode == "Open":
            temp_string = "W on 4:"
        else:
            temp_string = "W on 10:"
        overall_string += f" | {temp_string} " + str(round(dict[specific_value]['Worker'] / dict[specific_value]['Count'], 1))
    except KeyError:
        pass
    if mode == "Spell":
        try:
            overall_string += " | Pickrate: " + str(round(dict[specific_value]['Count']/dict[specific_value]['Offered'] * 100, 1))+"%"
        except ZeroDivisionError:
            overall_string += " | Pickrate: " + str(round(dict[specific_value]['Count']/games * 100, 1))+"%"
    I1.text((10, 80), overall_string , font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    x = 126
    y = 130
    offset = 45
    offset2 = 25
    offset3 = 0
    offset_counter = 0
    max_x = []
    for i, val in enumerate(dict_values):
        newIndex = sorted(dict[specific_value][val], key=lambda k: int(dict[specific_value][val][k]["Count"]), reverse=True)
        for idx, val2 in enumerate(newIndex):
            if idx == 15: break
            im.paste(im2, (x - 12, y - 12 + offset3 + (offset * offset_counter)))
            if val != "MMs": type = "icon"
            else: type = "legion"
            im.paste(util.get_icons_image(type, val2), (x, y + offset3 + (offset * offset_counter)))
            I1.text((x, y + offset2 + offset * (offset_counter+1)), str(dict[specific_value][val][val2]['Count']), font=myFont, fill=(255, 255, 255))
            I1.text((x, y + offset2 + offset * (offset_counter+2)), str(round(dict[specific_value][val][val2]['Wins'] / dict[specific_value][val][val2]['Count'] * 100, 1)) + '%', font=myFont, fill=(255, 255, 255))
            I1.text((x, y + offset2 + offset * (offset_counter+3)), str(round(dict[specific_value][val][val2]['Count'] / dict[specific_value]['Count'] * 100, 1)) + '%', font=myFont, fill=(255, 255, 255))
            x += 106
        max_x.append(x)
        offset2 += 25
        offset3 += 25
        offset_counter += 4
        x = 126
    exclude = ["Open:", "Adds:", "MMs:", "Spell:", "Combo:", "Targets:"]
    dict_values_counter = 0
    for i, k in enumerate(keys):
        I1.text((8, y), k, font=myFont, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
        if k not in exclude and (k != ''):
            if k == "Playrate:": rgb =(200,20,0)
            else: rgb = (169, 169, 169)
            im3 = PIL.Image.new(mode="RGB", size=(max_x[dict_values_counter] - 38, 4), color=rgb)
            im.paste(im3, (8, y + 30))
            y += offset
        else:
            y += offset - 10
        if i == 4 or i == 9: dict_values_counter += 1
    image_id = util.id_generator()
    im.save(output_folder + image_id + '.png')
    return output_folder + image_id + '.png'

def gameid_visualizer_singleplayer(gameid, start_wave, player_index):
    image_link = ""
    url = 'https://apiv2.legiontd2.com/games/byId/' + gameid + '?includeDetails=true'
    api_response = requests.get(url, headers=header)
    gamedata = json.loads(api_response.text)
    units_dict = json.load(open("Files/json/units.json"))
    if (gamedata == {'message': 'Internal server error'}) or (gamedata == {'err': 'Entry not found.'}):
        return "GameID not found. (Games that are not concluded or older than 1 year are not available in the API)"
    player_dict = {}
    player = gamedata["playersData"][player_index]
    player_dict[player["playerName"]] = {"avatar_url": legion_api.getprofile(player["playerId"])["avatarUrl"],
                                         "roll": player["rolls"].replace(" ", "").split(","), "legion": player["legion"], "elo": player["overallElo"],
                                         "elo_change": player["eloChange"]}
    wave = start_wave
    first = True
    mode = 'RGB'
    colors = (30, 30, 30)
    x = 10
    y = 350
    box_size = 64
    line_width = 3
    offset = box_size + line_width
    im = PIL.Image.new(mode=mode, size=(20+offset*9, 1750), color=colors)
    horz_line = PIL.Image.new(mode="RGB", size=(box_size*9+line_width*10, line_width), color=(155, 155, 155))
    vert_line = PIL.Image.new(mode="RGB", size=(line_width, box_size*14+line_width*15), color=(155, 155, 155))
    I1 = ImageDraw.Draw(im)
    ttf = 'Files/RobotoCondensed-Regular.ttf'
    myFont_tiny = ImageFont.truetype(ttf, 30)
    myFont_small = ImageFont.truetype(ttf, 40)
    myFont_title = ImageFont.truetype(ttf, 60)
    y2 = 125
    im.paste(Image.open(open("Files/Waves/Wave"+str(wave+1)+".png", "rb")), (10,10))
    I1.text((80, 10), "Wave "+str(wave+1), font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0),fill=(255, 255, 255))
    I1.text((80, 75),"Patch: " + gamedata["version"], font=myFont_small, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    #player
    av_image = util.get_icons_image("avatar", player_dict[player["playerName"]]["avatar_url"])
    if util.im_has_alpha(np.array(av_image)):
        im.paste(av_image, (x, y2), mask=av_image)
    else:
        im.paste(av_image, (x, y2))
    I1.text((x+80, y2), str(player["playerName"]), font=myFont_title, stroke_width=2,stroke_fill=(0,0,0), fill=(255, 255, 255))
    if wave > 9:
        im.paste(util.get_icons_image("icon_send", player["chosenSpell"].replace(" ", "")), (x+500, y2))
    try:
        im.paste(util.get_icons_image("legion", player_dict[player["playerName"]]["legion"]), (x, y2+80))
    except FileNotFoundError:
        im.paste(util.get_icons_image("icon", player_dict[player["playerName"]]["legion"]), (x, y2 + 80))
    if len(player_dict[player["playerName"]]["roll"]) > 1:
        for c, unit in enumerate(player_dict[player["playerName"]]["roll"]):
            im.paste(util.get_icons_image("icon", unit.replace("_unit_id", "")), (x+offset+16+(offset*c), y2 + 80))
    for i in range(15):
        im.paste(horz_line, (x,y+offset*i))
    for i in range(10):
        im.paste(vert_line, (x+offset*i,y))
    build_per_wave = player["buildPerWave"][wave]
    value = 0
    for w_index, unit2 in enumerate(build_per_wave):
        unit2_list = unit2.split(":")
        unit2_name = unit2_list[0]
        unit_stacks = int(unit2_list[2])
        for unitjson in units_dict:
            if unit2_name == "hell_raiser_buffed_unit_id":
                unit2_name = "hell_raiser_unit_id"
            if unitjson["unitId"] == unit2_name:
                if unit_stacks > 0:
                    value += util.get_unit_stacks_value(unit2_name, unit_stacks, w_index)
                value += int(unitjson["totalValue"])
        unit2 = unit2.split("_unit_id:")
        unit_x = float(unit2[1].split("|")[0])-0.5
        unit_y = 14-float(unit2[1].split("|")[1].split(":")[0])-0.5
        im.paste(util.get_icons_image("icon", unit2[0]), (int(x + line_width + offset * unit_x), int(y + line_width + offset * unit_y)))
        if player["chosenSpellLocation"] != "-1|-1":
            if unit2_list[1] == player["chosenSpellLocation"] and wave > 9:
                im.paste(util.get_icons_image("icon", player["chosenSpell"]).resize((32,32)),(int(x + line_width + offset * unit_x), int(y + line_width + offset * unit_y)))
        try:
            if player["chosenChampionLocation"] != "-1|-1":
                if unit2_list[1] == player["chosenChampionLocation"]:
                    im.paste(util.get_icons_image("legion", "Champion").resize((32,32)),(int(x + 32 + line_width + offset * unit_x), int(y + line_width + offset * unit_y)))
        except Exception: pass
        if unit_stacks != 0:
            I1.text((int(x + line_width + offset * unit_x), int(y + 32 + line_width + offset * unit_y)), str(unit_stacks), font=myFont_tiny, stroke_width=1, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    im.paste(util.get_icons_image("icon", "Value32").resize((64,64)), (x, y2 + 150), mask=util.get_icons_image("icon", "Value32").resize((64,64)))
    I1.text((x + 70, y2 + 160), str(value), font=myFont_small, stroke_width=2,stroke_fill=(0,0,0), fill=(255, 255, 255))
    im.paste(util.get_icons_image("icon", "Worker"), (x+230, y2 + 150))
    I1.text((x + 300, y2 + 160), str(round(player["workersPerWave"][wave-1], 1)), font=myFont_small, stroke_width=2, stroke_fill=(0, 0, 0),fill=(255, 255, 255))
    im.paste(util.get_icons_image("icon", "Income").resize((64,64)), (x + 450, y2 + 150), mask=util.get_icons_image("icon", "Income").resize((64,64)))
    I1.text((x + 520, y2 + 160), str(round(player["incomePerWave"][wave-1], 1)), font=myFont_small,stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    im.paste(util.get_icons_image("icon", "Mythium32").resize((64, 64)), (x, y+20+offset*14),mask=util.get_icons_image("icon", "Mythium32").resize((64, 64)))
    I1.text((x+70, y+20+offset*14), str(util.count_mythium(player["mercenariesReceivedPerWave"][wave])+len(player["opponentKingUpgradesPerWave"][wave])*20), font=myFont_small,stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    send_count = 0
    for send in player["mercenariesReceivedPerWave"][wave]:
        if send_count < 9:
            im.paste(util.get_icons_image("icon_send", send.replace(" ", "")), (x+offset*send_count, y+20+offset*15))
        elif send_count >= 9:
            im.paste(util.get_icons_image("icon_send", send.replace(" ", "")),(x + offset * (send_count-9), y + 20 + offset * 16))
        elif send_count >18:
            break
        send_count += 1
    for send in player["opponentKingUpgradesPerWave"][wave]:
        if send_count < 9:
            im.paste(util.get_icons_image("icon_send", send.replace(" ", "")), (x+offset*send_count, y+20+offset*15))
        elif send_count >= 9:
            im.paste(util.get_icons_image("icon_send", send.replace(" ", "")),(x + offset * (send_count-9), y + 20 + offset * 16))
        elif send_count >18:
            break
        send_count += 1
    im.paste(util.get_icons_image("icon", "Leaked"), (x, y+220+offset*14))
    leak = util.calc_leak(player["leaksPerWave"][wave], wave)
    if leak > 0:
        I1.text((x+offset, y+220+offset*14), str(leak)+"%", font=myFont_small, stroke_width=2, stroke_fill=(0, 0, 0),fill=(255, 255, 255))
    leak_count = 0
    for leak in player["leaksPerWave"][wave]:
        if leak_count < 9:
            im.paste(util.get_icons_image("icon_send", leak.replace(" ", "")),(x + offset * leak_count, y + 225 + offset * 15))
        elif leak_count >= 9:
            im.paste(util.get_icons_image("icon_send", leak.replace(" ", "")),(x + offset * (leak_count - 9), y + 225 + offset * 16))
        elif leak_count > 18:
            break
        leak_count += 1
    image_id = util.id_generator()
    im2 = im.crop((0, 0, 20 + offset * 9, 1508))
    im2.save(shared_folder+image_id+'.png')
    im3 = im.crop((0,1508,20+offset*9, 1750))
    im3.save(shared_folder + image_id + '_covered.png')
    image_link = shared_folder+image_id+'.png'
    return image_link
