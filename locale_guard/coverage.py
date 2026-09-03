from __future__ import annotations

from .model import CoverageReport, LanguageCoverage, LocaleGuardConfig
from .scanner import discover_documents


def calculate_coverage(config: LocaleGuardConfig) -> CoverageReport:
    documents = discover_documents(config)
    total = len(documents)
    languages: dict[str, LanguageCoverage] = {}
    for code, language in config.languages.items():
        present = sum(1 for doc in documents if doc.translations.get(code) is not None)
        missing = total - present
        percentage = 0.0 if total == 0 else (present / total) * 100.0
        languages[code] = LanguageCoverage(
            code=code,
            name=language.name,
            country=language.country,
            present=present,
            missing=missing,
            total=total,
            percentage=percentage,
            minimum_coverage=language.minimum_coverage,
        )
    return CoverageReport(canonical_total=total, documents=documents, languages=languages)
