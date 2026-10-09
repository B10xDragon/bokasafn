"""Real-browser complete/incomplete series, title aliases and historical backup compatibility."""
from pathlib import Path
exec(Path(__file__).with_name('live_browser.py').read_text().split('with sync_playwright() as p:')[0])
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 ctx=context(browser,viewport={'width':320,'height':844},is_mobile=True,has_touch=True)
 page=new_page(ctx);page.wait_for_function('window.browseReady')
 def complete():
  page.goto(URL+'?series=harry-potter',wait_until='networkidle');page.wait_for_function('window.browseReady')
  assert page.locator('[data-browse-book]').count()==7
  ids=page.locator('[data-browse-book]').evaluate_all('(xs)=>xs.map(x=>Number(x.dataset.browseBook))')
  assert [next(b for b in CATALOG if b['id']==i)['series']['number'] for i in ids]==list(range(1,8))
  assert '7 af 7 bókum í safninu' in page.locator('.series-availability').text_content()
  assert page.locator('.series-missing').count()==0
  for i in ids[:2]:page.locator(f'[data-browse-book="{i}"] [data-browse-action="read"]').click()
  assert '2 af 7 bókum lesnar' in page.locator('#browse-related').text_content()
  page.locator(f'[data-browse-book="{ids[0]}"] .browse-cover').click()
  assert 'Bók 1 af 7' in page.locator('.book-browse-links').text_content()
  page.get_by_role('button',name='Næsta bók í safninu:',exact=False).click()
  assert 'leyniklefinn' in page.locator('#book-dialog-title').text_content();page.keyboard.press('Escape')
  page.reload();page.wait_for_function('window.browseReady');assert '2 af 7' in page.locator('#browse-related').text_content()
 check('Harry Potter has exactly seven clean ordered works, available-only progress and next-book links',complete)
 def gaps():
  page.goto(URL+'?series=eragon',wait_until='networkidle');page.wait_for_function('window.browseReady')
  assert '3 af 4 bókum í safninu' in page.locator('.series-availability').text_content()
  assert 'Vantar bókarnúmer: 3' in page.locator('.series-missing').text_content()
  page.locator('[data-browse-book="1030865"] .browse-cover').click();page.get_by_role('button',name='Næsta bók í safninu:',exact=False).click()
  assert 'Arfleifðin' in page.locator('#book-dialog-title').text_content();page.keyboard.press('Escape')
  page.goto(URL+'?series=artemis-fowl',wait_until='networkidle');page.wait_for_function('window.browseReady')
  assert 'Bækur með óstaðfest númer geta samsvarað þessum eyðum' in page.locator('.series-missing').text_content()
  assert 'Bókaröð óstaðfest' in page.locator('[data-browse-book="1004024"]').text_content()
  page.goto(URL+'?series=malin-fors',wait_until='networkidle');page.wait_for_function('window.browseReady')
  assert 'að minnsta kosti 14' in page.locator('.series-availability').text_content()
  assert 'Heildarlengd aðalraðarinnar er óstaðfest' in page.locator('#browse-related').text_content()
 check('gaps, unresolved numbering and ongoing sequences never appear falsely complete',gaps)
 def historical_titles():
  old='Harry Potter og eldbikarinn – NÝ'
  baseline=json.loads((ROOT/'tests/fixtures/pre-series-completion-books.json').read_text());old=next(b['title'] for b in baseline if b['id']==1227681)
  page.fill('#book-search',old);assert page.locator('.book-card[data-book-id="1227681"]').count()==1
  assert page.locator('.book-card[data-book-id="1227681"]').text_content().find('NÝ')<0
  page.evaluate('(title)=>{pendingImport=parseBackup(JSON.stringify({version:14,read:[title],liked:[title],reviews:{[title]:{rating:4,comment:"Þ æ ö 😀"}}}));applyImport("merge");}',old)
  assert page.evaluate('userData.read.includes(1227681)&&userData.liked.includes(1227681)')
  page.goto(URL+'?book=1227681',wait_until='networkidle');page.wait_for_function('window.browseReady')
  assert page.locator('#book-dialog-title').text_content()=='Harry Potter og eldbikarinn'
  assert page.evaluate('userData.reviews[1227681].comment')=='Þ æ ö 😀'
  assert page.evaluate('parseBackupLine(encodeBackupLine(createReadingBackup())).data.read.includes(1227681)')
  page.keyboard.press('Escape')
 check('old-title search, v14 import, cleaned detail titles, unchanged IDs and BOKASAFN backups',historical_titles)
 def aliases_and_mobile():
  page.evaluate('''()=>{pendingImport=parseBackup(JSON.stringify({version:15,read:[1126426,1110431],reviews:{1126426:{rating:2,comment:'Old'},1110431:{rating:5,comment:'New'}}}));applyImport('merge');}''')
  assert page.evaluate('userData.read.filter(i=>i===1110431).length')==1
  assert page.evaluate('userData.reviewConflicts.some(r=>r.bookId===1110431&&r.comment==="Old")')
  page.goto(URL+'?book=1126426',wait_until='networkidle');page.wait_for_function('window.browseReady')
  assert 'viskusteinninn' in page.locator('#book-dialog-title').text_content();page.keyboard.press('Escape')
  for sid in ['harry-potter','jack-reacher','millennium']:
   page.evaluate('(id)=>openBrowse("series",id)',sid)
   for width in [320,390]:
    page.set_viewport_size({'width':width,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert page.locator('#browse-related').evaluate('(e)=>e.scrollWidth<=e.clientWidth')
 check('historical edition aliases preserve conflicts and long incomplete-series notes fit mobile screens',aliases_and_mobile)
 assert not ERRORS,ERRORS;assert not FAILURES,FAILURES
 browser.close()
server.shutdown();server.server_close();print(f'{COUNT} completion browser groups passed')
