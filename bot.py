import asyncio

import discord
from discord.ext import commands

from config import DISCORD_TOKEN
from commands import EXTENSIONS


intents = discord.Intents.all()


class OsuBot(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix="+",
            intents=intents
        )


    async def setup_hook(self):

        for extension in EXTENSIONS:

            await self.load_extension(
                extension
            )

            print(
                f"Loaded: {extension}"
            )


        synced = await self.tree.sync()

        print(
            f"Synced {len(synced)} slash commands."
        )


    async def on_ready(self):

        print(
            f"{self.user} has connected to Discord!"
        )


async def main():

    bot = OsuBot()

    async with bot:

        await bot.start(
            DISCORD_TOKEN
        )


if __name__ == "__main__":

    asyncio.run(main())