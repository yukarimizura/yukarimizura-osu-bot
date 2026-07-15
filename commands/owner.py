from discord.ext import commands

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx):
        synced = await self.bot.tree.sync()
        await ctx.send(f"✅ Synced {len(synced)} slash commands.")

async def setup(bot):
    await bot.add_cog(Owner(bot))