"""Rendered form and simulated documented Formspree contract. No email delivery claim."""
from pathlib import Path
exec(Path(__file__).with_name('live_browser.py').read_text().split('with sync_playwright() as p:')[0])
ENDPOINT='https://formspree.io/f/testform123';SENT=[];MODE='success'
def provider(route):
 global MODE
 SENT.append(json.loads(route.request.post_data));mode=MODE
 if mode=='network':route.abort();return
 if mode=='slow':import time;time.sleep(.4)
 code={'error':500,'rate':429}.get(mode,200)
 route.fulfill(status=code,content_type='application/json',body=json.dumps({'errors':[{'message':'error'}]} if code!=200 else {'ok':True} if mode=='unconfirmed' else {'next':'https://formspree.io/thanks'}))
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium');ctx=context(browser,viewport={'width':390,'height':844},has_touch=True,is_mobile=True);ctx.route(ENDPOINT,provider);page=new_page(ctx)
 def open_form():page.evaluate('openRecommendModal()');page.wait_for_timeout(100)
 def activate():page.evaluate('BOKASAFN_SUGGESTIONS={enabled:true,endpoint:"'+ENDPOINT+'"};syncSuggestionAvailability()')
 def fill():
  page.fill('#rec-title','Hermiskaði');page.fill('#rec-author','Suzanne Collins');page.fill('#rec-series','Hungurleikarnir');page.fill('#rec-ideas','Góð bók. Þ æ ö');page.fill('#rec-url','https://www.forlagid.is/vara/hermiskadi/')
 def pending():
  open_form();expect(page.locator('#suggestion-submit')).to_be_disabled();assert 'bíður virkjunar' in page.locator('#suggestion-status').inner_text();expect(page.locator('#rec-title')).to_be_focused()
  page.fill('#rec-title','Drög');page.keyboard.press('Escape');open_form();assert page.input_value('#rec-title')=='Drög';assert not SENT
 check('pending activation cannot claim success or make a request; dialog keeps drafts',pending)
 def required():
  activate();page.fill('#rec-title','');page.locator('#suggestion-submit').click();expect(page.locator('#rec-title')).to_have_attribute('aria-invalid','true');assert 'bókatitil' in page.locator('#suggestion-status').inner_text();page.fill('#rec-title','Hermiskaði');page.locator('#suggestion-submit').click();expect(page.locator('#rec-author')).to_be_focused();assert not SENT
 check('required title and author use Icelandic validation and keyboard focus',required)
 def invalid():
  fill();page.fill('#rec-url','https://forlagid.is.evil.invalid/vara/test');page.locator('#suggestion-submit').click();expect(page.locator('#rec-url')).to_have_attribute('aria-invalid','true');assert not SENT
  page.fill('#rec-url','https://www.forlagid.is/vara/hermiskadi/');page.evaluate('document.getElementById("rec-website").value="bot"');page.evaluate('submitRecommendation()');assert not SENT;page.evaluate('document.getElementById("rec-website").value=""')
 check('invalid and deceptive URLs and honeypot submissions never leave the page',invalid)
 def success():
  fill();page.fill('#rec-title','<script>window.injected=true</script>');page.locator('#suggestion-submit').click();expect(page.locator('#suggestion-status')).to_contain_text('móttekin');assert len(SENT)==1
  assert SENT[-1]['subject']=='Bókasafn — Ný bókatillaga: <script>window.injected=true</script>';assert SENT[-1]['Höfundur']=='Suzanne Collins';assert SENT[-1]['_gotcha']=='';assert not page.evaluate('Boolean(window.injected)');assert page.input_value('#rec-title').startswith('<script>');assert page.evaluate('document.querySelectorAll("#suggestion-status script").length')==0
 check('confirmed provider acceptance alone shows success and script text stays inert',success)
 def duplicate():
  global MODE
  MODE='slow';fill();before=len(SENT);snapshot=page.evaluate('()=>{submitRecommendation();submitRecommendation();return {busy:suggestionSending,disabled:document.getElementById("suggestion-submit").disabled,aria:document.getElementById("suggestion-form").getAttribute("aria-busy")}}');assert snapshot=={'busy':True,'disabled':True,'aria':'true'};expect(page.locator('#suggestion-status')).to_contain_text('móttekin');assert len(SENT)==before+1;MODE='success'
 check('in-flight double submits produce one request and accessible busy feedback',duplicate)
 def failures():
  global MODE
  for mode in ['error','rate','network','unconfirmed']:
   MODE=mode;fill();page.locator('#suggestion-submit').click();expect(page.locator('#suggestion-status')).to_have_attribute('role','alert');assert 'móttekin' not in page.locator('#suggestion-status').inner_text();assert page.input_value('#rec-title')=='Hermiskaði';expect(page.locator('#suggestion-submit')).to_be_enabled()
  MODE='success';page.locator('#rec-author').focus();page.keyboard.press('Enter');expect(page.locator('#suggestion-status')).to_contain_text('móttekin')
 check('500, 429, network and unconfirmed responses keep text and permit keyboard retry',failures)
 def layouts():
  for width in [320,390,768,1440]:
   page.set_viewport_size({'width':width,'height':800})
   for theme in ['light','dark','green','purple','orange']:
    page.evaluate('(t)=>setBokasafnTheme(t)',theme);assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');assert page.evaluate('activeDialog.content.scrollWidth<=activeDialog.content.clientWidth+1');page.locator('#suggestion-submit').scroll_into_view_if_needed();assert page.locator('#suggestion-submit').bounding_box()['height']>=44
  page.set_viewport_size({'width':320,'height':740});page.wait_for_timeout(120);page.locator('#suggestion-submit').scroll_into_view_if_needed();bounds=page.locator('#suggestion-submit').bounding_box();assert bounds['y']>=0 and bounds['y']+bounds['height']<=740;page.screenshot(path=str(ARTIFACTS/'suggestion-form-320.png'));page.keyboard.press('Escape');expect(page.locator('#recommend-modal')).to_be_hidden()
 check('touch mobile tablet desktop and all themes fit; Escape closes the dialog',layouts)
 assert not ERRORS,ERRORS
 (ARTIFACTS/'suggestion-results.json').write_text(json.dumps({'groupsPassed':COUNT,'requestsIntercepted':len(SENT),'liveEmailsSent':0,'deliveryVerified':False,'mode':'simulated Formspree HTTP acceptance/error contract'},indent=2));browser.close();server.shutdown();print(str(COUNT)+' suggestion browser groups passed')
