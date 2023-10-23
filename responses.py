import requests
import json

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
    if '!test' in p_message:
        return ':GK~1:'


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


def apicall_getname(playerid):
    url = 'https://apiv2.legiontd2.com/players/byId/' + playerid
    api_response = requests.get(url, headers=header)
    playername = json.loads(api_response.text)
    return playername['playerName']


def apicall_getstats(playerid):
    request_type = 'players/stats/' + playerid
    url = 'https://apiv2.legiontd2.com/' + request_type
    api_response = requests.get(url, headers=header)
    stats = json.loads(api_response.text)
    return stats


def apicall_getmatchistory(playerid, games, offset):
    request_type = 'players/matchHistory/' + str(playerid) + '?limit=' + str(games) +'&offset=' + str(offset) + '&countResults=false'
    url = 'https://apiv2.legiontd2.com/' + request_type
    api_response = requests.get(url, headers=header)
    history_raw = json.loads(api_response.text)
    return history_raw


def apicall_matchhistorywins(playername, playerid):
    history_raw = apicall_getmatchistory(playerid, 10, 0)
    player_names = extract_values(history_raw, 'playerName')
    game_results = extract_values(history_raw, 'gameResult')
    wins = count_value(str(playername).lower(), 'won', player_names, game_results)
    return wins


def apicall_matchhistoryelogain(playername, playerid):
    history_raw = apicall_getmatchistory(playerid, 10, 0)
    player_names = extract_values(history_raw, 'playerName')
    elochanges = extract_values(history_raw, 'eloChange')
    elochange_final = count_elochange(str(playername).lower(), player_names, elochanges)
    output = elochange_final
    if elochange_final > 0:
        output = '+' + str(elochange_final)
    return output


def apicall_wave1tendency(playername, bool):
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
    games_limit = 400
    try:
        history_raw = apicall_getmatchistory(playerid, 50, 0) + apicall_getmatchistory(playerid, 50, 50)
    except TypeError as e:
        print(e)
        return playername + ' has not played enough games.'
    playernames = list(divide_chunks(extract_values(history_raw, 'playerName')[1], 1))
    if bool:
        snail = list(divide_chunks(extract_values(history_raw, 'mercenariesSentPerWave')[1], 1))
        kingup = list(divide_chunks(extract_values(history_raw, 'kingUpgradesPerWave')[1], 1))
    else:
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
    if send_total > 4:
        return (playername).capitalize() + "'s Wave 1 stats: (Last " + str(send_total) + " ranked games)\nKingup: " + \
            str(kingup_total) + ' (Attack: ' + str(kingup_atk_count) + ' Regen: ' + str(kingup_regen_count) + \
            ' Spell: ' + str(kingup_spell_count) + ')\nSnail: ' + str(snail_count) + '\nSave: ' + str(save_count)
    else:
        return 'Not enough ranked data'


