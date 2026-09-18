import discord
from utils.beatmap.parser import extract_beatmap_id, extract_beatmap_from_embed

async def _extract_from_message(message: discord.Message) -> int | None:
    """Helper to check content and embeds of a single message."""
    if not message:
        return None

    # Check text content first
    beatmap_id = extract_beatmap_id(message.content)
    if beatmap_id:
        return beatmap_id

    # Check attached embeds
    for embed in message.embeds:
        beatmap_id = await extract_beatmap_from_embed(embed)
        if beatmap_id:
            return beatmap_id

    return None

async def resolve_beatmap_id(ctx, arg: str | None) -> int | None:
    # 1. Direct user argument (URL or raw ID)
    if arg:
        beatmap_id = extract_beatmap_id(arg)
        if beatmap_id:
            return beatmap_id

    channel = ctx.channel

    # 2. Reply reference (Prefix command replying to a beatmap)
    if getattr(ctx, "message", None) and ctx.message.reference:
        try:
            replied_msg = await channel.fetch_message(ctx.message.reference.message_id)
            beatmap_id = await _extract_from_message(replied_msg)
            if beatmap_id:
                return beatmap_id
        except (discord.NotFound, discord.HTTPException):
            pass

    # 3. Context Menu / Slash Command resolved messages
    if ctx.interaction and ctx.interaction.data.get("resolved"):
        resolved_messages = ctx.interaction.data["resolved"].get("messages", {})
        for msg_data in resolved_messages.values():
            beatmap_id = extract_beatmap_id(msg_data.get("content"))
            if beatmap_id:
                return beatmap_id

    # 4. Fallback: Search the last 10 messages in the channel
    # Skip the trigger message itself so it doesn't parse its own invocation
    trigger_id = ctx.message.id if getattr(ctx, "message", None) else None

    async for msg in channel.history(limit=10):
        if trigger_id and msg.id == trigger_id:
            continue

        beatmap_id = await _extract_from_message(msg)
        if beatmap_id:
            return beatmap_id

    return None