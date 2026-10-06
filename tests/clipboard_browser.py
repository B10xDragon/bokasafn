"""Full-envelope clipboard regressions with real assets, including iOS selection failures.
Run: python tests/clipboard_browser.py. Chromium required; physical iOS is not emulated.
"""
from pathlib import Path
exec((Path(__file__).with_name('backups_browser.py')).read_text().split('with sync_playwright() as p:')[0])

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
    ctx=context(browser,permissions=['clipboard-read','clipboard-write'],viewport={'width':768,'height':1024},has_touch=True)
    page=new_page(ctx)
    def opened():
        page.evaluate('openTextBackup()');page.wait_for_timeout(350)
        line=page.evaluate('generatedBackupLine')
        assert line.startswith('BOKASAFN:1:') and '\n' not in line and '\r' not in line
        assert page.locator('#backup-line-output').input_value()==line
        return line
    def copy():
        page.get_by_role('button',name='Afrita línuna',exact=True).click()
        page.wait_for_timeout(200)
    def clipboard():return page.evaluate('navigator.clipboard.readText()')
    def native():
        line=opened()
        page.evaluate('document.getElementById("backup-line-output").setSelectionRange(50,80)')
        copy();assert clipboard()==line and clipboard()!=line.rsplit(':',1)[1]
        assert 'Öll línan' in page.locator('#backup-line-copy-status').text_content()
    check('canonical framing, exact display, native copy ignores partial selection and includes header',native)
    def canonical():
        line=opened();page.evaluate('document.getElementById("backup-line-output").value="payload-only"')
        copy();assert clipboard()==line and page.locator('#backup-line-output').input_value()==line
    check('copy takes canonical snapshot even if DOM value differs',canonical)
    def manual():
        line=opened()
        page.locator('#backup-line-output').focus();page.evaluate('document.getElementById("backup-line-output").setSelectionRange(60,90)')
        page.keyboard.press('Control+c');assert clipboard()==line
        page.evaluate('''() => {window.originalSelect=HTMLTextAreaElement.prototype.select;
            HTMLTextAreaElement.prototype.select=function(){this.setSelectionRange(50,this.value.length)};}''')
        page.get_by_role('button',name='Velja alla línuna',exact=True).click()
        assert page.locator('#backup-line-output').evaluate('(n)=>n.selectionStart===0&&n.selectionEnd===n.value.length')
        page.keyboard.press('Control+c');assert clipboard()==line
    check('manual partial copy and select-all override preserve complete envelope',manual)
    def fallback():
        line=opened()
        page.evaluate('window.nativeClipboard=navigator.clipboard;Object.defineProperty(navigator,"clipboard",{configurable:true,value:undefined})')
        copy();assert page.evaluate('nativeClipboard.readText()')==line
        assert 'Öll línan' in page.locator('#backup-line-copy-status').text_content()
        assert page.locator('#feature-dialog-body textarea').count()==1
        page.evaluate('Object.defineProperty(navigator,"clipboard",{configurable:true,value:nativeClipboard})')
    check('unavailable clipboard API falls back despite simulated Safari partial selection',fallback)
    def rejected():
        line=opened();page.evaluate('() => {window.originalWrite=navigator.clipboard.writeText.bind(navigator.clipboard);navigator.clipboard.writeText=()=>Promise.reject(Error("denied"));}')
        copy();assert clipboard()==line
        assert 'Öll línan' in page.locator('#backup-line-copy-status').text_content()
    check('clipboard rejection automatically falls back and copies exact string',rejected)
    def ios():
        line=opened()
        page.evaluate('''() => {window.originalPlatform=navigator.platform;window.originalTouchPoints=navigator.maxTouchPoints;Object.defineProperty(navigator,'platform',{configurable:true,value:'MacIntel'});
            Object.defineProperty(navigator,'maxTouchPoints',{configurable:true,value:5});
            window.writeCalls=0;navigator.clipboard.writeText=()=>{writeCalls++;return Promise.reject(Error('denied'))};}''')
        copy();assert clipboard()==line and page.evaluate('writeCalls')==0
        assert 'Öll línan' in page.locator('#backup-line-copy-status').text_content()
    check('iPad desktop user agent path copies synchronously before rejected permission promise',ios)
    def failures():
        opened();page.evaluate('window.originalExec=document.execCommand.bind(document);document.execCommand=()=>true')
        copy();assert 'tókst ekki' in page.locator('#backup-line-copy-status').text_content()
        page.evaluate('document.execCommand=()=>false');copy()
        assert 'tókst ekki' in page.locator('#backup-line-copy-status').text_content()
        page.evaluate('() => {document.execCommand=originalExec;navigator.clipboard.writeText=originalWrite;Object.defineProperty(navigator,"platform",{configurable:true,value:originalPlatform});Object.defineProperty(navigator,"maxTouchPoints",{configurable:true,value:originalTouchPoints});}')
    check('false success and denied copy do not report success; temporary buffers removed',failures)
    def roundtrip():
        page.evaluate('''userData.personalGoals.push({id:1,text:'Íslenska Þ æ ö 🐉 "quoted" \\n newline \\u2028 separator',completed:false});saveUserData();''')
        line=opened();copy();assert clipboard()==line
        expected=page.evaluate('(line)=>parseBackupLine(line).data',line)
        page.evaluate('openDeleteAllConfirmation()');page.wait_for_timeout(350)
        page.locator('#feature-dialog-body .destructive').click();page.wait_for_timeout(350)
        assert page.evaluate('generatedBackupLine')==''
        page.evaluate('openTextImport()');page.wait_for_timeout(350)
        page.locator('#backup-line-input').focus();page.keyboard.press('Control+v')
        assert page.locator('#backup-line-input').input_value()==line
        page.get_by_role('button',name='Athuga afrit',exact=True).click()
        assert 'gilt' in page.locator('#backup-line-status').text_content()
        page.get_by_role('button',name='Flytja inn',exact=True).click();page.wait_for_timeout(350)
        page.get_by_role('button',name='Skipta út gögnum',exact=True).click()
        page.get_by_role('button',name='Já, skipta út',exact=True).click();page.wait_for_timeout(350)
        assert page.evaluate('JSON.parse(JSON.stringify(userData))')==expected
    check('real clipboard copy/paste validates, delete/import exactly restores Unicode reading data',roundtrip)
    def large():
        page.evaluate('localStorage.setItem("bokasafn-large-clipboard", "Þæö😀\\\"".repeat(150000))')
        line=opened();assert len(line)>1_000_000
        copy();assert clipboard()==line
        assert page.evaluate('(line)=>parseBackupLine(line).raw.storage.local["bokasafn-large-clipboard"]===localStorage.getItem("bokasafn-large-clipboard")',line)
        page.evaluate('Object.defineProperty(navigator,"clipboard",{configurable:true,value:undefined})')
        copy();assert page.evaluate('nativeClipboard.readText()')==line
        page.locator('#backup-line-output').focus();page.evaluate('document.getElementById("backup-line-output").setSelectionRange(1000,2000)')
        page.keyboard.press('Control+c');assert page.evaluate('nativeClipboard.readText()')==line
    check('large Unicode backups use full native, fallback and partial manual copies without truncation',large)
    assert not ERRORS,ERRORS
    assert not FAILURES,FAILURES
    ctx.close();browser.close()
    print(f'{COUNT} clipboard browser groups passed; real CDN dependencies: {len(DEPENDENCIES)}')
server.shutdown()
