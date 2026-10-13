# Complete genre audit

Date: 2026-10-12. Branch: Beta. Baseline: `d9665a67de23a79b14c9ff8ca66c25913d77d922`.

All **663 active books** were individually reviewed against their title, author and Forlagið description. All **663 individual publisher pages** were fetched again; their descriptions match the previously preserved source evidence. One additional Forlagið companion-volume page establishes the future/Mars setting of Ljónið and Skógurinn. Store categories are corroboration, not the classification rule. No other metadata sources were used.

## Results

- Books reviewed: **663**; changed genre lists: **663**; substantive content changes beyond aliases/metadata-facet removal: **618**.
- Original genre names: **16**; final controlled taxonomy: **26**. Nine old names retired: five renamed and four non-genre shopping/audience/translation facets separated.
- Identified series reviewed: **62**; inconsistent shared-genre coverage fixed in **35** series. Sixty series previously lacked at least one reviewed core genre, including genres missing from every volume. These are different counts.
- Remaining shared-major-genre inconsistencies: **0**. Twelve additional publisher-supported related-book groups were compared without inventing catalog series identifiers.
- Explicit manual-review entries: **17**; 646 decisions have sufficient publisher evidence for their present classification.
- Active books remain **663**. No books added or removed; IDs, titles, authors, descriptions, covers, pages, series, URLs and identity mappings unchanged.

## Original taxonomy

| Name | Books |
|---|---:|
| Fantasía | 64 |
| Fræðibækur | 9 |
| Glæpir | 121 |
| Hrollvekja | 12 |
| Klassík | 76 |
| Ljóð | 4 |
| Ráðgáta | 15 |
| Rómantík | 20 |
| Skáldsögur | 395 |
| Skáldverk | 474 |
| Spenna | 185 |
| Ungmenni | 202 |
| Vísindaskáldsaga | 19 |
| Ævintýri | 8 |
| Ævisögur | 12 |
| Þýddar bækur | 235 |

## New taxonomy

Primary and secondary genres follow the catalog ordering. Literary form, audience tags, translation status and original broad query facets live separately in `classification`. Classic literature is a tradition facet; poetry, short stories and scripts are useful literary forms, not physical formats. Generic Skáldskapur is an honest fallback requiring manual review, not a claim of realistic fiction.

