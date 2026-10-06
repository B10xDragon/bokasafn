# Local data and backups

The app remains static and uses `library_v15`. `library_v14` is never modified.
Version 15 still references books by numeric catalog ID. Its existing read,
wishlist, review, goal, daily-time, total-time, unresolved-title and running-timer
fields keep their original meaning. Unknown legacy titles remain recoverable.

Additive fields:

- `completedDates`: last recorded local completion date by book ID. Old read
  flags have no invented completion date. Pages count only completed books.
- `sessions`: unique ID, local save date and elapsed seconds for each newly saved
  timer session. Old aggregate time is not converted into fictional sessions.
- `achievements`: achievement ID and first unlock date. Unlocks remain earned.
- `challenges`: unique ID, escaped display title, kind, target, start/end local
  dates, baseline book IDs, baseline seconds for the starting day, completion date.

Daily reading history retains its recorded local date when moved between time
zones. Timers split at local midnight using calendar arithmetic, including DST.
Weekly goals retain the existing rolling-seven-day definition. Monthly goals use
calendar-month-to-date time. Both current and longest streaks count consecutive
local dates satisfying the chosen goal, with yesterday grace for current streak.
No target means ten minutes daily. Changing the target recalculates past streaks;
already unlocked achievements remain earned. Activity days mean days with any
saved time, independently of the goal.

A monthly book challenge includes known completions from that calendar month.
Other book challenges count completions after joining and exclude baseline books.
Minute challenges subtract reading already saved on the starting day. An author
challenge compares authors against all books read when joining.

# Import rules

JSON envelopes use `format: bokasafn-backup`, `backupVersion: 1`, `data`,
`preferences.theme`, export time/timezone, and archived legacy/recovery data.
Exports also include exact persisted data. Raw v14/v15 objects can be imported.
Unknown schema versions, invalid types/dates/reviews/history/challenges/sessions,
files above 5 MB and excessively large arrays are rejected before mutation.

Import offers merge or explicit confirmed replacement. Active timer sessions must
be finished first; imported running sessions are archived but never resumed (to
avoid counting time spent transferring a file as reading). Before any write, the
current data/preferences and import source are archived under
`library_import_backup_<timestamp>` keys. Storage failure aborts without claiming
success. Exports include these recovery copies; they can also be found in browser
storage. Replacement does not remove v14 or recovery copies.

Merge unions read/wishlist IDs, retains conflicting existing reviews and current
goal/theme settings, deduplicates sessions/challenges by ID, retains earned
achievements, unions unresolved titles and combines personal goals by exact text.
For overlapping daily totals it uses the maximum, not addition; total reading time
is at least either backup's total and the sum of merged daily time. This prevents
repeated import from double counting, but cannot distinguish independent sessions
on the same day in old aggregate data. The UI explains this conservative rule.

# Local recommendations

Books already read or personally rated 1–2 are excluded. Ratings 4–5 contribute
+2/+3 to their categories and twice that to their author; ratings 1–2 contribute
-4/-8. Unrated wishlist books contribute +1/+2 and read books +0.25/+0.5.
A candidate gets the sum of its category and author weights plus 4 if wishlisted.
Ties use stable book ID. Without history, catalog ID gives a deterministic starter
selection. Each suggestion states its main positive signal. No API is involved.
Advanced rating filters/sorts use personal ratings, not a public average.

The site has no accounts, backend, current-reading state or current-page tracking.

Repeated joins cannot create another active copy of a built-in challenge. The
monthly challenge can be joined once per calendar month, even after completion;
other built-ins can be joined again after completing the previous challenge.
Identical old challenge records are grouped into one displayed card. Different
baselines or completion dates remain separate. Grouping never deletes stored
records, and exports retain every ID. Deleting the displayed card explicitly
removes all identical copies represented by that card.
