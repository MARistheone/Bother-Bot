"""Design tokens, scoring values, and message templates. Single source of truth."""

import os

# ── Color Tokens ──────────────────────────────────────────────
COLOR_BOARD = 0x2B2D31
COLOR_DEFAULT_TASK = 0x5865F2
COLOR_COMPLETE = 0x57F287
COLOR_OVERDUE = 0xED4245

# ── Scoring Constants ─────────────────────────────────────────
SCORE_COMPLETE = 10
SCORE_OVERDUE_PER_DAY = -5
SCORE_SNOOZE = -2

# ── Database Path ─────────────────────────────────────────────
DB_PATH = os.environ.get("DB_PATH", "/app/data/database.db")

# ── Status Emojis ─────────────────────────────────────────────
STATUS_EMOJI = {
    "pending": "\U0001f7e1",     # :yellow_circle:
    "completed": "\U0001f7e2",   # :green_circle:
    "overdue": "\U0001f534",     # :red_circle:
}

# ── Celebration Messages ──────────────────────────────────────
# Placeholders: {user}, {task}
CELEBRATION_MESSAGES = [
    "Well well well, {user} actually did something. **{task}** — done. Don't let it go to your head.",
    "Stop the presses! {user} completed **{task}**. Miracles DO happen.",
    "Look at {user} being a functioning adult! **{task}** — checked off. Proud of you (kinda).",
    "{user} just crushed **{task}**. Someone get this person a trophy... or at least a snack.",
    "Alert the media — {user} finished **{task}**. The streak of disappointment is OVER.",
    "Oh snap, {user} knocked out **{task}**! Keep this energy up and you might actually impress me.",
]

# ── Shame Messages ────────────────────────────────────────────
# Placeholders: {user}, {tasks}
SHAME_MESSAGES = [
    "Hey {user}, remember these? Yeah, still not done:\n{tasks}",
    "{user}... buddy... pal... these tasks aren't going to do themselves:\n{tasks}",
    "Attention everyone: {user} is allergic to productivity. Evidence:\n{tasks}",
    "Breaking news: {user} continues to ignore their responsibilities:\n{tasks}",
    "Dear {user}, your tasks called. They miss you. Please visit them:\n{tasks}",
    "{user}, I'm not mad. I'm just disappointed. Very, very disappointed.\n{tasks}",
]

# ── Prod Messages ─────────────────────────────────────────────
# Placeholders: {user}, {task}
PROD_PENDING_MESSAGES = [
    "> Hey {user}, a little birdie told me **{task}** isn't done yet. Tick tock.",
    "> {user}! Remember **{task}**? Yeah, it's still waiting for you.",
    "> Paging {user}! **{task}** is collecting dust. Just saying.",
    "> {user}, **{task}** is starting to grow cobwebs. You gonna do something about that?",
    "> Excuse me {user}, but **{task}** would like a word with you.",
    "> {user}... **{task}** isn't going to do itself. Or IS it? (Spoiler: it's not.)",
]

PROD_OVERDUE_MESSAGES = [
    "> \U0001f6a8 RED ALERT, {user}. **{task}** is officially OVERDUE. Get on it.",
    "> Did you forget about **{task}** {user}? Because the deadline didn't.",
    "> Hello {user}? **{task}** called from the past. It wants its completion back.",
    "> {user}, **{task}** is overdue and silently judging you.",
    "> \u26a0\ufe0f WARNING: {user} is slacking. **{task}** is past its deadline!",
]

# ── Snooze Messages ─────────────────────────────────────────────
# Placeholders: {user}, {task}
SNOOZE_MESSAGES = [
    "{user} just snoozed **{task}**. Procrastination is an art form.",
    "Booo! {user} pushed off **{task}** for another day. Weak.",
    "{user} is cowardly running away from **{task}**... again.",
    "Another day, another excuse. {user} snoozed **{task}**.",
    "{user} kicked **{task}** down the road. Classic.",
]
