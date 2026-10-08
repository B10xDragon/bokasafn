# Reviewed 13+ catalog

The 8 October 2026 cleanup supersedes the expansion policy below. The active
catalog contains only approved Forlagið products. Every pre-cleanup ID has an
explicit decision in `Resources/catalog-decisions.json` and a corresponding
six-question result in `Resources/catalog-audit.json`. Uncertain entries are
quarantined for teacher/librarian review, not assumed to be unsuitable or silently
removed. The audit records source categories, a short description excerpt,
verification date/hash, reasons, and every metadata correction.

Never delete historical identities or renumber books. The frozen baseline is
`tests/fixtures/pre-cleanup-books.json`. `Resources/catalog-identities.json` holds
reviewed duplicate aliases and complete archived book records. Its generated
`js/catalog-identities.js` is part of the static deployment. Keep it synchronized.

To repeat curation, reverify product pages using the collector, preserve its cache,
review every decision, then run:

```sh
python scripts/curate_catalog.py --verified /path/to/verified.json --cache /path/to/cache
python scripts/validate_catalog.py
python tests/catalog_tools.py
```

`verified.json` contains one `{catalogId, record}` or `{catalogId, url, error}`
for each baseline ID. `record` is the collector's parsed Forlagið metadata. The
curator refuses missing decisions, unverified retained products, missing identity
approval, alias chains and absent verification attempts. Category/author exceptions
require explicit per-book decisions, with reasons from the publisher text. Unknown
edition page/year values remain null. Explicit translator credits in the source
text are separated from novel authors; unqualified creator credits remain as the
publisher lists them.

The validator fails definite errors, including duplicate IDs/title-author pairs,
missing metadata, broken/altered covers, invalid numeric metadata, excluded
categories, missing Forlagið evidence, inconsistent audit membership and reused
archived IDs. Likely subtitle/creator variants and easy-reader signals are reported
for review rather than automatically merged. Meaningful volume numbers and different
authors remain distinct. The expansion builder refuses to resurrect retired entries
once this audit exists; any further additions need reviewed source/identity evidence.
Keep the site static; these Python tools run only during maintenance.

## Historical expansion notes (superseded where they conflict with the audit)


All additions use individual product pages on https://www.forlagid.is/ as the
sole metadata source. Category pages discover candidates; they do not substitute
for product-page verification. `Resources/catalog-sources.json` records each
product URL/ID, source categories, chosen physical edition, cover URL and hashes,
verification date and how language was assessed. The catalog report records the
category pagination visited, counts and rejected entries. Stock availability can
change after the verification date; listing a book does not promise stock.

The original 39 complete records are preserved in `tests/fixtures` and checked
against the deployed JSON. Their IDs, titles and page counts remain unchanged.
New IDs are `1000000 + Forlagið product ID`; sorting never assigns identities. The builder refuses to remove or replace an ID
from the catalog committed at HEAD (or the current file in a non-Git checkout).
Retain the source cache when refreshing; another edition must not take over a
shipped identity.
Keep existing entries and IDs when refreshing sources. Do not regenerate an
existing book from another edition's product ID or replace its identity.

Collectors use edition-insensitive title keys for punctuation, case, paperback,
ebook and presentation tags. Same-title ambiguity is skipped and recorded rather
than merging unrelated books. Similar series titles still require review because
volume numbers matter. The builder additionally rejects normalized duplicates. Reviewed bundle/journal
exclusions are recorded in `Resources/catalog-exclusions.json`.

`pages` and `publicationYear` are `null` when not reliably listed. Page counts
come from the selected edition's explicit “Síður” cell; digits in descriptions,
prices and unrelated products are never used as page counts. Language is recorded
as Icelandic only when supported by an Icelandic/translation category or explicit
translation credit or explicit Icelandic-edition statement on the product page. Other entries have Icelandic titles and descriptions in the
Icelandic catalog, but the edition language may not be explicitly labeled.
Foreign-language/map categories are excluded. Store categories are mapped to the
small Icelandic category set; explicit genre claims in descriptions supplement
them. `catalog-category-overrides.json` records a few reviewed fantasy additions
where the synopsis describes magic or supernatural fictional settings but the
store only supplies an age category.

Descriptions in `catalog-summaries.json` are short original summaries written
from the product page. Remaining descriptions summarize bibliographic facts and
source categories; they do not invent storylines. Full publisher descriptions
and downloaded HTML stay in the external collector cache, outside the repository.

Covers are selected from the current product's main image, excluding related
products. Local filenames use its product ID. They are proportionally reduced
without cropping to at most 360×540 and saved as WebP; no other image service is
used. Source and resulting bytes have separate SHA-256 hashes.

## Build-time tools

```sh
python -m pip install -r scripts/requirements.txt
python scripts/collect_forlagid.py --cache /path/to/preserved-cache
python scripts/build_catalog.py --cache /path/to/preserved-cache
python scripts/validate_catalog.py
python scripts/verify_source_cache.py --cache /path/to/preserved-cache
```

Preserve the cache for reruns: requests reuse already downloaded pages/images.
At most two requests are in flight and starts are globally spaced at least one
second apart. Failed requests back off. Collection does not modify `books.json`;
building is a separate review step. Review summaries, duplicate/skip reports and
validation before committing. `verify_source_cache.py` reparses each original
cached product page, verifies the Forlagið canonical URL, and checks the selected
cover URL and original image bytes. It makes no network requests. The deployed website has no Python dependencies.

## Rendering and compatibility

Search/filter/sorting, recommendations, random selection and URLs use the entire
catalog. The grid initially displays 60 matching books, then exposes more through
“Sýna fleiri bækur”. Changing filters resets the visible slice; reading/wishlist
changes with the same filters preserve it. Keyboard focus moves to the first newly
shown book. Filter/sorting wrappers suppress intermediate renders so only the
final result reaches the DOM. Cover images retain lazy loading, including saved-book/review archives.
Script and main-stylesheet URLs carry the catalog release version so a cached older renderer does not
load alongside the new pagination wrappers.
Book-dialog text wraps long Icelandic compound words, and its text column can shrink
beside the cover; the longest catalog titles and words are checked at 320px.

The existing library_v14/v15 storage and JSON/text backup formats are unchanged.
`tests/fixtures/pre-expansion-reading.*` represents data backed up with the original
catalog and is imported against the expanded catalog in the regression tests.
Run all existing suites plus `tests/catalog_browser.py`; the browser suite measures
initial rendering, filter latency and DOM size with real site dependencies.
