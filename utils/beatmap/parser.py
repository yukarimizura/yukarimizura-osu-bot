import re
import discord

BEATMAP_REGEX = re.compile(
    r"(?:https?://)?(?:osu\.)?ppy\.sh/(?:beatmaps/|b/|beatmapsets/\d+#[a-z]*/|beatmapsets/\d+#/?)(\d+)",
    re.IGNORECASE
)

def extract_beatmap_id(text: str | None) -> int | None:
    if not text:
        return None
    match = BEATMAP_REGEX.search(text)
    return int(match.group(1)) if match else None

async def extract_beatmap_from_embed(embed: discord.Embed) -> int | None:
    # 1. Direct embed attributes
    for text in (embed.url, embed.title, embed.description):
        bid = extract_beatmap_id(text)
        if bid:
            return bid

    # 2. Author and footer
    if embed.author and embed.author.url:
        bid = extract_beatmap_id(embed.author.url)
        if bid:
            return bid

    if embed.footer and embed.footer.text:
        bid = extract_beatmap_id(embed.footer.text)
        if bid:
            return bid

    # 3. Field values & names (for compatibility with other bot embeds)
    for field in embed.fields:
        bid = extract_beatmap_id(field.value) or extract_beatmap_id(field.name)
        if bid:
            return bid

    return None