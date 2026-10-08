#!/usr/bin/env python3
"""Validate reviewed series and author metadata without networking or user-data changes."""
import json,re,sys,unicodedata,collections
from pathlib import Path
from validate_catalog import forlagid_product
ROOT=Path(__file__).resolve().parents[1]
def author_key(value):return ''.join(c for c in unicodedata.normalize('NFKC',value).casefold() if c.isalnum())
def inspect(books,series,authors,audit,sources):
 errors=[];warnings=[]
 def require(ok,message):
  if not ok:errors.append(message)
 for label,items in [('series',series),('author',authors)]:
  require(len({x['id'] for x in items})==len(items),f'Duplicate {label} ID')
  for x in items:
   require(bool(re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*',x['id'])),f'Invalid {label} ID: {x["id"]}')
   require(isinstance(x.get('name'),str) and bool(x['name'].strip()),f'Missing {label} name')
 sdict={x['id']:x for x in series};adict={x['id']:x for x in authors};evidence={x['bookId']:x for x in audit};members=collections.defaultdict(list);seen_author={}
 require(len(evidence)==len(audit) and set(evidence)=={b['id'] for b in books},'Audit must examine each active book exactly once')
 for a in authors:
  for name in [a['name'],*a.get('aliases',[])]:
   k=author_key(name);require(k not in seen_author or seen_author[k]==a['id'],f'Author variant split across IDs: {name}');seen_author[k]=a['id']
 for b in books:
  names=b['author'].split(', ');ids=b.get('authorIds',[])
  require(len(names)==len(ids) and len(set(ids))==len(ids),f'{b["id"]}: missing/duplicate author references')
  for name,aid in zip(names,ids):
   a=adict.get(aid);require(a is not None and author_key(name) in {author_key(n) for n in [a['name'],*a.get('aliases',[])]} if a else False,f'{b["id"]}: author identity mismatch: {name}')
  e=evidence.get(b['id'],{});source=sources.get(b['id'],{})
  require(e.get('sourceURL')==b.get('sourceURL')==source.get('url') and e.get('sourceHTMLSHA256')==source.get('sourceHTMLSHA256'),f'{b["id"]}: missing/mismatched Forlagið evidence')
  require(forlagid_product(e.get('sourceURL')) and bool(re.fullmatch('[0-9a-f]{64}',e.get('sourceHTMLSHA256',''))),f'{b["id"]}: invalid publisher URL/hash')
  require(e.get('sourceTitle')==b['title'],f'{b["id"]}: publisher identity mismatch')
  require(e.get('status') in ['verified','uncertain','no_verified_evidence'],f'{b["id"]}: invalid audit status')
  s=b.get('series')
  if not s:
   require(e.get('series') is None,f'{b["id"]}: unassigned book has stale series audit')
   require(e.get('status')!='verified',f'{b["id"]}: verified series missing');continue
  registry=sdict.get(s.get('id'));require(registry is not None,f'{b["id"]}: unknown series ID')
  if not registry:continue
  require(s.get('name')==registry['name'] and s.get('total')==registry.get('total'),f'{b["id"]}: inconsistent series definition')
  n=s.get('number');total=s.get('total');require(n is None or type(n) is int and n>0,f'{b["id"]}: invalid series number')
  require(total is None or type(total) is int and total>0 and (n is None or type(n) is int and n<=total),f'{b["id"]}: invalid series total')
  require(e.get('status')=='verified' and e.get('series')==s and bool(e.get('evidence')),f'{b["id"]}: series lacks reviewed publisher evidence')
  if n is None:warnings.append(f'{b["id"]}: verified membership; ordering remains unknown')
  members[s['id']].append(b)
 for sid,items in members.items():
  numbers=[b['series']['number'] for b in items if b['series']['number'] is not None]
  require(len(numbers)==len(set(numbers)),f'{sid}: repeated series numbers require explicit edition/subseries review')
 require(set(members)==set(sdict),'Series registry contains empty/stale groups')
 require({aid for b in books for aid in b.get('authorIds',[])}==set(adict),'Author registry contains empty/stale identities')
 return {'books':len(books),'series':len(series),'assignedBooks':sum(len(x) for x in members.values()),'uniqueAuthors':len(authors),'multiBookSeries':sum(len(x)>1 for x in members.values()),'uncertainBooks':sum(e.get('status')=='uncertain' or e.get('numberUncertain',False) for e in audit),'errors':errors,'warnings':warnings}
def main():
 read=lambda p:json.loads((ROOT/p).read_text())
 r=inspect(read('Resources/books.json'),read('Resources/series.json'),read('Resources/authors.json'),read('Resources/series-audit.json')['entries'],{x['id']:x for x in read('Resources/catalog-sources.json')})
 expected='// Generated from Resources/authors.json. IDs are reserved across display-name changes.\nglobalThis.BOKASAFN_AUTHORS = '+json.dumps(read('Resources/authors.json'),ensure_ascii=False,separators=(',',':'))+';\n'
 if (ROOT/'js/browse-metadata.js').read_text()!=expected:r['errors'].append('Browser author registry is stale')
 print(json.dumps(r,ensure_ascii=False,indent=2));return bool(r['errors'])
if __name__=='__main__':sys.exit(main())
