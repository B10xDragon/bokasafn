#!/usr/bin/env python3
"""Dependency-free validation of deployed catalog, original identities and source/cover chain."""
import collections, hashlib, json, re, sys
from pathlib import Path
from urllib.parse import urlparse
from catalog_keys import title_key
ROOT=Path(__file__).resolve().parents[1]
ALLOWED={'Grín','Rómantík','Þýddar bækur','Spenna','Ævintýri','Fantasía','Hrollvekja','Ráðgáta','Ungmenni','Glæpir','Klassík','Ævisögur','Vísindaskáldsaga','Barnabækur','Skáldsögur','Skáldverk','Fræðibækur','Myndasögur','Ljóð'}
def validate():
 books=json.loads((ROOT/'Resources/books.json').read_text());original=json.loads((ROOT/'tests/fixtures/original-39-books.json').read_text());sources=json.loads((ROOT/'Resources/catalog-sources.json').read_text())
 ids=set();keys={};covers={};evidence={r['id']:r for r in sources};errors=[]
 def check(condition,message):
  if not condition:errors.append(message)
 check(len(evidence)==len(sources),'Duplicate source ID')
 byid={b['id']:b for b in books}
 for b in original:check(byid.get(b['id'])==b,f"Original book {b['id']} changed")
 for b in books:
  bid=b.get('id');label=f'{bid}: {b.get("title")}'
  check(type(bid) is int and bid>=1 and bid not in ids,label+' invalid/repeated ID');ids.add(bid)
  check(isinstance(b.get('title'),str) and bool(b['title'].strip()),label+' missing title')
  check(isinstance(b.get('author'),str) and bool(b['author'].strip()) and len(b['author'])<500,label+' invalid author')
  key=title_key(b['title']);check(key not in keys,label+' duplicate title/edition '+str(keys.get(key)));keys[key]=bid
  cats=b.get('categories');check(isinstance(cats,list) and cats and len(set(cats))==len(cats) and set(cats)<=ALLOWED,label+' invalid category')
  pages=b.get('pages');check(pages is None or type(pages) is int and 0<pages<=20000,label+' invalid page count')
  cover=ROOT/b['cover'];check(cover.is_file(),label+' missing cover')
  if bid<=39:continue
  r=evidence.get(bid);check(r is not None,label+' missing source record')
  if not r:continue
  url=urlparse(r['url']);check(url.scheme=='https' and url.hostname=='www.forlagid.is' and url.path.startswith('/vara/'),label+' invalid metadata source')
  imageurl=urlparse(r['coverSourceURL']);check(imageurl.scheme=='https' and imageurl.hostname in {'www.forlagid.is','forlagid.is'} and imageurl.path.startswith('/wp-content/uploads/'),label+' invalid cover source')
  check(bid==1000000+r['sourceProductId'],label+' unstable new ID')
  check(b['title']==r['title'] and b['author']==r['author'] and b['sourceURL']==r['url'],label+' source metadata mismatch')
  check(b['pages']==r['edition']['pages'] and b['publicationYear']==r['edition']['year'],label+' edition metadata mismatch')
  year=b['publicationYear'];check(year is None or type(year) is int and 1800<=year<=2099,label+' invalid year')
  check(b['cover']==f"Resources/Images/forlagid-{r['sourceProductId']}.webp",label+' wrong cover filename')
  check(len(b['description'].strip())>=30,label+' missing original summary')
  for field in ['coverSHA256','coverSourceSHA256','sourceHTMLSHA256']:check(bool(re.fullmatch('[0-9a-f]{64}',r[field])),label+' invalid evidence hash '+field)
  if cover.is_file():
   raw=cover.read_bytes();digest=hashlib.sha256(raw).hexdigest();check(digest==r['coverSHA256'],label+' cover hash does not match source record')
   check(raw[:4]==b'RIFF' and raw[8:12]==b'WEBP',label+' invalid WebP file')
   check(digest not in covers,label+' shared cover requires review with '+str(covers.get(digest)));covers[digest]=bid
 check(set(evidence)=={b['id'] for b in books if b['id']>39},'Source/catalog membership mismatch')
 stats=json.loads((ROOT/'Resources/catalog-report.json').read_text())
 rejected=json.loads((ROOT/'Resources/catalog-rejections.json').read_text())
 check(stats['previous']==len(original) and stats['final']==len(books) and stats['added']==len(sources),'Catalog statistics/count mismatch')
 check(stats['added']+len(rejected)==stats['candidatesExplored'],'Candidate accounting incomplete')
 report={'books':len(books),'originalBooksPreserved':len(original),'added':len(sources),'covers':sum((ROOT/b['cover']).is_file() for b in books),'pageCounts':sum(b.get('pages') is not None for b in books),'categories':dict(sorted(collections.Counter(c for b in books for c in b['categories']).items())),'errors':errors}
 print(json.dumps(report,ensure_ascii=False,indent=2))
 return 1 if errors else 0
if __name__=='__main__':sys.exit(validate())
