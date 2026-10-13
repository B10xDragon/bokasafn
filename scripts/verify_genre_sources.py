"""Reparse saved Forlagið pages offline and verify the complete genre audit evidence."""
import argparse,hashlib,json
from pathlib import Path
from collect_forlagid import Collector,source_url
class OfflineCollector(Collector):
 def fetch(self,url,binary=False):
  source_url(url);return (self.cache/(hashlib.sha256(url.encode()).hexdigest()+('.bin' if binary else '.html'))).read_bytes()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--cache',type=Path,required=True);args=parser.parse_args()
 root=Path(__file__).resolve().parents[1];audit=json.loads((root/'Resources/genre-audit.json').read_text());collector=OfflineCollector(args.cache)
 count=0
 for entry in audit['entries']:
  ev=entry['publisherEvidence'];r=collector.parse({'url':ev['url'],'reviewedCoverAuthor':ev.get('authorEvidence')},allow_unmapped=True)
  for key,recordkey in [('title','title'),('author','author'),('description','sourceDescription'),('sourceCategories','sourceCategories'),('sourceHTMLSHA256','sourceHTMLSHA256'),('sourceProductId','sourceProductId')]:
   if ev[key]!=r[recordkey]:raise ValueError(f"Book {entry['bookId']}: {key} does not match publisher page")
  count+=1
 for ev in audit.get('additionalPublisherEvidence',[]):
  r=collector.parse({'url':ev['url']},allow_unmapped=True)
  for key in ['title','author','sourceDescription','sourceHTMLSHA256','sourceProductId']:
   if ev[key]!=r[key]:raise ValueError('Additional publisher evidence mismatch: '+key)
 print(f'{count} active book sources and {len(audit.get("additionalPublisherEvidence",[]))} companion source verified offline; no network or catalog changes.')
if __name__=='__main__':main()
