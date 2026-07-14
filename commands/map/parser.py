import re

BEATMAP_REGEX = re.compile(
    r"(?:https?://)?(?:osu\.)?ppy\.sh/(?:beatmaps/|b/|beatmapsets/\d+#(?:osu|mania|taiko|fruits)/)(\d+)"
)

def extract_beatmap_id(text: str | None):

    if not text:
        return None

    match = BEATMAP_REGEX.search(text)

    if match:
        return int(match.group(1))

    return None

async def extract_beatmap_from_embed(embed) -> int | None:
    if embed.url:
        result = extract_beatmap_id(embed.url)
        if result:
            return result
        
    if embed.title:
        result = extract_beatmap_id(embed.title)
        if result:
            return result
        
    if embed.description:
        result = extract_beatmap_id(embed.description)
        if result:
            return result
    return None