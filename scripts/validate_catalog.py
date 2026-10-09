#!/usr/bin/env python3
"""Validate static catalog and its reviewed Forlagið/identity evidence. No network required.
Likely matches are warnings unless the audit records their resolution.
"""
import argparse, collections, difflib, hashlib, json, re, sys
from pathlib import Path
from urllib.parse import urlparse
from catalog_keys import title_key, author_key, likely_duplicate
ROOT=Path(__file__).resolve().parents[1]
ALLOWED={'Grín','Rómantík','Þýddar bækur','Spenna','Ævintýri','Fantasía','Hrollvekja','Ráðgáta','Ungmenni','Glæpir','Klassík','Ævisögur','Vísindaskáldsaga','Skáldsögur','Skáldverk','Fræðibækur','Ljóð'}
def forlagid_product(url):
 try:
  p=urlparse(url);return p.scheme=='https' and p.hostname in {'forlagid.is','www.forlagid.is'} and p.path.startswith('/vara/') and not p.username
 except (TypeError,ValueError):return False

def inspect_books(books,root=ROOT,sources=None,audit=None,identities=None):
 errors=[];warnings=[];ids=set();keys={};byid={};sources=sources or {};audit=audit or {};identities=identities or {}
 def check(ok,label,message):
  if not ok:errors.append(f'{label}: {message}')
 for b in books:
  if not isinstance(b,dict):errors.append('Catalog entry must be an object');continue
  bid=b.get('id');label=f'{bid}: {b.get("title", "?")}'
  check(type(bid) is int and bid>=1,label,'invalid ID');check(bid not in ids,label,'duplicate ID');ids.add(bid);byid[bid]=b
  for field in ['title','author','description','cover']:
   check(isinstance(b.get(field),str) and bool(b[field].strip()),label,'missing '+field)
  if not isinstance(b.get('title'),str) or not isinstance(b.get('author'),str):continue
  key=(title_key(b['title']),author_key(b['author']))
  check(key not in keys,label,'duplicate title/author of '+str(keys.get(key)));keys[key]=bid
  cats=b.get('categories');check(isinstance(cats,list) and bool(cats) and all(isinstance(c,str) for c in cats) and len(set(cats))==len(cats) and set(cats)<=ALLOWED,label,'invalid or excluded category')
  pages=b.get('pages');check('pages' in b and (pages is None or type(pages) is int and 0<pages<=20000),label,'invalid/missing page count (use null if unknown)')
  year=b.get('publicationYear');check(year is None or type(year) is int and 1800<=year<=2099,label,'invalid publication year')
  cover=b.get('cover','');coverpath=root/cover if isinstance(cover,str) else root/'__missing__'
  check(isinstance(cover,str) and cover.startswith('Resources/Images/') and '..' not in Path(cover).parts and coverpath.is_file(),label,'broken/unsafe cover path')
  check(forlagid_product(b.get('sourceURL')),label,'missing/invalid Forlagið source')
  r=sources.get(bid)
  if sources:
   check(r is not None,label,'missing source evidence')
   if r:
    check(r.get('url')==b.get('sourceURL'),label,'source URL mismatch')
    check(r.get('catalogTitle',r.get('title'))==b.get('title') and r.get('catalogAuthor',r.get('author'))==b.get('author'),label,'source title/author mismatch')
    imageurl=urlparse(r.get('coverSourceURL',''));check(imageurl.scheme=='https' and imageurl.hostname in {'www.forlagid.is','forlagid.is'} and imageurl.path.startswith('/wp-content/uploads/'),label,'invalid cover source')
    check(r.get('edition',{}).get('pages')==pages,label,'source page count mismatch')
    check(r.get('edition',{}).get('year')==year,label,'source publication year mismatch')
    if coverpath.is_file():check(hashlib.sha256(coverpath.read_bytes()).hexdigest()==r.get('coverSHA256'),label,'cover hash mismatch')
    for field in ['sourceHTMLSHA256','coverSHA256']:
     check(bool(re.fullmatch('[0-9a-f]{64}',r.get(field,''))),label,'invalid evidence hash '+field)
    sourcecats=r.get('sourceCategories',[])
    check(not any(c.startswith('Myndasögur') for c in sourcecats),label,'comic source category')
    if ('6-12 ára' in sourcecats or '0-5 ára' in sourcecats) and '13 ára og eldri' not in sourcecats:
     check(audit.get(bid,{}).get('audienceException') is not None,label,'younger-reader source requires reviewed exception')
    if 'Léttlestrarbækur' in sourcecats:warnings.append(label+': easy-reader source requires suitability review')
    if '6-12 ára' in sourcecats and '13 ára og eldri' in sourcecats and not audit.get(bid,{}).get('audienceException'):
     warnings.append(label+': mixed younger/teen audience requires a documented suitability review')
  if audit:check(audit.get(bid,{}).get('status')=='retained',label,'not approved in catalog audit')
  if re.search(r'myndas[öa]g|syrpa|kidd[ai] klauf|dagbók kidda|leyndarmál lindu|skúli skelfir|graphic novel|manga|lærum stafina|litabók|þrautabók',b['title']+' '+b.get('description',''),re.I):warnings.append(label+': potential comic/younger-reader format')
 for i,a in enumerate(books):
  if not isinstance(a,dict):continue
  for b in books[i+1:]:
   if isinstance(b,dict) and likely_duplicate(a,b):
    pair=sorted([a['id'],b['id']]);resolved=identities.get('distinctPairs',[])
    if pair not in resolved:warnings.append(f'Likely duplicate requiring review: {pair}: {a["title"]} / {b["title"]}')
 aliases=identities.get('aliases',{});archived={b['id'] for b in identities.get('archived',[])}
 for old,target in aliases.items():
  check(str(target) not in aliases,old,'alias chain/cycle');check(int(old) not in ids,old,'merged ID still in catalog');check(target in ids or target in archived,old,'alias target missing')
 check(not(ids & archived),'identities','archived ID reused in live catalog')
 return {'books':len(books),'errors':errors,'warnings':warnings,'categories':dict(sorted(collections.Counter(c for b in books for c in b.get('categories',[])).items()))}

