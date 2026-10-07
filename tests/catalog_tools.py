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
if __name__=='__main__':unittest.main()
