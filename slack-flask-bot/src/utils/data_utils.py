import json

USERS_FILE = "data/users.json"

def get_user_data():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_user_data(data):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)