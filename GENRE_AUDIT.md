# Simplified genre audit

Date: 2026-10-12. Branch: Beta. Baseline: `bf5227313267f41df61158a21e2cddc741877453`.

## Results

- **26 → 14** controlled discovery genres.
- **663 active books reviewed**, **550 displayed genre lists reclassified**, **113 unchanged**. All books have **1–3** valid, unique genres.
- All **62 identified series** reviewed again; **zero missing shared major genres or new series inconsistencies**. Twelve additional previously verified related-book groups remain consistent.
- **17 finer classifications remain uncertain**, inherited and explicitly preserved from the researched audit. No missing plot details were guessed.
- IDs and all title/author/description/cover/page/series/URL metadata unchanged. No book added, removed, renumbered or restored.

## Fourteen genres

| Genre | Books | Meaning |
|---|---:|---|
| Fantasía | 131 | Fantasíur og töfraraunsæi; bókstafleg yfirnáttúruleg forsenda, ekki aðeins myndlíking. |
| Vísindaskáldskapur og dystópía | 30 | Vísindaskáldskapur, framtíðarheimar eða dystópísk samfélög. |
| Spenna og glæpasögur | 314 | Spennutryllar og sakamál; ráðgátur tengdar glæparannsókn tilheyra þessum flokki. |
| Hrollvekjur og ráðgátur | 54 | Hrollvekjur eða ráðgátur sem eru ekki fyrst og fremst glæparannsóknir; bók þarf ekki að vera hvort tveggja. |
| Ævintýri | 92 | Ferðalög, leiðangrar, björgun og stórar hættulegar raunir. |
| Rómantík | 50 | Ást eða ástarsamband er aðalþráður, ekki einungis aukaatriði. |
| Skáldsögur og skáldskapur | 165 | Raunsæi, bókmenntamiðaður skáldskapur og skáldævisögur; einnig varfærinn almennur flokkur fyrir óljós skáldverk. Heitið fullyrðir ekki að hvert verk sé raunsætt. |
| Sögulegar skáldsögur | 29 | Skáldaðar frásagnir af sérstöku eldra tímabili; aðskildar frá sagnfræði. |
| Klassískar bókmenntir | 90 | Staðfest sígild bókmenntaverk eða hefð. |
| Húmor | 47 | Gaman, háð eða kómedíutónn er miðlægur og staðfestur. |
| Ljóð, smásögur og leikrit | 28 | Ljóð, smásögur, örsögur, leikrit og handrit; raunverulegt bókmenntaform er varðveitt sér. |
| Ævisögur og endurminningar | 18 | Staðreyndalegar ævisögur, sjálfsævisögur, dagbækur og endurminningar; skáldævisögur eru áfram skáldskapur. |
| Saga og samfélag | 17 | Sagnfræði og staðreyndamiðuð samfélagsumræða, ekki skáldað samfélagsþema. |
| Fræðibækur og vísindi | 10 | Fræðileg upplýsinga-, vísinda-, tækni-, kennslu-, hand- og orðabókarrit. |

## Review and mapping decisions

The complete prior audit supplies an individually reviewed Forlagið description and reason for every book. Every record was reconsidered for broad-group membership using that existing evidence; there was no new unsupported plot or age inference and no need to refetch unchanged publisher metadata. The original 26-category decisions and fresh publisher evidence are archived in `Resources/genre-audit-v1.json` and `GENRE_AUDIT_V1.md`.

Important context-sensitive choices:

