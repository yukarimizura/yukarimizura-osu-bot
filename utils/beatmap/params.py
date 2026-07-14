import re

MOD_ALIASES = {
    "HD": "HD",
    "HR": "HR",
    "DT": "DT",
    "NC": "NC",
    "EZ": "EZ",
    "FL": "FL",
    "HT": "HT",
    "SD": "SD",
    "PF": "PF",
}


def parse_score_params(arg: str | None):
    if not arg:
        return {}

    tokens = arg.split()

    mods = []
    accuracy = None
    misses = None
    beatmap_id = None

    for token in tokens:
        token_upper = token.upper()
        token_lower = token.lower()

        # -------------------------
        # MODS
        # -------------------------
        if token_upper.startswith("+"):
            token_upper = token_upper[1:]

        if token_lower == "nm":
            mods = []
            continue

        if (
            len(token_upper) >= 2
            and len(token_upper) % 2 == 0
            and all(token_upper[i:i+2] in MOD_ALIASES for i in range(0, len(token_upper), 2))
        ):
            mods.extend(
                token_upper[i:i+2]
                for i in range(0, len(token_upper), 2)
            )
            continue

        # -------------------------
        # ACCURACY
        # -------------------------
        if "%" in token:
            try:
                accuracy = float(token.replace("%", ""))
                continue
            except:
                pass

        if token_lower.startswith("acc="):
            try:
                value = token.split("=")[1].replace("%", "")
                accuracy = float(value)
                continue
            except:
                pass

        # -------------------------
        # MISSES
        # -------------------------
        if token_lower == "fc":
            misses = 0
            continue

        if token.endswith("m"):
            try:
                misses = int(token[:-1])
                continue
            except:
                pass

        if token_lower.startswith("miss="):
            try:
                misses = int(token.split("=")[1])
                continue
            except:
                pass

        # -------------------------
        # BEATMAP ID
        # -------------------------
        if token.isdigit():
            beatmap_id = int(token)

    # remove duplicate mods
    mods = list(dict.fromkeys(mods))

    return {
        "beatmap_id": beatmap_id,
        "mods": mods,
        "accuracy": accuracy,
        "misses": misses,
    }