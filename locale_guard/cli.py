from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import ConfigError, load_config
from .coverage import calculate_coverage
from .engine import check, update
from .markers import MarkerError
from .scanner import ScanError


def _print_coverage(report) -> None:
    print("LocaleGuard")
    print("=" * 72)
    print(f"Canonical documents: {report.canonical_total}")
    print("-" * 72)
    for coverage in report.languages.values():
        print(
            f"{coverage.name:<20} {coverage.present:>5} / {coverage.total:<5} "
            f"{coverage.percentage:>6.1f}%   missing={coverage.missing}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="locale-guard", description="Deterministic documentation localization governance")
    parser.add_argument("--config", default=".locale-guard.yml", help="project-relative configuration path")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("scan", help="calculate and display localization coverage")
    sub.add_parser("update", help="regenerate README, report, language bars, and flag assets")
    sub.add_parser("check", help="verify generated localization state without modifying files")
    missing = sub.add_parser("missing", help="list missing canonical documents for a language")
    missing.add_argument("language", help="configured translated language code")
    json_parser = sub.add_parser("json", help="emit machine-readable coverage JSON")
    json_parser.add_argument("--pretty", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = load_config(Path(args.config))
        if args.command == "scan":
            _print_coverage(calculate_coverage(config))
            return 0
        if args.command == "update":
            report = update(config)
            _print_coverage(report)
            print("\nGenerated localization state updated.")
            return 0
        if args.command == "check":
            result = check(config)
            _print_coverage(result.report)
            if result.ok:
                print("\n[PASS] LocaleGuard validation passed.")
                return 0
            print("\n[FAIL] LocaleGuard validation failed:")
            for problem in result.problems:
                print(f"  - {problem}")
            print("\nRun 'locale-guard update' (or the submodule wrapper) and commit generated changes.")
            return 1
        if args.command == "missing":
            report = calculate_coverage(config)
            if args.language not in report.languages:
                parser.error(f"unknown translated language: {args.language}")
            coverage = report.languages[args.language]
            print(f"{coverage.name}: {coverage.present}/{coverage.total} ({coverage.percentage:.1f}%)")
            for document in report.documents:
                if document.translations.get(args.language) is None:
                    print(document.relative_path.as_posix())
            return 0
        if args.command == "json":
            report = calculate_coverage(config)
            payload = {
                "canonical": {"total": report.canonical_total, "code": config.canonical.code},
                "languages": {
                    code: {
                        "name": coverage.name,
                        "present": coverage.present,
                        "missing": coverage.missing,
                        "total": coverage.total,
                        "percentage": round(coverage.percentage, 4),
                    }
                    for code, coverage in report.languages.items()
                },
            }
            print(json.dumps(payload, indent=2 if args.pretty else None, sort_keys=True))
            return 0
    except (ConfigError, ScanError, MarkerError, FileNotFoundError, OSError, RuntimeError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    return 2