- Science fiction and dystopia merge once, so the Hunger Games trilogy consistently has Vísindaskáldskapur og dystópía plus Spenna og glæpasögur.
- A crime mystery belongs with Spenna og glæpasögur. Leyndardómar only maps to Hrollvekjur og ráðgátur when it is not a crime-investigation genre; a reader is not told that every detective novel is horror. An independently verified horror strand would remain meaningful.
- The broad fiction label is **Skáldsögur og skáldskapur**, deliberately replacing the suggested narrower Raunsæjar skáldsögur. Literary experiments, unclear fictional works and autofiction are not falsely declared realistic.
- Magical realism joins broad Fantasía. Real magic remains distinct from metaphorical language; no new fantasy premise is inferred.
- Autofiction remains fiction. Historical fiction is retained only where the prior content evidence supports the historical setting; fictionalised lives do not become factual biographies.
- Poetry, short stories and drama share one discovery button, while their actual literary form remains separate metadata.
- Biography and memoir share one nonfiction group. History/society and reference/science/technology each share a broad nonfiction group. A historical novel does not become nonfiction.
- Classic literature, romance, humor, adventure and fantasy remain useful distinct facets rather than imposing one identical genre on all works by an author.

The retired-name mapping is published in `Resources/genre-taxonomy.json`. The current `Resources/genre-audit.json` includes all 663 before/after lists, the prior detailed rationale, current rationale, source description, source product ID, verified date, hash, status, classifications and supporting references. Its `changes` array includes every one of the 550 changed IDs.

Detailed previous genres are preserved internally in `classification.detailedGenres`, not exposed as active filter options. Primary/secondary genre fields use only the current fourteen names. Audience, translation and physical format do not become genres.

## Every identified series

| Series | Books present | Shared main categories |
|---|---:|---|
| Erlendur | 14 | Spenna og glæpasögur |
| Hungurleikarnir | 3 | Vísindaskáldskapur og dystópía, Spenna og glæpasögur |
| Eragon | 3 | Fantasía, Ævintýri |
| Hvísl hrafnanna | 3 | Fantasía, Spenna og glæpasögur |
| Artemis Fowl | 7 | Fantasía, Ævintýri |
| Ljósaskipti | 3 | Fantasía, Rómantík |
| Joona Linna | 10 | Spenna og glæpasögur |
| Hörður Grímsson | 11 | Spenna og glæpasögur |
| Jack Reacher | 13 | Spenna og glæpasögur |
| Malin Fors | 13 | Spenna og glæpasögur |
| Deild Q | 11 | Spenna og glæpasögur |
| Þriggja heima saga | 4 | Fantasía, Ævintýri |
| Mjallhvít | 2 | Spenna og glæpasögur |
| John-John | 2 | Skáldsögur og skáldskapur |
| Stella Blómkvist | 12 | Spenna og glæpasögur |
| Kurt Wallander | 9 | Spenna og glæpasögur |
| Freyju saga | 2 | Vísindaskáldskapur og dystópía, Spenna og glæpasögur |
| Rökkurhæðir | 6 | Hrollvekjur og ráðgátur, Fantasía |
| Millennium | 5 | Spenna og glæpasögur |
| Harry Potter | 7 | Fantasía, Ævintýri, Klassískar bókmenntir |
| Anna í Grænuhlíð | 5 | Skáldsögur og skáldskapur, Klassískar bókmenntir |
| Bert | 1 | Húmor, Skáldsögur og skáldskapur |
| Alex Rider | 2 | Spenna og glæpasögur, Ævintýri |
| Saga eftirlifenda | 3 | Fantasía, Ævintýri |
| Vera | 10 | Spenna og glæpasögur |
| Skuggasaga | 2 | Fantasía, Ævintýri |
| Handan Hulunnar | 4 | Fantasía, Spenna og glæpasögur |
| Shetland | 8 | Spenna og glæpasögur |
| Nora Sand | 6 | Spenna og glæpasögur |
| Konráð | 7 | Spenna og glæpasögur |
| Úlfur og Edda | 2 | Fantasía, Ævintýri |
| Kepler 62 | 1 | Vísindaskáldskapur og dystópía, Ævintýri |
| Hagfors | 6 | Spenna og glæpasögur |
| Bækur duftsins | 1 | Fantasía, Ævintýri |
| Ótrúleg ævintýri Brjálínu Hansen | 3 | Skáldsögur og skáldskapur |
| Hafsfólkið | 3 | Fantasía, Spenna og glæpasögur |
| Gunnhildur | 4 | Spenna og glæpasögur |
| Bölvun múmíunnar | 2 | Fantasía, Ævintýri, Hrollvekjur og ráðgátur |
| Nornasaga | 2 | Fantasía, Ævintýri |
| SKAM | 4 | Ljóð, smásögur og leikrit |
| Dulstafir | 3 | Fantasía, Ævintýri |
| Kóngsríkið | 2 | Spenna og glæpasögur |
| Jarmalandskrónikan | 2 | Fantasía, Ævintýri |
| Haparanda | 2 | Spenna og glæpasögur |
| Á morgun | 1 | Spenna og glæpasögur, Ævintýri |
| Morðin í Åre | 5 | Spenna og glæpasögur |
| Seiðmagn andstæðnanna | 3 | Rómantík |
| Olivia Rönning og Tom Stilton | 4 | Spenna og glæpasögur |
| Kroníkuserían | 2 | Spenna og glæpasögur |
| Österlen-morðin | 2 | Spenna og glæpasögur |
| Dóra og Rado | 2 | Spenna og glæpasögur |
| Skuggabrúin | 3 | Fantasía, Vísindaskáldskapur og dystópía |
| Emma Sköld | 7 | Spenna og glæpasögur |
| Evert Bäckström | 3 | Spenna og glæpasögur |
| Dr. Ruth Galloway | 3 | Spenna og glæpasögur |
| Lítilmagnar | 1 | Spenna og glæpasögur |
| Hildur | 3 | Spenna og glæpasögur |
| Bergþóra í Hvömmum | 3 | Sögulegar skáldsögur, Spenna og glæpasögur |
| Sjöleikurinn | 3 | Skáldsögur og skáldskapur |
| Maigret | 2 | Spenna og glæpasögur |
| Heimilishjálpin | 3 | Spenna og glæpasögur, Hrollvekjur og ráðgátur |
| Agentarnir | 1 | Spenna og glæpasögur |

