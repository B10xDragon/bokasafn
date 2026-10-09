# Compact recommendations and responsive layout audit

Changes are confined to UI, accessibility and tests. The catalog, book IDs,
reading-data schema and backup formats are unchanged.

## Recommendations

“Mælt með fyrir þig” is a native `details`/`summary` disclosure, closed on a
fresh page load. Its approximately 50px header matches “Ítarlegar síur”, with
an icon, suggestion count, chevron and synchronized `aria-expanded` and
`aria-controls`. Enter, Space and touch work without a custom keyboard handler.
Opening it renders the existing algorithm’s recommendations with small lazy
covers, complete titles, authors, reasons and book-detail buttons. “Hvað á ég
að lesa?” remains inside the expanded section. Closing removes the cards from
the DOM; ranking logic is unchanged.

State survives ordinary library/statistics/series/author navigation because the
disclosure remains mounted. A reload starts compact. Deliberately keeping this
UI choice outside reading storage avoids a new preference/backup schema or
writing to users’ existing saved data. Confirmed delete-all also closes it.

## Shared layouts

- All five navigation destinations remain visible. Narrow phones use three
  buttons above two, next to a compact brand/search row. From 430px the five
  destinations fit one row; from 600px the brand grows and navigation uses a
  flexible row. At 1180px the complete header becomes one aligned desktop row.
- Landscape viewports below 500px high use a non-sticky header so it does not
  consume scarce vertical space. The content/header widths stop at 100rem.
- Book grids select their column count from available space, with a 140px
  minimum card width and fluid gaps. Covers keep a 2:3 slot and use `contain`.
  Full title/author text wraps, without two-line clipping. Read/wishlist controls
  have 44px targets and appear for keyboard focus and any coarse pointer,
  including a secondary touchscreen. At tested widths, 320px has two columns,
  768px four, 1440px eight and 1920px nine.
- Timer, section spacing, metric cards and goal panels use smaller fluid padding.
  Recommendations use neutral theme surfaces, not solid accent-filled cards or
  large colored shadows. Catalog author labels and filled control labels are
  checked at at least 4.5:1 contrast in every theme; theme hues are preserved
  using slightly darker control surfaces. This is not a full WCAG certification.
- Dialogs use bounded widths, `dvh` with a `vh` fallback, internal scrolling and
  coalesced `visualViewport` resize/scroll handling. On widths below 768px,
  categories sit beside an 88px cover rather than stacking under a large image.
  Text fields use readable 16px base sizes, avoiding automatic focus zoom on
  browsers that use that threshold, without disabling browser zoom.
- Existing dialog focus trapping, Escape and focus restoration remain. A stale
  closing timer cannot hide a freshly reopened dialog. Reduced-motion users get
  immediate closes/page positioning and no CSS transitions or shimmer animation.

## Verification

The machine-readable final results are in
[Resources/responsive-test-results.json](Resources/responsive-test-results.json).

Requested widths: **320, 360, 375, 390, 430, 480, 600, 720, 768, 820, 1024,
1180, 1280, 1366, 1440, 1920 and 2560px**.

Intermediate widths: **340, 412, 540, 640, 744, 900, 1100, 1179, 1181, 1250,
1500 and 2048px**. All 29 widths are checked across all five themes, including
library/statistics layouts, visible navigation/search controls and overflow.
Series/author views also run across the width sweep and existing browsing tests.

Additional checks cover touch, keyboard disclosure, compact/expanded cards,
unchanged recommendations with/without reading history, portrait/landscape,
all dialog families, rapid reopen, focus trapping, reduced-height and simulated
visual-viewport keyboard geometry, long Icelandic titles, long literal backup
strings, complete selection/import compatibility, reduced motion, 200% root
text scaling at 320/390/820/1440px and Chromium pinch zoom.

Headless Firefox and Linux WebKit run separate smoke tests at six widths,
all themes, typed search, browsing, routes, filters, disclosures, dialogs and
portable backup selection/parsing. **Linux WebKit is not native Safari or iOS.**
No physical iPhone, iPad, Android, Samsung Internet or touchscreen laptop was
used. Software keyboard geometry is simulated, not a real OS keyboard. Text
scaling and CDP pinch zoom do not automate browser chrome’s zoom controls.

The existing regression suites, all existing real-browser suites, all catalog
validators and offline Forlagið evidence checks are run as well. Runtime
framework/dependency count is unchanged; browser engines are test tools only.

## Screenshots

These are actual Chromium captures, inspected during the audit:

- [320px library](docs/responsive/library-320.png)
- [1440px desktop library](docs/responsive/library-1440.png)
- [390px expanded recommendations](docs/responsive/recommendations-390.png)
- [390px book dialog](docs/responsive/book-dialog-390.png)
- [820px statistics](docs/responsive/statistics-820.png)
- [720px Harry Potter series](docs/responsive/series-720.png)

The initial 320px audit measured a 321px header, a 946px always-expanded
recommendation section and a catalog starting 2158px down. The final 320px header is 174px, the collapsed recommendation section is
50px, and the catalog starts 873px down. At 768px the header is 135px and the
catalog starts 693px down; at 1440px the header is 79px and the catalog starts
606px down. These are captured measurements, not promised uniform heights on
devices with different fonts/text-size settings.

Final checks pass: 104 distinct unit/tool cases (214 executions including three
regression timezones), all 68 existing browser groups, six new responsive groups
and four Firefox/WebKit groups. All three validators have zero errors. The
isolated full-catalog benchmark measured 92ms median filtering and 1.19 seconds
to ready.
