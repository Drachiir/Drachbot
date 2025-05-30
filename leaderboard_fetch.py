import os
import json
import requests
from datetime import datetime

calls = 200
today = datetime.today()
date = today.strftime("%y-%m-%d")

with open('Files/json/Secrets.json', 'r') as f:
    secret_file = json.load(f)
    f.close()

header = {'x-api-key': secret_file.get('apikey')}

leaderboard_dir = f"/shared2/leaderboard/data/leaderboard_{date}"
parsed_dir = "/shared2/leaderboard"
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
    
# Step to delete raw data files
for file in os.listdir(leaderboard_dir):
    file_path = os.path.join(leaderboard_dir, file)
    try:
        os.remove(file_path)
    except Exception as e:
        print(f"Error deleting {file_path}: {e}")
