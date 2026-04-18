import json
from pathlib import Path

from stitch import APP_DIR


def get_stitch_dir() -> Path:
    return Path.cwd() / APP_DIR


def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def read_json(path: Path) -> dict:
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def write_json(path: Path, data: dict):
    ensure_dir(path.parent)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def write_text(path: Path, text: str):
    ensure_dir(path.parent)
    path.write_text(text, encoding="utf-8")


def get_config_path() -> Path:
    return get_stitch_dir() / "config.json"


def get_session_path() -> Path:
    return get_stitch_dir() / "current_session.json"


def get_sessions_dir() -> Path:
    return get_stitch_dir() / "sessions"


def get_context_path() -> Path:
    return get_stitch_dir() / "context.md"


def get_file_map_path() -> Path:
    return get_stitch_dir() / "file_map.json"


def is_initialized() -> bool:
    return get_stitch_dir().exists() and get_config_path().exists()
