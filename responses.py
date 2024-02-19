import io
import requests
import json
from collections import Counter
import pathlib
from pathlib import Path
import datetime
import os
import glob
import re
import time
import bot
import PIL
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from imgurpython import ImgurClient
import numpy as np
import math
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

with open('Files/Secrets.json') as f:
    secret_file = json.load(f)
    header = {'x-api-key': secret_file.get('apikey')}
    imgur_client = ImgurClient(secret_file.get('imgur'), secret_file.get('imgurcs'))

def divide_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]

def im_has_alpha(img_arr):
    h,w,c = img_arr.shape
    return True if c ==4 else False

def create_image_mmstats(dict, ranked_count, playerid, avgelo, patch, megamind = False, megamind_count = 0, transparency = True):
    if playerid != 'all' and 'nova cup' not in playerid:
        playername = apicall_getprofile(playerid)['playerName']
        avatar = apicall_getprofile(playerid)['avatarUrl']
    else:
        playername = playerid.capitalize()
    def calc_wr(dict, mm):
        try:
            return str(round(dict[mm]['Wins']/dict[mm]['Count'] * 100, 1))
        except ZeroDivisionError as e:
            return '0'
    def calc_pr(dict, mm):
        try:
            if megamind:
                return str(round(dict[mm]['Count'] / megamind_count * 100, 1))
            else:
                return str(round(dict[mm]['Count'] / ranked_count * 100, 1))
        except ZeroDivisionError as e:
            return '0'
    def most_common(dict, mm):
        try:
            data = Counter(dict[mm]['Opener'])
            data2 = Counter(dict[mm]['Spell'])
            return [data.most_common(1)[0][0], data2.most_common(1)[0][0]]
        except IndexError as e:
            return 'No data'
    def get_open_wrpr(dict, mm):
        wins = 0
        count = 0
        for i, x in enumerate(dict[mm]['Opener']):
            if most_common(dict, mm)[0] in x:
                count += 1
                if dict[mm]['Results'][i] == 'won':
                    wins += 1
        try:
            return [count, round(wins / count * 100, 1), round(count / dict[mm]['Count'] * 100, 1)]
        except ZeroDivisionError as e:
            return '000'
    def get_w10(dict, i):
        try:
            return round(sum(dict[i]['W10']) / dict[i]['Count'], 1)
        except ZeroDivisionError as e:
            return '0'
    def get_spell_wrpr(dict, mm):
        wins = 0
        count = 0
        for i, x in enumerate(dict[mm]['Spell']):
            if most_common(dict, mm)[1] in x:
                count += 1
                if dict[mm]['Results'][i] == 'won':
                    wins += 1
        try:
            return [count, round(wins / count * 100, 1), round(count / dict[mm]['Count'] * 100, 1)]
        except ZeroDivisionError as e:
            return '000'
    def calc_elo(dict, mm):
        try:
            return round(dict[mm]['Elo'] / dict[mm]['Count'])
        except ZeroDivisionError as e:
            return '0'
    keys = ['Games:', 'Winrate:', 'Pickrate', 'Elo:', 'W on 10:', 'Open:', '', 'Games:', 'Winrate:', 'Playrate:','Spells:', '', 'Games:', 'Winrate:', 'Playrate:']
    url = 'https://cdn.legiontd2.com/icons/Items/'
    url2 = 'https://cdn.legiontd2.com/icons/'
    if transparency:
        mode = 'RGBA'
        colors = (0,0,0,0)
    else:
        mode = 'RGB'
        colors = (49,51,56)
    if megamind:
        im = PIL.Image.new(mode=mode, size=(1490-106, 895), color=colors)
    else:
        im = PIL.Image.new(mode=mode, size=(1490, 895), color=colors)
    im2 = PIL.Image.new(mode="RGB", size=(88, 900), color=(25,25,25))
    im3 = PIL.Image.new(mode="RGB", size=(1495, 4), color=(169, 169, 169))
    I1 = ImageDraw.Draw(im)
    ttf = 'Files/RobotoCondensed-Regular.ttf'
    myFont_small = ImageFont.truetype(ttf, 20)
    myFont = ImageFont.truetype(ttf, 25)
    myFont_title = ImageFont.truetype(ttf, 30)
    if playername == 'All' or 'Nova cup' in playername:
        string = ''
    else:
        string = "'s"
        avatar_url = 'https://cdn.legiontd2.com/' + avatar
        avatar_response = requests.get(avatar_url)
        av_image = Image.open(BytesIO(avatar_response.content))
        gold_border = Image.open('Files/gold_64.png')
        if im_has_alpha(np.array(av_image)):
            im.paste(av_image, (24, 100), mask=av_image)
        else:
            im.paste(av_image, (24, 100))
        im.paste(gold_border, (24, 100), mask=gold_border)
    if megamind:
        I1.text((10, 15), str(playername)+string+" Megamind stats (From "+str(ranked_count)+" ranked games, Avg elo: "+str(avgelo)+")", font=myFont_title, stroke_width=2, stroke_fill=(0,0,0), fill=(255, 255, 255))
    else:
        I1.text((10, 15), str(playername) + string + " Mastermind stats (From " + str(ranked_count) + " ranked games, Avg elo: " + str(avgelo) + ")", font=myFont_title, stroke_width=2,stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    I1.text((10, 55), 'Patches: ' + ', '.join(patch), font=myFont_small, stroke_width=2, stroke_fill=(0,0,0), fill=(255, 255, 255))
    x = 126
    y = 190
    for i in dict:
        im.paste(im2, (x-12, 100))
        url_new = url + i + '.png'
        response = requests.get(url_new)
        mm_image = Image.open(BytesIO(response.content))
        im.paste(mm_image, (x, 112))
        I1.text((x, 190), str(dict[i]['Count']), font=myFont, fill=(255, 255, 255))
        I1.text((x, 240), str(calc_wr(dict, i))+'%', font=myFont, fill=(255, 255, 255))
        I1.text((x, 290), str(calc_pr(dict, i))+'%', font=myFont, fill=(255, 255, 255))
        I1.text((x, 340), str(calc_elo(dict, i)), font=myFont, fill=(255, 255, 255))
        I1.text((x, 390), str(get_w10(dict, i)), font=myFont, fill=(255, 255, 255))
        I1.text((x, 520), str(get_open_wrpr(dict, i)[0]), font=myFont, fill=(255, 255, 255))
        I1.text((x, 570), str(get_open_wrpr(dict, i)[1])+'%', font=myFont, fill=(255, 255, 255))
        I1.text((x, 620), str(get_open_wrpr(dict, i)[2])+'%', font=myFont, fill=(255, 255, 255))
        I1.text((x, 750), str(get_spell_wrpr(dict, i)[0]), font=myFont, fill=(255, 255, 255))
        I1.text((x, 800), str(get_spell_wrpr(dict, i)[1]) + '%', font=myFont, fill=(255, 255, 255))
        I1.text((x, 850), str(get_spell_wrpr(dict, i)[2]) + '%', font=myFont, fill=(255, 255, 255))
        url_new = url2 + str(most_common(dict, i)[0]).replace(' ', '') + '.png'
        if url_new == 'https://cdn.legiontd2.com/icons/N.png':
            url_new = 'https://cdn.legiontd2.com/icons/Secret/SadHopper.png'
        response = requests.get(url_new)
        unit_image = Image.open(BytesIO(response.content))
        im.paste(unit_image, (x, 440))
        url_new = url2 + str(most_common(dict, i)[1]).replace(' ', '') + '.png'
        if 'none' in url_new:
            url_new = 'https://cdn.legiontd2.com/icons/Granddaddy.png'
        if url_new == 'https://cdn.legiontd2.com/icons/PresstheAttack.png':
            url_new = 'https://cdn.legiontd2.com/icons/PressTheAttack.png'
        if url_new == 'https://cdn.legiontd2.com/icons/o.png':
            url_new = 'https://cdn.legiontd2.com/icons/Secret/HermitHas0Friends.png'
        response = requests.get(url_new)
        spell_image = Image.open(BytesIO(response.content))
        im.paste(spell_image, (x, 670))
        x += 106
    for k in keys:
        if (k != 'Open:') and (k != 'Spells:') and (k != ''):
            im.paste(im3, (10, y+30))
        I1.text((10, y), k, font=myFont, stroke_width=2, stroke_fill=(0,0,0), fill=(255, 255, 255))
        if (k != 'Open:') and (k != 'Spells:') and (k != ''):
            y += 50
        else:
            y += 40
    im.save('Files/output.png', 'PNG')
    image_upload = imgur_client.upload_from_path('Files/output.png')
    print('Uploading output.png to Imgur...')
    return image_upload['link']

def create_image_mmstats_fiesta(dict, ranked_count, playerid, avgelo, patch, transparency = True):
    if playerid != 'all' and 'nova cup' not in playerid:
        playername = apicall_getprofile(playerid)['playerName']
        avatar = apicall_getprofile(playerid)['avatarUrl']
    else:
        playername = playerid.capitalize()
    def calc_wr(dict, mm):
        try:
            return str(round(dict[mm]['Wins']/dict[mm]['Count'] * 100, 1))
        except ZeroDivisionError as e:
            return '0'
    def calc_pr(dict, mm):
        try:
            return str(round(dict[mm]['Count'] / ranked_count * 100, 1))
        except ZeroDivisionError as e:
            return '0'
    def most_common(dict, mm, amount, key):
        try:
            data = Counter(dict[mm][key])
            return [data.most_common(amount)]
        except IndexError as e:
            return 'No data'
    def get_wrpr(dict, mm, opener, key):
        wins = 0
        count = 0
        for i, x in enumerate(dict[mm][key]):
            if opener in x:
                count += 1
                if dict[mm]['Results'][i] == 'won':
                    wins += 1
        try:
            return [count, round(wins / count * 100, 1), round(count / dict[mm]['Count'] * 100, 1), wins]
        except ZeroDivisionError as e:
            return '000'
    def get_open_w10(dict, mm, opener):
        count = 0
        w10 = 0
        for i, x in enumerate(dict[mm]['Opener']):
            if opener in x:
                w10 += dict[mm]['W10'][i][9]
                count += 1
        return round(w10/count, 1)
    def get_worker_list(dict, mm, waves):
        workers = []
        count = 0
        for c in range(waves):
            workers.append(0)
        for x in dict[mm]['W10']:
            count += 1
            for i, y in enumerate(workers):
                workers[i] += x[i]
        for w, n in enumerate(workers):
            workers[w] = round(workers[w]/count, 1)
        return workers
    def get_leak_list(dict, mm, waves):
        leaks = []
        count = 0
        for c in range(waves):
            leaks.append(0)
        for x in dict[mm]['Leaks']:
            count += 1
            for i, y in enumerate(leaks):
                leaks[i] += x[i]
        for w, n in enumerate(leaks):
            leaks[w] = round(leaks[w]/count, 1)
        return leaks

    def get_open_leak(dict, mm, opener):
        count = 0
        waves = 0
        leak = 0
        leak_w1 = 0
        for i, x in enumerate(dict[mm]['Opener']):
            if opener in x:
                for counter, l in enumerate(dict[mm]['Leaks'][i]):
                    if counter == 0:
                        count += 1
                        waves += 1
                        leak_w1 += l
                        leak += l
                    else:
                        leak += l
                        waves += 1
        return [round(leak_w1/count, 1), round(leak/waves, 1)]

        return round(w10/count, 1)
    def calc_elo(dict, mm):
        try:
            return round(dict[mm]['Elo'] / dict[mm]['Count'])
        except ZeroDivisionError as e:
            return '0'
    keys = ['Games:', 'Winrate:', 'Pickrate:', 'W on 10:', 'Leaks:', 'W1 Leak:']
    keys2 = ['Games:', 'Winrate:', 'Playrate:']
    url = 'https://cdn.legiontd2.com/icons/Items/'
    url2 = 'https://cdn.legiontd2.com/icons/'
    if transparency:
        mode = 'RGBA'
        colors = (0,0,0,0)
    else:
        mode = 'RGB'
        colors = (49,51,56)
    if playername != 'All':
        im = PIL.Image.new(mode=mode, size=(1470, 770), color=colors)
    else:
        im = PIL.Image.new(mode=mode, size=(1810, 780), color=colors)
    im2 = PIL.Image.new(mode="RGB", size=(88, 365), color=(25,25,25))
    im4 = PIL.Image.new(mode="RGB", size=(812, 760), color=(25, 25, 25))
    im5 = PIL.Image.new(mode="RGB", size=(320, 760), color=(25, 25, 25))
    I1 = ImageDraw.Draw(im)
    ttf = 'Files/RobotoCondensed-Regular.ttf'
    myFont_small = ImageFont.truetype(ttf, 20)
    myFont = ImageFont.truetype(ttf, 25)
    myFont_title = ImageFont.truetype(ttf, 30)
    if playername == 'All' or 'Nova cup' in playername:
        string = ''
    else:
        string = "'s"
        avatar_url = 'https://cdn.legiontd2.com/' + avatar
        avatar_response = requests.get(avatar_url)
        av_image = Image.open(BytesIO(avatar_response.content))
        gold_border = Image.open('Files/gold_64.png')
        if im_has_alpha(np.array(av_image)):
            im.paste(av_image, (24, 100), mask=av_image)
        else:
            im.paste(av_image, (24, 100))
        im.paste(gold_border, (24, 100), mask=gold_border)
    I1.text((10, 15), str(playername)+string+" Fiesta stats (From "+str(ranked_count)+" ranked games, Avg elo: "+str(avgelo)+")", font=myFont_title, stroke_width=2, stroke_fill=(0,0,0), fill=(255, 255, 255))
    I1.text((10, 55), 'Patches: ' + ', '.join(patch), font=myFont_small, stroke_width=2, stroke_fill=(0,0,0), fill=(255, 255, 255))
    x = 126
    y = 160
    y2 = 570
    y3 = 138
    step = 106
    offset = 50
    I1.text((x - 12, 90), "Most common Fiesta openers:", font=myFont, stroke_width=2, stroke_fill=(0,0,0), fill=(255, 255, 255))
    I1.text((x - 12, y2-70), "Most common Legion Spells with Fiesta:", font=myFont, stroke_width=2, stroke_fill=(0, 0, 0),fill=(255, 255, 255))
    if playername != 'All':
        I1.text((114+106*5, 90), "Fiesta stats:", font=myFont, stroke_width=2, stroke_fill=(0, 0, 0),fill=(255, 255, 255))
        im.paste(im4, (114+106*5, y - 32))
        fiesta_image_response = requests.get('https://cdn.legiontd2.com/icons/Items/Fiesta.png')
        fiesta_image = Image.open(BytesIO(fiesta_image_response.content))
        im.paste(fiesta_image, (x + step * 5, y - 20))
        I1.text((x + 70 + step * 5, y - 20), "Wins:", font=myFont, fill=(255, 255, 255))
        I1.text((x + 70 + step * 5, y + 10), "Losses:", font=myFont, fill=(255, 255, 255))
        I1.text((x + 50 + step * 6, y - 20), str(dict['Fiesta']['Wins']), font=myFont, fill=(0, 255, 0))
        I1.text((x + 50 + step * 6, y + 10), str(dict['Fiesta']['Count']-dict['Fiesta']['Wins']), font=myFont, fill=(255, 0, 0))
        winrate = round(dict['Fiesta']['Wins']/dict['Fiesta']['Count']*100, 1)
        if winrate >= 50:
            rgb = (0, 255, 0)
        else:
            rgb = (255, 0, 0)
        I1.text((x + 10 + step * 7, y - 5), "Winrate:", font=myFont, fill=(255, 255, 255))
        I1.text((x + step * 8, y - 5), str(winrate)+'%', font=myFont, fill=(rgb))
        workers = get_worker_list(dict, 'Fiesta', 10)
        leaks = get_leak_list(dict, 'Fiesta', 10)
        waves = ['1','2','3','4','5','6','7','8','9','10']
        plt.rcParams["figure.figsize"] = (9, 6.2)
        plt.rcParams['axes.autolimit_mode'] = 'round_numbers'
        params = {"ytick.color": "w",
                  "xtick.color": "w",
                  "axes.labelcolor": "w",
                  "axes.edgecolor": "w"}
        plt.rcParams.update(params)
        plt.grid()
        plt.plot(waves, workers,color='green',linewidth=3,marker='o',label='Workers')
        plt.xlabel('Waves')
        plt.ylabel('Workers')
        plt.legend(bbox_to_anchor=(0.45,1.07))
        plt.twinx()
        plt.plot(waves, leaks, color='red', linewidth=3, marker='o', label='Leak%')
        plt.ylabel('Leak%')
        plt.legend(bbox_to_anchor=(0.7,1.07))
        img_buf = io.BytesIO()
        plt.savefig(img_buf,transparent=True, format='png')
        plt.close()
        worker_graph = Image.open(img_buf)
        im.paste(worker_graph, (x-60 + step * 5, y), worker_graph)
    else:
        offset2 = 30
        I1.text((114 + 106 * 5, 90), "Fiesta Players:", font=myFont, stroke_width=2, stroke_fill=(0, 0, 0),fill=(255, 255, 255))
        leaderboard_ids = most_common(dict, 'Fiesta', 10, 'PlayerIds')
        im.paste(im5, (114 + 106 * 5, y - 32))
        for player in leaderboard_ids[0]:
            player_stats = get_wrpr(dict, 'Fiesta', player[0], 'PlayerIds')
            player_profile = apicall_getprofile(player[0])
            avatar = player_profile['avatarUrl']
            avatar_url = 'https://cdn.legiontd2.com/' + avatar
            avatar_response = requests.get(avatar_url)
            av_image = Image.open(BytesIO(avatar_response.content))
            gold_border = Image.open('Files/gold_64.png')
            av_image = av_image.resize((48,48))
            gold_border = gold_border.resize((48,48))
            if im_has_alpha(np.array(av_image)):
                im.paste(av_image, (126 + 106 * 5, y3), mask=av_image)
            else:
                im.paste(av_image, (126 + 106 * 5, y3))
            im.paste(gold_border, (126 + 106 * 5, y3), mask=gold_border)
            I1.text((180 + 106 * 5, y3-5), player_profile['playerName'], font=myFont_small,fill=(255, 255, 255))
            if player_stats[1] >= 50:
                rgb = (0,255,0)
            else:
                rgb = (255,0,0)
            I1.text((180 + 106 * 5, y3 - 5 + offset2),'(' + str(player_stats[1]) + '% wr, ' + str(player_stats[0]) + ' games)', font=myFont_small,fill=(rgb))
            y3 += 65
        #Graph
        x2 = 452
        I1.text((x2 + 106 * 5, 90), "Fiesta stats:", font=myFont, stroke_width=2, stroke_fill=(0, 0, 0),
                fill=(255, 255, 255))
        im.paste(im4, (x2 + 106 * 5, y - 32))
        fiesta_image_response = requests.get('https://cdn.legiontd2.com/icons/Items/Fiesta.png')
        fiesta_image = Image.open(BytesIO(fiesta_image_response.content))
        im.paste(fiesta_image, (x2+12 + step * 5, y - 20))
        I1.text((x2 + 80 + step * 5, y - 20), "Wins:", font=myFont, fill=(255, 255, 255))
        I1.text((x2 + 80 + step * 5, y + 10), "Losses:", font=myFont, fill=(255, 255, 255))
        I1.text((x2 + 60 + step * 6, y - 20), str(dict['Fiesta']['Wins']), font=myFont, fill=(0, 255, 0))
        I1.text((x2 + 60 + step * 6, y + 10), str(dict['Fiesta']['Count'] - dict['Fiesta']['Wins']), font=myFont,
                fill=(255, 0, 0))
        winrate = round(dict['Fiesta']['Wins'] / dict['Fiesta']['Count'] * 100, 1)
        if winrate >= 50:
            rgb = (0, 255, 0)
        else:
            rgb = (255, 0, 0)
        I1.text((x2 + 20 + step * 7, y - 5), "Winrate:", font=myFont, fill=(255, 255, 255))
        I1.text((x2 + 10 + step * 8, y - 5), str(winrate) + '%', font=myFont, fill=(rgb))
        workers = get_worker_list(dict, 'Fiesta', 10)
        leaks = get_leak_list(dict, 'Fiesta', 10)
        waves = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10']
        plt.rcParams["figure.figsize"] = (9, 6.2)
        plt.rcParams['axes.autolimit_mode'] = 'round_numbers'
        params = {"ytick.color": "w",
                  "xtick.color": "w",
                  "axes.labelcolor": "w",
                  "axes.edgecolor": "w"}
        plt.rcParams.update(params)
        plt.grid()
        plt.plot(waves, workers, color='green', linewidth=3, marker='o', label='Workers')
        plt.xlabel('Waves')
        plt.ylabel('Workers')
        plt.legend(bbox_to_anchor=(0.45, 1.07))
        plt.twinx()
        plt.plot(waves, leaks, color='red', linewidth=3, marker='o', label='Leak%')
        plt.ylabel('Leak%')
        plt.legend(bbox_to_anchor=(0.7, 1.07))
        img_buf = io.BytesIO()
        plt.savefig(img_buf, transparent=True, format='png')
        plt.close()
        worker_graph = Image.open(img_buf)
        im.paste(worker_graph, (x2 - 60 + step * 5, y), worker_graph)
    most_common_opens = most_common(dict, 'Fiesta', 5, 'Opener')[0]
    most_common_spells = most_common(dict, 'Fiesta', 5, 'Spell')[0]
    for unit in most_common_opens:
        im.paste(im2, (x-12, y-32))
        url_new = url2 + unit[0].replace(' ', '') + '.png'
        response = requests.get(url_new)
        opener_image = Image.open(BytesIO(response.content))
        im.paste(opener_image, (x, y-20))
        I1.text((x, y+offset*1), str(get_wrpr(dict, 'Fiesta', unit[0], 'Opener')[0]), font=myFont, fill=(255, 255, 255))
        I1.text((x, y+offset*2), str(get_wrpr(dict, 'Fiesta', unit[0], 'Opener')[1]) + '%', font=myFont, fill=(255, 255, 255))
        I1.text((x, y+offset*3), str(get_wrpr(dict, 'Fiesta', unit[0], 'Opener')[2]) + '%', font=myFont, fill=(255, 255, 255))
        I1.text((x, y+offset*4), str(get_open_w10(dict, 'Fiesta', unit[0])), font=myFont,fill=(255, 255, 255))
        I1.text((x, y+offset*5), str(get_open_leak(dict, 'Fiesta', unit[0])[1]) + '%', font=myFont, fill=(255, 255, 255))
        I1.text((x, y+offset*6), str(get_open_leak(dict, 'Fiesta', unit[0])[0]) + '%', font=myFont, fill=(255, 255, 255))
        x += 106
    x = 126
    for spell in most_common_spells:
        im.paste(im2, (x - 12, y2 - 32))
        url_new = url2 + spell[0].replace(' ', '') + '.png'
        if 'none' in url_new:
            url_new = 'https://cdn.legiontd2.com/icons/Granddaddy.png'
        if url_new == 'https://cdn.legiontd2.com/icons/PresstheAttack.png':
            url_new = 'https://cdn.legiontd2.com/icons/PressTheAttack.png'
        response = requests.get(url_new)
        spell_image = Image.open(BytesIO(response.content))
        im.paste(spell_image, (x, y2 - 20))
        I1.text((x, y2+offset*1), str(get_wrpr(dict, 'Fiesta', spell[0], 'Spell')[0]), font=myFont,fill=(255, 255, 255))
        I1.text((x, y2+offset*2), str(get_wrpr(dict, 'Fiesta', spell[0], 'Spell')[1]) + '%', font=myFont,fill=(255, 255, 255))
        I1.text((x, y2+offset*3), str(get_wrpr(dict, 'Fiesta', spell[0], 'Spell')[2]) + '%', font=myFont,fill=(255, 255, 255))
        x += 106
    im3 = PIL.Image.new(mode="RGB", size=(86+106*len(most_common_opens), 4), color=(169, 169, 169))
    for k in keys:
        im.paste(im3, (10, y+80))
        I1.text((10, y+50), k, font=myFont, stroke_width=2, stroke_fill=(0,0,0), fill=(255, 255, 255))
        y += 50
    for k in keys2:
        if k == 'Spells:':
            I1.text((10, y2 + 50), k, font=myFont, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
            y2 += 50
        else:
            im.paste(im3, (10, y2+80))
            I1.text((10, y2+50), k, font=myFont, stroke_width=2, stroke_fill=(0,0,0), fill=(255, 255, 255))
            y2 += 50
    im.save('Files/output.png')
    image_upload = imgur_client.upload_from_path('Files/output.png')
    print('Uploading output.png to Imgur...')
    return image_upload['link']

def create_image_mmstats_champion(dict, unit_dict, ranked_count, playerid, avgelo, patch, transparency = True):
    if playerid != 'all' and 'nova cup' not in playerid:
        playername = apicall_getprofile(playerid)['playerName']
        avatar = apicall_getprofile(playerid)['avatarUrl']
    else:
        playername = playerid.capitalize()
    def most_common(mm, amount, key):
        try:
            data = Counter(dict[mm][key].keys())
            return data.most_common(amount)
        except IndexError as e:
            return 'No data'
    def most_common_spell(unit):
        try:
            data = Counter(dict['Champion']['ChampionUnit'][unit]['Spell'])
            return [data.most_common(50)]
        except IndexError as e:
            return 'No data'
    def get_w10(unit):
        try:
            return round(dict['Champion']['ChampionUnit'][unit]['W10'] / dict['Champion']['ChampionUnit'][unit]['Count'], 1)
        except ZeroDivisionError as e:
            return '0'
    def calc_elo(mm):
        try:
            return round(dict[mm]['Elo'] / dict[mm]['Count'])
        except ZeroDivisionError as e:
            return '0'
    def calc_unit_wr(unit):
        try:
            return round(dict['Champion']['ChampionUnit'][unit]['Wins'] / dict['Champion']['ChampionUnit'][unit]['Count'] * 100, 1)
        except ZeroDivisionError as e:
            return '0'
    def get_spell_wr(unit, spell):
        wins = 0
        count = 0
        for i, x in enumerate(dict['Champion']['ChampionUnit'][unit]['Spell']):
            if spell in x:
                count += 1
                if dict['Champion']['ChampionUnit'][unit]['Results'][i] == 'won':
                    wins += 1
        try:
            return round(wins / count * 100, 1)
        except ZeroDivisionError as e:
            return '0'
    keys = ['Games:', 'Winrate:', 'W on 10:', 'Spell:', '', 'Games:', 'Winrate:','Games:', 'Winrate:', 'W on 10:', 'Spell:', '', 'Games:', 'Winrate:']
    url = 'https://cdn.legiontd2.com/icons/Items/'
    url2 = 'https://cdn.legiontd2.com/icons/'
    if transparency:
        mode = 'RGBA'
        colors = (0,0,0,0)
    else:
        mode = 'RGB'
        colors = (49,51,56)
    im = PIL.Image.new(mode=mode, size=(1485, 940), color=colors)
    im2 = PIL.Image.new(mode="RGB", size=(88, 425), color=(25,25,25))
    I1 = ImageDraw.Draw(im)
    ttf = 'Files/RobotoCondensed-Regular.ttf'
    myFont_small = ImageFont.truetype(ttf, 20)
    myFont = ImageFont.truetype(ttf, 25)
    myFont_title = ImageFont.truetype(ttf, 30)
    if playername == 'All' or 'Nova cup' in playername:
        string = ''
    else:
        string = "'s"
        avatar_url = 'https://cdn.legiontd2.com/' + avatar
        avatar_response = requests.get(avatar_url)
        av_image = Image.open(BytesIO(avatar_response.content))
        gold_border = Image.open('Files/gold_64.png')
        if im_has_alpha(np.array(av_image)):
            im.paste(av_image, (24, 100), mask=av_image)
        else:
            im.paste(av_image, (24, 100))
        im.paste(gold_border, (24, 100), mask=gold_border)
    I1.text((10, 15), str(playername)+string+" Champion stats (From "+str(ranked_count)+" ranked games, Avg elo: "+str(avgelo)+")", font=myFont_title, stroke_width=2, stroke_fill=(0,0,0), fill=(255, 255, 255))
    I1.text((10, 55), 'Patches: ' + ', '.join(patch), font=myFont_small, stroke_width=2, stroke_fill=(0,0,0), fill=(255, 255, 255))
    x = 126
    y = 190
    offset = 50
    count = 0
    line_1 = 0
    line_2 = 0
    for unit in unit_dict:
        if count == 13:
            line_1 = 13
            y = 600
            x = 126
        elif count < 13:
            line_1 = count+1
        if count == 26:
            line_2 = 13
            break
        elif count < 26 and count > 13:
            line_2 = count - 12
        im.paste(im2, (x - 12, y-90))
        if ' ' in unit:
            unit_string = unit.split(' ')
            unit_new = ''
            for s in unit_string:
                unit_new = unit_new + s.capitalize()
            url_new = url2 + unit_new + '.png'
        else:
            url_new = url2 + unit.capitalize() + '.png'
        response = requests.get(url_new)
        opener_image = Image.open(BytesIO(response.content))
        im.paste(opener_image, (x, y-78))
        I1.text((x, y), str(dict['Champion']['ChampionUnit'][unit]['Count']), font=myFont,fill=(255, 255, 255))
        I1.text((x, y + offset * 1), str(calc_unit_wr(unit)) + '%', font=myFont,fill=(255, 255, 255))
        I1.text((x, y + offset * 2), str(get_w10(unit)), font=myFont,fill=(255, 255, 255))
        spell_name = most_common_spell(unit)[0][0]
        url_new = url2 + spell_name[0].replace(' ', '') + '.png'
        if 'none' in url_new:
            url_new = 'https://cdn.legiontd2.com/icons/Granddaddy.png'
        if url_new == 'https://cdn.legiontd2.com/icons/PresstheAttack.png':
            url_new = 'https://cdn.legiontd2.com/icons/PressTheAttack.png'
        response = requests.get(url_new)
        spell_image = Image.open(BytesIO(response.content))
        im.paste(spell_image, (x, y + offset * 3))
        I1.text((x, y + offset * 4.6), str(spell_name[1]), font=myFont, fill=(255, 255, 255))
        I1.text((x, y + offset * 5.6), str(get_spell_wr(unit, spell_name[0])) + '%', font=myFont, fill=(255, 255, 255))
        x += 106
        count += 1
    im3 = PIL.Image.new(mode="RGB", size=(86 + 106 * line_1, 4), color=(169, 169, 169))
    x = 126
    y = 190
    count2 = 0
    for k in keys:
        if count2 == 7 and count > 13:
            y = 600
            x = 126
            im3 = PIL.Image.new(mode="RGB", size=(86 + 106 * line_2, 4), color=(169, 169, 169))
        elif count2 == 7 and line_2 == 0:
            break
        if (k != 'Open:') and (k != 'Spell:') and (k != ''):
            im.paste(im3, (10, y + 30))
        I1.text((10, y), k, font=myFont, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
        if (k != 'Open:') and (k != 'Spell:') and (k != ''):
            y += 50
        else:
            y += 40
        count2 += 1
    im.save('Files/output.png')
    image_upload = imgur_client.upload_from_path('Files/output.png')
    print('Uploading output.png to Imgur...')
    return image_upload['link']

def create_image_openstats(dict, games, playerid, avgelo, patch, transparency = True):
    if playerid != 'all' and 'nova cup' not in playerid:
        playername = apicall_getprofile(playerid)['playerName']
        avatar = apicall_getprofile(playerid)['avatarUrl']
    else:
        playername = playerid.capitalize()
    def calc_wr(dict, unit):
        try:
            return str(round(dict[unit]['OpenWins']/dict[unit]['Count'] * 100, 1))
        except ZeroDivisionError as e:
            return '0'
    def calc_pr(dict, unit):
        try:
            return str(round(dict[unit]['Count'] / games * 100, 1))
        except ZeroDivisionError as e:
            return '0'
    def get_w10(dict, i):
        try:
            return round(dict[i]['W4'] / dict[i]['Count'], 1)
        except ZeroDivisionError as e:
            return '0'
    keys = ['Games:', 'Winrate:', 'Playrate:', 'W on 4:', 'Best add:', '', 'Games:', 'Winrate:', 'Playrate:', 'Best MMs:','', 'Games:', 'Winrate:', 'Playrate:', 'Best\nSpells:','', 'Games:', 'Winrate:', 'Playrate:']
    url = 'https://cdn.legiontd2.com/icons/Items/'
    url2 = 'https://cdn.legiontd2.com/icons/'
    if transparency:
        mode = 'RGBA'
        colors = (0,0,0,0)
    else:
        mode = 'RGB'
        colors = (49,51,56)
    im = PIL.Image.new(mode=mode, size=(1700, 975), color=colors)
    im2 = PIL.Image.new(mode="RGB", size=(88, 900), color=(25, 25, 25))
    im3 = PIL.Image.new(mode="RGB", size=(1676, 4), color=(169, 169, 169))
    I1 = ImageDraw.Draw(im)
    ttf = 'Files/RobotoCondensed-Regular.ttf'
    myFont_small = ImageFont.truetype(ttf, 20)
    myFont = ImageFont.truetype(ttf, 25)
    myFont_title = ImageFont.truetype(ttf, 30)
    if playername == 'All' or 'Nova cup' in playername:
        suffix = ''
    else:
        suffix = "'s"
        avatar_url = 'https://cdn.legiontd2.com/' + avatar
        avatar_response = requests.get(avatar_url)
        av_image = Image.open(BytesIO(avatar_response.content))
        gold_border = Image.open('Files/gold_64.png')
        if im_has_alpha(np.array(av_image)):
            im.paste(av_image, (24, 100), mask=av_image)
        else:
            im.paste(av_image, (24, 100))
        im.paste(gold_border, (24, 100), mask=gold_border)
    I1.text((10, 15), str(playername) + suffix + " Opener stats (From " + str(games) + " ranked games, Avg elo: " + str(avgelo) + ")", font=myFont_title, stroke_width=2,stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    I1.text((10, 55), 'Patches: ' + ', '.join(patch), font=myFont_small, stroke_width=2, stroke_fill=(0, 0, 0),fill=(255, 255, 255))
    x = 126
    y = 175
    offset = 45
    for i in range(15):
        im.paste(im2, (x - 12, 88))
        x += 106
    x = 126
    for i, unit in enumerate(dict):
        if i == 15 or dict[unit]['Count'] == 0:
            crop = 15 - i
            break
        if ' ' in unit:
            string = unit.split(' ')
            unit_new = ''
            for s in string:
                unit_new = unit_new + s.capitalize()
            url_new = url2 + unit_new + '.png'
        else:
            url_new = url2 + unit.capitalize() + '.png'
        response = requests.get(url_new)
        unit_image = Image.open(BytesIO(response.content))
        im.paste(unit_image, (x, 100))
        I1.text((x, y), str(dict[unit]['Count']), font=myFont, fill=(255, 255, 255))
        I1.text((x, y+offset), str(calc_wr(dict, unit)) + '%', font=myFont, fill=(255, 255, 255))
        I1.text((x, y+offset*2), str(calc_pr(dict, unit)) + '%', font=myFont, fill=(255, 255, 255))
        I1.text((x, y+offset*3), str(get_w10(dict, unit)), font=myFont, fill=(255, 255, 255))
        def get_perf_score(dict2, key):
            new_dict = {}
            for xy in dict2[key]:
                if dict2[key][xy]['Wins'] / dict2[key][xy]['Count'] < dict2['OpenWins'] / dict2['Count']:
                    continue
                new_dict[xy] = dict2[key][xy]['Wins'] / dict2[key][xy]['Count'] * (dict2[key][xy]['Count'] / dict2['Count'])
            newIndex = sorted(new_dict,key=lambda k: new_dict[k], reverse=True)
            return newIndex
        newIndex = get_perf_score(dict[unit], 'OpenWith')
        if ' ' in newIndex[0]:
            string = newIndex[0].split(' ')
            unit_new = ''
            for s in string:
                unit_new = unit_new + s.capitalize()
            url_new = url2 + unit_new + '.png'
        else:
            url_new = url2 + newIndex[0].capitalize() + '.png'
        if url_new == 'https://cdn.legiontd2.com/icons/PackRatNest.png':
            url_new = 'https://cdn.legiontd2.com/icons/PackRat(Footprints).png'
        response = requests.get(url_new)
        temp_image = Image.open(BytesIO(response.content))
        im.paste(temp_image, (x, y + offset * 4))
        I1.text((x, y + 25+offset * 5), str(dict[unit]['OpenWith'][newIndex[0]]['Count']), font=myFont, fill=(255, 255, 255))
        I1.text((x, y + 25+offset * 6), str(round(dict[unit]['OpenWith'][newIndex[0]]['Wins'] / dict[unit]['OpenWith'][newIndex[0]]['Count']*100, 1)) + '%', font=myFont, fill=(255, 255, 255))
        I1.text((x, y + 25+offset * 7), str(round(dict[unit]['OpenWith'][newIndex[0]]['Count'] / dict[unit]['Count']*100, 1)) + '%', font=myFont, fill=(255, 255, 255))
        newIndex = get_perf_score(dict[unit], 'MMs')
        url_new = url + newIndex[0].capitalize() + '.png'
        if url_new == 'https://cdn.legiontd2.com/icons/Items/Cashout.png':
            url_new = 'https://cdn.legiontd2.com/icons/Items/CashOut.png'
        if url_new == 'https://cdn.legiontd2.com/icons/Items/Lockin.png':
            url_new = 'https://cdn.legiontd2.com/icons/Items/LockIn.png'
        if url_new == 'https://cdn.legiontd2.com/icons/Items/Doublelockin.png':
            url_new = 'https://cdn.legiontd2.com/icons/Items/DoubleLockIn.png'
        response = requests.get(url_new)
        temp_image = Image.open(BytesIO(response.content))
        im.paste(temp_image, (x, y + 25+offset * 8))
        I1.text((x, y + 50+offset * 9), str(dict[unit]['MMs'][newIndex[0]]['Count']), font=myFont,fill=(255, 255, 255))
        I1.text((x, y + 50+offset * 10), str(round(dict[unit]['MMs'][newIndex[0]]['Wins'] / dict[unit]['MMs'][newIndex[0]]['Count']*100, 1)) + '%', font=myFont, fill=(255, 255, 255))
        I1.text((x, y + 50+offset * 11),str(round(dict[unit]['MMs'][newIndex[0]]['Count'] / dict[unit]['Count'] * 100, 1)) + '%',font=myFont, fill=(255, 255, 255))
        newIndex = get_perf_score(dict[unit], 'Spells')
        if ' ' in newIndex[0]:
            string = newIndex[0].split(' ')
            spell_new = ''
            for s in string:
                spell_new = spell_new + s.capitalize()
            url_new = url2 + spell_new + '.png'
        else:
            url_new = url2 + newIndex[0].capitalize() + '.png'
        if 'None' in url_new:
            url_new = 'https://cdn.legiontd2.com/icons/Granddaddy.png'
        if url_new == 'https://cdn.legiontd2.com/icons/PresstheAttack.png':
            url_new = 'https://cdn.legiontd2.com/icons/PressTheAttack.png'
        response = requests.get(url_new)
        temp_image = Image.open(BytesIO(response.content))
        im.paste(temp_image, (x, y + 50+offset * 12))
        I1.text((x, y + 75 + offset * 13), str(dict[unit]['Spells'][newIndex[0]]['Count']), font=myFont,fill=(255, 255, 255))
        I1.text((x, y + 75 + offset * 14), str(round(dict[unit]['Spells'][newIndex[0]]['Wins'] / dict[unit]['Spells'][newIndex[0]]['Count'] * 100, 1)) + '%',font=myFont, fill=(255, 255, 255))
        I1.text((x, y + 75 + offset * 15),str(round(dict[unit]['Spells'][newIndex[0]]['Count'] / dict[unit]['Count'] * 100, 1)) + '%',font=myFont, fill=(255, 255, 255))
        x += 106
    for k in keys:
        if (k != 'Best add:') and (k != 'Best MMs:') and (k != '') and (k != 'Best\nSpells:'):
            im.paste(im3, (10, y+30))
        if k == 'Best\nSpells:':
            I1.text((10, y-5), k, font=myFont, stroke_width=2, stroke_fill=(0,0,0), fill=(255, 255, 255))
        else:
            I1.text((10, y), k, font=myFont, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
        if (k != 'Best add:') and (k != 'Best MMs:') and (k != '') and (k != 'Best\nSpells:'):
            y += offset
        else:
            y += offset - 10
    im.save('Files/output.png')
    image_upload = imgur_client.upload_from_path('Files/output.png')
    print('Uploading output.png to Imgur...')
    return image_upload['link']


def extract_values(obj, key):
    arr = []

    def extract(obj, arr, key):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == key:
                    arr.append(v)
                elif isinstance(v, (dict, list)):
                    extract(v, arr, key)
        elif isinstance(obj, list):
            for item in obj:
                extract(item, arr, key)
        return key + ":", arr

    results = extract(obj, arr, key)
    return results


def count_value(playername, value, player_names, data):
    value_count = 0
    for i in range(len(player_names[1])):
        if str(player_names[1][i]).lower() == playername and str(data[1][i]).lower() == value:
            value_count = value_count + 1
    return value_count

mercs = {"Snail": (20, 6), "Giant Snail": (20, 6), "Robo": (40, 10), "Lizard": (40, 12), "Dragon Turtle": (40, 12), "Brute": (60, 15), "Fiend": (60, 18), "Dino": (80, 24),
         "Hermit": (80, 20), "Cannoneer": (100, 30), "Imp": (100, 13), "Safety Mole": (120, 30), "Drake": (120, 36), "Pack Leader": (160, 40),
         "Mimic": (160, 40), "Witch": (200, 50), "Ogre": (200, 50), "Ghost Knight": (240, 60), "Four Eyes": (240, 60), "Centaur": (280, 70),
         "Shaman": (320, 80), "Siege Ram": (320, 80), "Needler": (360, 90), "Kraken": (400, 100), "Froggo": (0, 3)}

creep_values = {"Crab": (72, 6), "Wale": (84, 7), "Hopper": (90, 5), "Flying Chicken": (96, 8), "Scorpion": (108, 9), "Scorpion King": (108, 36),
                "Rocko": (114, 19), "Sludge": (120, 10), "Blob": (120, 2), "Kobra": (132, 11), "Carapace": (144, 12), "Granddaddy": (150, 63),
                "Quill Shooter": (156, 13), "Mantis": (168, 14), "Drill Golem": (180, 30), "Killer Slug": (192, 16), "Quadrapus": (204, 17),
                "Giant Quadrapus": (204, 68), "Cardinal": (216, 12), "Metal Dragon": (228, 19), "Wale Chief": (252, 42), "Dire Toad": (276, 23),
                "Maccabeus": (300, 126), "Legion Lord": (360, 30), "Legion King": (360, 120)}
wave_values = (72,84,90,96,108,114,120,132,144,150,156,168,180,192,204,216,228,252,276,300,360)

def count_mythium(send):
    send_amount = 0
    for x in send:
        send_amount += mercs.get(x)[0]
    return send_amount

def calc_leak(leak, wave):
    leak_amount = 0
    send_amount = 0
    wave_total = wave_values[wave]
    for x in leak:
        if x in creep_values:
            leak_amount += creep_values.get(x)[1]
        else:
            leak_amount += mercs.get(x)[1]
    return round(leak_amount / wave_total * 100, 1)

def count_elochange(playername, player_names, data):
    value_count = 0
    for i in range(len(player_names[1])):
        if str(player_names[1][i]).lower() == playername:
            value_count = value_count + data[1][i]
    return value_count

def handle_response(message, author) -> str:
    p_message = message.lower()
    if '!elo fine' in p_message:    return str(apicall_elo('fine', 0) + ' :eggplant:')
    if 'julian' in p_message:       return 'julian sucks'
    if 'penny' in p_message:        return 'penny sucks'
    if 'green' in p_message:        return '<:green:1136426397619978391> & aggressive'
    if 'kidkpro' in p_message:      return ':eggplant:'
    if 'widderson' in p_message:    return ':banana:'
    if 'ofma' in p_message:         return ':a: :b:'
    if 'drachir' in p_message:      return '<:GK:1161013811927601192>'
    if 'shea' in p_message:         return 'sister? <:sheastare:1121047323464712273>'
    if 'aviator' in p_message:      return '<:aviator:1180232477537738944>'
    if 'lucy' in p_message:         return 'snail angle <:Dice:1180232938399469588>'
    if 'king' in p_message:         return "like its the most fun i've had playing legion pretty much"
    if 'genom' in p_message:        return ":rat:"
    if 'quacker' in p_message:      return ":duck: quack"
    if 'toikan' in p_message:       return "nyctea, :older_man:"
    if 'jokeonu' in p_message:      return "look dis brah, snacc"
    if 'mrbuzz' in p_message:       return "(On his smurf)"
    if 'nyctea' in p_message:       return "toikan,"
    if '!github' in p_message:      return 'https://github.com/Drachiir/Legion-Elo-Bot'
    if '!test' in p_message:        return ffstats()
    if '!update' in p_message and str(author) == 'drachir_':    return ladder_update(p_message[8:])
    if '!novaupdate' in p_message and str(author) == 'drachir_':    return pull_games_by_id(message.split('|')[1],message.split('|')[2])
    if '!update' in p_message and str(author) != 'drachir_':    return 'thanks ' + str(author) + '!'


def apicall_getid(playername):
    request_type = 'players/byName/' + playername
    url = 'https://apiv2.legiontd2.com/' + request_type
    print(request_type)
    try:
        api_response = requests.get(url, headers=header)
        if 'Limit Exceeded' in api_response.text:
            return 1
        api_response.raise_for_status()
    except requests.exceptions.HTTPError:
        return 0
    else:
        playerid = json.loads(api_response.text)
        print(playerid['_id'])
        return playerid['_id']


def apicall_getprofile(playerid):
    url = 'https://apiv2.legiontd2.com/players/byId/' + playerid
    api_response = requests.get(url, headers=header)
    playername = json.loads(api_response.text)
    return playername


def apicall_getstats(playerid):
    request_type = 'players/stats/' + playerid
    url = 'https://apiv2.legiontd2.com/' + request_type
    api_response = requests.get(url, headers=header)
    stats = json.loads(api_response.text)
    return stats

def get_games_saved_count(playerid):
    if playerid == 'all':
        count = 0
        path1 = str(pathlib.Path(__file__).parent.resolve()) + "/Profiles/"
        playernames = os.listdir(path1)
        for i, x in enumerate(playernames):
            path2 = str(pathlib.Path(__file__).parent.resolve()) + "/Profiles/" + playernames[i] + "/gamedata/"
            try:
                json_files = [pos_json for pos_json in os.listdir(path2) if pos_json.endswith('.json')]
            except FileNotFoundError:
                continue
            except NotADirectoryError:
                continue
            count += len(json_files)
        return count
    else:
        path = str(pathlib.Path(__file__).parent.resolve()) + "/Profiles/" + playerid + "/gamedata/"
        if Path(Path(str(path))).is_dir():
            json_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.json')]
            if len(json_files) == 0:
                return 200
            else:
                return len(json_files)
        else:
            return 200

def apicall_pullgamedata(playerid, offset, path, expected):
    ranked_count = 0
    games_count = 0
    output = []
    url = 'https://apiv2.legiontd2.com/players/matchHistory/' + str(playerid) + '?limit=' + str(50) + '&offset=' + str(offset) + '&countResults=false'
    print('Pulling ' + str(50) + ' games from API...')
    api_response = requests.get(url, headers=header)
    raw_data = json.loads(api_response.text)
    print('Saving ranked games.')
    for x in raw_data:
        if ranked_count == expected:
            break
        if (raw_data == {'message': 'Internal server error'}) or (raw_data == {'err': 'Entry not found.'}):
            break
        if (x['queueType'] == 'Normal'):
            ranked_count += 1
            if Path(Path(str(path + 'gamedata/')+x['date'].split('.')[0].replace('T', '-').replace(':', '-')+'_'+x['version'].replace('.', '-')+'_'+str(x['gameElo'])+ '_' + str(x['_id']) + ".json")).is_file():
                print('File already there, breaking loop.')
                break
            with open(str(path + 'gamedata/')+x['date'].split('.')[0].replace('T', '-').replace(':', '-')+'_'+x['version'].replace('.', '-')+'_'+str(x['gameElo'])+'_' + str(x['_id']) + ".json", "w") as f:
                json.dump(x, f)
        games_count += 1
    output.append(ranked_count)
    output.append(games_count)
    return output

def get_games_loop(playerid, offset, path, expected, timeout_limit = 5):
    data = apicall_pullgamedata(playerid, offset, path, expected)
    count = data[0]
    games_count = data[1]
    timeout = 0
    while count < expected:
        if timeout == timeout_limit:
            print('Timeout while pulling games.')
            break
        offset += 50
        data = apicall_pullgamedata(playerid, offset, path, expected)
        if data[0] + data[1] == 0:
            timeout += 1
        count += data[0]
        games_count += data[1]
    else:
        print('All '+str(expected)+' required games pulled.')
    return games_count

def apicall_getmatchistory(playerid, games, min_elo=0, patch='0', update = 0, earlier_than_wave10 = False, sort_by = "date"):
    patch_list = []
    if patch != '0' and "," in patch:
        patch_list = patch.split(',')
    elif patch != '0' and "-" not in patch and "+" not in patch:
        patch_list = patch.split(',')
    elif patch != "0" and "+" in patch and "-" not in patch:
        patch_new = patch.split("+")
        if len(patch_new) == 2:
            patch_new = patch_new[1].split('.')
            for x in range(12 - int(patch_new[1])):
                if int(patch_new[1]) + x < 10:
                    prefix = "0"
                else:
                    prefix = ""
                patch_list.append(patch_new[0] + "." + prefix + str(int(patch_new[1]) + x))
        else:
            return []
    elif patch != "0" and "-" in patch:
        patch_new = patch.split("-")
        if len(patch_new) == 2:
            patch_new2 = patch_new[0].split('.')
            patch_new3 = patch_new[1].split('.')
            for x in range(int(patch_new3[1])-int(patch_new2[1])+1):
                if int(patch_new2[1]) + x < 10:
                    prefix = "0"
                else:
                    prefix = ""
                patch_list.append(patch_new2[0] + "." + prefix + str(int(patch_new2[1]) + x))
        else:
            return []
    if len(patch_list) > 5:
        return "Too many patches."
    games_count = 0
    if playerid != 'all' and 'nova cup' not in playerid:
        path = str(pathlib.Path(__file__).parent.resolve()) + "/Profiles/" + playerid + "/"
        if not Path(Path(str(path))).is_dir():
            print(playerid + ' profile not found, creating new folder...')
            new_profile = True
            Path(str(path+'gamedata/')).mkdir(parents=True, exist_ok=True)
            with open(str(path) + "gamecount_" + playerid + ".txt", "w") as f:
                data = get_games_loop(playerid, 0, path, games)
                playerstats = apicall_getstats(playerid)
                try:
                    wins = playerstats['rankedWinsThisSeason']
                except KeyError:
                    wins = 0
                try:
                    losses = playerstats['rankedLossesThisSeason']
                except KeyError:
                    losses = 0
                ranked_games = wins + losses
                lines = [str(ranked_games), str(data)]
                f.write('\n'.join(lines))
        else:
            new_profile = False
            for file in glob.glob(path + '*.txt'):
                file_path = file
            with open(file, 'r') as f:
                txt = f.readlines()
                ranked_games_old = int(txt[0])
                games_amount_old = int(txt[1])
            playerstats = apicall_getstats(playerid)
            try:
                wins = playerstats['rankedWinsThisSeason']
            except KeyError:
                wins = 0
            try:
                losses = playerstats['rankedLossesThisSeason']
            except KeyError:
                losses = 0
            ranked_games = wins + losses
            games_diff = ranked_games - ranked_games_old
            if ranked_games_old < ranked_games:
                games_count += get_games_loop(playerid, 0, path, games_diff)
            json_files = [pos_json for pos_json in os.listdir(path + 'gamedata/') if pos_json.endswith('.json')]
            if len(json_files) < games:
                games_count += get_games_loop(playerid, games_amount_old, path, games-len(json_files))
            with open(str(path) + "gamecount_" + playerid + ".txt", "w") as f:
                f.truncate(0)
                lines = [str(ranked_games), str(games_amount_old+games_count)]
                f.write('\n'.join(lines))
        if update == 0:
            raw_data = []
            json_files = [pos_json for pos_json in os.listdir(path + 'gamedata/') if pos_json.endswith('.json')]
            count = 0
            if sort_by == "date":
                sorted_json_files = sorted(json_files, key=lambda x: time.mktime(time.strptime(x.split('_')[-4].split('/')[-1], "%Y-%m-%d-%H-%M-%S")), reverse=True)
            elif sort_by == "elo":
                sorted_json_files = sorted(json_files, key=lambda x: x.split("_")[-2], reverse=True)
            for i, x in enumerate(sorted_json_files):
                with (open(path + '/gamedata/' + x) as f):
                    raw_data_partial = json.load(f)
                    f.close()
                    if raw_data_partial['gameElo'] >= min_elo:
                        if patch == '0':
                            if count == games:
                                break
                            if earlier_than_wave10 == True:
                                count += 1
                                raw_data.append(raw_data_partial)
                            elif raw_data_partial['endingWave'] >= 10 and earlier_than_wave10 == False:
                                count += 1
                                raw_data.append(raw_data_partial)
                        else:
                            if count == games:
                                break
                            for x in patch_list:
                                if str(raw_data_partial['version']).startswith('v'+x):
                                    if earlier_than_wave10 == True:
                                        count += 1
                                        raw_data.append(raw_data_partial)
                                    elif raw_data_partial['endingWave'] >= 10 and earlier_than_wave10 == False:
                                        count += 1
                                        raw_data.append(raw_data_partial)
    else:
        if 'nova cup' in playerid:
            path2 = str(pathlib.Path(__file__).parent.resolve()) + "/Profiles/" + playerid + '/gamedata/'
            json_files = []
            raw_data = []
            if patch != '0':
                for y in patch_list:
                    json_files.extend([path2 + pos_json for pos_json in os.listdir(path2) if pos_json.endswith('.json') and pos_json.split('_')[-3].startswith('v' + y.replace('.', '-')) and int(pos_json.split('_')[-2]) >= min_elo])
            else:
                json_files.extend([path2 + pos_json for pos_json in os.listdir(path2) if pos_json.endswith('.json') and int(pos_json.split('_')[-2]) >= min_elo])
            sorted_json_files = sorted(json_files, key=lambda x: time.mktime(time.strptime(x.split('_')[-4].split('/')[-1], "%Y-%m-%d-%H-%M-%S")), reverse=True)
        else:
            path1 = str(pathlib.Path(__file__).parent.resolve()) + "/Profiles/"
            playernames = sorted(os.listdir(path1))
            print(playernames)
            raw_data = []
            json_files = []
            json_counter = 0
            for i, x in enumerate(playernames):
                if '.zip' in x:
                    continue
                # if x == "0":
                #     continue
                # playerid = apicall_getid(playernames[i])
                # if playerid == 0:
                #     print('invalid id')
                #     continue
                path2 = str(pathlib.Path(__file__).parent.resolve()) + "/Profiles/" + playernames[i] + '/gamedata/'
                # print(path2)
                # os.rename(path2, str(pathlib.Path(__file__).parent.resolve()) + "/Profiles/" + str(playerid))
                # os.rename(str(pathlib.Path(__file__).parent.resolve()) + "/Profiles/" + str(playerid) + "/gamecount_" + playernames[i] + ".txt", str(pathlib.Path(__file__).parent.resolve()) + "/Profiles/" + str(playerid) + "/gamecount_" + str(playerid) + ".txt")
                if patch != '0':
                    for y in patch_list:
                        try:
                            json_files.extend([path2 + pos_json for pos_json in os.listdir(path2) if pos_json.endswith('.json') and pos_json.split('_')[-3].startswith('v'+y.replace('.', '-')) and int(pos_json.split('_')[-2]) >= min_elo])
                        except FileNotFoundError:
                            continue
                else:
                    try:
                        json_files.extend([path2 + pos_json for pos_json in os.listdir(path2) if pos_json.endswith('.json') and int(pos_json.split('_')[-2]) >= min_elo])
                    except FileNotFoundError:
                        continue
            if sort_by == "date":
                sorted_json_files = sorted(json_files, key=lambda x: time.mktime(time.strptime(x.split('_')[-4].split('/')[-1],"%Y-%m-%d-%H-%M-%S")), reverse=True)
            elif sort_by == "elo":
                sorted_json_files = sorted(json_files, key=lambda x: x.split("_")[-2], reverse=True)
        count = 0
        for i, x in enumerate(sorted_json_files):
            if count == games and games != 0:
                break
            with open(x) as f:
                raw_data_partial = json.load(f)
                f.close()
                # print(x.split('_')[0] + '-' + raw_data_partial['date'].split('T')[1].replace(':', '-').split('.')[0] + '_v10-' + x.split('_v10-')[1])
                # os.rename(x, x.split('_')[0] + '-' + raw_data_partial['date'].split('T')[1].replace(':', '-').split('.')[0] + '_v10-' + x.split('_v10-')[1])
                if (raw_data_partial not in raw_data):
                    if earlier_than_wave10 == True:
                        count += 1
                        raw_data.append(raw_data_partial)
                    elif raw_data_partial['endingWave'] >= 10 and earlier_than_wave10 == False:
                        count += 1
                        raw_data.append(raw_data_partial)
    if update == 0:
        print(len(raw_data))
        return raw_data
    else:
        if new_profile:
            return data
        else:
            return games_diff

def ffstats():
    games = apicall_getmatchistory("all", 0, patch="11.01", earlier_than_wave10=True)
    ff_count = 0
    win_team = []
    lose_team = []
    for game in games:
        if game["endingWave"] < 10:
            ff_count += 1
    return str(len(games)) + " " + str(ff_count)

def ladder_update(amount=100):
    url = 'https://apiv2.legiontd2.com/players/stats?limit='+str(amount)+'&sortBy=overallElo&sortDirection=-1'
    api_response = requests.get(url, headers=header)
    leaderboard = json.loads(api_response.text)
    games_count = 0
    for i, player in enumerate(leaderboard):
        print(str(i+1) + '. ' + player["profile"][0]["playerName"])
        ranked_games = player['rankedWinsThisSeason'] + player['rankedLossesThisSeason']
        print(ranked_games)
        if ranked_games >= 200:
            games_count += apicall_getmatchistory(player["_id"], 200, 0, '0', 1)
        elif ranked_games == 0:
            print('No games this season.')
            continue
        else:
            games_count += apicall_getmatchistory(player["_id"], ranked_games, 0, '0', 1)
    return 'Pulled ' + str(games_count) + ' new games from the Top ' + str(amount)

def pull_games_by_id(file, name):
    path = '/home/container/Profiles/' + name
    if not Path(Path(str(path + '/gamedata/'))).is_dir():
        print(name + ' profile not found, creating new folder...')
        Path(str(path + '/gamedata/')).mkdir(parents=True, exist_ok=True)
    with open(file, 'r') as f:
        txt = f.readlines()
        print('Pulling ' + str(len(txt)) + ' games from API...')
        for game_id in txt:
            game_id = str(game_id).replace('\n', '')
            print('Pulling game id: ' + str(game_id))
            url = 'https://apiv2.legiontd2.com/games/byId/'+game_id+'?includeDetails=true'
            print(url)
            api_response = requests.get(url, headers=header)
            x = json.loads(api_response.text)
            if (x == {'message': 'Internal server error'}) or (x == {'err': 'Entry not found.'}):
                    print(x)
                    break
            if Path(Path(str(path + '/gamedata/') + x['date'].split('.')[0].replace('T', '-').replace(':','-') + '_' +x['version'].replace('.', '-') + '_' + str(x['gameElo']) + '_' + str(x['_id']) + ".json")).is_file():
                print('File already there, breaking loop.')
                break
            with open(str(path + '/gamedata/') + x['date'].split('.')[0].replace('T', '-').replace(':','-') + '_' +x['version'].replace('.', '-') + '_' + str(x['gameElo']) + '_' + str(x['_id']) + ".json","w") as f:
                json.dump(x, f)
    return 'Success'

def apicall_matchhistorydetails(playerid):
    playername = apicall_getprofile(playerid)['playerName']
    history_raw = apicall_getmatchistory(playerid, 10)
    player_names = extract_values(history_raw, 'playerName')
    game_results = extract_values(history_raw, 'gameResult')
    wins = count_value(str(playername).lower(), 'won', player_names, game_results)
    elochanges = extract_values(history_raw, 'eloChange')
    elochange_final = count_elochange(str(playername).lower(), player_names, elochanges)
    output = []
    if elochange_final > 0:
        output.append('+' + str(elochange_final))
    else:
        output.append(elochange_final)
    output.append(wins)
    return output

def apicall_leaderboard(ranks=10, transparency=True):
    url = 'https://apiv2.legiontd2.com/players/stats?limit=' + str(ranks) + '&sortBy=overallElo&sortDirection=-1'
    api_response = requests.get(url, headers=header)
    leaderboard = json.loads(api_response.text)
    player_dict = {}
    url = 'https://cdn.legiontd2.com/icons/Items/'
    url2 = 'https://cdn.legiontd2.com/icons/'
    if transparency:
        mode = 'RGBA'
        colors = (0, 0, 0, 0)
    else:
        mode = 'RGB'
        colors = (49, 51, 56)
    im = PIL.Image.new(mode=mode, size=(758, 830), color=colors)
    im2 = PIL.Image.new(mode="RGB", size=(720, 76), color=(25, 25, 25))
    I1 = ImageDraw.Draw(im)
    ttf = 'Files/RobotoCondensed-Regular.ttf'
    myFont_small = ImageFont.truetype(ttf, 20)
    myFont = ImageFont.truetype(ttf, 25)
    myFont_title = ImageFont.truetype(ttf, 30)
    x = 24
    y = 24
    offset = 80
    for i, player in enumerate(leaderboard):
        im.paste(im2, (x-6,y-6))
        avatar_url = 'https://cdn.legiontd2.com/' + player["profile"][0]["avatarUrl"]
        avatar_response = requests.get(avatar_url)
        av_image = Image.open(BytesIO(avatar_response.content))
        gold_border = Image.open('Files/gold_64.png')
        if im_has_alpha(np.array(av_image)):
            im.paste(av_image, (x, y), mask=av_image)
        else:
            im.paste(av_image, (x, y))
        im.paste(gold_border, (x, y), mask=gold_border)
        last_game = apicall_getmatchistory(player["_id"], 1, earlier_than_wave10=True)
        game_date = datetime.strptime(last_game[0]["date"].split(".000Z")[0].replace("T", "-"), '%Y-%m-%d-%H:%M:%S')
        if game_date < datetime.now() - timedelta(days=2) or player["profile"][0]["playerName"] == "InDaHole":
            tent = Image.open('Files/tent.png')
            im.paste(tent, (x, y), mask=tent)
        I1.text((x + offset, y), str(i+1)+". "+player["profile"][0]["playerName"], font=myFont, stroke_width=2, stroke_fill=(0, 0, 0),fill=(255, 255, 255))
        width = I1.textlength(str(i+1)+". "+player["profile"][0]["playerName"], font=myFont)
        try:
            I1.text((x+width+10+offset, y+5), player["profile"][0]["guildTag"], font=myFont_small, stroke_width=2, stroke_fill=(0, 0, 0),fill=(247, 203, 27))
        except KeyError:
            print(player["profile"][0]["playerName"]+ " has no guild.")
        if player["overallElo"] >= 2800:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Legend.png'
        elif player["overallElo"] >= 2600:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Grandmaster.png'
        elif player["overallElo"] >= 2400:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/SeniorMaster.png'
        elif player["overallElo"] >= 2200:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Master.png'
        else:
            rank_url = 'https://cdn.legiontd2.com/icons/Ranks/Expert.png'
        rank_response = requests.get(rank_url)
        rank_image = Image.open(BytesIO(rank_response.content))
        rank_image = rank_image.resize((32,32))
        im.paste(rank_image, (x + offset, y+30), mask=rank_image)
        I1.text((x + offset+ 40, y+30), str(player["overallElo"]), font=myFont, stroke_width=2, stroke_fill=(0, 0, 0),fill=(255, 255, 255))
        width2 = I1.textlength(str(player["overallElo"]), font=myFont)
        I1.text((x + offset + 60+width2, y + 33), "W: "+str(player["rankedWinsThisSeason"])+" L: "+str(player["rankedLossesThisSeason"]), font=myFont_small, stroke_width=2,stroke_fill=(0, 0, 0), fill=(255, 255, 255))
        width2 += I1.textlength("W: "+str(player["rankedWinsThisSeason"])+" L: "+str(player["rankedLossesThisSeason"]), font=myFont_small)
        winrate = round(player["rankedWinsThisSeason"]/(player["rankedWinsThisSeason"]+player["rankedLossesThisSeason"])*100, 1)
        if winrate >= 50:
            rgb = (0,255,0)
        else:
            rgb = (255, 0, 0)
        I1.text((x + offset + 70+width2, y + 33), "(WR: "+str(winrate)+ "%)", font=myFont_small, stroke_width=2,stroke_fill=(0, 0, 0), fill=(rgb))
        width2 += I1.textlength("(WR: "+str(winrate)+ "%)", font=myFont_small)
        if player["winStreak"] != 0:
            I1.text((x + offset + 90+width2, y + 33), "Win Streak: "+str(player["winStreak"]), font=myFont_small, stroke_width=2,stroke_fill=(0, 0, 0), fill=(0, 255, 0))
            width2 +=  I1.textlength("Win Streak: "+str(player["winStreak"]), font=myFont_small)
        else:
            I1.text((x + offset + 90+width2, y + 33), "Loss Streak: "+str(player["lossStreak"]), font=myFont_small, stroke_width=2,stroke_fill=(0, 0, 0), fill=(255, 0, 0))
            width2 += I1.textlength("Loss Streak: "+str(player["lossStreak"]), font=myFont_small)
        lp_response = requests.get("https://cdn.legiontd2.com/icons/LadderPoints.png")
        lp_image = Image.open(BytesIO(lp_response.content))
        lp_image = lp_image.resize((32, 32))
        im.paste(lp_image, (x + offset+int(width2)+110, y + 30), mask=lp_image)
        I1.text((x + offset + 142 + width2, y + 33), " LP: "+str(player["ladderPoints"]), font=myFont_small, stroke_width=2,stroke_fill=(0, 0, 0), fill=(255,255,255))
        y += offset
    im.save('Files/output.png')
    image_upload = imgur_client.upload_from_path('Files/output.png')
    print('Uploading output.png to Imgur...')
    return image_upload['link']


def apicall_elograph(playername, games, patch, transparency = True):
    playerid = apicall_getid(playername)
    if playerid == 0:
        return 'Player ' + playername + ' not found.'
    if playerid == 1:
        return 'API limit reached.'
    if games == 0:
        games = get_games_saved_count(playerid)
    try:
        history_raw = apicall_getmatchistory(playerid, games, 0, patch, earlier_than_wave10=True)
    except TypeError as e:
        print(e)
        return playername + ' has not played enough games.'
    if history_raw == "Too many patches.":
        return "Too many patches."
    games = len(history_raw)
    if games == 0:
        return 'No games found.'
    playerids = list(divide_chunks(extract_values(history_raw, 'playerId')[1], 4))
    gameresult = list(divide_chunks(extract_values(history_raw, 'gameResult')[1], 4))
    elo = list(divide_chunks(extract_values(history_raw, 'overallElo')[1], 4))
    elo_change = list(divide_chunks(extract_values(history_raw, 'eloChange')[1], 4))
    gameid = extract_values(history_raw, '_id')
    patches = extract_values(history_raw, 'version')[1]
    new_patches = []
    for x in patches:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches = list(dict.fromkeys(new_patches))
    count = 0
    elo_per_game = []
    while count < games:
        playerids_ranked = playerids[count]
        elo_ranked = elo[count]
        elo_change_ranked = elo_change[count]
        for i, x in enumerate(playerids_ranked):
            if x == playerid:
                elo_per_game.insert(0, elo_ranked[i]+elo_change_ranked[i])
        count += 1
    #Image generation
    x = 126
    y = 160
    if transparency:
        mode = 'RGBA'
        colors = (0,0,0,0)
    else:
        mode = 'RGB'
        colors = (49,51,56)
    im = PIL.Image.new(mode=mode, size=(1180, 770), color=colors)
    im2 = PIL.Image.new(mode="RGB", size=(88, 900), color=(25, 25, 25))
    im3 = PIL.Image.new(mode="RGB", size=(1676, 4), color=(169, 169, 169))
    I1 = ImageDraw.Draw(im)
    ttf = 'Files/RobotoCondensed-Regular.ttf'
    #player_profile = apicall_getprofile(playerid)
    myFont_small = ImageFont.truetype(ttf, 20)
    myFont = ImageFont.truetype(ttf, 25)
    myFont_title = ImageFont.truetype(ttf, 30)
    I1.text((10, 15), playername.capitalize() + "'s Elo Graph (From " + str(games) + " ranked games)", font=myFont_title, stroke_width=2, stroke_fill=(0, 0, 0), fill=(255, 255, 255))
    I1.text((10, 55), 'Patches: ' + ', '.join(patches), font=myFont_small, stroke_width=2, stroke_fill=(0, 0, 0),fill=(255, 255, 255))
    #matplotlib graph
    params = {"ytick.color": "w",
              "xtick.color": "w",
              "axes.labelcolor": "w",
              "axes.edgecolor": "w",
              "figure.figsize": (14, 8),
              'axes.autolimit_mode': 'round_numbers',
              'font.weight': 'bold'}
    if len(elo_per_game) > 100:
        marker_plot = ''
    else:
        marker_plot = 'o'
    plt.rcParams.update(params)
    plt.grid(linewidth=2)
    plt.xlabel('Games', weight='bold')
    plt.ylabel('Elo', weight='bold')
    plt.margins(x=0)
    plt.plot(range(1,games+1), elo_per_game, color='red', marker=marker_plot, linewidth=2.5, label='Elo')
    plt.xticks(ticks=plt.xticks()[0], labels=plt.xticks()[0].astype(int))
    plt.margins(x=0)
    img_buf = io.BytesIO()
    plt.savefig(img_buf, transparent=True, format='png')
    plt.close()
    elo_graph = Image.open(img_buf)
    im.paste(elo_graph, (-100,0), elo_graph)

    im.save('Files/output.png')
    image_upload = imgur_client.upload_from_path('Files/output.png')
    print('Uploading output.png to Imgur...')
    return image_upload['link']

def apicall_sendstats(playername, starting_wave, games, min_elo, patch, sort="date"):
    if starting_wave > 20:
        return "Enter a wave before 21."
    elif starting_wave < 0:
        return "Invalid Wave number."
    starting_wave -= 1
    if playername.lower() == 'all':
        playerid = 'all'
        suffix = ''
        if ((games == 0) or (games > get_games_saved_count(playerid)* 0.25)) and (min_elo < 2700) and (patch == '0'):
            return 'Too many games, please limit data.'
    elif 'nova cup' in playername:
        suffix = ''
        playerid = playername
    else:
        suffix = "'s"
        playerid = apicall_getid(playername)
        if playerid == 0:
            return 'Player ' + playername + ' not found.'
        if playerid == 1:
            return 'API limit reached.'
        if games == 0:
            games = get_games_saved_count(playerid)
    try:
        history_raw = apicall_getmatchistory(playerid, games, min_elo=min_elo, patch=patch, sort_by=sort)
    except TypeError as e:
        print(e)
        return playername + ' has not played enough games.'
    games = len(history_raw)
    if games == 0:
        return 'No games found.'
    if 'nova cup' in playerid:
        playerid = 'all'
    playerids = list(divide_chunks(extract_values(history_raw, 'playerId')[1], 4))
    sends = list(divide_chunks(extract_values(history_raw, 'mercenariesSentPerWave')[1], 4))
    kingups = list(divide_chunks(extract_values(history_raw, 'kingUpgradesPerWave')[1], 4))
    gameresults = list(divide_chunks(extract_values(history_raw, 'gameResult')[1], 4))
    endingwaves = extract_values(history_raw, 'endingWave')
    patches = extract_values(history_raw, 'version')
    game_ids = extract_values(history_raw, '_id')
    gameelo = extract_values(history_raw, 'gameElo')
    gameelo_list = []
    patches2 = list(dict.fromkeys(patches[1]))
    new_patches = []
    for x in patches2:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches2 = list(dict.fromkeys(new_patches))
    print('starting sendstats command...')
    count = 0
    send_count = 0
    sends_dict = {}
    while count < games:
        playerids_ranked = playerids[count]
        sends_ranked = sends[count]
        endingwave_ranked = endingwaves[1][count]
        kingups_ranked = kingups[count]
        gameresults_ranked = gameresults[count]
        gameelo_list.append(gameelo[1][count])
        for i, x in enumerate(playerids_ranked):
            if playerid == 'all' or x == playerid:
                save_on_1 = False
                if endingwave_ranked <= starting_wave+1:
                    continue
                if starting_wave != -1:
                    if len(sends_ranked[i][starting_wave]) == 0 and len(kingups_ranked[i][starting_wave]) == 0:
                        continue
                elif starting_wave == -1:
                    if len(sends_ranked[i][0]) == 0 and len(kingups_ranked[i][0]) == 0:
                        save_on_1 = True
                    else:
                        continue
                if (save_on_1 == False) and (len(sends_ranked[i][starting_wave]) > 0 or len(kingups_ranked[i][starting_wave]) > 0):
                    send_count += 1
                    for n in range(endingwave_ranked-starting_wave-1):
                        sent = False
                        if len(sends_ranked[i][starting_wave+n+1]) > 0 or len(kingups_ranked[i][starting_wave+n+1]) > 0:
                            if "Wave " + str(starting_wave+n+2) in sends_dict:
                                sends_dict["Wave " + str(starting_wave+n+2)] += 1
                                sent = True
                                break
                            else:
                                sends_dict["Wave " + str(starting_wave+n+2)] = 1
                                sent = True
                                break
                elif save_on_1 == True:
                    send_count += 1
                    for n in range(endingwave_ranked-1):
                        sent = False
                        if len(sends_ranked[i][n]) > 0 or len(kingups_ranked[i][n]) > 0:
                            if "Wave " + str(n+1) in sends_dict:
                                sends_dict["Wave " + str(n+1)] += 1
                                sent = True
                                break
                            else:
                                sends_dict["Wave " + str(n+1)] = 1
                                sent = True
                                break
        count += 1
    if not sends_dict:
        return "No Wave" + str(starting_wave+1) + " sends found."
    else:
        avg_gameelo = round(sum(gameelo_list) / len(gameelo_list))
        newIndex = sorted(sends_dict, key=lambda x: sends_dict[x], reverse=True)
        sends_dict = {k: sends_dict[k] for k in newIndex}
        result_string = ""
        for key in list(sends_dict):
            result_string += key + ": "+ str(sends_dict[key])+" sends ("+str(round(sends_dict[key]/send_count*100,1))+"%)\n"
        if playerid == "all":
            games_num = games * 4
        else:
            games_num = games
        if starting_wave != -1:
            return playername.capitalize() + suffix + " Wave " + str(starting_wave+1) + " send stats. (Last " + str(games) + " ranked games, Avg. Elo: "+str(avg_gameelo)+")\n" +\
                "Sends on Wave "+str(starting_wave+1)+": "+str(send_count)+" ("+str(round(send_count/games_num*100,1))+"%)\nNext send(s):\n"+ result_string
        else:
            return playername.capitalize() + suffix + " Wave 1 save stats. (Last " + str(games) + " ranked games, Avg. Elo: " + str(avg_gameelo) + ")\n" + \
                "Saves on Wave 1: " + str(send_count) + " (" + str(round(send_count / games_num * 100, 1)) + "%)\nNext send(s):\n" + result_string

def apicall_wave1tendency(playername, option, games, min_elo, patch, sort="date"):
    if playername.lower() == 'all':
        playerid = 'all'
        suffix = ''
        if ((games == 0) or (games > get_games_saved_count(playerid)* 0.25)) and (min_elo < 2700) and (patch == '0'):
            return 'Too many games, please limit data.'
    elif 'nova cup' in playername:
        suffix = ''
        playerid = playername
    else:
        suffix = "'s"
        playerid = apicall_getid(playername)
        if playerid == 0:
            return 'Player ' + playername + ' not found.'
        if playerid == 1:
            return 'API limit reached.'
        if games == 0:
            games = get_games_saved_count(playerid)
    count = 0
    snail_count = 0
    kingup_atk_count = 0
    kingup_regen_count = 0
    kingup_spell_count = 0
    save_count = 0
    leaks_count = 0
    try:
        history_raw = apicall_getmatchistory(playerid, games, min_elo=min_elo, patch=patch, sort_by=sort)
    except TypeError as e:
        print(e)
        return playername + ' has not played enough games.'
    games = len(history_raw)
    if games == 0:
        return 'No games found.'
    if 'nova cup' in playerid:
        playerid = 'all'
    playerids = list(divide_chunks(extract_values(history_raw, 'playerId')[1], 4))
    if option == 'send' or playerid == 'all':
        snail = list(divide_chunks(extract_values(history_raw, 'mercenariesSentPerWave')[1], 4))
        kingup = list(divide_chunks(extract_values(history_raw, 'kingUpgradesPerWave')[1], 4))
    elif option == 'received':
        snail = list(divide_chunks(extract_values(history_raw, 'mercenariesReceivedPerWave')[1], 4))
        kingup = list(divide_chunks(extract_values(history_raw, 'opponentKingUpgradesPerWave')[1], 4))
    leaks = list(divide_chunks(extract_values(history_raw, 'leaksPerWave')[1], 4))
    gameid = extract_values(history_raw, '_id')
    gameelo = extract_values(history_raw, 'gameElo')
    gameelo_list = []
    while count < games:
        playerids_ranked = playerids[count]
        snail_ranked = snail[count]
        kingup_ranked = kingup[count]
        leaks_ranked = leaks[count]
        gameelo_list.append(gameelo[1][count])
        for i, x in enumerate(playerids_ranked):
            if playerid == 'all' or x == playerid:
                if len(snail_ranked[i][0]) > 0:
                    if str(snail_ranked[i][0][0]) == 'Snail':
                        snail_count = snail_count + 1
                        if option == 'send' and playerid != 'all':
                            if i == 0:
                                if len(leaks_ranked[2][0]) != 0:
                                    leaks_count += 1
                            if i == 1:
                                if len(leaks_ranked[3][0]) != 0:
                                    leaks_count += 1
                            if i == 2:
                                if len(leaks_ranked[1][0]) != 0:
                                    leaks_count += 1
                            if i == 3:
                                if len(leaks_ranked[0][0]) != 0:
                                    leaks_count += 1
                        if option == 'received' or playerid == 'all':
                            if len(leaks_ranked[i][0]) != 0:
                                leaks_count += 1
                        continue
                elif len(kingup_ranked[i][0]) > 0:
                    if str(kingup_ranked[i][0][0]) == 'Upgrade King Attack':
                        kingup_atk_count = kingup_atk_count + 1
                        continue
                    if str(kingup_ranked[i][0][0]) == 'Upgrade King Regen':
                        kingup_regen_count = kingup_regen_count + 1
                        continue
                    if str(kingup_ranked[i][0][0]) == 'Upgrade King Spell':
                        kingup_spell_count = kingup_spell_count + 1
                        continue
                else:
                    save_count = save_count + 1
                    continue
        count += 1
    send_total = kingup_atk_count+kingup_regen_count+kingup_spell_count+snail_count+save_count
    kingup_total = kingup_atk_count+kingup_regen_count+kingup_spell_count
    avg_gameelo = round(sum(gameelo_list) / len(gameelo_list))
    if playerid == 'all':
        option = ''
    if send_total > 4:
        return ((playername).capitalize() +suffix+" Wave 1 " + option + " stats: (Last " + str(games) + " ranked games, Avg. Elo: "+str(avg_gameelo)+") <:Stare:1148703530039902319>\nKingup: " + \
            str(kingup_total) + ' | ' + str(round(kingup_total/send_total*100,1)) + '% (Attack: ' + str(kingup_atk_count) + ' Regen: ' + str(kingup_regen_count) + \
            ' Spell: ' + str(kingup_spell_count) + ')\nSnail: ' + str(snail_count) + ' | ' + str(round(snail_count/send_total*100,1)) + '% (Leak count: ' + str(leaks_count) + ' (' + str(round(leaks_count/snail_count*100, 2)) + '%))'+\
            '\nSave: ' + str(save_count)) + ' | '  + str(round(save_count/send_total*100,1)) + '%'
    else:
        return 'Not enough ranked data'


def apicall_winrate(playername, playername2, option, games, patch):
    playerid = apicall_getid(playername)
    if playerid == 0:
        return 'Player ' + playername + ' not found.'
    if playerid == 1:
        return 'API limit reached.'
    if playername2.lower() != 'all':
        playerid2 = apicall_getid(playername2)
        if playerid2 == 0:
            return 'Player ' + playername2 + ' not found.'
    if games == 0:
        games = get_games_saved_count(playerid)
    count = 0
    win_count = 0
    game_count = 0
    ranked_count = 0
    queue_count = 0
    games_limit = games * 4
    playerid2_list = []
    gameresults = []
    try:
        history_raw = apicall_getmatchistory(playerid, games, 0, patch)
    except TypeError as e:
        print(e)
        return playername + ' has not played enough games.'
    if history_raw == "Too many patches.":
        return "Too many patches."
    games = len(history_raw)
    if games == 0:
        return 'No games found.'
    games_limit = games * 4
    playerids = list(divide_chunks(extract_values(history_raw, 'playerId')[1], 1))
    gameresult = list(divide_chunks(extract_values(history_raw, 'gameResult')[1], 1))
    gameid = extract_values(history_raw, '_id')
    patches = extract_values(history_raw, 'version')[1]
    patches_list = []
    while count < games_limit:
        gameresult_ranked_west = gameresult[count] + gameresult[count + 1]
        gameresult_ranked_east = gameresult[count + 2] + gameresult[count + 3]
        playerids_ranked_west = playerids[count] + playerids[count + 1]
        playerids_ranked_east = playerids[count + 2] + playerids[count + 3]
        if playername2.lower() != 'all':
            for i, x in enumerate(playerids_ranked_west):
                if x == playerid:
                    if option == 'against':
                        if playerids_ranked_east[0] == playerid2:
                            patches_list.append(patches[ranked_count])
                            game_count += 1
                            if gameresult_ranked_west[i] == 'won':
                                win_count += 1
                        elif playerids_ranked_east[1] == playerid2:
                            patches_list.append(patches[ranked_count])
                            game_count += 1
                            if gameresult_ranked_west[i] == 'won':
                                win_count += 1
                    elif option == 'with':
                        if playerids_ranked_west[0] == playerid2:
                            patches_list.append(patches[ranked_count])
                            game_count += 1
                            if gameresult_ranked_west[i] == 'won':
                                win_count += 1
                        elif playerids_ranked_west[1] == playerid2:
                            patches_list.append(patches[ranked_count])
                            game_count += 1
                            if gameresult_ranked_west[i] == 'won':
                                win_count += 1
            for i, x in enumerate(playerids_ranked_east):
                if x == playerid:
                    if option == 'against':
                        if playerids_ranked_west[0] == playerid2:
                            patches_list.append(patches[ranked_count])
                            game_count += 1
                            if gameresult_ranked_east[i] == 'won':
                                win_count += 1
                        elif playerids_ranked_west[1] == playerid2:
                            patches_list.append(patches[ranked_count])
                            game_count += 1
                            if gameresult_ranked_east[i] == 'won':
                                win_count += 1
                    elif option == 'with':
                        if playerids_ranked_east[0] == playerid2:
                            patches_list.append(patches[ranked_count])
                            game_count += 1
                            if gameresult_ranked_east[i] == 'won':
                                win_count += 1
                        elif playerids_ranked_east[1] == playerid2:
                            patches_list.append(patches[ranked_count])
                            game_count += 1
                            if gameresult_ranked_east[i] == 'won':
                                win_count += 1
        else:
            patches_list.append(patches[ranked_count])
            for i, x in enumerate(playerids_ranked_west):
                if x == playerid:
                    if option == 'against':
                        playerid2_list.append(playerids_ranked_east[0])
                        gameresults.append(gameresult_ranked_west[i])
                        playerid2_list.append(playerids_ranked_east[1])
                        gameresults.append(gameresult_ranked_west[i])
                    elif option == 'with':
                        if playerids_ranked_west[0] != playerid:
                            playerid2_list.append(playerids_ranked_west[0])
                            gameresults.append(gameresult_ranked_west[i])
                        elif playerids_ranked_west[1] != playerid:
                            playerid2_list.append(playerids_ranked_west[1])
                            gameresults.append(gameresult_ranked_west[i])
            for i, x in enumerate(playerids_ranked_east):
                if x == playerid:
                    if option == 'against':
                        playerid2_list.append(playerids_ranked_west[0])
                        gameresults.append(gameresult_ranked_east[i])
                        playerid2_list.append(playerids_ranked_west[1])
                        gameresults.append(gameresult_ranked_east[i])
                    elif option == 'with':
                        if playerids_ranked_east[0] != playerid:
                            playerid2_list.append(playerids_ranked_east[0])
                            gameresults.append(gameresult_ranked_east[i])
                        elif playerids_ranked_east[1] != playerid:
                            playerid2_list.append(playerids_ranked_east[1])
                            gameresults.append(gameresult_ranked_east[i])
        count += 4
        ranked_count += 1
    patches = list(dict.fromkeys(patches_list))
    new_patches = []
    for x in patches:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches = list(dict.fromkeys(new_patches))
    if playername2.lower() == 'all':
        most_common_mates = Counter(playerid2_list).most_common(6)
        winrates = []
        for i, x in enumerate(most_common_mates):
            counter = 0
            for c, v in enumerate(playerid2_list):
                if v == x[0]:
                    if gameresults[c] == 'won':
                        counter += 1
            winrates.append(round(counter / x[1] * 100, 2))
            winrates.append(counter)
        return str(playername).capitalize() + "'s winrate " + option + ' any players (From ' + str(ranked_count) + ' ranked games)\n' +\
            apicall_getprofile(most_common_mates[0][0])['playerName'] + ': ' + str(winrates[1]) + ' win - ' + str(most_common_mates[0][1] - winrates[1]) + ' lose (' + str(winrates[0]) + '% winrate)\n' + \
            apicall_getprofile(most_common_mates[1][0])['playerName'] + ': ' + str(winrates[3]) + ' win - ' + str(most_common_mates[1][1] - winrates[3]) + ' lose (' + str(winrates[2]) + '% winrate)\n' + \
            apicall_getprofile(most_common_mates[2][0])['playerName'] + ': ' + str(winrates[5]) + ' win - ' + str(most_common_mates[2][1] - winrates[5]) + ' lose (' + str(winrates[4]) + '% winrate)\n' + \
            apicall_getprofile(most_common_mates[3][0])['playerName'] + ': ' + str(winrates[7]) + ' win - ' + str(most_common_mates[3][1] - winrates[7]) + ' lose (' + str(winrates[6]) + '% winrate)\n' + \
            apicall_getprofile(most_common_mates[4][0])['playerName'] + ': ' + str(winrates[9]) + ' win - ' + str(most_common_mates[4][1] - winrates[9]) + ' lose (' + str(winrates[8]) + '% winrate)\n' + \
            apicall_getprofile(most_common_mates[5][0])['playerName'] + ': ' + str(winrates[11]) + ' win - ' + str(most_common_mates[5][1] - winrates[11]) + ' lose (' + str(winrates[10]) + '% winrate)\n' + \
            'Patches: ' + ', '.join(patches)
    else:
        try: return str(playername).capitalize() + "'s winrate " + option + ' ' + str(playername2).capitalize() + '(From ' + str(game_count) + ' ranked games)\n' +\
            str(win_count) + ' win - ' + str(game_count-win_count) + ' lose (' + str(round(win_count / game_count * 100, 2)) +\
            '% winrate)\nPatches: ' + ', '.join(patches)
        except ZeroDivisionError as e:
            print(e)
            return str(playername).capitalize() + ' and ' + str(playername2).capitalize() + ' have no games played ' + option + ' each other.'


def apicall_elcringo(playername, games, patch, min_elo, option, sort="date"):
    if playername.lower() == 'all':
        playerid = 'all'
        suffix = ''
        if ((games == 0) or (games > get_games_saved_count(playerid)* 0.25)) and (min_elo < 2700) and (patch == '0' or patch == '10'):
            return 'Too many games, please limit data.'
        if games == 0:
            games = get_games_saved_count(playerid)
    elif 'nova cup' in playername:
        suffix = ''
        playerid = playername
    else:
        playerid = apicall_getid(playername)
        if playerid == 0:
            return 'Player ' + playername + ' not found.'
        if playerid == 1:
            return 'API limit reached, you can still use "all" commands.'
        suffix = "'s"
        if games == 0:
            games = get_games_saved_count(playerid)
    count = 0
    save_count_list = []
    save_count_pre10_list = []
    save_count = 0
    save_count_pre10 = 0
    ending_wave_list = []
    worker_10_list = []
    income_10_list = []
    mythium_list = []
    mythium_pre10_list = []
    mythium_list_pergame = []
    kinghp_list = []
    leaks_list = []
    leaks_pre10_list = []
    try:
        history_raw = apicall_getmatchistory(playerid, games, min_elo, patch, sort_by=sort, earlier_than_wave10=True)
    except TypeError as e:
        print(e)
        return playername + ' has not played enough games.'
    if history_raw == "Too many patches.":
        return "Too many patches."
    games = len(history_raw)
    if games == 0:
        return 'No games found.'
    if 'nova cup' in playerid:
        playerid = 'all'
    playerids = list(divide_chunks(extract_values(history_raw, 'playerId')[1], 4))
    endingwaves = extract_values(history_raw, 'endingWave')
    snail = list(divide_chunks(extract_values(history_raw, 'mercenariesSentPerWave')[1], 4))
    kingup = list(divide_chunks(extract_values(history_raw, 'kingUpgradesPerWave')[1], 4))
    workers = list(divide_chunks(extract_values(history_raw, 'workersPerWave')[1], 4))
    income = list(divide_chunks(extract_values(history_raw, 'incomePerWave')[1], 4))
    leaks = list(divide_chunks(extract_values(history_raw, 'leaksPerWave')[1], 4))
    kinghp_left = extract_values(history_raw, 'leftKingPercentHp')
    kinghp_right = extract_values(history_raw, 'rightKingPercentHp')
    gameid = extract_values(history_raw, '_id')
    gameelo = extract_values(history_raw, 'gameElo')
    gameelo_list = []
    patches = extract_values(history_raw, 'version')
    patches2 = list(dict.fromkeys(patches[1]))
    new_patches = []
    for x in patches2:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches2 = list(dict.fromkeys(new_patches))
    print('starting elcringo command...')
    while count < games:
        ending_wave_list.append(endingwaves[1][count])
        playerids_ranked = playerids[count]
        snail_ranked = snail[count]
        kingup_ranked = kingup[count]
        workers_ranked = workers[count]
        income_ranked = income[count]
        leaks_ranked = leaks[count]
        mythium_list_pergame.clear()
        gameelo_list.append(gameelo[1][count])
        for i, x in enumerate(playerids_ranked):
            if x == playerid or playerid == 'all':
                for n, s in enumerate(snail_ranked[i]):
                    small_send = 0
                    send = count_mythium(snail_ranked[i][n]) + len(kingup_ranked[i][n]) * 20
                    mythium_list_pergame.append(send)
                    if n <= 9:
                        if workers_ranked[i][n] > 5:
                            small_send = (workers_ranked[i][n] - 5) / 4 * 20
                        if send <= small_send and option.value == "Yes":
                            save_count_pre10 += 1
                        elif send == 0 and option.value == "No":
                            save_count_pre10 += 1
                    elif n > 9:
                        if patches[1][count].startswith('v11'):
                            worker_adjusted = workers_ranked[i][n]
                        elif patches[1][count].startswith('v10'):
                            worker_adjusted = workers_ranked[i][n] * (pow((1 + 6 / 100), n+1))
                        small_send = worker_adjusted / 4 * 20
                        if send <= small_send and option.value == "Yes":
                            save_count += 1
                        elif send == 0 and option.value == "No":
                            save_count += 1
                mythium_list.append(sum(mythium_list_pergame))
                mythium_pre10 = 0
                for counter, myth in enumerate(mythium_list_pergame):
                    mythium_pre10 += myth
                    if counter == 9:
                        break
                mythium_pre10_list.append(mythium_pre10)
                try:
                    worker_10_list.append(workers_ranked[i][9])
                    income_10_list.append(income_ranked[i][9])
                except Exception:
                    pass
                leak_amount = 0
                leak_pre10_amount = 0
                for y in range(endingwaves[1][count]):
                    if len(leaks_ranked[i][y]) > 0:
                        p = calc_leak(leaks_ranked[i][y], y)
                        leak_amount += p
                        if y < 10:
                            leak_pre10_amount += p
                leaks_list.append(leak_amount/endingwaves[1][count])
                leaks_pre10_list.append(leak_pre10_amount/10)
                try:
                    if i == 0 or 1:
                        kinghp_list.append(kinghp_left[1][count][9])
                    else:
                        kinghp_list.append(kinghp_right[1][count][9])
                except Exception:
                    pass
            mythium_list_pergame.clear()
        save_count_pre10_list.append(save_count_pre10)
        save_count_list.append(save_count)
        save_count_pre10 = 0
        save_count = 0
        count += 1
    waves_post10 = round(sum(ending_wave_list) / len(ending_wave_list), 2) - 10
    if playerid == 'all':
        saves_pre10 = round(sum(save_count_pre10_list) / len(save_count_pre10_list)/4, 2)
        saves_post10 = round(sum(save_count_list) / len(save_count_list)/4, 2)
    else:
        saves_pre10 = round(sum(save_count_pre10_list) / len(save_count_pre10_list), 2)
        saves_post10 = round(sum(save_count_list) / len(save_count_list), 2)
    mythium_pre10 = round(sum(mythium_pre10_list) / len(mythium_pre10_list))
    mythium = round(sum(mythium_list) / len(mythium_list))
    leaks_total = round(sum(leaks_list) / len(leaks_list), 1)
    leaks_pre10_total = round(sum(leaks_pre10_list) / len(leaks_pre10_list), 1)
    king_hp_10 = sum(kinghp_list) / len(kinghp_list)
    avg_gameelo = sum(gameelo_list) / len(gameelo_list)

    return (playername).capitalize() +suffix+" elcringo stats(Averages from " + str(games) +" ranked games):<:GK:1161013811927601192>\n" \
        'Saves first 10: ' + str(saves_pre10) + '/10 waves (' + str(round(saves_pre10 / 10 * 100, 2)) + '%)\n' +\
        'Saves after 10: ' + str(saves_post10)+'/' + str(round(waves_post10, 2)) + ' waves (' + str(round(saves_post10 / waves_post10 * 100, 2)) + '%)\n'\
        'Worker on 10: ' + str(round(sum(worker_10_list) / len(worker_10_list), 2)) + "\n" \
        'Leaks: ' + str(leaks_total) + "% (First 10: "+str(leaks_pre10_total)+"%)\n" \
        'Income on 10: ' + str(round(sum(income_10_list) / len(income_10_list), 1)) + "\n" \
        'King hp on 10: ' + str(round(king_hp_10 * 100, 2)) + '%\n' + \
        'Mythium sent: ' + str(mythium) + ' (Pre 10: '+str(mythium_pre10)+', Post 10: '+str(mythium-mythium_pre10)+')\n' + \
        'Game elo: ' + str(round(avg_gameelo)) + '\n' + \
        'Patches: ' + ', '.join(patches2)

def apicall_elcringo2(playername, games, patch, min_elo, option):
    if playername.lower() == 'all':
        playerid = 'all'
        suffix = ''
        if ((games == 0) or (games > get_games_saved_count(playerid)* 0.25)) and (min_elo < 2700) and (patch == '0'):
            return 'Too many games, please limit data.'
        if games == 0:
            games = get_games_saved_count(playerid)
    elif 'nova cup' in playername:
        suffix = ''
        playerid = playername
    else:
        playerid = apicall_getid(playername)
        if playerid == 0:
            return 'Player ' + playername + ' not found.'
        if playerid == 1:
            return 'API limit reached, you can still use "all" commands.'
        suffix = "'s"
        if games == 0:
            games = get_games_saved_count(playerid)
    try:
        history_raw = apicall_getmatchistory(playerid, games, min_elo, patch)
    except TypeError as e:
        print(e)
        return playername + ' has not played enough games.'
    if history_raw == "Too many patches.":
        return "Too many patches."
    games = len(history_raw)
    if games == 0:
        return 'No games found.'
    if 'nova cup' in playerid:
        playerid = 'all'
    gameelo_list = []
    count = 0
    elcringo_dict = {}
    player_dict = {}
    for i in range(21):
        player_dict["Wave"+str(i)] = {}
    playerids = list(divide_chunks(extract_values(history_raw, 'playerId')[1], 4))
    sends = list(divide_chunks(extract_values(history_raw, 'mercenariesSentPerWave')[1], 4))
    kingup = list(divide_chunks(extract_values(history_raw, 'kingUpgradesPerWave')[1], 4))
    workers = list(divide_chunks(extract_values(history_raw, 'workersPerWave')[1], 4))
    income = list(divide_chunks(extract_values(history_raw, 'incomePerWave')[1], 4))
    leaks = list(divide_chunks(extract_values(history_raw, 'leaksPerWave')[1], 4))
    kinghp_left = extract_values(history_raw, 'leftKingPercentHp')
    kinghp_right = extract_values(history_raw, 'rightKingPercentHp')
    gameid = extract_values(history_raw, '_id')
    gameelo = extract_values(history_raw, 'gameElo')
    endingwaves = extract_values(history_raw, 'endingWave')
    patches = extract_values(history_raw, 'version')
    patches2 = list(dict.fromkeys(patches[1]))
    new_patches = []
    for x in patches2:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches2 = list(dict.fromkeys(new_patches))
    print('starting elcringo command...')

def apicall_openstats(playername, games, min_elo, patch, sort="date"):
    novacup = False
    if playername == 'all':
        playerid = 'all'
        if ((games == 0) or (games > get_games_saved_count(playerid)* 0.25)) and (min_elo < 2700) and (patch == '0'):
            return 'Too many games, please limit data.'
        if games == 0:
            games = get_games_saved_count(playerid)
    elif 'nova cup' in playername:
        novacup = True
        playerid = playername
    else:
        playerid = apicall_getid(playername)
        if playerid == 0:
            return 'Player ' + playername + ' not found.'
        if playerid == 1:
            return 'API limit reached, you can still use "all" commands.'
        if games == 0:
            games = get_games_saved_count(playerid)
    try:
        history_raw = apicall_getmatchistory(playerid, games, min_elo, patch, sort_by=sort)
    except TypeError as e:
        print(e)
        return playername + ' has not played enough games.'
    if history_raw == "Too many patches.":
        return "Too many patches."
    if len(history_raw) == 0:
        return 'No games found.'
    games = len(history_raw)
    unit_dict = {}
    with open('Files/units.json', 'r') as f:
        units_json = json.load(f)
        units_extracted = extract_values(units_json, 'unitId')
        value_extracted = extract_values(units_json, 'totalValue')[1]
    for i, x in enumerate(units_extracted[1]):
        if value_extracted[i] and int(value_extracted[i]) > 0:
            string = x
            string = string.replace('_', ' ')
            string = string.replace(' unit id', '')
            unit_dict[string] = {'Count': 0,'OpenWins': 0,'W4': 0,'OpenWith': {},'MMs': {},'Spells': {}}
    unit_dict['pack rat nest'] = {'Count': 0, 'OpenWins': 0,'W4': 0, 'OpenWith': {},'MMs': {},'Spells': {}}
    if 'nova cup' in playerid:
        playerid = 'all'
    playerids = list(divide_chunks(extract_values(history_raw, 'playerId')[1], 4))
    masterminds = list(divide_chunks(extract_values(history_raw, 'legion')[1], 4))
    gameresult = list(divide_chunks(extract_values(history_raw, 'gameResult')[1], 4))
    workers = list(divide_chunks(extract_values(history_raw, 'workersPerWave')[1], 4))
    spell = list(divide_chunks(extract_values(history_raw, 'chosenSpell')[1], 4))
    fighters = list(divide_chunks(extract_values(history_raw, 'buildPerWave')[1], 4))
    gameelo = extract_values(history_raw, 'gameElo')
    patches = extract_values(history_raw, 'version')
    gameid = extract_values(history_raw, '_id')
    patches = list(dict.fromkeys(patches[1]))
    new_patches = []
    gameelo_list = []
    count = 0
    for x in patches:
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '') + '.' + string.split('.', periods)[1])
    patches = list(dict.fromkeys(new_patches))
    print('Starting openstats command...')
    while count < games:
        playerids_ranked = playerids[count]
        masterminds_ranked = masterminds[count]
        gameresult_ranked = gameresult[count]
        workers_ranked = workers[count]
        spell_ranked = spell[count]
        gameelo_list.append(gameelo[1][count])
        if playerid.lower() != 'all' and 'nova cup' not in playerid:
            for i, x in enumerate(playerids_ranked):
                if x == playerid:
                    opener_ranked_raw = [fighters[count][i][0],fighters[count][i][1],fighters[count][i][2],fighters[count][i][3]]
                    player_num = i
                    break
        else:
            opener_ranked_raw = []
            for i in range(4):
                opener_ranked_raw.extend([fighters[count][i][0],fighters[count][i][1],fighters[count][i][2],fighters[count][i][3]])
        opener_ranked = []
        for i, x in enumerate(opener_ranked_raw):
            opener_ranked.extend([[]])
            for v, y in enumerate(x):
                string = y.split('_unit_id:')
                opener_ranked[i].append(string[0].replace('_', ' '))
        if playerid.lower() != 'all' and 'nova cup' not in playerid:
            s = set()
            for x in range(4):
                for y in opener_ranked[x]:
                    s.add(y)
            for y in s:
                try:
                    if y != opener_ranked[0][0]:
                        if y in unit_dict[opener_ranked[0][0]]['OpenWith']:
                            unit_dict[opener_ranked[0][0]]['OpenWith'][y]['Count'] += 1
                            if gameresult_ranked[player_num] == 'won':
                                unit_dict[opener_ranked[0][0]]['OpenWith'][y]['Wins'] += 1
                        else:
                            unit_dict[opener_ranked[0][0]]['OpenWith'][y] = {'Count': 1, 'Wins': 0}
                            if gameresult_ranked[player_num] == 'won':
                                unit_dict[opener_ranked[0][0]]['OpenWith'][y]['Wins'] += 1
                    else:
                        unit_dict[opener_ranked[0][0]]['Count'] += 1
                        if masterminds_ranked[player_num] not in unit_dict[opener_ranked[0][0]]['MMs']:
                            unit_dict[opener_ranked[0][0]]['MMs'][masterminds_ranked[player_num]] = {'Count': 1, 'Wins': 0}
                        else:
                            unit_dict[opener_ranked[0][0]]['MMs'][masterminds_ranked[player_num]]['Count'] += 1
                        if spell_ranked[player_num] not in unit_dict[opener_ranked[0][0]]['Spells']:
                            unit_dict[opener_ranked[0][0]]['Spells'][spell_ranked[player_num]] = {'Count': 1, 'Wins': 0}
                        else:
                            unit_dict[opener_ranked[0][0]]['Spells'][spell_ranked[player_num]]['Count'] += 1
                        unit_dict[opener_ranked[0][0]]['W4'] += workers_ranked[player_num][3]
                        if gameresult_ranked[player_num] == 'won':
                            unit_dict[opener_ranked[0][0]]['OpenWins'] += 1
                            unit_dict[opener_ranked[0][0]]['MMs'][masterminds_ranked[player_num]]['Wins'] += 1
                            unit_dict[opener_ranked[0][0]]['Spells'][spell_ranked[player_num]]['Wins'] += 1
                except IndexError:
                    continue
        else:
            counter = 0
            for i in range(4):
                s = set()
                for x in range(counter, counter+4):
                    for y in opener_ranked[x]:
                        s.add(y)
                for y in s:
                    try:
                        if y != opener_ranked[counter][0]:
                            if y in unit_dict[opener_ranked[counter][0]]['OpenWith']:
                                unit_dict[opener_ranked[counter][0]]['OpenWith'][y]['Count'] += 1
                                if gameresult_ranked[i] == 'won':
                                    unit_dict[opener_ranked[counter][0]]['OpenWith'][y]['Wins'] += 1
                            else:
                                unit_dict[opener_ranked[counter][0]]['OpenWith'][y] = {'Count': 1, 'Wins': 0}
                                if gameresult_ranked[i] == 'won':
                                    unit_dict[opener_ranked[counter][0]]['OpenWith'][y]['Wins'] += 1
                        else:
                            unit_dict[opener_ranked[counter][0]]['Count'] += 1
                            if masterminds_ranked[i] not in unit_dict[opener_ranked[counter][0]]['MMs']:
                                unit_dict[opener_ranked[counter][0]]['MMs'][masterminds_ranked[i]] = {'Count': 1,'Wins': 0}
                            else:
                                unit_dict[opener_ranked[counter][0]]['MMs'][masterminds_ranked[i]]['Count'] += 1
                            if spell_ranked[i] not in unit_dict[opener_ranked[counter][0]]['Spells']:
                                unit_dict[opener_ranked[counter][0]]['Spells'][spell_ranked[i]] = {'Count': 1, 'Wins': 0}
                            else:
                                unit_dict[opener_ranked[counter][0]]['Spells'][spell_ranked[i]]['Count'] += 1
                            unit_dict[opener_ranked[counter][0]]['W4'] += workers_ranked[i][3]
                            if gameresult_ranked[i] == 'won':
                                unit_dict[opener_ranked[counter][0]]['OpenWins'] += 1
                                unit_dict[opener_ranked[counter][0]]['MMs'][masterminds_ranked[i]]['Wins'] += 1
                                unit_dict[opener_ranked[counter][0]]['Spells'][spell_ranked[i]]['Wins'] += 1
                    except IndexError:
                        continue
                counter += 4
        count += 1
    newIndex = sorted(unit_dict, key=lambda x: unit_dict[x]['Count'], reverse=True)
    unit_dict = {k: unit_dict[k] for k in newIndex}
    avgelo = round(sum(gameelo_list)/len(gameelo_list))
    if novacup:
        playerid = playername
    return create_image_openstats(unit_dict, games, playerid, avgelo, patches)

def apicall_mmstats(playername, games, min_elo, patch, mastermind = 'all', sort="date"):
    novacup = False
    if mastermind != 'all':
        mastermind = mastermind.value
    if playername == 'all':
        playerid = 'all'
        if ((games == 0) or (games > get_games_saved_count(playerid)* 0.25)) and (min_elo < 2700) and (patch == '0'):
            return 'Too many games, please limit data.'
        if games == 0:
            games = get_games_saved_count(playerid)
    elif 'nova cup' in playername:
        novacup = True
        playerid = playername
    else:
        playerid = apicall_getid(playername)
        if playerid == 0:
            return 'Player ' + playername + ' not found.'
        if playerid == 1:
            return 'API limit reached, you can still use "all" commands.'
        if games == 0:
            games = get_games_saved_count(playerid)
    count = 0
    if mastermind == 'All':
        mmnames_list = ['LockIn', 'Greed', 'Redraw', 'Yolo', 'Fiesta', 'CashOut', 'Castle', 'Cartel', 'Chaos', 'Champion', 'DoubleLockIn', 'Kingsguard', 'Megamind']
    elif mastermind == 'Megamind':
        mmnames_list = ['LockIn', 'Greed', 'Redraw', 'Yolo', 'Fiesta', 'CashOut', 'Castle', 'Cartel', 'Chaos', 'Champion', 'DoubleLockIn', 'Kingsguard']
    else:
        mmnames_list = [mastermind]
    masterminds_dict = {}
    for x in mmnames_list:
        masterminds_dict[x] = {"Count": 0, "Wins": 0, "W10": [], "Results": [], "Opener": [], "Spell": [], "Elo": 0, "Leaks": [], "PlayerIds": [], "ChampionUnit": {}}
    gameelo_list = []
    try:
        history_raw = apicall_getmatchistory(playerid, games, min_elo, patch, sort_by=sort)
    except TypeError as e:
        print(e)
        return playername + ' has not played enough games.'
    if history_raw == "Too many patches.":
        return "Too many patches."
    if len(history_raw) == 0:
        return 'No games found.'
    games = len(history_raw)
    if 'nova cup' in playerid:
        playerid = 'all'
    playerids = list(divide_chunks(extract_values(history_raw, 'playerId')[1], 4))
    masterminds = list(divide_chunks(extract_values(history_raw, 'legion')[1], 4))
    gameresult = list(divide_chunks(extract_values(history_raw, 'gameResult')[1], 4))
    workers = list(divide_chunks(extract_values(history_raw, 'workersPerWave')[1], 4))
    opener = list(divide_chunks(extract_values(history_raw, 'firstWaveFighters')[1], 4))
    elo = list(divide_chunks(extract_values(history_raw, 'overallElo')[1], 4))
    endingwaves = extract_values(history_raw, 'endingWave')
    spell = list(divide_chunks(extract_values(history_raw, 'chosenSpell')[1], 4))
    if mastermind == 'All' or mastermind == 'Megamind':
        megamind = list(divide_chunks(extract_values(history_raw, 'megamind')[1], 4))
        if len(megamind) < games:
            megamind = 'N/A'
    elif mastermind == 'Fiesta':
        leaks = list(divide_chunks(extract_values(history_raw, 'leaksPerWave')[1], 4))
    elif mastermind == 'Champion':
        champ_location = []
        for g in history_raw:
            champ_location_temp = list(divide_chunks(extract_values(g, 'chosenChampionLocation')[1], 4))
            if len(champ_location_temp) > 0:
                champ_location.append(champ_location_temp[0])
            else:
                champ_location.append(champ_location_temp)
        build_per_wave = list(divide_chunks(extract_values(history_raw, 'buildPerWave')[1], 4))
    gameelo = extract_values(history_raw, 'gameElo')
    patches = extract_values(history_raw, 'version')
    gameid = extract_values(history_raw, '_id')
    patches = list(dict.fromkeys(patches[1]))
    new_patches = []
    megamind_count = 0
    for x in patches:
        if x.startswith('v10') and mastermind == 'Megamind':
            return 'Only 11.XX patches for megamind.'
        elif x.startswith('v10') and mastermind == 'Champion':
            return 'Only 11.XX patches for champion.'
        string = x
        periods = string.count('.')
        new_patches.append(string.split('.', periods)[0].replace('v', '')+'.'+string.split('.', periods)[1])
    patches = list(dict.fromkeys(new_patches))
    print('Starting mmstats command...')
    while count < games:
        playerids_ranked = playerids[count]
        masterminds_ranked = masterminds[count]
        gameresult_ranked = gameresult[count]
        workers_ranked = workers[count]
        opener_ranked = opener[count]
        elo_ranked = elo[count]
        spell_ranked = spell[count]
        gameelo_list.append(gameelo[1][count])
        match mastermind:
            case 'All':
                if megamind != 'N/A':
                    megamind_ranked = megamind[count]
                for i, x in enumerate(playerids_ranked):
                    if playerid == 'all' or x == playerid:
                        if megamind != 'N/A' and megamind_ranked[i] == True:
                            mastermind_current = 'Megamind'
                        else:
                            mastermind_current = masterminds_ranked[i]
                        masterminds_dict[mastermind_current]["Count"] += 1
                        if gameresult_ranked[i] == 'won':
                            masterminds_dict[mastermind_current]["Wins"] += 1
                        masterminds_dict[mastermind_current]["W10"].append(workers_ranked[i][9])
                        masterminds_dict[mastermind_current]['Results'].append(gameresult_ranked[i])
                        masterminds_dict[mastermind_current]['Spell'].append(spell_ranked[i])
                        masterminds_dict[mastermind_current]['Elo'] += elo_ranked[i]
                        if ',' in opener_ranked[i]:
                            string = opener_ranked[i]
                            commas = string.count(',')
                            masterminds_dict[mastermind_current]['Opener'].append(string.split(',', commas)[commas])
                        else:
                            masterminds_dict[mastermind_current]['Opener'].append(opener_ranked[i])
                        
            case 'Fiesta':
                leaks_ranked = leaks[count]
                for i, x in enumerate(playerids_ranked):
                    if playerid == 'all' or x == playerid:
                        if masterminds_ranked[i] == 'Fiesta':
                            masterminds_dict[masterminds_ranked[i]]["Count"] += 1
                            if gameresult_ranked[i] == 'won':
                                masterminds_dict[masterminds_ranked[i]]["Wins"] += 1
                            masterminds_dict[masterminds_ranked[i]]["W10"].append(workers_ranked[i])
                            masterminds_dict[masterminds_ranked[i]]['Results'].append(gameresult_ranked[i])
                            masterminds_dict[masterminds_ranked[i]]['Spell'].append(spell_ranked[i])
                            masterminds_dict[masterminds_ranked[i]]['PlayerIds'].append(playerids_ranked[i])
                            masterminds_dict[masterminds_ranked[i]]['Elo'] += elo_ranked[i]
                            leaks_temp = []
                            for y in range(endingwaves[1][count]):
                                if len(leaks_ranked[i][y]) > 0:
                                    p = calc_leak(leaks_ranked[i][y], y)
                                    leaks_temp.append(p)
                                else:
                                    leaks_temp.append(0)
                            masterminds_dict[masterminds_ranked[i]]['Leaks'].append(leaks_temp)
                            if ',' in opener_ranked[i]:
                                string = opener_ranked[i]
                                commas = string.count(',')
                                masterminds_dict[masterminds_ranked[i]]['Opener'].append(string.split(',', commas)[commas])
                            else:
                                masterminds_dict[masterminds_ranked[i]]['Opener'].append(opener_ranked[i])
            case 'Megamind':
                if megamind != 'N/A':
                    megamind_ranked = megamind[count]
                for i, x in enumerate(playerids_ranked):
                    if playerid == 'all' or x == playerid:
                        if megamind != 'N/A' and megamind_ranked[i] == True:
                            if masterminds_ranked[i] == 'Megamind':
                                continue
                            else:
                                megamind_count += 1
                                masterminds_dict[masterminds_ranked[i]]["Count"] += 1
                                if gameresult_ranked[i] == 'won':
                                    masterminds_dict[masterminds_ranked[i]]["Wins"] += 1
                                masterminds_dict[masterminds_ranked[i]]["W10"].append(workers_ranked[i][9])
                                masterminds_dict[masterminds_ranked[i]]['Results'].append(gameresult_ranked[i])
                                masterminds_dict[masterminds_ranked[i]]['Spell'].append(spell_ranked[i])
                                masterminds_dict[masterminds_ranked[i]]['Elo'] += elo_ranked[i]
                                if ',' in opener_ranked[i]:
                                    string = opener_ranked[i]
                                    commas = string.count(',')
                                    masterminds_dict[masterminds_ranked[i]]['Opener'].append(string.split(',', commas)[commas])
                                else:
                                    masterminds_dict[masterminds_ranked[i]]['Opener'].append(opener_ranked[i])
            case 'Champion':
                unit_dict = {}
                with open('Files/units.json', 'r') as f:
                    units_json = json.load(f)
                    units_extracted = extract_values(units_json, 'unitId')
                    value_extracted = extract_values(units_json, 'totalValue')[1]
                for i, x in enumerate(units_extracted[1]):
                    if value_extracted[i] and int(value_extracted[i]) > 0:
                        string = x
                        string = string.replace('_', ' ')
                        string = string.replace(' unit id', '')
                        unit_dict[string] = int(value_extracted[i])
                champ_location_ranked = champ_location[count]
                build_per_wave_ranked = build_per_wave[count]
                for i, x in enumerate(playerids_ranked):
                    if playerid == 'all' or x == playerid and masterminds_ranked[i] == 'Champion':
                        if len(champ_location_ranked) > 0:
                            champ_location_current = champ_location_ranked[i]
                            if champ_location_current == '-1|-1':
                                continue
                            masterminds_dict[masterminds_ranked[i]]["Count"] += 1
                            if gameresult_ranked[i] == 'won':
                                masterminds_dict[masterminds_ranked[i]]["Wins"] += 1
                            masterminds_dict[masterminds_ranked[i]]['Elo'] += elo_ranked[i]
                            champ_found = False
                            for wave in build_per_wave_ranked[i]:
                                if champ_found == True:
                                    break
                                for unit in wave:
                                    unit_name = unit.split('_unit_id:')[0].replace('_', ' ')
                                    if unit.split(':')[1] == champ_location_current and 'grarl' not in unit and 'pirate' not in unit and unit_dict[unit_name] > 50:
                                        if "seedling" in unit_name:
                                            print(gameid[1][count])
                                        if unit_name in masterminds_dict[masterminds_ranked[i]]['ChampionUnit']:
                                            masterminds_dict[masterminds_ranked[i]]['ChampionUnit'][unit_name]['Count'] += 1
                                            if gameresult_ranked[i] == 'won':
                                                masterminds_dict[masterminds_ranked[i]]['ChampionUnit'][unit_name]["Wins"] += 1
                                            masterminds_dict[masterminds_ranked[i]]['ChampionUnit'][unit_name]['Spell'].append(spell_ranked[i])
                                            masterminds_dict[masterminds_ranked[i]]['ChampionUnit'][unit_name]['Results'].append(gameresult_ranked[i])
                                            masterminds_dict[masterminds_ranked[i]]['ChampionUnit'][unit_name]["W10"] += workers_ranked[i][9]
                                        else:
                                            masterminds_dict[masterminds_ranked[i]]['ChampionUnit'][unit_name] = {"Count": 1, "Wins": 0, "Spell": [], "W10": 0, "Results": []}
                                            if gameresult_ranked[i] == 'won':
                                                masterminds_dict[masterminds_ranked[i]]['ChampionUnit'][unit_name]["Wins"] += 1
                                            masterminds_dict[masterminds_ranked[i]]['ChampionUnit'][unit_name]['Spell'].append(spell_ranked[i])
                                            masterminds_dict[masterminds_ranked[i]]['ChampionUnit'][unit_name]['Results'].append(gameresult_ranked[i])
                                            masterminds_dict[masterminds_ranked[i]]['ChampionUnit'][unit_name]["W10"] += workers_ranked[i][9]
                                        champ_found = True
        count += 1
    if mastermind == 'Champion':
        unit_dict = masterminds_dict['Champion']['ChampionUnit']
        newIndex = sorted(unit_dict, key=lambda x: unit_dict[x]['Count'], reverse=True)
        unit_dict = {k: unit_dict[k] for k in newIndex}
    else:
        newIndex = sorted(masterminds_dict, key=lambda x: masterminds_dict[x]['Count'], reverse=True)
        masterminds_dict = {k: masterminds_dict[k] for k in newIndex}
    avg_gameelo = round(sum(gameelo_list)/len(gameelo_list))
    if novacup:
        playerid = playername
    match mastermind:
        case 'All':
            return create_image_mmstats(masterminds_dict, count, playerid, avg_gameelo, patches)
        case 'Fiesta':
            return create_image_mmstats_fiesta(masterminds_dict, count, playerid, avg_gameelo, patches)
        case 'Megamind':
            return create_image_mmstats(masterminds_dict, count, playerid, avg_gameelo, patches, True, megamind_count)
        case 'Champion':
            return create_image_mmstats_champion(masterminds_dict, unit_dict, count, playerid, avg_gameelo, patches)

def apicall_elo(playername, rank):
    playerid = apicall_getid(playername)
    if playerid == 0:
        output = 'Player ' + str(playername) + ' not found.'
    if playerid == 1:
        return 'API limit reached.'
    else:
        stats = apicall_getstats(playerid)
        playtime_minutes = stats['secondsPlayed'] / 60
        playtime_hours = playtime_minutes / 60
        url = 'https://apiv2.legiontd2.com/players/stats?limit=100&sortBy=overallElo&sortDirection=-1'
        api_response = requests.get(url, headers=header)
        leaderboard = json.loads(api_response.text)
        if stats['rankedWinsThisSeason'] + stats['rankedLossesThisSeason'] > 0:
            history_details = apicall_matchhistorydetails(playerid)
        else:
            history_details = [0,0]
        new_dict = {item['_id']: item['_id'] for item in leaderboard}
        if rank == 0:
            for i, key in enumerate(new_dict.keys()):
                if key == playerid:
                    index = i
                    return str(playername).capitalize() + ' is rank ' + str(index + 1) + ' with ' + str(
                        stats['overallElo']) + ' elo (Peak: ' + str(stats['overallPeakEloThisSeason']) + ') and ' + str(
                        round(playtime_hours)) + ' in game hours.\nThey have won ' + \
                        str(history_details[1]) + ' out of their last 10 games. (Elo change: ' + \
                        str(history_details[0]) + ')'
            else:
                return str(playername).capitalize() + ' has ' + str(stats['overallElo']) + ' elo (Peak: ' + str(
                    stats['overallPeakEloThisSeason']) + ') with ' + str(round(playtime_hours)) + ' in game hours.\n' \
                    'They have won ' + str(history_details[1]) + ' out of their last 10 games. ' \
                    '(Elo change: ' + str(history_details[0]) + ')'
        else:
            return str(playername).capitalize() + ' is rank ' + str(rank) + ' with ' + str(
                stats['overallElo']) + ' elo (Peak: ' + str(stats['overallPeakEloThisSeason']) + ') and ' + str(
                round(playtime_hours)) + ' in game hours.\nThey have won ' + \
                str(history_details[1]) + ' out of their last 10 games. (Elo change: ' + \
                str(history_details[0]) + ')'


def apicall_bestie(playername):
    playerid = apicall_getid(playername)
    if playerid == 0:
        return 'Player ' + str(playername) + ' not found.'
    if playerid == 1:
        return 'API limit reached.'
    else:
        request_type = 'players/bestFriends/' + playerid
        url = 'https://apiv2.legiontd2.com/' + request_type + '?limit=1&offset=0'
        api_response = requests.get(url, headers=header)
        bestie = json.loads(api_response.text)
        if not bestie:
            return 'no bestie :sob: (No data)'
        else:
            for bestie_new in bestie[0].values():
                print(bestie_new['playerName'])
                bestie_name = bestie_new['playerName']
                break
            print(bestie[0]['count'])

            return str(playername).capitalize() + "'s bestie is " + bestie_name + ' :heart: with ' + str(
                bestie[0]['count']) + ' games together.'


def apicall_showlove(playername, playername2):
    playerid = apicall_getid(playername)
    print(playername)
    print(playername2)
    if playerid == 0:
        return 'Player ' + str(playername) + ' not found.'
    if playerid == 1:
        return 'API limit reached.'
    else:
        request_type = 'players/bestFriends/' + playerid
        url = 'https://apiv2.legiontd2.com/' + request_type + '?limit=50&offset=0'
        api_response = requests.get(url, headers=header)
        bestie = json.loads(api_response.text)
        count = 0
        nextvaluesave = 0
        while count < len(bestie):
            for bestie_new in bestie[count].values():
                if isinstance(bestie_new, dict):
                    name = bestie_new['playerName']
                    if str(name).lower() == str(playername2).lower():
                        print('found target')
                        nextvaluesave = 1
                    count = count + 1
                else:
                    if nextvaluesave == 1:
                        love_count = bestie_new
                        print(love_count)
                        return playername.capitalize() + ' has played ' + str(
                            love_count) + ' games with ' + playername2.capitalize() + ' :heart:'
    return 'Not enough games played together'


def apicall_rank(rank):
    url = 'https://apiv2.legiontd2.com/players/stats?limit=1&offset=' + str(
        int(rank) - 1) + '&sortBy=overallElo&sortDirection=-1'
    api_response = requests.get(url, headers=header)
    player_info = json.loads(api_response.text)
    if 'Limit Exceeded' in player_info:
        return 'API limit reached.'
    try:
        name = apicall_getprofile(player_info[0]['_id'])
    except Exception:
        return 'Player not found.'
    return apicall_elo(str(name['playerName']).lower(), rank)


def apicall_gamestats(playername):
    playerid = apicall_getid(playername)
    if playerid == 1:
        return 'API limit reached.'
    stats = apicall_getstats(playerid)
    wins = stats['rankedWinsThisSeason']
    loses = stats['rankedLossesThisSeason']
    try:
        winrate = wins / (wins + loses)
    except ZeroDivisionError:
        return 'No games played this season.'
    return str(playername).capitalize() + "'s stats(Season 2024):\nElo: " + str(stats['overallElo']) + '(Peak: ' + str(
        stats['overallPeakEloThisSeason']) + ')\nGames played: ' + \
        str(wins + loses) + '\nWinrate: ' + str(round(winrate * 100)) + '%\nBehavior score: ' + str(
            stats['behaviorScore'] / 10)


