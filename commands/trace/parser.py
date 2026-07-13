import re
import discord

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

async def extract_beatmap_from_message(message: discord.Message, ) -> int | None:
    beatmap_id = extract_beatmap_id(
        message.content
    )

    if beatmap_id is not None:
        return beatmap_id
    
    for embed in message.embeds:
        candidates = [
            embed.url,
            embed.title,
            embed.description,
        ]

        if embed.author:
            candidates.append(embed.author.url)

        if embed.footer:
            candidates.append(embed.footer.text)

        for text in candidates:
            beatmap_id = extract_beatmap_id(text)

            if beatmap_id is not None:
                return beatmap_id
            
    return None