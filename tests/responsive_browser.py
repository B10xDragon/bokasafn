"""Actual rendering at requested/intermediate widths; no Safari/iOS claims."""
from pathlib import Path
import re
exec(Path(__file__).with_name('live_browser.py').read_text().split('with sync_playwright() as p:')[0])
OUT=ARTIFACTS/'responsive';OUT.mkdir(exist_ok=True)
WIDTHS=[320,360,375,390,430,480,600,720,768,820,1024,1180,1280,1366,1440,1920,2560]
INTERMEDIATE=[340,412,540,640,744,900,1100,1179,1181,1250,1500,2048]
THEMES=['light','dark','green','purple','orange'];MEASUREMENTS=[]
def no_overflow(q):
 r=q.evaluate('''()=>({viewport:innerWidth,document:document.documentElement.scrollWidth,bad:[...document.querySelectorAll('main button,main input,main select,main textarea,.browse-book,.book-card,nav button')].filter(n=>n.getClientRects().length && !n.closest('.hidden') && !n.closest('.heat-scroll')).filter(n=>{const r=n.getBoundingClientRect();return r.left < -1 || r.right>innerWidth+1}).map(n=>n.id||n.className).slice(0,8)})''')
 assert r['document']<=r['viewport']+1 and not r['bad'],r

def metadata_contrast(q):
 colors=q.locator('.book-card').first.evaluate("n=>({fg:getComputedStyle(n.querySelector('p')).color,bg:getComputedStyle(n).backgroundColor,body:getComputedStyle(document.body).backgroundColor})")
 def luminance(color):
  rgb=[int(x)/255 for x in re.findall(r'\d+',color)[:3]]
  rgb=[x/12.92 if x<=.04045 else ((x+.055)/1.055)**2.4 for x in rgb]
  return sum(x*w for x,w in zip(rgb,[.2126,.7152,.0722]))
 bg=colors['body'] if colors['bg']=='rgba(0, 0, 0, 0)' else colors['bg'];a,b=sorted([luminance(colors['fg']),luminance(bg)])
 assert (b+.05)/(a+.05)>=4.5,colors
 control=q.locator('.feature-button:not(.secondary):not(.destructive)').first.evaluate('n=>({fg:getComputedStyle(n).color,bg:getComputedStyle(n).backgroundColor})')
 a,b=sorted([luminance(control['fg']),luminance(control['bg'])]);assert (b+.05)/(a+.05)>=4.5,control

def dialog_bounds(q):
 q.wait_for_function('activeDialog && activeDialog.modal.getAttribute("aria-hidden")==="false"')
 r=q.evaluate('''()=>{const r=activeDialog.content.getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom,height:r.height,vh:visualViewport.height,top:visualViewport.offsetTop,overflow:activeDialog.content.scrollWidth-activeDialog.content.clientWidth}}''')
 assert r['x']>=0 and r['right']<=q.viewport_size['width']+1 and r['y']>=r['top']-1 and r['bottom']<=r['top']+r['vh']+1 and r['overflow']<=1,r

