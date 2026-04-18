from stitch.session import get_current_session, get_session_history
from stitch.store import (
    get_config_path,
    get_context_path,
    get_file_map_path,
    read_json,
    write_text,
)


def save_context() -> str:
    context = generate_context()
    write_text(get_context_path(), context)
    return context


def generate_context() -> str:
    config = read_json(get_config_path())
    session = get_current_session()
    history = get_session_history()
    file_map = read_json(get_file_map_path())

    task, plan, progress, decisions, dead_ends, files_touched = (
        None, None, [], [], [], []
    )

    if session:
        task = session.get("task")
        plan = session.get("plan")
        progress = session.get("progress", [])
        decisions = session.get("decisions", [])
        dead_ends = session.get("dead_ends", [])
        files_touched = session.get("files_touched", [])

    if history:
        last = history[-1]
        if not task:
            task = last.get("task")
        if not plan:
            plan = last.get("plan")
        if not progress:
            progress = last.get("progress", [])
        if not decisions:
            decisions = last.get("decisions", [])
        if not dead_ends:
            dead_ends = last.get("dead_ends", [])

    lines = []

    # Header
    project_name = config.get("project_name", "Unknown")
    stack = ", ".join(config.get("tech_stack", []))
    lines.append(f"# Project: {project_name}")
    if stack:
        lines.append(f"**Stack:** {stack}")
    if history:
        lines.append(f"**Past sessions:** {len(history)}")
    lines.append("")

    # Task
    if task:
        lines.append("## Current Task")
        lines.append(task)
        lines.append("")

    # Plan
    if plan:
        lines.append("## Plan")
        lines.append(plan["description"])
        lines.append("")
        for step in plan.get("steps", []):
            icon = {
                "done": "[x]",
                "in-progress": "[~]",
                "skipped": "[-]",
            }.get(step["status"], "[ ]")
            line = f"- {icon} {step['title']}"
            if step.get("detail"):
                line += f" -- {step['detail']}"
            if step.get("notes"):
                line += f" (note: {step['notes']})"
            lines.append(line)
        lines.append("")

    # Progress
    if progress:
        lines.append("## Progress")
        for p in progress:
            lines.append(f"- {p['message']}")
        lines.append("")

    # Decisions
    if decisions:
        lines.append("## Key Decisions")
        for i, d in enumerate(decisions, 1):
            line = f"{i}. {d['choice']}"
            if d.get("reason"):
                line += f" -- {d['reason']}"
            lines.append(line)
        lines.append("")

    # Dead ends
    if dead_ends:
        lines.append("## Dead Ends (don't retry)")
        for d in dead_ends:
            line = f"- **{d['what']}**"
            if d.get("why"):
                line += f" -- {d['why']}"
            lines.append(line)
        lines.append("")

    # File map — show ALL files so AI never needs to explore
    file_entries = file_map.get("files", {})
    if file_entries:
        lines.append("## Project Files")
        lines.append("Do NOT explore directories yourself. This is the complete project structure.")
        lines.append("Ignored: node_modules, __pycache__, .venv, dist, build, .git, and other cache/package dirs.")
        lines.append("")
        for path, desc in file_entries.items():
            if desc:
                lines.append(f"- `{path}` -- {desc}")
            else:
                lines.append(f"- `{path}`")
        lines.append("")

    # Next steps
    if plan:
        pending = [
            s for s in plan.get("steps", [])
            if s["status"] in ("pending", "in-progress")
        ]
        if pending:
            lines.append("## Next Steps")
            for step in pending:
                if step["status"] == "in-progress":
                    lines.append(f"-> Continue: {step['title']}")
                else:
                    lines.append(f"- {step['title']}")
            lines.append("")

    return "\n".join(lines)
