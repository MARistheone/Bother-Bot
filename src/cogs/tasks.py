"""/task command group and button interaction callbacks. Delegates to embeds.py, views.py, db.py."""

import datetime
import logging

import discord
from discord import app_commands
from discord.ext import commands

from src import db
from src.embeds import build_task_embed
from src.views import TaskView

log = logging.getLogger("bother-bot")


class TasksCog(commands.Cog):
    """Handles task creation and button interactions."""

    task_group = app_commands.Group(name="task", description="Task management commands")

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @task_group.command(name="add", description="Add a new task")
    @app_commands.describe(
        description="What do you need to do?",
        due_date="Due date (YYYY-MM-DD). Defaults to tomorrow.",
        recurrence="How often does this repeat?",
    )
    @app_commands.choices(recurrence=[
        app_commands.Choice(name="None", value="none"),
        app_commands.Choice(name="Daily", value="daily"),
        app_commands.Choice(name="Weekly", value="weekly"),
    ])
    async def task_add(
        self,
        interaction: discord.Interaction,
        description: str,
        due_date: str | None = None,
        recurrence: app_commands.Choice[str] | None = None,
    ) -> None:
        uid = str(interaction.user.id)
        recurrence_val = recurrence.value if recurrence else "none"

        # Check registration
        user = await db.get_user(uid)
        if not user or not user["private_channel_id"]:
            await interaction.response.send_message(
                "You need to `/opt-in` first!", ephemeral=True
            )
            return

        # Default due_date to tomorrow
        if not due_date:
            tomorrow = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
            due_date = tomorrow.strftime("%Y-%m-%d")

        # Create task in DB
        task_id = await db.add_task(uid, description, due_date, recurrence_val)

        # Build embed and view
        embed = build_task_embed(description, "pending", due_date, recurrence_val)
        view = TaskView(task_id=task_id)

        # Send to user's private channel
        channel = self.bot.get_channel(int(user["private_channel_id"]))
        if not channel:
            await interaction.response.send_message(
                "Couldn't find your task channel. Contact an admin.", ephemeral=True
            )
            return

        msg = await channel.send(embed=embed, view=view)
        await db.update_task_message_id(task_id, str(msg.id))

        await interaction.response.send_message(
            f"Task added! Check {channel.mention}", ephemeral=True
        )
        log.info("Task %d created for user %s: %s", task_id, uid, description)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TasksCog(bot))
