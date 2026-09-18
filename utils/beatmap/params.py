import re

MOD_ALIASES = {
    "NF": "NF", "EZ": "EZ", "TD": "TD", "HD": "HD", "HR": "HR",
    "SD": "SD", "DT": "DT", "RX": "RX", "HT": "HT", "NC": "NC",
    "FL": "FL", "AT": "AT", "SO": "SO", "AP": "AP", "PF": "PF",
}

def parse_score_params(arg: str | None) -> dict:
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
        clean_mods = token_upper.lstrip("+")
        if token_lower == "nm":
            mods = []
            continue

        if (
            len(clean_mods) >= 2
            and len(clean_mods) % 2 == 0
            and all(clean_mods[i:i+2] in MOD_ALIASES for i in range(0, len(clean_mods), 2))
        ):
            mods.extend(clean_mods[i:i+2] for i in range(0, len(clean_mods), 2))
            continue

        # -------------------------
        # ACCURACY
        # -------------------------
        if "%" in token:
            try:
                val = float(token.replace("%", ""))
                if 0 <= val <= 100:
                    accuracy = val
                    continue
            except ValueError:
                pass

        if token_lower.startswith("acc="):
            try:
                val = float(token.split("=")[1].replace("%", ""))
                if 0 <= val <= 100:
                    accuracy = val
                    continue
            except ValueError:
                pass

        # -------------------------
        # MISSES
        # -------------------------
        if token_lower == "fc":
            misses = 0
            continue

        if token_lower.endswith("m") and token[:-1].isdigit():
            misses = int(token[:-1])
            continue

        if token_lower.startswith("miss="):
            try:
                misses = int(token.split("=")[1])
                continue
            except ValueError:
                pass

        # -------------------------
        # BEATMAP ID
        # -------------------------
        if token.isdigit():
            # Treat large integer IDs as beatmap IDs
            beatmap_id = int(token)

    # Deduplicate while preserving order
    mods = list(dict.fromkeys(mods))

    return {
        "beatmap_id": beatmap_id,
        "mods": mods,
        "accuracy": accuracy,
        "misses": misses,
    }