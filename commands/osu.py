import discord

from discord.ext import commands

from utils import (
    MODE_NAMES,
    OSU_PINK,
    unlink_user,
    link_user,
    get_linked_user
)


class OsuCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.hybrid_command(
        name="link",
        description="Link your Discord account to your osu! account."
    )
    async def link(
        self,
        ctx: commands.Context,
        *,
        username: str
    ):

        async with ctx.typing():
            user = await self.bot.osu.get_user(username)

        if user is None:
            await ctx.send(
                f"Could not find osu! player `{username}`."
            )
            return

        link_user(
            ctx.author.id,
            user
        )

        await ctx.send(
            f"Successfully linked "
            f"{ctx.author.mention} to "
            f"**{user['username']}**!"
        )
    @commands.command()
    async def unlink(self, ctx):

        success = unlink_user(ctx.author.id)

        if not success:
            await ctx.send(
                "You don't have an osu! account linked."
            )
            return

        await ctx.send(
            f"Successfully unlinked {ctx.author.mention}'s osu! account."
        )

    @commands.hybrid_command(
        name="osu",
        description="Show an osu! player's profile."
    )
    async def osu(
        self,
        ctx: commands.Context,
        *,
        username: str = None
    ):

        if username is None:

            linked_user = get_linked_user(
                ctx.author.id
            )

            if linked_user is None:
                await ctx.send(
                    "You haven't linked an osu! account yet. "
                    "Use `!link <username>` first."
                )
                return

            username = str(
                linked_user["osu_id"]
            )

        async with ctx.typing():
            user = await self.bot.osu.get_user(username)

        if user is None:
            await ctx.send(
                f"Could not find osu! player `{username}`."
            )
            return

        main_mode = user["playmode"]
        stats = user["statistics"]

        global_rank = stats.get("global_rank")
        country_rank = stats.get("country_rank")
        pp = stats.get("pp", 0)
        accuracy = stats.get("hit_accuracy", 0)
        play_count = stats.get("play_count", 0)

        embed = discord.Embed(
            title=user["username"],
            url=(
                f"https://osu.ppy.sh/users/"
                f"{user['id']}"
            ),
            color=OSU_PINK
        )

        embed.set_thumbnail(
            url=user["avatar_url"]
        )

        embed.add_field(
            name="Global Rank",
            value=(
                f"#{global_rank:,}"
                if global_rank
                else "N/A"
            ),
            inline=True
        )

        embed.add_field(
            name="Country Rank",
            value=(
                f"#{country_rank:,}"
                if country_rank
                else "N/A"
            ),
            inline=True
        )

        embed.add_field(
            name="PP",
            value=f"{pp:,.2f}",
            inline=True
        )

        embed.add_field(
            name="Accuracy",
            value=f"{accuracy:.2f}%",
            inline=True
        )

        embed.add_field(
            name="Play Count",
            value=f"{play_count:,}",
            inline=True
        )

        embed.set_footer(
            text=MODE_NAMES.get(
                main_mode,
                main_mode
            )
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(
        OsuCommands(bot)
    )