# Regression checks

Run the dependency-free data, timer, and filtering checks with Node.js:

```sh
node tests/regression.test.cjs
```

Run the browser checks with Python, Playwright, and Chromium installed:

```sh
python tests/browser.py
```

Set `CHROMIUM_PATH` if Chromium is not at `/usr/bin/chromium`.
The browser suite serves repository files through Playwright routes. It supplies
minimal Tailwind layout utilities and excludes third-party fonts/icons, so it
tests functionality without depending on CDNs. It is not a visual regression test.

Run the second-pass browser checks with real styling and dependencies:

```sh
python tests/live_browser.py
```

This suite starts a local HTTP server and downloads the actual Tailwind script,
Font Awesome CSS/fonts, and Google Fonts through curl using the environment's
proxy and CA trust. It checks the initial cover batch, five viewport sizes
(320, 390, 768, 1440, and 1920 pixels), both views, every theme, mobile touch,
search/filter/sorting flows, reviews, timers, goals, migration, slow startup, and
failed saves. Dependency caches and screenshots are saved in the system temporary
directory. Network access and curl are required. This is Chromium testing with
emulated mobile input, not testing on physical Android/iOS devices.

Saved data migrates from `library_v14` to `library_v15`. The original v14 copy is
left untouched. Unmatched legacy titles are retained in `unresolved` and retried
on future catalog loads. Corrupt v15 text is backed up under a recovery key before
falling back to the v14 copy; unknown future schema versions are not overwritten.

Active timers continue from their saved start time after reopening the page;
paused timers stay paused. Stopping writes reading totals and the cleared session
in one operation. Failed writes leave the session available for retry. Midnight
crossings allocate time to each local date.

Daily streaks use the selected minute target. Weekly streaks count consecutive
days meeting the rolling-seven-day target; monthly streaks count consecutive days
meeting the calendar-month-to-date target. With no target, the existing ten-minute
daily reading threshold remains. Historical streaks are recalculated when the
target changes because the original app does not record goal history.

New feature checks:

- `node tests/regression.test.cjs` includes additive v15 history, safe backups/merge,
  achievements, challenge baselines, recommendations, advanced filters and random
  selection. Run with `TZ=America/New_York` and `TZ=Atlantic/Reykjavik` too.
- `python tests/features_browser.py` uses the same real CDN assets as the live suite.
  It checks all five themes at 320/390/768/1440/1920px, actual downloads/imports,
  cross-browser storage transfer, deep links and history, random/filter controls,
  achievements/challenges and keyboard heatmap navigation.

The older dialog tests locate the final focusable control rather than assuming
that the review-save button is last, because book views now include a share link.

Full reset and portable text-backup checks:

- `node tests/regression.test.cjs` additionally checks CRC32/byte-length framing,
  Unicode and lone-surrogate round trips, large backups beyond the previous size
  limits, rejected corruption/truncation/versions, namespaced deletion/rollback
  and version 1 / version 2 / v14 compatibility.
- `python tests/backups_browser.py` uses real assets to check confirmation,
  Cancel/Escape, fresh-user reset with an active timer, no refresh resurrection,
  full native clipboard copy, matching JSON/text envelopes, exact restoration
  of reading data/theme/recovery/session storage and a paused timer, merge and
  replacement, validation, all themes at phone/tablet widths, and denied
  deletion/clipboard fallback.

Run every real-asset suite plus `tests/browser.py` for complete verification.

The reset suite also checks delayed file reads and two open tabs cannot revive
old data, large clipboard export/delete/import, and a running timer's restoration,
refresh recovery and final save. New York and Reykjavík regression runs include
all reset/backup tests.

`python tests/clipboard_browser.py` adds eleven real-asset clipboard groups covering
canonical framing/display, native clipboard writes independent of DOM/selection,
partial manual copying, Safari selection simulation, absent/rejected Clipboard
API fallback, iPad desktop-user-agent dispatch, honest failure reporting, real
copy/paste/validate/delete/import with Unicode, and backups larger than 1 MB.
These tests use Chromium's actual system clipboard. iOS detection and partial
selection are simulated; they do not replace verification on a physical iPad.
Run this suite in addition to all four existing browser suites and regression tests.