Individual-volume differences supported by their original Forlagið descriptions remain, including Einvígið’s historical setting, Anna frá eyjunni’s romance and the humorous Deild Q/Backström/Dóra titles. These differences are not treated as errors or copied to every volume. Main-series and companion identities are unchanged.

## Manual-review list

| ID | Title | Present genres | Original unresolved evidence |
|---|---|---|
| 14 | Hrafnskló | Spenna og glæpasögur | Forlagið staðfestir nístandi spennu en gefur engan söguþráð. Fínni flokkun bíður yfirferðar; hvorki fantasía né hrollvekja eru giskuð út frá höfundi. [Forlagið](https://www.forlagid.is/vara/hrafnsklo/) |
| 34 | Leitin að tilgangi unglingsins | Húmor | Lýsingin sýnir kómísk samtöl og unglingalíf en ekki skýra skáldaða sögu eða vísindalegt sálfræðirit. Húmor er staðfestur; formið þarfnast yfirferðar. [Forlagið](https://www.forlagid.is/vara/leitin-a%c3%b0-tilgangi-unglingsins/) |
| 1008625 | Ormstunga | Fantasía, Ævintýri | Heimar, innsigli, skuggar, manngálkn og víðfeðm ferðalög bera forsendurnar. Sprenging eða höfundarlíking við vísindaskáldskap er ekki sjálfkrafa aðalgrein allra bindanna. Vísindaskáldskaparflokkur verslunar fyrir þetta bindi fær ekki stoð í tækni-/framtíðarforsendum kynningarinnar; fínni blöndugrein bíður yfirferðar. [Forlagið](https://www.forlagid.is/vara/ormstunga/) |
| 1014834 | Múrinn | Vísindaskáldskapur og dystópía, Spenna og glæpasögur | Freyja lifir í lokuðu framtíðarsamfélagi undir einvaldi og valdsveitum; samfélagsstjórn, raunverulegt frelsi og lífshætta bera báðar bækur. Goðheimaheiti ein sér sanna ekki hefðbundna töfrafantasíu. Óstaðfest auka-fantasíugrein úr verslunarflokki er ekki giskuð inn; bíður efnislegrar yfirferðar. [Forlagið](https://www.forlagid.is/vara/freyju-saga-murinn/) |
| 1015158 | Djásn | Vísindaskáldskapur og dystópía, Spenna og glæpasögur | Freyja lifir í lokuðu framtíðarsamfélagi undir einvaldi og valdsveitum; samfélagsstjórn, raunverulegt frelsi og lífshætta bera báðar bækur. Goðheimaheiti ein sér sanna ekki hefðbundna töfrafantasíu. Óstaðfest auka-fantasíugrein úr verslunarflokki er ekki giskuð inn; bíður efnislegrar yfirferðar. [Forlagið](https://www.forlagid.is/vara/freyju-saga-2-djasn/) |
| 1017328 | Skólaus á öðrum fæti | Skáldsögur og skáldskapur | Einmana stúlka býr til ímyndunarheim; lýsingin greinir ekki hvort yfirnáttúrulegir atburðir séu bókstaflegir eða myndlíkingar. Ekki giskað á fantasíugrein. [Forlagið](https://www.forlagid.is/vara/skolaus-a-o%c3%b0rum-f%c3%a6ti/) |
| 1018220 | Gegnum glervegginn | Spenna og glæpasögur | Flótti úr glerhvolfi og kynngimögnuð atburðarás eru staðfest; lýsingin skilgreinir ekki tækni eða galdra svo nákvæmari furðusagnagrein bíður. [Forlagið](https://www.forlagid.is/vara/gegnum-glervegginn/) |
| 1022615 | Hundrað ára einsemd | Skáldsögur og skáldskapur, Klassískar bókmenntir | Lýsing staðfestir sígilda ættarskáldsögu og kallar hana goðsagnakennda; hún staðfestir ekki nánari mörk töfraraunsæis og myndmáls. Engin sértæk töfraraunsæisgrein giskuð. [Forlagið](https://www.forlagid.is/vara/hundra%c3%b0-ara-einsemd-kilja-ny/) |
| 1065586 | Lífsbjörgin | Skáldsögur og skáldskapur | Kynning staðfestir skáldskap um samfélög í heimskautaveðrum en ekki skýrari grein eða tíma. Sértækari flokkun bíður yfirferðar. [Forlagið](https://www.forlagid.is/vara/lifsbjoergin/) |
| 1128809 | Húsið í september | Spenna og glæpasögur | Lýsingin staðfestir ógn og spennu en hvorki töfra né vísindaskáldskaparheim; nánari tegund krefst handvirkrar yfirferðar. [Forlagið](https://www.forlagid.is/vara/husid-i-september/) |
| 1237339 | Sumarið ’75 | Skáldsögur og skáldskapur | Útgefandi gefur lesfyrirmæli um RADIO-bók en engan söguþráð. Skáldskapur staðfestur; hvorki söguleg skáldsaga né leikrit er giskað af heiti/lesaðferð. [Forlagið](https://www.forlagid.is/vara/sumarid-75/) |
| 1261322 | Kasia og Magdalena | Spenna og glæpasögur, Rómantík | Lýsingin fjallar um yfirheyrslur, dauðsföll og ást Magdalenu á Kasiu; ekkert yfirnáttúrulegt er staðfest. Nánari flokkun þarfnast yfirferðar. [Forlagið](https://www.forlagid.is/vara/kasia-og-magdalena/) |
| 1264728 | Undirheimar | Hrollvekjur og ráðgátur, Spenna og glæpasögur | Hvarf Esterar er staðfest en lýsingin gefur ekki eðli undirheima. Bókstitillinn er ekki sönnun um töfra eða geimferð. [Forlagið](https://www.forlagid.is/vara/undirheimar/) |
| 1279075 | Klær gaupunnar | Skáldsögur og skáldskapur | Þekkt villuvörpun: lýsing vörusíðunnar fjallar um Vikuspá en heitið er Klær gaupunnar. Hún er ekki notuð sem efnisleg sönnun. Fínni flokkun bíður leiðréttingar útgefanda. [Forlagið](https://www.forlagid.is/vara/klaer-gaupunnar/) |
| 1285680 | Frumbyrjur | Skáldsögur og skáldskapur | Lýsing gefur afskekktan bæ, jólanótt og dularfullar dyr, en ekki hvort atburðirnir séu bókstaflega yfirnáttúrulegir. Engin fantasía/hrollvekja giskuð af einni setningu. [Forlagið](https://www.forlagid.is/vara/frumbyrjur/) |
| 1292923 | Útlendingurinn | Skáldsögur og skáldskapur, Klassískar bókmenntir | Bókin er staðfest sígild skáldsaga en Forlagið gefur aðeins upphafsorð sögumanns; nákvæmari efnistök eru ekki giskuð úr þekkingu á Camus. [Forlagið](https://www.forlagid.is/vara/utlendingurinn/) |
| 1295882 | Harðindi | Ævintýri | Ferð manns og merar á harðindatímum staðfest; hvorki tiltekið sögutímabil né framtíðarsamfélag kemur fram og því ekki giskað á sögulega grein eða dystópíu. [Forlagið](https://www.forlagid.is/vara/hardindi/) |

Klær gaupunnar still has an unusable publisher description of another book. Its generic fiction fallback is now honestly included in the broad fiction group; its review flag is preserved. Broad discovery groups do not resolve absent evidence.

## Runtime and compatibility

Main and advanced filters, book details, series/author filters, recommendations, random selection and favorite-genre statistics use the fourteen current names. Long filter labels wrap inside bounded touch targets instead of forcing mobile overflow.

All 26 previous genre queries and older aliases remain interpretable. Historical Leyndardómar/Ráðgáta queries retain crime and non-crime mysteries through the preserved detailed evidence; they do not force crime books into the horror group. Archived records project their genres to the new display vocabulary without rewriting saved data. Age/translation/form queries retain the previous compatibility handling.

Reading data and backup schemas are unchanged. Both JSON and BOKASAFN imports retain historical genre text in raw storage; arbitrary saved namespace values are not destructively rewritten. Previously earned achievements and completed challenges remain saved, while current genre-diversity statistics reflect the simplified categories.

## Validation and tests

Run `python scripts/validate_genres.py`: definite schema/name/duplicate/empty/provenance problems fail. The taxonomy must contain 12–14 names. More than three tags or suspicious series differences are review warnings; legitimately different secondary genres are allowed. The 17 current warnings correspond to the manual-review list, not unreviewed series gaps.

Run `python scripts/build_genre_metadata.py` after taxonomy changes. It generates only the lightweight browser registry, never a content classifier. The legacy publisher-store builder remains blocked from replacing audited genres.

Verification commands and final measurements are recorded in `Resources/simplification-test-results.json`. Unit/browser coverage includes all old genre queries, combined filters, recommendations, random picking, series ordering, favorite genres, unchanged metadata, both backup formats, archived history and mobile/desktop layouts. Email form tests and activation limits are documented separately in `BOOK_SUGGESTIONS_SETUP.md`.

Final verification: **143 distinct unit cases**, **273 executions** including three time zones, and **91 browser groups passed**. All four validators passed; genre validation: **0 errors, 17 documented review warnings, no series gaps**. Chromium 151.0, Firefox 153.0 and Linux WebKit 26.5 were tested, with 29 widths (320–2560px) and all five themes. Full-catalog filter-to-layout latency: **119.7 ms median**, **154.5 ms maximum**. Email form tests use intercepted provider responses; live email delivery remains pending activation.