def validate(root=ROOT):
 books=json.loads((root/'Resources/books.json').read_text())
 source_list=json.loads((root/'Resources/catalog-sources.json').read_text());sources={r['id']:r for r in source_list}
 audit=json.loads((root/'Resources/catalog-audit.json').read_text());entries={r['id']:r for r in audit['entries']}
 identities=json.loads((root/'Resources/catalog-identities.json').read_text())
 maintenance_path=root/'Resources/series-completion-audit.json'
 maintenance=json.loads(maintenance_path.read_text()) if maintenance_path.exists() else {}
 additions={e['bookId']:e for e in maintenance.get('additions',[])}
 current_audit={**entries,**{bid:{**e,'status':'retained'} for bid,e in additions.items()}}
 report=inspect_books(books,root,sources,current_audit,identities)
 if len(sources)!=len(source_list):report['errors'].append('Duplicate source ID')
 if set(sources)!=set(b['id'] for b in books):report['errors'].append('Source/catalog membership mismatch')
 baseline=json.loads((root/'tests/fixtures/pre-cleanup-books.json').read_text())
 if set(entries)!=set(b['id'] for b in baseline) or len(entries)!=len(audit['entries']):report['errors'].append('Audit must cover every original ID exactly once')
 if audit['counts']['original']!=len(baseline) or audit['counts']['final']+len(additions)!=len(books):report['errors'].append('Audit count mismatch')
 counts=audit['counts']
 for field,kind in [('duplicatesRemoved','duplicate'),('childrenRemoved','children'),('comicsRemoved','comic')]:
  if counts[field]!=sum(e['status']=='removed' and e.get('kind')==kind for e in entries.values()):report['errors'].append('Audit reason count mismatch: '+field)
 if counts['manualReview']!=sum(e['status']=='uncertain' for e in entries.values()):report['errors'].append('Manual review count mismatch')
 expected_aliases={str(e['id']):e['duplicateOf'] for e in entries.values() if e.get('duplicateOf')}
 expected_aliases.update({str(e['removedId']):e['retainedId'] for e in maintenance.get('duplicateAliases',[])})
 if identities['aliases']!=expected_aliases:report['errors'].append('Alias mapping differs from reviewed duplicate decisions')
 archived={b['id'] for b in identities['archived']};aliases=identities['aliases']
 for b in baseline:
  if b['id'] not in {x['id'] for x in books} and b['id'] not in archived and str(b['id']) not in aliases:report['errors'].append(f'Historical ID lost: {b["id"]}')
 expected='// Generated from Resources/catalog-identities.json; never renumber IDs.\n'+'globalThis.BOKASAFN_CATALOG_IDENTITIES = '+json.dumps(identities,ensure_ascii=False,separators=(',',':'))+';\n'
 if (root/'js/catalog-identities.js').read_text()!=expected:report['errors'].append('Browser identity manifest is stale')
 print(json.dumps(report,ensure_ascii=False,indent=2));return 1 if report['errors'] else 0
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);sys.exit(validate(p.parse_args().root))
