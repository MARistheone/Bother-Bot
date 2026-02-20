"""All discord.ext.tasks loops. Overdue checker (hourly), Wall of Shame (9PM), Daily Reset (midnight)."""

import datetime
import logging
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks

from src import db
from src.embeds import build_task_embed, build_shame_embed
from src.scoring import calculate_days_overdue, calculate_overdue_penalty
from src.views import TaskView

log = logging.getLogger("bother-bot")

TZ = ZoneInfo("America/New_York")


class LoopsCog(commands.Cog):
    """Automated loops: overdue checker, Wall of Shame, daily reset."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self) -> None:
        self.check_overdue.start()
        self.wall_of_shame.start()
        self.daily_reset.start()

    async def cog_unload(self) -> None:
        self.check_overdue.cancel()
        self.wall_of_shame.cancel()
        self.daily_reset.cancel()

    # ── Overdue Checker (hourly) ─────────────────────────────────

    @tasks.loop(hours=1)
    async def check_overdue(self) -> None:
        """Mark pending tasks past due as overdue, deduct points, update embeds."""
        candidates = await db.get_overdue_candidates()
        if not candidates:
            return

        board_dirty = False
        now = datetime.datetime.now(datetime.timezone.utc)

        for task in candidates:
            task_id = task["id"]
            uid = task["discord_id"]

            # Mark overdue
            await db.update_task_status(task_id, "overdue")

            # Calculate and apply penalty
            due_dt = datetime.datetime.strptime(task["due_date"], "%Y-%m-%d")
            days = calculate_days_overdue(due_dt, now)
            if days > 0:
                penalty = calculate_overdue_penalty(days)
                await db.update_score(uid, penalty)

            # Update the embed in the user's private channel
            if task["message_id"]:
                user = await db.get_user(uid)
                if user and user["private_channel_id"]:
                    channel = self.bot.get_channel(int(user["private_channel_id"]))
                    if channel:
                        try:
                            msg = await channel.fetch_message(int(task["message_id"]))
                            embed = build_task_embed(
                                task["description"],
                                "overdue",
                                task["due_date"],
                                task["recurrence"],
                            )
                            await msg.edit(embed=embed)
                        except discord.NotFound:
                            log.warning("Task %d message not found in channel", task_id)
                        except (discord.Forbidden, discord.HTTPException) as e:
                            log.warning("Failed to update task %d embed: %s", task_id, e)

            board_dirty = True
            log.info("Task %d marked overdue for user %s", task_id, uid)

        if board_dirty:
            try:
                from src.cogs.accountability import refresh_board
                await refresh_board(self.bot)
            except Exception as e:
                log.warning("Failed to refresh board after overdue check: %s", e)

    @check_overdue.before_loop
    async def before_check_overdue(self) -> None:
        await self.bot.wait_until_ready()

    # ── Wall of Shame (9PM ET daily) ─────────────────────────────

    @tasks.loop(time=datetime.time(hour=21, minute=0, tzinfo=TZ))
    async def wall_of_shame(self) -> None:
        """Post shame embeds for users with pending/overdue tasks."""
        meat_grinder_id = await db.get_config("meat_grinder_channel_id")
        if not meat_grinder_id:
            return

        channel = self.bot.get_channel(int(meat_grinder_id))
        if not channel:
            return

        shame_tasks = await db.get_pending_tasks_due_today()
        if not shame_tasks:
            return

        # Group by user
        grouped: dict[str, list[str]] = {}
        for task in shame_tasks:
            uid = task["discord_id"]
            if uid not in grouped:
                grouped[uid] = []
            grouped[uid].append(task["description"])

        for uid, task_descs in grouped.items():
            guild = channel.guild
            member = guild.get_member(int(uid))
            name = member.display_name if member else f"User {uid}"

            embed = build_shame_embed(name, task_descs)
            try:
                await channel.send(
                    content=f"<@{uid}>",
                    embed=embed,
                )
                log.info("Wall of Shame posted for user %s (%d tasks)", uid, len(task_descs))
            except (discord.Forbidden, discord.HTTPException) as e:
                log.error("Failed to send Wall of Shame for user %s: %s", uid, e)

    @wall_of_shame.before_loop
    async def before_wall_of_shame(self) -> None:
        await self.bot.wait_until_ready()

    # ── Daily Reset (midnight ET) ────────────────────────────────

    @tasks.loop(time=datetime.time(hour=0, minute=0, tzinfo=TZ))
    async def daily_reset(self) -> None:
        """Regenerate completed recurring tasks for the next cycle."""
        completed = await db.get_completed_recurring_tasks()
        if not completed:
            return

        for task in completed:
            uid = task["discord_id"]
            recurrence = task["recurrence"]

            # Calculate next due date
            if task["due_date"]:
                try:
                    base = datetime.datetime.strptime(task["due_date"], "%Y-%m-%d")
                except ValueError:
                    base = datetime.datetime.now(datetime.timezone.utc)
            else:
                base = datetime.datetime.now(datetime.timezone.utc)

            if recurrence == "daily":
                next_due = base + datetime.timedelta(days=1)
            elif recurrence == "weekly":
                next_due = base + datetime.timedelta(weeks=1)
            else:
                continue

            next_due_str = next_due.strftime("%Y-%m-%d")

            # Create new task
            new_id = await db.add_task(uid, task["description"], next_due_str, recurrence)

            # Send to user's private channel
            user = await db.get_user(uid)
            if user and user["private_channel_id"]:
                channel = self.bot.get_channel(int(user["private_channel_id"]))
                if channel:
                    try:
                        embed = build_task_embed(
                            task["description"], "pending", next_due_str, recurrence
                        )
                        view = TaskView(task_id=new_id)
                        msg = await channel.send(embed=embed, view=view)
                        await db.update_task_message_id(new_id, str(msg.id))
                        self.bot.add_view(view)
                    except (discord.Forbidden, discord.HTTPException) as e:
                        log.warning("Failed to send recurring task %d: %s", new_id, e)

            log.info(
                "Recurring task regenerated: %d -> %d (%s, due %s)",
                task["id"], new_id, recurrence, next_due_str,
            )

        try:
            from src.cogs.accountability import refresh_board
            await refresh_board(self.bot)
        except Exception as e:
            log.warning("Failed to refresh board after daily reset: %s", e)

    @daily_reset.before_loop
    async def before_daily_reset(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(LoopsCog(bot))
