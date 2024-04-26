import PIL
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import legion_api
import util

output_folder = "Files/output/"

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
            if megamind: im = PIL.Image.new(mode=config[0], size=(1380, 770), color=config[1])
            else: im = PIL.Image.new(mode=config[0], size=(1485, 770), color=config[1])
            keys = ['Games:', 'Winrate:', 'Pickrate', 'W on 10:', 'Best Open:', '', 'Games:', 'Winrate:', 'Playrate:','Best Spell:', '', 'Games:', 'Winrate:', 'Playrate:']
            dict_values = ["Opener", "Spell"]
            icon_type = "legion"
        case "Open":
            im = PIL.Image.new(mode=config[0], size=(1700, 975), color=config[1])
            keys = ['Games:', 'Winrate:', 'Playrate:', 'W on 4:', 'Best Add:', '', 'Games:', 'Winrate:', 'Playrate:', 'Best MMs:', '', 'Games:', 'Winrate:', 'Playrate:', 'Best Spell:', '', 'Games:', 'Winrate:', 'Playrate:']
            dict_values = ["OpenWith", "MMs", "Spells"]
            icon_type = "icon"
        case "Spell":
            im = PIL.Image.new(mode=config[0], size=(1700, 770), color=config[1])
            keys = ['Games:', 'Winrate:', 'Playrate:', 'W on 10:', 'Best Open:', '', 'Games:', 'Winrate:', 'Playrate:', 'Best MMs:', '', 'Games:', 'Winrate:', 'Playrate:']
            dict_values = ["Opener", "MMs"]
            icon_type = "icon"
        case "Unit":
            im = PIL.Image.new(mode=config[0], size=(1700, 930), color=config[1])
            keys = ['Games:', 'Winrate:', 'Playrate:', 'Best\nCombo:', '', 'Games:', 'Winrate:', 'Playrate:', 'Best MM:', '', 'Games:', 'Winrate:', 'Playrate:', 'Best Spell:', '', 'Games:', 'Winrate:', 'Playrate:']
            dict_values = ["ComboUnit", "MMs", "Spells"]
            icon_type = "icon"
    im2 = PIL.Image.new(mode="RGB", size=(88, 900), color=(25,25,25))
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
    offset_counter = 4
    for i, dict_key in enumerate(dict):
        if dict[dict_key]["Count"] == 0 or i == 15:
            break
        im.paste(im2, (x - 12, 88))
        im.paste(util.get_icons_image(icon_type, dict_key), (x, 100))
        I1.text((x, y), str(dict[dict_key]['Count']), font=myFont, fill=(255, 255, 255))
        I1.text((x, y + offset), str(round(dict[dict_key]['Wins']/dict[dict_key]['Count'] * 100, 1)) + '%', font=myFont, fill=(255, 255, 255))
        I1.text((x, y + offset * 2), str(calc_pr(dict, dict_key)) + '%', font=myFont, fill=(255, 255, 255))
        try:
            I1.text((x, y + offset * 3), str(round(dict[dict_key]['Worker'] / dict[dict_key]['Count'], 1)), font=myFont, fill=(255, 255, 255))
        except KeyError: offset_counter = 3
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
        offset_counter = 4
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
        I1.text((10, 80), "Games: " + str(dict[specific_value]["Count"]) + ", Wins: " + str(dict[specific_value]["Wins"]) + ", Losses: " + str(dict[specific_value]["Count"] - dict[specific_value]["Wins"]) + ", Winrate: " + str(round(dict[specific_value]["Wins"] / dict[specific_value]["Count"] * 100, 1)) + "%", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    except ZeroDivisionError:
        I1.text((10, 80), "Games: " + str(dict[specific_value]["Count"]) + ", Wins: " + str(dict[specific_value]["Wins"]) + ", Losses: " + str(dict[specific_value]["Count"] - dict[specific_value]["Wins"]) + ", Winrate: " + str(0) + "%", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
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
    exclude = ["Open:", "Adds:", "MMs:", "Spell:", "Combo:"]
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