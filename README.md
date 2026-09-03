# LocaleGuard

LocaleGuard is a deterministic localization governance tool for documentation repositories. It measures translation coverage against canonical English docs, generates language navigation and completeness metrics, identifies missing files, and helps teams prevent drift, reduce manual tracking, and keep multilingual documentation consistent through CI.

## Core contract

LocaleGuard **does not translate documentation**. It governs localization state.

A consuming repository defines one canonical documentation tree and zero or more localized trees. LocaleGuard treats the canonical tree as the denominator, matches localized documents by relative path, calculates completeness, generates presentation artifacts, and validates that those artifacts are current.

LocaleGuard is designed to be consumed as an **immutable Git submodule dependency**. A consuming project MUST NOT modify files inside the LocaleGuard checkout. Project configuration, documentation, generated reports, and generated flag assets remain owned by the parent repository.

## Recommended consuming-project layout

```text
my-project/
├── README.md
├── .locale-guard.yml
├── docs/
│   ├── en/                         # canonical documentation
│   │   ├── architecture/
│   │   ├── process/
│   │   ├── specifications/
│   │   └── technical/
│   ├── i18n/
│   │   ├── es/
│   │   ├── de/
│   │   └── ja/
│   └── _generated/
│       ├── localization-status.md
│       └── assets/flags/
└── tools/
    └── locale-guard/               # immutable Git submodule
```

The identity of a document is its path relative to the canonical root. For example:

```text
Canonical: docs/en/architecture/system-overview.md
Identity:  architecture/system-overview.md
Spanish:   docs/i18n/es/architecture/system-overview.md
German:    docs/i18n/de/architecture/system-overview.md
Japanese:  docs/i18n/ja/architecture/system-overview.md
```

A localized counterpart either exists or does not exist. LocaleGuard 0.1 does not attempt to score translation quality or freshness.

## Installation as an immutable submodule

From the parent repository:

```bash
git submodule add https://github.com/phpwalter/locale-guard.git tools/locale-guard
git -C tools/locale-guard checkout foundation
git add .gitmodules tools/locale-guard
```

The parent repository pins the exact LocaleGuard commit. Upgrading LocaleGuard is therefore an explicit dependency change.

## Configuration

Copy `.locale-guard.example.yml` to `.locale-guard.yml` in the parent repository and tailor it to the project.

```yaml
version: 1

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
      country: ES
    de:
      name: Deutsch
      country: DE
    ja:
      name: 日本語
      country: JP

files:
  include:
    - "**/*.md"
  exclude:
    - "_generated/**"
    - "_templates/**"

output:
  status_report: docs/_generated/localization-status.md
  flag_directory: docs/_generated/assets/flags

readme:
  enabled: true
  path: README.md

navigation:
  enabled: true
```

Language codes are localization identities. Country codes are presentation metadata used only to select a flag. LocaleGuard never treats a flag as the identity of a language.

## README localization panel

LocaleGuard controls only the marked section of the parent README:

```html
<!-- locale-guard:summary:start -->
<!-- locale-guard:summary:end -->
```

`update` calculates completeness from the live repository tree and replaces that section with the generated language panel. Percentages are never stored as authoritative data.

## Per-document language navigation

Add these markers to any canonical or localized Markdown document that should display language navigation:

```html
<!-- locale-guard:language-bar:start -->
<!-- locale-guard:language-bar:end -->
```

LocaleGuard replaces only the content inside the markers. Existing translations become links; missing translations remain visible as unavailable languages.

## Commands

When LocaleGuard is used as a submodule:

```bash
python -B tools/locale-guard/locale_guard.py scan
python -B tools/locale-guard/locale_guard.py update
python -B tools/locale-guard/locale_guard.py check
python -B tools/locale-guard/locale_guard.py missing es
python -B tools/locale-guard/locale_guard.py json --pretty
```

`scan` calculates current coverage without writing files.

`update` regenerates project-owned README content, status report, language navigation, and required flag copies.

`check` is strictly read-only. It recalculates expected output and fails when repository state differs.

`missing <language>` lists canonical documents with no counterpart for a configured language.

`json` exposes coverage for dashboards and external automation.

## CI policy

LocaleGuard intentionally distinguishes incomplete translation coverage from broken governance.

By default, missing translations do **not** fail CI. The following do:

- invalid configuration;
- stale generated README localization data;
- stale generated status reports;
- stale language-navigation regions;
- missing or stale generated flag assets;
- malformed language-bar markers;
- modifications to the immutable LocaleGuard dependency;
- failure of an explicitly configured minimum-coverage threshold.

A project may opt into a threshold:

```yaml
translations:
  root: docs/i18n
  languages:
    es:
      name: Español
      country: ES
      minimum_coverage: 80
```

## CI adapters

Examples are provided for:

- GitHub Actions: `ci/github/locale-guard.yml`
- GitLab CI: `ci/gitlab/locale-guard.yml`
- Azure DevOps: `ci/azure-devops/locale-guard.yml`
- Bitbucket Pipelines: `ci/bitbucket/locale-guard.yml`

The consuming pipeline checks out submodules, installs PyYAML, and runs:

```bash
python -B tools/locale-guard/locale_guard.py check
```

CI never rewrites parent-repository files. Developers or release automation run `update` and commit generated changes explicitly.

## Generated assets

LocaleGuard keeps master flag assets under `assets/flags/` inside the immutable dependency. `update` copies only the flags required by the consuming project's configuration to its configured generated-assets directory. This keeps rendered documentation self-contained while the dependency remains immutable.

## Determinism

LocaleGuard's governing invariant is:

> Given the same configuration and repository state, LocaleGuard produces the same localization status and generated output.

No network calls, translation APIs, LLMs, timestamps, or external databases are required during scanning, generation, or CI validation.

## Development

The `foundation` branch is the active integration branch for version `0.1.0`. The test suite covers configuration validation, canonical scanning, derived completeness, generated outputs, read-only checks, quality gates, and marker integrity.

Run:

```bash
python -m pip install -e . pytest
python -m pytest
```

## License

LocaleGuard is released under the MIT License. See `LICENSE`.
