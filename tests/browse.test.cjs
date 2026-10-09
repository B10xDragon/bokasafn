const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const root=path.resolve(__dirname,'..'),books=JSON.parse(fs.readFileSync(path.join(root,'Resources/books.json')));
const ctx={console,allBooks:books,userData:{read:[],liked:[]},document:{addEventListener(){}},Map,Set};vm.createContext(ctx);
for(const f of ['js/browse-metadata.js','js/browse.js'])vm.runInContext(fs.readFileSync(path.join(root,f),'utf8'),ctx);
const run=s=>vm.runInContext(s,ctx),json=s=>JSON.parse(run(`JSON.stringify(${s})`));let count=0;
function test(name,fn){fn();count++;console.log('PASS '+name)}
run('buildBrowseIndex()');
test('entire catalog has stable author identities and publisher-reviewed series',()=>{assert.equal(run('browseIndex.authors.size'),351);assert.equal(run('browseIndex.series.size'),62);assert.equal(run('[...browseIndex.series.values()].reduce((n,s)=>n+s.books.length,0)'),276);assert.equal(new Set(books.map(b=>b.id)).size,663);});
test('series preserve verified gaps and sort by actual numbers',()=>{assert.deepEqual(json('browseIndex.series.get("artemis-fowl").books.map(b=>b.series.number)'),[1,2,4,6,8,null,null]);assert.deepEqual(json('browseIndex.series.get("harry-potter").books.map(b=>b.series.number)'),[1,2,3,4,5,6,7]);});
test('unknown numbers stay separate from verified reading order',()=>{assert.deepEqual(json('browseIndex.series.get("artemis-fowl").books.map(b=>b.series.number)'),[1,2,4,6,8,null,null]);assert.deepEqual(json('seriesNeighbors(allBooks.find(b=>b.id===1004024))'),{});});
test('series progress counts only available books once',()=>{run('userData.read=[37,37,1030865,1030282,999999]');assert.deepEqual(json('seriesProgress(browseIndex.series.get("eragon"))'),{read:2,available:3});run('userData.read=[]');assert.deepEqual(json('seriesProgress(browseIndex.series.get("harry-potter"))'),{read:0,available:7});});
test('previous and next refer to available numbered books',()=>{assert.equal(run('seriesNeighbors(allBooks.find(b=>b.id===1028393)).next.id'),1030299);assert.equal(run('seriesNeighbors(allBooks.find(b=>b.id===37)).previous'),undefined);});
test('Icelandic composed/decomposed accents and search aliases work',()=>{assert.equal(run('browseFold("ÞRÍLEIKUR Æ Ö Ð")'),'thrileikur ae o d');assert(run('browseSuggestions("thriggja heima").some(r=>r.type==="series")'));assert(run('browseSuggestions("ARNALDUR INDRIÐASON").some(r=>r.type==="author")'));assert.equal(run('browseFold("o\\u0301")'),run('browseFold("ó")'));});
test('main search includes series members and typed series/author suggestions',()=>{assert(run('browseSuggestions("Eragon").some(r=>r.type==="series")'));assert(run('browseSuggestions("Paolini").some(r=>r.type==="author")'));assert(run('catalogMatchesSearch(allBooks.find(b=>b.id===36),"Hungurleikarnir")'));});
test('all coauthors receive their own books and punctuation variants normalize conservatively',()=>{const s=books.find(b=>b.id===1008310);for(const id of s.authorIds){ctx.aid=id;assert(run('browseIndex.authors.get(aid).books.some(b=>b.id===1008310)'));}assert.equal(run('authorIdentityKey("J. K. Rowling")'),run('authorIdentityKey("j.k.rowling")'));assert.notEqual(run('authorIdentityKey("Ásta")'),run('authorIdentityKey("Asta")'));});
test('synthetic combined search exposes all three result types and normalizes duplicate author variants',()=>{run(`var savedBooks=allBooks;allBooks=[{id:1,title:'Eragon',author:'Eragon Author',series:{id:'eragon',name:'Eragon',number:1},categories:[]},{id:2,title:'Another',author:'ERAGON AUTHOR',categories:[]}];buildBrowseIndex(allBooks,[]);`);assert.equal(run('browseIndex.authors.size'),1);assert.deepEqual(new Set(json('browseSuggestions("Eragon").map(r=>r.type)')),new Set(['book','series','author']));run('allBooks=savedBooks;buildBrowseIndex()');});
test('full catalog indexing and repeated combined search remain bounded',()=>{const start=performance.now();for(let i=0;i<20;i++)run('buildBrowseIndex();browseSuggestions("ó")');assert(performance.now()-start<3000);assert(run('browseSuggestions("ó").length<=11'));});
console.log(count+' browsing unit tests passed');

test('finite complete and unresolved series totals are different from available reading progress',()=>{
 assert.deepEqual(json('seriesAvailability(browseIndex.series.get("harry-potter"))'),{known:7,available:7,missing:[],unknown:0,complete:true});
 assert.deepEqual(json('seriesAvailability(browseIndex.series.get("eragon"))'),{known:4,available:3,missing:[3],unknown:0,complete:false});
 assert.equal(run('seriesAvailability(browseIndex.series.get("malin-fors")).complete'),false);
 assert.equal(run('seriesAvailability(browseIndex.series.get("artemis-fowl")).unknown'),2);
});
test('every cleaned title remains searchable using its former bookstore title',()=>{
 const baseline=JSON.parse(fs.readFileSync(path.join(root,'tests/fixtures/pre-series-completion-books.json')));
 for(const old of baseline){const current=books.find(b=>b.id===old.id);if(old.title!==current.title){ctx.oldTitle=old.title;ctx.bid=old.id;assert(run('catalogMatchesSearch(allBooks.find(b=>b.id===bid),oldTitle)'),old.title);}}
 assert(books.some(b=>b.title==='Fahrenheit 451'));assert(books.some(b=>b.title==='40 vikur'));
});
console.log(count+' browsing unit tests passed');

test('publisher-verified Hafsfólkið is complete and unknown Handan ordinals are not guessed',()=>{
 assert.deepEqual(json('browseIndex.series.get("hafsfolkid").books.map(b=>b.series.number)'),[1,2,3]);
 assert.equal(run('seriesAvailability(browseIndex.series.get("hafsfolkid")).complete'),true);
 assert.deepEqual(json('browseIndex.series.get("handan-hulunnar").books.map(b=>b.series.number)'),[1,null,null,null]);
 assert.equal(run('seriesAvailability(browseIndex.series.get("handan-hulunnar")).complete'),false);
 assert.equal(run('seriesAvailability(browseIndex.series.get("alex-rider")).known'),6);
 assert.equal(run('seriesAvailability(browseIndex.series.get("alex-rider")).complete'),false);
});
console.log(count+' browsing unit tests passed');
