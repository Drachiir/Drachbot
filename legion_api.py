import datetime
import json
import pathlib
import random
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

import discord

import drachbot_db
import peewee_pg
import util
import peewee
from peewee import fn
from peewee_pg import PlayerProfile, GameData, PlayerData, db
from peewee import InterfaceError, OperationalError
from psycopg2 import OperationalError as Psycopg2OperationalError
import requests

with open('Files/json/Secrets.json', 'r') as f:
    secret_file = json.load(f)
    f.close()

header = {'x-api-key': secret_file.get('apikey')}

def get_random_games():
    games = []
    for i in range(8):
        games.append([1400+200*i, 1400+200*(i+1), ""])
    offset = 200
    games_found = 0
    tries = 0
    while games_found < 8:
        if tries == 50: break
        try:
            url = 'https://apiv2.legiontd2.com/games?limit=50&offset='+str(offset)+'&sortBy=date&sortDirection=-1&includeDetails=false&countResults=false&queueType=Normal'
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
            offset += random.randint(50,1000)
        except Exception:
            traceback.print_exc()
        tries += 1
    return games

def get_leaderboard(num):
    url = f'https://apiv2.legiontd2.com/players/stats?limit={num}&sortBy=overallElo&sortDirection=-1'
    api_response = requests.get(url, headers=header)
    return json.loads(api_response.text)

def getid(playername):
    try:
        with db.atomic():
            profile_data_query = (PlayerProfile
                                  .select(PlayerProfile.player_id)
                                  .where(fn.LOWER(PlayerProfile.player_name) == fn.LOWER(playername))
                                  .dicts())
            rows = list(profile_data_query)
            if len(rows) == 1:
                return rows[0]["player_id"]
    except InterfaceError as e:
        print(f"InterfaceError: {e}")
        # Try reconnecting if the connection was closed
        if db.is_closed():
            db.connect()
            return getid(playername)  # Retry the function after reconnecting
    except (OperationalError, Psycopg2OperationalError) as e:
        print(f"Database error: {e}")
    #Get id by api if not found in db
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
        playerid = json.loads(api_response.text)
        return playerid['_id']

def getprofile(playerid):
    request_type = 'players/byId/'
    url = 'https://apiv2.legiontd2.com/' + request_type + playerid
    api_response = requests.get(url, headers=header)
    player_profile = json.loads(api_response.text)
    return player_profile

def getstats(playerid):
    request_type = 'players/stats/'
    url = 'https://apiv2.legiontd2.com/' + request_type + playerid
    api_response = requests.get(url, headers=header)
    stats = json.loads(api_response.text)
    return stats

def pullgamedata(playerid, offset, expected):
    ranked_count = 0
    games_count = 0
    url = 'https://apiv2.legiontd2.com/players/matchHistory/' + str(playerid) + '?limit=' + str(50) + '&offset=' + str(offset) + '&countResults=false'
    api_response = requests.get(url, headers=header)
    raw_data = json.loads(api_response.text)
    for x in raw_data:
        if ranked_count == expected:
            break
        if (raw_data == {'message': 'Internal server error'}) or (raw_data == {'err': 'Entry not found.'}):
            print(f"API fail: {url}\n{raw_data}")
            break
        if x['queueType'] == 'Normal':
            ranked_count += 1
            try:
                peewee_pg.save_game(x)
            except Exception:
                break
        games_count += 1
    return [ranked_count, games_count]

@db.atomic()
def get_recent_games(calls=2, time_delta=3, timeout_count_max = 1):
    date_now = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    date_after = (datetime.now(tz=timezone.utc) - timedelta(minutes=time_delta+10)).strftime("%Y-%m-%d %H:%M:%S")
    date_now = date_now.replace(" ", "%20")
    date_now = date_now.replace(":", "%3A")
    date_after = date_after.replace(" ", "%20")
    date_after = date_after.replace(":", "%3A")
    offset = 50
    ranked_count = 0
    timeout_count = 0
    ranks_dict = {
        'Legend': [2800, '<:Legend:1217999693234176050>', 0],
        'GrandMaster': [2600, '<:Grandmaster:1217999691883741224>', 0],
        'SeniorMaster': [2400, '<:SeniorMaster:1217999704349081701>', 0],
        'Master': [2200, '<:Master:1217999699114590248>', 0],
        'Expert': [2000, '<:Expert:1217999688494747718>', 0],
        'Diamond': [1800, '<:Diamond:1217999686888325150>', 0],
        'Platinum': [1600, '<:Platinum:1217999701337571379>', 0],
        'Gold': [1400, '<:Gold:1217999690369335407>', 0],
        'Silver': [1200, '<:Silver:1217999706555158631>', 0],
        'Bronze': [1000, '<:Bronze:1217999684484862057>', 0],
        'Unranked': [0, "<:Unranked:1241064654717980723>", 0]
    }
    def add_game_count(elo):
        for elo_bracket in ranks_dict:
            if elo >= ranks_dict[elo_bracket][0]:
                ranks_dict[elo_bracket][2] += 1
                break
    for i in range(calls):
        if timeout_count == timeout_count_max:
            break
        temp = 0
        url = (f'https://apiv2.legiontd2.com/games'
                f'?limit=50&offset={offset*i}&sortBy=gameElo&sortDirection=-1'
                f'&dateBefore={date_now}'
                f'&dateAfter={date_after}'
                f'&includeDetails=true&countResults=false&queueType=Normal')
        history_raw = json.loads(requests.get(url, headers= header).text)
        if (history_raw == {'message': 'Internal server error'}) or (history_raw == {'err': 'Entry not found.'}):
            timeout_count += 1
            print("api fail", history_raw)
            continue
        for game in history_raw:
            if game['queueType'] == 'Normal':
                if game["gameElo"] < 1600:
                    temp = 50
                    break
                if GameData.get_or_none(GameData.game_id == game["_id"]) is None:
                    timeout_count = 0
                    add_game_count(game["gameElo"])
                    ranked_count += 1
                    try:
                        peewee_pg.save_game(game)
                    except Exception:
                        pass
                else:
                    temp += 1
        if temp == 50:
            timeout_count += 1
    output = ""
    for i in ranks_dict:
        if ranks_dict[i][2] != 0:
            output += f"{util.get_ranked_emote(ranks_dict[i][0])} {i}: {util.human_format(ranks_dict[i][2])} Games\n"

    return discord.Embed(color=util.random_color(),
                         title=f"Pulled {util.human_format(ranked_count)} new ranked games.",
                         description=output).set_author(name="[Scheduled Update]", icon_url="https://overlay.drachbot.site/favicon.ico")

def save_game_by_id(game_id):
    url = 'https://apiv2.legiontd2.com/games/byId/' + game_id + '?includeDetails=true'
    api_response = requests.get(url, headers=header)
    x = json.loads(api_response.text)
    peewee_pg.save_game(x)