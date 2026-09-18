import math
import discord
from discord.ext import commands

from utils import (
    get_linked_user,
    MODE_NAMES,
    OSU_PINK,
    GRADE_DISPLAY,
    format_mods
)


class TopPaginationView(discord.ui.View):

    def __init__(self, bot, ctx, user, scores, mode_name, per_page=5):
        super().__init__(timeout=900)
        self.ctx = ctx
        self.bot = bot
        self.user = user
        self.scores = scores
        self.mode_name = mode_name
        self.per_page = per_page
        self.current_page = 0
        self.total_pages = math.ceil(len(scores) / per_page)
        self.message = None
        self.update_buttons()

    def update_buttons(self):
        self.first_page.disabled = self.current_page == 0
        self.previous_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page >= self.total_pages - 1
        self.last_page.disabled = self.current_page >= self.total_pages - 1

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message(
                "Only the person who used this command can control these pages.",
                ephemeral=True
            )
            return False
        return True

    async def create_embed(self):
        start = self.current_page * self.per_page
        end = start + self.per_page
        page_scores = self.scores[start:end]

        embed = discord.Embed(color=OSU_PINK)
        embed.set_author(
            name=f"Top {len(self.scores)} {self.mode_name} plays · {self.user['username']}",
            icon_url=self.user["avatar_url"]
        )

        descriptions = []
        for local_index, score in enumerate(page_scores, start=start + 1):
            beatmap = score["beatmap"]
            beatmapset = score["beatmapset"]
            title = f"{beatmapset['artist']} - {beatmapset['title']}"
            difficulty = beatmap["version"]
            beatmap_url = f"https://osu.ppy.sh/beatmaps/{beatmap['id']}"

            pp = score.get("pp")
            accuracy = score.get("accuracy", 0) * 100
            combo = score.get("max_combo", 0)
            rank = score.get("rank", "?")
            mods = format_mods(score.get("mods", []))
            star_rating = beatmap.get("difficulty_rating", 0)
            max_combo = beatmap.get("max_combo")

            # Calculate modded star rating and accurate max combo
            performance = await self.bot.osu.calculate_score_performance(score)
            if performance:
                if performance.get("star_rating") is not None:
                    star_rating = performance["star_rating"]
                if performance.get("max_combo"):
                    max_combo = performance["max_combo"]

            combo_text = f"{combo:,}x"
            if max_combo:
                combo_text += f"/{max_combo:,}x"

            pp_text = f"**{pp:.2f}pp**" if pp is not None else "**N/A pp**"
            grade = GRADE_DISPLAY.get(rank, rank)

            play_text = (
                f"**#{local_index}** · **[{title}]({beatmap_url})**\n"
                f"↳ **{difficulty}** · `{star_rating:.2f}★`\n"
                f"{grade} · {pp_text} · **{accuracy:.2f}%** · **{combo_text}** · `{mods}`"
            )
            descriptions.append(play_text)

        embed.description = "\n\n".join(descriptions)
        embed.set_footer(text=f"{self.mode_name} · Page {self.current_page + 1}/{self.total_pages}")
        return embed

    @discord.ui.button(emoji="⏮️", style=discord.ButtonStyle.secondary)
    async def first_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = 0
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.button(emoji="◀️", style=discord.ButtonStyle.secondary)
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page -= 1
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.button(emoji="▶️", style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page += 1
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.edit_original_response(embed=embed, view=self)

    @discord.ui.button(emoji="⏭️", style=discord.ButtonStyle.secondary)
    async def last_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = self.total_pages - 1
        self.update_buttons()
        embed = await self.create_embed()
        await interaction.edit_original_response(embed=embed, view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


class TopCommands(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="top", aliases=["best"], description="Show the top osu! plays of a player.")
    async def top(self, ctx: commands.Context, *, username: str = None):
        if username is None:
            linked_user = get_linked_user(ctx.author.id)
            if linked_user is None:
                await ctx.send("You haven't linked an osu! account yet. Use `!link <username>` first.")
                return
            username = str(linked_user["osu_id"])

        async with ctx.typing():
            user = await self.bot.osu.get_user(username)
            if user is None:
                await ctx.send(f"Could not find osu! player `{username}`.")
                return

            scores = await self.bot.osu.get_best_scores(
                user["id"],
                mode=user["playmode"],
                limit=100
            )

        if scores is None:
            await ctx.send("Something went wrong while getting top plays.")
            return

        if not scores:
            await ctx.send(f"**{user['username']}** has no top plays.")
            return

        mode_name = MODE_NAMES.get(user["playmode"], user["playmode"])
        view = TopPaginationView(
            bot=self.bot,
            ctx=ctx,
            user=user,
            scores=scores,
            mode_name=mode_name,
            per_page=5
        )

        embed = await view.create_embed()
        message = await ctx.send(embed=embed, view=view)
        view.message = message


async def setup(bot):
    await bot.add_cog(TopCommands(bot))