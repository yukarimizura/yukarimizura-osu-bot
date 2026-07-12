from .trace import TraceCommands


async def setup(bot):
    await bot.add_cog(
        TraceCommands(bot)
    )