# Bother Bot - Task Tracker

## Phase 0: Framework Setup
- [x] W0-T1: Create CLAUDE.md
- [x] W0-T2: Initialize git repository
- [x] W0-T3: Create .planning/ directory structure
- [x] W0-T4: Create STATE.md
- [x] W0-T5: Create tasks.md
- [x] W0-T6: Create Phase 1 plan (XML task specs)

---

## Phase 1: Foundation (no Discord connection needed)

### Wave 1 (parallel - zero dependencies)
- [x] W1-T1: Project scaffold (Dockerfile, docker-compose.yml, requirements.txt, .gitignore, .env.example, src/__init__.py)
- [x] W1-T2: Constants module (colors, scoring values, message templates)
- [x] W1-T3: Database layer (schema init + CRUD operations)
- [x] W1-T4: Scoring module (pure point calculation functions)

### Wave 2 (depends on Wave 1)
- [x] W2-T1: Embed builders (all 4 embed types: task pending/complete/overdue, board)
- [x] W2-T2: Persistent View classes (TaskView with Done/Snooze buttons)
- [x] W2-T3: Embed verification tests (test_embeds.py)
- [x] W2-T4: DB + scoring tests (test_db.py, test_scoring.py)

### Wave 3 (depends on Wave 2)
- [x] W3-T1: Bot entry point with cog loading skeleton (bot.py)

**Gate**: All tests pass. Docker image builds. ✅

---

## Phase 2: Core Commands (requires test Discord server)

### Wave 1 (parallel)
- [x] W1-T1: /opt-in command + private channel creation with permissions
- [x] W1-T2: /task add command + embed delivery to private channel

### Wave 2 (depends on Wave 1)
- [x] W2-T1: Mark Done button handler (green embed, remove buttons, +10 score)
- [x] W2-T2: Snooze button handler (new due date, -2 score)
- [x] W2-T3: /board refresh + accountability board embed

### Wave 3 (depends on Wave 2)
- [x] W3-T1: Celebration message in #the-meat-grinder on task completion
- [x] W3-T2: Board auto-update on task state change

**Gate**: Full task lifecycle works. Manual Discord verification checklist passes. ✅ (code complete, needs live Discord test)

---

## Phase 3: Automation Loops (the "bother" engine)

### Wave 1 (parallel)
- [x] W1-T1: Overdue checker loop (hourly - mark overdue, red embed, deduct points)
- [x] W1-T2: Wall of Shame loop (9PM daily - ping users with pending/overdue tasks)
- [x] W1-T3: Daily Reset loop (midnight - regenerate recurring tasks, clean completed)

### Wave 2 (depends on Wave 1)
- [x] W2-T1: /prod command (public reminder for user's overdue tasks)
- [x] W2-T2: Recurring task generation on completion (daily/weekly cycle)

**Gate**: Full cycle: create user -> add task -> overdue -> shame -> complete -> celebrate. ✅ (69/69 tests pass)

---

## Phase 4: Hardening & Deploy

### Wave 1 (parallel)
- [x] W1-T1: Error handling (rate limits, deleted channels, permission errors)
- [x] W1-T2: Bot restart resilience (re-register persistent views, re-fetch board message)
- [x] W1-T3: Logging setup (structured logs to stdout for Docker)
- [x] W1-T4: Timezone audit (all datetime.now() calls use UTC)

### Wave 2 (depends on Wave 1)
- [ ] W2-T1: Deploy to Synology NAS via Docker Compose
- [ ] W2-T2: Volume persistence test (restart container, verify DB intact)
- [ ] W2-T3: Final end-to-end walkthrough (all manual verification checklists)

**Gate**: Production-ready on NAS. Bot survives restarts.
