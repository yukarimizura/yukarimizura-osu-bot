import asyncio
import aiohttp

import discord
from discord.ext import commands
from api.osu_api import OsuAPI

from config import DISCORD_TOKEN
from commands import EXTENSIONS


intents = discord.Intents.all()


class OsuBot(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix="+",
            intents=intents
        )

        self.osu = OsuAPI()

    async def setup_hook(self):

        await self.osu.start()

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

    async def close(self):

        await self.osu.close()

        await super().close()


async def main():

    bot = OsuBot()

    async with bot:

        await bot.start(
            DISCORD_TOKEN
        )


if __name__ == "__main__":

    asyncio.run(main())