| Genre | Books | Definition |
|---|---:|---|
| Fantasía | 125 | Bókstaflegir galdrar, goðsagnaverur eða aðrir töfraheimar eru meginforsendur frásagnar, ekki aðeins myndlíkingar. |
| Vísindaskáldskapur | 28 | Ímyndaðar vísindalegar/tæknilegar forsendur, geimverur eða framtíðarveröld eru burðarás skáldaðrar frásagnar. |
| Dystópía | 14 | Skáldað samfélag alræðis, kúgunar eða djúpstæðrar félagslegrar hnignunar; ekki hvert einasta persónulegt áfall. |
| Spenna | 179 | Viðvarandi hætta, ógn, eltingarleikur eða spennutryllisbygging; orðið spennandi eitt getur verið markaðsmál. |
| Glæpasögur | 235 | Sakamál, glæparannsókn eða átök við gerendur eru burðarás; umfjöllun um glæpi í fræðiriti nægir ekki. |
| Leyndardómar | 168 | Lausn ráðgátu, rannsókn hvarfs eða dularfullra ummerkja ber frásögnina; ekki allar ráðgátur fela í sér glæp. |
| Hrollvekjur | 21 | Ógn, ásókn, hryllingur eða hrollvekjuforsenda er miðlægt form; ein hræðileg sena eða lýsingarorð um glæp nægir ekki. |
| Ævintýri | 92 | Ferðalag, leiðangur, björgun eða stórar hættulegar raunir bera frásögnina; ekki hvert ævintýri er yfirnáttúrulegt. |
| Sögulegar skáldsögur | 29 | Skálduð frásögn endurskapar sérstakt eldra tímabil/atburði. Sagnfræðirit eru aðskilin og aldur útgáfu nægir ekki. |
| Raunsæjar skáldsögur | 107 | Skálduð líf, þroski, fjölskylda og samfélag innan eðlilegra veruleikaforsenda. Ekki sett með fantasíu sem lýsir sama söguheimi. |
| Rómantík | 50 | Ástarsamband, leit að ást eða ástarflækja er aðalþráður; aukasamband eða kynferðisleg sena eitt nægir ekki. |
| Bókmenntaskáldskapur | 51 | Útgefandi leggur áherslu á margræða/stílmiðaða, tilraunakennda eða íhugula persónufrásögn. Ekki samheiti yfir allar skáldsögur. |
| Töfraraunsæi | 6 | Óvenjulegir eða yfirnáttúrulegir atburðir fléttast inn í annars kunnuglega veröld í bókmenntamiðaðri frásögn. |
| Húmor | 47 | Gaman, háð eða kómedíutónn er staðfest og miðlægur; ekki bætt við eingöngu vegna fyndins höfundar eða starfs hans. |
| Skáldævisögur | 7 | Skálduð eða tilraunakennd eiginlífsfrásögn; aðskilin frá staðreyndalegum sjálfsævisögum. |
| Ljóð | 5 | Ljóð, kvæði eða söguljóð eru form verksins; það að höfundur hafi áður skrifað ljóð nægir ekki. |
| Smásögur | 20 | Smásögur, örsögur eða afmarkaðar stuttar frásagnir eru form safnsins; ekki allar bækur í Skáldverkum eru skáldsögur. |
| Leikrit og handrit | 4 | Leikrit eða sjónvarps-/kvikmyndahandrit með senum og samtölum; ekki þykkt bókar eða myndskreyting. |
| Klassískar bókmenntir | 90 | Staðfest sígild bókmenntaverk/hefð. Forlagiðs bókaflokkur einn gerir ekki orðabók að klassískri skáldsögu. |
| Saga | 15 | Fræðileg frásögn af raunverulegum sögulegum atburðum, tímabilum eða þróun; sögulegar skáldsögur aðskildar. |
| Ævisögur | 6 | Frásögn af ævi raunverulegs fólks, samin af öðrum; skáldaðar sögupersónur gera ekki skáldsögu að ævisögu. |
| Sjálfsævisögur | 12 | Staðfestar eigin æviminningar, dagbækur eða sjálfsævisögur; skáldævisögur eru aðskildar. |
| Fræðibækur | 9 | Upplýsinga-, kennslu-, hand- eða orðabækur; aðeins notað þegar form/markmið er fræðilegt. |
| Samfélagsmál | 2 | Staðreyndamiðuð samfélagsumræða/fræðsla, t.d. um ofbeldi eða kerfi. Félagslegur söguþráður einn gerir skáldsögu ekki að fræðiriti. |
| Tækni | 1 | Fræðileg umfjöllun um tæki, uppfinningar eða tæknilega þróun; ekki vísindaskáldskapur. |
| Skáldskapur | 3 | Varfærinn bráðabirgðaflokkur þegar skáldað form er staðfest en gögn nægja ekki til nákvæmari greinar; krefst skráðrar handvirkrar yfirferðar. |

## Editorial method and evidence

Every standalone work has its own content-based decision. Every series has a reviewed common-genre rationale, with each volume checked against its individual description. Exceptions are retained when supported, rather than cloning the first volume. Marketing labels, author biographies and unrelated books advertised in a description are not evidence for the current work’s genre. Typical assignments have one to four tags.

`Resources/genre-audit.json` records all 663 old/new lists, reasons, status, classification fields, publisher text, product ID, date and page SHA-256; its `changes` array supplies a compact machine-readable change report. Supporting active-book IDs or publisher URLs make cross-volume reasoning traceable. Evidence uncertainty is explicit, including an unusable description for Klær gaupunnar.

### Examples

