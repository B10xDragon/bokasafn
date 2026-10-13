"""Completion decisions fail safely without stripping real literary numbers or inventing totals."""
import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from validate_completion import availability,inspect,presentation_flags
ROOT=Path(__file__).resolve().parents[1]
class CompletionMetadata(unittest.TestCase):
 def setUp(self):
  read=lambda p:json.loads((ROOT/p).read_text())
  self.books=read('Resources/books.json');self.baseline=read('tests/fixtures/pre-series-completion-books.json');self.sources={x['id']:x for x in read('Resources/catalog-sources.json')};self.series=read('Resources/series.json');self.audit=read('Resources/series-completion-audit.json');self.identities=read('Resources/catalog-identities.json')
 def result(self):return inspect(self.books,self.baseline,self.sources,self.series,self.audit,self.identities)
 def test_every_title_and_addition_has_reviewed_evidence(self):self.assertFalse(self.result()['errors'])
 def test_missing_title_review_and_unreviewed_addition_fail(self):
  self.audit['titleReviews'].pop();self.assertTrue(self.result()['errors'])
  self.audit['additions'].pop();self.assertTrue(any('addition was not reviewed' in x for x in self.result()['errors']))
 def test_no_marketing_suffixes_but_real_numbers_and_subtitles_survive(self):
  for title in ['Harry Potter – NÝ','Bókin NÝ ÚTGÁFA','Bókin-rafbók','(6) Harry Potter','Bókin #3']:self.assertTrue(presentation_flags(title),title)
  for title in ['40 vikur','Fahrenheit 451','Hvísl hrafnanna 3','Skýrsla 64','Tómas Jónsson – metsölubók','Bölvun múmíunnar – seinni hluti']:self.assertFalse(presentation_flags(title),title)
 def test_original_ids_metadata_and_old_title_aliases_are_required(self):
  self.books[0]['id']=9999999;self.assertTrue(self.result()['errors'])
  self.books=copy.deepcopy(self.baseline);self.books[0]['pages']=1;self.assertTrue(any('pages changed' in x for x in self.result()['errors']))
 def test_removed_child_or_comic_id_cannot_be_reintroduced(self):
  bid=self.audit['additions'][0]['bookId'];self.audit['priorExclusions'].append({'id':bid,'kind':'children'});self.assertTrue(any('unsuitable book restored' in x for x in self.result()['errors']))
 def test_complete_missing_and_unknown_ordinal_are_not_equivalent(self):
  s={'id':'synthetic','total':3};books=[{'series':{'id':'synthetic','number':n}} for n in [1,2,3]]
  self.assertTrue(availability(s,books)['complete']);books[1]['series']['number']=None
  r=availability(s,books);self.assertFalse(r['complete']);self.assertEqual(r['missingNumbers'],[2]);self.assertEqual(r['available'],3)
  books[1]['series']['number']=2;s={'id':'synthetic','knownTotal':3};self.assertFalse(availability(s,books)['complete'])
 def test_false_final_total_and_stale_order_are_errors(self):
  entry=next(x for x in self.audit['series'] if x['availability']['complete']);entry['totalEvidence']=[];entry['bookIds'].reverse();errors=self.result()['errors'];self.assertTrue(any('finite total lacks' in x for x in errors));self.assertTrue(any('reading order' in x for x in errors))
 def test_new_cover_hash_and_safe_duplicate_alias_are_required(self):
  bid=self.audit['additions'][0]['bookId'];self.sources[bid]['coverSHA256']='0'*64;self.assertTrue(any('cover bytes mismatch' in x for x in self.result()['errors']))
  self.audit['duplicateAliases'][0]['retainedId']=9999999;self.assertTrue(any('unsafe duplicate alias' in x for x in self.result()['errors']))
if __name__=='__main__':unittest.main()
