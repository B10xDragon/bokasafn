#!/usr/bin/env python3
"""Build-time Forlagið collector. Requires beautifulsoup4 and Pillow; no runtime dependencies.
Caches fetched pages/covers outside the repository and starts at most one request/second.
Run with --cache /path/to/cache. Does not change the deployed catalog; build separately.
"""
import argparse, hashlib, io, json, re, subprocess, time, threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
BASE='https://www.forlagid.is/'
# Complete teenage category; bounded complementary samples from larger categories.
SEEDS=[
 ('barna-og-unglingabaekur/13-ara-og-eldri',None),
 ('barna-og-unglingabaekur/6-12-ara',6),
 ('barna-og-unglingabaekur/myndasogur-born-unglingar',3),
 ('barna-og-unglingabaekur/fraedi-og-handbaekur',None),
 ('skaldverk/islenskar-skaldsogur',4),
 ('skaldverk/klassisk-verk',8),
 ('skaldverk/visindaskaldskapur',None),
 ('skaldverk/spennusogur',4),
 ('skaldverk/thyddar-skaldsogur',4),
]
from catalog_categories import normalize_categories
from catalog_keys import title_key
from catalog_scope import is_activity_title
def source_url(url):
 parsed=urlparse(url)
 if parsed.scheme!='https' or parsed.hostname not in {'www.forlagid.is','forlagid.is'}:raise ValueError('Non-Forlagið URL')
 return url
def write_json(path,value):
 temp=path.with_suffix(path.suffix+'.tmp')
 temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
 temp.replace(path)

