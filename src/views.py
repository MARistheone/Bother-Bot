"""ALL discord.ui.View and Button subclasses live here."""

import discord


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
        """Stub — wired to full logic in Phase 2 (cogs/tasks.py)."""
        await interaction.response.send_message(
            "Task marked as done!", ephemeral=True
        )

    async def snooze_callback(self, interaction: discord.Interaction) -> None:
        """Stub — wired to full logic in Phase 2 (cogs/tasks.py)."""
        await interaction.response.send_message(
            "Task snoozed by 1 day!", ephemeral=True
        )
