"""Genre errors fail, editorial uncertainty and series differences stay review warnings."""
import copy,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from validate_genres import inspect,normalize_genre
ROOT=Path(__file__).resolve().parents[1]
class GenreAudit(unittest.TestCase):
 def setUp(self):
  self.books=json.loads((ROOT/'Resources/books.json').read_text());self.tax=json.loads((ROOT/'Resources/genre-taxonomy.json').read_text());self.audit=json.loads((ROOT/'Resources/genre-audit.json').read_text())
 def result(self,audit=True):return inspect(self.books,self.tax,self.audit if audit else None)
 def test_complete_audit_has_no_errors(self):self.assertFalse(self.result()['errors']);self.assertEqual(len(self.audit['entries']),len(self.books))
 def test_real_hunger_games_and_fantasy_core(self):
  for b in self.books:
   sid=b.get('series',{}).get('id')
   if sid=='hungurleikarnir':self.assertTrue({'Vísindaskáldskapur og dystópía','Spenna og glæpasögur'}<=set(b['categories']))
   if sid in ['harry-potter','eragon']:self.assertTrue({'Fantasía','Ævintýri'}<=set(b['categories']))
   if b['id'] in [1128809,1261322]:self.assertNotIn('Fantasía',b['categories'])
   if b['id'] in [4,1166304]:self.assertIn('Vísindaskáldskapur og dystópía',b['categories'])
 def test_normalizes_aliases_case_and_composed_icelandic(self):
  for old,new in [('Fantasia','Fantasía'),('GLÆPIR','Spenna og glæpasögur'),('Vi\u0301sindaska\u0301ldsaga','Vísindaskáldskapur og dystópía'),('Hrollvekja','Hrollvekjur og ráðgátur')]:self.assertEqual(normalize_genre(old,self.tax),new)
  self.assertIsNone(normalize_genre(None,self.tax))
 def test_empty_and_invalid_genre_types_fail_safely(self):
  for bad in [None,{},'Fantasía',[],[None],[{}],['']]:
   self.books[0]['categories']=bad;self.assertTrue(self.result(audit=False)['errors'])
 def test_unknown_capitalization_and_deprecated_names_fail(self):
  for bad in ['Óþekkt','fantasía','Glæpir','Fantasía ']:
   self.books[0]['categories']=[bad];self.assertTrue(self.result(audit=False)['errors'])
 def test_duplicate_tags_including_case_variants_fail(self):
  for tags in [['Fantasía','Fantasía'],['Fantasía','fantasía']]:self.books[0]['categories']=tags;self.assertTrue(any('duplicate genre' in x for x in self.result(False)['errors']))
 def test_age_translation_and_broad_store_facets_are_not_genres(self):
  for bad in ['Ungmenni','Þýddar bækur','Skáldsögur','Skáldverk','13+','Harry Potter','Kilja']:
   self.books[0]['categories']=[bad];self.assertTrue(self.result(False)['errors'])
 def test_primary_secondary_metadata_cannot_disagree(self):
  self.books[0]['classification']['primaryGenre']='Fantasía';self.assertTrue(any('primary/secondary' in x for x in self.result(False)['errors']))
 def synthetic(self,tags):
  self.books=[{'id':i+1,'title':'Bók','categories':g,'classification':{'primaryGenre':g[0],'secondaryGenres':g[1:],'literaryForm':'novel','audienceTags':[],'translated':False,'legacyFacets':[]},'series':{'id':'saga'}} for i,g in enumerate(tags)]
 def test_series_majority_difference_warns_not_errors(self):
  self.synthetic([['Fantasía'],['Fantasía'],['Ævintýri']]);r=self.result(False);self.assertFalse(r['errors']);self.assertTrue(any('2/3 volumes' in x for x in r['warnings']))
 def test_legitimate_individual_secondary_genre_is_allowed(self):
  self.synthetic([['Fantasía','Ævintýri'],['Fantasía','Ævintýri','Rómantík'],['Fantasía','Ævintýri']]);self.assertFalse(self.result(False)['errors']);self.assertFalse(self.result(False)['warnings'])
 def test_excessive_tagging_is_a_review_warning(self):
  self.synthetic([['Fantasía','Ævintýri','Rómantík','Spenna og glæpasögur','Hrollvekjur og ráðgátur']]);r=self.result(False);self.assertFalse(r['errors']);self.assertTrue(any('excessive' in x for x in r['warnings']))
 def test_broad_fiction_does_not_claim_exclusive_realism(self):
  self.synthetic([['Fantasía','Skáldsögur og skáldskapur']]);r=self.result(False);self.assertFalse(r['errors']);self.assertFalse(r['warnings'])
 def test_missing_audit_and_publisher_source_fail(self):
  self.audit['entries'].pop();self.assertTrue(self.result()['errors'])
  self.audit['entries'][0]['publisherEvidence']['url']='https://www.example.org/book';self.assertTrue(any('Forlagið' in x for x in self.result()['errors']))
 def test_manual_review_fallback_cannot_be_claimed_as_verified(self):
  e=next(e for e in self.audit['entries'] if 'Skáldskapur' in e['classification']['detailedGenres']);e['status']='reviewed';self.assertTrue(any('fallback' in x for x in self.result()['errors']))
 def test_no_book_identity_or_other_metadata_changed(self):
  old=json.loads((ROOT/'tests/fixtures/pre-genre-audit-books.json').read_text());self.assertEqual({b['id'] for b in old},{b['id'] for b in self.books})
  by={b['id']:b for b in self.books}
  for b in old:self.assertEqual({k:v for k,v in b.items() if k!='categories'},{k:v for k,v in by[b['id']].items() if k not in ['categories','classification']})
 def test_taxonomy_alias_targets_are_valid(self):
  self.tax['aliases']['Gamalt']='Óþekkt';self.assertTrue(any('unknown target' in x for x in self.result(False)['errors']))
 def test_fourteen_broad_groups_and_one_to_three_tags(self):
  self.assertEqual(len(self.tax['genres']),14)
  self.assertTrue(all(1<=len(b['categories'])<=3 for b in self.books))
 def test_crime_mysteries_are_not_automatically_horror(self):
  for b in self.books:
   old=b['classification']['detailedGenres']
   if 'Glæpasögur' in old and 'Leyndardómar' in old and 'Hrollvekjur' not in old:self.assertNotIn('Hrollvekjur og ráðgátur',b['categories'])
 def test_simplification_preserves_original_evidence_and_classification_properties(self):
  before=json.loads((ROOT/'tests/fixtures/pre-simplified-genres.json').read_text());by={b['id']:b for b in self.books}
  for old in before:
   new=by[old['id']];self.assertEqual(old['categories'],new['classification']['detailedGenres'])
   for key in ['literaryForm','audienceTags','translated','legacyFacets']:self.assertEqual(old['classification'][key],new['classification'][key])
if __name__=='__main__':unittest.main()
