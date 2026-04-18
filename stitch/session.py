from datetime import datetime

from stitch.store import (
    get_session_path,
    get_sessions_dir,
    read_json,
    write_json,
)


def create_session() -> dict:
    session = {
        "id": datetime.now().strftime("%Y-%m-%d_%H%M%S"),
        "started_at": datetime.now().isoformat(),
        "ended_at": None,
        "task": None,
        "plan": None,
        "progress": [],
        "decisions": [],
        "dead_ends": [],
        "files_touched": [],
    }
    write_json(get_session_path(), session)
    return session


def get_current_session() -> dict | None:
    session = read_json(get_session_path())
    return session if session else None


def ensure_session() -> dict:
    session = get_current_session()
    if not session:
        session = create_session()
    return session


def update_session(updates: dict):
    session = ensure_session()
    session.update(updates)
    write_json(get_session_path(), session)
    _auto_save_context()
    return session


def add_to_session(key: str, entry: dict):
    session = ensure_session()
    if key not in session:
        session[key] = []
    session[key].append(entry)
    write_json(get_session_path(), session)
    _auto_save_context()
    return session


def batch_update(
    task: str = None,
    progress_items: list[str] = None,
    decisions: list[tuple[str, str]] = None,
    dead_ends: list[tuple[str, str]] = None,
    step_updates: list[tuple[str, str]] = None,
    plan_desc: str = None,
    plan_steps: list[str] = None,
):
    session = ensure_session()
    now = datetime.now().isoformat()

    if task:
        session["task"] = task

    if plan_desc:
        steps = [
            {"title": s, "detail": "", "status": "pending", "notes": ""}
            for s in (plan_steps or [])
        ]
        session["plan"] = {
            "description": plan_desc,
            "steps": steps,
            "created_at": now,
            "revised_at": None,
            "revision_history": [],
        }

    if progress_items:
        for msg in progress_items:
            session["progress"].append({"message": msg, "timestamp": now})

    if decisions:
        for choice, reason in decisions:
            session["decisions"].append({
                "choice": choice, "reason": reason, "timestamp": now,
            })

    if dead_ends:
        for what, why in dead_ends:
            session["dead_ends"].append({
                "what": what, "why": why, "timestamp": now,
            })

    if step_updates and session.get("plan"):
        for title, status in step_updates:
            for step in session["plan"]["steps"]:
                if step["title"].lower() == title.lower():
                    step["status"] = status
                    break

    write_json(get_session_path(), session)
    _auto_save_context()
    return session


def archive_session() -> dict | None:
    session = get_current_session()
    if not session:
        return None
    session["ended_at"] = datetime.now().isoformat()
    sessions_dir = get_sessions_dir()
    sessions_dir.mkdir(parents=True, exist_ok=True)
    archive_path = sessions_dir / f"{session['id']}.json"
    write_json(archive_path, session)
    return session


def get_session_history() -> list:
    sessions_dir = get_sessions_dir()
    if not sessions_dir.exists():
        return []
    sessions = []
    for f in sorted(sessions_dir.glob("*.json")):
        sessions.append(read_json(f))
    return sessions


def _auto_save_context():
    from stitch.store import is_initialized
    if not is_initialized():
        return
    from stitch.context import save_context
    save_context()


# --- Plan management ---


def set_plan(description: str, steps: list[dict]):
    plan = {
        "description": description,
        "steps": steps,
        "created_at": datetime.now().isoformat(),
        "revised_at": None,
        "revision_history": [],
    }
    update_session({"plan": plan})
    return plan


def update_plan_step(step_title: str, status: str, notes: str = None):
    session = get_current_session()
    if not session or not session.get("plan"):
        return None
    for step in session["plan"]["steps"]:
        if step["title"].lower() == step_title.lower():
            step["status"] = status
            if notes:
                step["notes"] = notes
            break
    else:
        return None
    write_json(get_session_path(), session)
    _auto_save_context()
    return session["plan"]


def revise_plan(reason: str, new_description: str = None, new_steps: list = None):
    session = get_current_session()
    if not session or not session.get("plan"):
        return None
    session["plan"]["revision_history"].append({
        "previous_description": session["plan"]["description"],
        "reason": reason,
        "revised_at": datetime.now().isoformat(),
    })
    if new_description:
        session["plan"]["description"] = new_description
    if new_steps:
        session["plan"]["steps"] = new_steps
    session["plan"]["revised_at"] = datetime.now().isoformat()
    write_json(get_session_path(), session)
    _auto_save_context()
    return session["plan"]
