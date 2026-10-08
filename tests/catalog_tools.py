"""Catalog normalization regressions; dependency-free like the validator."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from catalog_keys import title_key
from catalog_language import icelandic_evidence
from catalog_categories import normalize_categories
from catalog_scope import is_activity_title
class CatalogKeys(unittest.TestCase):
 def test_punctuation_case_and_unicode(self):
  self.assertEqual(title_key('Álfar – saga'),title_key('A\u0301LFAR: saga'))
 def test_physical_digital_editions(self):
  for suffix in [' – kilja',' (rafbók)',' – hljóðbók',' (2. útgáfa)',' – myndskreytt']:
   self.assertEqual(title_key('Bókin'+suffix),title_key('Bókin'))
 def test_store_presentation_and_original_hunger_games(self):
  self.assertEqual(title_key('(6) Harry Potter og blendingsprinsinn NÝ'),title_key('Harry Potter og blendingsprinsinn'))
  self.assertEqual(title_key('Eldar kvikna (Hungurleikar 2)'),title_key('Eldar kvikna'))
  self.assertEqual(title_key('Hermiskaði (Hungurleikar 3)'),title_key('Hermiskaði'))
 def test_meaningful_series_numbers_remain_distinct(self):
  self.assertNotEqual(title_key('Hvísl hrafnanna 3'),title_key('Hvísl hrafnanna'))
  self.assertNotEqual(title_key('Hundmann (1)'),title_key('Hundmann (2)'))
  self.assertNotEqual(title_key('Goðheimar 13: Feigðardraumar'),title_key('Goðheimar 14: Múrinn'))
class CatalogLanguage(unittest.TestCase):
 def test_explicit_translation(self):
  for text in ['Hér er komin áttunda bókin í íslenskri þýðingu.','Bókin kemur nú í fyrsta sinn út á íslensku.','Sverrir þýddi yfir á íslenskt skordýramál.']:
   self.assertIsNotNone(icelandic_evidence({'sourceDescription':text}))
 def test_classics_source_language(self):
  self.assertIsNotNone(icelandic_evidence({'sourceCategories':['Íslensk klassík']}))
  self.assertIsNotNone(icelandic_evidence({'sourceCategories':['Þýdd klassík']}))
 def test_no_nationality_or_title_inference(self):
  self.assertIsNone(icelandic_evidence({'sourceDescription':'Skáldsaga eftir íslenskan höfund um tungumál og þýðingar.'}))
class CatalogCategories(unittest.TestCase):
 def test_target_audience_and_genre(self):
  self.assertEqual(normalize_categories(['Barna- og unglingabækur','13 ára og eldri'],'Fantasía og hrollvekja'),['Ungmenni','Fantasía','Hrollvekja'])
 def test_fiction_and_translation(self):
  self.assertEqual(normalize_categories(['Þýddar skáldsögur','Skáldverk'],'Glæpasaga'),['Þýddar bækur','Skáldverk','Skáldsögur','Glæpir'])
 def test_broad_fiction_does_not_imply_novel(self):
  self.assertEqual(normalize_categories(['Skáldverk'],'Smásögur'),['Skáldverk'])
 def test_poetry_not_novel(self):
  self.assertEqual(normalize_categories(['13 ára og eldri'],'Barnaljóð Þórarins'),['Ungmenni','Ljóð'])
 def test_explicit_fantasy_classic_and_crime_categories(self):
  self.assertEqual(normalize_categories(['Fantasíur','Sígildar barnabækur','Norrænar glæpasögur'],''),['Fantasía','Klassík','Glæpir'])
 def test_nonfiction_topic_mentions_do_not_become_fiction_genres(self):
  self.assertEqual(normalize_categories(['Fræði- og handbækur'],'Rómantískar ástir í þjóðsögum og saga glæpasagna.'),['Fræðibækur'])
  self.assertEqual(normalize_categories(['Fræði- og handbækur','Fantasíur'],''),['Fræðibækur','Fantasía'])
class CatalogScope(unittest.TestCase):
 def test_diary_novels_and_memoirs_are_reading_books(self):
  for title in ['Dagbók Kidda klaufa 18: Ekkert mál','Randver kjaftar frá 1: Besti vinur Kidda skrifar eigin dagbók','Dagbók Önnu Frank']:
   self.assertFalse(is_activity_title(title))
 def test_actual_coloring_activity_books(self):
  for title in ['Kósí krútt – Krúttleg og sæt litabók','Litabókin hennar Rosie Flo','Þrautabók','Spilastokkur','Lubbi verkefnabók #2','Þankastrik 2026/1 RAUTT','Blæja – Hefjum leik!: skemmtibók með límmiðum (Bluey)']:
   self.assertTrue(is_activity_title(title))

class CatalogAuditValidation(unittest.TestCase):
 def setUp(self):
  import tempfile
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  (self.root/'Resources/Images').mkdir(parents=True);(self.root/'Resources/Images/test.webp').write_bytes(b'local cover')
  self.book={'id':1,'title':'Álfar – saga','author':'Höfundur','description':'Verified prose description','categories':['Fantasía'],'cover':'Resources/Images/test.webp','pages':None,'sourceURL':'https://www.forlagid.is/vara/alfar/'}
 def inspect(self,books):
  from validate_catalog import inspect_books
  return inspect_books(books,self.root)
 def test_definite_errors_fail_and_unknown_page_count_is_valid(self):
  self.assertEqual(self.inspect([self.book])['errors'],[])
  for change in [{'pages':0},{'pages':-3},{'pages':'10'},{'id':None},{'sourceURL':'https://forlagid.is.evil/vara/book/'},{'cover':'Resources/Images/missing.webp'},{'categories':['Myndasögur']},{'description':''}]:
   self.assertTrue(self.inspect([{**self.book,**change}])['errors'],change)
 def test_duplicate_ids_and_normalized_title_author_are_errors(self):
  self.assertTrue(self.inspect([self.book,{**self.book,'title':'Another work'}])['errors'])
  other={**self.book,'id':2,'title':'ÁLFAR: SAGA','author':'HÖFUNDUR'}
  self.assertTrue(self.inspect([self.book,other])['errors'])
 def test_different_authors_and_numbered_series_are_not_rejected(self):
  self.assertFalse(self.inspect([self.book,{**self.book,'id':2,'author':'Annar höfundur'}])['errors'])
  from catalog_keys import likely_duplicate
  self.assertFalse(likely_duplicate({**self.book,'title':'Eragon #1'},{**self.book,'id':2,'title':'Eragon #2: Öldungurinn'}))
 def test_subtitles_and_creator_variants_trigger_review_not_automatic_deletion(self):
  result=self.inspect([{**self.book,'title':'Stormsker','author':'Birkir Blær'},{**self.book,'id':2,'title':'Stormsker – Fólkið sem fangaði vindinn','author':'Birkir Blær, Annar'}])
  self.assertFalse(result['errors']);self.assertTrue(result['warnings'])

class RepeatCuration(unittest.TestCase):
 def test_repeated_curation_keeps_verified_legacy_cover_paths_and_identity(self):
  import tempfile,json,hashlib,contextlib,io
  import curate_catalog
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp)
   for part in ['Resources/Images','tests/fixtures','js','cache']:(root/part).mkdir(parents=True)
   cover='Resources/Images/forlagid-1234.webp';raw=b'previously verified local bytes';(root/cover).write_bytes(raw)
   old={'id':1,'title':'Gömul saga','author':'Höfundur','description':'Original accurate prose summary','cover':'Resources/Images/legacy.jpg','categories':['Ungmenni'],'pages':200}
   archived={**old,'id':2,'title':'Barnabók'}
   (root/'tests/fixtures/pre-cleanup-books.json').write_text(json.dumps([old,archived]))
   record={'id':1001234,'sourceProductId':1234,'title':'Gömul saga','author':'Höfundur','sourceCategories':['13 ára og eldri'],'sourceDescription':'Verified substantial adolescent prose narrative.','edition':{'pages':None,'year':None,'format':None},'url':'https://www.forlagid.is/vara/saga/','coverSourceURL':'https://www.forlagid.is/wp-content/uploads/cover.jpg','sourceHTMLSHA256':'a'*64,'verifiedAt':'2026-10-08'}
   prior={**record,'id':1,'coverSHA256':hashlib.sha256(raw).hexdigest(),'coverSourceSHA256':'b'*64,'coverVerifiedAt':'2026-10-07'}
   (root/'Resources/catalog-sources.json').write_text(json.dumps([prior]))
   browsing={'series':{'id':'saga','name':'Saga','number':1},'authorIds':['hofundur']}
   (root/'Resources/books.json').write_text(json.dumps([{**old,**browsing}]))
   decisions={'1':{'status':'retained','kind':'prose','audience':'13+','comic':False,'identityVerified':True,'reason':'Verified teen prose'},'2':{'status':'removed','kind':'children','audience':'under13','comic':False,'identityVerified':True,'reason':'Verified younger-reader edition'}}
   original_root=curate_catalog.ROOT
   try:
    curate_catalog.ROOT=root
    with contextlib.redirect_stdout(io.StringIO()):
     for _ in range(2):
      curate_catalog.apply([{'catalogId':1,'record':record},{'catalogId':2,'error':'No fresh page'}],decisions,root/'cache')
      books=json.loads((root/'Resources/books.json').read_text());self.assertEqual(books[0]['cover'],cover);self.assertEqual(books[0]['id'],1)
      for key,value in browsing.items():self.assertEqual(books[0][key],value);self.assertIsNone(books[0]['pages'])
      sources=json.loads((root/'Resources/catalog-sources.json').read_text());self.assertEqual(sources[0]['coverVerifiedAt'],'2026-10-07')
      identities=json.loads((root/'Resources/catalog-identities.json').read_text());self.assertEqual(identities['archived'][0]['id'],2)
   finally:curate_catalog.ROOT=original_root

if __name__=='__main__':unittest.main()
