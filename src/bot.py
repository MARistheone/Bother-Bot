"""Bot init, tree sync, cog loading. NOTHING ELSE goes here."""

import os
import logging

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

# MUST load dotenv before importing src modules so they can read DB_PATH
load_dotenv()

from src.db import init_db, get_active_task_ids
from src.views import TaskView

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
    """Sync command tree, refresh board, and log startup."""
    if GUILD_ID:
        guild = discord.Object(id=int(GUILD_ID))
        bot.tree.copy_global_to(guild=guild)
        await bot.tree.sync(guild=guild)
        log.info("Synced command tree to guild %s", GUILD_ID)
    else:
        await bot.tree.sync()
        log.info("Synced command tree globally")

    # Refresh the board on startup to ensure it's current after restart
    try:
        from src.cogs.accountability import refresh_board
        await refresh_board(bot)
        log.info("Board refreshed on startup")
    except Exception as e:
        log.warning("Failed to refresh board on startup: %s", e)

    log.info("Logged in as %s (ID: %s)", bot.user, bot.user.id)


async def setup_hook():
    """Register persistent views and load cogs."""
    await init_db()

    # Re-register persistent TaskViews so buttons survive restarts
    task_ids = await get_active_task_ids()
    for tid in task_ids:
        bot.add_view(TaskView(task_id=tid))
    log.info("Re-registered %d persistent TaskViews", len(task_ids))

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
        except commands.ExtensionFailed as e:
            log.error("Extension failed to load: %s — %s", ext, e)


bot.setup_hook = setup_hook


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
) -> None:
    """Global handler for unhandled slash command errors."""
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "You don't have permission to use this command.", ephemeral=True
        )
    elif isinstance(error, app_commands.CommandOnCooldown):
        await interaction.response.send_message(
            f"Slow down! Try again in {error.retry_after:.0f}s.", ephemeral=True
        )
    else:
        log.error("Unhandled command error in /%s: %s", interaction.command.name if interaction.command else "unknown", error)
        if not interaction.response.is_done():
            await interaction.response.send_message(
                "Something went wrong. Try again later.", ephemeral=True
            )


def main():
    """Entry point for running the bot."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    # Suppress noisy discord.py gateway/heartbeat logs
    logging.getLogger("discord").setLevel(logging.WARNING)
    logging.getLogger("discord.http").setLevel(logging.WARNING)

    bot.run(TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
