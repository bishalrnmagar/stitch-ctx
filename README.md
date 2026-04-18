# Stitch — AI Session Context Manager for Claude, Codex, ChatGPT & Any LLM

[![PyPI version](https://img.shields.io/pypi/v/stitch-ctx)](https://pypi.org/project/stitch-ctx/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/stitch-ctx)](https://pypi.org/project/stitch-ctx/)
[![Python](https://img.shields.io/pypi/pyversions/stitch-ctx)](https://pypi.org/project/stitch-ctx/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Save and restore AI coding session progress** — so your next Claude Code, Codex, ChatGPT, Cursor, Copilot, or Windsurf session picks up exactly where you left off. No lost context, no wasted tokens, no repeated work.

> Your AI coding session expires. You start a new one. The AI has zero memory — it re-reads your entire project, wastes tokens, loses decisions, and might redo work you already finished. **Stitch fixes that.**

## The Problem: AI Coding Assistants Forget Everything

Every time your AI coding session expires or you switch between AI tools, you lose:
- **Task progress** — the AI redoes finished work
- **Architecture decisions** — the AI second-guesses choices you already made
- **Failed approaches** — the AI retries things you know don't work
- **Token budget** — the AI wastes tokens re-exploring your codebase

Stitch captures the **soft knowledge** that lives in your AI session but not in your code — and generates a compact markdown file any AI model reads on startup.

## How It Works

```
Session 1 (expires)              Session 2 (new)
├── Built login & signup         ├── Reads .stitch/context.md
├── Chose JWT over sessions      ├── "Welcome back! Login & signup done.
├── bcrypt failed, used argon2   │    Next up: password reset.
└── Next: password reset         │    Using JWT (not sessions). Skip bcrypt."
                                 └── Continues from password reset ✓
```

## Installation

**Requires:** Python 3.10+

```bash
pip install stitch-ctx
```

Verify it works:

```bash
stitch --version
```

## Quick Start

```bash
cd your-project
stitch init
```

That's it. Stitch will:
- Auto-detect your project name from the folder
- Auto-detect your tech stack from project files
- Scan your project structure (skipping node_modules, __pycache__, etc.)
- Set up hooks for Claude, Codex, and ChatGPT automatically

Now start any AI session. The AI reads `.stitch/context.md` and greets you:

```
Welcome back! Last session you finished the login and signup endpoints.
Next up: password reset flow. Ready to continue?
```

**For ChatGPT or models without auto-read:** copy the contents of `.stitch/starter_prompt.txt` into your first message.

## What Gets Captured

| What | Example | Why It Matters |
|---|---|---|
| **Task** | "Build user auth with JWT" | AI knows the goal |
| **Plan** | 4 steps, step 2 in-progress | AI continues the same plan, not a new one |
| **Progress** | "Login done, signup done" | AI won't redo finished work |
| **Decisions** | "JWT over sessions — stateless" | AI won't second-guess your choices |
| **Dead Ends** | "bcrypt fails on Windows" | AI won't retry known failures |
| **Project Files** | Full file tree with descriptions | AI won't waste tokens exploring your codebase |

## Commands

### The one command the AI uses

The AI logs everything in a single call using `stitch update`:

```bash
# Set task + log progress + log decision, all at once
stitch update \
  -t "build auth system" \
  -p "login endpoint done" \
  -p "signup endpoint done" \
  -d "JWT::stateless API" \
  -x "bcrypt::install fails on Windows" \
  -s "Auth routes::done"
```

| Flag | What it does | Format |
|---|---|---|
| `-t` | Set current task | `-t "description"` |
| `-p` | Log progress (repeatable) | `-p "what was done"` |
| `-d` | Log decision (repeatable) | `-d "choice::reason"` |
| `-x` | Log dead end (repeatable) | `-x "what::why"` |
| `-s` | Update plan step (repeatable) | `-s "step name::status"` |
| `--plan` | Set plan description | `--plan "description"` |
| `--plan-steps` | Set plan steps (repeatable) | `--plan-steps "step name"` |

Every call auto-saves `.stitch/context.md` — even if the session crashes, the last known state is preserved.

### Commands you might use manually

```bash
stitch init                     # One-time project setup
stitch status                   # Show current session state
stitch save                     # Archive session + generate context
stitch save -m "stopping here"  # Save with a final note
stitch resume                   # Regenerate context.md
stitch history                  # List past sessions
stitch files                    # Re-scan project structure
```

### Individual logging commands

These also work if you prefer them over `stitch update`:

```bash
stitch task "build auth system"
stitch plan "Build in 4 steps" -s "Schema" -s "Routes" -s "Middleware" -s "Tests"
stitch plan-step "Schema" --status done
stitch progress "login endpoint complete"
stitch decision "PostgreSQL" --reason "need full-text search"
stitch dead-end "SQLite FTS" --reason "too limited"
stitch file src/auth/login.py "handles JWT login"
```

## Supported AI Models

Stitch sets up hooks for **all models** during `stitch init`:

| Model | Hook File | Integration |
|---|---|---|
| **Claude Code** | `CLAUDE.md` | Automatic — reads on session start |
| **Codex (OpenAI)** | `.codex/instructions.md` | Automatic — reads on session start |
| **ChatGPT / Others** | `.stitch/starter_prompt.txt` | Paste into first message |

Switch between models anytime. The context file is plain markdown — every model can read it.

## What Stitch Ignores

The file scanner automatically skips directories that waste AI tokens:

`node_modules`, `__pycache__`, `.venv`, `venv`, `dist`, `build`, `.git`, `.next`, `.nuxt`, `target`, `vendor`, `.cache`, `.terraform`, and more.

It also skips lock files (`package-lock.json`, `yarn.lock`, etc.), compiled files (`.pyc`, `.so`, `.dll`), and media files.

## Auto-Detected Tech Stacks

Stitch detects your stack from project files:

**Languages:** Python, Node.js, TypeScript, Go, Rust, Java, Kotlin, Ruby, PHP, Elixir, Dart, C/C++, C#/.NET

**Frameworks:** Django, Flask, Next.js, Nuxt, Angular, SvelteKit, Vite

**Tools:** Docker, Terraform, Prisma, Tailwind CSS

## Example Output

When you run `stitch resume` or when the AI reads `.stitch/context.md`:

```markdown
# Project: my-api
**Stack:** Python, FastAPI
**Past sessions:** 3

## Current Task
Build user authentication with JWT tokens

## Plan
Build auth in 4 steps

- [x] DB schema and models
- [x] Login & signup endpoints
- [~] Password reset flow
- [ ] Email verification

## Progress
- Created User model with email, password_hash fields
- Login returns JWT, signup validates email uniqueness
- Password reset endpoint scaffolded, needs email integration

## Key Decisions
1. JWT over sessions -- stateless, better for API consumers
2. Argon2 for password hashing -- bcrypt had install issues
3. PostgreSQL over SQLite -- need full-text search later

## Dead Ends (don't retry)
- **bcrypt** -- fails to compile on Windows, use argon2 instead
- **SQLite FTS5** -- too limited, switched to PostgreSQL

## Project Files
Do NOT explore directories yourself. This is the complete project structure.
- `src/models/user.py` -- User model, password hashing
- `src/routes/auth.py` -- login, signup, token refresh
- `src/routes/reset.py` -- password reset (in progress)
- `src/db/migrations/001_users.sql`
- `tests/test_auth.py`

## Next Steps
-> Continue: Password reset flow
- Email verification
```

## Project Structure

After `stitch init`, your project will have:

```
your-project/
├── .stitch/                    # Stitch data (gitignore or commit, your choice)
│   ├── config.json             # Project name, tech stack
│   ├── current_session.json    # Active session state
│   ├── sessions/               # Archived past sessions
│   ├── context.md              # What the AI reads on startup
│   ├── file_map.json           # Project file index
│   └── starter_prompt.txt      # For ChatGPT / manual paste
├── CLAUDE.md                   # Claude Code hook (appended, not overwritten)
└── .codex/
    └── instructions.md         # Codex hook (appended, not overwritten)
```

## Why Stitch?

| Without Stitch | With Stitch |
|---|---|
| AI forgets everything between sessions | AI resumes exactly where you left off |
| Wastes tokens re-reading your project | Compact context file saves token budget |
| Retries failed approaches | Dead ends are recorded and avoided |
| Second-guesses your architecture | Decisions are preserved with reasoning |
| Different behavior across AI tools | Same context file works with every LLM |

## FAQ

### Does Stitch work with Cursor, Copilot, or Windsurf?

Yes. Stitch generates a plain markdown context file (`.stitch/context.md`) that any AI coding assistant can read. For tools that support custom instructions, point them to this file.

### How is this different from CLAUDE.md or .cursorrules?

Those files store static project rules. Stitch tracks **dynamic session state** — what you've done, what's next, what failed, and what decisions you made. They complement each other.

### Does Stitch send data to any server?

No. Stitch is 100% local. All data stays in your `.stitch/` directory. Nothing is sent anywhere.

### How much context does it use?

The generated `context.md` is typically 50-200 lines — a fraction of what the AI would spend re-exploring your project manually.

## Contributing

Contributions are welcome. Please [open an issue](https://github.com/bishalrnmagar/stitch-ctx/issues) first to discuss what you'd like to change.

## Links

- [PyPI](https://pypi.org/project/stitch-ctx/)
- [GitHub](https://github.com/bishalrnmagar/stitch-ctx)
- [Issues](https://github.com/bishalrnmagar/stitch-ctx/issues)

## License

[MIT](LICENSE)
