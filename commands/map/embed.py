import discord
from utils.constants import OSU_PINK
from api.pp_calculator import load_beatmap, calculate_pp
from rosu_pp_py import Difficulty

def estimate_hits(total_objects: int, acc: float, misses: int):
    """
    Bathbot-style hit distribution solver using search.
    """

    misses = min(misses, total_objects)
    remaining = total_objects - misses

    if remaining <= 0:
        return 0, 0, 0

    target_total = acc / 100 * 300 * total_objects

    best = None
    best_diff = float("inf")

    # limit search space (important for performance)
    max_100 = min(remaining, 2000)  # safe cap

    for n100 in range(max_100 + 1):
        for n50 in range(min(remaining - n100, 200) + 1):  # 50s are usually low

            n300 = remaining - n100 - n50

            if n300 < 0:
                continue

            total = 300*n300 + 100*n100 + 50*n50

            diff = abs(total - target_total)

            if diff < best_diff:
                best_diff = diff
                best = (n300, n100, n50)

            # early exit if perfect match
            if diff == 0:
                return best

    return best if best else (remaining, 0, 0)

async def create_map_embed(beatmap, params, session):

    title = beatmap["beatmapset"]["title"]
    artist = beatmap["beatmapset"]["artist"]
    version = beatmap["version"]
    creator = beatmap["beatmapset"]["creator"]

    bpm = beatmap["bpm"]

    cs = beatmap["cs"]
    ar = beatmap["ar"]
    od = beatmap["od"]
    hp = beatmap["drain"]

    length = beatmap["total_length"]
    minutes = length // 60
    second = length % 60
    thumbnail = beatmap["beatmapset"]["covers"]["card"]

    # -------------------------
    # PARAMS
    # -------------------------

    mods = params.get("mods", [])
    acc = params.get("accuracy", 100.0)
    misses = params.get("misses", 0)

    mod_str = "".join(mods) if mods else "NM"

    # -------------------------
    # LOAD .OSU FOR CALC
    # -------------------------

    beatmap_id = beatmap["id"]
    parsed = await load_beatmap(session, beatmap_id)

    if parsed is None:
        return discord.Embed(
            title =  "Failed to load beatmap for calculation."
        )
    
    difficulty = Difficulty(mods=mods).calculate(parsed)

    stars = getattr(difficulty, "stars", beatmap["difficulty_rating"])
    max_combo = getattr(difficulty, "max_combo", beatmap.get("max_combo", 0))

    total_objects = getattr(parsed, "n_objects", None)
    if total_objects is None:
        total_objects = len(parsed.hit_objects)

    misses = min(misses, total_objects)

    # -------------------------
    # MAIN PP
    # -------------------------

    n300, n100, n50 = estimate_hits(total_objects, acc, misses)

    pp = calculate_pp(
        beatmap=parsed,
        mods=mods,
        combo=max_combo,
        n300=n300,
        n100=n100,
        n50=n50,
        misses=misses
    ) or 0

    # -------------------------
    # FC PP
    # -------------------------
    fc_pp = calculate_pp(
        beatmap=parsed,
        mods=mods,
        combo=max_combo,
        n300=n300 + misses,
        n100=n100,
        n50=n50,
        misses=0
    ) or 0
    
    # -------------------------
    # MULTI ACC
    # -------------------------
    acc_values = [95, 97, 99, 100]
    acc_lines = []

    for a in acc_values:
        n300, n100, n50 = estimate_hits(total_objects, a, 0)

        value = calculate_pp(
            beatmap=parsed,
            mods=mods,
            combo=max_combo,
            n300=n300,
            n100=n100,
            n50=n50,
            misses=0
        ) or 0

        acc_lines.append(f"**{a}%** → {value:.0f}pp")

    # -------------------------
    # EMBED
    # -------------------------


    embed = discord.Embed(
        title = f"{artist} - {title} [{version}]",
        color = OSU_PINK,
    )

    embed.set_thumbnail(url=thumbnail)

    embed.add_field(
        name = "Map Info",
        value = (
            f"⭐ {stars:.2f} • {mod_str} | BPM {bpm}\n"
            f"CS {cs} • AR {ar} • OD {od} • HP {hp}\n"
            f"Length: {minutes}:{second:02d}\n"
            f"Max Combo: {max_combo}"
        ),
        inline=False
    )

    embed.add_field(
        name = "PP Simulation",
        value = (
            f"🎯 {acc:.2f}% → **{pp:.0f}pp**\n"
            f"💯 FC → **{fc_pp:.0f}pp**\n\n"
            + "\n".join(acc_lines)
        ),
        inline=False
    )

    embed.set_footer(text = f"Mapped by {creator}")

    return embed