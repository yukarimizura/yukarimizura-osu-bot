import json
import os


DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "users.json"
)


def get_empty_data():
    return {
        "linked_users": {},
        "username_history": {}
    }


def load_data():
    if not os.path.exists(DATA_FILE):
        return get_empty_data()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        return get_empty_data()


def save_data(data):
    os.makedirs(
        os.path.dirname(DATA_FILE),
        exist_ok=True
    )

    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


def link_user(discord_id, osu_user):
    data = load_data()

    data["linked_users"][str(discord_id)] = {
        "osu_id": osu_user["id"],
        "username": osu_user["username"],
        "mode": osu_user["playmode"]
    }

    save_data(data)


def get_linked_user(discord_id):
    data = load_data()

    return data["linked_users"].get(
        str(discord_id)
    )


def save_username_history(osu_user):
    data = load_data()

    osu_id = osu_user["id"]

    current_username = osu_user["username"]

    data["username_history"][
        current_username.lower()
    ] = osu_id

    for old_name in osu_user.get(
        "previous_usernames",
        []
    ):
        data["username_history"][
            old_name.lower()
        ] = osu_id

    save_data(data)


def find_osu_id_by_username(username):
    data = load_data()

    return data["username_history"].get(
        username.lower()
    )

def unlink_user(discord_id):
    data = load_data()

    discord_id = str(discord_id)

    if discord_id not in data["linked_users"]:
        return False

    del data["linked_users"][discord_id]

    save_data(data)

    return True