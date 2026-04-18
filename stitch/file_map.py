import os
from datetime import datetime
from pathlib import Path

from stitch import APP_DIR
from stitch.store import get_file_map_path, read_json, write_json

IGNORE_DIRS = {
    # Version control
    ".git", ".svn", ".hg",
    # Python
    "__pycache__", ".venv", "venv", "env", ".env",
    ".tox", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".eggs", "*.egg-info",
    # Node / JS
    "node_modules", ".next", ".nuxt", ".output",
    "bower_components",
    # Build output
    "dist", "build", "out", "target", "_build",
    # Package managers
    ".yarn", ".pnp",
    # IDE / editor
    ".idea", ".vscode", ".fleet",
    # OS
    ".DS_Store", "Thumbs.db",
    # Rust
    "target",
    # Go
    "vendor",
    # Ruby
    ".bundle",
    # PHP
    "vendor",
    # Misc caches
    ".cache", ".parcel-cache", ".turbo", ".vercel",
    ".terraform", ".serverless",
    # Stitch itself
    APP_DIR,
}

IGNORE_EXTENSIONS = {
    # Compiled
    ".pyc", ".pyo", ".so", ".dll", ".exe", ".o", ".obj",
    ".class", ".jar", ".war",
    # Source maps / locks
    ".map",
    # Media (usually not relevant to AI)
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg",
    ".mp3", ".mp4", ".wav", ".avi",
    ".ttf", ".woff", ".woff2", ".eot",
    # Archives
    ".zip", ".tar", ".gz", ".bz2", ".rar",
    # DB
    ".sqlite", ".db",
}

IGNORE_FILES = {
    ".DS_Store", "Thumbs.db",
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "Pipfile.lock", "poetry.lock", "composer.lock",
    "Gemfile.lock", "Cargo.lock",
}


def scan_project(project_dir: Path, max_depth: int = 4) -> dict:
    files = {}
    for root, dirs, filenames in os.walk(project_dir):
        dirs[:] = [
            d for d in dirs
            if d not in IGNORE_DIRS and not d.startswith(".")
        ]
        depth = len(Path(root).relative_to(project_dir).parts)
        if depth > max_depth:
            dirs.clear()
            continue
        for filename in filenames:
            if filename in IGNORE_FILES:
                continue
            filepath = Path(root) / filename
            if filepath.suffix in IGNORE_EXTENSIONS:
                continue
            rel_path = str(filepath.relative_to(project_dir)).replace("\\", "/")
            files[rel_path] = ""
    return {"files": files, "scanned_at": datetime.now().isoformat()}


def save_file_map(project_dir: Path) -> dict:
    file_map = scan_project(project_dir)
    existing = read_json(get_file_map_path())
    if existing.get("files"):
        for path, desc in existing["files"].items():
            if path in file_map["files"] and desc:
                file_map["files"][path] = desc
    write_json(get_file_map_path(), file_map)
    return file_map


def update_file_description(file_path: str, description: str):
    file_map = read_json(get_file_map_path())
    if "files" not in file_map:
        file_map["files"] = {}
    file_map["files"][file_path] = description
    write_json(get_file_map_path(), file_map)
    return file_map
