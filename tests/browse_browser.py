"""Real-server browsing, route, storage, keyboard, theme and performance checks."""
from pathlib import Path
exec(Path(__file__).with_name('live_browser.py').read_text().split('with sync_playwright() as p:')[0])
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 ctx=context(browser,viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
 page=new_page(ctx);page.wait_for_function('window.browseReady')
 def series_directory():
  page.click('#nav-series');assert '?browse=series' in page.url
  assert page.locator('#browse-results .browse-tile').count()==36
  page.fill('#browse-search','Eragon');assert page.locator('#browse-results .browse-tile').count()==1
  page.locator('#browse-results a').click();assert '?series=eragon' in page.url
  assert page.locator('[data-browse-book]').count()==3
  assert page.locator('[data-browse-book]').evaluate_all('(nodes)=>nodes.map(n=>Number(n.dataset.browseBook))')==[37,1030865,1004620]
  assert '0 af 3' in page.locator('#browse-related').text_content()
  page.locator('[data-browse-book="37"] [data-browse-action="read"]').click();assert '1 af 3' in page.locator('#browse-related').text_content()
  page.locator('[data-browse-book="37"] [data-browse-action="like"]').click();assert page.evaluate('userData.liked.includes(37)')
  page.reload();page.wait_for_function('window.browseReady');assert '1 af 3' in page.locator('#browse-related').text_content()
 check('series directory, ordered books, catalog-only progress, wishlist and refresh',series_directory)
 def details_routes():
  page.locator('[data-browse-book="37"] .browse-cover').click();expect(page.locator('#desc-modal')).to_be_visible()
  assert 'Bókaflokkur: Eragon — Bók 1' in page.locator('.book-browse-links').text_content()
  page.get_by_role('button',name='Næsta bók í safninu:',exact=False).click();assert 'Öldungurinn' in page.locator('#book-dialog-title').text_content()
  assert 'book=1030865' in page.url
  page.go_back();page.wait_for_timeout(350);assert 'Eragon' in page.locator('#book-dialog-title').text_content()
  page.go_forward();page.wait_for_timeout(350);assert 'Öldungurinn' in page.locator('#book-dialog-title').text_content()
  page.locator('.book-browse-links a[data-browse-kind="series"]').click();expect(page.locator('#desc-modal')).to_be_hidden();assert 'series=eragon' in page.url and 'book=' not in page.url
  page.goto(URL+'?book=1030282',wait_until='networkidle');page.wait_for_function('window.browseReady');assert 'Eragon' in page.locator('#book-dialog-title').text_content()
  page.keyboard.press('Escape')
 check('book details, next/previous available links, Back/Forward and legacy book aliases',details_routes)
 def authors():
  page.click('#nav-authors');page.fill('#browse-search','arnaldur indridason');assert page.locator('#browse-results .browse-tile').count()==1
  page.locator('#browse-results a').click();assert 'author=arnaldur-indridason' in page.url
  assert page.locator('[data-browse-book]').count()>=4
  assert 'Erlendur' in page.locator('#browse-related').text_content();assert 'Konráð' in page.locator('#browse-related').text_content()
  page.select_option('#browse-state','unread');assert all(not x for x in page.locator('[data-browse-action="read"]').evaluate_all('(n)=>n.map(x=>x.getAttribute("aria-pressed")==="true")'))
  page.select_option('#browse-sort','pages-desc')
  ids=page.locator('[data-browse-book]').evaluate_all('(n)=>n.map(x=>Number(x.dataset.browseBook))');lengths=[next(b for b in CATALOG if b['id']==i).get('pages') or 0 for i in ids];assert lengths==sorted(lengths,reverse=True)
  page.reload();page.wait_for_function('window.browseReady');assert 'Arnaldur Indriðason' in page.locator('#browse-title').text_content()
  page.go_back();page.wait_for_timeout(350);assert 'Höfundar' in page.locator('#browse-title').text_content()
  page.go_forward();page.wait_for_timeout(350);assert 'Arnaldur Indriðason' in page.locator('#browse-title').text_content()
 check('author search, multiple series, filter/sort, shareable URL and browser history',authors)
 def suggestions():
  page.fill('#book-search','ERAGON');assert page.locator('#search-suggestions [data-result-type="series"]').count()==1
  assert page.locator('#search-suggestions [data-result-type="book"]').count()==3
  page.locator('#search-suggestions [data-result-type="series"]').click();assert 'series=eragon' in page.url
  page.fill('#book-search','paolini');assert page.locator('#search-suggestions [data-result-type="author"]').count()==1
  page.locator('#search-suggestions [data-result-type="author"]').focus();page.keyboard.press('Enter');assert 'author=christopher-paolini' in page.url
  page.fill('#book-search','Hungurleikarnir');assert page.locator('.book-card').count()>=3
  page.locator('#search-suggestions [data-result-type="series"]').click();assert page.locator('[data-browse-book]').count()==3
 check('combined typed suggestions, keyboard activation, author and series main search',suggestions)
 def partial_order():
  page.goto(URL+'?series=harry-potter',wait_until='networkidle');page.wait_for_function('window.browseReady');assert '0 af 7' in page.locator('#browse-related').text_content();assert '7 bækur' in page.locator('#browse-related').text_content()
  page.goto(URL+'?series=artemis-fowl',wait_until='networkidle');page.wait_for_function('window.browseReady');assert 'Bókaröð óstaðfest' in page.locator('[data-browse-book="1004024"]').text_content()
  page.goto(URL+'?author=missing-author',wait_until='networkidle');page.wait_for_function('window.browseReady');assert 'Fannst ekki' in page.locator('#browse-title').text_content()
 check('partial series, verified totals, unknown ordinals and invalid author routes',partial_order)
 def mobile_themes():
  page.evaluate("openBrowse('series','eragon')")
  for width in [320,390,768,1440,1920]:
   page.set_viewport_size({'width':width,'height':900})
   for theme in ['light','dark','green','purple','orange']:
    page.evaluate('(t)=>setBokasafnTheme(t)',theme)
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),(width,theme)
    assert page.locator('#browse-results').evaluate('(e)=>e.scrollWidth<=e.clientWidth')
    assert page.locator('[data-browse-action="read"]').first.bounding_box()['width']>=44
  page.locator('[data-browse-action="read"]').first.focus();page.keyboard.press('Enter');assert page.locator('[data-browse-action="read"]').first.evaluate('(e)=>e===document.activeElement')
 check('all themes and mobile/desktop widths, touch targets and keyboard focus after status changes',mobile_themes)
 def backups_and_speed():
  page.evaluate('''()=>{openBrowse('series','eragon');if(userData.read.includes(37))toggleRead(37);pendingImport=parseBackup(JSON.stringify({version:14,read:['Eragon'],liked:['Eragon'],reviews:{}}));applyImport('merge');}''')
  assert '1 af 3' in page.locator('#browse-related').text_content()
  assert page.locator('[data-browse-book="37"] [data-browse-action="like"]').get_attribute('aria-pressed')=='true'
  assert page.evaluate('JSON.stringify(parseBackup(JSON.stringify(createReadingBackup())).data)===JSON.stringify(parseBackupLine(encodeBackupLine(createReadingBackup())).data)')
  assert page.evaluate('userData.version')==15
  result=page.evaluate('''()=>{const start=performance.now();for(let i=0;i<20;i++){buildBrowseIndex();browseSuggestions('ó');}openBrowse('author');return {indexAndSearchMs:performance.now()-start,tiles:document.querySelectorAll('.browse-tile').length};}''');assert result['indexAndSearchMs']<3000,result;assert result['tiles']==36
  (ARTIFACTS/'browse-performance.json').write_text(json.dumps(result,indent=2));print(result)
 check('existing portable backups and complete-catalog indexing/search/rendering performance',backups_and_speed)
 assert not ERRORS,ERRORS;assert not FAILURES,FAILURES
 browser.close()
server.shutdown();server.server_close();print(f'{COUNT} browsing browser groups passed')
