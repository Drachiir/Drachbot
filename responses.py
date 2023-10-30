import requests
import json
from collections import Counter
import pathlib
from pathlib import Path
import datetime
import os
import glob
import re

with open('Secrets.json') as f:
    secret_file = json.load(f)
    header = {'x-api-key': secret_file.get('apikey')}

def divide_chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i:i + n]


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


def count_mythium(send):
    mercs = {"Snail": 20, "Giant Snail": 20, "Lizard": 40, "Dragon Turtle": 40, "Brute": 60, "Fiend": 60, "Dino": 80,
             "Hermit": 80, "Cannoneer": 100, "Imp": 100, "Safety Mole": 120, "Drake": 120, "Pack Leader": 160,
             "Mimic": 160, "Witch": 200, "Ogre": 200, "Ghost Knight": 240, "Four Eyes": 240, "Centaur": 280,
             "Shaman": 320, "Siege Ram": 320, "Needler": 360, "Kraken": 400}
    send_amount = 0
    for x in send:
        send_amount = send_amount + mercs.get(x)
    return send_amount


def count_elochange(playername, player_names, data):
    value_count = 0
    for i in range(len(player_names[1])):
        if str(player_names[1][i]).lower() == playername:
            value_count = value_count + data[1][i]
    return value_count


def handle_response(message) -> str:
    p_message = message.lower()
    if '!elo fine' in p_message:
        return str(apicall_elo('fine', 0) + ' :eggplant:')
    if '!julian' in p_message:
        return 'julian sucks'
    if '!penny' in p_message:
        return 'penny sucks'
    if '!green' in p_message:
        return 'fast & aggressive'
    if 'kidkpro' in p_message:
        return ':eggplant:'
    if 'widderson' in p_message:
        return ':banana:'
    if '!github' in p_message:
        return 'https://github.com/Drachiir/Legion-Elo-Bot'


def apicall_getid(playername):
    request_type = 'players/byName/' + playername
    url = 'https://apiv2.legiontd2.com/' + request_type
    print(request_type)
    try:
        api_response = requests.get(url, headers=header)
        api_response.raise_for_status()
    except requests.exceptions.HTTPError as err:
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

def get_games_saved_count(playername):
    path = str(pathlib.Path(__file__).parent.resolve()) + "/Profiles/" + playername + "/gamedata/"
    if Path(Path(str(path))).is_dir():
        json_files = [pos_json for pos_json in os.listdir(path) if pos_json.endswith('.json')]
        if len(json_files) < 400:
            return 400
        else:
            return len(json_files)
    else:
        return 400

def apicall_pullgamedata(playerid, offset, path):
    ranked_count = 0
    games_count = 0
    output = []
    url = 'https://apiv2.legiontd2.com/players/matchHistory/' + str(playerid) + '?limit=' + str(50) + '&offset=' + str(offset) + '&countResults=false'
    print('Pulling ' + str(50) + ' games from API...')
    api_response = requests.get(url, headers=header)
    raw_data = json.loads(api_response.text)
    print('Saving ranked games.')
    for x in raw_data:
        if (x['queueType'] == 'Normal') and (x['endingWave'] >= 10):
            date = str(x['date']).replace(':', '')
            date = date.replace('.', '')
            if Path(Path(str(path + 'gamedata/') + date + '_' + str(x['_id']) + ".json")).is_file():
                print('File already there, breaking loop.')
                break
            ranked_count += 1
            with open(str(path + 'gamedata/') + date + '_' + str(x['_id']) + ".json", "w") as f:
                json.dump(x, f)
        games_count += 1
    output.append(ranked_count)
    output.append(games_count)
    return output

def get_games_loop(playerid, offset, path, expected):
    data = apicall_pullgamedata(playerid, offset, path)
    count = data[0]
    games_count = data[1]
    while count < expected:
        offset += 50
        data = apicall_pullgamedata(playerid, offset, path)
        count += data[0]
        games_count += data[1]
    else:
        print('All required games pulled.')
    return games_count

