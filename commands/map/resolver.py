from .parser import extract_beatmap_id, extract_beatmap_from_embed

async def resolve_beatmap_id(ctx, arg: str | None) -> int | None:

    # -------------------------
    # 1. Direct input (works for both)
    # -------------------------
    if arg:
        beatmap_id = extract_beatmap_id(arg)
        if beatmap_id:
            return beatmap_id

    
    # -------------------------
    # 2. SLASH COMMAND handling
    # -------------------------
    if ctx.interaction:
        interaction = ctx.interaction

        if interaction.data.get("resolved"):
            message = interaction.data["resolved"].get("messages", {})
            for msg_data in message.values():
                beatmap_id = extract_beatmap_id(msg_data.get("content"))
                if beatmap_id:
                    return beatmap_id
            
    # fallback: channel history
        async for msg in interaction.channel.history(limit=10):
            beatmap_id = extract_beatmap_id(msg.content)
            if beatmap_id:
                return beatmap_id
            
            for embed in msg.embeds:
                beatmap_id = await extract_beatmap_from_embed(embed)
                if beatmap_id:
                    return beatmap_id
                
        return None

    # -------------------------
    # 3. PREFIX COMMAND handling
    # -------------------------

    if ctx.message.reference:
        msg = await ctx.channel.fetch_message(
            ctx.message.reference.message_id
        )

        beatmap_id = extract_beatmap_id(msg.content)
        if beatmap_id:
            return beatmap_id
        
        for embed in msg.embeds:
            beatmap_id = await extract_beatmap_from_embed(embed)
            if beatmap_id:
                return beatmap_id
            
    # fallback history
    async for msg in ctx.channel.history(limit=10):
        beatmap_id = extract_beatmap_id(msg.content)
        if beatmap_id:
            return beatmap_id
        
        for embed in msg.embeds:
            beatmap_id = await extract_beatmap_from_embed(embed)
            if beatmap_id:
                return beatmap_id
            
    return None