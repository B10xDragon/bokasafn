"""Offline Chromium regression checks. Run: python tests/browser.py

Requires Playwright and Chromium. Routes serve the actual repository files;
third-party fonts/icons are excluded and minimal Tailwind layout utilities are
supplied locally so these checks do not depend on CDN availability.
"""
import json
import mimetypes
import os
from pathlib import Path
from urllib.parse import urlparse, unquote
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
URL = 'http://bokasafn.test/'
UTILITY_CSS = '''.hidden{display:none!important}.opacity-0{opacity:0}.pointer-events-none{pointer-events:none}
.fixed{position:fixed}.inset-0{inset:0}.flex{display:flex}.items-center{align-items:center}
.justify-center{justify-content:center}.grid{display:grid}.relative{position:relative}
.absolute{position:absolute}.flex-col{flex-direction:column}.w-full{width:100%}
.max-w-lg{max-width:32rem}.max-w-md{max-width:28rem}.max-w-4xl{max-width:56rem}
.z-\\[100\\]{z-index:100}.z-\\[110\\]{z-index:110}.z-50{z-index:50}
.p-6{padding:1.5rem}.p-4{padding:1rem}.bg-white{background:white}
button,[role=button]{cursor:pointer} #book-grid{grid-template-columns:repeat(6,1fr);gap:1rem}
.book-img-container{height:140px}.book-img-container img{width:100%;height:100%}
#desc-modal-content,#recommend-modal-content,#stop-confirm-modal-content{max-height:90vh;overflow-y:auto}
#desc-modal-content img{width:120px;height:180px}
'''

def route_files(route):
    url = urlparse(route.request.url)
    if url.hostname == 'cdn.tailwindcss.com':
        route.fulfill(content_type='application/javascript', body='const style=document.createElement("style");style.textContent='+json.dumps(UTILITY_CSS)+';document.head.appendChild(style);')
        return
    if url.hostname != 'bokasafn.test':
        route.fulfill(content_type='text/css', body='')
        return
    path = ROOT / (unquote(url.path).lstrip('/') or 'index.html')
    if path.is_file():
        route.fulfill(content_type=mimetypes.guess_type(path)[0] or 'text/plain', body=path.read_bytes())
    else:
        route.fulfill(status=404, body='missing')

