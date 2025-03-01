import os
import json
import requests
from legion_api import header

calls = 200
date = "13-02-25"

leaderboard_dir = f"leaderboard/leaderboard_{date}"
parsed_dir = "shared2/leaderboard"
os.makedirs(leaderboard_dir, exist_ok=True)
os.makedirs(parsed_dir, exist_ok=True)

for i in range(calls):
    url = f'https://apiv2.legiontd2.com/players/stats?limit=1000&offset={i * 1000}&sortBy=overallElo&sortDirection=-1'
    api_response = requests.get(url, headers=header)
    data = json.loads(api_response.text)

    with open(f"{leaderboard_dir}/leaderboard_data{i}.json", "w") as f:
        json.dump(data, f)

    print(f"{i + 1}/{calls}")

parsed_data = []
for file in os.listdir(leaderboard_dir):
    with open(f"{leaderboard_dir}/{file}") as f:
        data = json.load(f)

    for player in data:
        try:
            elo = player["overallElo"]
            wins = player["rankedWinsThisSeason"]
            losses = player["rankedLossesThisSeason"]
        except Exception:
            continue

        if wins + losses == 0:
            continue

        parsed_data.append([elo, wins, losses])

with open(f"{parsed_dir}/leaderboard_parsed_{date}.json", "w") as f:
    json.dump(parsed_data, f)
