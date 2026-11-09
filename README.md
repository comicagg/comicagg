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

## Read snapshots and deferred cleanup

The reader signs a snapshot containing a boundary for each displayed subscription.
Marking a comic read (including voting) advances only that subscription's
`read_through` marker. Marking all read advances the markers included in the page
in one transaction. Neither action deletes unread rows during the request.
Entries delivered after the page snapshot remain unread on the next visit.
Comics not included in the page, including inactive comics, are not cleared.
Stale tabs cannot move markers backwards or affect a replacement subscription.

Ordering uses `Comic.unread_sequence` and `UnreadStrip.read_sequence`, not primary
key allocation or timestamps. Distribution allocates a sequence per strip while
holding the comic row lock until commit; ordinary unread creation acquires that
same lock in `UnreadStrip.save()`. Bulk writers must hold the comic lock, allocate
sequences, and persist the updated counter in the same transaction, as the
distributor does. Do not write counters or read markers from stale model instances;
their normal `save()` methods deliberately exclude those fields from updates.

Subscribing creates no unread entries. Distribution concurrent with subscription
may include or omit the new subscriber. Unsubscribing waits for distribution and
removes the subscription, marker, and all its unread entries. Mark-unread makes
only the latest strip unread (leaving any existing older unreads unchanged);
if that strip was logically read, it receives a fresh sequence. Operations that
both lock a comic and its subscriptions must acquire the comic lock first.
Multi-comic operations lock comics and then subscriptions in primary-key order.

The `comics.tasks.cleanup_read_strips.cleanup_read_strips` task runs every
15 minutes, deleting up to 100 batches of 1,000 logically read rows, with a
separate transaction per batch. Pending strips retain their rows until distribution
completes, because those rows suppress duplicate delivery. Task results report
the number deleted; monitor cleanup throughput and retained-row growth and tune
the task's batch limits or schedule if cleanup cannot keep up. `active()` and
`available()` on the unread manager exclude logically read rows; unfiltered
`objects`/related-manager queries intentionally include them for maintenance.

### Deployment

Stop web writes (maintenance mode) and pause comic-update, distribution, and
cleanup workers before deploying this change. Do not overlap old and new workers.
Run
`uv run python src/manage.py migrate` and
`uv run python src/manage.py ensure_tasks`, then restart web processes, Celery
workers, and beat and restore access. Migration `0016` backfills sequences from
existing unread IDs, initializes comic counters and zero read markers, consolidates
duplicate subscriptions (keeping the earliest position), and adds a relationship
constraint and unread lookup index. It updates the unread table and creates an
index, so allow maintenance time proportional to its size.
Before rolling back to code without markers, physically delete all logically read
rows while writers are stopped; simply dropping the markers would resurrect them.

Both reader mutations now require POST, CSRF, and a valid signed snapshot.
Already-open pages using the old JavaScript must be reloaded; missing or invalid
snapshots return HTTP 400 without clearing newer entries. The disabled legacy
`src/api` app is not part of this change.

New strips may take up
to the next 15-minute dispatch plus queue time to appear; the existing four-hour
comic scraping schedule is unchanged. Schedule registration follows the existing
`ensure_tasks` behavior: newly registered schedules start at midnight UTC the
following day.

Regression tests cover model and AJAX behavior, signed reader snapshots,
migrations, deferred cleanup, and concurrent PostgreSQL distribution. Run with
the normal Django environment configured, pointing `DJANGO_DATABASE` at a
dedicated PostgreSQL database whose role can create test databases:

```sh
uv run python src/manage.py test comics comicagg --noinput
npm run test:js
```

PostgreSQL is required to exercise row-lock tests; SQLite skips those tests.
The test workflow also runs the Django suites against a PostgreSQL service so
these concurrency regressions are exercised in CI.

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
