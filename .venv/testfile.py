import json

def read_player_words_from_package_json(filepath="package.json"):
    with open(filepath, "r") as f:
        return json.load(f)



