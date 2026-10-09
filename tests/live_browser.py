"""Second-pass checks using a real HTTP server and actual CDN CSS/JS/fonts.
Run: python tests/live_browser.py (requires Playwright, Chromium, curl and network).
Downloaded dependencies and screenshots stay in the system temporary directory.
"""
import unicodedata
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
    page.wait_for_function(f'typeof appReady !== "undefined" && appReady && window.featuresReady && allBooks.length==={len(CATALOG)}')
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
    browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH','/usr/bin/chromium'),args=['--no-sandbox'])
    desktop=context(browser,viewport={'width':1440,'height':1000})
    page=new_page(desktop)

    def assets():
        assert page.evaluate('getComputedStyle(document.getElementById("book-grid")).display')=='grid'
        assert page.evaluate('getComputedStyle(document.getElementById("book-grid")).gridTemplateColumns.split(" ").length')==10
        assert page.evaluate('[...document.fonts].some(font=>font.family==="Plus Jakarta Sans"&&font.status==="loaded")')
        assert page.evaluate('[...document.fonts].some(font=>font.family==="Font Awesome 6 Free"&&font.status==="loaded")')
        # Scroll through lazy-loaded covers without substituting image data.
        height=page.evaluate('document.documentElement.scrollHeight')
        for y in range(0,height,600):page.evaluate('(y)=>window.scrollTo(0,y)',y);page.wait_for_timeout(30)
        page.wait_for_function('[...document.querySelectorAll(".book-card img")].every(img=>img.complete&&img.naturalWidth>0)')
        assert page.locator('.book-card img').count()==min(len(CATALOG),60)
        assert page.evaluate('[...document.querySelectorAll(".book-card img")].every(img=>!img.src.endsWith("cover-placeholder.svg")&&img.alt)')
        page.evaluate('window.scrollTo(0,0)')
    check('actual Tailwind, Google Font, Font Awesome and the initial cover batch load',assets)

    def responsive_themes():
        palettes={'light':'rgb(248, 250, 252)','dark':'rgb(9, 9, 11)','green':'rgb(7, 19, 14)','purple':'rgb(13, 7, 21)','orange':'rgb(18, 11, 5)'}
        for width,height,cols in [(320,740,2),(390,844,2),(768,1024,6),(1440,1000,10),(1920,1080,12)]:
            page.set_viewport_size({'width':width,'height':height})
            for theme,color in palettes.items():
                page.evaluate('(theme)=>setBokasafnTheme(theme)',theme);page.wait_for_timeout(220)
                assert page.evaluate('getComputedStyle(document.body).backgroundColor')==color
                assert page.evaluate('getComputedStyle(document.getElementById("book-grid")).gridTemplateColumns.split(" ").length')==cols
                assert page.evaluate('document.documentElement.scrollWidth')==width
                for selector in ['#nav-library','#nav-stats','#nav-appearance','#book-search','#timer-primary-btn']:
                    inside_viewport(page,selector)
                page.click('#nav-appearance')
                inside_viewport(page,'#appearance-panel')
                expect(page.locator(f'.theme-option[data-theme="{theme}"]')).to_have_attribute('aria-pressed','true')
                page.keyboard.press('Escape')
                page.click('#nav-stats');page.wait_for_timeout(300)
                inside_viewport(page,'#personal-goal-input');inside_viewport(page,'button[onclick="addPersonalGoal()"]')
                assert page.locator('button[onclick="addPersonalGoal()"]').bounding_box()['width']>=40
                parent=page.locator('#personal-goal-input').evaluate('(e)=>({width:e.parentElement.clientWidth,scroll:e.parentElement.scrollWidth})')
                assert parent['scroll']<=parent['width']+1,parent
                page.screenshot(path=str(ARTIFACTS/f'live-{width}-{theme}-stats.png'),full_page=True)
                page.click('#nav-library');page.wait_for_timeout(300)
                page.screenshot(path=str(ARTIFACTS/f'live-{width}-{theme}-library.png'),full_page=True)
        page.set_viewport_size({'width':1440,'height':1000})
        for theme in palettes:
            page.evaluate('(theme)=>setBokasafnTheme(theme)',theme)
            page.emulate_media(color_scheme='dark');page.emulate_media(color_scheme='light')
            expect(page.locator('body')).to_have_attribute('data-theme',theme)
            page.reload(wait_until='networkidle');page.wait_for_function('appReady')
            expect(page.locator('body')).to_have_attribute('data-theme',theme)
        page.evaluate('setBokasafnTheme("system")');page.emulate_media(color_scheme='dark')
        expect(page.locator('body')).to_have_attribute('data-theme','dark')
        page.emulate_media(color_scheme='light');expect(page.locator('body')).to_have_attribute('data-theme','light')
    check('five viewport sizes, all themes, both pages, saved choices and OS theme changes',responsive_themes)

    def searching():
        reset(page)
        for query in ['Hildur','vetrar','ORRI','ó','no such book 000']:
            page.fill('#book-search',query)
            def fold(value):
                return ''.join(c for c in unicodedata.normalize('NFKD',value).lower() if not unicodedata.combining(c)).replace('þ','th').replace('ð','d').replace('æ','ae')
            expected=[book['id'] for book in CATALOG if fold(query) in fold(book['title']+'\n'+'\n'.join(book.get('titleAliases',[]))+'\n'+book['author']+'\n'+book.get('series',{}).get('name',''))]
            actual=page.locator('#book-grid .book-card').evaluate_all('(cards)=>cards.map(card=>Number(card.dataset.bookId))')
            assert page.evaluate('filteredBooks.map(book=>book.id)')==expected,(query,expected)
            assert actual==expected[:60],(query,actual,expected[:60])
            assert page.locator('#search-suggestions [data-result-type=book]').count()==min(5,len(expected))
            assert page.locator('#search-suggestions [role=button]').count()<=11
        page.fill('#book-search','Hildur');page.keyboard.press('ArrowDown')
        first=page.locator('#search-suggestions [role=button]').first
        expect(first).to_be_focused();page.keyboard.press('ArrowDown');expect(first.locator('xpath=following-sibling::li[1]')).to_be_focused()
        page.keyboard.press('ArrowUp');expect(first).to_be_focused();page.keyboard.press('Enter')
        expect(page.locator('#search-suggestions')).to_be_hidden();expect(page.locator('#book-search')).to_be_focused()
        page.fill('#book-search','vetrar');page.keyboard.press('ArrowDown');page.keyboard.press('Escape')
        expect(page.locator('#book-search')).to_be_focused();expect(page.locator('#search-suggestions')).to_be_hidden()
        page.fill('#book-search','Hildur');first=page.locator('#search-suggestions [role=button]').first;first.click()
        expect(page.locator('#search-suggestions')).to_be_hidden()
        page.fill('#book-search','')
        expect(page.locator('.book-card')).to_have_count(min(len(CATALOG),60))
    check('title/author/case/Icelandic searches, no results, mouse and keyboard suggestions',searching)

    def categories_sorting():
        reset(page)
        page.locator('[data-category="Ævintýri"]').click();page.locator('[data-category="Fantasía"]').click()
        ids=[book['id'] for book in CATALOG if 'Ævintýri' in book['categories'] and any(c in ['Fantasía','Fantasia'] for c in book['categories'])]
        assert page.locator('.book-card').evaluate_all('(cards)=>cards.map(card=>Number(card.dataset.bookId))')==ids
        page.fill('#book-search','Álfareiðin');assert page.locator('.book-card').count()==1
        page.fill('#book-search','');page.locator('[data-category="Allir"]').click()
        assert page.locator('[data-category="Fantasia"]').count()==0
        for mode in ['title-asc','title-desc','author-asc','pages-asc','pages-desc','default']:
            page.select_option('#book-sort',mode)
            assert page.locator('.book-card').count()==min(len(CATALOG),60)
            actual=page.evaluate('filteredBooks.map(book=>book.id)')
            if mode.startswith('pages'):
                values=page.evaluate('filteredBooks.filter(book=>Number(book.pages)>0).map(book=>Number(book.pages))');assert values==sorted(values,reverse=mode.endswith('desc'))
            elif mode=='default':assert actual==sorted(book["id"] for book in CATALOG)
        page.locator(f'.book-card[data-book-id="{CATALOG[0]["id"]}"]').hover();page.locator(f'.book-card[data-book-id="{CATALOG[0]["id"]}"] [data-action=like]').click()
        page.locator(f'.book-card[data-book-id="{CATALOG[0]["id"]}"] [data-action=read]').click()
        page.locator('[data-category="❤️ Óskalisti"]').click();page.locator('[data-category="✅ Lesið"]').click()
        expect(page.locator('.book-card')).to_have_count(1)
        page.select_option('#book-sort','title-desc')
        page.locator('[data-action=like]').focus();page.keyboard.press('Enter')
        expect(page.locator('.book-card')).to_have_count(0)
        page.locator('[data-category="❤️ Óskalisti"]').click()
        expect(page.locator('.book-card')).to_have_count(1)
        page.locator('[data-action=read]').focus();page.keyboard.press('Space')
        expect(page.locator('.book-card')).to_have_count(0)
        page.locator('[data-category="Allir"]').click();page.select_option('#book-sort','default')
    check('AND categories plus search, all sorting modes, read/wishlist intersections and stale-filter fixes',categories_sorting)

    def reviews_dialogs():
        reset(page)
        for width,height in [(1440,1000),(390,844),(320,740)]:
            page.set_viewport_size({'width':width,'height':height})
            for theme in ['light','dark','green','purple','orange']:
                page.evaluate('(theme)=>setBokasafnTheme(theme)',theme)
                trigger=page.locator('.book-card [data-action=info]').first;trigger.focus();page.keyboard.press('Enter')
                dialog=page.locator('#desc-modal-content');expect(dialog).to_be_focused();page.wait_for_timeout(300)
                assert dialog.evaluate('(d)=>d.scrollTop')==0
                inside_viewport(page,'#desc-modal-content')
                close=page.locator('#desc-modal-content button[aria-label="Loka bókaupplýsingum"]')
                box=close.bounding_box();assert box['y']>=0 and box['y']+box['height']<=height,box
                page.screenshot(path=str(ARTIFACTS/f'live-{width}-{theme}-book.png'))
                page.keyboard.press('Tab');expect(close).to_be_focused()
                page.locator('#desc-modal-content button').last.focus();page.keyboard.press('Tab');expect(close).to_be_focused()
                page.keyboard.press('Shift+Tab');expect(page.locator('#desc-modal-content button').last).to_be_focused()
                page.keyboard.press('Escape');expect(trigger).to_be_focused();expect(page.locator('#desc-modal')).to_be_hidden()
                recommend=page.locator('button[onclick="openRecommendModal()"]');recommend.click()
                expect(page.locator('#rec-title')).to_be_focused();inside_viewport(page,'#recommend-modal-content')
                page.keyboard.press('Escape');expect(recommend).to_be_focused();expect(page.locator('#recommend-modal')).to_be_hidden()
        page.set_viewport_size({'width':1440,'height':1000});page.evaluate('setBokasafnTheme("light")')
        page.locator('.book-card [data-action=info]').first.click()
        page.click('#save-review-btn');assert 'Veldu stjörnur' in page.locator('#desc-modal-content [data-dialog-status]').text_content()
        assert page.evaluate('Object.keys(userData.reviews).length')==0
        payload='Quotes " & <b>literal</b> </textarea><img src=x onerror="window.injected=true">'
        for rating in range(1,6):
            button=page.get_by_role('button',name=f'{rating} stjörnur',exact=True);button.focus();page.keyboard.press('Space');expect(button).to_have_attribute('aria-pressed','true')
        page.fill('#review-text',payload);page.click('#save-review-btn')
        expect(page.locator('#review-text')).to_have_value(payload)
        assert page.evaluate('(id)=>userData.read.includes(id)&&userData.reviews[id].rating===5&&window.injected===undefined',CATALOG[0]['id'])
        page.keyboard.press('Escape');page.reload(wait_until='networkidle');page.wait_for_function('appReady')
        page.click('#nav-stats');page.wait_for_timeout(300)
        assert payload in page.locator('#reviews-archive').text_content()
        assert page.locator('#reviews-archive img[src="x"]').count()==0
        page.locator('#reviews-archive [role=button]').first.focus();page.keyboard.press('Enter')
        expect(page.locator('#review-text')).to_have_value(payload)
        page.get_by_role('button',name='2 stjörnur',exact=True).click();page.fill('#review-text','Edited review');page.click('#save-review-btn');page.keyboard.press('Escape')
        assert page.evaluate('(id)=>userData.reviews[id].rating',CATALOG[0]['id'])==2
        page.click('#nav-library');page.wait_for_timeout(300)
    check('desktop/mobile book & recommendation dialogs in every theme, focus trapping, all ratings, validation, edits and escaped reviews',reviews_dialogs)

    def mobile_touch():
        mobile=context(browser,viewport={'width':390,'height':844},is_mobile=True,has_touch=True,device_scale_factor=2)
        q=new_page(mobile)
        card=q.locator(f'.book-card[data-book-id="{CATALOG[0]["id"]}"]');card.scroll_into_view_if_needed()
        expect(card.locator('[data-action=like]')).to_be_visible();card.locator('[data-action=like]').tap()
        q.locator('[data-category="❤️ Óskalisti"]').tap();expect(q.locator('.book-card')).to_have_count(1)
        q.locator('[data-action=info]').tap();expect(q.locator('#desc-modal-content')).to_be_focused()
        q.locator('#desc-modal-content button[aria-label="Loka bókaupplýsingum"]').tap()
        expect(q.locator('#desc-modal')).to_be_hidden()
        q.locator('#nav-appearance').tap();q.locator('[data-theme="green"]').tap();expect(q.locator('body')).to_have_attribute('data-theme','green')
        q.locator('#nav-appearance').tap();q.locator('#nav-stats').tap();q.wait_for_timeout(300)
        q.fill('#personal-goal-input','Touch goal');q.locator('button[onclick="addPersonalGoal()"]').tap()
        assert 'Touch goal' in q.locator('#personal-goals-list').text_content()
        mobile.close()
    check('emulated touch: visible wishlist control, modal close, theme choice and adding goals',mobile_touch)

    def timer_recovery():
        reset(page)
        page.click('#timer-primary-btn');page.wait_for_timeout(1150);page.click('#timer-primary-btn')
        assert page.evaluate('timerState.active && timerState.paused && timerState.elapsedBeforePause>=1000')
        elapsed=page.evaluate('timerState.elapsedBeforePause');page.wait_for_timeout(1100)
        assert page.evaluate('timerState.elapsedBeforePause')==elapsed
        page.reload(wait_until='networkidle');page.wait_for_function('appReady')
        assert page.evaluate('timerState.paused && timerState.elapsedBeforePause')==elapsed
        page.click('#timer-primary-btn');page.evaluate('timerState.startTime-=65000;saveUserData()')
        page.reload(wait_until='networkidle');page.wait_for_function('appReady')
        assert page.evaluate('timerState.active && !timerState.paused')
        page.click('#timer-stop-btn');page.keyboard.press('Escape');assert page.evaluate('timerState.active')
        page.click('#timer-primary-btn');page.click('#timer-stop-btn')
        expect(page.locator('#stop-confirm-modal-content button').first).to_be_focused()
        page.locator('#stop-confirm-modal-content button').first.click()
        total=page.evaluate('userData.totalSeconds');assert total>=66
        page.reload(wait_until='networkidle');page.wait_for_function('appReady')
        assert page.evaluate('userData.totalSeconds')==total and not page.evaluate('timerState.active')
        assert page.evaluate('Object.values(userData.dailyProgress).reduce((a,b)=>a+b,0)')==total
    check('real timer start/pause/resume, active and paused refresh recovery, cancel/save and no double counting',timer_recovery)

    def goals():
        reset(page);page.click('#nav-stats');page.wait_for_timeout(300)
        page.fill('#personal-goal-input','<img src=x onerror="window.injected=true"> goal');page.keyboard.press('Enter')
        assert page.locator('#personal-goals-list img').count()==0
        page.locator('#personal-goals-list button[aria-pressed]').click();expect(page.locator('#personal-goals-list button[aria-pressed]')).to_have_attribute('aria-pressed','true')
        page.reload(wait_until='networkidle');page.wait_for_function('appReady');page.click('#nav-stats');page.wait_for_timeout(300)
        expect(page.locator('#personal-goals-list button[aria-pressed]')).to_have_attribute('aria-pressed','true')
        page.locator('#personal-goals-list button[aria-label^="Eyða"]').click();expect(page.locator('#personal-goals-list button')).to_have_count(0)
        page.evaluate('userData.dailyProgress={};const today=new Date();const yesterday=new Date();yesterday.setDate(yesterday.getDate()-1);userData.dailyProgress[getLocalYYYYMMDD(today)]=1800;userData.dailyProgress[getLocalYYYYMMDD(yesterday)]=1800;')
        page.fill('#target-minutes-input','30');page.select_option('#goal-type-select','daily')
        expect(page.locator('#stat-streak')).to_have_text('2');assert 'Markmiði náð' in page.locator('#minutes-goal-status').text_content()
        page.fill('#target-minutes-input','60');expect(page.locator('#stat-streak')).to_have_text('0')
        page.select_option('#goal-type-select','weekly');expect(page.locator('#stat-streak')).to_have_text('1')
        page.select_option('#goal-type-select','monthly');expect(page.locator('#stat-streak')).to_have_text('1')
        page.fill('#target-minutes-input','0');expect(page.locator('#stat-streak')).to_have_text('2')
        expect(page.locator('#minutes-goal-progress-container')).to_be_hidden()
        page.fill('#target-minutes-input','-5');assert page.evaluate('userData.minutesGoal')==0
        page.reload(wait_until='networkidle');page.wait_for_function('appReady')
        assert page.evaluate('userData.goalType')=='monthly'
    check('personal goal add/complete/delete/reload, safe text, daily/weekly/monthly progress and clearing/invalid targets',goals)

    def migration():
        legacy={'liked':[CATALOG[0]['title'],'Missing old title'],'read':[CATALOG[0]['title']],'reviews':{CATALOG[0]['title']:{'rating':4,'comment':'Old <b>literal</b> review','date':'1.10.2026'}},'totalSeconds':1234,'dailyProgress':{'2026-10-01':1234},'minutesGoal':20,'goalType':'weekly','personalGoals':[{'id':10,'text':'Old goal','completed':True}]}
        ctx=context(browser);ctx.add_init_script('if(!sessionStorage.seeded){localStorage.setItem("library_v14",'+json.dumps(json.dumps(legacy))+');sessionStorage.seeded="yes";}')
        q=new_page(ctx)
        state=q.evaluate('userData');assert state['liked']==[CATALOG[0]['id']] and state['read']==[CATALOG[0]['id']] and state['totalSeconds']==1234 and state['reviews'][str(CATALOG[0]['id'])]['rating']==4
        assert state['unresolved']['liked']==['Missing old title']
        assert json.loads(q.evaluate('localStorage.getItem("library_v14")'))==legacy
        altered=[dict(book) for book in CATALOG];altered[0]['title']='Renamed book title'
        q.route('**/Resources/books.json',lambda route:route.fulfill(content_type='application/json',body=json.dumps(altered)))
        q.reload(wait_until='networkidle');q.wait_for_function('appReady')
        assert q.evaluate('(id)=>userData.liked.includes(id)&&userData.read.includes(id)&&userData.reviews[id].rating===4',CATALOG[0]['id'])
        assert 'Renamed book title' in q.locator(f'.book-card[data-book-id="{CATALOG[0]["id"]}"]').text_content()
        ctx.close()
        for saved in ['{malformed','null','{"reviews":null,"read":null,"liked":null,"dailyProgress":null,"personalGoals":null}']:
            ctx=context(browser);ctx.add_init_script('localStorage.setItem("library_v14",'+json.dumps(saved)+')');q=new_page(ctx)
            assert q.evaluate('localStorage.getItem("library_v14")')==saved
            assert q.locator('.book-card').count()==min(len(CATALOG),60)
            ctx.close()
    check('real v14 migration, backup/unmatched preservation, title renaming and corrupt/partial storage',migration)

    def startup():
        seed=json.dumps({'version':15,'read':[1],'totalSeconds':7200})
        ctx=context(browser);ctx.add_init_script('if(!sessionStorage.seeded){localStorage.setItem("library_v15",'+json.dumps(seed)+');sessionStorage.seeded="yes"}')
        q=ctx.new_page();q.on('pageerror',lambda e:ERRORS.append(str(e)));pending=[]
        q.route('**/Resources/books.json',lambda route:pending.append(route))
        q.goto(URL,wait_until='domcontentloaded');q.wait_for_function('typeof handleTimerPrimaryAction==="function"')
        assert q.locator('main').evaluate('(el)=>el.inert')
        assert q.locator('nav').evaluate('(el)=>el.inert')
        q.evaluate('handleTimerPrimaryAction()');assert not q.evaluate('timerState.active')
        assert q.evaluate('saveUserData()') is False
        assert q.evaluate('localStorage.getItem("library_v15")')==seed
        q.reload(wait_until='domcontentloaded');q.wait_for_function('typeof handleTimerPrimaryAction==="function"')
        # Cancelling the old fetch during navigation can finish initialization
        # in the old document. Normalization is allowed; saved progress must stay.
        saved = json.loads(q.evaluate('localStorage.getItem("library_v15")'))
        assert saved['totalSeconds']==7200 and saved['read']==[1],saved
        q.wait_for_timeout(100)
        assert len(pending)>=2
        for old_route in pending[:-1]:
            try: old_route.abort()
            except Exception: pass  # Navigation has already cancelled the old request.
        pending[-1].fulfill(content_type='application/json',body=json.dumps(CATALOG))
        q.wait_for_function('appReady');assert q.evaluate('userData.totalSeconds')==7200
        assert q.evaluate('userData.read.includes(1)')
        assert not q.locator('main').evaluate('(el)=>el.inert')
        q.locator('#timer-primary-btn').click();assert q.evaluate('timerState.active')
        ctx.close()
    check('slow catalog and refresh before initialization preserve existing saved progress',startup)

    def fallback_storage_errors():
        reset(page)
        image=page.locator('.book-card img').first
        image.evaluate('(img)=>img.src="Resources/Images/missing.jpg"')
        page.wait_for_function('document.querySelector(".book-card img").src.endsWith("cover-placeholder.svg")')
        assert image.evaluate('(img)=>img.onerror===null && !img.classList.contains("opacity-0")')
        page.wait_for_function('document.querySelector(".book-card img").complete&&document.querySelector(".book-card img").naturalWidth>0')
        assert image.get_attribute('alt')
        page.locator('.book-card [data-action=info]').first.click()
        modal_image=page.locator('#desc-modal-content img');modal_image.evaluate('(img)=>img.src="Resources/Images/missing-modal.jpg"')
        page.wait_for_function('document.querySelector("#desc-modal-content img").src.endsWith("cover-placeholder.svg")')
        assert modal_image.evaluate('(img)=>img.onerror===null')
        page.keyboard.press('Escape')
        missing_context=context(browser)
        missing_page=new_page(missing_context)
        missing_fallback=[]
        def missing_svg(route):
            missing_fallback.append(route.request.url);route.fulfill(status=404,body='missing')
        missing_page.route('**/cover-placeholder.svg',missing_svg)
        failed_image=missing_page.locator('.book-card img').first
        failed_image.evaluate('(img)=>{img.loading="eager";img.src="Resources/Images/another-missing.jpg"}')
        missing_page.wait_for_function('document.querySelector(".book-card img").src.endsWith("cover-placeholder.svg") && document.querySelector(".book-card img").complete')
        missing_page.wait_for_timeout(300)
        assert len(missing_fallback)==1,missing_fallback
        assert failed_image.evaluate('(img)=>img.onerror===null && !!img.alt && !img.classList.contains("opacity-0")')
        missing_context.close()
        page.click('#timer-primary-btn');page.evaluate('() => {timerState.startTime-=10000;checkpointTimer();window.originalSetItem=Storage.prototype.setItem;Storage.prototype.setItem=function(){throw new DOMException("quota","QuotaExceededError")};}')
        page.click('#timer-stop-btn');page.locator('#stop-confirm-modal-content button').first.click()
        assert page.evaluate('timerState.active') and page.evaluate('userData.totalSeconds')==0
        assert 'Ekki tókst að vista' in page.locator('#stop-confirm-modal-content [data-dialog-status]').text_content()
        page.evaluate('() => {Storage.prototype.setItem=window.originalSetItem;}');page.locator('#stop-confirm-modal-content button').first.click()
        assert not page.evaluate('timerState.active') and page.evaluate('userData.totalSeconds')>=10
    check('grid/dialog cover failures and failed-save dialog announcement with safe timer retry',fallback_storage_errors)

    assert not ERRORS,ERRORS
    assert not FAILURES,FAILURES
    print(json.dumps({'groups_passed':COUNT,'uncaught_errors':ERRORS,'dependency_failures':FAILURES,'real_dependency_urls':DEPENDENCIES,'artifacts':str(ARTIFACTS)},indent=2),flush=True)
    browser.close()
server.shutdown();server.server_close()
