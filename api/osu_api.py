TOKEN = None
TOKEN_EXPIRE = 0

import aiohttp

from config import OSU_CLIENT_ID, OSU_CLIENT_SECRET

from utils import (
    save_username_history,
    find_osu_id_by_username
)


async def get_osu_token():
    url = "https://osu.ppy.sh/oauth/token"

    data = {
        "client_id": int(OSU_CLIENT_ID),
        "client_secret": OSU_CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "public"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
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

            return result["access_token"]


async def get_osu_user(username):
    token = await get_osu_token()

    if token is None:
        return None

    headers = {
        "Authorization": f"Bearer {token}"
    }

    known_osu_id = find_osu_id_by_username(
        username
    )

    if known_osu_id is not None:
        lookup_value = known_osu_id
    else:
        lookup_value = username

    async with aiohttp.ClientSession() as session:

        url = (
            f"https://osu.ppy.sh/api/v2/users/"
            f"{lookup_value}"
        )

        async with session.get(
            url,
            headers=headers
        ) as response:

            if response.status == 404:
                return None

            if response.status != 200:
                error = await response.text()

                print(
                    f"osu! API error: {error}"
                )

                return None

            general_user = await response.json()

        main_mode = general_user["playmode"]
        user_id = general_user["id"]

        url = (
            f"https://osu.ppy.sh/api/v2/users/"
            f"{user_id}/{main_mode}"
        )

        async with session.get(
            url,
            headers=headers
        ) as response:

            if response.status != 200:
                error = await response.text()

                print(
                    f"osu! API error: {error}"
                )

                return None

            user = await response.json()

    save_username_history(user)

    return user

async def get_recent_scores(user_id, mode=None, limit=5):
    token = await get_osu_token()

    if token is None:
        return None

    headers = {
        "Authorization": f"Bearer {token}"
    }

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

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url,
            headers=headers,
            params=params
        ) as response:

            if response.status != 200:
                error = await response.text()
                print(f"osu! recent scores API error: {error}")
                return None

            return await response.json()
        
async def get_best_scores(user_id, mode="osu", limit=5):
    token = await get_osu_token()

    if token is None:
        return None

    url = (
        f"https://osu.ppy.sh/api/v2/users/"
        f"{user_id}/scores/best"
    )

    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {
        "mode": mode,
        "limit": limit
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url,
            headers=headers,
            params=params
        ) as response:

            if response.status != 200:
                print(
                    f"Failed to get best scores: "
                    f"HTTP {response.status}"
                )
                return None

            return await response.json()

async def get_beatmap(
    beatmap_id
):

    token = await get_osu_token()

    if token is None:
        return None

    headers = {
        "Authorization": f"Bearer {token}"
    }

    url = (
        f"https://osu.ppy.sh/api/v2/"
        f"beatmaps/{beatmap_id}"
    )

    async with aiohttp.ClientSession() as session:

        async with session.get(
            url,
            headers=headers
        ) as response:

            if response.status != 200:

                error = await response.text()

                print(
                    f"Beatmap API error: {error}"
                )

                return None

            return await response.json()

async def get_trace_scores(
    user_id,
    beatmap_id,
    mode="osu"
):
    token = await get_osu_token()

    if token is None:
        return None

    headers = {
        "Authorization": f"Bearer {token}"
    }

    params = {
        "mode": mode
    }

    url = (
        f"https://osu.ppy.sh/api/v2/"
        f"beatmaps/{beatmap_id}"
        f"/scores/users/{user_id}/all"
    )

    print("=" * 60)
    print("TRACE URL:", url)
    print("TRACE PARAMS:", params)
    print("USER ID:", user_id)
    print("BEATMAP ID:", beatmap_id)
    print("=" * 60)

    async with aiohttp.ClientSession() as session:

        async with session.get(
            url,
            headers=headers,
            params=params
        ) as response:

            print("STATUS:", response.status)

            text = await response.text()
            print(text)

            if response.status != 200:
                return None

            result = await response.json()

            return result.get("scores", [])