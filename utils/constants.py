# utils/constants.py (Add or update these)

OSU_PINK = 0xFF66AA

MODE_NAMES = {
    "osu": "osu!",
    "taiko": "osu!taiko",
    "fruits": "osu!catch",
    "mania": "osu!mania"
}

GRADE_DISPLAY = {
    "XH": "✦ SS",
    "X": "✦ SS",
    "SH": "◆ S",
    "S": "◆ S",
    "A": "🟢 A",
    "B": "🔵 B",
    "C": "🟡 C",
    "D": "🟠 D",
    "F": "🔴 FAILED"
}

def format_mods(mods) -> str:
    """Format an osu! mods list/dict into '+HDHR' or 'NM'."""
    if not mods:
        return "NM"

    result = []
    for mod in mods:
        if isinstance(mod, str):
            result.append(mod)
        elif isinstance(mod, dict):
            acronym = mod.get("acronym")
            if acronym:
                result.append(acronym)

    return "+" + "".join(result) if result else "NM"


def get_hit_stat(statistics: dict, *names) -> int:
    """Extract hit stat counts from an osu! score statistics object."""
    for name in names:
        val = statistics.get(name)
        if val is not None:
            return val
    return 0