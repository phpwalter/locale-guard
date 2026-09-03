from __future__ import annotations

import shutil
from pathlib import Path

from .model import LocaleGuardConfig


class AssetError(RuntimeError):
    pass


def tool_root() -> Path:
    return Path(__file__).resolve().parents[1]


def required_flag_codes(config: LocaleGuardConfig) -> tuple[str, ...]:
    codes = [config.canonical.country.lower()]
    codes.extend(language.country.lower() for language in config.languages.values())
    return tuple(dict.fromkeys(codes))


def expected_flag_sources(config: LocaleGuardConfig) -> dict[Path, Path]:
    source_root = tool_root() / "assets" / "flags"
    outputs: dict[Path, Path] = {}
    for code in required_flag_codes(config):
        source = source_root / f"{code}.svg"
        if not source.is_file():
            raise AssetError(f"required bundled flag is missing: {source}")
        outputs[config.output.flag_directory / source.name] = source
    return outputs


def copy_flags(config: LocaleGuardConfig) -> None:
    for destination, source in expected_flag_sources(config).items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
