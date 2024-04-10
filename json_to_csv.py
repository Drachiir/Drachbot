import json
import os
import pathlib
import csv

def legion_json_to_csv():
    path1 = str(pathlib.Path(__file__).parent.resolve()) + "/Games/"
    games = sorted(os.listdir(path1))
    json_files = set()
    count = 0
    for i, x in enumerate(games):
        if x.split("_")[1].startswith("v11"):
            path2 = str(pathlib.Path(__file__).parent.resolve()) + "/Games/" + x
            json_files.add(path2)
    csv_legend = ["match_id","match_date","ending_wave","version","duration","average_elo","spell_choices","player_id","player_name","mastermind","result","player_elo","elo_change","fighters","legion_spell","legion_spell_unit","opener","party_size","megamind"]
    csv_file_name = "/shared/Drachbot_data.csv"
    try:
        os.remove(csv_file_name)
    except Exception: pass
    with open(csv_file_name, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(csv_legend)
    for x in json_files:
        with open(x) as f:
            game = json.load(f)
            f.close()
            for player in game["playersData"]:
                with open (csv_file_name, "a", newline="", encoding="utf-8") as csvfile:
                    writer = csv.writer(csvfile, delimiter=",",quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    try:
                        megamind = player["megamind"]
                    except KeyError:
                        megamind = "N/A"
                    unit_found = False
                    spell_unit = ""
                    if player["chosenSpellLocation"] != "-1|-1":
                        for wave in player["buildPerWave"]:
                            if unit_found == True:
                                break
                            for unit in wave:
                                unit_name = unit.split('_unit_id:')[0].replace('_', ' ')
                                if unit.split(':')[1] == player["chosenSpellLocation"] and 'grarl' not in unit and 'pirate' not in unit:
                                    unit_found = True
                                    spell_unit = unit_name
                    else:
                        spell_unit = "N/A"
                    writer.writerow([game["_id"],game["date"],game["endingWave"],game["version"],game["gameLength"],game["gameElo"],game["spellChoices"],
                                    player["playerId"],player["playerName"],player["legion"],player["gameResult"],player["overallElo"],
                                    player["eloChange"],player["fighters"],player["chosenSpell"],spell_unit,player["firstWaveFighters"],player["partySize"], megamind])
        count += 1
        print(str(count) + " out of " + str(len(json_files)) + " parsed")
    return "https://overlay.drachbot.site/Drachbot_data.csv"
