#!/usr/bin/env python3
"""Apply explicit per-ID audit decisions to a frozen catalog, never renumbering it.
The source JSON is produced by the Forlagið collector outside the repository.
This command requires decisions for *every* shipped ID, including uncertainties.
"""
import argparse,collections,hashlib,io,json,sys,re
from pathlib import Path
from collect_forlagid import Collector,write_json
from catalog_keys import title_key,author_key
from catalog_categories import normalize_categories
from catalog_language import icelandic_evidence
ROOT=Path(__file__).resolve().parents[1]
def apply(verified,decisions,cache):
 if (ROOT/'Resources/series-completion-audit.json').exists():raise ValueError('Historical curation replay would discard reviewed series additions/titles. Maintain the completion audit and run the current catalog validators instead.')
 current_path=ROOT/'Resources/books.json'
 current={b['id']:b for b in json.loads(current_path.read_text())} if current_path.exists() else {}
 original=json.loads((ROOT/'tests/fixtures/pre-cleanup-books.json').read_text())
 old_sources={r['id']:r for r in json.loads((ROOT/'Resources/catalog-sources.json').read_text())}
 byid={b['id']:b for b in original};fresh={r['catalogId']:r for r in verified};decisions={int(k):v for k,v in decisions.items()}
 if set(decisions)!=set(byid):raise ValueError('Explicit decisions must cover every shipped ID exactly once')
 if set(fresh)!=set(byid):raise ValueError('Verification must attempt every shipped ID')
 aliases={str(bid):d['duplicateOf'] for bid,d in decisions.items() if d.get('duplicateOf')}
 for bid,target in aliases.items():
  if target not in byid or str(target) in aliases:raise ValueError('Missing target or alias chain')
 books=[];sources=[];entries=[];archived=[];collector=Collector(cache)
 from PIL import Image
 for bid,old in byid.items():
  d=decisions[bid];v=fresh[bid];r=v.get('record');status=d['status']
  if status not in ['retained','removed','uncertain'] or not d.get('reason'):raise ValueError(f'Invalid decision {bid}')
  e={'id':bid,'title':old['title'],'author':old['author'],**d,
     'checks':{'duplicate':{'isDuplicate':bool(d.get('duplicateOf')),'retainedId':d.get('duplicateOf')},
               'audience':d.get('audience','uncertain'),'comic':d.get('comic'),
               'educational':d.get('kind') in ['prose','duplicate'] if status!='uncertain' else None,
               'forlagid':{'verified':r is not None and d.get('identityVerified',False),'url':r['url'] if r else v.get('url',old.get('sourceURL')),'verifiedAt':r.get('verifiedAt') if r else None,'error':v.get('error')},
               'metadata':{'status':'identity_mismatch' if not d.get('identityVerified',False) else 'not_reverified' if not r else 'checked','changes':{}}}}
  if r:
   e['sourceCategories']=r['sourceCategories'];e['sourceHTMLSHA256']=r['sourceHTMLSHA256']
   # Short source excerpt supplies inspectable context without copying full blurbs.
   e['sourceExcerpt']=r['sourceDescription'][:220]
   observed={'title':r['title'],'author':r['author'],'pages':r['edition']['pages'],'publicationYear':r['edition']['year']}
   for field,value in observed.items():
    if old.get(field)!=value:e['checks']['metadata']['changes'][field]={'before':old.get(field),'sourceValue':value}
   if e['checks']['metadata']['changes'] and status!='retained':e['checks']['metadata']['status']='identity_mismatch' if not d.get('identityVerified',False) else 'differences_observed_archived_without_reassignment'

  if status=='retained':
   if not r:raise ValueError(f'Cannot retain unverified book {bid}')
   if not d.get('identityVerified'):raise ValueError(f'Identity must be established {bid}')
   b={**old,'title':r['title'],'author':d.get('verifiedAuthor',r['author']),
      'pages':r['edition']['pages'],'publicationYear':r['edition']['year'],'sourceURL':r['url']}
   for key in ['series','authorIds']:
    if key in current.get(bid,{}):b[key]=current[bid][key]
   translators=[]
   for creator in r['author'].split(', '):
    name=re.sub(r'\s+þýddi$','',creator)
    if creator.endswith(' þýddi') or re.search(re.escape(name)+r'\s+þýddi',r['sourceDescription'],re.I):translators.append(name)
   if translators:
    remaining=[c for c in r['author'].split(', ') if re.sub(r'\s+þýddi$','',c) not in translators]
    if remaining and not d.get('verifiedAuthor'):b['author']=', '.join(remaining)
    b['translators']=translators
   for role in ['translators','illustrators','adapters']:
    if role in d:b[role]=d[role]
   cats=normalize_categories(r['sourceCategories'],r['sourceDescription']);cats=[c for c in cats if c not in ['Myndasögur','Barnabækur']]
   b['categories']=list(dict.fromkeys(cats+d.get('categoryAdditions',[])))
   lang=icelandic_evidence(r)
   b.pop('language',None)
   if lang:b['language']='is'
   prev=old_sources.get(bid)
   if prev and r['coverSourceURL']==prev['coverSourceURL']:
    coverhash=prev['coverSHA256'];sourcehash=prev['coverSourceSHA256']
    candidates=[prev.get('cover',old['cover']),f"Resources/Images/forlagid-{r['sourceProductId']}.webp"]
    b['cover']=next((p for p in candidates if (ROOT/p).is_file() and hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==coverhash),None)
    if b['cover'] is None:raise ValueError(f'Previously verified cover bytes missing for {bid}')
   else:
    raw=collector.fetch(r['coverSourceURL'],True);sourcehash=hashlib.sha256(raw).hexdigest()
    img=Image.open(io.BytesIO(raw));img.load();img.thumbnail((360,540));out=io.BytesIO();img.convert('RGB').save(out,format='WEBP',quality=86,method=6)
    target=ROOT/'Resources/Images'/f"forlagid-{r['sourceProductId']}.webp";target.write_bytes(out.getvalue());b['cover']=str(target.relative_to(ROOT));coverhash=hashlib.sha256(out.getvalue()).hexdigest()
   if prev and prev.get('summaryMethod')=='original bibliographic summary' or d.get('rewriteDescription'):
    kind='skáldverk' if any(c in b['categories'] for c in ['Skáldverk','Skáldsögur','Klassík']) else 'bók'
    facts=f"{b['title']} er {kind} eftir {b['author']}."
    if b['publicationYear']:facts+=f" Skráð útgáfuár hjá Forlaginu er {b['publicationYear']}."
    if b['pages']:facts+=f" Skráður blaðsíðufjöldi er {b['pages']}."
    b['description']=facts
   for field in ['title','author','pages','publicationYear','cover','categories','description','sourceURL','language']:
    if old.get(field)!=b.get(field):e['checks']['metadata']['changes'][field]={'before':old.get(field),'after':b.get(field)}
   e['checks']['metadata']['status']='corrected' if e['checks']['metadata']['changes'] else 'accurate'
   src={k:r[k] for k in ['sourceProductId','title','author','sourceCategories','coverSourceURL','sourceHTMLSHA256','verifiedAt','edition','url']}
   src.update(catalogAuthor=b['author'],coverVerifiedAt=prev.get('coverVerifiedAt',prev['verifiedAt']) if prev and r['coverSourceURL']==prev['coverSourceURL'] else r['verifiedAt'],id=bid,coverSHA256=coverhash,coverSourceSHA256=sourcehash,language='is' if lang else None,languageEvidence=lang or 'Edition language not explicitly established',discoveredIn=prev.get('discoveredIn',[]) if prev else [],summaryMethod='retained original summary' if b['description']==old['description'] else 'original bibliographic summary')
   books.append(b);sources.append(src)
  elif not d.get('duplicateOf'):
   archived.append({**old,'archived':True,'archiveReason':d['reason']})
  entries.append(e)
 counts={'original':len(original),'final':len(books),'duplicatesRemoved':sum(d.get('kind')=='duplicate' for d in decisions.values()),'childrenRemoved':sum(d.get('kind')=='children' for d in decisions.values()),'comicsRemoved':sum(d.get('kind')=='comic' for d in decisions.values()),'otherRemoved':sum(d['status']=='removed' and d.get('kind') not in ['duplicate','children','comic'] for d in decisions.values()),'manualReview':sum(d['status']=='uncertain' for d in decisions.values()),'explicitIcelandicLanguage':sum(b.get('language')=='is' for b in books),'languageUnconfirmed':sum(b.get('language')!='is' for b in books)}
 identities={'version':1,'aliases':aliases,'archived':archived,'legacyTitles':{b['title']:b['id'] for b in original},'distinctPairs':[[1028393,1151506],[1030299,1151506],[1,1102811],[1115190,1153419],[1050528,1083730],[1050528,1102305],[1095511,1299502],[1022956,1190979],[1228061,1285676],[1296766,1297974],[1297974,1297976],[37,1030865],[39,1101175],[39,1127152]]}
 write_json(ROOT/'Resources/books.json',books);write_json(ROOT/'Resources/catalog-sources.json',sources)
 write_json(ROOT/'Resources/catalog-identities.json',identities)
 (ROOT/'js/catalog-identities.js').write_text('// Generated from Resources/catalog-identities.json; never renumber IDs.\n'+'globalThis.BOKASAFN_CATALOG_IDENTITIES = '+json.dumps(identities,ensure_ascii=False,separators=(',',':'))+';\n')
 write_json(ROOT/'Resources/catalog-audit.json',{'schemaVersion':1,'date':'2026-10-08','policy':'Forlagið-verified prose for teenage readers; uncertainties quarantined, historical IDs reserved. Counts use mutually exclusive primary reasons.','counts':counts,'entries':entries})
 print(json.dumps(counts,ensure_ascii=False,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--verified',type=Path,required=True);p.add_argument('--decisions',type=Path,default=ROOT/'Resources/catalog-decisions.json');p.add_argument('--cache',type=Path,required=True);a=p.parse_args();apply(json.loads(a.verified.read_text()),json.loads(a.decisions.read_text()),a.cache)
