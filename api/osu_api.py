import aiohttp
import time
from api.pp_calculator import calculate_score_performance

from config import OSU_CLIENT_ID, OSU_CLIENT_SECRET

from utils import (
    save_username_history,
    find_osu_id_by_username
)
class OsuAPI:

    def __init__(self):

        self.session = None

        self.token = None

        self.token_expire = 0

    async def start(self):

        if self.session is None:

            self.session = aiohttp.ClientSession()


    async def close(self):

        if self.session:

            await self.session.close()

            self.session = None

    

    async def get_token(self):

            if self.token is not None and time.time() < self.token_expire:
                return self.token

            url = "https://osu.ppy.sh/oauth/token"

            data = {
                "client_id": int(OSU_CLIENT_ID),
                "client_secret": OSU_CLIENT_SECRET,
                "grant_type": "client_credentials",
                "scope": "public"
            }

            async with self.session.post(
                url,
                json=data
            ) as response:

                if response.status != 200:
                    error = await response.text()

                    print(
                        f"osu! authentication error: {error}"
                    )

                    return None

                result = await response.json()

                self.token = result["access_token"]

                self.token_expire = (
                    time.time()
                    + result["expires_in"]
                    - 60
                )

                return self.token

    async def _get(self, url, params=None):
        print("ENTER _GET")

        token = await self.get_token()
        print("TOKEN:", token is not None)

        if token is None:
            return None

        headers = {
            "Authorization": f"Bearer {token}"
        }

        print("BEFORE REQUEST")

        async with self.session.get(
            url,
            headers=headers,
            params=params
        ) as response:

            print("STATUS:", response.status)

            if response.status != 200:
                error = await response.text()
                print(error)
                return None

            print("RETURN JSON")
            return await response.json()


    async def get_user(self, username):

        known_osu_id = find_osu_id_by_username(
            username
        )

        if known_osu_id is not None:
            lookup_value = known_osu_id
        else:
            lookup_value = username
        
        url = (
            f"https://osu.ppy.sh/api/v2/users/"
            f"{lookup_value}"
        )

        general_user = await self._get(url)
        
        if general_user is None:
            return None

        main_mode = general_user["playmode"]
        user_id = general_user["id"]

        url = (
            f"https://osu.ppy.sh/api/v2/users/"
            f"{user_id}/{main_mode}"
        )

        user = await self._get(url)

        if user is None:
            return None

        save_username_history(user)

        return user

    async def get_recent_scores(self, user_id, mode=None, limit=5):
        params = {
            "limit": limit,
            "include_fails": 1
        }

        if mode is not None:
            params["mode"] = mode

        url = (
            f"https://osu.ppy.sh/api/v2/users/"
            f"{user_id}/scores/recent"
        )

        print("GET RECENT:", url)
        print("PARAMS:", params)


        return await self._get(
            url,
            params=params
)
        
    async def get_best_scores(
        self,
        user_id,
        mode="osu",
        limit=5
    ):
        url = (
            f"https://osu.ppy.sh/api/v2/users/"
            f"{user_id}/scores/best"
        )

        params = {
            "mode": mode,
            "limit": limit
        }

        return await self._get(
            url,
            params=params
        )

    async def get_beatmap(
        self,
        beatmap_id
    ):

        url = (
            f"https://osu.ppy.sh/api/v2/"
            f"beatmaps/{beatmap_id}"
        )

        return await self._get(url)

    async def get_trace_scores(
        self,
        user_id,
        beatmap_id,
        mode="osu"
    ):
        url = (
            f"https://osu.ppy.sh/api/v2/"
            f"beatmaps/{beatmap_id}"
            f"/scores/users/{user_id}/all"
        )

        params = {
            "mode": mode
        }

        result = await self._get(
            url,
            params=params
        )

        if result is None:
            return None

        return result.get("scores", [])

    async def calculate_score_performance(self, score):
        return await calculate_score_performance(score)