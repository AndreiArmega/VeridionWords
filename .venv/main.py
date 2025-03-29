import requests
from time import sleep
import random
from testfile import read_player_words_from_package_json

host = "http://172.18.4.158:8000"
post_url = f"{host}/submit-word"
get_url = f"{host}/get-word"
status_url = f"{host}/status"

NUM_ROUNDS = 5
LOSS = 30
abstract = ["Disease", "Cure", "Shadow", "Light", "Virus", "Sound", "Time", "Fate", "Logic", "Karma", "Peace", "War",
            "Enlightenment",
            "Anti-matter", "Rebirth", "Human Spirit", "Entropy"]

player_words = read_player_words_from_package_json()

blacklist = ["Stone", "Feather", "Bacteria", "Vaccine", "Echo", "Wind", "Sandstorm", "Enlightenment", "Whale", "Moon",
             "Tsunami", "Plague",
             "Tectonic Shift", "Apocalyptic Meteor", "Earth’s Core", "Entropy", ]

lowercase_blacklist = [word.lower() for word in blacklist]

player_words = {
    key: value
    for key, value in player_words.items()
    if value['text'].lower() not in lowercase_blacklist
}
print(player_words)

word_value_dict = {
    word_id: {"word": word_data["text"], "value": word_data["cost"]}
    for word_id, word_data in player_words.items()
}

values = [item["value"] for item in word_value_dict.values()]
mean_value = sum(values) / len(values) if values else 0
print("mean value:", mean_value)

enemy_words = []
enemy_word_values = []
mean_enemy_word_value = 0
persistent_answer = mean_value

used_words = set()  # Set to track used words


def what_beats(word, status):
    global enemy_words, enemy_word_values, mean_enemy_word_value, persistent_answer, used_words

    if status:
        round_num = status.get('round', 1)
        p1_total_cost = status.get('p1_total_cost', 0)
        p2_total_cost = status.get('p2_total_cost', 0)
        p1_word = status.get('p1_word', "")

        p2_word = status.get('p2_word', "")
        sum_to_victory = p1_total_cost - p2_total_cost

        enemy_word_cost = next(
            (item["value"] for item in word_value_dict.values() if item["word"] == p2_word),
            None
        )
        if enemy_word_cost is not None:
            enemy_word_values.append(enemy_word_cost)

        if enemy_word_values:
            mean_enemy_word_value = sum(enemy_word_values) / len(enemy_word_values)

        if round_num == 1:
            persistent_answer = 21
            best_match_id = min(word_value_dict.keys(), key=lambda wid: abs(word_value_dict[wid]["value"] - 21))
        elif round_num == 2:
            persistent_answer = mean_value
            best_match_id = min(word_value_dict.keys(), key=lambda wid: abs(word_value_dict[wid]["value"] - mean_value))
        else:
            if sum_to_victory > 0 and round_num < NUM_ROUNDS:
                persistent_answer -= sum_to_victory / (NUM_ROUNDS - round_num)
            else:
                persistent_answer += -sum_to_victory - (-round_num + (NUM_ROUNDS + 1))

            non_abstract_values = [
                item["value"] for item in word_value_dict.values()
                if item["word"] not in abstract
            ]

            if non_abstract_values:
                min_non_abstract = min(non_abstract_values)
            else:
                min_non_abstract = mean_value * 0.5

            dynamic_lower_bound = max(mean_enemy_word_value * 0.6, min_non_abstract)

            persistent_answer = max(dynamic_lower_bound, int(persistent_answer))

    available_word_ids = [wid for wid in word_value_dict.keys() if word_value_dict[wid]["word"] not in used_words]

    if not available_word_ids:
        print("No available words left!")
        return None

    best_match_id = min(available_word_ids, key=lambda wid: abs(word_value_dict[wid]["value"] - persistent_answer))

    used_words.add(word_value_dict[best_match_id]["word"])

    return int(best_match_id)


def play_game(player_id):
    for round_id in range(1, NUM_ROUNDS + 1):
        round_num = -1
        while round_num != round_id:
            try:
                response = requests.get(get_url)
                response.raise_for_status()
                get_word_data = response.json()
                print(get_word_data)
                sys_word = get_word_data['word']
                round_num = get_word_data['round']
            except requests.exceptions.RequestException as e:
                print(f"Error getting word: {e}")
                sleep(2)
                continue

            sleep(1)

        stat = None
        if round_id > 1:
            try:
                status = requests.get(status_url)
                status.raise_for_status()
                stat = status.json().get('status')
            except requests.exceptions.RequestException as e:
                print(f"Error getting status: {e}")
                sleep(2)
                continue
            print(status.json())

        choosen_word = what_beats(sys_word, stat)
        if choosen_word is None:
            print("Game over, no words left to choose!")
            break

        print("chosen word:", player_words[str(choosen_word)])
        data = {"player_id": player_id, "word_id": choosen_word, "round_id": round_id}
        try:
            response = requests.post(post_url, json=data)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error submitting word: {e}")
            sleep(2)
            continue
        print(response.json())


play_game("3IoEOXE1q7")
