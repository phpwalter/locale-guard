from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .model import CanonicalConfig, FileRules, LanguageConfig, LocaleGuardConfig, NavigationConfig, OutputConfig, ReadmeConfig


class ConfigError(ValueError):
    pass


def _mapping(value: Any, key: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigError(f"'{key}' must be a mapping")
    return value


def _string(value: Any, key: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"'{key}' must be a non-empty string")
    return value.strip()


def _path(project_root: Path, value: Any, key: str) -> Path:
    raw = _string(value, key)
    path = Path(raw)
    if path.is_absolute():
        raise ConfigError(f"'{key}' must be project-relative, not absolute")
    normalized = (project_root / path).resolve()
    try:
        normalized.relative_to(project_root.resolve())
    except ValueError as exc:
        raise ConfigError(f"'{key}' must remain inside the project root") from exc
    return normalized


def load_config(config_path: Path) -> LocaleGuardConfig:
    config_path = config_path.resolve()
    if not config_path.exists():
        raise ConfigError(f"configuration file not found: {config_path}")

    project_root = config_path.parent.resolve()
    try:
        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML: {exc}") from exc

    root = _mapping(data, "root")
    version = root.get("version", 1)
    if version != 1:
        raise ConfigError(f"unsupported configuration version: {version}")

    canonical_raw = _mapping(root.get("canonical"), "canonical")
    canonical_code = _string(canonical_raw.get("code"), "canonical.code")
    canonical = CanonicalConfig(
        code=canonical_code,
        name=_string(canonical_raw.get("name"), "canonical.name"),
        country=_string(canonical_raw.get("country", "US"), "canonical.country").upper(),
        root=_path(project_root, canonical_raw.get("root"), "canonical.root"),
    )

    translations_raw = _mapping(root.get("translations"), "translations")
    translation_root = _path(project_root, translations_raw.get("root"), "translations.root")
    languages_raw = _mapping(translations_raw.get("languages"), "translations.languages")
    if not languages_raw:
        raise ConfigError("at least one translated language must be configured")

    languages: dict[str, LanguageConfig] = {}
    for code, language_value in languages_raw.items():
        if not isinstance(code, str) or not code.strip():
            raise ConfigError("language codes must be non-empty strings")
        code = code.strip()
        if code == canonical_code:
            raise ConfigError(f"canonical language '{canonical_code}' must not appear in translations.languages")
        language = _mapping(language_value, f"translations.languages.{code}")
        minimum = language.get("minimum_coverage")
        if minimum is not None:
            if not isinstance(minimum, (int, float)) or not 0 <= float(minimum) <= 100:
                raise ConfigError(f"minimum coverage for '{code}' must be between 0 and 100")
            minimum = float(minimum)
        languages[code] = LanguageConfig(
            code=code,
            name=_string(language.get("name"), f"translations.languages.{code}.name"),
            country=_string(language.get("country"), f"translations.languages.{code}.country").upper(),
            root=(translation_root / code).resolve(),
            minimum_coverage=minimum,
        )

    files_raw = _mapping(root.get("files", {}), "files")
    include = files_raw.get("include", ["**/*.md"])
    exclude = files_raw.get("exclude", [])
    if not isinstance(include, list) or not all(isinstance(item, str) and item for item in include):
        raise ConfigError("files.include must be a list of glob strings")
    if not isinstance(exclude, list) or not all(isinstance(item, str) and item for item in exclude):
        raise ConfigError("files.exclude must be a list of glob strings")

    output_raw = _mapping(root.get("output", {}), "output")
    output = OutputConfig(
        status_report=_path(project_root, output_raw.get("status_report", "docs/_generated/localization-status.md"), "output.status_report"),
        flag_directory=_path(project_root, output_raw.get("flag_directory", "docs/_generated/assets/flags"), "output.flag_directory"),
    )

    readme_raw = _mapping(root.get("readme", {}), "readme")
    display_raw = _mapping(readme_raw.get("display", {}), "readme.display")
    section_raw = _mapping(readme_raw.get("section", {}), "readme.section")
    readme = ReadmeConfig(
        enabled=bool(readme_raw.get("enabled", True)),
        path=_path(project_root, readme_raw.get("path", "README.md"), "readme.path"),
        start_marker=_string(section_raw.get("start_marker", "<!-- locale-guard:summary:start -->"), "readme.section.start_marker"),
        end_marker=_string(section_raw.get("end_marker", "<!-- locale-guard:summary:end -->"), "readme.section.end_marker"),
        show_flags=bool(display_raw.get("flags", True)),
        show_counts=bool(display_raw.get("counts", True)),
        show_percentages=bool(display_raw.get("percentages", True)),
        show_progress=bool(display_raw.get("progress_bar", True)),
    )

    navigation_raw = _mapping(root.get("navigation", {}), "navigation")
    navigation = NavigationConfig(
        enabled=bool(navigation_raw.get("enabled", True)),
        start_marker=_string(navigation_raw.get("start_marker", "<!-- locale-guard:language-bar:start -->"), "navigation.start_marker"),
        end_marker=_string(navigation_raw.get("end_marker", "<!-- locale-guard:language-bar:end -->"), "navigation.end_marker"),
    )

    return LocaleGuardConfig(
        version=version,
        project_root=project_root,
        canonical=canonical,
        languages=languages,
        files=FileRules(tuple(include), tuple(exclude)),
        readme=readme,
        output=output,
        navigation=navigation,
    )
