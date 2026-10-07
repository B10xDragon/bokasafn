#!/usr/bin/env python3
"""Build deployed JSON from verified collector records and original summaries.
No publisher descriptions are copied into the repository. Uncurated descriptions
summarize only verified bibliographic facts and source categories, not invented plots.
"""
import argparse, collections, json, subprocess
from pathlib import Path
from catalog_keys import title_key
from catalog_language import icelandic_evidence
from catalog_categories import normalize_categories
from catalog_scope import is_activity_title
ROOT=Path(__file__).resolve().parents[1]
def factual_summary(r):
 cats=r['categories'];author=r['author']
 kind='myndasaga' if 'Myndasögur' in cats else 'fræðibók' if 'Fræðibækur' in cats else 'fantasía' if 'Fantasía' in cats else 'spennusaga' if 'Spenna' in cats else 'skáldverk' if 'Skáldverk' in cats or 'Skáldsögur' in cats else 'bók'
 audience=' Forlagið flokkar hana með ungmennabókum.' if 'Ungmenni' in cats else ' Hún er í barnabókaflokki Forlagsins.' if 'Barnabækur' in cats else ''
 opening=f"{r['title']} er {kind} eftir {author}."+audience
 edition=r['edition'];facts=[]
 if edition['year']:facts.append(f"Útgáfan sem er skráð hjá Forlaginu er frá {edition['year']}.")
 if edition['pages']:facts.append(f"Skráður blaðsíðufjöldi þeirrar útgáfu er {edition['pages']}.")
 return opening+' '+ ' '.join(facts)
def main(cache):
 original=json.loads((ROOT/'tests/fixtures/original-39-books.json').read_text())
 records=json.loads((cache/'records.json').read_text());summaries=json.loads((ROOT/'Resources/catalog-summaries.json').read_text())
 books=original[:];sources=[]
 exclusions=json.loads((ROOT/'Resources/catalog-exclusions.json').read_text())
 category_overrides=json.loads((ROOT/'Resources/catalog-category-overrides.json').read_text())
 keys={title_key(b['title']):b for b in original};build_rejections=[]
 accepted=[]
 for r in records:
  if is_activity_title(r['title']):
   build_rejections.append({'url':r['url'],'listingTitle':r['title'],'discoveredIn':r['discoveredIn'],'reason':'Activity/stationery item outside reading scope'})
   continue
  if str(r['sourceProductId']) in exclusions:
   build_rejections.append({'url':r['url'],'listingTitle':r['title'],'discoveredIn':r['discoveredIn'],'reason':exclusions[str(r['sourceProductId'])]})
   continue
  key=title_key(r['title'])
  if key in keys:
   build_rejections.append({'url':r['url'],'listingTitle':r['title'],'discoveredIn':r['discoveredIn'],'reason':'Duplicate book/edition after presentation normalization','duplicateOf':keys[key]['id']})
   continue
  keys[key]=r;accepted.append(r)
 records=accepted
 for r in sorted(records,key=lambda r:r['id']):
  language_evidence=icelandic_evidence(r)
  if language_evidence:r['language']='is';r['languageEvidence']=language_evidence
  r['categories']=normalize_categories(r['sourceCategories'],r['sourceDescription'])
  override=category_overrides.get(str(r['sourceProductId']))
  if override:r['categories']=list(dict.fromkeys(r['categories']+override['categories']))
  summary=summaries.get(str(r['sourceProductId']),factual_summary(r)).strip()
  b={k:r[k] for k in ['id','title','author','categories','cover']};b['description']=summary;b['pages']=r['edition']['pages'];b['publicationYear']=r['edition']['year'];b['sourceURL']=r['url']
  if r['language']:b['language']=r['language']
  books.append(b)
  sources.append({**{k:r[k] for k in ['id','sourceProductId','title','author','sourceCategories','coverSourceURL','coverSourceSHA256','coverSHA256','sourceHTMLSHA256','verifiedAt','language','languageEvidence','discoveredIn']},'url':r['url'],'edition':r['edition'],'reviewedCategoryAdditions':override,'summaryMethod':'reviewed original summary' if str(r['sourceProductId']) in summaries else 'original bibliographic summary'})
 # Prevent a future refresh from dropping or reassigning already shipped IDs.
 baseline=subprocess.run(['git','show','HEAD:Resources/books.json'],cwd=ROOT,capture_output=True,text=True)
 shipped=json.loads(baseline.stdout) if baseline.returncode==0 else json.loads((ROOT/'Resources/books.json').read_text())
 new_by_id={b['id']:b for b in books}
 for old in shipped:
  replacement=new_by_id.get(old['id'])
  if replacement is None or title_key(replacement['title'])!=title_key(old['title']):
   raise ValueError(f"Build would remove/change shipped book identity {old['id']}: {old['title']}")
 (ROOT/'Resources/books.json').write_text(json.dumps(books,ensure_ascii=False,indent=2)+'\n')
 (ROOT/'Resources/catalog-sources.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2)+'\n')
 report=json.loads((cache/'discovery.json').read_text());rejected=json.loads((cache/'rejected.json').read_text())+build_rejections
 stats={'candidatesExplored':len(report['candidates']),'previous':len(original),'final':len(books),'added':len(records),'withCovers':sum(bool(b['cover']) for b in books),'withPageCounts':sum(isinstance(b.get('pages'),int) and b['pages']>0 for b in books),'newWithExplicitIcelandicEvidence':sum(r['language']=='is' for r in records),'newIcelandicListingsWithoutExplicitLanguage':sum(r['language'] is None for r in records),'categories':dict(sorted(collections.Counter(c for b in books for c in b['categories']).items())),'duplicateListingsRejected':sum('Duplicate' in x['reason'] for x in rejected),'skipped':len([x for x in rejected if 'Duplicate' not in x['reason']]),'verificationFailuresSkipped':sum(x['reason'].startswith(('Missing ','No reliable','No book-specific','Source request','Cover too small','Non-Forlagið')) for x in rejected),'newWithPublicationYear':sum(r['edition']['year'] is not None for r in records),'skipReasons':dict(collections.Counter(x['reason'] for x in rejected if 'Duplicate' not in x['reason'])),'discovery':report['categories'],'summaries':dict(collections.Counter(x['summaryMethod'] for x in sources))}
 (ROOT/'Resources/catalog-report.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n')
 (ROOT/'Resources/catalog-rejections.json').write_text(json.dumps(rejected,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(stats,ensure_ascii=False,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--cache',type=Path,default=Path('/tmp/bokasafn-forlagid-cache'));main(p.parse_args().cache)
