import glob
import json
import os
import os.path
import pathlib
import time
from pathlib import Path
import legion_api
import peewee_pg
import util
from peewee_pg import PlayerProfile, GameData, PlayerData, db
from playhouse.postgres_ext import *
import datetime
from datetime import datetime, timezone

def get_games_loop(playerid, offset, expected, timeout_limit = 1):
    data = legion_api.pullgamedata(playerid, offset, expected)
    count = data[0]
    games_count = data[1]
    timeout = 0
    while count < expected:
        if data[0] == 0:
            timeout += 1
        count += data[0]
        games_count += data[1]
        if timeout == timeout_limit:
            break
        offset += 50
        data = legion_api.pullgamedata(playerid, offset, expected)

    return games_count

@db.atomic()
def get_matchistory(playerid, games, min_elo=0, patch='0', update = 0, earlier_than_wave10 = False, sort_by = "date", req_columns=None, skip_stats=False, max_elo = 9001, include_wave_one_finishes=False):
    if req_columns is None:
        req_columns = []
    patch_list = []
    if earlier_than_wave10:
        earliest_wave = 1 if include_wave_one_finishes else 2
    else:
        earliest_wave = 11
    if sort_by == "date":
        sort_arg = GameData.date
    else:
        sort_arg = GameData.game_elo
    if patch != '0' and "-" not in patch and "+" not in patch:
        patch_list = patch.replace(" ", "").split(',')
    elif patch != "0" and "+" in patch and "-" not in patch:
        patch_new = patch.replace(" ", "").replace("+", "")
        print(patch_new)
        if len(patch_new) == 5:
            patch_new = patch_new.split('.')
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
            start_major, start_minor = map(int, patch_new[0].split('.'))
            end_major, end_minor = map(int, patch_new[1].split('.'))

            for major in range(start_major, end_major + 1):
                if major == start_major:
                    for minor in range(start_minor, 12):
                        prefix = "0" if minor < 10 else ""
                        patch_list.append(f"{major}.{prefix}{minor}")
                elif major == end_major:
                    for minor in range(0, end_minor + 1):
                        prefix = "0" if minor < 10 else ""
                        patch_list.append(f"{major}.{prefix}{minor}")
                else:
                    for minor in range(0, 12):
                        prefix = "0" if minor < 10 else ""
                        patch_list.append(f"{major}.{prefix}{minor}")
        else:
            return []
    games_count = 0
    if playerid != 'all':
        if games == 0:
            games2 = GameData.select().where(GameData.player_ids.contains(playerid)).count()
        else:
            games2 = games
        if not skip_stats:
            if PlayerProfile.get_or_none(PlayerProfile.player_id == playerid) is None:
                print(playerid + ' profile not found, creating new database entry...')
                new_profile = True
                playerstats = legion_api.getstats(playerid)
                try:
                    wins = playerstats['rankedWinsThisSeason']
                except KeyError:
                    wins = 0
                try:
                    losses = playerstats['rankedLossesThisSeason']
                except KeyError:
                    losses = 0
                playerprofile = legion_api.getprofile(playerid)
                try:
                    ladder_points = playerstats["ladderPoints"]
                except KeyError:
                    ladder_points = 0
                PlayerProfile(
                    player_id=playerid,
                    player_name=playerprofile["playerName"],
                    total_games_played=playerstats["gamesPlayed"],
                    ranked_wins_current_season=wins,
                    ranked_losses_current_season=losses,
                    ladder_points=ladder_points,
                    offset=0,
                    last_updated=datetime.now(tz=timezone.utc)
                ).save()
                data = get_games_loop(playerid, 0, 300)
            else:
                new_profile = False
                playerstats = legion_api.getstats(playerid)
                data = PlayerProfile.select().where(PlayerProfile.player_id == playerid).get()
                ranked_games_old = data.ranked_wins_current_season+data.ranked_losses_current_season
                try:
                    wins = playerstats['rankedWinsThisSeason']
                except KeyError:
                    wins = 0
                try:
                    losses = playerstats['rankedLossesThisSeason']
                except KeyError:
                    losses = 0
                try:
                    ladder_points = playerstats["ladderPoints"]
                except KeyError:
                    ladder_points = 0
                PlayerProfile.update(
                    ladder_points = ladder_points,
                    ranked_wins_current_season=wins,
                    ranked_losses_current_season=losses,
                    last_updated=datetime.now()
                ).where(PlayerProfile.player_id == playerid).execute()
                ranked_games = wins + losses
                games_diff = ranked_games - ranked_games_old
                if ranked_games_old < ranked_games:
                    games_count += get_games_loop(playerid, 0, games_diff)
                games_count_db = PlayerData.select().where(PlayerData.player_id == playerid).count()
                if games_count_db < games2:
                    games_count += get_games_loop(playerid, data.offset, games2-games_count_db, timeout_limit=5)
                if games_count > 0:
                    PlayerProfile.update(offset=games_count+data.offset).where(PlayerProfile.player_id == playerid).execute()
        if update == 0:
            raw_data = []
            if patch in ["12", "11", "10"]:
                expr = GameData.version.startswith("v"+patch)
            elif patch != "0":
                if len(patch_list) == 1:
                    expr = fn.Substr(GameData.version, 2, len(patch_list[0])).in_(patch_list)
                else:
                    expr = fn.Substr(GameData.version, 2, 5).in_(patch_list)
            else:
                expr = True
            game_data_query = (PlayerData
                         .select(*req_columns[0])
                         .join(GameData)
                         .where((GameData.queue == "Normal") & GameData.player_ids.contains(playerid) & (GameData.game_elo >= min_elo) & expr & (GameData.ending_wave >= earliest_wave))
                         .order_by(sort_arg.desc(), GameData.id.desc(), PlayerData.player_slot)
                         .limit(games2*4)).dicts()
            for i, row in enumerate(game_data_query.iterator()):
                p_data = {}
                for field in req_columns[2]:
                    p_data[field] = row[field]
                if i % 4 == 0:
                    temp_data = {}
                    for field in req_columns[1]:
                        temp_data[field] = row[field]
                    temp_data["players_data"] = [p_data]
                else:
                    try:
                        temp_data["players_data"].append(p_data)
                    except Exception:
                        pass
                if i % 4 == 3:
                    try:
                        if len(temp_data["players_data"]) == 4:
                            temp_data["players_data"] = sorted(temp_data["players_data"], key=lambda x: x['player_slot'])
                            raw_data.append(temp_data)
                            temp_data = {}
                    except KeyError:
                        temp_data = {}
    else:
        raw_data = []
        if patch in ["13", "12", "11", "10"]:
            expr = GameData.version.startswith("v" + patch)
        elif patch != "0":
            if len(patch_list) == 1:
                expr = fn.Substr(GameData.version, 2, len(patch_list[0])).in_(patch_list)
            else:
                expr = fn.Substr(GameData.version, 2, 5).in_(patch_list)
        else:
            expr = True
        games_limit = 200000
        game_data_query = (PlayerData
                           .select(*req_columns[0])
                           .join(GameData)
                           .where((GameData.queue == "Normal") & expr & ((GameData.game_elo >= min_elo) & (GameData.game_elo <= max_elo)) & (GameData.ending_wave >= earliest_wave))
                           .order_by(sort_arg.desc(), GameData.id.desc(), PlayerData.player_slot)
                           .limit(games_limit * 4)).dicts()
        for i, row in enumerate(game_data_query.iterator()):
            p_data = {}
            for field in req_columns[2]:
                p_data[field] = row[field]
            if i % 4 == 0:
                temp_data = {}
                for field in req_columns[1]:
                    temp_data[field] = row[field]
                temp_data["players_data"] = [p_data]
            else:
                try:
                    temp_data["players_data"].append(p_data)
                except Exception:
                    pass
            if i % 4 == 3:
                try:
                    if len(temp_data["players_data"]) == 4:
                        temp_data["players_data"] = sorted(temp_data["players_data"], key=lambda x: x['player_slot'])
                        raw_data.append(temp_data)
                        temp_data = {}
                except KeyError:
                    temp_data = {}
    if update == 0:
        return raw_data
    else:
        if new_profile:
            return data
        else:
            return games_diff
        