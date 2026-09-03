# Flag asset notice

LocaleGuard uses ISO 3166-1 alpha-2 country identifiers for display flags. Language identity is always determined by the configured language code; flags are never used as language identifiers.

The bundled flag assets are sourced from `svg-country-flags` version `1.2.10` by Hampus Nilsson, distributed with license identifier `PD` (public domain). The source package repository is `hjnilsson/country-flags`.

Bundled mappings:

- `US` -> `us.svg`
- `ES` -> `es.svg`
- `DE` -> `de.svg`
- `JP` -> `jp.svg`

The Spanish display asset preserves the package's rendered coat-of-arms detail while remaining packaged as an SVG container for consistent LocaleGuard asset handling.
