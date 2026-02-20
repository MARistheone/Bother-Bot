"""Bot init, tree sync, cog loading. NOTHING ELSE goes here."""

import asyncio
import os
import logging

import discord
from discord.ext import commands
from dotenv import load_dotenv

from src.db import init_db
from src.views import TaskView

load_dotenv()

TOKEN = os.environ["DISCORD_TOKEN"]
GUILD_ID = os.environ.get("GUILD_ID")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)

log = logging.getLogger("bother-bot")


@bot.event
async def on_ready():
    """Sync command tree and log startup."""
    if GUILD_ID:
        guild = discord.Object(id=int(GUILD_ID))
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
        log.info("Synced command tree to guild %s", GUILD_ID)
    else:
        await bot.tree.sync()
        log.info("Synced command tree globally")

    log.info("Logged in as %s (ID: %s)", bot.user, bot.user.id)


async def setup_hook():
    """Register persistent views and load cogs."""
    await init_db()

    # Re-register persistent TaskViews for existing tasks.
    # Phase 2 will query active task IDs from the DB and register
    # a TaskView for each. For now, the pattern is established.
    # Example: bot.add_view(TaskView(task_id=some_id))

    cog_extensions = [
        "src.cogs.tasks",
        "src.cogs.accountability",
        "src.cogs.loops",
    ]
    for ext in cog_extensions:
        try:
            await bot.load_extension(ext)
            log.info("Loaded extension: %s", ext)
        except commands.ExtensionNotFound:
            log.warning("Extension not found (skipped): %s", ext)


bot.setup_hook = setup_hook


def main():
    """Entry point for running the bot."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    bot.run(TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
