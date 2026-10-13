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
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    ctx=context(browser,viewport={'width':1280,'height':889})
    ctx.grant_permissions(['clipboard-read','clipboard-write'])
    page=new_page(ctx)
    def seed():
        page.evaluate(r'''() => {
          clearInterval(timerState.interval);timerState=emptyTimerState();
          const text='Þú, ég, æöðþ 😀 中文 " \\ \n \r \t </textarea><img src=x> \u2028\u2029';
          const date=getLocalYYYYMMDD(new Date());
          userData=normalizeUserData({version:15,read:[allBooks[0].id],liked:[allBooks[1].id],reviews:{[allBooks[0].id]:{rating:5,comment:text,date:'í gær'}},totalSeconds:7200,dailyProgress:{[date]:7200},minutesGoal:20,goalType:'weekly',personalGoals:[{id:1,text,completed:true}],completedDates:{[allBooks[0].id]:date},sessions:[{id:'session-one',date,seconds:7200}],challenges:[{id:'challenge-one',title:text,kind:'books',target:3,start:date,baseline:[allBooks[0].id],historyMode:null}],unresolved:{read:['Óþekkt eldri bók'],liked:[],reviews:{'Óþekkt':{rating:4,comment:text,date:'áður'}}}});
          timerState=emptyTimerState();timerState.active=true;timerState.paused=true;timerState.startTime=Date.now();timerState.elapsedBeforePause=12345;timerState.dailyMilliseconds[date]=12345;
          saveUserData();setBokasafnTheme('green');
          localStorage.setItem('library_v14',JSON.stringify({read:['Óþekkt eldri bók'],liked:[]}));
          localStorage.setItem('library_v15_recovery_original','unreadable original æöðþ');
          localStorage.setItem('library_import_backup_original','old backup 😀');
          localStorage.setItem('bokasafn-custom-preference','private preference');
          sessionStorage.setItem('bokasafn-session-preference','session preference');
          localStorage.setItem('unrelated-site','keep');sessionStorage.setItem('unrelated-session','keep');
          pendingImport=null;updateTimerUI();updateStatsUI();showPage('stats');
        }''');page.wait_for_timeout(350)
    def cancel_delete():
        seed()
        before=page.evaluate('({data:JSON.stringify(userData),local:JSON.stringify(userStorageSnapshot(localStorage)),session:JSON.stringify(userStorageSnapshot(sessionStorage)),timer:JSON.stringify(timerState)})')
        page.evaluate('confirmDeleteAllData()');assert page.evaluate('JSON.stringify(userData)')==before['data']
        page.get_by_role('button',name='Eyða öllum gögnum',exact=True).click();page.wait_for_timeout(350)
        assert 'ekki afturkallað' in page.locator('#feature-dialog-body').text_content()
        expect(page.get_by_role('button',name='Hætta við',exact=True)).to_be_focused()
        assert page.locator('#feature-dialog-body .destructive').evaluate('(n)=>getComputedStyle(n).backgroundColor')=='rgb(185, 28, 28)'
        page.get_by_role('button',name='Hætta við',exact=True).click();page.wait_for_timeout(350)
        after=page.evaluate('({data:JSON.stringify(userData),local:JSON.stringify(userStorageSnapshot(localStorage)),session:JSON.stringify(userStorageSnapshot(sessionStorage)),timer:JSON.stringify(timerState)})');assert after==before
        page.get_by_role('button',name='Eyða öllum gögnum',exact=True).click();page.wait_for_timeout(350);page.keyboard.press('Escape');page.wait_for_timeout(350);assert page.evaluate('JSON.stringify(userData)')==before['data']
    check('delete requires confirmation, focuses Cancel and both Cancel/Escape preserve every value',cancel_delete)
    saved={}
    def generate_copy():
        page.get_by_role('button',name='Búa til afritslínu',exact=True).click();page.wait_for_timeout(350)
        line=page.locator('#backup-line-output').input_value();assert not any(c in line for c in '\r\n\u2028\u2029');saved['line']=line
        saved['backup']=json.loads(page.evaluate('(line)=>decodeBackupLine(line)',line))
        assert saved['backup']['backupVersion']==2 and saved['backup']['data']['reviews']
        assert 'ekki dulkóðuð' in page.locator('#reading-insights').text_content()
        page.get_by_role('button',name='Velja alla línuna',exact=True).click();assert page.locator('#backup-line-output').evaluate('(n)=>n.selectionEnd-n.selectionStart')==len(line)
        page.get_by_role('button',name='Afrita línuna',exact=True).click();page.wait_for_timeout(150);assert page.evaluate('navigator.clipboard.readText()')==line
        assert 'Öll línan' in page.locator('#backup-line-copy-status').text_content()
        page.keyboard.press('Escape');page.wait_for_timeout(350)
        with page.expect_download() as result:page.get_by_role('button',name='Sækja JSON-afrit',exact=True).click()
        target=ARTIFACTS/'full-backup.json';result.value.save_as(target);saved['json']=target;backup=json.loads(target.read_text());assert backup['data']==saved['backup']['data'];assert backup['preferences']==saved['backup']['preferences'];assert backup['storage']==saved['backup']['storage']
    check('full one-line generation/select/native clipboard and JSON represent exactly the same data',generate_copy)
    def reset_all():
        page.evaluate('searchQuery="private";activeCategories=["✅ Lesið"];currentRating=5;document.getElementById("book-search").value="private";document.getElementById("personal-goal-input").value="unsaved private";document.getElementById("filter-min").value="100";setBookSort("pages-desc");pendingImport={private:"stale"}')
        page.get_by_role('button',name='Eyða öllum gögnum',exact=True).click();page.wait_for_timeout(350);page.locator('#feature-dialog-body .destructive').click();page.wait_for_timeout(350)
        assert page.evaluate('JSON.stringify(userData)===JSON.stringify(normalizeUserData({}))')
        assert page.evaluate('Object.keys(userStorageSnapshot(localStorage)).length')==0
        assert page.evaluate('Object.keys(userStorageSnapshot(sessionStorage)).length')==0
        assert page.evaluate('localStorage.getItem("unrelated-site")')=='keep';assert page.evaluate('sessionStorage.getItem("unrelated-session")')=='keep'
        assert page.evaluate('!timerState.active && timerState.elapsedBeforePause===0 && pendingImport===null && currentRating===0 && searchQuery==="" && activeCategories.length===0')
        assert page.locator('#main-timer-display').text_content()=='00:00:00'
        assert page.locator('#personal-goal-input').input_value()=='';assert page.locator('#book-sort').input_value()=='default';assert page.locator('#filter-min').input_value()==''
        assert page.evaluate('bokasafnThemePreference')=='system';assert page.locator('.book-card').count()==min(len(CATALOG),60)
        expect(page.locator('#library-page')).to_be_visible()
        page.reload();page.wait_for_function('window.featuresReady');assert page.evaluate('userData.read.length===0&&userData.totalSeconds===0&&!timerState.active&&Object.keys(userData.achievements).length===0&&userData.challenges.length===0')
        assert page.evaluate('localStorage.getItem("library_v14")') is None
    check('confirmed reset removes all namespaces, backups, active timer, drafts and filters without stale state or reload resurrection',reset_all)
    def restore_exact():
        page.evaluate('openTextImport()');page.wait_for_timeout(350)
        page.fill('#backup-line-input',saved['line']);page.get_by_role('button',name='Athuga afrit',exact=True).click();assert 'Afritið er gilt' in page.locator('#backup-line-status').text_content()
        page.get_by_role('button',name='Flytja inn',exact=True).click();page.wait_for_timeout(350);page.get_by_role('button',name='Skipta út gögnum',exact=True).click();page.get_by_role('button',name='Já, skipta út',exact=True).click();page.wait_for_timeout(350)
        assert page.evaluate('JSON.parse(JSON.stringify(userData))')==saved['backup']['data']
        assert page.evaluate('bokasafnThemePreference')==saved['backup']['preferences']['theme']
        assert page.evaluate('timerState.active && timerState.paused && timerState.elapsedBeforePause===12345')
        for key,value in saved['backup']['storage']['local'].items():assert page.evaluate('(key)=>localStorage.getItem(key)',key)==value,key
        for key,value in saved['backup']['storage']['session'].items():assert page.evaluate('(key)=>sessionStorage.getItem(key)',key)==value,key
        page.reload();page.wait_for_function('window.featuresReady');assert page.evaluate('JSON.parse(JSON.stringify(userData))')==saved['backup']['data']
    check('export/delete/import replacement restores every reading field, Unicode, preferences, recovery values and paused timer exactly',restore_exact)
    def validation_merge():
        page.evaluate('confirmStopReading();showPage("stats")');page.wait_for_timeout(350)
        page.evaluate('openTextImport()');page.wait_for_timeout(350)
        for bad in ['bad',saved['line'][:-20],saved['line'].replace(':1:',':99:',1),saved['line']+'\n',saved['line'][:-1]+'!']:
            page.fill('#backup-line-input',bad);page.get_by_role('button',name='Athuga afrit',exact=True).click();assert page.locator('#backup-line-import').is_disabled();assert page.locator('#backup-line-status').text_content()
        page.fill('#backup-line-input',saved['line']);page.get_by_role('button',name='Athuga afrit',exact=True).click();assert page.locator('#backup-line-import').is_enabled()
        page.fill('#backup-line-input','bad');assert page.locator('#backup-line-import').is_disabled();assert page.evaluate('pendingImport') is None
        page.keyboard.press('Escape');page.wait_for_timeout(350);page.evaluate('toggleRead(allBooks[2].id);setBokasafnTheme("dark");openTextImport()');page.wait_for_timeout(350)
        page.fill('#backup-line-input',saved['line']);page.get_by_role('button',name='Athuga afrit',exact=True).click();page.get_by_role('button',name='Flytja inn',exact=True).click();page.wait_for_timeout(350);page.get_by_role('button',name='Sameina örugglega',exact=True).click();page.wait_for_timeout(350)
        assert page.evaluate('userData.read.includes(allBooks[0].id)&&userData.read.includes(allBooks[2].id)');assert page.evaluate('bokasafnThemePreference')=='dark';assert page.evaluate('localStorage.getItem("bokasafn-theme")')=='dark';assert not page.evaluate('timerState.active')
        # Existing JSON path restores the same full envelope and session.
        page.evaluate('showPage("stats")');page.wait_for_timeout(350);page.set_input_files('#backup-file',saved['json']);page.wait_for_timeout(350);page.get_by_role('button',name='Skipta út gögnum',exact=True).click();page.get_by_role('button',name='Já, skipta út',exact=True).click();page.wait_for_timeout(350)
        assert page.evaluate('JSON.parse(JSON.stringify(userData))')==saved['backup']['data']
    check('corrupt/truncated/version/multiline errors, editing invalidates approval, safe merge and existing JSON replacement',validation_merge)
    def layouts_failures():
        page.evaluate('confirmStopReading();showPage("stats")');page.wait_for_timeout(350)
        for width in [320,390,1280]:
            page.set_viewport_size({'width':width,'height':889})
            for theme in ['light','dark','green','purple','orange']:
                page.evaluate('(theme)=>setBokasafnTheme(theme)',theme)
                for opener in ['openTextBackup()','openTextImport()','openDeleteAllConfirmation()']:
                    page.evaluate(opener);page.wait_for_timeout(350);inside_viewport(page,'#feature-modal-content');assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
                    first=page.locator('#feature-modal-content button').first;last=page.locator('#feature-modal-content button:enabled').last
                    last.focus();page.keyboard.press('Tab');assert page.locator('#feature-modal-content').evaluate('(n)=>n.contains(document.activeElement)')
                    page.keyboard.press('Escape');page.wait_for_timeout(350)
        seed();before=page.evaluate('JSON.stringify(userData)');page.evaluate('openDeleteAllConfirmation()');page.wait_for_timeout(350)
        page.evaluate('() => {window.nativeRemove=Storage.prototype.removeItem;Storage.prototype.removeItem=function(){throw new DOMException("denied","SecurityError")};}')
        page.locator('#feature-dialog-body .destructive').click();assert page.evaluate('JSON.stringify(userData)')==before;assert page.locator('#feature-modal-content [data-dialog-status]').text_content()
        page.evaluate('() => {Storage.prototype.removeItem=window.nativeRemove;}');page.keyboard.press('Escape');page.wait_for_timeout(350)
        page.evaluate('navigator.clipboard.writeText=()=>Promise.reject(Error("denied"));document.execCommand=()=>false;openTextBackup()');page.wait_for_timeout(350);page.get_by_role('button',name='Afrita línuna',exact=True).click();assert 'handvirkt' in page.locator('#backup-line-copy-status').text_content()
        page.keyboard.press('Escape')
    check('new dialogs at phone/tablet widths in all themes, keyboard Escape, denied deletion and clipboard fallback',layouts_failures)
    def large_and_running():
        other=context(browser,viewport={'width':1280,'height':889});other.grant_permissions(['clipboard-read','clipboard-write']);q=new_page(other)
        q.evaluate('(text)=>{userData.reviews[allBooks[0].id]={rating:4,comment:text.repeat(150000),date:"6.10.2026"};userData.personalGoals=[{id:1,text:"Æ".repeat(15000),completed:false}];openTextBackup();}', 'Þ😀\n"')
        q.wait_for_timeout(350)
        line=q.locator('#backup-line-output').input_value();assert len(line)>1000000;assert not '\n' in line
        q.get_by_role('button',name='Afrita línuna',exact=True).click();q.wait_for_timeout(150);assert q.evaluate('navigator.clipboard.readText()')==line
        assert q.evaluate('(line)=>parseBackupLine(line).data.personalGoals[0].text.length',line)==15000
        q.keyboard.press('Escape');q.wait_for_timeout(350)
        q.evaluate('openDeleteAllConfirmation()');q.wait_for_timeout(350);q.locator('#feature-dialog-body .destructive').click();q.wait_for_timeout(350)
        q.evaluate('openTextImport()');q.wait_for_timeout(350);q.fill('#backup-line-input',line);q.get_by_role('button',name='Athuga afrit',exact=True).click();q.get_by_role('button',name='Flytja inn',exact=True).click();q.wait_for_timeout(350);q.get_by_role('button',name='Skipta út gögnum',exact=True).click();q.get_by_role('button',name='Já, skipta út',exact=True).click();q.wait_for_timeout(350)
        assert q.evaluate('userData.personalGoals[0].text.length')==15000
        assert q.evaluate('userData.reviews[allBooks[0].id].comment')==q.evaluate('(line)=>parseBackupLine(line).data.reviews[allBooks[0].id].comment',line)
        q.evaluate('openDeleteAllConfirmation()');q.wait_for_timeout(350);q.locator('#feature-dialog-body .destructive').click();q.wait_for_timeout(350)
        q.evaluate('userData=normalizeUserData({});handleTimerPrimaryAction();timerState.startTime-=5000;window.runningLine=encodeBackupLine(createReadingBackup());openDeleteAllConfirmation()');q.wait_for_timeout(350);q.locator('#feature-dialog-body .destructive').click();q.wait_for_timeout(350)
        q.evaluate('openTextImport()');q.wait_for_timeout(350);q.fill('#backup-line-input',q.evaluate('window.runningLine'));q.get_by_role('button',name='Athuga afrit',exact=True).click();q.get_by_role('button',name='Flytja inn',exact=True).click();q.wait_for_timeout(350);q.get_by_role('button',name='Skipta út gögnum',exact=True).click();q.get_by_role('button',name='Já, skipta út',exact=True).click();q.wait_for_timeout(350)
        assert q.evaluate('timerState.active&&!timerState.paused&&timerState.elapsedBeforePause>=5000')
        q.reload();q.wait_for_function('window.featuresReady');assert q.evaluate('timerState.active&&!timerState.paused');q.evaluate('confirmStopReading()');assert q.evaluate('userData.totalSeconds>=5')
        other.close()
    check('large full-line clipboard without truncation and running timer restore/reload/save',large_and_running)
    def delayed_import_reset():
        page.evaluate('''() => {
          clearInterval(timerState.interval);timerState=emptyTimerState();
          const backup=createReadingBackup();
          window.finishDelayedFile=null;
          previewImport({files:[{text:()=>new Promise(resolve=>{window.finishDelayedFile=()=>resolve(JSON.stringify(backup));})}],value:''});
          openDeleteAllConfirmation();
        }''');page.wait_for_timeout(350);page.locator('#feature-dialog-body .destructive').click();page.wait_for_timeout(350);page.evaluate('finishDelayedFile()');page.wait_for_timeout(250)
        assert page.evaluate('pendingImport===null&&userData.read.length===0&&userData.totalSeconds===0')
        assert page.locator('#feature-modal').get_attribute('aria-hidden')=='true'
    check('delayed file reading cannot resurrect a pending import after complete reset',delayed_import_reset)
    def two_tab_reset():
        other=context(browser);first_page=new_page(other)
        first_page.evaluate('toggleRead(allBooks[0].id);handleTimerPrimaryAction();handleTimerPrimaryAction()')
        second_page=new_page(other);assert second_page.evaluate('userData.read.length')==1
        first_page.evaluate('openDeleteAllConfirmation()');first_page.wait_for_timeout(350);first_page.locator('#feature-dialog-body .destructive').click();first_page.wait_for_timeout(500)
        second_page.wait_for_function('window.featuresReady&&userData.read.length===0&&!timerState.active')
        second_page.evaluate('saveUserData()');assert first_page.evaluate('JSON.parse(localStorage.getItem("library_v15")).read.length')==0
        other.close()
    check('complete reset clears other open tabs and prevents stale-save resurrection',two_tab_reset)
    assert not ERRORS,ERRORS
    assert not FAILURES,FAILURES
    print(json.dumps({'groups_passed':COUNT,'uncaught_errors':ERRORS,'dependency_failures':FAILURES},indent=2))
    browser.close()
server.shutdown();server.server_close()
