from pathlib import Path

from stitch import APP_DIR, APP_NAME


def setup_all_hooks(project_dir: Path):
    _setup_claude(project_dir)
    _setup_codex(project_dir)
    _setup_generic(project_dir)


def _stitch_block() -> str:
    return f"""
# {APP_NAME.title()} -- Session Context Manager

## On Session Start
- Check if `{APP_DIR}/context.md` exists
- If it does, read it and greet the user with a summary of previous progress
- Format: "Welcome back! Last session: [summary]. Next up: [next steps]. Ready to continue?"

## During Work
Use `{APP_NAME} update` to log everything in a single call (saves tokens):

  {APP_NAME} update -t "task" -p "progress note" -d "choice::reason" -x "what::why" -s "step::done"

Flags:
  -t   Set current task
  -p   Log progress (repeatable)
  -d   Log decision as "choice::reason" (repeatable)
  -x   Log dead end as "what::why" (repeatable)
  -s   Update plan step as "title::status" (repeatable)
  --plan "desc" --plan-steps "step1" --plan-steps "step2"   Set plan

Example -- log multiple things in one call:
  {APP_NAME} update -p "login endpoint done" -p "signup endpoint done" -d "JWT::stateless API" -s "Auth routes::done"

Every call auto-saves {APP_DIR}/context.md so no progress is lost even if the session crashes.

## Do NOT explore these directories
node_modules, __pycache__, .venv, venv, dist, build, .git, .tox, .pytest_cache
Instead, read `{APP_DIR}/context.md` for the file map -- it shows which files matter and what they do.

## Before Session Ends
- Run `{APP_NAME} save` to archive the session
""".strip()


def _append_if_missing(filepath: Path, block: str):
    if filepath.exists():
        existing = filepath.read_text(encoding="utf-8")
        if APP_NAME in existing:
            return
        filepath.write_text(existing + "\n\n" + block, encoding="utf-8")
    else:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(block, encoding="utf-8")


def _setup_claude(project_dir: Path):
    _append_if_missing(project_dir / "CLAUDE.md", _stitch_block())


def _setup_codex(project_dir: Path):
    _append_if_missing(
        project_dir / ".codex" / "instructions.md",
        _stitch_block(),
    )


def _setup_generic(project_dir: Path):
    prompt_file = project_dir / APP_DIR / "starter_prompt.txt"
    prompt_file.parent.mkdir(parents=True, exist_ok=True)
    prompt_file.write_text(
        "Paste this at the start of your AI session:\n\n"
        "---\n"
        f"Read the file `{APP_DIR}/context.md` in this project directory. "
        "It contains context from our previous session. Summarize what was done "
        "and what's next, then continue from where we left off.\n"
        f"Use `{APP_NAME} update` to log progress as you work.\n"
        "---\n",
        encoding="utf-8",
    )
