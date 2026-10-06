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
