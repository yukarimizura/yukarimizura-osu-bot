import json
import os
import asyncio


DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "data",
    "users.json"
)

_CACHE = {"linked_users": {}, "username_history": {}}

def init_storage():
    global _CACHE
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                _CACHE = json.load(f)
        except (json.JSONDecodeError, OSError):
            _CACHE = {"linked_users": {}, "username_history": {}}

def _write_to_disk():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(_CACHE, file, indent=4, ensure_ascii=False)

async def save_data_async():
    await asyncio.to_thread(_write_to_disk)

def link_user(discord_id, osu_user):
    _CACHE["linked_users"][str(discord_id)] = {
        "osu_id": osu_user["id"],
        "username": osu_user["username"],
        "mode": osu_user["playmode"]
    }
    asyncio.create_task(save_data_async())

def get_linked_user(discord_id):
    return _CACHE["linked_users"].get(str(discord_id))

def save_username_history(osu_user):
    current = osu_user["username"].lower()
    _CACHE["username_history"][current] = osu_user["id"]
    for old_name in osu_user.get("previous_usernames", []):
        _CACHE["username_history"][old_name.lower()] = osu_user["id"]
    asyncio.create_task(save_data_async())

def find_osu_id_by_username(username):
    return _CACHE["username_history"].get(username.lower())

def unlink(discord_id):
    discord_id = str(discord_id)
    if discord_id in _CACHE["linked_users"]:
        del _CACHE["linked_users"][discord_id]
        asyncio.create_task(save_data_async())
        return True
    return False

init_storage()