[![ci](https://github.com/comicagg/comicagg/actions/workflows/ci.yml/badge.svg?branch=development)](https://github.com/comicagg/comicagg/actions/workflows/ci.yml)
[![tests](https://github.com/comicagg/comicagg/actions/workflows/test.yml/badge.svg?branch=development)](https://github.com/comicagg/comicagg/actions/workflows/test.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/comicagg/comicagg/badge)](https://scorecard.dev/viewer/?uri=github.com/comicagg/comicagg)

# comicagg

This is the Django code for the website at https://www.comicagg.com

Currently built with Python 3.14 and Django 5.2.

## Python development

Use Python 3.14 and uv 0.12.12. From the repository root, install the runtime
dependencies and development tools with:

```sh
uv sync
```

To include the optional Django Debug Toolbar dependencies, use the `debug` group:
`uv sync --group debug`. Ruff lint and formatting checks are:

```sh
uv run ruff check src
uv run ruff format --check src
```

## JavaScript behavior tests

From the repository root, with Node.js 22 or newer:

```sh
npm ci
npx playwright install --with-deps chromium
npm run test:js
```

The Playwright suite in `tests/javascript/` loads the application scripts in
Chromium. It checks DOM visibility, filtering, layout and scrolling, image
loading/retry, counters, cookie consent, blog navigation, request confirmations,
and request methods, form encoding, CSRF headers, and success/failure UI.
Responses and images are intercepted locally; no Django server, database, CDN, or
external website is needed. Unexpected requests and uncaught browser errors fail
tests. The suite also runs in the Tests workflow; failure traces are uploaded.

These are characterization tests for the JavaScript migration, not full Django
end-to-end tests. Fixture markup represents the current page hooks, but does not
render Django templates or exercise htmx swaps. Organization tests substitute only
the independent Dojo container/event boundary: actual drag gestures and Dojo itself
are not covered. The application scripts use only native browser APIs (no Prototype
or jQuery); update the centralized script loading in `fixtures.js` and page hooks as
necessary, retaining the observable behavior and HTTP assertions.

Named `fixme` cases document existing defects without requiring their preservation:
omitted consent-request callbacks, saving an empty list, and
multi-comic trash removal. They are skipped, not passing coverage; enable and refine
their regression tests when fixing those defects.
