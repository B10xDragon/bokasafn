# Series and author browsing

The catalog now contains 663 active books with 351 stable author identities.
62 series contain 276 assigned books; 56 have multiple available books.
See [SERIES_COMPLETION.md](SERIES_COMPLETION.md) for the catalog-wide completion
and title audit, verified additions, explicit gaps and audience holds.

Bókaflokkar and Höfundar appear in the existing navigation. Direct links use
`?series=eragon`, `?author=arnaldur-indridason` and `?browse=series|author`.
Book links continue using `?book=ID`; opening a book from a series or author
preserves that context. Refresh and browser Back/Forward restore the selection.

Directories offer name search, cover previews and book counts, with 36 results
per render. Series show available books in verified reading order, existing
read/wishlist controls, progress and book details with previous/next available
numbered books. Author pages include related series, category and reading-status
filters, and title/page sorting. Main search covers titles, authors and series,
with Bók, Bókaflokkur and Höfundur suggestion labels. Search normalizes case,
Unicode accents and Icelandic characters; names retain their original spelling.

## Reviewed metadata

`Resources/series-audit.json` records a decision for every active book, with the
publisher product URL, title, review date, captured HTML SHA-256 and evidence.
Verified entries include the publisher description and related active book IDs
used for cross-checking. All 493 original product pages were freshly verified on 2026-10-09, and every
new product page was verified on Forlagið. Raw publisher titles remain separate
from clean `catalogTitle` values. No other source, biography or portrait is used.

`no_verified_evidence` means the reviewed publisher metadata did not establish
literary series membership; it does not assert that a book is standalone.
Publishing imprints and mentions of other works are excluded. Unnamed sequels
and trilogies remain flagged rather than receiving invented series names.

85 books require further series review: 49 unassigned/uncertain and 36 with
verified membership but unknown numbering. These remain available as books.
Unknown ordinals appear last, explicitly labelled, and have no previous/next
navigation. Vera uses the publisher's product-title numbers consistently rather
than mixing them with translated publication counts.

Verified `total` describes a finite main sequence. `knownTotal` records only a
verified lower bound when the final length is unknown. The UI displays available
versus known totals and missing/unresolved numbers separately from reading
progress, which counts only available members once per read ID. Harry Potter
has seven available works and progress out of seven; Eragon has three of four
and progress out of three. Companion works are excluded from main-series counts.

## Maintaining the data

- Keep book IDs, series IDs and author IDs stable across display-name changes.
- Add an optional `series` object to a book only after reviewing Forlagið:
  `{ "id": "eragon", "name": "Eragon", "number": 1 }`.
  Use `number: null` for unknown order. Add `total` only with publisher evidence.
- Keep definitions in `Resources/series.json` consistent with book metadata.
  Update that book's audit decision and publisher evidence at the same time.
- Every book has `authorIds`; `Resources/authors.json` supplies names and aliases.
  Compare complete names using Unicode normalization, case and punctuation;
  keep diacritics for identity comparisons. Do not fuzzy-merge different people.
  Each coauthor gets a separate identity. Translators retain their existing role.
- When editing the author registry, regenerate `js/browse-metadata.js` using
  `python scripts/build_browse_metadata.py`.
- Run `python scripts/validate_catalog.py`,
  `python scripts/validate_browsing.py` and `python scripts/validate_completion.py`, then the browsing tests.

The browsing validator fails on duplicate/stale identities, invalid references,
missing audits or source mismatches, inconsistent names/totals, invalid ordinal
values, and repeated known ordinals. Unknown ordinals produce warnings.
Catalog curation preserves additive series and author metadata; subsequent
publisher changes still require validating the author identities and series.

No storage schema changed. Reading history, archived entries, ratings, reviews,
challenges, recommendations and JSON/BOKASAFN backups use existing IDs and data.
The site remains static with no new runtime dependency or backend.

## Validation

See `Resources/series-completion-tests.json` for current counts and measured performance;
`Resources/browsing-test-results.json` records the earlier browsing implementation.
The regression suite passes in UTC, Atlantic/Reykjavik and America/New_York.
All existing browser suites and the seven new browsing groups pass. Mobile
checks cover 320px and larger widths across every theme, with keyboard controls
and screen-reader labels. Existing catalog tests also verify cover loading,
recommendations, random selection, sorting, statistics and loading performance.

Title changes keep the old display title in `titleAliases` and its historical
identity in `legacyTitles`. Never overwrite an existing legacy title mapping to
point at a different author's book. New additions require a reviewed event in
`series-completion-audit.json`, fresh source evidence and an approved audience
assessment. Keep the earlier cleanup audit unchanged. The historical curation
script deliberately refuses replay after this later maintenance audit exists.