- Hungurleikarnir, Eldar kvikna and Hermiskaði now consistently have Vísindaskáldskapur, Dystópía and Spenna. Prequels retain their own catalog identity.
- Harry Potter retains Fantasía and Ævintýri across all seven volumes. Forlagið calls the sequence sígild; Klassískar bókmenntir is kept consistently. Eragon uses Fantasía and Ævintýri, not science fiction inferred from its author’s interests.
- Kepler 62 and Vítisvélar use Vísindaskáldskapur where aliens, space or future machine cities establish the premise, despite broad fantasy store placement.
- Ljónið and Skógurinn use Vísindaskáldskapur: the verified sequel Nornin explicitly establishes 2096 and a Mars expedition. A mysterious closet alone would not establish fantasy.
- Húsið í september and Kasia og Magdalena lose unsupported fantasy tags; suspense is established, while finer boundaries remain flagged.
- SKAM volumes are Leikrit og handrit, not an age group masquerading as genre.
- Glæður galdrabáls is historical fiction, not nonfiction merely because it uses historical records. Íslensk orðabók remains Fræðibækur rather than fictional classics because of an imprint label.
- Huldukonan’s title does not make its family story fantasy. Horror requires a sustained frightening premise rather than a single frightening scene.

## All series reviewed

| Series | Available books | Shared major genres | Supported individual additions |
|---|---:|---|---|
| Erlendur | 14 | Glæpasögur, Leyndardómar | 1008184: Sögulegar skáldsögur |
| Hungurleikarnir | 3 | Vísindaskáldskapur, Dystópía, Spenna | — |
| Eragon | 3 | Fantasía, Ævintýri | — |
| Hvísl hrafnanna | 3 | Fantasía, Spenna | — |
| Artemis Fowl | 7 | Fantasía, Ævintýri | — |
| Ljósaskipti | 3 | Fantasía, Rómantík | — |
| Joona Linna | 10 | Glæpasögur, Spenna | — |
| Hörður Grímsson | 11 | Glæpasögur, Spenna | — |
| Jack Reacher | 13 | Spenna, Glæpasögur | — |
| Malin Fors | 13 | Glæpasögur, Leyndardómar | — |
| Deild Q | 11 | Glæpasögur, Spenna | 1290740: Húmor |
| Þriggja heima saga | 4 | Fantasía, Ævintýri | — |
| Mjallhvít | 2 | Spenna, Glæpasögur | — |
| John-John | 2 | Raunsæjar skáldsögur | — |
| Stella Blómkvist | 12 | Glæpasögur, Spenna | — |
| Kurt Wallander | 9 | Glæpasögur, Leyndardómar | — |
| Freyju saga | 2 | Vísindaskáldskapur, Dystópía, Spenna | — |
| Rökkurhæðir | 6 | Hrollvekjur, Fantasía | — |
| Millennium | 5 | Glæpasögur, Spenna | — |
| Harry Potter | 7 | Fantasía, Ævintýri, Klassískar bókmenntir | — |
| Anna í Grænuhlíð | 5 | Raunsæjar skáldsögur, Klassískar bókmenntir | 1032610: Rómantík |
| Bert | 1 | Húmor, Raunsæjar skáldsögur | — |
| Alex Rider | 2 | Spenna, Ævintýri | — |
| Saga eftirlifenda | 3 | Fantasía, Ævintýri | — |
| Vera | 10 | Glæpasögur, Leyndardómar | — |
| Skuggasaga | 2 | Fantasía, Ævintýri | — |
| Handan Hulunnar | 4 | Fantasía, Glæpasögur, Spenna | — |
| Shetland | 8 | Glæpasögur, Leyndardómar | — |
| Nora Sand | 6 | Glæpasögur, Leyndardómar | — |
| Konráð | 7 | Glæpasögur, Leyndardómar | — |
| Úlfur og Edda | 2 | Fantasía, Ævintýri | — |
| Kepler 62 | 1 | Vísindaskáldskapur, Ævintýri | — |
| Hagfors | 6 | Glæpasögur, Leyndardómar | — |
| Bækur duftsins | 1 | Fantasía, Ævintýri | — |
| Ótrúleg ævintýri Brjálínu Hansen | 3 | Raunsæjar skáldsögur | — |
| Hafsfólkið | 3 | Fantasía, Spenna | — |
| Gunnhildur | 4 | Glæpasögur, Spenna | — |
| Bölvun múmíunnar | 2 | Fantasía, Ævintýri, Leyndardómar | — |
| Nornasaga | 2 | Fantasía, Ævintýri | — |
| SKAM | 4 | Leikrit og handrit | — |
| Dulstafir | 3 | Fantasía, Ævintýri | — |
| Kóngsríkið | 2 | Glæpasögur, Spenna | — |
| Jarmalandskrónikan | 2 | Fantasía, Ævintýri | — |
| Haparanda | 2 | Glæpasögur, Spenna | — |
| Á morgun | 1 | Spenna, Ævintýri | — |
| Morðin í Åre | 5 | Glæpasögur, Leyndardómar | — |
| Seiðmagn andstæðnanna | 3 | Rómantík | — |
| Olivia Rönning og Tom Stilton | 4 | Glæpasögur, Spenna | — |
| Kroníkuserían | 2 | Glæpasögur, Spenna | — |
| Österlen-morðin | 2 | Glæpasögur, Leyndardómar | — |
| Dóra og Rado | 2 | Glæpasögur, Spenna | 1227509: Húmor |
| Skuggabrúin | 3 | Fantasía, Vísindaskáldskapur | — |
| Emma Sköld | 7 | Glæpasögur, Leyndardómar | — |
| Evert Bäckström | 3 | Glæpasögur, Leyndardómar | 1240620: Húmor |
| Dr. Ruth Galloway | 3 | Glæpasögur, Leyndardómar | — |
| Lítilmagnar | 1 | Glæpasögur, Spenna | — |
| Hildur | 3 | Glæpasögur, Leyndardómar | — |
| Bergþóra í Hvömmum | 3 | Sögulegar skáldsögur, Glæpasögur, Leyndardómar | 1301360: Rómantík |
| Sjöleikurinn | 3 | Bókmenntaskáldskapur | — |
| Maigret | 2 | Glæpasögur, Leyndardómar | — |
| Heimilishjálpin | 3 | Spenna, Leyndardómar | — |
| Agentarnir | 1 | Spenna, Glæpasögur | — |

