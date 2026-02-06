from pathlib import Path
from .config import settings

def ensure_dirs():
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.outputs_dir.mkdir(parents=True, exist_ok=True)

def safe_join(base: Path, name: str) -> Path:
    # very simple filename safety
    name = name.replace("/", "_").replace("\\", "_")
    return base / name
