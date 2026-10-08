# Series and author browsing

The 493 active books and their IDs are unchanged. Forlagið evidence identifies
59 series containing 94 books; 25 series contain multiple available books.
348 author identities cover the entire catalog, including coauthors.

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
used for cross-checking. Research reuses the complete Forlagið product-page
captures verified on 2026-10-08 during the catalog audit; each capture was checked
against its recorded hash and the active catalog's source URL. No other source
was used. No titles, covers, biographies or portraits were added.

`no_verified_evidence` means the reviewed publisher metadata did not establish
literary series membership; it does not assert that a book is standalone.
Publishing imprints and mentions of other works are excluded. Unnamed sequels
and trilogies remain flagged rather than receiving invented series names.

59 books require further review: 49 have unassigned/uncertain series metadata
and ten have verified membership but unknown numbering. These remain available
as books. Unknown ordinals appear last, explicitly labelled, and have no
previous/next navigation. Vera's publisher title and description use conflicting
numbering, so the conflicting ordinal was withheld. All uncertain titles and
reasons are in the machine-readable audit.

Verified totals describe the publisher's series, not library completeness.
Progress always counts only available catalog members, once per existing read
ID. For example, Harry Potter has four available books (4–7), so progress is
out of four even though the verified series total is seven. Split volumes of
Bölvun múmíunnar use the explicit fyrri/seinni labels for order; no total is
asserted. Author-character sequences use the publisher's labels, not a guessed
bibliographic order.

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
- Run both `python scripts/validate_catalog.py` and
  `python scripts/validate_browsing.py`, then the browsing tests.

The browsing validator fails on duplicate/stale identities, invalid references,
missing audits or source mismatches, inconsistent names/totals, invalid ordinal
values, and repeated known ordinals. Unknown ordinals produce warnings.
Catalog curation preserves additive series and author metadata; subsequent
publisher changes still require validating the author identities and series.

No storage schema changed. Reading history, archived entries, ratings, reviews,
challenges, recommendations and JSON/BOKASAFN backups use existing IDs and data.
The site remains static with no new runtime dependency or backend.

## Validation

See `Resources/browsing-test-results.json` for counts and measured performance.
The regression suite passes in UTC, Atlantic/Reykjavik and America/New_York.
All existing browser suites and the seven new browsing groups pass. Mobile
checks cover 320px and larger widths across every theme, with keyboard controls
and screen-reader labels. Existing catalog tests also verify cover loading,
recommendations, random selection, sorting, statistics and loading performance.
