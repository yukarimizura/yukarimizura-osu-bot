import discord
from utils.constants import OSU_PINK
from api.pp_calculator import load_beatmap, calculate_pp, _DIFFICULTY_CACHE, MAX_DIFFICULTY_CACHE
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
    miss_ratio = misses / total_objects
    retention = 1 - (miss_ratio ** 0.7)
    combo = max_combo * retention - misses * (max_combo / total_objects) * 2

    return int(max(0, min(combo, max_combo)))

def estimate_hits(map_info, acc, misses, od, mods):
    total_objects = map_info["total"]
    circles, sliders, spinners = map_info["circles"], map_info["sliders"], map_info["spinners"]
    acc = max(0.0, min(acc, 100.0))
    misses = min(misses, total_objects)

    remaining = total_objects - misses
    if remaining <= 0:
        return 0, 0, 0

    effective_objects = circles + sliders * 0.85 + spinners
    target_total = acc / 100 * 300 * effective_objects

    effective_od = od * (1.4 if "HR" in mods else 0.5 if "EZ" in mods else 1.0)
    effective_od = min(effective_od, 10)

    speed_factor = 1.1 if ("DT" in mods or "NC" in mods) else 0.9 if "HT" in mods else 1.0
    fifty_weight = (0.5 + (10 - effective_od) * 0.15) * speed_factor
    hundred_weight = (0.2 + (10 - effective_od) * 0.05) * speed_factor

    best_score, best = float("inf"), None
    est_n100 = (300 * remaining - target_total) / 200
    window = max(10, int(remaining * 0.05))

    for n100 in range(int(max(0, est_n100 - window)), int(min(remaining, est_n100 + window)) + 1):
        n300 = remaining - n100
        if n300 < 0:
            continue
        n50 = 0
        diff = target_total - (300 * n300 + 100 * n100)
        if diff > 0:
            n50 = min(int(diff / 50), n300, int(circles * 0.08))
            n300 -= n50

        diff = abs((300 * n300 + 100 * n100 + 50 * n50) - target_total)
        score = diff + (n50 * fifty_weight + hundred_weight * n100)

        if score < best_score:
            best_score, best = score, (n300, n100, n50)
        if diff < 0.01:
            break

    return best if best else (int(remaining), 0, 0)

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
    beatmap_id = beatmap["id"]
    parsed = await load_beatmap(session, beatmap_id)
    if parsed is None:
        return discord.Embed(title="Failed to load beatmap for calculation.")

    mods = params.get("mods", [])
    acc = params.get("accuracy", 100.0)
    misses = params.get("misses", 0)

    key = (beatmap_id, tuple(sorted(mods)))
    if key in _DIFFICULTY_CACHE:
        difficulty = _DIFFICULTY_CACHE[key]
        _DIFFICULTY_CACHE.move_to_end(key)
    else:
        difficulty = Difficulty(mods=mods).calculate(parsed)
        _DIFFICULTY_CACHE[key] = difficulty
        _DIFFICULTY_CACHE.move_to_end(key)
        while len(_DIFFICULTY_CACHE) > MAX_DIFFICULTY_CACHE:
            _DIFFICULTY_CACHE.popitem(last=False)

    stars = getattr(difficulty, "stars", beatmap["difficulty_rating"])
    max_combo = getattr(difficulty, "max_combo", beatmap.get("max_combo", 0))

    map_info = {
        "circles": parsed.n_circles,
        "sliders": parsed.n_sliders,
        "spinners": parsed.n_spinners,
        "total": parsed.n_circles + parsed.n_sliders + parsed.n_spinners
    }

    n300, n100, n50 = estimate_hits(map_info, acc, misses, beatmap["accuracy"], mods)
    combo = estimate_combo(max_combo, misses, map_info["total"])

    pp = calculate_pp(
        beatmap=parsed,
        mods=mods,
        combo=combo,
        n300=n300,
        n100=n100,
        n50=n50,
        misses=misses,
        passed_objects=map_info["total"] - misses if misses else None
    ) or 0

    acc_headers, acc_pps = [], []
    for a in (95, 97, 99, 100):
        h300, h100, h50 = estimate_hits(map_info, a, 0, beatmap["accuracy"], mods)
        val = calculate_pp(parsed, mods, max_combo, h300, h100, h50, 0) or 0
        acc_headers.append(f"{a}%")
        acc_pps.append(f"{val:.0f}pp")

    embed = discord.Embed(
        title=f"{beatmap['beatmapset']['artist']} - {beatmap['beatmapset']['title']} [{beatmap['version']}]",
        color=OSU_PINK
    )
    embed.set_thumbnail(url=beatmap["beatmapset"]["covers"]["card"])
    embed.description = f"**⭐ {stars:.2f} • {''.join(mods) if mods else 'NM'}**\nMapped by **{beatmap['beatmapset']['creator']}**"
    
    length = beatmap["total_length"]
    embed.add_field(
        name="📊 Map Stats",
        value=(
            f"`{beatmap['bpm']}` **BPM** • `{length // 60}:{length % 60:02d}` • `{max_combo}x`\n"
            f"**CS** `{beatmap['cs']}` • **AR** `{beatmap['ar']}` • **OD** `{beatmap['accuracy']}` • **HP** `{beatmap['drain']}`"
        ),
        inline=False
    )
    embed.add_field(
        name="🎯 Objects",
        value=f"Circle: {map_info['circles']} Sliders: {map_info['sliders']} Spinners: {map_info['spinners']}",
        inline=True
    )
    embed.add_field(
        name="💎 PP Calculator",
        value=f"**Accuracy**\n`{' | '.join(acc_headers)}`\n`{' | '.join(acc_pps)}`",
        inline=False
    )
    embed.set_footer(text=f"Mapped by {beatmap['beatmapset']['creator']}")
    return embed