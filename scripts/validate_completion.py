#!/usr/bin/env python3
"""Validate the entire title review, approved additions, finite totals and identity preservation."""
import json,re,sys,hashlib
from pathlib import Path
from catalog_keys import title_key,author_key
from validate_catalog import forlagid_product
ROOT=Path(__file__).resolve().parents[1]
def presentation_flags(title):
 return bool(re.search(r'(?:\s|[–—-])(?:NÝ(?:\s+ÚTGÁFA)?|endurútgáfa|kilja|rafbók|hljóðbók|innbundin|íslensk klassík|hardcover|paperback)\s*$|\((?:NÝ(?: ÚTGÁFA)?|kilja|innbundin|\d+\. útgáfa)\)\s*$|\b(?:ISBN|SKU)\s*[:#]?\s*[\d-]+\s*$|^\(\d+\)\s|#\d+',title,re.I))
def availability(series,books):
 members=[b for b in books if b.get('series',{}).get('id')==series['id']];known=series.get('total') or series.get('knownTotal') or max([len(members),*[b['series']['number'] or 0 for b in members]])
 nums={b['series']['number'] for b in members if b['series']['number'] is not None};unknown=sum(b['series']['number'] is None for b in members);missing=[n for n in range(1,known+1) if n not in nums]
 return {'known':known,'available':len(members),'missingNumbers':missing,'unknownNumbers':unknown,'complete':bool(series.get('total') and not missing and not unknown)}
def inspect(books,baseline,sources,series,audit,identities):
 errors=[];warnings=[];old={b['id']:b for b in baseline};current={b['id']:b for b in books};reviews={x['bookId']:x for x in audit['titleReviews']};additions={x['bookId']:x for x in audit['additions']};decisions={x['id']:x for x in audit.get('priorExclusions',[])}
 def require(ok,msg):
  if not ok:errors.append(msg)
 require(len(current)==len(books),'Duplicate book IDs')
 workKeys=[(title_key(b['title']),author_key(b['author'])) for b in books]
 require(len(set(workKeys))==len(workKeys),'Duplicate literary title/author')
 require(set(reviews)==set(current) and len(reviews)==len(audit['titleReviews']),'Every catalog title must have exactly one review')
 require(set(current)==set(old)|set(additions),'An original ID was lost or an addition was not reviewed')
 for bid,b in current.items():
  r=reviews.get(bid,{});src=sources.get(bid,{})
  require(r.get('title')==b['title'] and r.get('publisherTitle')==src.get('title') and r.get('sourceURL')==b['sourceURL'] and r.get('sourceHTMLSHA256')==src.get('sourceHTMLSHA256') and bool(r.get('reason')),f'{bid}: title review/provenance mismatch')
  require(not presentation_flags(b['title']) or r.get('literalTitleException'),f'{bid}: unreviewed marketing/series presentation remains in title')
  require(b['title'].strip()==b['title'] and '  ' not in b['title'],f'{bid}: title whitespace')
  aliases=b.get('titleAliases',[])
  require(isinstance(aliases,list) and all(isinstance(x,str) and bool(x.strip()) for x in aliases) and len(set(aliases))==len(aliases),f'{bid}: invalid title aliases')
  if bid in old:
   for key in ['author','cover','pages','publicationYear']:
    require(b.get(key)==old[bid].get(key),f'{bid}: existing {key} changed unexpectedly')
   if b['title']!=old[bid]['title']:
    legacy=identities['legacyTitles'].get(old[bid]['title']);legacy=identities['aliases'].get(str(legacy),legacy)
    require(old[bid]['title'] in b.get('titleAliases',[]) and legacy==bid,f'{bid}: old title compatibility lost')
  else:
   e=additions.get(bid,{});require(e.get('audience')=='13+' and e.get('comic') is False and e.get('identityVerified') is True and forlagid_product(e.get('sourceURL')),f'{bid}: addition lacks reviewed suitability/identity/source')
   require(decisions.get(bid,{}).get('kind') not in ['children','comic'],f'{bid}: previously excluded unsuitable book restored')
   path=ROOT/b['cover']
   require(path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==src.get('coverSHA256'),f'{bid}: cover bytes mismatch')
 for s in series:
  result=availability(s,books);entry=next((x for x in audit['series'] if x['seriesId']==s['id']),{})
  require(entry.get('availability')==result,f'{s["id"]}: stale completeness/gap report')
  members=sorted([b for b in books if b.get('series',{}).get('id')==s['id']],key=lambda b:(b['series']['number'] or float('inf'),b['title']))
  require(entry.get('bookIds')==[b['id'] for b in members],f'{s["id"]}: audited reading order is stale')
  if s.get('total'):require(bool(entry.get('totalEvidence')),f'{s["id"]}: finite total lacks publisher evidence')
  require(not s.get('total') or s['total']>=result['available'],f'{s["id"]}: available books exceed finite main-series total')
  if result['unknownNumbers']:warnings.append(f'{s["id"]}: {result["unknownNumbers"]} ordering decisions remain unresolved')
 for e in audit.get('duplicateAliases',[]):
  require(identities['aliases'].get(str(e['removedId']))==e['retainedId'] and e['retainedId'] in current and e['removedId'] not in current and bool(e.get('evidence')),f'{e["removedId"]}: unsafe duplicate alias')
 return {'books':len(books),'titleReviews':len(reviews),'additions':len(additions),'completeSeries':sum(availability(s,books)['complete'] for s in series),'incompleteOrUnresolvedSeries':sum(not availability(s,books)['complete'] for s in series),'errors':errors,'warnings':warnings}
def main():
 read=lambda p:json.loads((ROOT/p).read_text());r=inspect(read('Resources/books.json'),read('tests/fixtures/pre-series-completion-books.json'),{r['id']:r for r in read('Resources/catalog-sources.json')},read('Resources/series.json'),read('Resources/series-completion-audit.json'),read('Resources/catalog-identities.json'))
 print(json.dumps(r,ensure_ascii=False,indent=2));return bool(r['errors'])
if __name__=='__main__':sys.exit(main())
