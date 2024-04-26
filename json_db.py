import glob
import json
import os
import os.path
import pathlib
import time
from pathlib import Path
import legion_api

def get_games_saved_count(playerid):
    path = str(pathlib.Path(__file__).parent.resolve()) + "/Profiles/" + playerid + "/gamedata/"
    if Path(Path(str(path))).is_dir():
        json_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.json')]
        if len(json_files) == 0:
            return 200
        else:
            return len(json_files)
    else:
        return 200

def get_games_loop(playerid, offset, path, expected, timeout_limit = 3):
    print("Starting get_games_loop, expecting " + str(expected) + " games.")
    data = legion_api.pullgamedata(playerid, offset, path, expected)
    count = data[0]
    games_count = data[1]
    timeout = 0
    while count < expected:
        if timeout == timeout_limit:
            print('Timeout while pulling games.')
            break
        offset += 50
        data = legion_api.pullgamedata(playerid, offset, path, expected)
        if data[0] + data[1] == 0:
            timeout += 1
        count += data[0]
        games_count += data[1]
    else:
        print('All '+str(expected)+' required games pulled.')
    return games_count

def get_matchistory(playerid, games, min_elo=0, patch='0', update = 0, earlier_than_wave10 = False, sort_by = "date"):
    patch_list = []
    if patch != '0' and "," in patch:
        patch_list = patch.replace(" ", "").split(',')
    elif patch != '0' and "-" not in patch and "+" not in patch:
        patch_list = patch.replace(" ", "").split(',')
    elif patch != "0" and "+" in patch and "-" not in patch:
        patch_new = patch.replace(" ", "").split("+")
        if len(patch_new) == 2:
            patch_new = patch_new[1].split('.')
            for x in range(13 - int(patch_new[1])):
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
    games_count = 0
    if playerid != 'all' and 'nova cup' not in playerid:
        if games == 0:
            games2 = get_games_saved_count(playerid)
        else:
            games2 = games
        path = str(pathlib.Path(__file__).parent.resolve()) + "/Profiles/" + playerid + "/"
        if not Path(Path(str(path))).is_dir():
            print(playerid + ' profile not found, creating new folder...')
            new_profile = True
            Path(str(path+'gamedata/')).mkdir(parents=True, exist_ok=True)
            with open(str(path) + "gamecount_" + playerid + ".txt", "w") as f:
                data = get_games_loop(playerid, 0, path, games2)
                playerstats = legion_api.getstats(playerid)
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
            playerstats = legion_api.getstats(playerid)
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
            if len(json_files) < games2:
                games_count += get_games_loop(playerid, games_amount_old, path, games2-len(json_files))
            with open(str(path) + "gamecount_" + playerid + ".txt", "w") as f:
                f.truncate(0)
                lines = [str(ranked_games), str(games_amount_old+games_count)]
                f.write('\n'.join(lines))
        if update == 0:
            raw_data = []
            if games == 0:
                games2 = get_games_saved_count(playerid)
            json_files = [pos_json for pos_json in os.listdir(path + 'gamedata/') if pos_json.endswith('.json')]
            count = 0
            if sort_by == "date":
                sorted_json_files = sorted(json_files, key=lambda x: time.mktime(time.strptime(x.split('_')[-4].split('/')[-1], "%Y-%m-%d-%H-%M-%S")), reverse=True)
            elif sort_by == "elo":
                sorted_json_files = sorted(json_files, key=lambda x: x.split("_")[-2], reverse=True)
            for i, x in enumerate(sorted_json_files):
                with open(path + '/gamedata/' + x) as f:
                    raw_data_partial = json.load(f)
                    f.close()
                    if raw_data_partial['gameElo'] >= min_elo:
                        if patch == '0':
                            if count == games2:
                                break
                            if earlier_than_wave10 == True:
                                count += 1
                                raw_data.append(raw_data_partial)
                            elif raw_data_partial['endingWave'] > 10 and earlier_than_wave10 == False:
                                count += 1
                                raw_data.append(raw_data_partial)
                        else:
                            if count == games2:
                                break
                            for x in patch_list:
                                if str(raw_data_partial['version']).startswith('v'+x):
                                    if earlier_than_wave10 == True:
                                        count += 1
                                        raw_data.append(raw_data_partial)
                                    elif raw_data_partial['endingWave'] > 10 and earlier_than_wave10 == False:
                                        count += 1
                                        raw_data.append(raw_data_partial)
    else:
        if 'nova cup' in playerid:
            path2 = str(pathlib.Path(__file__).parent.resolve()) + "/Profiles/" + playerid + '/gamedata/'
            json_files = []
            raw_data = []
            try:
                if patch != '0':
                    for y in patch_list:
                        json_files.extend([path2 + pos_json for pos_json in os.listdir(path2) if pos_json.endswith('.json') and pos_json.split('_')[-3].startswith('v' + y.replace('.', '-')) and int(pos_json.split('_')[-2]) >= min_elo])
                else:
                    json_files.extend([path2 + pos_json for pos_json in os.listdir(path2) if pos_json.endswith('.json') and int(pos_json.split('_')[-2]) >= min_elo])
                sorted_json_files = sorted(json_files, key=lambda x: time.mktime(time.strptime(x.split('_')[-4].split('/')[-1], "%Y-%m-%d-%H-%M-%S")), reverse=True)
            except FileNotFoundError:
                return playerid + " not found. :("
        else:
            path1 = str(pathlib.Path(__file__).parent.resolve()) + "/Games/"
            raw_data = []
            json_files = []
            json_counter = 0
            if patch != '0':
                for y in patch_list:
                    json_files.extend([path1 + pos_json for pos_json in os.listdir(path1) if pos_json.endswith('.json') and pos_json.split('_')[-3].startswith('v'+y.replace('.', '-')) and int(pos_json.split('_')[-2]) >= min_elo])
            else:
                    json_files.extend([path1 + pos_json for pos_json in os.listdir(path1) if pos_json.endswith('.json') and int(pos_json.split('_')[-2]) >= min_elo])
            if sort_by == "date":
                sorted_json_files = sorted(json_files, key=lambda x: time.mktime(time.strptime(x.split('_')[-4].split('/')[-1],"%Y-%m-%d-%H-%M-%S")), reverse=True)
            elif sort_by == "elo":
                sorted_json_files = sorted(json_files, key=lambda x: x.split("_")[-2], reverse=True)
        count = 0
        for i, x in enumerate(sorted_json_files):
            if count == games and games != 0:
                break
            with open(x) as f:
                try:
                    raw_data_partial = json.load(f)
                except json.decoder.JSONDecodeError:
                    os.remove(x)
                    print("file error")
                f.close()
                if earlier_than_wave10 == True:
                    count += 1
                    raw_data.append(raw_data_partial)
                elif raw_data_partial['endingWave'] > 10 and earlier_than_wave10 == False:
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
        