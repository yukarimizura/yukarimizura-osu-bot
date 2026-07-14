from discord.ext import commands
import discord

from utils.beatmap.params import parse_score_params
from .resolver import resolve_beatmap_id
from .embed import create_map_embed


class Map(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="map",
        description="Show beatmap info"
    )
    async def map(
        self,
        ctx,
        arg: str = None
    ):
        if ctx.interaction:
            await ctx.defer()

        params = parse_score_params(arg) if arg else {}
        
        beatmap_id = await resolve_beatmap_id(ctx, arg)

        if beatmap_id is None:
            return await ctx.send(
                "Provide a beatmap link, or reply to a message containing one"
            )
        
        beatmap = await self.bot.osu.get_beatmap(beatmap_id)

        if beatmap is None:
            return await ctx.send(
                "Failed to fetch beatmap."
            )
        
        embed = await create_map_embed(
            beatmap,
            params,
            self.bot.osu.session
        )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Map(bot))