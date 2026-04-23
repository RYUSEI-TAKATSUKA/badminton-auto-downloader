from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# True when running inside a PyInstaller-built bundle.
IS_FROZEN = bool(getattr(sys, "frozen", False))


def _user_data_root() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        return Path(base) / "BWF Draw"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "BWF Draw"
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))) / "bwf-draw"


def _user_documents_root() -> Path:
    if sys.platform == "win32":
        return Path.home() / "Documents" / "BWF Draws"
    if sys.platform == "darwin":
        return Path.home() / "Documents" / "BWF Draws"
    return Path.home() / "BWF Draws"


if IS_FROZEN:
    PROFILE_DIR: Path = _user_data_root() / "profile"
    OUTPUT_ROOT: Path = _user_documents_root()
else:
    PROFILE_DIR = REPO_ROOT / "profile"
    OUTPUT_ROOT = REPO_ROOT / "output"


def ensure_dirs() -> None:
    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