Clipboard case checks require generated === displayed === actual clipboard text,
including explicit `BOKASAFN:1:` and rejected `bokasafn:` prefixes, for native
writeText, manual copy and the fallback. Additional checks exercise typed iOS
ClipboardItems with identical plain/HTML text, clear stale URL types, model the
iOS URL-promotion bug, and insert literal text/plain on paste while the importer
continues rejecting lowercase input. The URL-promotion model is not physical iOS.

Expanded Forlagið catalog checks:

```sh
python tests/catalog_tools.py
python scripts/validate_catalog.py
python tests/catalog_browser.py
```

These check edition normalization, explicit language evidence, preservation of the
original 39 identities (including archived records), unique IDs, normalized categories, known/unknown page counts,
metadata and local cover hashes, real-server loading of every cover, new book IDs,
Unicode normalization in search, bounded rendering and keyboard load-more,
combined filters/sorting/recommendations/random selection, deep links/history,
320px dialogs, pre-expansion JSON/text imports and measured filter latency.
Performance results are written to the temporary verification artifact directory.
The grid shows at most 60 cards initially; tests check the full filtered result
independently of this displayed slice.

Complete pass: run the Node suite (UTC, New York and Reykjavík), catalog tools
and validator, then all six Python browser suites: `browser`, `live_browser`,
`features_browser`, `backups_browser`, `clipboard_browser` and `catalog_browser`.

Reviewed cleanup checks:

```sh
python tests/cleanup_browser.py
```

Run this seventh browser suite in addition to all six existing suites. It exercises
real mobile Chromium, exact pre-migration rollback, duplicate and archived history,
conflicting review visibility, date/challenge preservation, JSON and BOKASAFN
round trips, repeated imports, statistics, excluded discovery/random/recommendation
candidates and retained/alias/archive/unknown book routes. The Node suite adds
idempotent normalization and conflicting import checks; catalog tools now exercise
strict errors versus likely-match warnings and legitimate same-title/different-author
and numbered-series cases. Frozen pre-cleanup identities replace the former
assumption that original metadata could never be corrected.

Series and author browsing adds `node tests/browse.test.cjs` (13 unit checks),
`python tests/browsing_tools.py` (8 validator checks), and
`python tests/browse_browser.py` (7 real-server browser groups). These exercise
verified ordering with gaps, unknown numbers, multiple authors, conservative
name normalization, typed search, catalog-only progress, direct links and
Back/Forward, unchanged portable backups, all five themes and 320–1920px
layouts, keyboard focus and complete-catalog performance.

Run `python scripts/validate_browsing.py` after changing catalog metadata;
see [BROWSING.md](../BROWSING.md) for the source review and maintenance process.

Complete-series and title maintenance adds:

```sh
python scripts/validate_completion.py
python tests/completion_tools.py
python tests/completion_browser.py
```

Run all three catalog validators, all Python tool suites, the Node regression
suite in UTC/New York/Reykjavík, `node tests/browse.test.cjs`, and all nine browser
suites (`browser`, `live_browser`, `features_browser`, `backups_browser`,
`clipboard_browser`, `catalog_browser`, `cleanup_browser`, `browse_browser`,
`completion_browser`). The completion checks cover finite/unknown totals,
missing and unknown numbers, title aliases, all original IDs and metadata,
held unsuitable additions, cover evidence, cleaned book dialogs, historical
edition aliases, conflict preservation, old-title imports and mobile notes.
See [SERIES_COMPLETION.md](../SERIES_COMPLETION.md) and its machine-readable test
report for the latest full-run results.

Responsive UI checks:

```sh
python tests/responsive_browser.py
python -m playwright install firefox webkit
python -m playwright install-deps firefox webkit
python tests/cross_engine_browser.py
```

The six responsive groups render all 17 requested widths and 12 intermediate
widths, all five themes, touch/keyboard disclosures, dialogs, simulated keyboard
viewport geometry, long titles/backups, contrast and 200% text scaling. They
write actual screenshots and measurements to the temporary verification artifact
folder. Cross-engine tests add four groups using Firefox and Linux WebKit;
`--engines firefox` or `--engines webkit` runs one installed engine explicitly.
Missing engines/dependencies fail rather than silently claiming coverage.
Run both alongside all nine existing browser suites and the existing Node/tool
checks. Keep the catalog performance benchmark isolated from parallel browsers.
See [RESPONSIVE_DESIGN.md](../RESPONSIVE_DESIGN.md) for implementation details,
verified coverage, screenshots and physical-device limitations.
