"""ALL discord.ui.View and Button subclasses live here."""

import datetime
import logging

import discord

from src import db
from src.embeds import build_task_embed, build_celebration_embed
from src.scoring import calculate_completion_score, calculate_snooze_penalty

log = logging.getLogger("bother-bot")


class TaskView(discord.ui.View):
    """Persistent view with Done and Snooze buttons for a task.

    timeout=None ensures this view survives bot restarts when
    re-registered in setup_hook().
    """

    def __init__(self, task_id: int):
        super().__init__(timeout=None)
        self.task_id = task_id

        done_button = discord.ui.Button(
            style=discord.ButtonStyle.success,
            label="Mark Done",
            custom_id=f"done_{task_id}",
        )
        done_button.callback = self.done_callback
        self.add_item(done_button)

        snooze_button = discord.ui.Button(
            style=discord.ButtonStyle.secondary,
            label="Snooze (1 Day)",
            custom_id=f"snooze_{task_id}",
        )
        snooze_button.callback = self.snooze_callback
        self.add_item(snooze_button)

    async def done_callback(self, interaction: discord.Interaction) -> None:
        """Mark the task as completed, update score, edit embed, remove buttons."""
        task = await db.get_task(self.task_id)
        if not task:
            await interaction.response.send_message("Task not found.", ephemeral=True)
            return

        if task["status"] == "completed":
            await interaction.response.send_message(
                "This task is already done!", ephemeral=True
            )
            return

        uid = task["discord_id"]

        # Update DB
        await db.update_task_status(self.task_id, "completed")
        score_delta = calculate_completion_score()
        await db.update_score(uid, score_delta)

        # Edit the message: green embed, no buttons
        embed = build_task_embed(
            task["description"], "completed", task["due_date"], task["recurrence"]
        )
        await interaction.response.edit_message(embed=embed, view=None)

        # Send celebration to meat grinder (if configured)
        meat_grinder_id = await db.get_config("meat_grinder_channel_id")
        if meat_grinder_id:
            channel = interaction.client.get_channel(int(meat_grinder_id))
            if channel:
                member = interaction.guild.get_member(int(uid))
                name = member.display_name if member else f"User {uid}"
                celeb_embed = build_celebration_embed(name, task["description"])
                await channel.send(embed=celeb_embed)

        # Auto-refresh the board
        from src.cogs.accountability import refresh_board
        await refresh_board(interaction.client)

        log.info("Task %d completed by %s (+%d pts)", self.task_id, uid, score_delta)

    async def snooze_callback(self, interaction: discord.Interaction) -> None:
        """Snooze the task by 1 day, deduct points, update embed."""
        task = await db.get_task(self.task_id)
        if not task:
            await interaction.response.send_message("Task not found.", ephemeral=True)
            return

        if task["status"] == "completed":
            await interaction.response.send_message(
                "This task is already done!", ephemeral=True
            )
            return

        uid = task["discord_id"]

        # Calculate new due date
        if task["due_date"]:
            try:
                current_due = datetime.datetime.strptime(task["due_date"], "%Y-%m-%d")
            except ValueError:
                current_due = datetime.datetime.now(datetime.timezone.utc)
        else:
            current_due = datetime.datetime.now(datetime.timezone.utc)

        new_due = current_due + datetime.timedelta(days=1)
        new_due_str = new_due.strftime("%Y-%m-%d")

        # Update DB
        await db.update_task_due_date(self.task_id, new_due_str)
        # Reset status to pending if it was overdue
        if task["status"] == "overdue":
            await db.update_task_status(self.task_id, "pending")
        score_delta = calculate_snooze_penalty()
        await db.update_score(uid, score_delta)

        # Edit the message with updated due date
        embed = build_task_embed(
            task["description"], "pending", new_due_str, task["recurrence"]
        )
        await interaction.response.edit_message(embed=embed, view=self)

        # Auto-refresh the board
        from src.cogs.accountability import refresh_board
        await refresh_board(interaction.client)

        log.info(
            "Task %d snoozed by %s to %s (%d pts)",
            self.task_id, uid, new_due_str, score_delta,
        )
