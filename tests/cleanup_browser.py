"""Real browser checks for the reviewed catalog and historical identities."""
from pathlib import Path
exec(Path(__file__).with_name('live_browser.py').read_text().split('with sync_playwright() as p:')[0])
IDENTITIES=json.loads((ROOT/'Resources/catalog-identities.json').read_text())
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
 ctx=context(browser,viewport={'width':390,'height':844},is_mobile=True,has_touch=True)
 duplicate=int(next(iter(IDENTITIES['aliases'])));canonical=IDENTITIES['aliases'][str(duplicate)]
 archived=next(b for b in IDENTITIES['archived'] if b['id']==10)
 old={'version':15,'read':[canonical,duplicate,archived['id']],'liked':[duplicate,archived['id']],
      'reviews':{str(canonical):{'rating':5,'comment':'Upprunaleg Þ æ ö 😀','date':'í dag'},str(duplicate):{'rating':2,'comment':'Önnur umsögn','date':'í gær'},str(archived['id']):{'rating':4,'comment':'Barnabók úr sögu','date':'áður'}},
      'completedDates':{str(canonical):'2026-01-01',str(duplicate):'2026-01-02'},'totalSeconds':600,'dailyProgress':{'2026-01-01':600},
      'challenges':[{'id':'old','kind':'books','title':'Markmið','target':3,'start':'2026-01-01','baseline':[canonical,duplicate]}]}
 ctx.add_init_script('if(!sessionStorage.seeded){localStorage.setItem("library_v15",'+json.dumps(json.dumps(old,ensure_ascii=False))+');sessionStorage.seeded="yes";}')
 page=new_page(ctx)
 def migration():
  state=page.evaluate('userData');assert state['read']==[canonical,archived['id']];assert state['liked']==[canonical,archived['id']]
  assert state['totalSeconds']==600;assert state['reviewConflicts'][0]['comment']=='Önnur umsögn';assert state['challenges'][0]['baseline']==[canonical]
  assert json.loads(page.evaluate('localStorage.getItem("library_catalog_backup_20261008")'))==old
  metrics=page.evaluate('readingMetrics()');assert metrics['books']==2
  expected=next(b for b in CATALOG if b['id']==canonical).get('pages') or 0
  assert metrics['pages']==expected+archived['pages']
  page.evaluate('showPage("stats");updateStatsUI()');assert archived['title'] in page.locator('#read-items').text_content()
  assert 'Önnur umsögn' in page.locator('#reviews-archive').text_content()
  page.reload();page.wait_for_function('window.featuresReady');assert page.evaluate('userData.reviewConflicts.length')==1
 check('alias migration preserves exact rollback, both reviews, dates, challenges and archived statistics',migration)
 def portable():
  result=page.evaluate('''()=>{const json=JSON.stringify(createReadingBackup());const line=encodeBackupLine(createReadingBackup());return {json:parseBackup(json).data,line:parseBackupLine(line).data};}''')
  assert result['json']==result['line'];assert result['json']['reviewConflicts'][0]['comment']=='Önnur umsögn'
  page.evaluate('''()=>{const incoming=normalizeUserData(userData);userData=mergeReadingData(userData,incoming);userData=mergeReadingData(userData,incoming);saveUserData();}''')
  assert page.evaluate('readingMetrics().books')==2;assert page.evaluate('userData.reviewConflicts.length')==1
 check('JSON and one-line backups round-trip archived data and repeated imports do not duplicate statistics',portable)
 def discovery_and_routes():
  page.evaluate('showPage("library");activeCategories=[];applyFilters()')
  assert page.evaluate('(id)=>!allBooks.some(b=>b.id===id)',archived['id'])
  assert page.evaluate('(id)=>recommendations(1000).every(r=>r.book.id!==id)',archived['id'])
  assert page.evaluate('(id)=>Array.from({length:100},()=>chooseRandom(allBooks).id).every(x=>x!==id)',archived['id'])
  page.goto(URL+'?book='+str(duplicate),wait_until='networkidle');page.wait_for_function('window.featuresReady');page.wait_for_timeout(350)
  expect(page.locator('#desc-modal')).to_be_visible();assert 'Eragon' in page.locator('#book-dialog-title').text_content()
  page.goto(URL+'?book='+str(archived['id']),wait_until='networkidle');page.wait_for_function('window.featuresReady');page.wait_for_timeout(350)
  expect(page.locator('#desc-modal')).to_be_visible();assert archived['title'] in page.locator('#book-dialog-title').text_content()
  assert 'Varðveitt bók' in page.locator('#modal-inner-content').text_content()
  assert page.locator('#desc-modal-content').evaluate('(e)=>e.scrollWidth<=e.clientWidth')
  page.goto(URL+'?book=999999999',wait_until='networkidle');page.wait_for_function('window.featuresReady');assert page.locator('#desc-modal').get_attribute('aria-hidden')=='true'
 check('retired books stay out of discovery, random and recommendations; aliases/archive routes and mobile dialogs work',discovery_and_routes)
 assert not ERRORS,ERRORS;assert not FAILURES,FAILURES
 browser.close()
server.shutdown();server.server_close();print(f'{COUNT} cleanup browser groups passed')