def apicall_getmatchistory(playerid, games):
    games_count = 0
    playername = apicall_getprofile(playerid)['playerName']
    path = str(pathlib.Path(__file__).parent.resolve()) + "/Profiles/" + playername + "/"
    if not Path(Path(str(path))).is_dir():
        print(playername + ' profile not found, creating new folder...')
        Path(str(path+'gamedata/')).mkdir(parents=True, exist_ok=True)
        with open(str(path) + "gamecount_" + playername + "_" + str(datetime.date.today()) + ".txt", "w") as f:
            data = get_games_loop(playerid, 0, path, games)
            playerstats = apicall_getstats(playerid)
            ranked_games = playerstats['rankedWinsThisSeason'] + playerstats['rankedLossesThisSeason']
            lines = [str(ranked_games), str(data)]
            f.write('\n'.join(lines))
    else:
        for file in glob.glob(path + '*.txt'):
            file_path = file
        with open(file, 'r') as f:
            txt = f.readlines()
            ranked_games_old = int(txt[0])
            games_amount_old = int(txt[1])
        playerstats = apicall_getstats(playerid)
        ranked_games = playerstats['rankedWinsThisSeason'] + playerstats['rankedLossesThisSeason']
        games_diff = ranked_games - ranked_games_old
        if ranked_games < ranked_games_old:
            games_count += get_games_loop(playerid, 0, path, games_diff)
        json_files = [pos_json for pos_json in os.listdir(path + 'gamedata/') if pos_json.endswith('.json')]
        if len(json_files) < games:
            games_count += get_games_loop(playerid, games_amount_old, path, games-len(json_files))
        with open(str(path) + "gamecount_" + playername + "_" + str(datetime.date.today()) + ".txt", "w") as f:
            f.truncate(0)
            lines = [str(ranked_games), str(games_amount_old+games_count)]
            f.write('\n'.join(lines))
    raw_data = []
    json_files = [pos_json for pos_json in os.listdir(path + 'gamedata/') if pos_json.endswith('.json')]
    #sorted_json_files = Tcl().call('lsort', '-decreasing', json_files)
    for i, x in enumerate(sorted(json_files, reverse=True)):
        if i > len(json_files)-1:
            break
        with open(path+'/gamedata/'+x) as f:
            raw_data_partial = json.load(f)
            raw_data.append(raw_data_partial)
    return raw_data

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

def apicall_wave1tendency(playername, option):
    playerid = apicall_getid(playername)
    if playerid == 0:
        return 'Player ' + playername + ' not found.'
    count = 0
    ranked_count = 0
    queue_count = 0
    snail_count = 0
    kingup_atk_count = 0
    kingup_regen_count = 0
    kingup_spell_count = 0
    save_count = 0
    games = 100
    games_limit = games * 4
    try:
        history_raw = apicall_getmatchistory(playerid, games)
    except TypeError as e:
        print(e)
        return playername + ' has not played enough games.'
    playernames = list(divide_chunks(extract_values(history_raw, 'playerName')[1], 1))
    if option == 0:
        snail = list(divide_chunks(extract_values(history_raw, 'mercenariesSentPerWave')[1], 1))
        kingup = list(divide_chunks(extract_values(history_raw, 'kingUpgradesPerWave')[1], 1))
    elif option == 1:
        snail = list(divide_chunks(extract_values(history_raw, 'mercenariesReceivedPerWave')[1], 1))
        kingup = list(divide_chunks(extract_values(history_raw, 'opponentKingUpgradesPerWave')[1], 1))
    gameid = extract_values(history_raw, '_id')
    queue_type = extract_values(history_raw, 'queueType')
    playercount = extract_values(history_raw, 'playerCount')
    while count < games_limit:
        if str(queue_type[1][queue_count]) == 'Normal':
            print('Ranked game: ' + str(ranked_count + 1) + ' | Gameid: ' + str(gameid[1][queue_count]))
            playernames_ranked = playernames[count] + playernames[count + 1] + playernames[count + 2] + playernames[count + 3]
            print(playernames_ranked)
            snail_ranked = snail[count] + snail[count + 1] + snail[count + 2] + snail[count + 3]
            kingup_ranked = kingup[count] + kingup[count + 1] + kingup[count + 2] + kingup[count + 3]
            for i, x in enumerate(playernames_ranked):
                if str(x).lower() == str(playername).lower():
                    if len(snail_ranked[i][0]) > 0:
                        if str(snail_ranked[i][0][0]) == 'Snail':
                            print(str(x) + ' sent: ' + str(snail_ranked[i][0][0]))
                            snail_count = snail_count + 1
                            break
                    elif len(kingup_ranked[i][0]) > 0:
                        if str(kingup_ranked[i][0][0]) == 'Upgrade King Attack':
                            print(str(x) + ' sent: ' + str(kingup_ranked[i][0][0]))
                            kingup_atk_count = kingup_atk_count + 1
                            break
                        if str(kingup_ranked[i][0][0]) == 'Upgrade King Regen':
                            print(str(x) + ' sent: ' + str(kingup_ranked[i][0][0]))
                            kingup_regen_count = kingup_regen_count + 1
                            break
                        if str(kingup_ranked[i][0][0]) == 'Upgrade King Spell':
                            print(str(x) + ' sent: ' + str(kingup_ranked[i][0][0]))
                            kingup_spell_count = kingup_spell_count + 1
                            break
                    else:
                        print(str(x) + ' saved Mythium')
                        save_count = save_count + 1
                        break

            count = count + 4
            queue_count = queue_count + 1
            ranked_count = ranked_count + 1

        elif playercount[1][queue_count] == 8:
            count = count + 8
            queue_count = queue_count + 1
            games_limit = games_limit + 4
            print('Skip 8 player game: ' + str(count))
        elif playercount[1][queue_count] == 2:
            count = count + 2
            queue_count = queue_count + 1
            games_limit = games_limit - 2
            print('Skip 2 player game: ' + str(count))
        elif playercount[1][queue_count] == 1:
            count = count + 1
            queue_count = queue_count + 1
            games_limit = games_limit - 3
            print('Skip 1 player game: ' + str(count))
        else:
            queue_count = queue_count + 1
            count = count + 4
            print('Skip 4 player game: ' + str(count))
    send_total = kingup_atk_count+kingup_regen_count+kingup_spell_count+snail_count+save_count
    kingup_total = kingup_atk_count+kingup_regen_count+kingup_spell_count
    if option == 0:
        output = 'send'
    elif option == 1:
        output = 'received'
    if send_total > 4:
        return (playername).capitalize() + "'s Wave 1 " + output + " stats: (Last " + str(send_total) + " ranked games)\nKingup: " + \
            str(kingup_total) + ' (Attack: ' + str(kingup_atk_count) + ' Regen: ' + str(kingup_regen_count) + \
            ' Spell: ' + str(kingup_spell_count) + ')\nSnail: ' + str(snail_count) + '\nSave: ' + str(save_count)
    else:
        return 'Not enough ranked data'


