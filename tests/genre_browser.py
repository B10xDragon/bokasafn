"""Actual rendered genre integration, compatibility and mobile/desktop checks."""
from pathlib import Path
exec(Path(__file__).with_name('live_browser.py').read_text().split('with sync_playwright() as p:')[0])
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium');ctx=context(browser,viewport={'width':1440,'height':1000});page=new_page(ctx)
 def filtering():
  reset(page);page.evaluate('activeCategories=["Vísindaskáldsaga","Dystópía"];applyFilters()')
  ids=page.evaluate('filteredBooks.map(b=>b.id)');assert {35,36,38}<=set(ids)
  assert page.evaluate('filteredBooks.every(b=>b.categories.includes("Vísindaskáldskapur")&&b.categories.includes("Dystópía"))')
  assert page.evaluate('activeCategories[0]')=='Vísindaskáldskapur'
  page.evaluate('activeCategories=["Fantasía","Ævintýri"];applyFilters()');assert page.evaluate('filteredBooks.some(b=>b.series?.id==="eragon")')
 check('canonical and legacy multi-genre filters with complete series',filtering)
 def search():
  reset(page);page.fill('#book-search','HUNGURLEIKARNIR');assert page.locator('[data-result-type="series"]').count()==1
  page.locator('[data-result-type="series"]').click();assert 'series=hungurleikarnir' in page.url
  assert page.evaluate('allBooks.filter(b=>b.series?.id==="hungurleikarnir").every(b=>matchesGenre(b,"Dystópía"))')
  page.reload();page.wait_for_function('window.browseReady');assert 'Hungurleikarnir' in page.locator('#browse-title').text_content()
 check('series search and shareable URL after genre correction',search)
 def recommendations():
  reset(page);page.evaluate('userData=normalizeUserData({version:15,read:[35],reviews:{35:{rating:5,comment:"Frábær dystópía"}}});updateStatsUI();document.getElementById("recommendations-panel").open=true')
  page.wait_for_timeout(200);assert page.evaluate('recommendations().length')==6;assert page.evaluate('recommendations().some(r=>[36,38].includes(r.book?.id||r.id))')
  assert page.evaluate('allBooks.filter(b=>[36,38].includes(b.id)).every(b=>b.categories.includes("Dystópía"))')
 check('personalized recommendations retain meaningful corrected genres',recommendations)
 def stats():
  page.evaluate('userData=normalizeUserData({version:15,read:[35,36,38],totalSeconds:420});updateStatsUI();showPage("stats")')
  assert page.evaluate('userData.totalSeconds')==420
  assert page.evaluate('readingMetrics().genres')==3
  assert page.evaluate('historyBooks().filter(b=>userData.read.includes(b.id)).every(b=>!bookGenres(b).includes("Þýddar bækur"))')
 check('favorite genres exclude translation and audience metadata without changing reading time',stats)
 def layouts():
  for width in [320,390,820,1440]:
   page.set_viewport_size({'width':width,'height':900});page.evaluate('showPage("library");openBookInfo(38)');page.wait_for_timeout(80)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   assert page.evaluate('activeDialog.content.scrollWidth<=activeDialog.content.clientWidth+1')
   assert 'vísindaskáldskapur' in page.locator('#desc-modal').inner_text().lower();page.keyboard.press('Escape')
  page.screenshot(path=str(ARTIFACTS/'genre-library-1440.png'))
 check('corrected genre badges fit mobile tablet and desktop dialogs',layouts)
 def backups():
  page.evaluate('userData=normalizeUserData({version:15,read:[35],liked:[38],reviews:{35:{rating:5,comment:"Þæö"}},totalSeconds:420,achievements:{"five-genres":"2026-01-01"}});localStorage.setItem("bokasafn_genre_filters",JSON.stringify(["Vísindaskáldsaga","Skáldsögur"]));globalThis.gb=createReadingBackup();globalThis.gj=parseBackup(JSON.stringify(gb));globalThis.gt=parseBackupLine(encodeBackupLine(gb))')
  assert page.evaluate('JSON.stringify(gj.data)===JSON.stringify(gt.data)')
  assert page.evaluate('gt.data.totalSeconds')==420
  assert page.evaluate('JSON.parse(gt.raw.storage.local.bokasafn_genre_filters)[0]')=='Vísindaskáldsaga'
  assert page.evaluate('gt.data.achievements["five-genres"]')=='2026-01-01'
 check('old genre preference bytes and user data survive JSON and BOKASAFN backups',backups)
 assert not ERRORS,ERRORS
 (ARTIFACTS/'genre-results.json').write_text(json.dumps({'groupsPassed':COUNT,'widths':[320,390,820,1440],'uncaughtErrors':ERRORS},indent=2));browser.close();server.shutdown();print(str(COUNT)+' genre browser groups passed')
