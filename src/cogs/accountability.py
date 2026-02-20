"""/opt-in, /board refresh, /config commands. Delegates to embeds.py and db.py."""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from src import db
from src.embeds import build_board_embed, build_welcome_embed

log = logging.getLogger("bother-bot")


async def refresh_board(bot: commands.Bot) -> None:
    """Re-render the accountability board embed.

    Fetches board_channel_id and board_message_id from config,
    builds a fresh embed, and edits the existing message.
    If the message was deleted, sends a new one and updates config.
    Silently returns if the board is not yet set up.
    """
    channel_id = await db.get_config("board_channel_id")
    if not channel_id:
        return

    channel = bot.get_channel(int(channel_id))
    if not channel:
        return

    # Build users_data from flat DB rows
    rows = await db.get_all_users_with_tasks()
    users_map: dict[str, dict] = {}
    guild = channel.guild

    for row in rows:
        uid = row["discord_id"]
        if uid not in users_map:
            member = guild.get_member(int(uid))
            name = member.display_name if member else f"User {uid}"
            users_map[uid] = {"name": name, "score": row["score"], "tasks": []}
        if row["task_id"] is not None:
            users_map[uid]["tasks"].append({
                "description": row["description"],
                "status": row["status"],
            })

    users_data = list(users_map.values())
    embed = build_board_embed(users_data)

    message_id = await db.get_config("board_message_id")
    if message_id:
        try:
            msg = await channel.fetch_message(int(message_id))
            await msg.edit(embed=embed)
            return
        except discord.NotFound:
            pass  # Message was deleted, send a new one

    msg = await channel.send(embed=embed)
    await db.set_config("board_message_id", str(msg.id))


class AccountabilityCog(commands.Cog):
    """Handles user registration, board management, and config."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="opt-in", description="Register and get your private task channel")
    async def opt_in(self, interaction: discord.Interaction) -> None:
        uid = str(interaction.user.id)

        user = await db.get_user(uid)
        if user and user["private_channel_id"]:
            await interaction.response.send_message(
                "You're already registered!", ephemeral=True
            )
            return

        # Register user if not in DB
        if not user:
            await db.add_user(uid)

        # Create private channel with permission overrides
        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(
                read_messages=True, send_messages=True
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True, send_messages=True
            ),
        }

        channel = await guild.create_text_channel(
            f"{interaction.user.display_name}-tasks",
            overwrites=overwrites,
        )

        await db.set_user_private_channel(uid, str(channel.id))

        # Send welcome embed to the new channel
        embed = build_welcome_embed(channel.mention)
        await channel.send(embed=embed)

        await interaction.response.send_message(
            f"You're in! Check out {channel.mention}", ephemeral=True
        )
        log.info("User %s opted in, channel %s created", uid, channel.id)

    @app_commands.command(
        name="board",
        description="Force refresh the accountability board (admin only)",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def board_refresh(self, interaction: discord.Interaction) -> None:
        # Store the channel where the board lives
        await db.set_config("board_channel_id", str(interaction.channel_id))

        # Build and send the board
        rows = await db.get_all_users_with_tasks()
        users_map: dict[str, dict] = {}
        guild = interaction.guild

        for row in rows:
            uid = row["discord_id"]
            if uid not in users_map:
                member = guild.get_member(int(uid))
                name = member.display_name if member else f"User {uid}"
                users_map[uid] = {"name": name, "score": row["score"], "tasks": []}
            if row["task_id"] is not None:
                users_map[uid]["tasks"].append({
                    "description": row["description"],
                    "status": row["status"],
                })

        users_data = list(users_map.values())
        embed = build_board_embed(users_data)

        # Delete old board message if it exists in this channel
        old_msg_id = await db.get_config("board_message_id")
        if old_msg_id:
            try:
                old_msg = await interaction.channel.fetch_message(int(old_msg_id))
                await old_msg.delete()
            except discord.NotFound:
                pass

        await interaction.response.send_message(embed=embed)
        # Fetch the response message to store its ID
        msg = await interaction.original_response()
        await db.set_config("board_message_id", str(msg.id))
        log.info("Board refreshed in channel %s", interaction.channel_id)

    @app_commands.command(
        name="set-meat-grinder",
        description="Set this channel as the meat grinder for celebrations/shame (admin)",
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def set_meat_grinder(self, interaction: discord.Interaction) -> None:
        await db.set_config("meat_grinder_channel_id", str(interaction.channel_id))
        await interaction.response.send_message(
            f"This channel is now the meat grinder \U0001f356", ephemeral=True
        )
        log.info("Meat grinder set to channel %s", interaction.channel_id)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AccountabilityCog(bot))
