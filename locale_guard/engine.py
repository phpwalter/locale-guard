from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .assets import copy_flags, expected_flag_sources
from .coverage import calculate_coverage
from .generators.navigation import expected_navigation_updates
from .generators.readme import expected_readme
from .generators.report import render_status_report
from .immutability import check_immutable_dependency
from .model import CoverageReport, LocaleGuardConfig


@dataclass(frozen=True)
class CheckResult:
    report: CoverageReport
    problems: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.problems


def _same_bytes(first: Path, second: Path) -> bool:
    return first.is_file() and first.read_bytes() == second.read_bytes()


def check(config: LocaleGuardConfig, *, enforce_immutable: bool = True) -> CheckResult:
    problems: list[str] = []
    if enforce_immutable:
        try:
            check_immutable_dependency()
        except Exception as exc:
            problems.append(str(exc))

    report = calculate_coverage(config)

    expected = expected_readme(config, report)
    if expected is not None:
        current = config.readme.path.read_text(encoding="utf-8")
        if current != expected:
            problems.append(f"README localization summary is stale: {config.readme.path}")

    expected_report = render_status_report(config, report)
    if not config.output.status_report.is_file() or config.output.status_report.read_text(encoding="utf-8") != expected_report:
        problems.append(f"localization status report is stale: {config.output.status_report}")

    for path, expected_text in expected_navigation_updates(config, report).items():
        if path.read_text(encoding="utf-8") != expected_text:
            problems.append(f"language navigation is stale: {path}")

    for destination, source in expected_flag_sources(config).items():
        if not _same_bytes(destination, source):
            problems.append(f"generated flag asset is stale or missing: {destination}")

    for coverage in report.languages.values():
        if coverage.minimum_coverage is not None and coverage.percentage < coverage.minimum_coverage:
            problems.append(
                f"{coverage.name} coverage {coverage.percentage:.1f}% is below required {coverage.minimum_coverage:.1f}%"
            )

    return CheckResult(report=report, problems=tuple(problems))


def update(config: LocaleGuardConfig) -> CoverageReport:
    report = calculate_coverage(config)
    copy_flags(config)

    expected = expected_readme(config, report)
    if expected is not None:
        config.readme.path.write_text(expected, encoding="utf-8")

    config.output.status_report.parent.mkdir(parents=True, exist_ok=True)
    config.output.status_report.write_text(render_status_report(config, report), encoding="utf-8")

    for path, expected_text in expected_navigation_updates(config, report).items():
        path.write_text(expected_text, encoding="utf-8")

    return report
