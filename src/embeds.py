"""ALL embed construction lives here. Cogs NEVER build embeds."""

import datetime
import random

import discord

from src.constants import (
    CELEBRATION_MESSAGES,
    COLOR_BOARD,
    COLOR_COMPLETE,
    COLOR_DEFAULT_TASK,
    COLOR_OVERDUE,
    SHAME_MESSAGES,
    SNOOZE_MESSAGES,
    STATUS_EMOJI,
)


def build_task_embed(
    description: str,
    status: str,
    due_date: str | None,
    recurrence: str = "none",
) -> discord.Embed:
    """Build an embed for a single task (pending, completed, or overdue)."""
    now = datetime.datetime.now(datetime.timezone.utc)

    if status == "completed":
        color = COLOR_COMPLETE
        title = f"{STATUS_EMOJI['completed']} [DONE] Task"
        desc = f"~~{description}~~"
    elif status == "overdue":
        color = COLOR_OVERDUE
        title = f"{STATUS_EMOJI['overdue']} OVERDUE: Task"
        desc = description
    else:  # pending
        color = COLOR_DEFAULT_TASK
        title = f"{STATUS_EMOJI['pending']} [PENDING] Task"
        desc = description

    embed = discord.Embed(title=title, description=desc, color=color, timestamp=now)

    if due_date:
        embed.add_field(name="Due Date", value=due_date, inline=True)

    if recurrence != "none":
        embed.add_field(name="Recurrence", value=recurrence.capitalize(), inline=True)

    return embed


def build_board_embed(users_data: list[dict]) -> discord.Embed:
    """Build the accountability board embed.

    users_data: list of dicts with keys: name, score, tasks
        where tasks is a list of dicts with keys: description, status
    Users are sorted by score descending.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    embed = discord.Embed(
        title="Accountability Board",
        color=COLOR_BOARD,
        timestamp=now,
    )

    sorted_users = sorted(users_data, key=lambda u: u["score"], reverse=True)

    for user in sorted_users:
        task_lines = []
        for task in user["tasks"]:
            emoji = STATUS_EMOJI.get(task["status"], "")
            task_lines.append(f"{emoji} {task['description']}")

        task_text = "\n".join(task_lines) if task_lines else "*No tasks*"
        field_name = f"**{user['name']}** — \U0001f3c6 {user['score']} pts"
        embed.add_field(name=field_name, value=task_text, inline=False)

    embed.set_footer(text="Last updated")
    return embed


def build_celebration_embed(
    user_name: str, task_description: str
) -> discord.Embed:
    """Build a celebration embed for a completed task."""
    now = datetime.datetime.now(datetime.timezone.utc)
    message = random.choice(CELEBRATION_MESSAGES).format(
        user=user_name, task=task_description
    )
    embed = discord.Embed(
        title="\U0001f389 Task Completed!",
        description=message,
        color=COLOR_COMPLETE,
        timestamp=now,
    )
    return embed


def build_shame_embed(
    user_name: str, overdue_tasks: list[str]
) -> discord.Embed:
    """Build a shame embed for overdue tasks."""
    now = datetime.datetime.now(datetime.timezone.utc)
    task_list = "\n".join(f"• {t}" for t in overdue_tasks)
    message = random.choice(SHAME_MESSAGES).format(
        user=user_name, tasks=task_list
    )
    embed = discord.Embed(
        title="\U0001f6a8 Wall of Shame",
        description=message,
        color=COLOR_OVERDUE,
        timestamp=now,
    )
    return embed


def build_snooze_embed(
    user_name: str, task_description: str
) -> discord.Embed:
    """Build a notification embed for a snoozed task."""
    now = datetime.datetime.now(datetime.timezone.utc)
    message = random.choice(SNOOZE_MESSAGES).format(
        user=user_name, task=task_description
    )
    embed = discord.Embed(
        title="\U000023f3 Task Snoozed",
        description=message,
        color=COLOR_DEFAULT_TASK,
        timestamp=now,
    )
    return embed


def build_welcome_embed(channel_mention: str) -> discord.Embed:
    """Build the welcome embed sent to a user's new private channel."""
    now = datetime.datetime.now(datetime.timezone.utc)
    embed = discord.Embed(
        title="\U0001f44b Welcome to Your Task Inbox!",
        description=(
            "This is your private task channel. "
            "New tasks will appear here with buttons to manage them.\n\n"
            "**How it works:**\n"
            "\U0001f7e2 **Mark Done** — Complete the task (+10 pts)\n"
            "\U000023f3 **Snooze** — Push it back 1 day (-2 pts)\n\n"
            "Add tasks with `/task add` and stay accountable!"
        ),
        color=COLOR_DEFAULT_TASK,
        timestamp=now,
    )
    return embed


def build_info_embed() -> discord.Embed:
    """Build the general bot instructions/info embed."""
    now = datetime.datetime.now(datetime.timezone.utc)
    embed = discord.Embed(
        title="\U0001f916 Bother Bot — How It Works",
        description=(
            "Welcome to the accountability server! I am here to make sure you get your stuff done, "
            "or shame you if you don't. Here is everything you need to know."
        ),
        color=COLOR_DEFAULT_TASK,
        timestamp=now,
    )
    embed.add_field(
        name="\U0001f3ab Getting Started",
        value="Use `/opt-in` in any channel to register. I will create a private task channel just for you.",
        inline=False
    )
    embed.add_field(
        name="\U0001f4dd Adding Tasks",
        value=(
            "Use `/task add` to create a task. You can use natural language for the due date "
            "(e.g., 'tomorrow', 'next friday', 'Oct 15'). If you don't set one, it defaults to tomorrow."
        ),
        inline=False
    )
    embed.add_field(
        name="\U0001f3ae The Game (Points)",
        value=(
            "\U0001f7e2 **Complete a task:** +10 points\n"
            "\U000023f3 **Snooze a task:** -2 points\n"
            "\U0001f534 **Overdue task:** -5 points (per day!)"
        ),
        inline=False
    )
    embed.add_field(
        name="\U0001f4e3 Board & Consequences",
        value=(
            "• Your score and active tasks are tracked on the `#accountability-board` in real-time.\n"
            "• Snoozed tasks are publicly called out in the meat grinder channel.\n"
            "• At 9 PM ET every day, anyone with pending or overdue tasks goes on the **Wall of Shame**.\n"
            "• Anyone can use `/prod @user [task]` to mock you about an active task."
        ),
        inline=False
    )
    return embed
