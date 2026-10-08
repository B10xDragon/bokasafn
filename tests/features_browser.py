"""Second-pass checks using a real HTTP server and actual CDN CSS/JS/fonts.
Run: python tests/live_browser.py (requires Playwright, Chromium, curl and network).
Downloaded dependencies and screenshots stay in the system temporary directory.
"""
import hashlib
import json
import mimetypes
import os
import subprocess
import tempfile
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT/'Resources/books.json').read_text())
CACHE = Path(tempfile.gettempdir())/'bokasafn-real-assets'
ARTIFACTS = Path(tempfile.gettempdir())/'bokasafn-verification'
CACHE.mkdir(exist_ok=True); ARTIFACTS.mkdir(exist_ok=True)
DEPENDENCIES = {}
FAILURES = []

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_): pass

# Fetch real bytes through curl's inherited proxy and CA trust. No fake styles or
# disabled TLS verification; route fulfillment only bridges executor networking.
def real_dependencies(route):
    url = route.request.url
    parsed = urlparse(url)
    target = CACHE/hashlib.sha256(url.encode()).hexdigest()
    if not target.exists():
        result = subprocess.run(['curl','--silent','--show-error','--fail','--location','--max-time','25',url],capture_output=True)
        if result.returncode:
            FAILURES.append({'url':url,'error':result.stderr.decode()});route.abort();return
        target.write_bytes(result.stdout)
    mime = mimetypes.guess_type(parsed.path)[0]
    if parsed.netloc == 'fonts.googleapis.com': mime = 'text/css'
    if parsed.netloc == 'cdn.tailwindcss.com': mime = 'application/javascript'
    DEPENDENCIES[url] = target.stat().st_size
    route.fulfill(body=target.read_bytes(),content_type=mime or 'application/octet-stream',headers={'Access-Control-Allow-Origin':'*'})

server = ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
URL = 'http://127.0.0.1:'+str(server.server_port)+'/'
ERRORS = []
COUNT = 0

def context(browser, **options):
    result=browser.new_context(**options)
    result.route('https://**/*',real_dependencies)
    return result

def ready(page):
    page.goto(URL,wait_until='networkidle')
    page.wait_for_function(f'appReady && window.featuresReady && allBooks.length==={len(CATALOG)}')
    page.evaluate('document.fonts.ready')
    page.wait_for_timeout(300)

def new_page(ctx):
    page=ctx.new_page()
    page.on('pageerror',lambda error:ERRORS.append(str(error)))
    ready(page)
    return page

def reset(page):
    page.evaluate('clearInterval(timerState.interval);timerState=emptyTimerState();userData=normalizeUserData({});activeCategories=[];searchQuery="";document.getElementById("book-search").value="";saveUserData();updateTimerUI();updateTimerDisplay();syncGoalUI();updateStatsUI();applyFilters();showPage("library")')
    page.wait_for_timeout(300)

def check(name, fn):
    global COUNT
    selected = os.environ.get('BOKASAFN_TEST_GROUP')
    if selected and selected not in name: return;
    fn();COUNT+=1;print('PASS '+name,flush=True)

