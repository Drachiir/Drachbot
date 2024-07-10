import json
import os
import datetime
import time
import traceback
from datetime import datetime, timedelta, timezone
from peewee import *
import platform
from playhouse.postgres_ext import *
from playhouse.pool import PooledPostgresqlExtDatabase
import requests
import time

if platform.system().lower() == "windows":
    games_folder = "Games/"
else:
    games_folder = "/shared/"

with open("Files/json/Secrets.json", "r") as f:
    secret_file = json.load(f)
    f.close()


db = PooledPostgresqlExtDatabase(
    "postgres",
    max_connections=10,
    stale_timeout=300,
    server_side_cursors=True,
    user=secret_file["pg_user"],
    password=secret_file["pg_password"],
    host=secret_file["pg_host"],
    port="5432"
)


class BaseModel(Model):
    class Meta:
        database = db


class PlayerProfile(BaseModel):
    id = AutoField()
    player_id = TextField(unique=True)
    player_name = TextField(unique=True)
    total_games_played = IntegerField()
    ranked_wins_current_season = IntegerField()
    ranked_losses_current_season = IntegerField()
    ladder_points = IntegerField()
    offset = IntegerField()
    last_updated = DateTimeField()


class GameData(BaseModel):
    id = AutoField()
    game_id = TextField(unique=True)  # "_id"
    queue = TextField(index=True)
    version = TextField(index=True)
    date = DateTimeField(index=True)
    ending_wave = IntegerField()  # "endingWave"
    game_length = IntegerField()  # "gameLength"
    game_elo = IntegerField(index=True)  # "gameElo"
    player_count = IntegerField()  # "playerCount"
    spell_choices = ArrayField(field_class=TextField, index=False)  # "spellChoices"
    left_king_hp = ArrayField(field_class=FloatField, index=False)  # "leftKingPercentHp"
    right_king_hp = ArrayField(field_class=FloatField, index=False)  # "rightKingPercentHp"
    player_ids = ArrayField(field_class=TextField, index=True)  # playersData[playerId]


class PlayerData(BaseModel):
    id = AutoField()
    game_id = ForeignKeyField(GameData, field="game_id")
    player_id = TextField()  # "playerID"
    player_name = TextField()  # "playerName"
    player_slot = IntegerField()  # "playerSlot"
    legion = TextField()
    workers = FloatField()
    fighter_value = IntegerField()  # "value"
    game_result = TextField()  # "gameResult"
    player_elo = IntegerField()  # "overallElo"
    elo_change = IntegerField()  # "eloChange"
    fighters = TextField()
    spell = TextField()  # "chosenSpell"
    spell_location = TextField()  # "chosenSpellLocation"
    party_size = IntegerField()
    opener = TextField()  # "firstWaveFighters"
    roll = TextField()  # "rolls"
    party_members = ArrayField(field_class=TextField, index=False)  # "partyMembers"
    party_members_ids = ArrayField(field_class=TextField, index=False)  # "partyMembersIds"
    mvp_score = IntegerField()  # "mvpScore"
    net_worth_per_wave = ArrayField(field_class=IntegerField, index=False)  # "netWorthPerWave"
    fighter_value_per_wave = ArrayField(field_class=IntegerField, index=False)  # "valuePerWave"
    workers_per_wave = ArrayField(field_class=FloatField, index=False)  # "workersPerWave"
    income_per_wave = ArrayField(field_class=IntegerField, index=False)  # "incomePerWave"
    mercs_sent_per_wave = ArrayField(field_class=TextField, index=False)  # "mercenariesSentPerWave"
    mercs_received_per_wave = ArrayField(field_class=TextField, index=False)  # "mercenariesReceivedPerWave"
    leaks_per_wave = ArrayField(field_class=TextField, index=False)  # "leaksPerWave"
    build_per_wave = ArrayField(field_class=TextField, index=False)  # "buildPerWave"
    leak_value = IntegerField()  # "leakValue"
    leaks_caught_value = IntegerField()  # "leaksCaughtValue"
    kingups_sent_per_wave = ArrayField(field_class=TextField, index=False)  # "kingUpgradesPerWave"
    kingups_received_per_wave = ArrayField(field_class=TextField, index=False)  # "opponentKingUpgradesPerWave"
    megamind = BooleanField()
    champ_location = TextField()  # "chosenChampionLocation"


