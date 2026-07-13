import aiohttp
import time
import asyncio
from api.pp_calculator import calculate_score_performance
from config import HTTP_MAX_RETRIES, HTTP_RETRY_DELAY

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

            timeout = aiohttp.ClientTimeout(
                total=15
            )

            self.session = aiohttp.ClientSession(
                timeout=timeout
            )


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

        token = await self.get_token()

        if token is None:
            return None

        headers = {
            "Authorization": f"Bearer {token}"
        }

        for attempt in range(HTTP_MAX_RETRIES):

            try:

                async with self.session.get(
                    url,
                    headers=headers,
                    params=params
                ) as response:

                    # Success
                    if response.status == 200:
                        return await response.json()

                    # Retry if failed

                    if response.status in (
                        500,
                        502,
                        503,
                        504
                    ):
                        if attempt < HTTP_MAX_RETRIES - 1:
                            await asyncio.sleep(
                                HTTP_RETRY_DELAY * (2 ** attempt)
                            ) 
                            continue

                    # Everything Else
                    error = await response.text()

                    print(
                        f"HTTP {response.status} "
                        f"for {url}: {error}" # Much easier Debugging if error
                    )

                    return None
                
            except (
                aiohttp.ClientConnectionError,
                aiohttp.ClientOSError,
                asyncio.TimeoutError
            ) as error:
                if attempt == HTTP_MAX_RETRIES - 1:
                    print(
                        f"Request failed after "
                        f"{HTTP_MAX_RETRIES} attempts: "
                        f"{error}"
                    )

                    return None
                
                await asyncio.sleep(
                    HTTP_RETRY_DELAY * (2 ** attempt)
                )

        return None

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
        return await calculate_score_performance(self.session, score)