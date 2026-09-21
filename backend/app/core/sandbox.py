import re
import os
from pathlib import Path
from uuid import UUID
from typing import Optional

from app.config import settings

# Patterns for dangerous operations that must be blocked
BLOCKED_PATTERNS = [
    # Unix root or broad destructive deletion
    r"\brm\s+-[a-zA-Z]*[rf][a-zA-Z]*\s+([/~]|\$HOME|\.\./\.\.)",
    r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f",
    r"\brm\s+-[a-zA-Z]*f[a-zA-Z]*r",
    r"\brm\s+--no-preserve-root",
    # Windows root or disk deletion
    r"\bdel\b.*(?:/[sS]|-[sS]|/[qQ]|-[qQ]).*[cC]:",
    r"\bdel\b.*[cC]:[\\/]",
    r"\brd\b.*[cC]:",
    r"\brmdir\b.*[cC]:",
    # Formatting disks
    r"\bmkfs",
    r"\bformat\s+[a-zA-Z]:",
    r"\bfdisk\b",
    r"\bparted\b",
    # Fork bombs
    r":\(\)\s*\{[^}]*:\s*\|\s*:\s*&\s*\};:",
    r"%\s*0\s*\|\s*%\s*0",
    # Destructive powershell
    r"Remove-Item\b.*-[rR]ecurse.*[cC]:",
    r"Remove-Item\b.*-[fF]orce.*[cC]:",
    # Dangerous system tampering
    r"\bchmod\s+-R\s+777\s+/",
    r"\bchown\s+-R\s+.*(?:\s+/|\s+/etc|\s+/var)",
    # Shutdown / restart
    r"\bshutdown\s+/[sSrR]",
]

COMPILED_BLOCKED = [re.compile(p, re.IGNORECASE) for p in BLOCKED_PATTERNS]

MAX_DEFAULT_TIMEOUT = 60  # seconds
MAX_OUTPUT_BYTES = 500_000  # 500 KB output limit


def is_safe_command(command: str) -> tuple[bool, Optional[str]]:
    """Validate whether a shell command is safe to execute."""
    cleaned = command.strip()
    if not cleaned:
        return False, "Command is empty"

    for pattern in COMPILED_BLOCKED:
        if pattern.search(cleaned):
            return False, f"Command contains forbidden or hazardous operation matching pattern: {pattern.pattern}"

    return True, None


def get_project_workspace_dir(project_id: str | UUID) -> Path:
    """Return and create the isolated project workspace directory."""
    base_dir = Path(settings.WORKSPACE_DIR).resolve()
    target_dir = (base_dir / str(project_id)).resolve()

    # Safety check: ensure target_dir is strictly within base_dir
    if not str(target_dir).startswith(str(base_dir)):
        raise ValueError("Directory traversal detected")

    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir
