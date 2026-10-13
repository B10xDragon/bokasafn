#!/usr/bin/env python3
"""Reparse only cached Forlagið pages and covers, with no network requests.
Confirms every deployed new book against its original product page and image.
Uses collection-time dependencies. Does not change files or the catalog.
"""
import argparse,hashlib,json,sys
from pathlib import Path
from collect_forlagid import Collector,ROOT
class OfflineCollector(Collector):
 def fetch(self,url,binary=False):
  path=self.cache/(hashlib.sha256(url.encode()).hexdigest()+('.bin' if binary else '.html'))
  if not path.is_file():raise ValueError('Missing cached source: '+url)
  return path.read_bytes()
def main(cache,allow_prior_covers=False):
 sources=json.loads((ROOT/'Resources/catalog-sources.json').read_text());collector=OfflineCollector(cache);errors=[];fresh_covers=0;prior_covers=0
 for index,r in enumerate(sources):
  try:
   parsed=collector.parse({'url':r['url'],'discoveredIn':r.get('discoveredIn',[]),'reviewedCoverAuthor':r.get('authorEvidence')},allow_unmapped=True)
   # Catalog IDs are stable historical identities, not publisher product IDs.
   for field in ['sourceProductId','title','author','sourceCategories','edition','coverSourceURL','sourceHTMLSHA256']:
    if parsed[field]!=r[field]:raise ValueError('Source metadata changed: '+field)
   path=cache/(hashlib.sha256(r['coverSourceURL'].encode()).hexdigest()+'.bin')
   if path.exists():
    raw=collector.fetch(r['coverSourceURL'],True)
    if hashlib.sha256(raw).hexdigest()!=r['coverSourceSHA256']:raise ValueError('Source cover bytes/hash mismatch')
    fresh_covers+=1
   elif allow_prior_covers and r.get('coverVerifiedAt') and r['coverVerifiedAt']<r['verifiedAt']:
    prior_covers+=1
   else:raise ValueError('Missing cached source cover; prior evidence was not authorized')
  except Exception as error:errors.append({'id':r['id'],'url':r['url'],'error':str(error)})
  if (index+1)%100==0:print(f'Checked {index+1}/{len(sources)} cached product/cover pairs',flush=True)
 print(json.dumps({'productPages':len(sources),'cachedSourceCovers':fresh_covers,'coversUsingPriorEvidence':prior_covers,'networkRequests':collector.network,'errors':errors},ensure_ascii=False,indent=2))
 return 1 if errors else 0
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--cache',type=Path,required=True);p.add_argument('--allow-prior-cover-evidence',action='store_true');args=p.parse_args();sys.exit(main(args.cache,args.allow_prior_cover_evidence))
