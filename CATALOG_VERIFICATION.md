# Catalog expansion verification — 7 October 2026

## Final inventory

| Measure | Result |
|---|---:|
| Previous books | 39 |
| Final books | 1,046 |
| Added books | 1,007 |
| Books with local covers | 1,046 |
| Books with verified page counts | 861 |
| Unknown page counts | 185 |
| New books with verified publication years | 874 |
| New editions with explicit Icelandic-language evidence | 329 |
| New Icelandic-focused listings without explicit edition-language labeling | 678 |
| Distinct candidate product URLs explored | 1,132 |
| Duplicate listings rejected | 27 |
| Other entries skipped | 98 |

The 98 other exclusions comprise 75 missing authors, four insufficient descriptions,
one ambiguous same-title/different-author identity and 18 scope exclusions
(foreign-language/maps, activity/stationery items, an overlapping trilogy bundle,
a workbook, a blank journal and a poster). Metadata was not invented to fill gaps.
Language counts are conservative: an Icelandic title or an author's nationality alone
does not establish an edition's language. Foreign-language sections were excluded.

## Categories

Categories overlap; these counts are not meant to sum to the catalog size.

| Category | Books |
|---|---:|
| Ungmenni | 487 |
| Barnabækur | 226 |
| Skáldverk | 337 |
| Skáldsögur | 291 |
| Þýddar bækur | 173 |
| Fræðibækur | 154 |
| Spenna | 106 |
| Fantasía | 95 |
| Myndasögur | 94 |
| Klassík | 93 |
| Glæpir | 57 |
| Rómantík | 24 |
| Ráðgáta | 22 |
| Hrollvekja | 22 |
| Vísindaskáldsaga | 20 |
| Ævisögur | 14 |
| Ævintýri | 13 |
| Ljóð | 5 |
| Grín | 1 |

## Sources and collection

Forlagið was the sole source for all 1,007 additions. Discovery visited 63 category
pages across nine sections: all 27 teenage pages, all ten children's nonfiction
pages, all four classics pages and the science-fiction page, plus complementary
samples of younger children's books, comics, Icelandic fiction, thrillers and
translated fiction. See [the category pagination and totals](Resources/catalog-report.json).
The larger remaining sections were not exhaustively collected.

Each accepted book was verified on its own product page. Author/creator credits,
selected edition's explicit page/year cells and main product image were isolated
from related-product cards. Covers were fetched from Forlagið, proportionally
resized and cached locally as WebP. Two requests could be in flight, with starts
globally spaced at least one second apart; cached downloads were reused.

[Source evidence](Resources/catalog-sources.json) records URLs, product IDs,
edition selection, verification dates and SHA-256 hashes for original HTML,
original cover bytes and local cover bytes. All 1,007 cached product/cover pairs
were reparsed and checked with zero errors and zero new network requests.
The validator also found zero errors in IDs, titles, author fields, normalized
categories, optional numbers, cover existence/hashes, duplicate detection and
candidate accounting. All original 39 complete records match the fixture exactly.

Descriptions include 258 reviewed original story/topic summaries and 749 original
bibliographic summaries. No full publisher descriptions were committed; the original
HTML and descriptions remain in the external maintenance cache.

## Automated results

All suites passed after the final data and layout corrections.

| Suite | Passed |
|---|---:|
| Node regression — UTC | 47 |
| Node regression — America/New_York | 47 |
| Node regression — Atlantic/Reykjavik | 47 |
| Catalog normalization/language/scope tools | 15 |
| Offline browser regression | 9 groups |
| Live real-asset browser regression | 11 groups |
| Features browser | 8 groups |
| Backups browser | 9 groups |
| Clipboard browser | 11 groups |
| Expanded catalog browser | 6 groups |

The 54 browser groups covered 320/390/768/1440/1920px layouts, all five themes,
both pages, search/suggestions and Unicode normalization, combined category/read/
wishlist/advanced filters, every sorting mode, reviews/ratings, timer refresh
recovery, goals/streaks, v14 migration and corrupt/denied storage, achievements,
challenges, recommendations, random selection, statistics, all local covers,
dialogs/focus/Escape/keyboard controls, new-book URLs and Back/Forward, and
pre-expansion JSON and BOKASAFN text backups. Tests also read/save/review every
catalog book and check statistics and both backup formats against all 1,046 IDs.
Clipboard checks include literal uppercase canonical values, native and fallback
copying, Unicode, corruption, truncation and backups larger than 1 MB.

## Performance

Measured with Chromium on the local static server, actual site styles/dependencies
and cached CDN asset files. Filter timing includes rendering, forced layout and
two animation frames; 18 measurements were taken for each catalog size.

| Measure | Result |
|---|---:|
| Initial catalog ready | 1,051.5 ms |
| Initial displayed cards | 60 |
| Initial grid descendant elements | 783 |
| Original 39 filter/layout median / maximum | 35.8 / 100.9 ms |
| Expanded filter/layout median / maximum | 122.5 / 169.4 ms |
| Every book read/wishlisted/reviewed: statistics/archive render | 412.6 ms |
| Deployed book JSON | 599,546 bytes |
| All local catalog covers | 39,115,772 bytes |

The initial grid is bounded. Load-more displays another 60 cards with keyboard
focus handling; all search/filter/recommendation/random/routing operations use the
complete catalog. Intermediate filter/sort renders are suppressed and archive
images load lazily. Timings are local-environment observations, not a mobile-network
or physical-device benchmark.

## Problems found and corrected

- New pagination initially survived a full user-data reset. Reset now restores the
  initial batch and filter signature without losing catalog data.
- A new long Icelandic compound word overflowed the 320px book dialog.
  Dialog text now wraps long words and its flex column can shrink. Longest titles
  and longest individual words are regression-tested.
- Edition/presentation variants, original Hunger Games entries and overlapping
  Moomin collections required additional duplicate normalization/exclusions.
- Diary novels were initially excluded alongside blank journals; 13 novels were
  recovered and the scope rule is regression-tested.
- Fantasy/classic store categories needed explicit normalization. Nonfiction
  topic mentions now cannot become fiction genres without an explicit store genre.
- Older browser assertions assumed the entire catalog was in the DOM. They now
  verify the complete filtered result and the displayed batch separately.

## Limits and follow-up work

Physical iPad/iOS Safari, Android devices, Firefox and a working WebKit browser
were not available for this pass. Chromium used mobile viewport/touch emulation;
the iOS clipboard paths were simulated and exercised against Chromium's actual
clipboard, not verified on a physical iPad. Real Tailwind, Font Awesome and Google
Font files were used. Every cover was checked through the real local HTTP server,
but no physical book or current warehouse stock was checked.

The source's language labeling and optional edition metadata remain incomplete.
More of the bibliographic descriptions could be expanded into reviewed story/topic
summaries. Further source pages can be collected using the documented cache workflow
while retaining shipped IDs. Source creator taxonomy can include illustrators;
credits are retained as Forlagið lists them.

The original 39 records were preserved, not freshly resourced. One known legacy
issue remains: book 39, Hvísl hrafnanna, lists Maggie Stiefvater while its existing
cover credits Malene Sølvsten. A future metadata correction can retain ID 39.
Nothing in this expansion renumbers or replaces that saved-book identity.
