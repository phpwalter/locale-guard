from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class CanonicalConfig:
    code: str
    name: str
    country: str
    root: Path


@dataclass(frozen=True)
class LanguageConfig:
    code: str
    name: str
    country: str
    root: Path
    minimum_coverage: float | None = None


@dataclass(frozen=True)
class FileRules:
    include: tuple[str, ...]
    exclude: tuple[str, ...]


@dataclass(frozen=True)
class ReadmeConfig:
    enabled: bool
    path: Path
    start_marker: str
    end_marker: str
    show_flags: bool
    show_counts: bool
    show_percentages: bool
    show_progress: bool


@dataclass(frozen=True)
class OutputConfig:
    status_report: Path
    flag_directory: Path


@dataclass(frozen=True)
class NavigationConfig:
    enabled: bool
    start_marker: str
    end_marker: str


@dataclass(frozen=True)
class LocaleGuardConfig:
    version: int
    project_root: Path
    canonical: CanonicalConfig
    languages: Mapping[str, LanguageConfig]
    files: FileRules
    readme: ReadmeConfig
    output: OutputConfig
    navigation: NavigationConfig


@dataclass(frozen=True)
class DocumentStatus:
    relative_path: Path
    canonical_path: Path
    translations: Mapping[str, Path | None]


@dataclass(frozen=True)
class LanguageCoverage:
    code: str
    name: str
    country: str
    present: int
    missing: int
    total: int
    percentage: float
    minimum_coverage: float | None


@dataclass(frozen=True)
class CoverageReport:
    canonical_total: int
    documents: tuple[DocumentStatus, ...]
    languages: Mapping[str, LanguageCoverage]