def apicall_winrate(playername, playername2, option):
    playerid = apicall_getid(playername)
    if playerid == 0:
        return 'Player ' + playername + ' not found.'
    if playername2.lower() != 'all':
        playerid2 = apicall_getid(playername2)
        if playerid2 == 0:
            return 'Player ' + playername2 + ' not found.'
    count = 0
    win_count = 0
    game_count = 0
    ranked_count = 0
    queue_count = 0
    games = get_games_saved_count(playername)
    games_limit = games * 4
    playername2_list = []
    gameresults = []
    try:
        history_raw = apicall_getmatchistory(playerid, games)
    except TypeError as e:
        print(e)
        return playername + ' has not played enough games.'
    games = get_games_saved_count(playername)
    games_limit = games * 4
    playernames = list(divide_chunks(extract_values(history_raw, 'playerName')[1], 1))
    gameresult = list(divide_chunks(extract_values(history_raw, 'gameResult')[1], 1))
    gameid = extract_values(history_raw, '_id')
    queue_type = extract_values(history_raw, 'queueType')
    playercount = extract_values(history_raw, 'playerCount')
    while count < games_limit:
        if str(queue_type[1][queue_count]) == 'Normal':
            print('Ranked game: ' + str(ranked_count + 1) + ' | Gameid: ' + str(gameid[1][queue_count]))
            playernames_ranked_west = playernames[count] + playernames[count + 1]
            playernames_ranked_east = playernames[count + 2] + playernames[count + 3]
            gameresult_ranked_west = gameresult[count] + gameresult[count + 1]
            gameresult_ranked_east = gameresult[count + 2] + gameresult[count + 3]
            if playername2.lower() != 'all':
                for i, x in enumerate(playernames_ranked_west):
                    if str(x).lower() == str(playername).lower():
                        if option == 0:
                            if playernames_ranked_east[0].lower() == playername2.lower():
                                game_count += 1
                                if gameresult_ranked_west[i] == 'won':
                                    win_count += 1
                            elif playernames_ranked_east[1].lower() == playername2.lower():
                                game_count += 1
                                if gameresult_ranked_west[i] == 'won':
                                    win_count += 1
                        elif option == 1:
                            if playernames_ranked_west[0].lower() == playername2.lower():
                                game_count += 1
                                if gameresult_ranked_west[i] == 'won':
                                    win_count += 1
                            elif playernames_ranked_west[1].lower() == playername2.lower():
                                game_count += 1
                                if gameresult_ranked_west[i] == 'won':
                                    win_count += 1
                for i, x in enumerate(playernames_ranked_east):
                    if str(x).lower() == str(playername).lower():
                        if option == 0:
                            if playernames_ranked_west[0].lower() == playername2.lower():
                                game_count += 1
                                if gameresult_ranked_east[i] == 'won':
                                    win_count += 1
                            elif playernames_ranked_west[1].lower() == playername2.lower():
                                game_count += 1
                                if gameresult_ranked_east[i] == 'won':
                                    win_count += 1
                        elif option == 1:
                            if playernames_ranked_east[0].lower() == playername2.lower():
                                game_count += 1
                                if gameresult_ranked_east[i] == 'won':
                                    win_count += 1
                            elif playernames_ranked_east[1].lower() == playername2.lower():
                                game_count += 1
                                if gameresult_ranked_east[i] == 'won':
                                    win_count += 1
            else:
                for i, x in enumerate(playernames_ranked_west):
                    if str(x).lower() == str(playername).lower():
                        if option == 0:
                            playername2_list.append(playernames_ranked_east[0])
                            gameresults.append(gameresult_ranked_west[i])
                            playername2_list.append(playernames_ranked_east[1])
                            gameresults.append(gameresult_ranked_west[i])
                        elif option == 1:
                            if playernames_ranked_west[0].lower() != playername.lower():
                                playername2_list.append(playernames_ranked_west[0])
                                gameresults.append(gameresult_ranked_west[i])
                            elif playernames_ranked_west[1].lower() != playername.lower():
                                playername2_list.append(playernames_ranked_west[1])
                                gameresults.append(gameresult_ranked_west[i])
                for i, x in enumerate(playernames_ranked_east):
                    if str(x).lower() == str(playername).lower():
                        if option == 0:
                            playername2_list.append(playernames_ranked_west[0])
                            gameresults.append(gameresult_ranked_east[i])
                            playername2_list.append(playernames_ranked_west[1])
                            gameresults.append(gameresult_ranked_east[i])
                        elif option == 1:
                            if playernames_ranked_east[0].lower() != playername.lower():
                                playername2_list.append(playernames_ranked_east[0])
                                gameresults.append(gameresult_ranked_east[i])
                            elif playernames_ranked_east[1].lower() != playername.lower():
                                playername2_list.append(playernames_ranked_east[1])
                                gameresults.append(gameresult_ranked_east[i])
            count = count + 4
            queue_count = queue_count + 1
            ranked_count = ranked_count + 1

        elif playercount[1][queue_count] == 8:
            count = count + 8
            queue_count = queue_count + 1
            games_limit = games_limit + 4
            print('Skip 8 player game: ' + str(count))
        elif playercount[1][queue_count] == 2:
            count = count + 2
            queue_count = queue_count + 1
            games_limit = games_limit - 2
            print('Skip 2 player game: ' + str(count))
        elif playercount[1][queue_count] == 1:
            count = count + 1
            queue_count = queue_count + 1
            games_limit = games_limit - 3
            print('Skip 1 player game: ' + str(count))
        else:
            queue_count = queue_count + 1
            count = count + 4
            print('Skip 4 player game: ' + str(count))
    if option == 0:
        output = 'against'
    elif option == 1:
        output = 'with'
    if playername2.lower() == 'all':
        most_common_mates = Counter(playername2_list).most_common(6)
        winrates = []
        for i, x in enumerate(most_common_mates):
            counter = 0
            for c, v in enumerate(playername2_list):
                if v == x[0]:
                    if gameresults[c] == 'won':
                        counter += 1
            winrates.append(round(counter / x[1] * 100, 2))
            winrates.append(counter)
        return str(playername).capitalize() + "'s winrate " + output + ' any players (From ' + str(ranked_count) + ' ranked games)\n' +\
            most_common_mates[0][0] + ': ' + str(winrates[1]) + ' win - ' + str(most_common_mates[0][1] - winrates[1]) + ' lose (' + str(winrates[0]) + '% winrate)\n' + \
            most_common_mates[1][0] + ': ' + str(winrates[3]) + ' win - ' + str(most_common_mates[1][1] - winrates[3]) + ' lose (' + str(winrates[2]) + '% winrate)\n' + \
            most_common_mates[2][0] + ': ' + str(winrates[5]) + ' win - ' + str(most_common_mates[2][1] - winrates[5]) + ' lose (' + str(winrates[4]) + '% winrate)\n' + \
            most_common_mates[3][0] + ': ' + str(winrates[7]) + ' win - ' + str(most_common_mates[3][1] - winrates[7]) + ' lose (' + str(winrates[6]) + '% winrate)\n' + \
            most_common_mates[4][0] + ': ' + str(winrates[9]) + ' win - ' + str(most_common_mates[4][1] - winrates[9]) + ' lose (' + str(winrates[8]) + '% winrate)\n' + \
            most_common_mates[5][0] + ': ' + str(winrates[11]) + ' win - ' + str(most_common_mates[5][1] - winrates[11]) + ' lose (' + str(winrates[10]) + '% winrate)'
    else:
        try: return str(playername).capitalize() + "'s winrate " + output + ' ' + str(playername2).capitalize() + '(From ' + str(game_count) + ' ranked games)\n' +\
            str(win_count) + ' win - ' + str(game_count-win_count) + ' lose (' + str(round(win_count / game_count * 100, 2)) +\
            '% winrate)'
        except ZeroDivisionError as e:
            print(e)
            return str(playername).capitalize() + ' and ' + str(playername2).capitalize() + ' have no games played ' + output + ' each other recently.'


