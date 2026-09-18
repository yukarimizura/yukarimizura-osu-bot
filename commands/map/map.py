import discord
from discord.ext import commands

from utils.beatmap.params import parse_score_params
from .resolver import resolve_beatmap_id
from .embed import create_map_embed


class Map(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(
        name="map",
        description="Show beatmap information and PP benchmarks."
    )
    async def map(self, ctx: commands.Context, *, arg: str = None):
        if ctx.interaction:
            await ctx.defer()
        else:
            await ctx.typing()

        params = parse_score_params(arg) if arg else {}
        beatmap_id = params.get("beatmap_id") or await resolve_beatmap_id(ctx, arg)

        if beatmap_id is None:
            await ctx.send("Provide a beatmap link, ID, or reply to a message containing one.")
            return

        beatmap = await self.bot.osu.get_beatmap(beatmap_id)
        if beatmap is None:
            await ctx.send("Failed to fetch beatmap data from osu! API.")
            return

        embed = await create_map_embed(
            beatmap=beatmap,
            params=params,
            session=self.bot.osu.session
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Map(bot))