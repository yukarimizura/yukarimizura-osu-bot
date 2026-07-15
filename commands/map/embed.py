import discord
from utils.constants import OSU_PINK
from api.pp_calculator import load_beatmap, calculate_pp
from rosu_pp_py import Difficulty

# global or bot-level cache
beatmap_cache = {}

difficulty_cache = {}


async def load_cached(session, beatmap_id):
    if beatmap_id in beatmap_cache:
        return beatmap_cache[beatmap_id]

    parsed = await load_beatmap(session, beatmap_id)
    beatmap_cache[beatmap_id] = parsed
    return parsed

def estimate_combo(max_combo: int, misses: int, total_objects: int):

    if misses == 0:
        return max_combo

    # combo scales based on how late misses happen
    # simulate average play: earlier misses hurt more

    miss_ratio = misses / total_objects

    # expected combo retention curve
    retention = 1 - (miss_ratio ** 0.7)

    combo = max_combo * retention

    # extra punishment per miss
    combo -= misses * (max_combo / total_objects) * 2

    return int(max(0, min(combo, max_combo)))

def estimate_hits(map_info, acc, misses, od, mods):

    total_objects = map_info["total"]
    circles = map_info["circles"]
    sliders = map_info["sliders"]
    spinners = map_info["spinners"]

    acc = max(0.0, min(acc, 100.0))
    misses = min(misses, total_objects)

    # 🎯 sliders are "easier" → shift accuracy weight
    slider_factor = 0.85

    remaining = total_objects - misses
    if remaining <= 0:
        return 0, 0, 0

    effective_objects = circles + sliders * slider_factor + spinners

    target_total = acc / 100 * 300 * effective_objects

    # --- OD scaling ---
    effective_od = od
    if "HR" in mods:
        effective_od *= 1.4
    if "EZ" in mods:
        effective_od *= 0.5
    effective_od = min(effective_od, 10)

    fifty_weight = 0.5 + (10 - effective_od) * 0.15
    hundred_weight = 0.2 + (10 - effective_od) * 0.05

    # --- speed mods affect perceived accuracy ---
    speed_factor = 1.0

    if "DT" in mods or "NC" in mods:
        speed_factor = 1.1   # harder → more 100/50
    elif "HT" in mods:
        speed_factor = 0.9   # easier → more 300

    # adjust penalty weights
    fifty_weight *= speed_factor
    hundred_weight *= speed_factor

    best = None
    best_score = float("inf")

    est_n100 = (300 * remaining - target_total) / 200
    window = max(10, int(remaining * 0.05))

    for n100 in range(
        int(max(0, est_n100 - window)),
        int(min(remaining, est_n100 + window)) + 1,
    ):
        n300 = remaining - n100
        if n300 < 0:
            continue

        n50 = 0

        total = 300*n300 + 100*n100
        diff = target_total - total

        if diff > 0:
            needed_50 = int(diff / 50)
            max_50 = int(circles * 0.08)  # only circles realistically 50

            n50 = min(needed_50, n300, max_50)
            n300 -= n50

        total = 300*n300 + 100*n100 + 50*n50
        diff = abs(total - target_total)

        penalty = (
            n50 * fifty_weight +
            n100 * hundred_weight
        )

        score = diff + penalty

        if score < best_score:
            best_score = score
            best = (n300, n100, n50)

        if diff < 0.01:
            break

    if best:
        return int(best[0]), int(best[1]), int(best[2])

    return int(remaining), 0, 0

map_info_cache = {}

def analyze_map(parsed, beatmap_id):
    if beatmap_id in map_info_cache:
        return map_info_cache[beatmap_id]

    info = {
        "circles": parsed.n_circles,
        "sliders": parsed.n_sliders,
        "spinners": parsed.n_spinners,
        "total": parsed.n_circles + parsed.n_sliders + parsed.n_spinners
    }

    map_info_cache[beatmap_id] = info
    return info

