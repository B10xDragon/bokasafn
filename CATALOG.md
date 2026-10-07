# Forlagið catalog maintenance

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
