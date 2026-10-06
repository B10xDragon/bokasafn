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
proxy and CA trust. It checks all 39 repository cover images, five viewport sizes
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

Run all three real-asset suites plus `tests/browser.py` for complete verification.

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
