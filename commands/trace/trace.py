import discord
from discord.ext import commands
from discord import app_commands

from utils import (
    get_linked_user,
    MODE_NAMES,
    OSU_PINK
)

from .core import (
    get_total_pages,
    get_page_scores,
    build_pb_section,
    build_history_entry
)

from .parser import (
    BEATMAP_REGEX,
    extract_beatmap_from_message
)

class TracePaginationView(discord.ui.View):

    def __init__(
        self,
        ctx,
        user,
        beatmap,
        scores,
        mode_name,
        per_page=4
    ):

        super().__init__(timeout=900)

        self.ctx = ctx
        self.user = user
        self.beatmap = beatmap
        self.scores = scores
        self.mode_name = mode_name

        self.per_page = per_page

        self.current_page = 0

        self.total_pages = get_total_pages(
            scores
        )

        self.message = None

        self.update_buttons()


    def update_buttons(self):

        self.first_page.disabled = (
            self.current_page == 0
        )

        self.previous_page.disabled = (
            self.current_page == 0
        )

        self.next_page.disabled = (
            self.current_page
            >= self.total_pages - 1
        )

        self.last_page.disabled = (
            self.current_page
            >= self.total_pages - 1
        )


    async def interaction_check(
        self,
        interaction: discord.Interaction
    ):

        if interaction.user.id != self.ctx.author.id:

            await interaction.response.send_message(
                "Only the person who used this command can control these pages.",
                ephemeral=True
            )

            return False

        return True


    async def create_embed(self):

        if self.current_page == 0:

            page_scores = get_page_scores(
                self.scores[1:],
                0
            )

        else:

            start = 1 + (
                self.current_page
                * 4
            )

            end = start + 4

            page_scores = self.scores[start:end]

        pb = self.scores[0]

        pb_compare = None

        if len(self.scores) > 1:
            pb_compare = self.scores[1]
            _, pb_difference = build_history_entry(
                pb,
                pb_compare
            )

        beatmapset = self.beatmap["beatmapset"]

        title = (
            f"{beatmapset['artist']} - "
            f"{beatmapset['title']}"
        )

        beatmap_url = (
            f"https://osu.ppy.sh/beatmaps/"
            f"{self.beatmap['id']}"
        )

        embed = discord.Embed(
            color=OSU_PINK
        )

        embed.set_author(

            name=(
                f"Trace • "
                f"{self.user['username']}"
            ),

            icon_url=self.user["avatar_url"]

        )

        embed.description = (

            f"**[{title}]({beatmap_url})**\n"

            f"↳ **{self.beatmap['version']}**"

            f" • "

            f"`{self.beatmap['difficulty_rating']:.2f}★`"

        )

        cover = (
            beatmapset
            .get("covers", {})
            .get("list@2x")
        )

        if cover:

            embed.set_thumbnail(
                url=cover
            )

        embed.add_field(
            name="🏆 Personal Best",
            value=build_pb_section(pb),
            inline=True
        )

        embed.add_field(
            name="Changes",
            value=pb_difference if pb_compare else "*No comparison*",
            inline=True
        )

        history_column = []
        changes_column = []

        for i, score in enumerate(page_scores):

            older = None

            if i + 1 < len(page_scores):
                older = page_scores[i + 1]

            history, difference = build_history_entry(
                score,
                older
            )

            history_column.append(history)

            if older is not None:
                changes_column.append(difference)
            else:
                changes_column.append("*No comparison*")  # invisible placeholder

        
        # Force next row
        embed.add_field(
            name="\u200b",
            value="\u200b",
            inline=False
        )


        embed.add_field(
            name="Other Scores",
            value="\n\n".join(history_column),
            inline=True
        )

        embed.add_field(
            name="Changes",
            value="\n\n".join(changes_column),
            inline=True
        )

        embed.set_footer(

            text=(
                f"{self.mode_name}"
                f" • "
                f"Page "
                f"{self.current_page+1}"
                f"/{self.total_pages}"
            )

        )

        return embed
    
    @discord.ui.button(
        emoji="⏮️",
        style=discord.ButtonStyle.secondary
    )
    async def first_page(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.defer()

        self.current_page = 0

        self.update_buttons()

        embed = await self.create_embed()

        await interaction.edit_original_response(
            embed=embed,
            view=self
        )


    @discord.ui.button(
        emoji="◀️",
        style=discord.ButtonStyle.secondary
    )
    async def previous_page(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.defer()

        self.current_page -= 1

        self.update_buttons()

        embed = await self.create_embed()

        await interaction.edit_original_response(
            embed=embed,
            view=self
        )


    @discord.ui.button(
        emoji="▶️",
        style=discord.ButtonStyle.secondary
    )
    async def next_page(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.defer()

        self.current_page += 1

        self.update_buttons()

        embed = await self.create_embed()

        await interaction.edit_original_response(
            embed=embed,
            view=self
        )


    @discord.ui.button(
        emoji="⏭️",
        style=discord.ButtonStyle.secondary
    )
    async def last_page(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        await interaction.response.defer()

        self.current_page = (
            self.total_pages - 1
        )

        self.update_buttons()

        embed = await self.create_embed()

        await interaction.edit_original_response(
            embed=embed,
            view=self
        )


    async def on_timeout(self):

        for item in self.children:
            item.disabled = True

        if self.message:

            try:

                await self.message.edit(
                    view=self
                )

            except discord.HTTPException:
                pass

class TraceCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.hybrid_command(
        name="trace",
        aliases=["tr"],
        description="Show score progression on a beatmap."
    )
    @app_commands.describe(
        username="osu! username",
        beatmap="Beatmap URL or beatmap ID"
    )
    async def trace(
        self,
        ctx: commands.Context,
        username: str = None,
        beatmap: str = None,
        *,
        query: str = None
    ):
        

        # ------------------------------------------
        # FIND BEATMAP
        # ------------------------------------------

        beatmap_id = None

        # Prefix command:
        # !trace https://...
        # ------------------------------------------
        # PREFIX COMMAND PARSER
        # ------------------------------------------

        if ctx.interaction is None:

            query = ctx.view.buffer[ctx.view.index:].strip()

            username = None
            beatmap = None

            #
            # Beatmap URL
            #

            match = BEATMAP_REGEX.search(query)

            if match:

                beatmap = match.group(0)

                query = query.replace(
                    match.group(0),
                    ""
                ).strip()

            #
            # Beatmap ID
            #

            if beatmap is None:

                tokens = query.split()

                for token in tokens:

                    if token.isdigit():

                        beatmap = token

                        query = query.replace(
                            token,
                            ""
                        ).strip()

                        break

            #
            # Remaining text is username
            #

            if query:

                username = query


        # URL / Beatmap ID
        if beatmap:

            match = BEATMAP_REGEX.search(beatmap)

            if match:

                beatmap_id = int(match.group(1))

            elif beatmap.isdigit():

                beatmap_id = int(beatmap)


        # ------------------------------------------
        # Reply detection
        # ------------------------------------------

        if beatmap_id is None and ctx.message:

            reference = ctx.message.reference

            if reference and reference.resolved:

                beatmap_id = await extract_beatmap_from_message(
                    reference.resolved
                )

        # ------------------------------------------
        # RECENT CHANNEL HISTORY
        # ------------------------------------------

        
        if beatmap_id is None:

            async for message in ctx.channel.history(limit=50):

                candidates = [message]

                if message.reference:

                    replied = message.reference.resolved

                    if replied is None:

                        try:
                            replied = await ctx.channel.fetch_message(
                                message.reference.message_id
                            )

                        except (
                            discord.NotFound,
                            discord.Forbidden,
                            discord.HTTPException
                        ):
                            replied = None

                    if replied:
                        candidates.append(replied)

                for candidate in candidates:

                    beatmap_id = await extract_beatmap_from_message(
                        candidate
                    )

                    if beatmap_id is not None:
                        break

                if beatmap_id is not None:
                    break

                    


        # ------------------------------------------
        # USERNAME
        # ------------------------------------------

        if username is None:

            linked = get_linked_user(
                ctx.author.id
            )

            if linked is None:

                await ctx.send(
                    "You haven't linked an osu! account yet.\nUse `!link <username>` first."
                )

                return

            username = str(
                linked["osu_id"]
            )


        # ------------------------------------------
        # FETCH USER
        # ------------------------------------------

        if beatmap_id is None:

            await ctx.send(
                "Please provide a beatmap URL or reply to a message containing one."
            )
            return

        if ctx.interaction:
            await ctx.defer()

        else:
            async with ctx.typing():
                pass

        user = await self.bot.osu.get_user(username)

        if user is None:

            await ctx.send(
                f"Could not find osu! player `{username}`."
            )

            return


        scores = await self.bot.osu.get_trace_scores(
            user["id"],
            beatmap_id,
            mode=user["playmode"]
        )

        beatmap = await self.bot.osu.get_beatmap(
            beatmap_id
        )

        if scores is None:

            await ctx.send(
                "Failed to fetch trace scores."
            )

            return
        
        if beatmap is None:

            await ctx.send(
                "Failed to fetch beatmap."
            )

            return


        if not scores:

            await ctx.send(
                f"**{user['username']}** has no scores on this beatmap."
            )

            return


        # ------------------------------------------
        # SORT
        # ------------------------------------------

        pb = max(
            scores,
            key=lambda s: s.get("pp") or 0
        )

        history_scores = [
            s for s in scores
            if s is not pb
        ]

        history_scores.sort(
            key=lambda s: s["created_at"],
            reverse=True
        )

        scores = [pb] + history_scores

        mode_name = MODE_NAMES.get(
            user["playmode"],
            user["playmode"]
        )

        view = TracePaginationView(
            ctx=ctx,
            user=user,
            beatmap=beatmap,
            scores=scores,
            mode_name=mode_name,
            per_page=4
        )

        embed = await view.create_embed()

        message = await ctx.send(
            embed=embed,
            view=view
        )

        view.message = message


async def setup(bot):

    await bot.add_cog(
        TraceCommands(bot)
    )