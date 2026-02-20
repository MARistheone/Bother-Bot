"""/task command group and button interaction callbacks. Delegates to embeds.py, views.py, db.py."""

import datetime
import logging
import dateparser

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

        # Parse or default due_date
        now = datetime.datetime.now(datetime.timezone.utc)
        if due_date:
            # Use dateparser to support things like "tomorrow", "next tuesday", "in 3 days"
            parsed_date = dateparser.parse(due_date, settings={'TIMEZONE': 'UTC', 'RETURN_AS_TIMEZONE_AWARE': True})
            if parsed_date:
                due_date_str = parsed_date.strftime("%Y-%m-%d")
            else:
                due_date_str = due_date # fallback in case dateparser fails
        else:
            tomorrow = now + datetime.timedelta(days=1)
            due_date_str = tomorrow.strftime("%Y-%m-%d")

        # Create task in DB
        task_id = await db.add_task(uid, description, due_date_str, recurrence_val)

        # Build embed and view
        embed = build_task_embed(description, "pending", due_date_str, recurrence_val)
        view = TaskView(task_id=task_id)

        # Send to user's private channel
        channel = self.bot.get_channel(int(user["private_channel_id"]))
        if not channel:
            await interaction.response.send_message(
                "Couldn't find your task channel. Contact an admin.", ephemeral=True
            )
            return

        try:
            msg = await channel.send(embed=embed, view=view)
            await db.update_task_message_id(task_id, str(msg.id))
        except (discord.Forbidden, discord.HTTPException) as e:
            log.error("Failed to send task %d to channel: %s", task_id, e)
            await interaction.response.send_message(
                "Task saved but couldn't send to your channel. Contact an admin.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"Task added! Check {channel.mention}", ephemeral=True
        )
        log.info("Task %d created for user %s: %s", task_id, uid, description)

        # Auto-refresh the board
        try:
            from src.cogs.accountability import refresh_board
            await refresh_board(self.bot)
        except Exception as e:
            log.warning("Failed to refresh board after task %d add: %s", task_id, e)

    @task_group.command(name="edit", description="Edit an existing task")
    @app_commands.describe(
        task="The task you want to edit",
        new_description="The new description (optional)",
        new_due_date="The new due date (e.g., 'tomorrow', 'next friday') (optional)",
        new_recurrence="The new recurrence (optional)"
    )
    @app_commands.choices(new_recurrence=[
        app_commands.Choice(name="None", value="none"),
        app_commands.Choice(name="Daily", value="daily"),
        app_commands.Choice(name="Weekly", value="weekly"),
    ])
    async def task_edit(
        self,
        interaction: discord.Interaction,
        task: str,
        new_description: str | None = None,
        new_due_date: str | None = None,
        new_recurrence: app_commands.Choice[str] | None = None,
    ) -> None:
        uid = str(interaction.user.id)

        # Match task string to actual task for this user
        pending = await db.get_tasks_for_user(uid, status="pending")
        overdue = await db.get_tasks_for_user(uid, status="overdue")
        all_active = pending + overdue

        target = next((t for t in all_active if t["description"] == task), None)
        if not target:
            await interaction.response.send_message(
                "I couldn't find that active task. Did you already complete it?",
                ephemeral=True
            )
            return

        task_id = target["id"]
        description = new_description if new_description is not None else target["description"]
        recurrence_val = new_recurrence.value if new_recurrence is not None else target["recurrence"]

        due_date_str = target["due_date"]
        if new_due_date:
            parsed_date = dateparser.parse(new_due_date, settings={'TIMEZONE': 'UTC', 'RETURN_AS_TIMEZONE_AWARE': True})
            if parsed_date:
                due_date_str = parsed_date.strftime("%Y-%m-%d")
            else:
                due_date_str = new_due_date

        await db.update_task_details(task_id, description, due_date_str, recurrence_val)

        # Edit the message if possible
        if target["message_id"]:
            user_data = await db.get_user(uid)
            if user_data and user_data["private_channel_id"]:
                channel = self.bot.get_channel(int(user_data["private_channel_id"]))
                if channel:
                    try:
                        msg = await channel.fetch_message(int(target["message_id"]))
                        embed = build_task_embed(
                            description,
                            target["status"],
                            due_date_str,
                            recurrence_val
                        )
                        await msg.edit(embed=embed)
                    except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
                        log.warning("Failed to edit task message for task %d: %s", task_id, e)

        await interaction.response.send_message("Task updated!", ephemeral=True)

        try:
            from src.cogs.accountability import refresh_board
            await refresh_board(self.bot)
        except Exception as e:
            log.warning("Failed to refresh board after task edit: %s", e)

    @task_edit.autocomplete("task")
    async def task_edit_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str,
    ) -> list[app_commands.Choice[str]]:
        user = interaction.namespace.user if hasattr(interaction.namespace, 'user') else interaction.user
        if not user:
            return []
        
        uid = str(user.id)
        pending = await db.get_tasks_for_user(uid, status="pending")
        overdue = await db.get_tasks_for_user(uid, status="overdue")
        active_tasks = pending + overdue
        
        choices = []
        for t in active_tasks:
            desc = t["description"]
            if current.lower() in desc.lower():
                label = desc[:100]
                choices.append(app_commands.Choice(name=label, value=desc))
            if len(choices) >= 25:
                break
        return choices


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(TasksCog(bot))