class Collector:
 def __init__(self,cache):
  self.cache=cache;cache.mkdir(parents=True,exist_ok=True);self.last=0;self.network=0;self.rate_lock=threading.Lock()
 def fetch(self,url,binary=False):
  source_url(url);path=self.cache/(hashlib.sha256(url.encode()).hexdigest()+('.bin' if binary else '.html'))
  if path.exists():return path.read_bytes()
  for attempt in range(3):
   with self.rate_lock:
    time.sleep(max(0,1.0-(time.monotonic()-self.last)));self.last=time.monotonic()
    self.network+=1
   r=subprocess.run(['curl','--silent','--show-error','--fail','--location','--proto','=https','--proto-redir','=https','--write-out','\n__FORLAGID_EFFECTIVE_URL__%{url_effective}','--max-time','45','--user-agent','Bokasafn-catalog-maintenance/1.0 (https://github.com/B10xDragon/bokasafn)',url],capture_output=True)
   if r.returncode==0 and r.stdout:
    body,effective=r.stdout.rsplit(b'\n__FORLAGID_EFFECTIVE_URL__',1)
    source_url(effective.decode().strip())
    if body:path.write_bytes(body);return body
   time.sleep(2*(attempt+1))
  raise ValueError('Source request failed: '+url)
 def discover(self):
  candidates={};report=[]
  for category,limit in SEEDS:
   url=BASE+'voruflokkur/'+category+'/'
   soup=BeautifulSoup(self.fetch(url),'html.parser');grid=soup.select_one('.jet-listing-grid__items')
   if grid is None:report.append({'url':url,'error':'No category grid'});continue
   pages=int(grid.get('data-pages','1'));end=min(pages,limit) if limit else pages;seen=set()
   for n in range(1,end+1):
    pageurl=url if n==1 else url+f'page/{n}/'
    if n>1:soup=BeautifulSoup(self.fetch(pageurl),'html.parser');grid=soup.select_one('.jet-listing-grid__items')
    cards=grid.select('.jet-listing-grid__item') if grid else []
    current=[]
    for card in cards:
     a=card.select_one('.jet-engine-listing-overlay-wrap[data-url]');title=card.select_one('.jet-listing-dynamic-field__content')
     if not a or not title:continue
     itemurl=source_url(a['data-url']);current.append(itemurl)
     item=candidates.setdefault(itemurl,{'url':itemurl,'listingTitle':title.get_text(' ',strip=True),'discoveredIn':[]})
     if pageurl not in item['discoveredIn']:item['discoveredIn'].append(pageurl)
    if n>1 and current and set(current).issubset(seen):raise ValueError('Repeated pagination page: '+pageurl)
    seen.update(current)
   report.append({'url':url,'availablePages':pages,'visitedPages':end,'listings':len(seen)})
   print('DISCOVER',category,len(seen),'unique total',len(candidates),flush=True)
  write_json(self.cache/'discovery.json',{'categories':report,'candidates':list(candidates.values())})
  return candidates
 def parse(self,item):
  raw=self.fetch(item['url']);soup=BeautifulSoup(raw,'html.parser');root=soup.select_one('[data-elementor-type="product"]')
  if not root:raise ValueError('Missing product template')
  canonical=soup.select_one('link[rel=canonical]')
  if not canonical or '/vara/' not in urlparse(source_url(canonical.get('href',''))).path:raise ValueError('Missing Forlagið product canonical URL')
  title=root.select_one('.product_title');title=title.get_text(' ',strip=True) if title else ''
  if not title:raise ValueError('Missing title')
  authors=[];translators=[]
  # Main metadata only: never mistake a related-book author for this book's author.
  for a in root.select('a[href*="/hofundar/"]'):
   if a.find_parent(class_='jet-listing-grid__item'):continue
   name=a.get_text(' ',strip=True)
   if name.startswith(('Þýðandi:','Þýðendur:')):translators.append(name);continue
   if name and name not in authors:authors.append(name)
  if not authors:raise ValueError('Missing author')
  cats=[]
  for a in root.select('a[href*="/voruflokkur/"]'):
   if a.find_parent(class_='jet-listing-grid__item'):continue
   cat=a.get_text(' ',strip=True)
   if cat and cat not in cats:cats.append(cat)
  if any(x in ' '.join(cats).casefold() for x in ['books in','books and maps','bücher','livres','landakort']):raise ValueError('Foreign-language/map listing outside scope')
  if is_activity_title(title):raise ValueError('Activity/stationery item outside reading scope')
  classes=' '.join(soup.body.get('class',[]));match=re.search(r'\bpostid-(\d+)\b',classes)
  if not match:raise ValueError('Missing stable source product ID')
  pid=int(match.group(1));edition=None
  for row in root.select('table.vartable tbody tr'):
   label=row.select_one('.optionscol');label=label.get_text(' ',strip=True) if label else ''
   if label not in ['Innbundin','Kilja','Bók','Heft','Harðspjalda','Pappakápa']:continue
   pages=row.select_one('.pagenumbercol');year=row.select_one('.yearcol')
   p=pages.get_text(strip=True) if pages else '';y=year.get_text(strip=True) if year else ''
   choice={'format':label,'pages':int(p) if re.fullmatch(r'[1-9]\d{0,4}',p) else None,'year':int(y) if re.fullmatch(r'(?:18|19|20)\d{2}',y) else None}
   if edition is None or label=='Innbundin':edition=choice
   if label=='Innbundin':break
  desc=''
  for field in root.select('.jet-listing-dynamic-field__content'):
   if field.find_parent(class_='jet-listing-grid__item'):continue
   text=field.get_text(' ',strip=True)
   if len(text)>len(desc):desc=text
  if len(desc)<35:raise ValueError('No reliable description')
  image=None
  for img in root.select('.elementor-widget-image img,.woocommerce-product-gallery img'):
   if img.find_parent(class_='jet-listing-grid__item'):continue
   url=img.get('src','')
   if '/wp-content/uploads/' in url and 'logo' not in url.casefold():image=img;break
  if not image:raise ValueError('No book-specific cover')
  cover=image['src'];sizes=[]
  for part in image.get('srcset','').split(','):
   m=re.match(r'\s*(\S+)\s+(\d+)w',part)
   if m:sizes.append((int(m.group(2)),m.group(1)))
  suitable=[x for x in sizes if 350<=x[0]<=700]
  if suitable:cover=min(suitable)[1]
  source_url(cover)
  normalized=normalize_categories(cats,desc)
  if not normalized:raise ValueError('Unmapped book category')
  language='is' if any(c in cats for c in ['Íslenskar skáldsögur','Þýddar skáldsögur']) or translators else None
  language_basis='Icelandic fiction category' if 'Íslenskar skáldsögur' in cats else 'Icelandic translation category/translator credit' if language else 'Icelandic title and presentation; edition language not explicitly stated'
  return {**item,'id':1000000+pid,'sourceProductId':pid,'title':title,'author':', '.join(authors),'sourceCategories':cats,'categories':normalized,'edition':edition or {'format':None,'pages':None,'year':None},'sourceDescription':desc,'coverSourceURL':cover,'language':language,'languageEvidence':language_basis,'translators':translators,'sourceHTMLSHA256':hashlib.sha256(raw).hexdigest(),'verifiedAt':datetime.now(timezone.utc).date().isoformat()}
 def collect(self,candidates):
  originals=json.loads((ROOT/'tests/fixtures/original-39-books.json').read_text());keys={title_key(b['title']):b for b in originals}
  path=self.cache/'records.json';records=json.loads(path.read_text()) if path.exists() else []
  rejected_path=self.cache/'rejected.json';rejected=json.loads(rejected_path.read_text()) if rejected_path.exists() else []
  done={r['url'] for r in records+rejected};keys.update({title_key(r['title']):r for r in records})
  pending=[]
  for item in candidates.values():
   if item['url'] in done:continue
   key=title_key(item['listingTitle'])
   if key in keys:rejected.append({**item,'reason':'Duplicate of original/existing title','duplicateOf':keys[key]['id']})
   else:pending.append(item)
  def load(item):
   try:
    r=self.parse(item);cover_raw=self.fetch(r['coverSourceURL'],True);r['coverSourceSHA256']=hashlib.sha256(cover_raw).hexdigest()
    image=Image.open(io.BytesIO(cover_raw));image.load()
    if image.width<80 or image.height<100:raise ValueError('Cover too small/not reliable')
    image.thumbnail((360,540));out=io.BytesIO();image.convert('RGB').save(out,format='WEBP',quality=86,method=6)
    return item,r,out.getvalue(),None
   except Exception as error:return item,None,None,str(error)
  # Two requests may be in flight, but all starts share the one/second limit.
  # map preserves discovery order, making edition selection reproducible.
  with ThreadPoolExecutor(max_workers=2) as pool:
   for index,(item,r,cover,error) in enumerate(pool.map(load,pending)):
    if error:rejected.append({**item,'reason':error})
    else:
     key=title_key(r['title'])
     if key in keys:
      other=keys[key];same=other['author'].casefold()==r['author'].casefold()
      rejected.append({**item,'reason':'Duplicate book/edition' if same else 'Ambiguous same title with different author','duplicateOf':other['id']})
     else:
      cover_path=ROOT/'Resources/Images'/f"forlagid-{r['sourceProductId']}.webp";cover_temp=cover_path.with_suffix('.webp.tmp');cover_temp.write_bytes(cover);cover_temp.replace(cover_path)
      r['cover']=str(cover_path.relative_to(ROOT));r['coverSHA256']=hashlib.sha256(cover).hexdigest()
      records.append(r);keys[key]=r
      write_json(path,records)
    write_json(rejected_path,rejected)
    if index%10==0:print('COLLECT',index+1,'/',len(pending),'accepted',len(records),'rejected',len(rejected),'requests',self.network,flush=True)
  print('DONE',len(records),'accepted',len(rejected),'rejected',flush=True)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--cache',type=Path,default=Path('/tmp/bokasafn-forlagid-cache'));parser.add_argument('--discover-only',action='store_true');args=parser.parse_args();c=Collector(args.cache)
 candidates=c.discover()
 if not args.discover_only:c.collect(candidates)
