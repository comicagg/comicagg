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

## Admin database statistics

Superusers can open **Database statistics** under **Other actions** in the admin,
or visit `/admin/database-statistics/`. The view shows exact row counts for all
installed, managed model tables, including automatically created many-to-many
tables. Proxy models are excluded because they share an existing table.
Counts are queried on every visit and can be expensive for large tables.

## Strip distribution

New strips are stored with `unreads_distributed=False`. Every 15 minutes, the
`comics.tasks.distribute_strips.distribute_pending_strips` Celery task queues one
`distribute_comic_strips` task per comic with pending strips. Each worker creates
unread rows for that comic's active subscribers in batches of at most 1,000,
then marks the selected strips distributed in the same transaction. Subscriptions
are evaluated when the worker runs. Duplicate tasks serialize on a comic row lock;
failures roll back and pending strips are retried on the next scheduled run.
Completed distribution is tracked independently of unread rows, so repeat tasks
do not make already-read strips unread again.

Deploy with comic-update and distribution workers paused, run
`uv run python src/manage.py migrate` and
`uv run python src/manage.py ensure_tasks`, then restart Celery workers and beat.
The migration marks historical strips distributed and consolidates duplicate
unread rows before adding uniqueness for `(user, strip)`. New strips may take up
to the next 15-minute dispatch plus queue time to appear; the existing four-hour
comic scraping schedule is unchanged. Schedule registration follows the existing
`ensure_tasks` behavior: newly registered schedules start at midnight UTC the
following day.

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