def apicall_winrate(playername, playername2, bool):
    playerid = apicall_getid(playername)
    if playerid == 0:
        return 'Player ' + playername + ' not found.'
    playerid2 = apicall_getid(playername2)
    if playerid2 == 0:
        return 'Player ' + playername2 + ' not found.'
    count = 0
    win_count = 0
    game_count = 0
    ranked_count = 0
    queue_count = 0
    games_limit = 1600
    try:
        history_raw = apicall_getmatchistory(playerid, 50, 0) + apicall_getmatchistory(playerid, 50, 50) +\
            apicall_getmatchistory(playerid, 50, 100) + apicall_getmatchistory(playerid, 50, 150) + \
            apicall_getmatchistory(playerid, 50, 200) + apicall_getmatchistory(playerid, 50, 250) + \
            apicall_getmatchistory(playerid, 50, 300) + apicall_getmatchistory(playerid, 50, 350)
            # apicall_getmatchistory(playerid, 50, 400) + apicall_getmatchistory(playerid, 50, 450) + \
            # apicall_getmatchistory(playerid, 50, 500) + apicall_getmatchistory(playerid, 50, 550) + \
            # apicall_getmatchistory(playerid, 50, 600) + apicall_getmatchistory(playerid, 50, 650) + \
            # apicall_getmatchistory(playerid, 50, 700) + apicall_getmatchistory(playerid, 50, 750)

    except TypeError as e:
        print(e)
        return playername + ' has not played enough games.'
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
            print(playernames_ranked_west, playernames_ranked_east)
            for i, x in enumerate(playernames_ranked_west):
                if str(x).lower() == str(playername).lower():
                    if bool:
                        if playernames_ranked_east[0].lower() == playername2.lower():
                            game_count += 1
                            print(gameresult_ranked_west[i])
                            if gameresult_ranked_west[i] == 'won':
                                win_count += 1
                        elif playernames_ranked_east[1].lower() == playername2.lower():
                            game_count += 1
                            print(gameresult_ranked_west[i])
                            if gameresult_ranked_west[i] == 'won':
                                win_count += 1
                    else:
                        if playernames_ranked_west[0].lower() == playername2.lower():
                            game_count += 1
                            print(gameresult_ranked_west[i])
                            if gameresult_ranked_west[i] == 'won':
                                win_count += 1
                        elif playernames_ranked_west[1].lower() == playername2.lower():
                            game_count += 1
                            print(gameresult_ranked_west[i])
                            if gameresult_ranked_west[i] == 'won':
                                win_count += 1
            for i, x in enumerate(playernames_ranked_east):
                if str(x).lower() == str(playername).lower():
                    if bool:
                        if playernames_ranked_west[0].lower() == playername2.lower():
                            game_count += 1
                            print(gameresult_ranked_east[i])
                            if gameresult_ranked_east[i] == 'won':
                                win_count += 1
                        elif playernames_ranked_west[1].lower() == playername2.lower():
                            game_count += 1
                            print(gameresult_ranked_east[i])
                            if gameresult_ranked_east[i] == 'won':
                                win_count += 1
                    else:
                        if playernames_ranked_east[0].lower() == playername2.lower():
                            game_count += 1
                            print(gameresult_ranked_east[i])
                            if gameresult_ranked_east[i] == 'won':
                                win_count += 1
                        elif playernames_ranked_east[1].lower() == playername2.lower():
                            game_count += 1
                            print(gameresult_ranked_east[i])
                            if gameresult_ranked_east[i] == 'won':
                                win_count += 1

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
    if bool:
        output = 'against'
    else:
        output = 'with'
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
    games_limit = 800
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
        history_raw = apicall_getmatchistory(playerid, 50, 0) + apicall_getmatchistory(playerid, 50, 50) + \
                      apicall_getmatchistory(playerid, 50, 100) + apicall_getmatchistory(playerid, 50, 150)
    except TypeError as e:
        print(e)
        return playername + ' has not played enough games.'
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
        new_dict = {item['_id']: item['_id'] for item in leaderboard}
        if rank == 0:
            for i, key in enumerate(new_dict.keys()):
                if key == playerid:
                    index = i
                    return str(playername).capitalize() + ' is rank ' + str(index + 1) + ' with ' + str(
                        stats['overallElo']) + ' elo (Peak: ' + str(stats['overallPeakEloThisSeason']) + ') and ' + str(
                        round(playtime_hours)) + ' in game hours.\nThey have won ' + \
                        str(apicall_matchhistorywins(playername, playerid)) + ' out of their last 10 games. (Elo change: ' + \
                        str(apicall_matchhistoryelogain(playername, playerid)) + ')'
            else:
                return str(playername).capitalize() + ' has ' + str(stats['overallElo']) + ' elo (Peak: ' + str(
                    stats['overallPeakEloThisSeason']) + ') with ' + str(round(playtime_hours)) + ' in game hours.\n' \
                    'They have won ' + str(apicall_matchhistorywins(playername, playerid)) + ' out of their last 10 games. ' \
                    '(Elo change: ' + str(apicall_matchhistoryelogain(playername, playerid)) + ')'
        else:
            return str(playername).capitalize() + ' is rank ' + str(rank) + ' with ' + str(
                stats['overallElo']) + ' elo (Peak: ' + str(stats['overallPeakEloThisSeason']) + ') and ' + str(
                round(playtime_hours)) + ' in game hours.\nThey have won ' + \
                str(apicall_matchhistorywins(playername, playerid)) + ' out of their last 10 games. (Elo change: ' + \
                str(apicall_matchhistoryelogain(playername, playerid)) + ')'


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
    print(player_info[0]['_id'])
    name = apicall_getname(player_info[0]['_id'])
    return apicall_elo(str(name).lower(), rank)


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


