import re
import discord

BEATMAP_REGEX = re.compile(
    r"(?:https?://)?(?:osu\.)?ppy\.sh/(?:beatmaps/|b/|beatmapsets/\d+#(?:osu|mania|taiko|fruits)/)(\d+)"
)

def extract_beatmap_id(text: str | None) -> int | None:
    if not text:
        return None
    match = BEATMAP_REGEX.search(text)
    return int(match.group(1)) if match else None

async def extract_beatmap_from_embed(embed: discord.Embed) -> int | None:
    for text in (embed.url, embed.title, embed.description):
        if text:
            bid = extract_beatmap_id(text)
            if bid:
                return bid
    if embed.author and embed.author.url:
        bid = extract_beatmap_id(embed.author.url)
        if bid:
            return bid
    if embed.footer and embed.footer.text:
        bid = extract_beatmap_id(embed.footer.text)
        if bid:
            return bid
    return None