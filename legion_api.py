import datetime
import json
import pathlib
import traceback
from datetime import datetime, timedelta
from pathlib import Path
import json_db

import requests

with open('Files/json/Secrets.json', 'r') as f:
    secret_file = json.load(f)
    f.close()

header = {'x-api-key': secret_file.get('apikey')}

def api_call_logger(request_type):
    try:
        with open("Files/json/api_calls.json", "r") as file:
            api_call_dict = json.load(file)
        date = datetime.now()
        if "next_reset" not in api_call_dict:
            api_call_dict["next_reset"] = (date + timedelta(days=1)).strftime("%m/%d/%Y")
        elif datetime.strptime(api_call_dict["next_reset"], "%m/%d/%Y") < datetime.now():
            api_call_dict = {"next_reset": (date + timedelta(days=1)).strftime("%m/%d/%Y")}
        if request_type not in api_call_dict:
            api_call_dict[request_type] = 1
        else:
            api_call_dict[request_type] += 1
        with open("Files/json/api_calls.json", "w") as file:
            json.dump(api_call_dict, file)
    except Exception:
        traceback.print_exc()

def get_random_games():
    games = []
    for i in range(6):
        games.append([1600+200*i, 1600+200*(i+1), ""])
    print(games)
    offset = 0
    games_found = 0
    tries = 0
    while games_found < 6:
        if tries == 50: break
        try:
            url = 'https://apiv2.legiontd2.com/games?limit=50&offset='+str(offset)+'&sortBy=date&sortDirection=-1&includeDetails=false&countResults=false&queueType=Normal'
            api_call_logger("/games")
            response = json.loads(requests.get(url, headers=header).text)
            for game in response:
                if game["endingWave"] < 5: continue
                for elo_bracket in games:
                    if elo_bracket[0] <= game["gameElo"] <= elo_bracket[1] and elo_bracket[2] == "":
                        print("game found with: "+str(game["gameElo"])+" elo")
                        elo_bracket.append(game["endingWave"])
                        elo_bracket.append(game["gameElo"])
                        elo_bracket[2] = game["_id"]
                        games_found += 1
                        break
            offset += 50
        except Exception:
            traceback.print_exc()
        tries += 1
    return games
        
        

def getid(playername):
    request_type = 'players/byName/'
    url = 'https://apiv2.legiontd2.com/' + request_type + playername
    try:
        api_response = requests.get(url, headers=header)
        if 'Limit Exceeded' in api_response.text:
            return 1
        api_response.raise_for_status()
    except requests.exceptions.HTTPError:
        return 0
    else:
        api_call_logger(request_type)
        playerid = json.loads(api_response.text)
        return playerid['_id']

def getprofile(playerid):
    request_type = 'players/byId/'
    url = 'https://apiv2.legiontd2.com/' + request_type + playerid
    api_response = requests.get(url, headers=header)
    player_profile = json.loads(api_response.text)
    api_call_logger(request_type)
    return player_profile

def getstats(playerid):
    request_type = 'players/stats/'
    url = 'https://apiv2.legiontd2.com/' + request_type + playerid
    api_response = requests.get(url, headers=header)
    stats = json.loads(api_response.text)
    api_call_logger(request_type)
    return stats

def pullgamedata(playerid, offset, path, expected):
    ranked_count = 0
    games_count = 0
    output = []
    url = 'https://apiv2.legiontd2.com/players/matchHistory/' + str(playerid) + '?limit=' + str(50) + '&offset=' + str(offset) + '&countResults=false'
    print('Pulling ' + str(50) + ' games from API...')
    api_response = requests.get(url, headers=header)
    api_call_logger("players/matchHistory/")
    raw_data = json.loads(api_response.text)
    print('Saving ranked games.')
    for x in raw_data:
        if ranked_count == expected:
            break
        if (raw_data == {'message': 'Internal server error'}) or (raw_data == {'err': 'Entry not found.'}):
            break
        if (x['queueType'] == 'Normal'):
            if Path(Path(str(path + 'gamedata/')+x['date'].split('.')[0].replace('T', '-').replace(':', '-')+'_'+x['version'].replace('.', '-')+'_'+str(x['gameElo'])+ '_' + str(x['_id']) + ".json")).is_file():
                print('File already there, breaking loop.')
                break
            ranked_count += 1
            with open(str(path + 'gamedata/')+x['date'].split('.')[0].replace('T', '-').replace(':', '-')+'_'+x['version'].replace('.', '-')+'_'+str(x['gameElo'])+'_' + str(x['_id']) + ".json", "w") as f:
                json.dump(x, f)
                f.close()
            if not Path(Path(str(pathlib.Path(__file__).parent.resolve()) + "/Games/"+x['date'].split('.')[0].replace('T', '-').replace(':', '-')+'_'+x['version'].replace('.', '-')+'_'+str(x['gameElo'])+ '_' + str(x['_id']) + ".json")).is_file():
                with open(str(pathlib.Path(__file__).parent.resolve()) + "/Games/"+x['date'].split('.')[0].replace('T', '-').replace(':', '-')+'_'+x['version'].replace('.', '-')+'_'+str(x['gameElo'])+'_' + str(x['_id']) + ".json", "w") as f2:
                    json.dump(x, f2)
                    f2.close()
        games_count += 1
    output.append(ranked_count)
    output.append(games_count)
    return output

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
            games_count += json_db.get_matchistory(player["_id"], 200, 0, '0', 1)
        elif ranked_games == 0:
            print('No games this season.')
            continue
        else:
            games_count += json_db.get_matchistory(player["_id"], ranked_games, 0, '0', 1)
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