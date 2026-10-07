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
def main(cache):
 sources=json.loads((ROOT/'Resources/catalog-sources.json').read_text());collector=OfflineCollector(cache);errors=[]
 for index,r in enumerate(sources):
  try:
   parsed=collector.parse({'url':r['url'],'discoveredIn':r['discoveredIn']})
   for field in ['id','sourceProductId','title','author','sourceCategories','edition','coverSourceURL','sourceHTMLSHA256']:
    if parsed[field]!=r[field]:raise ValueError('Source metadata changed: '+field)
   raw=collector.fetch(r['coverSourceURL'],True)
   if hashlib.sha256(raw).hexdigest()!=r['coverSourceSHA256']:raise ValueError('Source cover bytes/hash mismatch')
  except Exception as error:errors.append({'id':r['id'],'url':r['url'],'error':str(error)})
  if (index+1)%100==0:print(f'Checked {index+1}/{len(sources)} cached product/cover pairs',flush=True)
 print(json.dumps({'verifiedProductAndCoverPairs':len(sources),'networkRequests':collector.network,'errors':errors},ensure_ascii=False,indent=2))
 return 1 if errors else 0
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--cache',type=Path,required=True);sys.exit(main(p.parse_args().cache))
