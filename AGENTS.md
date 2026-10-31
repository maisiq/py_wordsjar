**Project Rules**
**Hard Constraints**
- Do not install new dependencies without confirmation.

**Style**
- Write commits in Conventional Commits format.

**Code Style**
- Full compliance with PEP8.
- Use double quotes for strings.

**Code Comment Rules**
**What is forbidden in comments:**
- DO NOT write narrative comments that retell what the next line of code does. Example of a bad comment: `# Increment counter` next to `counter += 1`.
- DO NOT reference the context of our dialogue. Phrases like "as we discussed", "to fix bug X", "temporary solution", "delete later", or "changed in this session" are forbidden. The comment must be understandable to someone who hasn't seen the dialogue.
- DO NOT leave change markers like `# ← new`, `# changed this line`, or `# added for the X bug`. This is transient trash that becomes outdated the moment of commit.

**What is acceptable:**
- The comment explains **WHY**, not **WHAT**. It is only needed for non-obvious things: hidden constraints (e.g., "call order matters"), non-standard workarounds, or the reason why the code looks exactly like this.

**Roadmap Management (ROADMAP.md)**
- Before starting any task, you **MUST** read the `ROADMAP.md` file to understand the current phase and the next uncompleted task.
- Upon completing a task, you **MUST** update `ROADMAP.md`: mark the completed item as `[x]` and, if necessary, move the `(<- CURRENT TASK)` marker to the next item.
- If a task is not part of the current phase in `ROADMAP.md`, do not start it without explicit user confirmation.

**Language Policy**
- **Internal work — ONLY in English:** All reasoning/thinking, tool call arguments (paths, search queries, file contents), code, variable names, code comments, docstrings, and commit messages must be in English. Text written to project files (README, documentation, configs) must be in English unless the user explicitly requests otherwise.
- **Communication with the user — ONLY in Russian:** Final responses to the user, explanations, questions, work reports, and error messages/warnings visible to the user must be in Russian.
- **Why this way:** English saves tokens during internal work. Russian is only needed where a human reads the text.

**File structure**
- The project file structure is described in `INDEX.md`.


**Memory Management**

You have a persistent memory system. Use it to maintain continuity across sessions.

**Memory Files**
- **MEMORY.md** — durable facts, decisions, lessons learned, and important context (NOT raw logs). Load and update this file in the main session.
- **memory/YYYY-MM-DD.md** — daily raw notes and observations. Use for transient details that may later be distilled into MEMORY.md.

**When to Update Memory**
- When the user says "remember this" or similar → update `memory/YYYY-MM-DD.md` or the relevant file.
- When you learn a lesson, make a mistake, or discover a durable fact → update `MEMORY.md` (or the relevant skill).
- When the user corrects you or gives feedback on your behavior → update `AGENTS.md` or `MEMORY.md` so the fix persists[reference:1].
- When you identify a recurring pattern or preference from interactions → save it for future sessions[reference:2].

**How to Update Memory (Rules)**
1. **Read before writing.** Always read the target memory file first. Never overwrite blindly.
2. **Write concrete updates.** No empty placeholders. "Mental notes" do not survive a restart[reference:3].
3. **Be selective.** Only record durable, reusable information — not every detail of the conversation.
4. **Deduplicate.** If a similar fact already exists, update it in place rather than adding a duplicate.
5. **Mark obsolete entries.** When a preference changes, mark the old entry as `superseded` instead of leaving contradictory active rules[reference:4].
6. **Keep MEMORY.md curated.** It should be a distilled summary, not a raw log. If it grows too large, move topic-specific details into separate files and reference them from `MEMORY.md`[reference:5].

**What NOT to Store**
- Passwords, API keys, tokens, or other secrets.
- One-off or transient details that have no future relevance.
- Raw conversation transcripts (keep only distilled facts).