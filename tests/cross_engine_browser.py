"""Cross-engine smoke tests. WebKit on Linux is not Safari/iOS device testing."""
import argparse
from pathlib import Path
exec(Path(__file__).with_name('live_browser.py').read_text().split('with sync_playwright() as p:')[0])
parser=argparse.ArgumentParser();parser.add_argument('--engines',nargs='+',choices=['firefox','webkit'],default=['firefox','webkit']);args=parser.parse_args();VERSIONS={}
with sync_playwright() as p:
 for engine in args.engines:
  browser=getattr(p,engine).launch();VERSIONS[engine]=browser.version
  ctx=context(browser,viewport={'width':390,'height':844},reduced_motion='reduce');q=new_page(ctx);q.wait_for_function('window.browseReady')
  def layouts():
   for width in [320,390,768,1180,1440,2560]:
    q.set_viewport_size({'width':width,'height':900})
    for theme in ['light','dark','green','purple','orange']:
     q.evaluate('(t)=>{setBokasafnTheme(t);showPage("library")}',theme)
     assert q.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(engine,width,theme)
     for selector in ['#book-search','#nav-library','#nav-series','#nav-authors','#nav-stats','#nav-appearance']:inside_viewport(q,selector)
     q.evaluate('showPage("stats")');assert q.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    q.evaluate('openBrowse("series","harry-potter")');assert q.locator('[data-browse-book]').count()==7
    q.evaluate('openBrowse("author","arnaldur-indridason")');assert q.locator('[data-browse-book]').count()>0
   q.evaluate('showPage("library");setBokasafnTheme("light")');q.set_viewport_size({'width':390,'height':844})
  check(engine+': six widths, five themes, all navigation and browsing pages',layouts)
  def interactions():
   summary=q.locator('#recommendations-panel summary');assert not q.evaluate('document.getElementById("recommendations-panel").open')
   summary.focus();q.keyboard.press('Enter');expect(summary).to_have_attribute('aria-expanded','true');expect(q.locator('#personal-recommendations button')).to_have_count(6)
   q.locator('#personal-recommendations button').first.click();expect(q.locator('#book-dialog-title')).to_be_visible();q.keyboard.press('Tab');assert q.evaluate('activeDialog.content.contains(document.activeElement)');q.keyboard.press('Escape')
   summary.focus();q.keyboard.press('Space');expect(summary).to_have_attribute('aria-expanded','false')
   q.fill('#book-search','ERAGON');assert q.locator('[data-result-type="series"]').count()==1;q.locator('[data-result-type="series"]').click();assert 'series=eragon' in q.url
   q.reload();q.wait_for_function('window.browseReady');assert 'Eragon' in q.locator('#browse-title').text_content()
   q.evaluate('showPage("library")');q.fill('#book-search','');q.locator('#advanced-filters summary').click();q.select_option('#filter-state','unread');assert q.locator('.book-card').count()>0
   for action in ['openRandomPicker()','openTextBackup()','openTextImport()','openDeleteAllConfirmation()','openRecommendModal()']:
    q.evaluate(action);q.wait_for_function('activeDialog!==null');assert q.evaluate('activeDialog.content.scrollWidth<=activeDialog.content.clientWidth+1');q.keyboard.press('Escape')
   q.evaluate('openRandomPicker();closeModal("feature-modal","feature-modal-content");openTextBackup()');q.wait_for_timeout(350);line=q.input_value('#backup-line-output');q.get_by_role('button',name='Velja alla línuna',exact=True).click();assert q.evaluate('document.getElementById("backup-line-output").selectionEnd')==len(line)
   assert q.evaluate('(line)=>JSON.stringify(parseBackupLine(line).data)===JSON.stringify(parseBackup(JSON.stringify(createReadingBackup())).data)',line)
   q.keyboard.press('Escape');q.reload();q.wait_for_function('window.browseReady');assert not q.evaluate('document.getElementById("recommendations-panel").open')
  check(engine+': keyboard disclosure, details, search, URLs, filters, dialogs and portable backup selection/import',interactions)
  browser.close()
 assert not ERRORS,ERRORS
 (ARTIFACTS/'cross-engine-results.json').write_text(json.dumps({'versions':VERSIONS,'groupsPassed':COUNT,'uncaughtErrors':ERRORS,'limitations':['Headless Firefox and Linux WebKit engine; no native Safari, physical iOS, iPadOS, Android or Samsung Internet test.']},indent=2));server.shutdown();print(str(COUNT)+' cross-engine browser groups passed')
