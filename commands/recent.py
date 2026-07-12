from datetime import datetime

import discord
from discord.ext import commands

from utils import (
    get_linked_user,
    MODE_NAMES,
    OSU_PINK
)


GRADE_DISPLAY = {
    "XH": "✦ SS",
    "X": "✦ SS",
    "SH": "◆ S",
    "S": "◆ S",
    "A": "🟢 A",
    "B": "🔵 B",
    "C": "🟡 C",
    "D": "🟠 D",
    "F": "🔴 FAILED"
}


def format_mods(mods):
    if not mods:
        return "NM"

    result = []

    for mod in mods:
        if isinstance(mod, str):
            result.append(mod)

        elif isinstance(mod, dict):
            acronym = mod.get("acronym")

            if acronym:
                result.append(acronym)

    if not result:
        return "NM"

    return "+" + "".join(result)


class RecentCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.hybrid_command(name="recent",aliases=["r"],description="Show the most recent osu! play of a player.")
    async def recent(self,ctx: commands.Context,*,username: str = None):

        # ------------------------------------------
        # GET USERNAME
        # ------------------------------------------

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


        # ------------------------------------------
        # FETCH USER + RECENT SCORE
        # ------------------------------------------

        async with ctx.typing():

            user = await self.bot.osu.get_user(
                username
            )

            if user is None:

                await ctx.send(
                    f"Could not find osu! player `{username}`."
                )
                return


            scores = await self.bot.osu.get_recent_scores(
                user["id"],
                mode=user["playmode"],
                limit=1
            )


        if scores is None:

            await ctx.send(
                "Something went wrong while getting recent scores."
            )
            return


        if not scores:

            await ctx.send(
                f"**{user['username']}** has no recent plays."
            )
            return


        # ------------------------------------------
        # SCORE DATA
        # ------------------------------------------

        score = scores[0]

        beatmap = score["beatmap"]
        beatmapset = score["beatmapset"]

        accuracy = (
            score.get("accuracy", 0)
            * 100
        )

        rank = score.get(
            "rank",
            "?"
        )

        combo = score.get(
            "max_combo",
            0
        )

        mods = format_mods(
            score.get("mods", [])
        )

        score_value = score.get(
            "total_score",
            score.get("score", 0)
        )


        # ------------------------------------------
        # BEATMAP DATA
        # ------------------------------------------

        star_rating = beatmap.get(
            "difficulty_rating",
            0
        )


        # ------------------------------------------
        # PP + FC CALCULATION
        # ------------------------------------------

        performance = await self.bot.osu.calculate_score_performance(
            score
        )

        actual_pp = score.get("pp")

        fc_pp = None
        fc_accuracy = None

        max_combo = beatmap.get(
            "max_combo"
        )


        if performance:

            if performance.get("actual_pp") is not None:
                actual_pp = performance["actual_pp"]

            fc_pp = performance.get("fc_pp")
            fc_accuracy = performance.get("fc_accuracy")

            if performance.get("max_combo"):
                max_combo = performance["max_combo"]

            if performance.get("star_rating") is not None:
                star_rating = performance["star_rating"]


        # ------------------------------------------
        # DISPLAY VALUES
        # ------------------------------------------

        grade_display = GRADE_DISPLAY.get(
            rank,
            f"🎯 {rank}"
        )

        mode_name = MODE_NAMES.get(
            user["playmode"],
            user["playmode"]
        )


        # ------------------------------------------
        # COMBO
        # ------------------------------------------

        combo_text = f"{combo:,}x"

        if max_combo:
            combo_text += (
                f" / {max_combo:,}x"
            )


        # ------------------------------------------
        # PP
        # ------------------------------------------

        if actual_pp is not None:
            actual_pp_text = (
                f"◆ **{actual_pp:.2f}pp**"
            )
        else:
            actual_pp_text = (
                "◆ **PP unavailable**"
            )


        # ------------------------------------------
        # BEATMAP TITLE + DIFFICULTY
        # ------------------------------------------

        title = (
            f"{beatmapset['artist']} - "
            f"{beatmapset['title']}"
        )

        difficulty_name = beatmap["version"]

        beatmap_url = (
            f"https://osu.ppy.sh/"
            f"beatmaps/{beatmap['id']}"
        )


        # ------------------------------------------
        # HIT STATISTICS
        # ------------------------------------------

        statistics = score.get(
            "statistics",
            {}
        )


        def get_hit_stat(*names):

            for name in names:

                value = statistics.get(name)

                if value is not None:
                    return value

            return 0


        count_300 = get_hit_stat(
            "great",
            "count_300"
        )

        count_100 = get_hit_stat(
            "ok",
            "count_100"
        )

        count_50 = get_hit_stat(
            "meh",
            "count_50"
        )

        count_miss = get_hit_stat(
            "miss",
            "count_miss"
        )


        # ------------------------------------------
        # CREATE EMBED
        # ------------------------------------------

        embed = discord.Embed(
            description=(
                f"**[{title}]({beatmap_url})**\n"
                f"↳ **[{difficulty_name}]({beatmap_url}?diff={beatmap['id']})** · "
                f"`{star_rating:.2f}★`\n\n"

                f"**{grade_display}** · **{score_value:,}**\n"
                f"─────────────────────"
            ),
            color=OSU_PINK
        )


        embed.add_field(
            name="Accuracy",
            value=f"◈ **{accuracy:.2f}%**",
            inline=True
        )


        embed.add_field(
            name="Performance",
            value=actual_pp_text,
            inline=True
        )


        embed.add_field(
            name="Combo & Mods",
            value=(
                f"**{combo_text}** · `{mods}`"
            ),
            inline=True
        )


        embed.add_field(
            name="Hit",
            value=(
                f"`{count_300:,}`**x 300** · "
                f"`{count_100:,}`**x 100** · "
                f"`{count_50:,}`**x 50** · "
                f"`{count_miss:,}`**x Miss**"
            ),
            inline=True
        )


        if (
            fc_pp is not None
            and fc_accuracy is not None
        ):

            embed.add_field(
                name="If FC",
                value=(
                    f"◆ **{fc_pp:.2f}pp** "
                    f"@ **{fc_accuracy:.2f}%**"
                ),
                inline=False
            )


        # ------------------------------------------
        # AUTHOR
        # ------------------------------------------

        embed.set_author(
            name=(
                f"Recent {mode_name} · "
                f"{user['username']}"
            ),
            icon_url=user["avatar_url"]
        )


        # ------------------------------------------
        # THUMBNAIL
        # ------------------------------------------

        cover_url = (
            beatmapset
            .get("covers", {})
            .get("list@2x")
        )

        if cover_url:

            embed.set_thumbnail(
                url=cover_url
            )


        # ------------------------------------------
        # TIMESTAMP
        # ------------------------------------------

        ended_at = score.get(
            "ended_at"
        )

        if ended_at:

            try:

                played_time = datetime.fromisoformat(
                    ended_at.replace(
                        "Z",
                        "+00:00"
                    )
                )

                embed.timestamp = played_time

            except ValueError:
                pass


        # ------------------------------------------
        # SEND
        # ------------------------------------------

        await ctx.send(
            embed=embed
        )


async def setup(bot):

    await bot.add_cog(
        RecentCommands(bot)
    )