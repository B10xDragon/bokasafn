"""Expanded catalog, old backups, bounded rendering and real-assets performance.
Run: python tests/catalog_browser.py (Playwright/Chromium; same assets as live suite).
"""
from pathlib import Path
import statistics,unicodedata
exec(Path(__file__).with_name('live_browser.py').read_text().split('with sync_playwright() as p:')[0])
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 ctx=context(browser,viewport={'width':1440,'height':1000})
 ctx.add_init_script('''window.firstCatalogReady=null;function markCatalogReady(){if(window.featuresReady){firstCatalogReady=performance.now();}else requestAnimationFrame(markCatalogReady);}requestAnimationFrame(markCatalogReady);''')
 page=new_page(ctx);added=[b for b in CATALOG if b['id']>39];assert len(added)>=100
 new=added[-1];PERFORMANCE={}
 def bounded():
  assert page.evaluate('allBooks.length')==len(CATALOG)
  assert page.locator('.book-card').count()==60
  assert page.locator('#book-grid *').count()<2500
  assert str(len(CATALOG)) in page.locator('#book-grid [role=status]').text_content()
  page.get_by_role('button',name='Sýna fleiri bækur',exact=True).focus();page.keyboard.press('Enter')
  assert page.locator('.book-card').count()==120
  assert page.evaluate('Number(document.activeElement.dataset.bookId)===filteredBooks[60].id')
  page.evaluate('toggleLike(filteredBooks[90].id)');assert page.locator('.book-card').count()==120
  page.fill('#book-search',new['title']);assert page.locator(f'.book-card[data-book-id="{new["id"]}"]').count()==1
  assert page.locator('.book-card').count()<=60
  page.fill('#book-search',unicodedata.normalize('NFD',new['title']));assert page.locator(f'.book-card[data-book-id="{new["id"]}"]').count()==1
  page.fill('#book-search','');assert page.locator('.book-card').count()==60
  page.evaluate('showMoreBooks()');assert page.locator('.book-card').count()==120
  page.evaluate('openDeleteAllConfirmation()');page.wait_for_timeout(350)
  page.locator('#feature-dialog-body .destructive').click();page.wait_for_timeout(350)
  assert page.locator('.book-card').count()==60
  assert page.evaluate('allBooks.length')==len(CATALOG)
  PERFORMANCE['initialReadyMs']=round(page.evaluate('firstCatalogReady'),1)
  PERFORMANCE['initialGridElements']=page.locator('#book-grid *').count()
 check('full catalog stays searchable while initial DOM and keyboard load-more are bounded',bounded)
 def complete_covers():
  result=page.evaluate('''async ()=>{const failed=[];for(let i=0;i<allBooks.length;i+=16){await Promise.all(allBooks.slice(i,i+16).map(b=>new Promise(resolve=>{const img=new Image();img.onload=()=>{if(!img.naturalWidth)failed.push(b.id);resolve()};img.onerror=()=>{failed.push(b.id);resolve()};img.src=b.cover;})));}return failed;}''')
  assert result==[],result
 check('every local cover resolves through the real server without image substitution',complete_covers)
 def filters_and_links():
  reset(page);page.evaluate('(id)=>{toggleRead(id);toggleLike(id)}',new['id'])
  page.evaluate('toggleCategory("❤️ Óskalisti");toggleCategory("✅ Lesið")');assert page.locator('.book-card').count()==1
  assert page.locator('.book-card').get_attribute('data-book-id')==str(new['id'])
  page.evaluate('(id)=>toggleRead(id)',new['id']);assert page.locator('.book-card').count()==0
  page.evaluate('toggleCategory("Allir");resetAdvancedFilters()')
  for mode in ['pages-asc','pages-desc','title-asc','author-asc']:
   page.select_option('#book-sort',mode);assert page.locator('.book-card').count()==60
   if mode.startswith('pages'):
    values=page.evaluate('filteredBooks.map(b=>Number(b.pages)||null)');known=[n for n in values if n]
    assert known==sorted(known,reverse=mode.endswith('desc'))
    assert values[:len(known)]==known
  page.goto(URL+'?book='+str(new['id']),wait_until='networkidle');page.wait_for_function('window.featuresReady');page.wait_for_timeout(350)
  expect(page.locator('#desc-modal')).to_be_visible();assert new['title'] in page.locator('#modal-inner-content').text_content()
  page.keyboard.press('Escape');page.wait_for_timeout(350);page.go_back();page.wait_for_timeout(350);expect(page.locator('#desc-modal')).to_be_visible()
  page.keyboard.press('Escape');page.wait_for_timeout(350)
  page.evaluate('(id)=>{userData.reviews[id]={rating:5,comment:"Þ æ ö 😀",date:"nú"};saveUserData()}',new['id'])
  disliked=added[0]['id']
  page.evaluate('(id)=>{userData.reviews[id]={rating:1,comment:"Æ ö",date:"nú"};saveUserData()}',disliked)
  assert page.evaluate('(id)=>recommendations(20).every(x=>!userData.read.includes(x.book.id)&&x.book.id!==id)',disliked)
  assert page.evaluate('JSON.stringify(recommendations(20))===JSON.stringify(recommendations(20))')
  cat=new['categories'][0];assert page.evaluate('(cat)=>chooseRandom(allBooks.filter(b=>matchesAdvanced(b,{category:cat})))?.categories.includes(cat)',cat)
  page.set_viewport_size({'width':320,'height':740});page.wait_for_timeout(250);assert page.evaluate('document.documentElement.scrollWidth')==320
  page.fill('#book-search',new['title']);page.locator(f'.book-card[data-book-id="{new["id"]}"] [data-action=info]').click();page.wait_for_timeout(350);expect(page.locator('#desc-modal')).to_be_visible();page.screenshot(path=str(ARTIFACTS/'catalog-mobile-320.png'));page.keyboard.press('Escape');page.wait_for_timeout(350)
  for book in sorted(CATALOG,key=lambda b:len(b['title']),reverse=True)[:3]+sorted(CATALOG,key=lambda b:max(map(len,b['title'].split())),reverse=True)[:3]:
   page.evaluate('(id)=>openBookInfo(id)',book['id']);page.wait_for_timeout(350)
   assert page.locator('#desc-modal-content').evaluate('(d)=>d.scrollWidth<=d.clientWidth'),book['title']
   page.keyboard.press('Escape');page.wait_for_timeout(350)
 check('new IDs work with combined filters, sorting, URLs/history, recommendations, random and 320px dialogs',filters_and_links)
 def old_backup():
  other=context(browser);q=new_page(other)
  q.evaluate('showPage("stats")');q.wait_for_timeout(350);q.set_input_files('#backup-file',ROOT/'tests/fixtures/pre-expansion-reading.json');q.wait_for_timeout(350)
  q.get_by_role('button',name='Skipta út gögnum',exact=True).click();q.get_by_role('button',name='Já, skipta út',exact=True).click();q.wait_for_timeout(350)
  assert q.evaluate('JSON.stringify(userData.read)')=='[1,21,39]'
  assert q.evaluate('userData.reviews[21].comment')=='Gömul umsögn – Þ æ ö 😀'
  q.reload();q.wait_for_function('window.featuresReady');assert q.evaluate('allBooks.find(b=>b.id===21).title')==next(b['title'] for b in CATALOG if b['id']==21)
  line=(ROOT/'tests/fixtures/pre-expansion-reading.txt').read_text();q.evaluate('openTextImport()');q.wait_for_timeout(350);q.fill('#backup-line-input',line);q.get_by_role('button',name='Athuga afrit',exact=True).click();assert q.evaluate('pendingImport.data.read[2]')==39
  q.get_by_role('button',name='Flytja inn',exact=True).click();q.wait_for_timeout(350);q.get_by_role('button',name='Sameina örugglega',exact=True).click();q.wait_for_timeout(350);assert q.evaluate('JSON.stringify(userData.read)')=='[1,21,39]'
  other.close()
 check('pre-expansion JSON replacement/text merge and refresh retain all original reading identities',old_backup)
 def performance():
  page.set_viewport_size({'width':1440,'height':1000});reset(page)
  result=page.evaluate('''async ()=>{const full=allBooks,original=historyBooks().filter(b=>b.id<=39),results={};for(const [name,books] of [['original39',original],['expanded',full]]){allBooks=books;const times=[];for(let i=0;i<18;i++){searchQuery=['','ó','hildur','unknown search'][i%4];const start=performance.now();applyFilters();document.getElementById('book-grid').getBoundingClientRect();await new Promise(requestAnimationFrame);await new Promise(requestAnimationFrame);times.push(performance.now()-start);}results[name]=times;}allBooks=full;searchQuery='';applyFilters();return results;}''')
  for name,times in result.items():
   PERFORMANCE[name]={'medianFilterToLayoutMs':round(statistics.median(times),1),'maxFilterToLayoutMs':round(max(times),1)}
  assert PERFORMANCE['expanded']['medianFilterToLayoutMs']<250,PERFORMANCE
  assert PERFORMANCE['expanded']['maxFilterToLayoutMs']<1500,PERFORMANCE
  PERFORMANCE['catalogBooks']=len(CATALOG)
  PERFORMANCE['catalogBytes']=(ROOT/'Resources/books.json').stat().st_size
  PERFORMANCE['coverBytes']=sum((ROOT/b['cover']).stat().st_size for b in CATALOG)
  (ARTIFACTS/'catalog-performance.json').write_text(json.dumps(PERFORMANCE,indent=2))
  print(json.dumps(PERFORMANCE,indent=2),flush=True)
 check('expanded filter-to-layout latency remains reasonable against the original 39-book baseline',performance)
 def large_history():
  result=page.evaluate('''async ()=>{const saved=userData;userData=normalizeUserData({});userData.read=allBooks.map(b=>b.id);userData.liked=allBooks.map(b=>b.id);userData.reviews=Object.fromEntries(allBooks.map(b=>[b.id,{rating:5,comment:'Þ æ ö 😀',date:'nú'}]));const start=performance.now();showPage('stats');updateStatsUI();document.getElementById('stats-page').getBoundingClientRect();await new Promise(requestAnimationFrame);await new Promise(requestAnimationFrame);const result={renderMs:performance.now()-start,metrics:readingMetrics(),readRows:document.getElementById('read-items').children.length,wishRows:document.getElementById('wishlist-items').children.length,reviews:document.getElementById('reviews-archive').children.length,lazyArchiveImages:[...document.querySelectorAll('#read-items img,#wishlist-items img,#reviews-archive img')].every(i=>i.loading==='lazy'),textBackupReadIDs:parseBackupLine(encodeBackupLine(createReadingBackup())).data.read,jsonBackupReadIDs:parseBackup(JSON.stringify(createReadingBackup())).data.read};userData=saved;updateStatsUI();showPage('library');return result;}''')
  assert result['metrics']['books']==len(CATALOG)
  assert result['metrics']['pages']==sum(b.get('pages') or 0 for b in CATALOG)
  assert result['metrics']['averageRating']==5
  assert result['readRows']==result['wishRows']==result['reviews']==len(CATALOG)
  assert result['lazyArchiveImages']
  assert result['textBackupReadIDs']==result['jsonBackupReadIDs']==[b['id'] for b in CATALOG]
  assert result['renderMs']<3000,result
  PERFORMANCE['allBooksReadWishlistReviewedRenderMs']=round(result['renderMs'],1)
  (ARTIFACTS/'catalog-performance.json').write_text(json.dumps(PERFORMANCE,indent=2))
  print('Complete-library reading history render:',round(result['renderMs'],1),'ms',flush=True)
 check('statistics and lazy archive images stay correct with every book read, saved and reviewed',large_history)
 assert not ERRORS,ERRORS;assert not FAILURES,FAILURES
 ctx.close();browser.close();print(f'{COUNT} expanded catalog browser groups passed',flush=True)
server.shutdown()
