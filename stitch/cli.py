import click
from datetime import datetime
from pathlib import Path

from stitch import APP_NAME, APP_DIR, __version__


def _require_init():
    from stitch.store import is_initialized
    if not is_initialized():
        click.echo(f"{APP_NAME} is not initialized. Run '{APP_NAME} init' first.")
        raise SystemExit(1)


@click.group()
@click.version_option(version=__version__, prog_name=APP_NAME)
def cli():
    """Stitch -- AI session context manager.

    Saves your AI session progress so the next session
    picks up where you left off.
    """
    pass


@cli.command()
@click.option("--name", default=None, help="Project name (default: folder name)")
@click.option("--stack", default=None, help="Tech stack, comma-separated (default: auto-detect)")
def init(name, stack):
    """Initialize stitch in the current project.

    Auto-detects project name and tech stack. Sets up hooks
    for Claude, Codex, and other AI models automatically.
    Scans project structure so AI knows the codebase layout.
    """
    from stitch.store import get_stitch_dir, write_json, get_config_path, is_initialized
    from stitch.hooks import setup_all_hooks
    from stitch.session import create_session
    from stitch.detect import detect_project_name, detect_tech_stack
    from stitch.file_map import save_file_map
    from stitch.context import save_context

    if is_initialized():
        click.echo(f"{APP_NAME} is already initialized in this project.")
        return

    project_dir = Path.cwd()
    project_name = name or detect_project_name(project_dir)
    if stack:
        tech_stack = [s.strip() for s in stack.split(",") if s.strip()]
    else:
        tech_stack = detect_tech_stack(project_dir)

    stitch_dir = get_stitch_dir()
    stitch_dir.mkdir(parents=True, exist_ok=True)
    (stitch_dir / "sessions").mkdir(exist_ok=True)

    config = {
        "project_name": project_name,
        "tech_stack": tech_stack,
        "created_at": datetime.now().isoformat(),
    }
    write_json(get_config_path(), config)
    create_session()
    setup_all_hooks(project_dir)

    file_map = save_file_map(project_dir)
    file_count = len(file_map.get("files", {}))
    save_context()

    click.echo(f"Initialized {APP_NAME} for '{project_name}'")
    if tech_stack:
        click.echo(f"  Stack:   {', '.join(tech_stack)}")
    click.echo(f"  Files:   {file_count} files indexed")
    click.echo(f"  Hooks:   CLAUDE.md, .codex/instructions.md, starter_prompt.txt")
    click.echo(f"  Ready -- any AI model will auto-read context on session start.")


# ── Batch update (primary command for AI) ──────────────────────


def _parse_pair(value: str) -> tuple[str, str]:
    """Parse 'key::value' into a tuple. If no :: found, return (value, '')."""
    if "::" in value:
        parts = value.split("::", 1)
        return (parts[0].strip(), parts[1].strip())
    return (value.strip(), "")


@cli.command()
@click.option("--task", "-t", default=None, help="Set current task")
@click.option("--progress", "-p", multiple=True, help="Log progress (repeatable)")
@click.option("--decision", "-d", multiple=True, help="Log decision as 'choice::reason'")
@click.option("--dead-end", "-x", multiple=True, help="Log dead end as 'what::why'")
@click.option("--step", "-s", multiple=True, help="Update plan step as 'title::status'")
@click.option("--plan", default=None, help="Set plan description")
@click.option("--plan-steps", multiple=True, help="Plan steps (use with --plan)")
def update(task, progress, decision, dead_end, step, plan, plan_steps):
    """Batch update session state in a single call.

    This is the primary command AI models should use. One call
    instead of many, minimal output, auto-saves context.md.

    Examples:

      stitch update -t "build auth" -p "login done" -p "signup done"

      stitch update -d "JWT::stateless API" -x "bcrypt::install fails"

      stitch update -s "Models::done" -s "Routes::in-progress"

      stitch update --plan "Build in 3 steps" --plan-steps "DB" --plan-steps "API" --plan-steps "Tests"
    """
    _require_init()
    from stitch.session import batch_update

    parsed_decisions = [_parse_pair(d) for d in decision] if decision else None
    parsed_dead_ends = [_parse_pair(d) for d in dead_end] if dead_end else None
    parsed_steps = [_parse_pair(s) for s in step] if step else None

    if parsed_steps:
        for i, (title, status) in enumerate(parsed_steps):
            if not status:
                parsed_steps[i] = (title, "done")

    batch_update(
        task=task,
        progress_items=list(progress) if progress else None,
        decisions=parsed_decisions,
        dead_ends=parsed_dead_ends,
        step_updates=parsed_steps,
        plan_desc=plan,
        plan_steps=list(plan_steps) if plan_steps else None,
    )

    click.echo("ok")