def inside_viewport(page, selector):
    box=page.locator(selector).bounding_box()
    assert box and box['width']>0 and box['x']>=-1 and box['x']+box['width']<=page.viewport_size['width']+1,(selector,box)

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    ctx=context(browser,viewport={'width':1440,'height':1000})
    page=new_page(ctx)
    def feature_layouts():
        for width in [320,390,768,1440,1920]:
            page.set_viewport_size({'width':width,'height':900})
            for theme in ['light','dark','green','purple','orange']:
                page.evaluate('(t)=>setBokasafnTheme(t)',theme)
                for view in ['library','stats']:
                    page.evaluate('(v)=>showPage(v)',view);page.wait_for_timeout(250)
                    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,theme,view,page.evaluate('[...document.querySelectorAll("body *")].filter(n=>n.getBoundingClientRect().right>innerWidth+1&&n.getBoundingClientRect().width>0).map(n=>[n.tagName,n.id,n.className,n.getBoundingClientRect().right]).slice(-20)'))
                    if view=='stats':
                        assert page.locator('#achievement-list article').count()==11
                        assert page.locator('.heat-cell').count()>=365
                        assert page.locator('.heat-cell[tabindex="0"]').count()==1
                        page.locator('.heat-cell[tabindex="0"]').focus();page.keyboard.press('ArrowLeft');assert page.locator('.heat-cell[tabindex="0"]').count()==1
                page.screenshot(path=str(ARTIFACTS/f'features-{width}-{theme}.png'),full_page=True)
        page.set_viewport_size({'width':1440,'height':1000});reset(page)
    check('new panels at five sizes and all themes, keyboard heatmap without horizontal page overflow',feature_layouts)
    def filters_random():
        page.locator('#advanced-filters summary').click()
        page.select_option('#filter-state','unread');page.fill('#filter-min','100');page.fill('#filter-max','200')
        assert page.evaluate('filteredBooks.every(b=>b.pages>=100&&b.pages<=200&&!userData.read.includes(b.id))')
        page.evaluate('resetAdvancedFilters();toggleRead(allBooks[0].id);toggleLike(allBooks[0].id)')
        page.select_option('#filter-state','wishlist');assert page.evaluate('filteredBooks.length')==1
        page.select_option('#filter-author',CATALOG[0]['author']);assert page.evaluate('filteredBooks.length')==1
        page.evaluate('resetAdvancedFilters();userData.reviews[allBooks[0].id]={rating:5,comment:"ok"};saveUserData();applyFilters()')
        page.select_option('#book-sort','rating-desc');assert page.evaluate('filteredBooks[0].id')==CATALOG[0]['id']
        page.select_option('#book-sort','recent-read');assert page.evaluate('filteredBooks[0].id')==CATALOG[0]['id']
        page.evaluate('openRandomPicker()');page.wait_for_timeout(350)
        page.fill('#random-min','99999');page.get_by_role('button',name='Velja bók',exact=True).click();assert 'Engin bók' in page.locator('#random-result').text_content()
        page.fill('#random-min','');page.get_by_role('button',name='Velja bók',exact=True).click();assert page.locator('#random-result h3').count()==1
        page.get_by_role('button',name='Skoða bókina',exact=True).click();page.wait_for_timeout(350);assert page.locator('#desc-modal').get_attribute('aria-hidden')=='false'
        page.keyboard.press('Escape');page.wait_for_timeout(350);reset(page)
    check('combined advanced filters, rating/recent sorts, random zero/results and accessible dialog handoff',filters_random)
    def urls():
        page.evaluate('openBookInfo(allBooks[0].id)');page.wait_for_timeout(350);assert '?book='+str(CATALOG[0]['id']) in page.url
        page.reload();page.wait_for_function('window.featuresReady');page.wait_for_timeout(350);assert page.locator('#book-dialog-title').text_content()==CATALOG[0]['title']
        page.keyboard.press('Escape');page.wait_for_timeout(400);assert 'book=' not in page.url
        page.evaluate('openBookInfo(allBooks[0].id)');page.wait_for_timeout(350);page.go_back();page.wait_for_timeout(350);assert page.locator('#desc-modal').get_attribute('aria-hidden')=='true'
        page.go_forward();page.wait_for_timeout(350);assert page.locator('#book-dialog-title').text_content()==CATALOG[0]['title']
        page.evaluate('openBookInfo(allBooks[1].id)');page.wait_for_timeout(350);page.go_back();page.wait_for_timeout(350);assert page.locator('#book-dialog-title').text_content()==CATALOG[0]['title']
        page.keyboard.press('Escape');page.wait_for_timeout(350)
        fresh=context(browser);second=fresh.new_page();second.goto(URL+'?book='+str(CATALOG[2]['id']));second.wait_for_function('window.featuresReady');second.wait_for_timeout(350);assert second.locator('#book-dialog-title').text_content()==CATALOG[2]['title'];fresh.close()
        page.goto(URL+'?book=999999');page.wait_for_function('window.featuresReady');assert page.locator('#desc-modal').get_attribute('aria-hidden')=='true';reset(page)
    check('book deep links, reload, close, Back/Forward, changing books and another browser',urls)
    def achievements_challenges():
        page.evaluate('showPage("stats");addBuiltInChallenge("fantasy");addBuiltInChallenge("author");addBuiltInChallenge("month");addBuiltInChallenge("pages")');page.wait_for_timeout(350)
        page.locator('#reading-insights details summary').click();page.fill('#challenge-title','<img src=x onerror=alert(1)>');page.fill('#challenge-target','1');page.get_by_role('button',name='Bæta við áskorun',exact=True).click()
        page.evaluate('toggleRead(allBooks.find(b=>b.categories.includes("Fantasía")).id)');assert page.evaluate('userData.challenges.some(c=>c.completed)');assert page.evaluate('!!userData.achievements.first')
        assert page.locator('#challenge-list img').count()==0
        page.reload();page.wait_for_function('window.featuresReady');assert page.evaluate('userData.challenges.length')==5;assert page.evaluate('!!userData.achievements.first')
        page.evaluate('showPage("stats")');page.wait_for_timeout(350);assert 'Lokið' in page.locator('#challenge-list').text_content()
        assert page.locator('#extended-metrics').text_content();assert page.locator('#personal-recommendations button').count()>0
        page.locator('#challenge-list button').last.click();assert page.evaluate('userData.challenges.length')==4
        reset(page)
    check('built-in/custom challenge progress completion reload deletion, escaped title and achievements',achievements_challenges)
    def backups():
        page.evaluate('toggleRead(allBooks[0].id);toggleLike(allBooks[1].id);setBokasafnTheme("purple");showPage("stats")');page.wait_for_timeout(350)
        with page.expect_download() as result:page.get_by_role('button',name='Sækja JSON-afrit',exact=True).click()
        downloaded=result.value;target=ARTIFACTS/'backup.json';downloaded.save_as(target);backup=json.loads(target.read_text());assert backup['data']['read']==[CATALOG[0]['id']];assert backup['preferences']['theme']=='purple'
        # Invalid imports leave the exact data untouched.
        before=page.evaluate('JSON.stringify(userData)')
        for content in ['{broken','null','{}',json.dumps({'version':99,'read':[]}),json.dumps({'read':[],'dailyProgress':{'bad':10}})]:
            page.set_input_files('#backup-file',{'name':'bad.json','mimeType':'application/json','buffer':content.encode()});page.wait_for_timeout(80);assert page.evaluate('JSON.stringify(userData)')==before
        page.evaluate('toggleRead(allBooks[2].id);userData.reviews[allBooks[0].id]={rating:5,comment:"local"};saveUserData()')
        page.set_input_files('#backup-file',target);page.wait_for_timeout(350);page.get_by_role('button',name='Sameina örugglega',exact=True).click();page.wait_for_timeout(350);assert page.evaluate('userData.read.length')==2;assert page.evaluate('userData.reviews[allBooks[0].id].comment')=='local'
        page.set_input_files('#backup-file',target);page.wait_for_timeout(350);page.get_by_role('button',name='Skipta út gögnum',exact=True).click();page.get_by_role('button',name='Já, skipta út',exact=True).click();page.wait_for_timeout(350);assert page.evaluate('userData.read.length')==1
        assert page.evaluate('Object.keys(localStorage).some(k=>k.startsWith("library_import_backup_"))')
        # Import on a fresh browser and import raw v14.
        other=context(browser);op=new_page(other);op.evaluate('showPage("stats")');op.wait_for_timeout(350);op.set_input_files('#backup-file',target);op.wait_for_timeout(350);op.get_by_role('button',name='Skipta út gögnum',exact=True).click();op.get_by_role('button',name='Já, skipta út',exact=True).click();op.wait_for_timeout(350);assert op.evaluate('userData.read.length')==1;assert op.evaluate('bokasafnThemePreference')=='purple'
        old=json.dumps({'read':[CATALOG[2]['title']],'liked':[],'totalSeconds':900});op.set_input_files('#backup-file',{'name':'v14.json','mimeType':'application/json','buffer':old.encode()});op.wait_for_timeout(350);op.get_by_role('button',name='Sameina örugglega',exact=True).click();op.wait_for_timeout(350);assert op.evaluate('userData.read.length')==2
        other.close();reset(page)
    check('actual backup download, malformed files, merge/replace confirmation rollback copies and cross-browser/v14 import',backups)
    def import_failures_and_sharing():
        reset(page);page.evaluate('showPage("stats")');page.wait_for_timeout(350)
        payload=json.dumps({'version':15,'read':[CATALOG[1]['id']],'liked':[],'totalSeconds':600})
        def preview():
            page.set_input_files('#backup-file',{'name':'ok.json','mimeType':'application/json','buffer':payload.encode()});page.wait_for_timeout(350)
        page.evaluate('handleTimerPrimaryAction()');preview();page.get_by_role('button',name='Sameina örugglega',exact=True).click()
        assert page.evaluate('timerState.active && userData.read.length===0')
        assert 'Vistaðu virku' in page.locator('#feature-modal-content [data-dialog-status]').text_content()
        page.keyboard.press('Escape');page.wait_for_timeout(350);page.evaluate('timerState.startTime-=10000;confirmStopReading()');page.wait_for_timeout(350)
        before=page.evaluate('JSON.stringify(userData)');stored=page.evaluate('localStorage.getItem("library_v15")')
        preview();page.evaluate('() => {window.savedSetter=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k==="library_v15")throw new DOMException("quota","QuotaExceededError");return window.savedSetter.call(this,k,v);};}')
        page.get_by_role('button',name='Sameina örugglega',exact=True).click();assert page.evaluate('JSON.stringify(userData)')==before;assert page.evaluate('localStorage.getItem("library_v15")')==stored
        assert 'Ekki tókst að vista' in page.locator('#feature-modal-content [data-dialog-status]').text_content()
        page.evaluate('() => {Storage.prototype.setItem=window.savedSetter;}');page.get_by_role('button',name='Sameina örugglega',exact=True).click();page.wait_for_timeout(350);assert page.evaluate('userData.read.includes(allBooks[1].id)')
        page.evaluate('showPage("library");openBookInfo(allBooks[0].id)');page.wait_for_timeout(350)
        ctx.grant_permissions(['clipboard-read','clipboard-write'])
        page.get_by_role('button',name='Afrita bókatengil',exact=True).click();page.wait_for_timeout(100);assert 'book='+str(CATALOG[0]['id']) in page.evaluate('navigator.clipboard.readText()')
        page.keyboard.press('Escape');page.reload();page.wait_for_function('window.featuresReady');assert 'book=' not in page.url;assert page.locator('#desc-modal').get_attribute('aria-hidden')=='true'
        reset(page)
    check('active-session import blocking, quota rollback and retry, actual clipboard link and immediate-close reload',import_failures_and_sharing)
    def duplicate_challenges():
        reset(page);page.evaluate('showPage("stats");setBokasafnTheme("green")');page.wait_for_timeout(350)
        for kind in ['month','pages','fantasy','author']:
            page.evaluate('(kind)=>{for(let i=0;i<8;i++)addBuiltInChallenge(kind);}',kind)
        assert page.evaluate('userData.challenges.length')==4
        page.reload();page.wait_for_function('window.featuresReady');page.evaluate('showPage("stats")');page.wait_for_timeout(350)
        assert page.locator('#challenge-list article').count()==4
        # Reproduce the screenshot's four old monthly copies, without deleting data.
        page.evaluate('userData.challenges=userData.challenges.filter(c=>c.kind==="books");const first=userData.challenges[0];for(let i=0;i<3;i++)userData.challenges.push({...first,id:newDataId(),baseline:[...first.baseline]});saveUserData();renderInsights()')
        assert page.locator('#challenge-list article').count()==1
        assert page.evaluate('userData.challenges.length')==4
        page.reload();page.wait_for_function('window.featuresReady');page.evaluate('showPage("stats")');page.wait_for_timeout(350)
        assert page.locator('#challenge-list article').count()==1
        for width in [320,390,1280]:
            page.set_viewport_size({'width':width,'height':889})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
        page.screenshot(path=str(ARTIFACTS/'challenge-duplicate-fix.png'),full_page=True)
        with page.expect_download() as result:page.get_by_role('button',name='Sækja JSON-afrit',exact=True).click()
        target=ARTIFACTS/'duplicate-preservation.json';result.value.save_as(target);assert len(json.loads(target.read_text())['data']['challenges'])==4
        page.locator('#challenge-list button').click();assert page.evaluate('userData.challenges.length')==0;assert page.locator('#challenge-list article').count()==0
        page.get_by_role('button',name='3 bækur í þessum mánuði',exact=True).click();assert page.evaluate('userData.challenges.length')==1
        page.evaluate('userData.challenges[0].completed=getLocalYYYYMMDD(new Date());saveUserData();addBuiltInChallenge("month")');assert page.evaluate('userData.challenges.length')==1
    check('repeat taps block duplicates and old identical cards collapse without data loss across reload and export',duplicate_challenges)
    def historical_discovery_challenges():
        reset(page)
        # Existing screenshot state: read fantasy book but challenges say 0/1.
        page.evaluate('const b=allBooks.find(b=>b.categories.includes("Fantasía"));userData=normalizeUserData({version:15,read:[b.id],challenges:[{id:"old-fantasy",title:"Lestu fantasíubók",kind:"fantasy",target:1,start:getLocalYYYYMMDD(new Date()),baseline:[b.id]},{id:"old-author",title:"Uppgötvaðu nýjan höfund",kind:"author",target:1,start:getLocalYYYYMMDD(new Date()),baseline:[b.id]}]});saveUserData()')
        page.reload();page.wait_for_function('window.featuresReady');page.evaluate('showPage("stats");setBokasafnTheme("green")');page.wait_for_timeout(350)
        assert page.evaluate('userData.challenges.every(c=>c.completed)')
        assert page.evaluate('Object.keys(userData.completedDates).length')==0
        for card in page.locator('#challenge-list article').all():
            assert 'Lokið' in card.text_content() and '1 / 1' in card.text_content()
            assert card.locator('progress').get_attribute('value')=='1'
        page.set_viewport_size({'width':1280,'height':889});page.screenshot(path=str(ARTIFACTS/'historical-challenges-complete.png'),full_page=True)
        page.get_by_role('button',name='Fantasíubók',exact=True).click();assert page.evaluate('userData.challenges.length')==3
        assert page.evaluate('userData.challenges[2].historyMode')=='since-start'
        assert page.evaluate('challengeProgress(userData.challenges[2])')==0
        page.evaluate('addBuiltInChallenge("fantasy")');assert page.evaluate('userData.challenges.length')==3
        page.reload();page.wait_for_function('window.featuresReady');assert page.evaluate('userData.challenges[2].historyMode')=='since-start';assert not page.evaluate('userData.challenges[2].completed')
        # First join after previous reading also recognises old history immediately.
        page.evaluate('userData.challenges=[];saveUserData();renderInsights();showPage("stats")');page.wait_for_timeout(350)
        page.get_by_role('button',name='Fantasíubók',exact=True).click();page.get_by_role('button',name='Nýr höfundur',exact=True).click()
        assert page.evaluate('userData.challenges.every(c=>c.historyMode==="all"&&c.completed)')
        page.evaluate('userData=normalizeUserData({});saveUserData();addBuiltInChallenge("fantasy");addBuiltInChallenge("author")');assert page.evaluate('userData.challenges.every(c=>!c.completed)')
    check('historical fantasy/author completions recover screenshot state, persist and exclude old books on repeat attempts',historical_discovery_challenges)
    assert not ERRORS,ERRORS
    assert not FAILURES,FAILURES
    print(json.dumps({'groups_passed':COUNT,'uncaught_errors':ERRORS,'dependency_failures':FAILURES},indent=2))
    browser.close()
server.shutdown();server.server_close()
