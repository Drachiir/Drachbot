import platform
import traceback
import json
import os

import drachbot_db
import legion_api
import jinja2
from jinja2 import Environment, FileSystemLoader

import util
from peewee_pg import GameData, PlayerData

if platform.system() == "Linux":
    shared_folder = "/shared/"
else:
    shared_folder = "shared/"

def stream_overlay(playerid, update = False, stream_started_at="", elo_change=0):
    try:
        if not os.path.isfile("sessions/session_" + playerid + ".json"):
            leaderboard = legion_api.get_leaderboard(99)
            for i, player in enumerate(leaderboard):
                if player["profile"][0]["_id"] == playerid:
                    initial_rank = "#"+str(i+1)
                    current_rank = "#"+str(i + 1)
                    initial_elo = player["overallElo"]
                    current_elo = player["overallElo"]
                    initial_wins = player["rankedWinsThisSeason"]
                    current_wins = player["rankedWinsThisSeason"]
                    initial_losses = player["rankedLossesThisSeason"]
                    current_losses = player["rankedLossesThisSeason"]
                    break
            else:
                initial_rank = ""
                current_rank = ""
                stats = legion_api.getstats(playerid)
                initial_elo = stats["overallElo"]
                current_elo = stats["overallElo"]
                try:
                    initial_wins = stats["rankedWinsThisSeason"]
                    current_wins = stats["rankedWinsThisSeason"]
                except Exception:
                    initial_wins = 0
                    current_wins = 0
                try:
                    initial_losses = stats["rankedLossesThisSeason"]
                    current_losses = stats["rankedLossesThisSeason"]
                except Exception:
                    initial_losses = 0
                    current_losses = 0
            live = False
            with open("sessions/session_" + playerid + ".json", "w") as f:
                session_dict = {"started_at": stream_started_at, "int_rank": initial_rank, "current_rank": current_rank,
                                "int_elo": initial_elo, "current_elo": current_elo, "int_wins": initial_wins, "current_wins": current_wins,
                                "int_losses": initial_losses, "current_losses": current_losses, "live": live,
                                "avg_leak": 0, "avg_worker10": 0, "history": []}
                json.dump(session_dict, f, default=str)
        else:
            with open("sessions/session_" + playerid + ".json", "r") as f:
                session_dict = json.load(f)
                if not session_dict.get("history"):
                    session_dict["history"] = []
                live = session_dict["live"]
                initial_elo = session_dict["int_elo"]
                initial_wins = session_dict["int_wins"]
                initial_losses = session_dict["int_losses"]
                initial_rank = session_dict["int_rank"]
                current_rank = session_dict["current_rank"]
                if update:
                    leaderboard = legion_api.get_leaderboard(99)
                    for i, player in enumerate(leaderboard):
                        if player["profile"][0]["_id"] == playerid:
                            current_rank = "#" + str(i + 1)
                            break
                    else:
                        current_rank = ""
                    stats = legion_api.getstats(playerid)
                    current_elo = stats["overallElo"]
                    try:
                        current_wins = stats["rankedWinsThisSeason"]
                    except Exception:
                        current_wins = 0
                    try:
                        current_losses = stats["rankedLossesThisSeason"]
                    except Exception:
                        current_losses = 0
                else:
                    current_elo = session_dict["current_elo"] + elo_change
                    if elo_change > 0:
                        current_wins = session_dict["current_wins"] + 1
                    else:
                        current_wins = session_dict["current_wins"]
                    if elo_change < 0:
                        current_losses = session_dict["current_losses"] + 1
                    else:
                        current_losses = session_dict["current_losses"]
            if live:
                initial_games = initial_wins + initial_losses
                current_games = current_wins + current_losses
                games = current_games-initial_games
                if update and games > 0:
                    req_columns = [[GameData.game_id, GameData.queue, GameData.date, GameData.version, GameData.ending_wave, GameData.game_elo, GameData.player_ids,
                                    PlayerData.player_id, PlayerData.player_slot, PlayerData.game_result, PlayerData.legion, PlayerData.megamind, PlayerData.elo_change,
                                    PlayerData.leaks_per_wave, PlayerData.workers_per_wave],
                                   ["game_id", "date", "version", "ending_wave", "game_elo"],
                                   ["player_id", "player_slot", "game_result", "legion", "megamind", "elo_change", "leaks_per_wave", "workers_per_wave"]]
                    history = drachbot_db.get_matchistory(playerid, games, req_columns=req_columns, earlier_than_wave10=True, include_wave_one_finishes=True)
                else:
                    history = session_dict["history"]
                with open("sessions/session_" + playerid + ".json", "w") as f:
                    session_dict = {"started_at": session_dict["started_at"], "int_rank": initial_rank, "current_rank": current_rank, "int_elo": initial_elo, "current_elo": current_elo,
                                    "int_wins": initial_wins, "current_wins": current_wins, "int_losses": initial_losses, "current_losses": current_losses, "live": live,
                                    "avg_leak": session_dict["avg_leak"], "avg_worker10": session_dict["avg_worker10"], "history": history}
                    json.dump(session_dict, f, default=str)
    except Exception:
        traceback.print_exc()
        print(f"Couldn't create session for: {playerid}")
        return None
    wins = current_wins-initial_wins
    losses = current_losses-initial_losses
    try:
        winrate = round(wins/(wins+losses)*100)
    except ZeroDivisionError:
        winrate = 0
    if winrate < 50:
        rgb = 'class="redText"'
    else:
        rgb = 'class="greenText"'
    elo_diff = current_elo-initial_elo
    if elo_diff >= 0:
        elo_str = "+"
        rgb2 = 'class="greenText"'
    else:
        elo_str = ""
        rgb2 = 'class="redText"'
    simple = "Simple/"
    def get_rank_url(elo):
        if elo >= 2800:
            rank_url = f'https://cdn.legiontd2.com/icons/Ranks/{simple}Legend.png'
        elif elo >= 2600:
            rank_url = f'https://cdn.legiontd2.com/icons/Ranks/{simple}GrandMaster.png'
        elif elo >= 2400:
            rank_url = f'https://cdn.legiontd2.com/icons/Ranks/{simple}SeniorMaster.png'
        elif elo >= 2200:
            rank_url = f'https://cdn.legiontd2.com/icons/Ranks/{simple}Master.png'
        elif elo >= 2000:
            rank_url = f'https://cdn.legiontd2.com/icons/Ranks/{simple}Expert.png'
        elif elo >= 1800:
            rank_url = f'https://cdn.legiontd2.com/icons/Ranks/{simple}Diamond.png'
        elif elo >= 1600:
            rank_url = f'https://cdn.legiontd2.com/icons/Ranks/{simple}Platinum.png'
        elif elo >= 1400:
            rank_url = f'https://cdn.legiontd2.com/icons/Ranks/{simple}Gold.png'
        elif elo >= 1200:
            rank_url = f'https://cdn.legiontd2.com/icons/Ranks/{simple}Silver.png'
        else:
            rank_url = f'https://cdn.legiontd2.com/icons/Ranks/{simple}Bronze.png'
        return rank_url
    rank_url_int = get_rank_url(initial_elo)
    rank_url_current = get_rank_url(current_elo)
    enviorment = jinja2.Environment(loader=FileSystemLoader("templates/"))
    template = enviorment.get_template("streamoverlay.html")
    html_file = template.render(rank_url_int=rank_url_int, rank_url_current=rank_url_current,
                                initial_elo=initial_elo, initial_rank=initial_rank, current_rank=current_rank,
                                wins=wins, losses=losses, current_elo=current_elo, winrate=winrate,
                                elo_diff=elo_diff, elo_str=elo_str, rgb=rgb, rgb2=rgb2, playerid=playerid, history=session_dict["history"])
    with open(shared_folder+playerid+'_output.html', "w") as f:
        f.write(html_file)

    template2 = enviorment.get_template("miscstatsoverlay.html")
    leak = 0
    worker10 = 0
    waves = 0
    for game in session_dict["history"]:
        for player in game["players_data"]:
            if player["player_id"] == playerid:
                for i, wave in enumerate(player["leaks_per_wave"]):
                    leak += util.calc_leak(wave, i)
                    waves += 1
                try:
                    worker10 += player["workers_per_wave"][9]
                except Exception:
                    pass
    try:
        avg_leak = round(leak / waves, 1)
        avg_worker10 = round(worker10 / len(session_dict["history"]), 1)
    except Exception:
        avg_leak = 0
        avg_worker10 = 0

    if not session_dict.get("avg_leak", 0) == 0:
        leak_delta = round(avg_leak - session_dict.get("avg_leak", 0), 1)
        worker_delta = round(avg_worker10 - session_dict.get("avg_worker10", 0), 1)
    else:
        leak_delta = 0
        worker_delta = 0
    session_dict["avg_leak"] = avg_leak
    session_dict["avg_worker10"] = avg_worker10
    with open("sessions/session_" + playerid + ".json", "w") as f:
        json.dump(session_dict, f, default=str)

    html_file2 = template2.render(playerid=playerid, avg_leak = avg_leak, avg_worker10 = avg_worker10, leak_delta = leak_delta, worker_delta = worker_delta)
    with open(shared_folder+playerid+'_output2.html', "w") as f:
        f.write(html_file2)

    return playerid+'_output.html'