def apicall_elcringo(playername):
    playerid = apicall_getid(playername)
    if playerid == 0:
        return 'Player ' + playername + ' not found.'
    count = 0
    ranked_count = 0
    queue_count = 0
    games = get_games_saved_count(playername)
    games_limit = games * 4
    save_count_list = []
    save_count_pre10_list = []
    save_count = 0
    save_count_pre10 = 0
    ending_wave_list = []
    worker_10_list = []
    mythium_list = []
    mythium_list_pergame = []
    kinghp_list = []
    try:
        history_raw = apicall_getmatchistory(playerid, games)
    except TypeError as e:
        print(e)
        return playername + ' has not played enough games.'
    games = get_games_saved_count(playername)
    games_limit = games * 4
    playernames = list(divide_chunks(extract_values(history_raw, 'playerName')[1], 1))
    endingwaves = extract_values(history_raw, 'endingWave')
    snail = list(divide_chunks(extract_values(history_raw, 'mercenariesSentPerWave')[1], 1))
    kingup = list(divide_chunks(extract_values(history_raw, 'kingUpgradesPerWave')[1], 1))
    workers = list(divide_chunks(extract_values(history_raw, 'workersPerWave')[1], 1))
    kinghp_left = extract_values(history_raw, 'leftKingPercentHp')
    kinghp_right = extract_values(history_raw, 'rightKingPercentHp')
    gameid = extract_values(history_raw, '_id')
    gameelo = extract_values(history_raw, 'gameElo')
    gameelo_list = []
    queue_type = extract_values(history_raw, 'queueType')
    playercount = extract_values(history_raw, 'playerCount')
    while count < games_limit:
        if str(queue_type[1][queue_count]) == 'Normal' and endingwaves[1][queue_count] >= 10:
            ending_wave_list.append(endingwaves[1][queue_count])
            print('Ranked game: ' + str(ranked_count + 1) + ' | Gameid: ' + str(gameid[1][queue_count]))
            playernames_ranked = playernames[count] + playernames[count + 1] + playernames[count + 2] + playernames[count + 3]
            snail_ranked = snail[count] + snail[count + 1] + snail[count + 2] + snail[count + 3]
            kingup_ranked = kingup[count] + kingup[count + 1] + kingup[count + 2] + kingup[count + 3]
            workers_ranked = workers[count] + workers[count + 1] + workers[count + 2] + workers[count + 3]
            mythium_list_pergame.clear()
            gameelo_list.append(gameelo[1][queue_count])
            for i, x in enumerate(playernames_ranked):
                if str(x).lower() == str(playername).lower():
                    for n, s in enumerate(snail_ranked[i]):
                        small_send = 0
                        send = count_mythium(snail_ranked[i][n]) + len(kingup_ranked[i][n]) * 20
                        mythium_list_pergame.append(send)
                        if n <= 9:
                            if workers_ranked[i][n] > 5:
                                worker_adjusted = workers_ranked[i][n] - 5
                                small_send = worker_adjusted / 5 * 20
                            if send <= small_send:
                                save_count_pre10 += 1
                        elif n > 9:
                            worker_adjusted = workers_ranked[i][n] * (pow((1 + 6 / 100), n+1))
                            small_send = worker_adjusted / 5 * 20
                            if send <= small_send:
                                save_count += 1
                    mythium_list.append(sum(mythium_list_pergame))
                    worker_10_list.append(workers_ranked[i][9])
                    if i == 0 or 1:
                        kinghp_list.append(kinghp_left[1][queue_count][9])
                    else:
                        kinghp_list.append(kinghp_right[1][queue_count][9])
            save_count_pre10_list.append(save_count_pre10)
            save_count_list.append(save_count)
            save_count_pre10 = 0
            save_count = 0
            count = count + 4
            queue_count = queue_count + 1
            ranked_count = ranked_count + 1

        elif playercount[1][queue_count] == 8:
            count = count + 8
            queue_count = queue_count + 1
            games_limit = games_limit + 4
            print('Skip 8 player game: ' + str(count))
        elif playercount[1][queue_count] == 2:
            count = count + 2
            queue_count = queue_count + 1
            games_limit = games_limit - 2
            print('Skip 2 player game: ' + str(count))
        elif playercount[1][queue_count] == 1:
            count = count + 1
            queue_count = queue_count + 1
            games_limit = games_limit - 3
            print('Skip 1 player game: ' + str(count))
        else:
            queue_count = queue_count + 1
            count = count + 4
            print('Skip 4 player game: ' + str(count))
    waves_post10 = round(sum(ending_wave_list) / len(ending_wave_list), 2) - 10
    saves_pre10 = round(sum(save_count_pre10_list) / len(save_count_pre10_list), 2)
    saves_post10 = round(sum(save_count_list) / len(save_count_list), 2)
    king_hp_10 = sum(kinghp_list) / len(kinghp_list)
    avg_gameelo = sum(gameelo_list) / len(gameelo_list)
    if ranked_count > 0:
        return (playername).capitalize() + "'s elcringo stats(Averages from last " + str(ranked_count) +" ranked games):<:GK:1161013811927601192>\n" \
            'Saves first 10:  ' + str(saves_pre10) + '/10 waves (' + str(round(saves_pre10 / 10 * 100, 2)) + '%)\n' +\
            'Saves after 10:  ' + str(saves_post10)+'/' + str(round(waves_post10, 2)) + ' waves (' + str(round(saves_post10 / waves_post10 * 100, 2)) + '%)\n'\
            'Worker on 10:  ' + str(round(sum(worker_10_list) / len(worker_10_list), 2)) + "\n"\
            'King hp on 10: ' + str(round(king_hp_10 * 100, 2)) + '%\n' + \
            'Game elo:  ' + str(round(avg_gameelo)) + '\n' + \
            'Mythium sent per game:  ' + str(round(sum(mythium_list) / len(mythium_list), 2))
    else:
        return 'Not enough ranked data'


