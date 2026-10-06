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
  dates, baseline book IDs, baseline seconds for the starting day, optional
  history mode, and completion date.

Daily reading history retains its recorded local date when moved between time
zones. Timers split at local midnight using calendar arithmetic, including DST.
Weekly goals retain the existing rolling-seven-day definition. Monthly goals use
calendar-month-to-date time. Both current and longest streaks count consecutive
local dates satisfying the chosen goal, with yesterday grace for current streak.
No target means ten minutes daily. Changing the target recalculates past streaks;
already unlocked achievements remain earned. Activity days mean days with any
saved time, independently of the goal.

A monthly book challenge includes known completions from that calendar month.
The first built-in fantasy and new-author challenges also recognise already-read
books, including legacy flags without known completion dates. Existing first
challenges recover this recognition automatically. Their completion date records
recognition, not an invented historical book date. Repeat attempts store
`historyMode: since-start` and require new completions after joining. Other book
challenges count completions after joining and exclude baseline books.
Minute challenges subtract reading already saved on the starting day. An author
challenge compares authors against all books read when joining on repeat attempts;
the first attempt recognises authors already discovered in the reading history.

# Import rules

JSON envelopes now use `format: bokasafn-backup`, `backupVersion: 2`, `data`,
`preferences.theme`, export time/timezone and complete `storage.local` /
`storage.session` snapshots of the app's namespaced user keys. The catalog is not
part of user data. Older version 1 envelopes and raw v14/v15 objects still import.
Unknown schema versions and invalid types/dates/reviews/history/challenges/timers
are rejected before mutation. There is no application-imposed backup text/file
length cap or truncation. Actual memory, clipboard and browser storage capacity
still apply; failures are reported without claiming successful restoration.

Import offers merge or explicitly confirmed replacement. A current active timer
must be finished first. Version 2 replacement restores a saved timer as well:
paused timers stay paused; running timers continue from their saved checkpoint,
including elapsed time while the backup was being transferred, consistent with
existing refresh recovery. Merge and legacy version 1 imports do not resume an
incoming timer. Both formats use exactly the same validation and import pipeline.

Before changes, current data/preferences/storage and the import source are
archived under `library_import_backup_<unique-ID>` keys. Version 2 replacement
restores imported namespaced storage and preserves the new rollback copies.
Merge keeps conflicting existing storage values. Storage failures attempt rollback
to the exact preceding memory and storage state and report an error. App snapshots
never read, replace or delete another site's unrelated storage keys.

# One-line encoding

`BOKASAFN:1:<UTF-8-byte-length>:<CRC32-hex>:<Base64URL-payload>` encodes compact
JSON of the same version 2 envelope used by file export. The line is ASCII and
contains no newline characters, even when reviews/goals contain line breaks,
Icelandic, emoji, quotes, Unicode separators or lone surrogate code units (JSON
escapes these before UTF-8 encoding). No fields are removed to shorten the line.
Length and CRC32 checks detect missing/corrupted payloads before validation. The
Base64URL encoding must be canonical. Unknown line/envelope versions are rejected
with Icelandic errors. CRC32 detects accidental damage; it is not an authenticity
signature. Encoding is not encryption. The UI explicitly treats backups as private.

# Complete reset

`Eyða öllum gögnum` opens the existing accessible dialog with a warning that only
an external backup allows recovery, Cancel focused first, and a red confirmation
button. Cancellation/Escape leave memory and storage intact. Confirmation removes
all `library_*` and `bokasafn-*`/`bokasafn_*` local and session storage keys,
including v14, recovery copies and imported backup sources. It stops the timer,
clears all reading state, cached imports, text drafts, filters, sort, URL book
selection and theme preference, then immediately shows the fresh-user catalog.
A later page save may create an empty v15 record, but old data cannot resurrect
from legacy/recovery keys. Unrelated origin storage and catalog/site files remain.

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

Reset also guards against asynchronous resurrection: pending file reads are
invalidated, other open tabs stop their timers and reload after deletion, and a
save compares the persisted library with the tab's last observed value before
writing. A stale tab must reload instead of overwriting a deletion/replacement.

Text-backup copying uses a canonical generated envelope, never the export field's
selection. Both the native Clipboard API and the editable-textarea fallback copy
that exact envelope. The fallback supplies the complete string in the copy event
and requires both a successful copy command and a populated clipboard event;
API rejection automatically retries it. On iOS it runs synchronously during the
original tap to retain user activation. Manual copying from the export field also
supplies the complete envelope, even when only part was selected. Closing the
dialog clears the private canonical string. Framing and integrity validation are
unchanged; payload-only strings remain invalid.

The case-sensitive marker is shared by the sole encoder and strict decoder.
Every copy representation uses the generated canonical string and checks that it
is identical to the export DOM value with the exact uppercase prefix. Fallback
and manual copying clear inherited URL types and write both HTML (literal span)
and plain text. iOS uses these two representations via ClipboardItem if the
synchronous fallback fails, rather than plain-only writeText. Other browsers
retain writeText. No invisible characters or format changes are introduced.
The import field inserts raw text/plain from paste events without allowing the
browser to substitute a URL representation; no case conversion is performed.

This addresses the transport risk documented in WebKit bug 253708
(https://bugs.webkit.org/show_bug.cgi?id=253708), where `Hello:` copies/pastes as
`hello:`. Chromium tests verify literal clipboard contents and model URL-preferred
insertion; physical iOS remains necessary to confirm the platform workaround.
