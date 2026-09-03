from __future__ import annotations

from pathlib import Path

import pytest

from locale_guard.config import ConfigError, load_config
from locale_guard.coverage import calculate_coverage
from locale_guard.engine import check, update
from locale_guard.markers import MarkerError, replace_marked_section


def write_config(root: Path, *, minimum: float | None = None) -> Path:
    minimum_line = f"\n      minimum_coverage: {minimum}" if minimum is not None else ""
    text = f"""version: 1
canonical:
  code: en
  name: English
  country: US
  root: docs/en
translations:
  root: docs/i18n
  languages:
    es:
      name: Español
      country: ES{minimum_line}
    de:
      name: Deutsch
      country: DE
    ja:
      name: 日本語
      country: JP
files:
  include:
    - \"**/*.md\"
output:
  status_report: docs/_generated/localization-status.md
  flag_directory: docs/_generated/assets/flags
readme:
  enabled: true
  path: README.md
navigation:
  enabled: true
"""
    path = root / ".locale-guard.yml"
    path.write_text(text, encoding="utf-8")
    return path


def make_project(root: Path) -> Path:
    (root / "docs/en/architecture").mkdir(parents=True)
    (root / "docs/i18n/es/architecture").mkdir(parents=True)
    (root / "docs/i18n/de/architecture").mkdir(parents=True)
    (root / "docs/i18n/ja/architecture").mkdir(parents=True)
    markers = "<!-- locale-guard:language-bar:start -->\nold\n<!-- locale-guard:language-bar:end -->"
    (root / "docs/en/architecture/a.md").write_text(f"# A\n\n{markers}\n", encoding="utf-8")
    (root / "docs/en/architecture/b.md").write_text("# B\n", encoding="utf-8")
    (root / "docs/i18n/es/architecture/a.md").write_text(f"# A ES\n\n{markers}\n", encoding="utf-8")
    (root / "README.md").write_text(
        "# Demo\n\n<!-- locale-guard:summary:start -->\nstale\n<!-- locale-guard:summary:end -->\n",
        encoding="utf-8",
    )
    return write_config(root)


def test_coverage_is_derived_from_canonical_tree(tmp_path: Path) -> None:
    config = load_config(make_project(tmp_path))
    report = calculate_coverage(config)
    assert report.canonical_total == 2
    assert report.languages["es"].present == 1
    assert report.languages["es"].percentage == 50.0
    assert report.languages["de"].percentage == 0.0


def test_update_generates_all_project_owned_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = load_config(make_project(tmp_path))
    import locale_guard.assets as assets
    import locale_guard.immutability as immutability

    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(assets, "tool_root", lambda: repo_root)
    monkeypatch.setattr(immutability, "tool_root", lambda: repo_root)

    report = update(config)
    assert report.languages["es"].percentage == 50.0
    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "Español" in readme
    assert "50.0%" in readme
    status = tmp_path / "docs/_generated/localization-status.md"
    assert status.is_file()
    assert "Missing 1 document(s)" in status.read_text(encoding="utf-8")
    assert (tmp_path / "docs/_generated/assets/flags/es.svg").is_file()
    en = (tmp_path / "docs/en/architecture/a.md").read_text(encoding="utf-8")
    assert "Español" in en
    assert "docs/i18n" not in en


def test_check_is_read_only_and_detects_stale_outputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = load_config(make_project(tmp_path))
    import locale_guard.assets as assets

    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(assets, "tool_root", lambda: repo_root)
    result = check(config, enforce_immutable=False)
    assert not result.ok
    assert any("README" in item for item in result.problems)
    assert not (tmp_path / "docs/_generated/localization-status.md").exists()


def test_check_passes_after_update(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = load_config(make_project(tmp_path))
    import locale_guard.assets as assets

    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(assets, "tool_root", lambda: repo_root)
    update(config)
    result = check(config, enforce_immutable=False)
    assert result.ok


def test_minimum_coverage_gate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    make_project(tmp_path)
    config = load_config(write_config(tmp_path, minimum=80))
    import locale_guard.assets as assets

    repo_root = Path(__file__).resolve().parents[1]
    monkeypatch.setattr(assets, "tool_root", lambda: repo_root)
    update(config)
    result = check(config, enforce_immutable=False)
    assert not result.ok
    assert any("below required 80.0%" in item for item in result.problems)


def test_canonical_language_cannot_be_translation(tmp_path: Path) -> None:
    path = tmp_path / ".locale-guard.yml"
    path.write_text(
        """version: 1
canonical: {code: en, name: English, root: docs/en}
translations:
  root: docs/i18n
  languages:
    en: {name: English, country: US}
""",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError):
        load_config(path)


def test_markers_require_exact_pair() -> None:
    with pytest.raises(MarkerError):
        replace_marked_section("nothing", "START", "END", "body")
    assert replace_marked_section("A START old END Z", "START", "END", "new") == "A START\nnew\nEND Z"


def test_double_star_include_matches_canonical_root_files(tmp_path: Path) -> None:
    config_path = make_project(tmp_path)
    (tmp_path / "docs/en/root.md").write_text("# Root\n", encoding="utf-8")
    config = load_config(config_path)
    report = calculate_coverage(config)
    assert report.canonical_total == 3
    assert any(doc.relative_path.as_posix() == "root.md" for doc in report.documents)