# ── Individual commands (still available) ──────────────────────


@cli.command()
@click.argument("description")
def task(description):
    """Set or update the current task."""
    _require_init()
    from stitch.session import update_session
    update_session({"task": description})
    click.echo(f"Task set: {description}")


@cli.command()
@click.argument("description")
@click.option("--steps", "-s", multiple=True, help="Plan steps (repeat -s for each step)")
def plan(description, steps):
    """Set the implementation plan."""
    _require_init()
    from stitch.session import set_plan

    step_list = [
        {"title": s, "detail": "", "status": "pending", "notes": ""}
        for s in steps
    ]
    set_plan(description, step_list)
    click.echo(f"Plan set: {description}")
    for i, s in enumerate(step_list, 1):
        click.echo(f"  {i}. {s['title']}")


@cli.command("plan-step")
@click.argument("title")
@click.option("--status", type=click.Choice(["pending", "in-progress", "done", "skipped"]), default=None)
@click.option("--notes", default=None, help="Notes about this step")
@click.option("--add", is_flag=True, help="Add as new step instead of updating")
def plan_step(title, status, notes, add):
    """Update a plan step or add a new one."""
    _require_init()
    from stitch.session import get_current_session, update_plan_step
    from stitch.store import get_session_path, write_json

    session = get_current_session()
    if not session or not session.get("plan"):
        click.echo(f"No plan set. Run '{APP_NAME} plan' first.")
        return

    if add:
        session["plan"]["steps"].append({
            "title": title, "detail": "", "status": status or "pending", "notes": notes or "",
        })
        write_json(get_session_path(), session)
        click.echo(f"Step added: {title}")
    else:
        result = update_plan_step(title, status or "done", notes)
        if result:
            click.echo(f"Step '{title}' -> {status or 'done'}")
        else:
            click.echo(f"Step '{title}' not found in plan.")


@cli.command("plan-revise")
@click.argument("reason")
@click.option("--description", "-d", default=None, help="New plan description")
def plan_revise(reason, description):
    """Revise the current plan with a reason."""
    _require_init()
    from stitch.session import revise_plan

    result = revise_plan(reason, new_description=description)
    if result:
        click.echo(f"Plan revised: {reason}")
    else:
        click.echo(f"No plan to revise. Run '{APP_NAME} plan' first.")


@cli.command()
@click.argument("message")
def progress(message):
    """Log a progress update."""
    _require_init()
    from stitch.session import add_to_session
    add_to_session("progress", {"message": message, "timestamp": datetime.now().isoformat()})
    click.echo(f"Progress: {message}")


@cli.command()
@click.argument("choice")
@click.option("--reason", "-r", default="", help="Why this decision was made")
def decision(choice, reason):
    """Log a key decision."""
    _require_init()
    from stitch.session import add_to_session
    add_to_session("decisions", {"choice": choice, "reason": reason, "timestamp": datetime.now().isoformat()})
    click.echo(f"Decision: {choice}")