async def create_map_embed(beatmap, params, session):

    title = beatmap["beatmapset"]["title"]
    artist = beatmap["beatmapset"]["artist"]
    version = beatmap["version"]
    creator = beatmap["beatmapset"]["creator"]

    bpm = beatmap["bpm"]

    cs = beatmap["cs"]
    ar = beatmap["ar"]
    od = beatmap["accuracy"]
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
    parsed = await load_cached(session, beatmap_id)

    if parsed is None:
        return discord.Embed(
            title =  "Failed to load beatmap for calculation."
        )

    key = (beatmap_id, tuple(sorted(mods)))

    if key in difficulty_cache:
        difficulty = difficulty_cache[key]
    else:
        difficulty = Difficulty(mods=mods).calculate(parsed)
        difficulty_cache[key] = difficulty

    stars = getattr(difficulty, "stars", beatmap["difficulty_rating"])
    max_combo = getattr(difficulty, "max_combo", beatmap.get("max_combo", 0))

    total_objects = getattr(parsed, "n_objects", None)
    if total_objects is None:
        n_circles = parsed.n_circles
        n_sliders = parsed.n_sliders
        n_spinners = parsed.n_spinners

        total_objects = n_circles + n_sliders + n_spinners

    misses = min(misses, total_objects)

    # -------------------------
    # MAIN PP
    # -------------------------

    map_info = analyze_map(parsed, beatmap_id)

    n300, n100, n50 = estimate_hits(
        map_info,
        acc,
        misses,
        od,
        mods
    )

    combo = estimate_combo(max_combo, misses, total_objects)

    passed_objects = total_objects - misses if misses else None

    pp = calculate_pp(
        beatmap=parsed,
        mods=mods,
        combo=combo,
        n300=n300,
        n100=n100,
        n50=n50,
        misses=misses,
        passed_objects = passed_objects,
    ) or 0

    # -------------------------
    # FC PP
    # -------------------------
    fc_combo = max_combo

    fc_n300 = total_objects - n100 - n50

    fc_pp = calculate_pp(
        beatmap=parsed,
        mods=mods,
        combo=fc_combo,
        n300=fc_n300,
        n100=n100,
        n50=n50,
        misses=0
    ) or 0
    
    # -------------------------
    # MULTI ACC
    # -------------------------
    acc_values = [95, 97, 99, 100]

    acc_headers = []
    acc_pps = []

    for a in acc_values:
        n300, n100, n50 = estimate_hits(
            map_info,
            a,
            0,
            od,
            mods
        )

        value = calculate_pp(
            beatmap=parsed,
            mods=mods,
            combo=max_combo,
            n300=n300,
            n100=n100,
            n50=n50,
            misses=0
        ) or 0

        acc_headers.append(f"{a}%")
        acc_pps.append(f"{value:.0f}pp")

    acc_header_line = " | ".join(acc_headers)
    acc_pp_line = " | ".join(acc_pps)

    # -------------------------
    # EMBED
    # -------------------------


    embed = discord.Embed(
        title=f"{artist} - {title} [{version}]",
        color=OSU_PINK,
    )

    embed.set_thumbnail(url=thumbnail)

    embed.description = (
        f"**⭐ {stars:.2f} • {mod_str}**\n"
        f"Mapped by **{creator}**"
    )

    embed.add_field(
        name="📊 Map Stats",
        value=(
            f"`{bpm}` **BPM** • `{minutes}:{second:02d}` • `{max_combo}x`\n"
            f"**CS** `{cs}` • **AR** `{ar}` • **OD** `{od}` • **HP** `{hp}`"
        ),
        inline=False
    )

    embed.add_field(
        name="🎯 Objects",
        value=(
            f"Circle: {map_info['circles']} "
            f"Sliders: {map_info['sliders']} "
            f"Spinners: {map_info['spinners']}"
        ),
        inline=True
    )

    embed.add_field(
        name="💎 PP Calculator",
        value=(
            f"**Accuracy**\n"
            f"`{acc_header_line}`\n"
            f"`{acc_pp_line}`"
        ),
        inline=False
    )

    embed.set_footer(
        text=f"Beatmap ID: {beatmap_id}"
    )

    embed.set_footer(text = f"Mapped by {creator}")

    return embed