## Unresolved classifications

These books retain only defensible genres; the flag concerns insufficient text or finer genre/form boundaries. They are not silently guessed or deleted.

| ID | Title | Present genres | Review reason / publisher |
|---|---|---|---|
| 14 | Hrafnskló | Spenna | Forlagið staðfestir nístandi spennu en gefur engan söguþráð. Fínni flokkun bíður yfirferðar; hvorki fantasía né hrollvekja eru giskuð út frá höfundi. [Forlagið](https://www.forlagid.is/vara/hrafnsklo/) |
| 34 | Leitin að tilgangi unglingsins | Húmor | Lýsingin sýnir kómísk samtöl og unglingalíf en ekki skýra skáldaða sögu eða vísindalegt sálfræðirit. Húmor er staðfestur; formið þarfnast yfirferðar. [Forlagið](https://www.forlagid.is/vara/leitin-a%c3%b0-tilgangi-unglingsins/) |
| 1008625 | Ormstunga | Fantasía, Ævintýri | Heimar, innsigli, skuggar, manngálkn og víðfeðm ferðalög bera forsendurnar. Sprenging eða höfundarlíking við vísindaskáldskap er ekki sjálfkrafa aðalgrein allra bindanna. Vísindaskáldskaparflokkur verslunar fyrir þetta bindi fær ekki stoð í tækni-/framtíðarforsendum kynningarinnar; fínni blöndugrein bíður yfirferðar. [Forlagið](https://www.forlagid.is/vara/ormstunga/) |
| 1014834 | Múrinn | Vísindaskáldskapur, Dystópía, Spenna | Freyja lifir í lokuðu framtíðarsamfélagi undir einvaldi og valdsveitum; samfélagsstjórn, raunverulegt frelsi og lífshætta bera báðar bækur. Goðheimaheiti ein sér sanna ekki hefðbundna töfrafantasíu. Óstaðfest auka-fantasíugrein úr verslunarflokki er ekki giskuð inn; bíður efnislegrar yfirferðar. [Forlagið](https://www.forlagid.is/vara/freyju-saga-murinn/) |
| 1015158 | Djásn | Vísindaskáldskapur, Dystópía, Spenna | Freyja lifir í lokuðu framtíðarsamfélagi undir einvaldi og valdsveitum; samfélagsstjórn, raunverulegt frelsi og lífshætta bera báðar bækur. Goðheimaheiti ein sér sanna ekki hefðbundna töfrafantasíu. Óstaðfest auka-fantasíugrein úr verslunarflokki er ekki giskuð inn; bíður efnislegrar yfirferðar. [Forlagið](https://www.forlagid.is/vara/freyju-saga-2-djasn/) |
| 1017328 | Skólaus á öðrum fæti | Bókmenntaskáldskapur | Einmana stúlka býr til ímyndunarheim; lýsingin greinir ekki hvort yfirnáttúrulegir atburðir séu bókstaflegir eða myndlíkingar. Ekki giskað á fantasíugrein. [Forlagið](https://www.forlagid.is/vara/skolaus-a-o%c3%b0rum-f%c3%a6ti/) |
| 1018220 | Gegnum glervegginn | Spenna | Flótti úr glerhvolfi og kynngimögnuð atburðarás eru staðfest; lýsingin skilgreinir ekki tækni eða galdra svo nákvæmari furðusagnagrein bíður. [Forlagið](https://www.forlagid.is/vara/gegnum-glervegginn/) |
| 1022615 | Hundrað ára einsemd | Bókmenntaskáldskapur, Klassískar bókmenntir | Lýsing staðfestir sígilda ættarskáldsögu og kallar hana goðsagnakennda; hún staðfestir ekki nánari mörk töfraraunsæis og myndmáls. Engin sértæk töfraraunsæisgrein giskuð. [Forlagið](https://www.forlagid.is/vara/hundra%c3%b0-ara-einsemd-kilja-ny/) |
| 1065586 | Lífsbjörgin | Skáldskapur | Kynning staðfestir skáldskap um samfélög í heimskautaveðrum en ekki skýrari grein eða tíma. Sértækari flokkun bíður yfirferðar. [Forlagið](https://www.forlagid.is/vara/lifsbjoergin/) |
| 1128809 | Húsið í september | Spenna | Lýsingin staðfestir ógn og spennu en hvorki töfra né vísindaskáldskaparheim; nánari tegund krefst handvirkrar yfirferðar. [Forlagið](https://www.forlagid.is/vara/husid-i-september/) |
| 1237339 | Sumarið ’75 | Skáldskapur | Útgefandi gefur lesfyrirmæli um RADIO-bók en engan söguþráð. Skáldskapur staðfestur; hvorki söguleg skáldsaga né leikrit er giskað af heiti/lesaðferð. [Forlagið](https://www.forlagid.is/vara/sumarid-75/) |
| 1261322 | Kasia og Magdalena | Spenna, Rómantík | Lýsingin fjallar um yfirheyrslur, dauðsföll og ást Magdalenu á Kasiu; ekkert yfirnáttúrulegt er staðfest. Nánari flokkun þarfnast yfirferðar. [Forlagið](https://www.forlagid.is/vara/kasia-og-magdalena/) |
| 1264728 | Undirheimar | Leyndardómar, Spenna | Hvarf Esterar er staðfest en lýsingin gefur ekki eðli undirheima. Bókstitillinn er ekki sönnun um töfra eða geimferð. [Forlagið](https://www.forlagid.is/vara/undirheimar/) |
| 1279075 | Klær gaupunnar | Skáldskapur | Þekkt villuvörpun: lýsing vörusíðunnar fjallar um Vikuspá en heitið er Klær gaupunnar. Hún er ekki notuð sem efnisleg sönnun. Fínni flokkun bíður leiðréttingar útgefanda. [Forlagið](https://www.forlagid.is/vara/klaer-gaupunnar/) |
| 1285680 | Frumbyrjur | Bókmenntaskáldskapur | Lýsing gefur afskekktan bæ, jólanótt og dularfullar dyr, en ekki hvort atburðirnir séu bókstaflega yfirnáttúrulegir. Engin fantasía/hrollvekja giskuð af einni setningu. [Forlagið](https://www.forlagid.is/vara/frumbyrjur/) |
| 1292923 | Útlendingurinn | Bókmenntaskáldskapur, Klassískar bókmenntir | Bókin er staðfest sígild skáldsaga en Forlagið gefur aðeins upphafsorð sögumanns; nákvæmari efnistök eru ekki giskuð úr þekkingu á Camus. [Forlagið](https://www.forlagid.is/vara/utlendingurinn/) |
| 1295882 | Harðindi | Ævintýri | Ferð manns og merar á harðindatímum staðfest; hvorki tiltekið sögutímabil né framtíðarsamfélag kemur fram og því ekki giskað á sögulega grein eða dystópíu. [Forlagið](https://www.forlagid.is/vara/hardindi/) |

Klær gaupunnar’s publisher page describes Vikuspá; the wrong synopsis is marked unusable and the book receives only the explicit generic-fiction fallback. No plot details are fabricated. Sumarið ’75 has promotional material rather than a usable synopsis; Lífsbjörgin also lacks adequate content evidence for a narrow genre.

## Compatibility and runtime behavior

Canonical genres drive main, advanced, author and series filters, random picking, recommendations, details and favorite-genre statistics. Case-insensitive NFC normalization handles Icelandic names and historical spellings. Same-meaning aliases map to the canonical taxonomy. Old Ungmenni/Þýddar bækur/Skáldsögur/Skáldverk queries use separate audience/translation/form/legacy facets rather than becoming active genre chips.

Existing storage and backup schemas are unchanged. Historical archive metadata is preserved; its genre display is projected through canonical aliases without rewriting the archive. JSON and BOKASAFN backups preserve old names in raw storage as bytes. No fictitious genre-preference schema or destructive migration was introduced. Previously earned achievements and completed challenges remain saved; future genre diversity uses the corrected taxonomy.

## Validation and maintenance

Run `python scripts/validate_genres.py`. Definite schema, unknown/deprecated/spelling, duplicate, empty, primary/secondary and source/audit errors fail validation. Majority differences, over-tagging and content uncertainty are review warnings, not automatic classification changes. All 17 current warnings correspond to the explicit manual-review list.

Run `python scripts/build_genre_metadata.py` after changing the taxonomy. This generates only the runtime registry; it does not classify books. Review new books manually and update their audit evidence before validation. Historical store-category mapping remains isolated; the old catalog builder refuses to overwrite a catalog with a genre audit.

Optional offline evidence verification: `python scripts/verify_genre_sources.py --cache PATH`, using cached Forlagið HTML and cover-author proof bytes. It performs no network requests and compares all recorded publisher fields and page hashes.

## Tests

Actual test commands and results are recorded in `Resources/genre-test-results.json`. Coverage includes the complete catalog, Unicode aliases, multi-genre/combined filters, series consistency and legitimate differences, recommendations, random picking, statistics, preserved identity metadata, storage, both backup formats, existing URLs and rendered mobile/desktop layouts. Browser coverage uses Chromium plus headless Firefox and Linux WebKit; this is not native Safari, physical iOS/iPadOS/Android or Samsung Internet testing.

Final verification: **128 distinct unit cases**, **254 unit executions** across UTC, America/New_York and Atlantic/Reykjavik, and **84 browser groups passed**. All four catalog/series/completion/genre validators passed; genre validation has **0 errors and 17 explicit review warnings**. Chromium, Firefox 153.0 and Linux WebKit 26.5 were exercised. All 29 requested/intermediate widths and all five themes passed. Isolated full-catalog filter-to-layout latency: **99.0 ms median**, **193.7 ms maximum**; 744,109 catalog bytes. Offline evidence reparse verified **663 active pages plus one companion page**.