def apicall_mmstats(playername):
    playerid = apicall_getid(playername)
    if playerid == 0:
        return 'Player ' + playername + ' not found.'
    count = 0
    ranked_count = 0
    queue_count = 0
    mmnames_list = ['LockIn', 'Greed', 'Redraw', 'Yolo', 'Fiesta', 'CashOut', 'Castle', 'Cartel', 'Chaos']
    masterminds_dict = {"LockIn": {"Count": 0, "Wins": 0, "W10": 0}, "Greed": {"Count": 0, "Wins": 0, "W10": 0},
                        "Redraw": {"Count": 0, "Wins": 0, "W10": 0}, "Yolo": {"Count": 0, "Wins": 0, "W10": 0},
                        "Fiesta": {"Count": 0, "Wins": 0, "W10": 0}, "CashOut": {"Count": 0, "Wins": 0, "W10": 0},
                        "Castle": {"Count": 0, "Wins": 0, "W10": 0}, "Cartel": {"Count": 0, "Wins": 0, "W10": 0},
                        "Chaos": {"Count": 0, "Wins": 0, "W10": 0}}
    opener_list = []
    masterminds_list = []
    gameresult_list = []
    games = get_games_saved_count(playername)
    games_limit = games * 4
    try:
        history_raw = apicall_getmatchistory(playerid, games)
    except TypeError as e:
        print(e)
        return playername + ' has not played enough games.'
    games = get_games_saved_count(playername)
    games_limit = games * 4
    playernames = list(divide_chunks(extract_values(history_raw, 'playerName')[1], 1))
    masterminds = list(divide_chunks(extract_values(history_raw, 'legion')[1], 1))
    gameresult = list(divide_chunks(extract_values(history_raw, 'gameResult')[1], 1))
    workers = list(divide_chunks(extract_values(history_raw, 'workersPerWave')[1], 1))
    opener = list(divide_chunks(extract_values(history_raw, 'firstWaveFighters')[1], 1))
    gameid = extract_values(history_raw, '_id')
    queue_type = extract_values(history_raw, 'queueType')
    playercount = extract_values(history_raw, 'playerCount')
    endingwaves = extract_values(history_raw, 'endingWave')
    while count < games_limit:
        if str(queue_type[1][queue_count]) == 'Normal' and endingwaves[1][queue_count] >= 10:
            print('Ranked game: ' + str(ranked_count + 1) + ' | Gameid: ' + str(gameid[1][queue_count]))
            playernames_ranked = playernames[count] + playernames[count + 1] + playernames[count + 2] + playernames[count + 3]
            masterminds_ranked = masterminds[count] + masterminds[count + 1] + masterminds[count + 2] + masterminds[count + 3]
            gameresult_ranked = gameresult[count] + gameresult[count + 1] + gameresult[count + 2] + gameresult[count + 3]
            workers_ranked = workers[count] + workers[count + 1] + workers[count + 2] + workers[count + 3]
            opener_ranked = opener[count] + opener[count + 1] + opener[count + 2] + opener[count + 3]
            for i, x in enumerate(playernames_ranked):
                if str(x).lower() == str(playername).lower():
                    masterminds_dict[masterminds_ranked[i]]["Count"] += 1
                    if gameresult_ranked[i] == 'won':
                        masterminds_dict[masterminds_ranked[i]]["Wins"] += 1
                    masterminds_dict[masterminds_ranked[i]]["W10"] += workers_ranked[i][9]
                    opener_list.append(opener_ranked[i])
                    masterminds_list.append(masterminds_ranked[i])
                    gameresult_list.append(gameresult_ranked[i])
            count = count + 4
            queue_count = queue_count + 1
            ranked_count = ranked_count + 1

        elif playercount[1][queue_count] == 8:
            count = count + 8
            queue_count = queue_count + 1
            games_limit = games_limit + 4
            print('Skip 8 player game: ' + str(count))
        elif playercount[1][queue_count] == 2:
            count = count + 2
            queue_count = queue_count + 1
            games_limit = games_limit - 2
            print('Skip 2 player game: ' + str(count))
        elif playercount[1][queue_count] == 1:
            count = count + 1
            queue_count = queue_count + 1
            games_limit = games_limit - 3
            print('Skip 1 player game: ' + str(count))
        else:
            queue_count = queue_count + 1
            count = count + 4
            print('Skip 4 player game: ' + str(count))

    mm1 = []
    mm2 = []
    mm3 = []
    mm4 = []
    mm1_openers = []
    mm2_openers = []
    mm3_openers = []
    mm4_openers = []
    mm1_results = []
    mm2_results = []
    mm3_results = []
    mm4_results = []
    for x in masterminds_dict:
        if len(mm1) == 0:
            mm1.append(x)
            mm1.append(masterminds_dict[x]['Count'])
            mm1.append(masterminds_dict[x]['Wins'])
            mm1.append(masterminds_dict[x]['W10'])
            continue
        elif masterminds_dict[x]['Count'] > mm1[1]:
            mm2_copy = mm2.copy()
            mm3_copy = mm3.copy()
            mm2.clear()
            mm2 = mm1.copy()
            mm3.clear()
            mm3 = mm2_copy
            mm4.clear()
            mm4 = mm3_copy
            mm1.clear()
            mm1.append(x)
            mm1.append(masterminds_dict[x]['Count'])
            mm1.append(masterminds_dict[x]['Wins'])
            mm1.append(masterminds_dict[x]['W10'])
            continue
        if len(mm2) == 0:
            mm2.append(x)
            mm2.append(masterminds_dict[x]['Count'])
            mm2.append(masterminds_dict[x]['Wins'])
            mm2.append(masterminds_dict[x]['W10'])
            continue
        elif masterminds_dict[x]['Count'] > mm2[1]:
            mm3_copy = mm3.copy()
            mm3 = mm2.copy()
            mm4.clear()
            mm4 = mm3_copy
            mm2.clear()
            mm2.append(x)
            mm2.append(masterminds_dict[x]['Count'])
            mm2.append(masterminds_dict[x]['Wins'])
            mm2.append(masterminds_dict[x]['W10'])
            continue
        if len(mm3) == 0:
            mm3.append(x)
            mm3.append(masterminds_dict[x]['Count'])
            mm3.append(masterminds_dict[x]['Wins'])
            mm3.append(masterminds_dict[x]['W10'])
            continue
        elif masterminds_dict[x]['Count'] > mm3[1]:
            mm4.clear()
            mm4 = mm3.copy()
            mm3.clear()
            mm3.append(x)
            mm3.append(masterminds_dict[x]['Count'])
            mm3.append(masterminds_dict[x]['Wins'])
            mm3.append(masterminds_dict[x]['W10'])
            continue
        if len(mm4) == 0:
            mm4.append(x)
            mm4.append(masterminds_dict[x]['Count'])
            mm4.append(masterminds_dict[x]['Wins'])
            mm4.append(masterminds_dict[x]['W10'])
            continue
        elif masterminds_dict[x]['Count'] > mm4[1]:
            mm4.clear()
            mm4.append(x)
            mm4.append(masterminds_dict[x]['Count'])
            mm4.append(masterminds_dict[x]['Wins'])
            mm4.append(masterminds_dict[x]['W10'])

    for i, x in enumerate(masterminds_list):
        if x == mm1[0]:
            mm1_results.append(gameresult_list[i])
            if ',' in opener_list[i]:
                string = opener_list[i]
                commas = string.count(',')
                mm1_openers.append(string.split(',',commas)[commas])
            else:
                mm1_openers.append(opener_list[i])
        if x == mm2[0]:
            mm2_results.append(gameresult_list[i])
            if ',' in opener_list[i]:
                string = opener_list[i]
                commas = string.count(',')
                mm2_openers.append(string.split(',', commas)[commas])
            else:
                mm2_openers.append(opener_list[i])
        if x == mm3[0]:
            mm3_results.append(gameresult_list[i])
            if ',' in opener_list[i]:
                string = opener_list[i]
                commas = string.count(',')
                mm3_openers.append(string.split(',', commas)[commas])
            else:
                mm3_openers.append(opener_list[i])
        if x == mm4[0]:
            mm4_results.append(gameresult_list[i])
            if ',' in opener_list[i]:
                string = opener_list[i]
                commas = string.count(',')
                mm4_openers.append(string.split(',', commas)[commas])
            else:
                mm4_openers.append(opener_list[i])

    def calc_wr(list):
        return str(round(list[2] / list[1] * 100, 2))
    def calc_pr(list):
        return str(round(list[1] / ranked_count * 100, 2))
    def most_common(list):
        data = Counter(list)
        return data.most_common(1)[0][0]
    def get_open_wrpr(list, list2, list3):
        wins = 0
        count = 0
        for i, x in enumerate(list2):
            if most_common(list2) in x:
                count += 1
                if list3[i] == 'won':
                    wins += 1
        return str(count) + ' Games, ' + str(round(wins / count * 100, 2)) + '% Winrate, ' + str(round(count / list[1] * 100, 2)) + '% Playrate'
    emojis = {"LockIn": "<:LockIn:1166779254554497095>", "Greed": "<:Greed:1166779251257790645>", "Redraw": "<:Redraw:1166779258073530368>",
              "Yolo": "<:Yolo:1166779261353476207>", "Fiesta": "<:Fiesta:1166779247768129617>", "CashOut": "<:CashOut:1166779238519681216>",
              "Castle": "<:Castle:1166779242013524091>", "Cartel": "<:Cartel:1166779236028252282>", "Chaos": "<:Chaos:1166779245247336458>"}
    output = ''
    if ranked_count > 5:
        if mm1[1] > 0:
            output = str(playername).capitalize() + "'s Mastermind stats(From last " + str(ranked_count) + ' ranked games):\n' +\
            emojis.get(mm1[0]) + mm1[0] + ' (' + str(mm1[1]) + ' Games, ' + str(calc_wr(mm1)) + '% Winrate, ' + str(calc_pr(mm1)) + '% Pickrate, Worker on 10: ' + str(round(mm1[3] / mm1[1], 2)) + ')\n' +\
            '-Fav. opener: ' + most_common(mm1_openers) + ' (' + str(get_open_wrpr(mm1, mm1_openers, mm1_results)) + ')\n'
        if mm2[1] > 0:
            output = output + emojis.get(mm2[0]) + mm2[0] + ' (' + str(mm2[1]) + ' Games, ' + str(calc_wr(mm2)) + '% Winrate, ' + str(calc_pr(mm2)) + '% Pickrate, Worker on 10: ' + str(round(mm2[3] / mm2[1], 2)) + ')\n' + \
            '-Fav. opener: ' + most_common(mm2_openers) + ' (' + str(get_open_wrpr(mm2, mm2_openers, mm2_results)) + ')\n'
        if mm3[1] > 0:
            output = output + emojis.get(mm3[0]) + mm3[0] + ' (' + str(mm3[1]) + ' Games, ' + str(calc_wr(mm3)) + '% Winrate, ' + str(calc_pr(mm3)) + '% Pickrate, Worker on 10: ' + str(round(mm3[3] / mm3[1], 2)) + ')\n' + \
            '-Fav. opener: ' + most_common(mm3_openers) + ' (' + str(get_open_wrpr(mm3, mm3_openers, mm3_results)) + ')\n'
        if mm4[1] > 0:
            output = output + emojis.get(mm4[0]) + mm4[0] + ' (' + str(mm4[1]) + ' Games, ' + str(calc_wr(mm4)) + '% Winrate, ' + str(calc_pr(mm4)) + '% Pickrate, Worker on 10: ' + str(round(mm4[3] / mm4[1], 2)) + ')\n' + \
            '-Fav. opener: ' + most_common(mm4_openers) + ' (' + str(get_open_wrpr(mm4, mm4_openers, mm4_results)) + ')\n'
        return output
    else:
        return 'Not enough ranked data'