@cli.command("dead-end")
@click.argument("what")
@click.option("--reason", "-r", default="", help="Why it didn't work")
def dead_end(what, reason):
    """Log something that didn't work (so future sessions don't retry)."""
    _require_init()
    from stitch.session import add_to_session
    add_to_session("dead_ends", {"what": what, "why": reason, "timestamp": datetime.now().isoformat()})
    click.echo(f"Dead end logged: {what}")


@cli.command("file")
@click.argument("path")
@click.argument("description")
def file_note(path, description):
    """Add or update a file description in the file map."""
    _require_init()
    from stitch.file_map import update_file_description
    update_file_description(path, description)
    click.echo(f"File mapped: {path} -- {description}")


@cli.command()
def files():
    """Scan and snapshot the project file structure."""
    _require_init()
    from stitch.file_map import save_file_map
    file_map = save_file_map(Path.cwd())
    count = len(file_map.get("files", {}))
    click.echo(f"Scanned {count} files.")


# ── Session management ─────────────────────────────────────────


@cli.command()
@click.option("--message", "-m", default="", help="Final note for this session")
def save(message):
    """Save current session and generate context for next session."""
    _require_init()
    from stitch.session import add_to_session, archive_session, create_session
    from stitch.context import save_context

    if message:
        add_to_session("progress", {"message": message, "timestamp": datetime.now().isoformat()})

    session = archive_session()
    if session:
        click.echo(f"Session archived: {session['id']}")

    save_context()
    click.echo(f"Context saved to {APP_DIR}/context.md")

    create_session()
    click.echo("New session started.")


@cli.command()
def resume():
    """Generate context.md for a new AI session."""
    _require_init()
    from stitch.context import save_context
    from stitch.store import get_context_path

    context = save_context()
    click.echo(f"Context generated: {get_context_path()}")
    click.echo("")
    click.echo(context)


@cli.command()
def status():
    """Show current session state."""
    _require_init()
    from stitch.session import get_current_session, get_session_history
    from stitch.store import get_config_path, read_json

    config = read_json(get_config_path())
    session = get_current_session()
    history = get_session_history()

    click.echo(f"Project: {config.get('project_name', 'Unknown')}")
    click.echo(f"Stack:   {', '.join(config.get('tech_stack', []))}")
    click.echo(f"Past sessions: {len(history)}")
    click.echo("")

    if not session:
        click.echo("No active session.")
        return

    click.echo(f"Session: {session.get('id', 'unknown')}")
    click.echo(f"Started: {session.get('started_at', 'unknown')}")

    if session.get("task"):
        click.echo(f"Task:    {session['task']}")

    plan = session.get("plan")
    if plan:
        click.echo(f"\nPlan: {plan['description']}")
        for step in plan.get("steps", []):
            icon = {"done": "x", "in-progress": "~", "skipped": "-", "pending": " "}.get(step["status"], " ")
            click.echo(f"  [{icon}] {step['title']}")

    if session.get("progress"):
        click.echo(f"\nProgress ({len(session['progress'])}):")
        for p in session["progress"][-5:]:
            click.echo(f"  - {p['message']}")

    if session.get("decisions"):
        click.echo(f"\nDecisions ({len(session['decisions'])}):")
        for d in session["decisions"]:
            click.echo(f"  - {d['choice']}")

    if session.get("dead_ends"):
        click.echo(f"\nDead ends ({len(session['dead_ends'])}):")
        for d in session["dead_ends"]:
            click.echo(f"  - {d['what']}")


@cli.command()
def history():
    """Show past sessions."""
    _require_init()
    from stitch.session import get_session_history

    sessions = get_session_history()
    if not sessions:
        click.echo("No past sessions yet.")
        return

    for s in sessions:
        task = s.get("task", "no task set")
        progress_n = len(s.get("progress", []))
        decisions_n = len(s.get("decisions", []))
        click.echo(f"  {s['id']}  |  {task}  |  {progress_n} progress, {decisions_n} decisions")


def main():
    cli()


if __name__ == "__main__":
    main()
