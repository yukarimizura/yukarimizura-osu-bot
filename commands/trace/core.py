from datetime import datetime, timezone
from math import ceil

SCORES_PER_PAGE = 4


# --------------------------------------------------------
# Pagination
# --------------------------------------------------------

def get_total_pages(scores):

    if not scores:
        return 1

    return ceil(len(scores) / SCORES_PER_PAGE)


def get_page_scores(scores, page):

    start = page * SCORES_PER_PAGE
    end = start + SCORES_PER_PAGE

    return scores[start:end]


# --------------------------------------------------------
# Helpers
# --------------------------------------------------------

def get_stat(score, *names):

    stats = score.get("statistics", {})

    for name in names:

        value = stats.get(name)

        if value is not None:
            return value

    return 0


def get_miss(score):

    return get_stat(
        score,
        "miss",
        "count_miss"
    )


def get_pp(score):

    return score.get("pp") or 0


def get_acc(score):

    return score.get("accuracy", 0) * 100


def get_combo(score):

    return score.get("max_combo", 0)


def get_date(score):

    return score.get("created_at")


# --------------------------------------------------------
# Time
# --------------------------------------------------------

def relative_time(date_string):

    if not date_string:
        return "-"

    played = datetime.fromisoformat(
        date_string.replace("Z", "+00:00")
    )

    now = datetime.now(timezone.utc)

    delta = now - played

    days = delta.days

    if days == 0:
        return "today"

    if days == 1:
        return "1d ago"

    if days < 30:
        return f"{days}d ago"

    months = days // 30

    if months < 12:
        return f"{months}mo ago"

    years = months // 12

    return f"{years}y ago"


def format_date(date_string):

    if not date_string:
        return "-"

    dt = datetime.fromisoformat(
        date_string.replace("Z", "+00:00")
    )

    return dt.strftime("%d %b %Y")

# --------------------------------------------------------
# Difference
# --------------------------------------------------------

def calculate_difference(newer, older):

    if newer is None:
        return {
            "pp": 0,
            "acc": 0,
            "combo": 0,
            "miss": 0
        }

    return {

        "pp":
            get_pp(newer)
            - get_pp(older),

        "acc":
            get_acc(newer)
            - get_acc(older),

        "combo":
            get_combo(newer)
            - get_combo(older),

        "miss":
            get_miss(older)
            - get_miss(newer)
    }


# --------------------------------------------------------
# Grade
# --------------------------------------------------------

GRADE_EMOJI = {

    "XH": "✦ SS",
    "X": "✦ SS",

    "SH": "◆ S",
    "S": "◆ S",

    "A": "🟢 A",
    "B": "🔵 B",
    "C": "🟡 C",
    "D": "🟠 D",

    "F": "🔴 F"
}


def get_grade(score):

    return GRADE_EMOJI.get(
        score.get("rank", "F"),
        "🔴 F"
    )

def get_mods(score):

    mods = score.get("mods", [])

    if not mods:
        return "NM"
    
    return "".join(mods)


# --------------------------------------------------------
# Personal Best
# --------------------------------------------------------

def build_pb_section(score):

    return (
        f"{get_grade(score)} • "
        f"`+{get_mods(score)}` • "
        f"**{get_pp(score):.2f}pp**\n"

        f"**{get_acc(score):.2f}%** • "
        f"**{get_combo(score):,}x**\n"

        f"❌ **{get_miss(score)} miss**\n"

        f"🕒 {relative_time(get_date(score))}"
    )


# --------------------------------------------------------
# Difference Panel
# --------------------------------------------------------

def build_difference_panel(diff):

    lines = []

    # PP
    if diff["pp"] > 0:
        lines.append(f"🟢 +{diff['pp']:.2f}pp")
    elif diff["pp"] < 0:
        lines.append(f"🔴 {diff['pp']:.2f}pp")
    else:
        lines.append("⚪ ±0pp")

    # Accuracy
    if diff["acc"] > 0:
        lines.append(f"🟢 +{diff['acc']:.2f}%")
    elif diff["acc"] < 0:
        lines.append(f"🔴 {diff['acc']:.2f}%")
    else:
        lines.append("⚪ ±0%")

    # Combo
    if diff["combo"] > 0:
        lines.append(f"🟢 +{diff['combo']}x")
    elif diff["combo"] < 0:
        lines.append(f"🔴 {diff['combo']}x")
    else:
        lines.append("⚪ ±0x")

    # Misses (lower is better!)
    if diff["miss"] < 0:
        lines.append(f"🟢 {diff['miss']} Miss")
    elif diff["miss"] > 0:
        lines.append(f"🔴 +{diff['miss']} Miss")
    else:
        lines.append("⚪ ±0 Miss")

    return "\n".join(lines)


# --------------------------------------------------------
# History Entry
# --------------------------------------------------------

def build_history_entry(
    score,
    older_score
):

    if older_score is None:

        diff = {
            "pp": 0,
            "acc": 0,
            "combo": 0,
            "miss": 0
        }

    else:

        diff = {

            "pp":
                get_pp(score)
                - get_pp(older_score),

            "acc":
                get_acc(score)
                - get_acc(older_score),

            "combo":
                get_combo(score)
                - get_combo(older_score),

            # fewer misses is better
            "miss":
                get_miss(score)
                - get_miss(older_score)

        }

    history = (

        f"{get_grade(score)} • "
        f"`+{get_mods(score)}` • "
        f"**{get_pp(score):.2f}pp**\n"

        f"**{get_acc(score):.2f}%** • "
        f"**{get_combo(score):,}x**\n"

        f"❌ **{get_miss(score)} miss**\n"

        f"🕒 {relative_time(get_date(score))}"

    )

    return history, build_difference_panel(diff)