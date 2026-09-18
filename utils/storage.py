import os
import json
from typing import Optional, Dict, Any

JSON_PATH = "data/users.json"
TEMP_PATH = "data/users.json.tmp"

class Storage:
    def __init__(self, file_path: str = JSON_PATH):
        self.file_path = file_path
        self._data: Dict[str, Any] = {"linked_users": {}, "username_history": {}}
        self.load()

    def load(self) -> None:
        """Load user data and username history from JSON."""
        if not os.path.exists(self.file_path):
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            self._save()
            return

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    self._data = json.loads(content)
                    # Guarantee top-level keys exist
                    self._data.setdefault("linked_users", {})
                    self._data.setdefault("username_history", {})
        except Exception:
            self._data = {"linked_users": {}, "username_history": {}}

    def _save(self) -> None:
        """Atomically write data to prevent file corruption."""
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(TEMP_PATH, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=4)
        os.replace(TEMP_PATH, self.file_path)



    def get_user(self, discord_id: int) -> Optional[Dict[str, Any]]:
        """Get linked osu! account details for a Discord ID."""
        return self._data["linked_users"].get(str(discord_id))

    def set_user(self, discord_id: int, osu_id: int, username: str, mode: str = "osu") -> None:
        """Link or update a user's osu! account and record alias history."""
        self._data["linked_users"][str(discord_id)] = {
            "osu_id": osu_id,
            "username": username,
            "mode": mode
        }

        self._data["username_history"][username.lower()] = osu_id
        self._save()

    def delete_user(self, discord_id: int) -> bool:
        """Unlink a Discord user."""
        str_id = str(discord_id)
        if str_id in self._data["linked_users"]:
            del self._data["linked_users"][str_id]
            self._save()
            return True
        return False

    def get_cached_osu_id(self, username: str) -> Optional[int]:
        """Look up an osu! ID from an alias or previous username."""
        return self._data["username_history"].get(username.lower())

    def set_cached_username(self, username: str, osu_id: int) -> None:
        """Cache an osu! username and ID pair."""
        self._data["username_history"][username.lower()] = osu_id
        self._save()

# Instance exports
storage = Storage()
user_storage = storage