def apicall_elo(playername, rank):
    playerid = apicall_getid(playername)
    if playerid == 0:
        output = 'Player ' + str(playername) + ' not found.'
    else:
        stats = apicall_getstats(playerid)
        playtime_minutes = stats['secondsPlayed'] / 60
        playtime_hours = playtime_minutes / 60
        url = 'https://apiv2.legiontd2.com/players/stats?limit=100&sortBy=overallElo&sortDirection=-1'
        api_response = requests.get(url, headers=header)
        leaderboard = json.loads(api_response.text)
        history_details = apicall_matchhistorydetails(playerid)
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
    name = apicall_getprofile(player_info[0]['_id'])
    return apicall_elo(str(name['playerName']).lower(), rank)


def apicall_gamestats(playername):
    playerid = apicall_getid(playername)
    stats = apicall_getstats(playerid)
    wins = stats['rankedWinsThisSeason']
    loses = stats['rankedLossesThisSeason']
    winrate = wins / (wins + loses)
    return str(playername).capitalize() + "'s stats(Season 2023):\nElo: " + str(stats['overallElo']) + '(Peak: ' + str(
        stats['overallPeakEloThisSeason']) + ')\nGames played: ' + \
        str(wins + loses) + '\nWinrate: ' + str(round(winrate * 100)) + '%\nBehavior score: ' + str(
            stats['behaviorScore'] / 10)


