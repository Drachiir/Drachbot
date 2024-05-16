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
from peewee_pg import PlayerProfile, GameData, PlayerData
from playhouse.postgres_ext import *
import datetime
from datetime import datetime, timezone

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

def get_games_loop(playerid, offset, expected, timeout_limit = 1):
    print("Starting get_games_loop, expecting " + str(expected) + " games.")
    data = legion_api.pullgamedata(playerid, offset, expected)
    count = data[0]
    games_count = data[1]
    timeout = 0
    while count < expected:
        if timeout == timeout_limit:
            print('Timeout while pulling games.')
            break
        offset += 50
        data = legion_api.pullgamedata(playerid, offset, expected)
        if data[0] == 0:
            timeout += 1
        count += data[0]
        games_count += data[1]
    else:
        print('All '+str(expected)+' required games pulled.')
    return games_count

def get_matchistory(playerid, games, min_elo=0, patch='0', update = 0, earlier_than_wave10 = False, sort_by = "date"):
    patch_list = []
    if earlier_than_wave10:
        earliest_wave = 4
    else:
        earliest_wave = 11
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
            games2 = GameData.select().where(GameData.player_ids.contains(playerid)).count()
        else:
            games2 = games
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
            if Path(Path("Profiles/"+ playerid + "/")).is_dir():
                with open("Profiles/"+ playerid + "/gamecount_"+playerid+".txt") as f:
                    txt = f.readlines()
                    offset = int(txt[1].replace("\n", ""))
            else:
                offset = 0
            PlayerProfile(
                player_id=playerid,
                player_name=playerprofile["playerName"],
                total_games_played=playerstats["gamesPlayed"],
                ranked_wins_current_season=wins,
                ranked_losses_current_season=losses,
                ladder_points=playerstats["ladderPoints"],
                offset=offset,
                last_updated=datetime.now(tz=timezone.utc)
            ).save()
            games_count_db = GameData.select().where(GameData.player_ids.contains(playerid) & GameData.version.startswith("v11")).count()
            if games_count_db < wins+losses:
                data = get_games_loop(playerid, 0, wins+losses-games_count_db)
            else:
                data = 0
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
            PlayerProfile.update(
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
                games_count += get_games_loop(playerid, data.offset, games2-games_count_db)
            if games_count > 0:
                PlayerProfile.update(offset=games_count+data.offset).where(PlayerProfile.player_id == playerid).execute()
        if update == 0:
            raw_data = []
            if sort_by == "date":
                sort_arg = GameData.date
            else:
                sort_arg = GameData.game_elo
            if patch == "11" or patch == "10":
                expr = GameData.version.startswith("v"+patch)
            elif patch != "0":
                expr = fn.Substr(GameData.version, 2, 5).in_(patch_list)
            else:
                expr = True
            game_data = PlayerData.select(GameData, PlayerData).join(
                GameData).where(GameData.player_ids.contains(playerid) & (GameData.game_elo >= min_elo) & expr & (GameData.ending_wave >= earliest_wave)).order_by(sort_arg.desc()).limit(games2*4)
            keys = ["mercenariesSentPerWave", "mercenariesReceivedPerWave", "leaksPerWave", "buildPerWave", "kingUpgradesPerWave", "opponentKingUpgradesPerWave"]
            def convert_data(player):
                for key in keys:
                    for i, wave in enumerate(player[key]):
                        if len(wave) == 0:
                            player[key][i] = []
                        else:
                            player[key][i] = wave.split(":")
                return player
            for i, game in enumerate(game_data):
                if game.game_result != "won" and game.game_result != "lost":
                    continue
                p_data = {
                    "playerId": game.player_id,
                    "playerName": game.player_name,
                    "legion": game.legion,
                    "gameResult": game.game_result,
                    "eloChange": game.elo_change,
                    "workers": game.workers,
                    "overallElo": game.player_elo,
                    "fighters": game.fighters,
                    "chosenSpell": game.spell,
                    "chosenSpellLocation": game.spell_location,
                    "partySize": game.party_size,
                    "firstWaveFighters": game.opener,
                    "rolls": game.roll,
                    "partyMembers": game.party_members,
                    "partyMembersIds": game.party_members_ids,
                    "mvpScore": game.mvp_score,
                    "netWorthPerWave": game.net_worth_per_wave,
                    "valuePerWave": game.fighter_value_per_wave,
                    "workersPerWave": game.workers_per_wave,
                    "incomePerWave": game.income_per_wave,
                    "mercenariesSentPerWave": game.mercs_sent_per_wave,
                    "mercenariesReceivedPerWave": game.mercs_received_per_wave,
                    "leaksPerWave": game.leaks_per_wave,
                    "buildPerWave": game.build_per_wave,
                    "leakValue": game.leak_value,
                    "leaksCaughtValue": game.leaks_caught_value,
                    "kingUpgradesPerWave": game.kingups_sent_per_wave,
                    "opponentKingUpgradesPerWave": game.kingups_received_per_wave,
                    "megamind": game.megamind,
                    "chosenChampionLocation": game.champ_location
                }
                p_data = convert_data(p_data)
                if i % 4 == 0:
                    temp_data = {
                        "_id": game.game_id.game_id,
                        "date": game.game_id.date,
                        "version": game.game_id.version,
                        "endingWave": game.game_id.ending_wave,
                        "gameElo": game.game_id.game_elo,
                        "leftKingPercentHp": game.game_id.left_king_hp,
                        "rightKingPercentHp": game.game_id.right_king_hp,
                        "playersData": [p_data]
                    }
                else:
                    try:
                        temp_data["playersData"].append(p_data)
                    except Exception:
                        pass
                if i % 4 == 3:
                    try:
                        if len(temp_data["playersData"]) == 4:
                            raw_data.append(temp_data)
                            temp_data = {}
                        else:
                            temp_data = {}
                    except KeyError:
                        temp_data = {}
                        
    elif 'nova cup' in playerid:
        patch = "0"
        if min_elo == util.current_minelo:
            min_elo = 0
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
    else:
        raw_data = []
        if sort_by == "date":
            sort_arg = GameData.date
        else:
            sort_arg = GameData.game_elo
        if patch == "11" or patch == "10":
            expr = GameData.version.startswith("v" + patch)
            if games == 0:
                games = GameData.select().where((GameData.version.startswith("v" + patch)) & (GameData.game_elo >= min_elo)).count()
        elif patch != "0":
            expr = fn.Substr(GameData.version, 2, 5).in_(patch_list)
            if games == 0:
                games = GameData.select().where(expr & (GameData.game_elo >= min_elo)).count()
        else:
            if games == 0:
                games = GameData.select().where(GameData.game_elo >= min_elo).count()
            expr = True
        game_data = PlayerData.select(GameData, PlayerData).join(
            GameData).where(expr & (GameData.game_elo >= min_elo) & (GameData.ending_wave >= earliest_wave)).order_by(sort_arg.desc()).limit(games * 4)
        keys = ["mercenariesSentPerWave", "mercenariesReceivedPerWave", "leaksPerWave", "buildPerWave", "kingUpgradesPerWave", "opponentKingUpgradesPerWave"]
        def convert_data(player):
            for key in keys:
                for i, wave in enumerate(player[key]):
                    if len(wave) == 0:
                        player[key][i] = []
                    else:
                        player[key][i] = wave.split(":")
            return player
        for i, game in enumerate(game_data):
            if game.game_result != "won" and game.game_result != "lost":
                continue
            p_data = {
                "playerId": game.player_id,
                "playerName": game.player_name,
                "legion": game.legion,
                "gameResult": game.game_result,
                "eloChange": game.elo_change,
                "workers": game.workers,
                "overallElo": game.player_elo,
                "fighters": game.fighters,
                "chosenSpell": game.spell,
                "chosenSpellLocation": game.spell_location,
                "partySize": game.party_size,
                "firstWaveFighters": game.opener,
                "rolls": game.roll,
                "partyMembers": game.party_members,
                "partyMembersIds": game.party_members_ids,
                "mvpScore": game.mvp_score,
                "netWorthPerWave": game.net_worth_per_wave,
                "valuePerWave": game.fighter_value_per_wave,
                "workersPerWave": game.workers_per_wave,
                "incomePerWave": game.income_per_wave,
                "mercenariesSentPerWave": game.mercs_sent_per_wave,
                "mercenariesReceivedPerWave": game.mercs_received_per_wave,
                "leaksPerWave": game.leaks_per_wave,
                "buildPerWave": game.build_per_wave,
                "leakValue": game.leak_value,
                "leaksCaughtValue": game.leaks_caught_value,
                "kingUpgradesPerWave": game.kingups_sent_per_wave,
                "opponentKingUpgradesPerWave": game.kingups_received_per_wave,
                "megamind": game.megamind,
                "chosenChampionLocation": game.champ_location
            }
            p_data = convert_data(p_data)
            if i % 4 == 0:
                temp_data = {
                    "_id": game.game_id.game_id,
                    "date": game.game_id.date,
                    "version": game.game_id.version,
                    "endingWave": game.game_id.ending_wave,
                    "gameElo": game.game_id.game_elo,
                    "leftKingPercentHp": game.game_id.left_king_hp,
                    "rightKingPercentHp": game.game_id.right_king_hp,
                    "playersData": [p_data]
                }
            else:
                try:
                    temp_data["playersData"].append(p_data)
                except Exception:
                    pass
            if i % 4 == 3:
                try:
                    if len(temp_data["playersData"]) == 4:
                        raw_data.append(temp_data)
                        temp_data = {}
                    else:
                        temp_data = {}
                except KeyError:
                    temp_data = {}
    if update == 0:
        print(len(raw_data))
        return raw_data
    else:
        if new_profile:
            return data
        else:
            return games_diff
        