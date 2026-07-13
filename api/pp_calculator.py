import os
import aiohttp

from collections import OrderedDict
from rosu_pp_py import Beatmap, Performance, Difficulty
from utils.cache import cleanup_cache, touch

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

BEATMAP_CACHE_DIR = os.path.join(
    BASE_DIR,
    "data",
    "beatmaps"
)

# ---------------------------------------------------------
# Parsed Beatmap Cache (Memory)
# ---------------------------------------------------------

MAX_PARSED_BEATMAPS = 100

_PARSED_BEATMAP_CACHE: OrderedDict[str, Beatmap] = OrderedDict()

async def get_beatmap_file(session, beatmap_id):

    os.makedirs(
        BEATMAP_CACHE_DIR,
        exist_ok=True
    )

    file_path = os.path.join(
        BEATMAP_CACHE_DIR,
        f"{beatmap_id}.osu"
    )

    # Already cached
    if os.path.exists(file_path):

        touch(file_path)

        return file_path

    # Need a new slot
    cleanup_cache(
        BEATMAP_CACHE_DIR,
        ".osu"
    )

    url = (
        f"https://osu.ppy.sh/osu/"
        f"{beatmap_id}"
    )

    async with session.get(url) as response:

        if response.status != 200:

            print(
                f"Failed downloading beatmap "
                f"{beatmap_id}"
            )

            return None

        content = await response.read()

    with open(file_path, "wb") as file:
        file.write(content)

    return file_path

async def load_beatmap(session, beatmap_id):
    # Memory cache
    beatmap = _PARSED_BEATMAP_CACHE.get(beatmap_id)

    if beatmap is not None:
        _PARSED_BEATMAP_CACHE.move_to_end(beatmap_id)
        return beatmap
    
    # Disk cache

    file_path = await get_beatmap_file(session, beatmap_id)

    if file_path is None:
        return None
    
    try:
        beatmap = Beatmap(path=file_path)

    except Exception as error:
        print(
            f"Could not parse beatmap "
            f"{beatmap_id}: {error}"
        )

        return None
    
    # Save into memory
    _PARSED_BEATMAP_CACHE[beatmap_id] = beatmap

    _PARSED_BEATMAP_CACHE.move_to_end(beatmap_id)

    #LRU Eviction

    while len(_PARSED_BEATMAP_CACHE) > MAX_PARSED_BEATMAPS:

        _PARSED_BEATMAP_CACHE.popitem(last=False)

    return beatmap


def get_stat(statistics, *names):
    for name in names:
        value = statistics.get(name)

        if value is not None:
            return value

    return 0


def extract_mods(score):
    mods = score.get("mods", [])

    result = []

    for mod in mods:

        if isinstance(mod, str):
            result.append(mod)

        elif isinstance(mod, dict):
            acronym = mod.get("acronym")

            if acronym:
                result.append(acronym)

    return result

def calculate_pp(
    beatmap,
    mods,
    combo,
    n300,
    n100,
    n50,
    misses,
    passed_objects=None
):
    """
    Calculate PP for a score state.

    Returns:
        float | None
    """

    try:

        kwargs = {
            "mods": mods,
            "combo": combo,
            "n300": n300,
            "n100": n100,
            "n50": n50,
            "misses": misses,
        }

        if passed_objects is not None:
            kwargs["passed_objects"] = passed_objects

        result = Performance(
            **kwargs
        ).calculate(beatmap)

        return result.pp

    except Exception as error:

        print(
            f"PP calculation failed: {error}"
        )

        return None


async def calculate_score_performance(session, score):
    beatmap_data = score.get("beatmap")

    if not beatmap_data:
        return None

    beatmap_id = beatmap_data["id"]

    beatmap = await load_beatmap(session,beatmap_id)

    if beatmap is None:
        return None

    statistics = score.get(
        "statistics",
        {}
    )

    count_300 = get_stat(
        statistics,
        "great",
        "count_300"
    )

    count_100 = get_stat(
        statistics,
        "ok",
        "count_100"
    )

    count_50 = get_stat(
        statistics,
        "meh",
        "count_50"
    )

    count_miss = get_stat(
        statistics,
        "miss",
        "count_miss"
    )

    current_combo = score.get(
        "max_combo",
        0
    )

    mods = extract_mods(score)


    # -------------------------
    # Calculate modded difficulty + max combo
    # -------------------------

    max_combo = beatmap_data.get(
        "max_combo"
    )

    star_rating = beatmap_data.get(
        "difficulty_rating",
        0
    )

    try:
        difficulty_result = Difficulty(
            mods=mods
        ).calculate(beatmap)

        calculated_max_combo = getattr(
            difficulty_result,
            "max_combo",
            None
        )

        calculated_stars = getattr(
            difficulty_result,
            "stars",
            None
        )

        if calculated_max_combo:
            max_combo = calculated_max_combo

        if calculated_stars is not None:
            star_rating = calculated_stars

    except Exception as error:
        print(
            f"Difficulty calculation failed: "
            f"{error}"
        )


    # -------------------------
    # Actual PP
    # -------------------------

    api_pp = score.get("pp")
    actual_pp = api_pp
    # Only calculate pp if osu API didn't provide it, or if the provided pp is 0.
    if actual_pp is None:

        total_hits = (
            count_300
            + count_100
            + count_50
            + count_miss
        )

        passed_objects = None

        if score.get("rank") == "F":
            passed_objects = total_hits

        actual_pp = calculate_pp(
            beatmap=beatmap,
            mods=mods,
            combo=current_combo,
            n300=count_300,
            n100=count_100,
            n50=count_50,
            misses=count_miss,
            passed_objects=passed_objects
        )

    # -------------------------
    # FC prediction
    # -------------------------
    #
    # Every miss is converted into a 300.
    #
    # Example:
    #
    # Actual:
    # 800x 300
    # 50x 100
    # 10x 50
    # 5 misses
    #
    # FC reconstruction:
    # 805x 300
    # 50x 100
    # 10x 50
    # 0 misses
    #

    fc_count_300 = (
        count_300
        + count_miss
    )

    fc_accuracy = None
    fc_pp = None


    total_fc_hits = (
        fc_count_300
        + count_100
        + count_50
    )


    if total_fc_hits > 0:
        fc_accuracy = (
            (
                300 * fc_count_300
                + 100 * count_100
                + 50 * count_50
            )
            /
            (
                300 * total_fc_hits
            )
            * 100
        )


    fc_pp = calculate_pp(
        beatmap=beatmap,
        mods=mods,
        combo=max_combo or current_combo,
        n300=fc_count_300,
        n100=count_100,
        n50=count_50,
        misses=0
    )

    return {
        "actual_pp": actual_pp,
        "fc_pp": fc_pp,
        "fc_accuracy": fc_accuracy,
        "current_combo": current_combo,
        "max_combo": max_combo,
        "star_rating": star_rating
    }