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
