"""Definite metadata errors fail; verified gaps and conservative identities remain valid."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from validate_browsing import inspect,author_key
class BrowsingMetadata(unittest.TestCase):
 def setUp(self):
  self.books=[{'id':1,'title':'Bók','author':'J. K. Höfundur','authorIds':['hofundur'],'sourceURL':'https://www.forlagid.is/vara/bok/','series':{'id':'saga','name':'Saga','number':1,'total':3}}]
  self.series=[{'id':'saga','name':'Saga','total':3}];self.authors=[{'id':'hofundur','name':'J.K. Höfundur','aliases':[]}]
  self.audit=[{'bookId':1,'status':'verified','sourceURL':self.books[0]['sourceURL'],'sourceHTMLSHA256':'a'*64,'sourceTitle':'Bók','series':copy.deepcopy(self.books[0]['series']),'evidence':'Fyrsta bókin í þríleiknum.'}]
  self.sources={1:{'url':self.books[0]['sourceURL'],'sourceHTMLSHA256':'a'*64}}
 def result(self):return inspect(self.books,self.series,self.authors,self.audit,self.sources)
 def test_valid_gaps_and_name_punctuation(self):self.assertFalse(self.result()['errors'])
 def test_missing_number_warns_without_inventing_order(self):
  self.books[0]['series']['number']=None;self.audit[0]['series']['number']=None
  self.assertFalse(self.result()['errors']);self.assertEqual(len(self.result()['warnings']),1)
 def test_duplicate_series_number_fails(self):
  b=copy.deepcopy(self.books[0]);b['id']=2;self.books.append(b)
  e=copy.deepcopy(self.audit[0]);e['bookId']=2;self.audit.append(e);self.sources[2]=self.sources[1]
  self.assertTrue(any('repeated series numbers' in e for e in self.result()['errors']))
 def test_invalid_number_and_total_fail(self):
  for n in [0,-1,True,4,'2']:
   self.books[0]['series']['number']=n;self.assertTrue(self.result()['errors'])
 def test_evidence_and_identity_mismatch_fail(self):
  self.audit[0]['sourceHTMLSHA256']='b'*64;self.assertTrue(self.result()['errors'])
  self.audit[0]['sourceHTMLSHA256']='a'*64;self.books[0]['authorIds']=['different'];self.assertTrue(self.result()['errors'])
 def test_coauthors_and_conservative_accent_identity(self):
  self.books[0]['author']+=', Ásta';self.books[0]['authorIds'].append('asta');self.authors.append({'id':'asta','name':'Ásta','aliases':[]})
  self.assertFalse(self.result()['errors']);self.assertNotEqual(author_key('Ásta'),author_key('Asta'))
 def test_duplicate_author_variants_and_incomplete_audit_fail(self):
  self.authors.append({'id':'other','name':'J. K. Höfundur','aliases':[]});self.assertTrue(self.result()['errors'])
  self.authors.pop();self.audit=[];self.assertTrue(self.result()['errors'])
if __name__=='__main__':unittest.main()
