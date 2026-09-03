from __future__ import annotations

import fnmatch
from pathlib import Path

from .model import DocumentStatus, LocaleGuardConfig


class ScanError(RuntimeError):
    pass


def _matches(path: Path, patterns: tuple[str, ...]) -> bool:
    value = path.as_posix()
    name = path.name
    for pattern in patterns:
        candidates = (pattern, pattern[3:]) if pattern.startswith("**/") else (pattern,)
        if any(fnmatch.fnmatch(value, candidate) or fnmatch.fnmatch(name, candidate) for candidate in candidates):
            return True
    return False


def discover_documents(config: LocaleGuardConfig) -> tuple[DocumentStatus, ...]:
    canonical_root = config.canonical.root
    if not canonical_root.exists() or not canonical_root.is_dir():
        raise ScanError(f"canonical documentation root does not exist: {canonical_root}")

    documents: list[DocumentStatus] = []
    for path in sorted(p for p in canonical_root.rglob("*") if p.is_file()):
        relative = path.relative_to(canonical_root)
        if not _matches(relative, config.files.include):
            continue
        if config.files.exclude and _matches(relative, config.files.exclude):
            continue
        translations = {
            code: candidate if candidate.is_file() else None
            for code, language in config.languages.items()
            if (candidate := language.root / relative)
        }
        documents.append(DocumentStatus(relative_path=relative, canonical_path=path, translations=translations))
    return tuple(documents)