def check(name, fn):
    fn()
    print('PASS ' + name, flush=True)

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH', '/usr/bin/chromium'), args=['--no-sandbox'])
    context = browser.new_context(viewport={'width':1280,'height':900}, color_scheme='dark')
    context.route('**/*', route_files)
    page = context.new_page()
    errors = []
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(URL)
    page.wait_for_function('allBooks.length === 39 && document.querySelectorAll(".book-card").length === 39')
    expect(page.locator('#book-sort')).to_have_count(1)
    first = page.evaluate('allBooks[0]')
    print('PASS catalog startup and existing sorting enhancement', flush=True)

    def filters():
        page.evaluate('toggleLike(1);toggleRead(1);toggleCategory("❤️ Óskalisti")')
        expect(page.locator('.book-card')).to_have_count(1)
        page.locator('[data-action="like"]').focus()
        page.keyboard.press('Enter')
        expect(page.locator('.book-card')).to_have_count(0)
        expect(page.locator('#book-search')).to_be_focused()
        page.evaluate('toggleCategory("Allir");toggleCategory("✅ Lesið")')
        page.locator('[data-action="read"]').focus()
        page.keyboard.press('Space')
        expect(page.locator('.book-card')).to_have_count(0)
        page.evaluate('toggleCategory("Allir")')
        page.select_option('#book-sort', 'title-desc')
        titles = page.locator('.book-card h3').all_text_contents()
        assert titles == page.evaluate('filteredBooks.map(book=>book.title)')
        page.select_option('#book-sort', 'default')
    check('keyboard wishlist/read controls recompute filters and preserve sorting', filters)

    def dialogs():
        card = page.locator('.book-card [data-action="info"]').first
        card.focus();page.keyboard.press('Enter')
        expect(page.locator('#desc-modal')).to_be_visible()
        expect(page.locator('#desc-modal-content')).to_be_focused()
        assert page.locator('main').evaluate('(el)=>el.inert')
        page.locator('#desc-modal-content button').last.focus();page.keyboard.press('Tab')
        expect(page.locator('#desc-modal-content button').first).to_be_focused()
        page.keyboard.press('Shift+Tab')
        expect(page.locator('#desc-modal-content button').last).to_be_focused()
        page.keyboard.press('Escape')
        expect(card).to_be_focused()
        expect(page.locator('#desc-modal')).to_be_hidden()
        assert not page.locator('main').evaluate('(el)=>el.inert')
        recommend = page.locator('button[onclick="openRecommendModal()"]')
        recommend.focus();page.keyboard.press('Enter')
        expect(page.locator('#rec-title')).to_be_focused()
        expect(page.locator('#recommend-modal-content')).to_have_class(__import__('re').compile('scale-100'))
        page.keyboard.press('Escape');expect(recommend).to_be_focused()
        expect(page.locator('#recommend-modal')).to_be_hidden()
    check('book and recommendation dialogs trap focus, close with Escape, restore focus', dialogs)

    def hostile_text():
        page.locator('.book-card [data-action="info"]').first.focus();page.keyboard.press('Enter')
        payload = '</textarea><img src=x onerror="window.injected=true"><script>window.injected=true</script>'
        page.fill('#review-text',payload)
        page.get_by_role('button',name='4 stjörnur',exact=True).click()
        expect(page.get_by_role('button',name='4 stjörnur',exact=True)).to_have_attribute('aria-pressed','true')
        page.click('#save-review-btn')
        expect(page.locator('#review-text')).to_have_value(payload)
        assert page.evaluate('window.injected === undefined')
        assert page.locator('#reviews-archive').text_content().find(payload)>=0
        page.keyboard.press('Escape')
        page.click('#nav-stats');page.wait_for_timeout(250)
        page.fill('#personal-goal-input',payload);page.keyboard.press('Enter')
        assert payload in page.locator('#personal-goals-list').text_content()
        assert page.locator('#personal-goals-list img, #personal-goals-list script').count()==0
        assert page.evaluate('window.injected === undefined')
        page.reload();page.wait_for_function('allBooks.length===39');page.evaluate('showPage("stats")');page.wait_for_timeout(250)
        assert payload in page.locator('#personal-goals-list').text_content()
        page.click('#nav-library');page.wait_for_timeout(250)
    check('hostile review and goal text remains literal before and after reload', hostile_text)

    def themes():
        for theme in ['light','green','dark','purple','orange']:
            page.evaluate('(theme)=>setBokasafnTheme(theme)',theme)
            page.emulate_media(color_scheme='light');page.emulate_media(color_scheme='dark')
            page.wait_for_timeout(50)
            expect(page.locator('body')).to_have_attribute('data-theme',theme)
            expect(page.locator(f'.theme-option[data-theme="{theme}"]')).to_have_attribute('aria-pressed','true')
            # System dark rules must not override selected theme surfaces.
            colors = page.evaluate('({surface:getComputedStyle(document.querySelector(".glass-card")).backgroundColor, theme:getComputedStyle(document.body).getPropertyValue("--theme-surface").trim()})')
            assert colors['surface']!='rgb(30, 41, 59)'
        page.evaluate('setBokasafnTheme("system")');page.emulate_media(color_scheme='light')
        expect(page.locator('body')).to_have_attribute('data-theme','light')
        page.emulate_media(color_scheme='dark')
        expect(page.locator('body')).to_have_attribute('data-theme','dark')
        page.evaluate('setBokasafnTheme("purple")');page.reload();page.wait_for_function('allBooks.length===39')
        expect(page.locator('body')).to_have_attribute('data-theme','purple')
        page.click('#nav-appearance');expect(page.locator('#nav-appearance')).to_have_attribute('aria-expanded','true')
        page.keyboard.press('Escape');expect(page.locator('#nav-appearance')).to_be_focused()
    check('manual and system themes behave consistently and survive reload', themes)

    def timer():
        page.evaluate('handleTimerPrimaryAction();timerState.startTime=Date.now()-65000;saveUserData()')
        page.reload();page.wait_for_function('allBooks.length===39 && timerState.active')
        assert page.evaluate('timerState.active && !timerState.paused')
        page.evaluate('handleTimerPrimaryAction()')
        elapsed = page.evaluate('timerState.elapsedBeforePause')
        page.reload();page.wait_for_function('timerState.active && timerState.paused')
        assert page.evaluate('timerState.elapsedBeforePause') == elapsed
        page.locator('#timer-stop-btn').focus();page.keyboard.press('Enter')
        expect(page.locator('#stop-confirm-modal-content button').first).to_be_focused()
        page.keyboard.press('Escape');expect(page.locator('#timer-stop-btn')).to_be_focused()
        assert page.evaluate('timerState.active')
        page.evaluate('confirmStopReading()');total = page.evaluate('userData.totalSeconds')
        assert total>=65
        page.reload();page.wait_for_function('allBooks.length===39')
        assert page.evaluate('userData.totalSeconds')==total
        assert not page.evaluate('timerState.active')
    check('running and paused timers survive real reloads without double counting', timer)

    def search_and_covers():
        page.fill('#book-search', first['title'][:6])
        page.keyboard.press('ArrowDown')
        expect(page.locator('#search-suggestions [role="button"]').first).to_be_focused()
        page.keyboard.press('Enter')
        expect(page.locator('#search-suggestions')).to_be_hidden()
        expect(page.locator('#book-search')).to_be_focused()
        page.fill('#book-search','')
        assert page.locator('img:not([alt])').count()==0
        page.locator('.book-card img').first.evaluate('(img)=>img.src="Resources/Images/missing-cover.jpg"')
        page.wait_for_function('document.querySelector(".book-card img").src.endsWith("cover-placeholder.svg")')
        assert page.locator('.book-card img').first.evaluate('(img)=>img.onerror===null')
        assert page.locator('.book-card img').first.evaluate('(img)=>img.complete && img.naturalWidth>0')
        assert 'Fantasia' not in page.locator('#category-filters').text_content()
    check('search suggestions work by keyboard; missing covers use local fallback; alt text present', search_and_covers)

    def denied_storage():
        isolated = browser.new_context()
        isolated.route('**/*', route_files)
        isolated.add_init_script('Object.defineProperty(window,"localStorage",{get(){throw new DOMException("Denied","SecurityError")}})')
        q=isolated.new_page();local_errors=[];q.on('pageerror',lambda e:local_errors.append(str(e)))
        q.goto(URL);q.wait_for_function('allBooks.length===39')
        q.evaluate('setBokasafnTheme("green");toggleLike(1);handleTimerPrimaryAction()')
        assert not local_errors,local_errors
        expect(q.locator('body')).to_have_attribute('data-theme','green')
        assert q.evaluate('userData.liked.includes(1)')
        q.evaluate('confirmStopReading()')
        assert q.evaluate('timerState.active')
        isolated.close()
    check('denied localStorage keeps the app usable and warns instead of reporting false saves', denied_storage)

    def failed_catalog():
        isolated = browser.new_context()
        isolated.route('**/*', route_files)
        isolated.route('**/Resources/books.json',lambda route:route.fulfill(status=500,body='failed'))
        q=isolated.new_page();local_errors=[];q.on('pageerror',lambda error:local_errors.append(str(error)))
        q.goto(URL)
        expect(q.locator('#book-grid')).to_contain_text('Ekki tókst að hlaða bókunum.')
        assert not local_errors,local_errors
        isolated.close()
    check('failed catalog keeps its load-error message without crashing startup', failed_catalog)

    assert not errors, errors
    print('9 browser regression groups passed; no uncaught JavaScript errors',flush=True)
    browser.close()