with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 ctx=context(browser,viewport={'width':390,'height':844},is_mobile=True,has_touch=True,reduced_motion='reduce');page=new_page(ctx);page.wait_for_function('window.browseReady')
 def disclosure():
  assert not page.evaluate('document.getElementById("recommendations-panel").open')
  assert page.locator('#personal-recommendations button').count()==0
  a=page.locator('#recommendations-panel').bounding_box();b=page.locator('#advanced-filters').bounding_box();assert a['height']<=80 and abs(a['height']-b['height'])<12,(a,b)
  data=page.evaluate('JSON.stringify(userData)');expected=page.evaluate('recommendations().map(x=>x.book.id)')
  summary=page.locator('#recommendations-panel summary');summary.focus();page.keyboard.press('Enter');expect(summary).to_have_attribute('aria-expanded','true')
  assert page.locator('#personal-recommendations button').count()==len(expected)
  assert page.evaluate('JSON.stringify(userData)')==data
  assert page.locator('#personal-recommendations img').count()==6
  assert page.locator('#personal-recommendations button').first.evaluate('(n)=>getComputedStyle(n).backgroundColor')!=page.evaluate('getComputedStyle(document.documentElement).getPropertyValue("--theme-accent").trim()')
  page.click('#nav-stats');page.click('#nav-library');assert page.evaluate('document.getElementById("recommendations-panel").open')
  summary.focus();page.keyboard.press('Space');expect(summary).to_have_attribute('aria-expanded','false');assert page.locator('#personal-recommendations button').count()==0
  # A reload starts compact; preference remains in the page, outside saved reading data.
  page.reload();page.wait_for_function('window.browseReady');assert not page.evaluate('document.getElementById("recommendations-panel").open')
 check('recommendations start compact, render only when expanded, support Enter/Space and retain navigation state without changing data',disclosure)
 def matrix():
  for width in sorted(set(WIDTHS+INTERMEDIATE)):
   page.set_viewport_size({'width':width,'height':900})
   for theme in THEMES:
    page.evaluate('(t)=>{setBokasafnTheme(t);showPage("library")}',theme);no_overflow(page);metadata_contrast(page)
    for selector in ['#book-search','#nav-library','#nav-series','#nav-authors','#nav-stats','#nav-appearance']:inside_viewport(page,selector)
    header=page.locator('nav').bounding_box()['height'];assert header<190 if width<600 else header<155,(width,header)
    cards=page.locator('.book-card');assert cards.count()==60
    assert cards.first.locator('h3').evaluate('(n)=>n.scrollHeight<=n.clientHeight+1')
    page.evaluate('showPage("stats")');no_overflow(page)
    if theme=='light':
     page.evaluate('openBrowse("series")');no_overflow(page);page.evaluate('openBrowse("author")');no_overflow(page)
    MEASUREMENTS.append({'width':width,'theme':theme,'headerHeight':round(header,1)})
  page.set_viewport_size({'width':390,'height':844});page.evaluate('setBokasafnTheme("light");showPage("library")')
 check('all 17 requested widths plus 12 intermediate widths, five themes and library/statistics/series/author layouts fit without offscreen controls',matrix)
 def expanded_touch():
  for w in [320,390,600,820,1180,1440,2560]:
   page.set_viewport_size({'width':w,'height':900});page.locator('#recommendations-panel summary').tap();expect(page.locator('#recommendations-panel summary')).to_have_attribute('aria-expanded','true');no_overflow(page)
   page.locator('#personal-recommendations button').first.tap();dialog_bounds(page)
   if w<768:assert page.locator('.book-detail-cover').bounding_box()['height']<190
   page.keyboard.press('Escape')
   page.get_by_role('button',name='Hvað á ég að lesa?',exact=True).click();dialog_bounds(page);page.keyboard.press('Escape')
   page.locator('#recommendations-panel summary').tap()
  page.evaluate('userData=normalizeUserData({version:15,read:[allBooks[0].id],liked:[allBooks[1].id],reviews:{[allBooks[2].id]:{rating:1,comment:"Nei"}}});updateStatsUI()')
  page.locator('#recommendations-panel summary').tap();expect(page.locator('#personal-recommendations button')).to_have_count(6)
  assert page.evaluate('recommendations().every(x=>!userData.read.includes(x.book.id)&&x.book.id!==allBooks[2].id)')
  page.locator('#recommendations-panel summary').tap()
 check('compact cover/reason cards, touch activation and random picker work on phones through desktops with and without reading history',expanded_touch)
 def dialogs():
  for w,h in [(320,568),(844,390),(600,480),(1024,768),(1440,900)]:
   page.set_viewport_size({'width':w,'height':h})
   for action in ['openBookInfo(allBooks[0].id)','openRecommendModal()','openRandomPicker()','openTextBackup()','openTextImport()','openDeleteAllConfirmation()']:
    page.evaluate(action);dialog_bounds(page);page.keyboard.press('Tab');assert page.evaluate('activeDialog.content.contains(document.activeElement)');page.keyboard.press('Escape');expect(page.locator('[role="dialog"]:visible')).to_have_count(0)
   page.evaluate('handleTimerPrimaryAction();showStopConfirmation()');dialog_bounds(page);page.keyboard.press('Escape');page.evaluate('clearInterval(timerState.interval);timerState=emptyTimerState();updateTimerUI()')
   page.click('#nav-appearance');inside_viewport(page,'#appearance-panel');assert page.locator('#appearance-panel').bounding_box()['height']<=h;page.keyboard.press('Escape')
  page.set_viewport_size({'width':390,'height':844})
  page.evaluate('openRandomPicker();closeModal("feature-modal","feature-modal-content");openTextBackup()');page.wait_for_timeout(350);expect(page.get_by_role('button',name='Velja alla línuna',exact=True)).to_be_visible();page.keyboard.press('Escape')
  page.evaluate('openBookInfo(allBooks[0].id)');page.fill('#review-text','Þetta er löng íslensk umsögn. '*100)
  # An actual layout-viewport resize, plus controlled visual-viewport keyboard geometry.
  page.set_viewport_size({'width':390,'height':340});page.wait_for_timeout(80);dialog_bounds(page);page.locator('#save-review-btn').scroll_into_view_if_needed();assert page.locator('#save-review-btn').bounding_box()['y']>=0
  page.evaluate('''()=>{globalThis.actualViewport=window.visualViewport;Object.defineProperty(window,'visualViewport',{configurable:true,value:{height:240,offsetTop:45}});syncDialogViewport()}''');dialog_bounds(page)
  page.evaluate('Object.defineProperty(window,"visualViewport",{configurable:true,value:actualViewport});syncDialogViewport()');page.keyboard.press('Escape');page.set_viewport_size({'width':390,'height':844})
 check('all dialog types fit portrait/landscape and reduced-height viewports, trap focus and adapt to simulated visual-viewport keyboard geometry',dialogs)
 def long_content():
  page.evaluate('allBooks[0].title="Ástarsaga þvert yfir heiminn og óvenjulegar ævintýraferðir " .repeat(8);applyFilters()')
  no_overflow(page);assert page.locator('.book-card h3').first.evaluate('(n)=>n.scrollHeight<=n.clientHeight+1')
  page.evaluate('userData=normalizeUserData({version:15,reviews:{[allBooks[0].id]:{rating:5,comment:"Íslensk stór bókasafnsumsögn Þ æ ö ".repeat(1000)}},read:[allBooks[0].id]});openTextBackup()');dialog_bounds(page)
  line=page.input_value('#backup-line-output');assert len(line)>10000
  page.get_by_role('button',name='Velja alla línuna',exact=True).click();assert page.evaluate('document.getElementById("backup-line-output").selectionEnd')==len(line)
  assert page.evaluate('(line)=>parseBackupLine(line).data.reviews[allBooks[0].id].comment.length',line)>10000
  page.keyboard.press('Escape');page.evaluate('openTextImport()');page.fill('#backup-line-input',line);dialog_bounds(page);page.keyboard.press('Escape')
  page.reload();page.wait_for_function('window.browseReady')
 check('long Icelandic titles remain fully visible and long literal backup strings can be selected and imported without overflow',long_content)
 def zoom_and_screenshots():
  page.add_style_tag(content='html {font-size:32px !important;}')
  for w in [320,390,820,1440]:
   page.set_viewport_size({'width':w,'height':1024});no_overflow(page);page.click('#nav-stats');no_overflow(page);page.click('#nav-library')
  page.reload();page.wait_for_function('window.browseReady')
  cdp=ctx.new_cdp_session(page);cdp.send('Emulation.setPageScaleFactor',{'pageScaleFactor':2});assert page.evaluate('visualViewport.scale')==2
  page.evaluate('openRandomPicker()');dialog_bounds(page);page.keyboard.press('Escape');cdp.send('Emulation.setPageScaleFactor',{'pageScaleFactor':1})
  for width,name,action in [(320,'library-320','showPage("library")'),(1440,'library-1440','showPage("library")'),(390,'recommendations-390','document.getElementById("recommendations-panel").open=true'),(820,'statistics-820','showPage("stats")'),(390,'book-dialog-390','openBookInfo(allBooks[0].id)'),(720,'series-720','openBrowse("series","harry-potter")')]:
   page.set_viewport_size({'width':width,'height':900});page.evaluate(action);page.evaluate('window.scrollTo({top:0,behavior:"instant"})');page.wait_for_timeout(100)
   if name.startswith('recommendations'):page.evaluate('window.scrollTo(0,document.getElementById("recommendations-panel").getBoundingClientRect().top+scrollY-document.querySelector("nav").getBoundingClientRect().height-12)')
   page.screenshot(path=str(OUT/(name+'.png')))
   if name.startswith('book-dialog'):page.keyboard.press('Escape')
  assert page.evaluate('matchMedia("(prefers-reduced-motion: reduce)").matches')
 check('200% text scaling, Chromium pinch-zoom, reduced motion and final screenshots',zoom_and_screenshots)
 assert not ERRORS,ERRORS
 (OUT/'results.json').write_text(json.dumps({'requestedWidths':WIDTHS,'intermediateWidths':INTERMEDIATE,'themes':THEMES,'layoutChecks':MEASUREMENTS,'groupsPassed':COUNT,'uncaughtErrors':ERRORS,'limitations':['This suite uses Chromium; separate cross-engine smoke checks cover Firefox and Linux WebKit. Native Safari and physical iOS/Android are not tested.','Keyboard checks simulate viewport geometry; no physical software keyboard was exercised.','Pinch zoom uses Chromium CDP and text scaling changes the root font size; browser chrome zoom is not automated.']},indent=2))
 browser.close();server.shutdown();print(str(COUNT)+' responsive browser groups passed')
