from __future__ import annotations

import os
from pathlib import Path


def relative_link(from_file: Path, to_path: Path) -> str:
    return Path(os.path.relpath(to_path, start=from_file.parent)).as_posix()


def progress_bar(percentage: float, width: int = 10) -> str:
    filled = max(0, min(width, int(round((percentage / 100.0) * width))))
    return "█" * filled + "░" * (width - filled)


def html_flag(src: str, alt: str, width: int = 22) -> str:
    return f'<img src="{src}" alt="{alt}" width="{width}" height="auto">'
