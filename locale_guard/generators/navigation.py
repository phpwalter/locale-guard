from __future__ import annotations

from pathlib import Path

from ..markers import MarkerError, replace_marked_section
from ..model import CoverageReport, DocumentStatus, LocaleGuardConfig
from ..rendering import html_flag, relative_link


def _language_item(current_file: Path, target: Path | None, flag_path: Path, name: str, active: bool) -> str:
    flag = html_flag(relative_link(current_file, flag_path), name, 20)
    label = f"{flag} {name}"
    if active:
        return f"**{label}**"
    if target is not None:
        return f"[{label}]({relative_link(current_file, target)})"
    return f"{label} *(missing)*"


def render_language_bar(
    config: LocaleGuardConfig,
    document: DocumentStatus,
    current_file: Path,
    current_code: str,
) -> str:
    items = []
    canonical_flag = config.output.flag_directory / f"{config.canonical.country.lower()}.svg"
    items.append(
        _language_item(
            current_file,
            document.canonical_path,
            canonical_flag,
            config.canonical.name,
            current_code == config.canonical.code,
        )
    )
    for code, language in config.languages.items():
        flag_path = config.output.flag_directory / f"{language.country.lower()}.svg"
        items.append(
            _language_item(
                current_file,
                document.translations.get(code),
                flag_path,
                language.name,
                current_code == code,
            )
        )
    return " | ".join(items)


def expected_navigation_updates(config: LocaleGuardConfig, report: CoverageReport) -> dict[Path, str]:
    if not config.navigation.enabled:
        return {}
    updates: dict[Path, str] = {}
    for document in report.documents:
        candidates: list[tuple[str, Path]] = [(config.canonical.code, document.canonical_path)]
        candidates.extend((code, path) for code, path in document.translations.items() if path is not None)
        for code, path in candidates:
            text = path.read_text(encoding="utf-8")
            has_start = config.navigation.start_marker in text
            has_end = config.navigation.end_marker in text
            if not has_start and not has_end:
                continue
            if has_start != has_end:
                raise MarkerError(f"incomplete language-bar marker pair in {path}")
            body = render_language_bar(config, document, path, code)
            updates[path] = replace_marked_section(
                text,
                config.navigation.start_marker,
                config.navigation.end_marker,
                body,
            )
    return updates
