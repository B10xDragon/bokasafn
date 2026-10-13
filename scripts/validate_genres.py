#!/usr/bin/env python3
"""Genre/schema errors fail; suspicious content/series differences require human review."""
import argparse,collections,json,re,sys,unicodedata
from pathlib import Path
from urllib.parse import urlparse
ROOT=Path(__file__).resolve().parents[1]
FORMATS={'novel','short-stories','poetry','drama','memoir','nonfiction','mixed','fiction'}
def key(value):return unicodedata.normalize('NFC',value).strip().casefold() if isinstance(value,str) else ''
def normalize_genre(value,taxonomy):
 if not isinstance(value,str):return None
 names={key(g['name']):g['name'] for g in taxonomy['genres']}
 names.update({key(old):new for old,new in taxonomy.get('aliases',{}).items()})
 return names.get(key(value),unicodedata.normalize('NFC',value).strip())
def inspect(books,taxonomy,audit=None):
 errors=[];warnings=[];names={g['name'] for g in taxonomy['genres']};ids=set();valid=[];groups=collections.defaultdict(list)
 def require(ok,msg):
  if not ok:errors.append(msg)
 require(len(names)==len(taxonomy['genres']),'Duplicate taxonomy names')
 require(12<=len(names)<=14,'Taxonomy must contain 12–14 broad genres')
 require(len({g['id'] for g in taxonomy['genres']})==len(taxonomy['genres']),'Duplicate taxonomy IDs')
 for g in taxonomy['genres']:
  require(bool(re.fullmatch('[a-z][a-z0-9-]*',g['id'])) and bool(g.get('definition')) and g.get('family') in {'fiction','nonfiction','form','tradition','general'},'Invalid taxonomy definition: '+g['name'])
 for old,new in taxonomy.get('aliases',{}).items():require(new in names,f'Alias {old}: unknown target {new}')
 for book in books:
  if not isinstance(book,dict):errors.append('Book must be an object');continue
  bid=book.get('id');require(type(bid) is int and bid>=1 and bid not in ids,f'{bid}: invalid/duplicate book ID')
  if type(bid) is not int or bid<1:continue
  ids.add(bid)
  cats=book.get('categories')
  if not isinstance(cats,list) or not cats or not all(isinstance(x,str) and x.strip() for x in cats):errors.append(f'{bid}: genres must be a nonempty string list');continue
  require(len({key(c) for c in cats})==len(cats),f'{bid}: duplicate genre tags')
  for c in cats:
   if c not in names:
    suggestion=normalize_genre(c,taxonomy)
    message='metadata facet/deprecated name' if c in taxonomy.get('legacyFacets',{}) else 'deprecated/spelling/capitalization' if suggestion in names else 'unknown genre'
    errors.append(f'{bid}: {message}: {c}'+(f' (use {suggestion})' if suggestion in names else ''))
  if len(cats)>3:warnings.append(f'{bid}: excessive tagging ({len(cats)}); review justification')
  if 'Raunsæjar skáldsögur' in cats and any(x in cats for x in ['Fantasía','Vísindaskáldskapur']):warnings.append(f'{bid}: realistic and speculative genres coexist; review whether different strands justify this')
  meta=book.get('classification')
  if not isinstance(meta,dict):errors.append(f'{bid}: missing separate classification metadata')
  else:
   require(meta.get('primaryGenre')==cats[0] and meta.get('secondaryGenres')==cats[1:],f'{bid}: primary/secondary genres disagree with display tags')
   require(meta.get('literaryForm') in FORMATS,f'{bid}: invalid literary form')
   require(isinstance(meta.get('audienceTags'),list) and set(str(x) for x in meta['audienceTags'])<= {'Ungmenni'},f'{bid}: invalid separate audience tags')
   require(isinstance(meta.get('legacyFacets'),list) and all(c in {'Skáldverk','Skáldsögur'} for c in meta.get('legacyFacets',[])),f'{bid}: invalid historical store facets')
   require(type(meta.get('translated')) is bool,f'{bid}: invalid separate translation flag')
  valid.append(book)
  series=book.get('series')
  if isinstance(series,dict) and isinstance(series.get('id'),str):groups[series['id']].append(book)
 # Majority overlap is a prompt for review, never an automatic classifier/error.
 for sid,items in groups.items():
  if len(items)<2:continue
  counts=collections.Counter(c for b in items for c in set(b['categories']))
  for genre,count in counts.items():
   if 1<count<len(items) and count>=len(items)*.6:
    warnings.append(f'{sid}: {genre} appears in {count}/{len(items)} volumes; review missing '+','.join(str(b['id']) for b in items if genre not in b['categories']))
 if audit is not None:
  entries=audit.get('entries',[]);reviewed={e.get('bookId'):e for e in entries};require(len(reviewed)==len(entries) and set(reviewed)==ids,'Audit must cover every active ID exactly once')
  for b in valid:
   bid=b['id'];e=reviewed.get(bid,{});p=e.get('publisherEvidence',{});url=urlparse(p.get('url',''))
   require(e.get('newGenres')==b['categories'] and e.get('classification')==b.get('classification') and bool(e.get('reason')),f'{bid}: stale/missing genre audit')
   require(e.get('status') in {'reviewed','manual_review'},f'{bid}: unreviewed decision')
   require(p.get('url')==b.get('sourceURL') and url.scheme=='https' and not url.username and not url.password and url.hostname in {'www.forlagid.is','forlagid.is'} and url.path.startswith('/vara/') and bool(re.fullmatch('[0-9a-f]{64}',p.get('sourceHTMLSHA256',''))) and bool(p.get('verifiedAt')) and type(p.get('sourceProductId')) is int and p['sourceProductId']>0,f'{bid}: missing verified Forlagið evidence')
   if p.get('descriptionUsable') is False:require(e.get('status')=='manual_review',f'{bid}: unusable publisher description needs review')
   if e.get('status')=='manual_review':warnings.append(f'{bid}: manual content/subgenre review remains: '+e.get('reason',''))
   if 'Skáldskapur' in b.get('classification',{}).get('detailedGenres',[]):require(e.get('status')=='manual_review',f'{bid}: generic fiction fallback needs explicit manual-review status')
  for s in audit.get('series',[]):
   for b in groups.get(s['seriesId'],[]):
    missing=set(s.get('sharedMajorGenres',[]))-set(b['categories'])
    if missing:warnings.append(f'{s["seriesId"]}/{b["id"]}: reviewed shared major genre missing: '+', '.join(sorted(missing)))
  byid={b['id']:b for b in valid}
  for s in audit.get('relatedGroups',[]):
   for bid in s['bookIds']:
    if bid in byid and not set(s['majorGenres'])<=set(byid[bid]['categories']):warnings.append(f'{s["id"]}/{bid}: related-work shared genre differs; review')
 return {'books':len(books),'genres':len(names),'series':len(groups),'errors':errors,'warnings':warnings,'distribution':dict(sorted(collections.Counter(c for b in valid for c in b['categories']).items()))}
def main():
 p=argparse.ArgumentParser();p.add_argument('--catalog',type=Path,default=ROOT/'Resources/books.json');p.add_argument('--taxonomy',type=Path,default=ROOT/'Resources/genre-taxonomy.json');p.add_argument('--audit',type=Path,default=ROOT/'Resources/genre-audit.json');p.add_argument('--without-audit',action='store_true');a=p.parse_args()
 try:r=inspect(json.loads(a.catalog.read_text()),json.loads(a.taxonomy.read_text()),None if a.without_audit else json.loads(a.audit.read_text()))
 except (OSError,ValueError,KeyError,TypeError) as e:print('Genre validation failed: '+str(e));return 1
 print(json.dumps(r,ensure_ascii=False,indent=2));return bool(r['errors'])
if __name__=='__main__':sys.exit(main())
