from .map import Map


async def setup(bot):
    await bot.add_cog(
        Map(bot)
    )