def save_game(data):
    date_format = "%Y-%m-%dT%H:%M:%S"
    pids = []
    for player in data["playersData"]:
        pids.append(player["playerId"])
    if len(pids) != 4:
        if len(pids) != 0:
            print("Odd number of pids for game" + data["_id"])
        else:
            print("Less than 4 player ids for game " + data["_id"])
        return
    if GameData.get_or_none(GameData.game_id == data["_id"]) is None:
        game_data = GameData(
            game_id=data["_id"],
            queue=data["queueType"],
            version=data["version"],
            date=datetime.strptime(data["date"].split(".")[0], date_format),
            ending_wave=data["endingWave"],
            game_length=data["gameLength"],
            game_elo=data["gameElo"],
            player_count=data["playerCount"],
            spell_choices=data["spellChoices"],
            left_king_hp=data["leftKingPercentHp"],
            right_king_hp=data["rightKingPercentHp"],
            player_ids=pids
        )
        game_data.save()
        for player in data["playersData"]:
            try:
                megamind = player["megamind"]
                champ_location = player["chosenChampionLocation"]
            except Exception:
                megamind = False
                champ_location = "N/A"
            
            def convert_data(keys):
                for key in keys:
                    new_list = []
                    for i, wave in enumerate(player[key]):
                        if len(wave) == 0:
                            new_list.append("")
                        else:
                            new_list.append("!".join(wave))
                    player[key] = new_list
            try:
                convert_data(["mercenariesSentPerWave", "mercenariesReceivedPerWave", "leaksPerWave", "buildPerWave", "kingUpgradesPerWave", "opponentKingUpgradesPerWave"])
                if player["gameResult"] is None:
                    player["gameResult"] = "Tied"
                player_data = PlayerData(
                    game_id=data["_id"],
                    player_id=player["playerId"],
                    player_name=player["playerName"],
                    player_slot=player["playerSlot"],
                    legion=player["legion"],
                    workers=player["workers"],
                    fighter_value=player["value"],
                    game_result=player["gameResult"],
                    player_elo=player["overallElo"],
                    elo_change=player["eloChange"],
                    fighters=player["fighters"],
                    spell=player["chosenSpell"],
                    spell_location=player["chosenSpellLocation"],
                    party_size=player["partySize"],
                    opener=player["firstWaveFighters"],
                    roll=player["rolls"],
                    party_members=player["partyMembers"],
                    party_members_ids=player["partyMembersIds"],
                    mvp_score=player["mvpScore"],
                    net_worth_per_wave=player["netWorthPerWave"],
                    fighter_value_per_wave=player["valuePerWave"],
                    workers_per_wave=player["workersPerWave"],
                    income_per_wave=player["incomePerWave"],
                    mercs_sent_per_wave=player["mercenariesSentPerWave"],
                    mercs_received_per_wave=player["mercenariesReceivedPerWave"],
                    leaks_per_wave=player["leaksPerWave"],
                    build_per_wave=player["buildPerWave"],
                    leak_value=player["leakValue"],
                    leaks_caught_value=player["leaksCaughtValue"],
                    kingups_sent_per_wave=player["kingUpgradesPerWave"],
                    kingups_received_per_wave=player["opponentKingUpgradesPerWave"],
                    megamind=megamind,
                    champ_location=champ_location
                )
                player_data.save()
            except Exception:
                traceback.print_exc()

# def main():
#     file_list = os.listdir(games_folder)
#     for index, game in enumerate(file_list):
#         with open(games_folder+game, "r") as f:
#             data = json.load(f)
#             f.close()
#         save_game(data)
#         print(f"{index + 1} out of {len(file_list)}")
#
# def drop_tables():
#     db.drop_tables([PlayerProfile, GameData, PlayerData])
#     db.create_tables([PlayerProfile, GameData, PlayerData])
#
# if __name__ == '__main__':
#     main()
#     quit()