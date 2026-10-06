const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const catalog = JSON.parse(fs.readFileSync(path.join(root, 'Resources/books.json')));
let passed = 0;
function test(name, fn) { fn(); passed++; console.log('PASS ' + name); }
function harness(stored = {}) {
    const storage = new Map(Object.entries(stored));
    const nodes = new Map();
    const makeNode = () => ({value:'', innerHTML:'', innerText:'', style:{}, children:[], classList:{add(){},remove(){},toggle(){},contains(){return false}},setAttribute(){},querySelector(){return null}});
    const ctx = { console:{warn(){},error(){}}, Date, Intl, Math, TextEncoder, TextDecoder, Uint8Array, btoa, atob, bokasafnThemePreference:'system', crypto:require('node:crypto'),
        document:{getElementById(id){if (!nodes.has(id)) nodes.set(id,makeNode());return nodes.get(id)},querySelector(){return null},querySelectorAll(){return []},addEventListener(){},activeElement:null},
        window:{addEventListener(){}}, localStorage:{get length(){return storage.size},key(i){return [...storage.keys()][i]??null},getItem(key){return storage.get(key)??null},setItem(key,value){storage.set(key,value)},removeItem(key){storage.delete(key)}},sessionStorage:{get length(){return 0},key(){return null},getItem(){return null},setItem(){},removeItem(){}},
        setInterval(){return 1},clearInterval(){},setTimeout(){},requestAnimationFrame(){},rememberBookFocus(){return null},restoreBookFocus(){},prepareDialog(){},restoreDialogFocus(){} };
    vm.createContext(ctx);
    for (const file of ['js/persistence.js','js/insights.js','js/app.js','js/backups.js']) vm.runInContext(fs.readFileSync(path.join(root,file),'utf8'),ctx);
    vm.runInContext('allBooks = '+JSON.stringify(catalog),ctx);
    vm.runInContext('appReady = true; userDataLoaded = true;', ctx);
    return {ctx,storage,nodes,run(code){return vm.runInContext(code,ctx)},data(){return JSON.parse(vm.runInContext('JSON.stringify(userData)',ctx))}};
}
const first=catalog[0];
test('catalog IDs and assets remain consistent',()=>{
    assert.equal(new Set(catalog.map(b=>b.id)).size,catalog.length);
    assert(catalog.every(b=>!b.categories.includes('Fantasia')));
    assert(catalog.some(b=>b.categories.includes('Fantasía')));
});
test('legacy migration preserves titles, reviews, goals and unknown books',()=>{
    const legacy={liked:[first.title,first.title,'Old missing book'],read:[first.title],reviews:{[first.title]:{rating:4,comment:'<b>literal</b>',date:'yesterday'},'Missing review':{rating:3,comment:'keep'}},totalSeconds:900,dailyProgress:{'2026-09-30':900},minutesGoal:25,goalType:'weekly',personalGoals:[{id:1,text:'keep',completed:true}]};
    const h=harness({library_v14:JSON.stringify(legacy)});h.run('loadUserData()');
    const d=h.data();assert.deepEqual(d.liked,[first.id]);assert.deepEqual(d.read,[first.id]);assert.equal(d.reviews[first.id].comment,'<b>literal</b>');assert.equal(d.totalSeconds,900);assert.equal(d.personalGoals[0].completed,true);assert.deepEqual(d.unresolved.liked,['Old missing book']);assert.equal(d.unresolved.reviews['Missing review'].comment,'keep');assert.equal(h.storage.get('library_v14'),JSON.stringify(legacy));assert(h.storage.has('library_v15'));
    h.run('allBooks[0].title="Renamed title"; loadUserData()');assert.deepEqual(h.data().liked,[first.id]);assert.equal(h.data().reviews[first.id].rating,4);
});
test('unmatched legacy titles migrate when a book returns',()=>{
    const h=harness({library_v14:JSON.stringify({liked:['Lost'],reviews:{Lost:{rating:5,comment:'recover'}}})});h.run('loadUserData(); allBooks.push({id:100,title:"Lost"});loadUserData()');assert.deepEqual(h.data().liked,[100]);assert.equal(h.data().reviews[100].comment,'recover');assert.deepEqual(h.data().unresolved.liked,[]);
});
test('malformed and partial saved data does not crash or destroy original data',()=>{
    for (const legacy of ['null','[]','{"read":null,"reviews":[],"dailyProgress":null,"personalGoals":null}','{"totalSeconds":-1,"minutesGoal":"bad","goalType":"invalid","liked":[{},null]}']) {
        const h=harness({library_v14:legacy});h.run('loadUserData();updateStatsUI()');assert.equal(h.data().totalSeconds,0);assert.equal(h.storage.get('library_v14'),legacy);
    }
    const h=harness({library_v14:'{invalid'});h.run('loadUserData();saveUserData()');assert.equal(h.storage.get('library_v14'),'{invalid');assert(!h.storage.has('library_v15'));
    const bad=harness({library_v15:'{broken',library_v14:JSON.stringify({liked:[first.title]})});bad.run('loadUserData()');assert.equal(bad.storage.get('library_v15_recovery'),'{broken');assert.deepEqual(bad.data().liked,[first.id]);
});
test('wishlist and read filters update immediately; invalid IDs are ignored',()=>{
    const h=harness();h.run(`userData=normalizeUserData({version:15,liked:[${first.id}],read:[${first.id}]});activeCategories=['❤️ Óskalisti'];applyFilters()`);assert.equal(h.run('filteredBooks.length'),1);h.run(`toggleLike(${first.id})`);assert.equal(h.run('filteredBooks.length'),0);h.run("activeCategories=['✅ Lesið'];applyFilters()");assert.equal(h.run('filteredBooks.length'),1);h.run(`toggleRead(${first.id});toggleLike(9999)`);assert.equal(h.run('filteredBooks.length'),0);assert.deepEqual(h.data().liked,[]);
});
test('future data schemas are preserved without being downgraded',()=>{
    const future=JSON.stringify({version:16,liked:[1],futureField:'keep'});
    const h=harness({library_v15:future});h.run('loadUserData();saveUserData()');assert.equal(h.storage.get('library_v15'),future);
});
test('startup writes cannot replace existing data before loading it',()=>{
    const saved=JSON.stringify({version:15,totalSeconds:900,read:[1]});
    const h=harness({library_v15:saved});h.run('userDataLoaded=false;appReady=false;handleTimerPrimaryAction()');assert.equal(h.run('saveUserData()'),false);assert.equal(h.storage.get('library_v15'),saved);assert.equal(h.run('timerState.active'),false);
});
test('dates, ratings, goals and sessions are validated before use',()=>{
    const h=harness({library_v15:JSON.stringify({version:15,dailyProgress:{'2026-02-30':500,'invalid':500,'2026-02-28':-10},reviews:{1:{rating:999,comment:'bad'}},personalGoals:[null,{id:1,text:'one'},{id:1,text:'two'}, {id:'bad',text:'three'}],session:{active:true,startTime:'bad'}})});h.run('loadUserData();updateStatsUI()');const data=h.data();assert.deepEqual(data.dailyProgress,{'2026-02-28':0});assert.deepEqual(data.reviews,{});assert.equal(new Set(data.personalGoals.map(goal=>goal.id)).size,3);assert.equal(data.session,null);
});
test('review saving recomputes active read filter',()=>{
    const h=harness();h.run("userData=normalizeUserData({});activeCategories=['✅ Lesið'];applyFilters();currentRating=5;openBookInfo=()=>{};");h.nodes.set('review-text',{value:'literal <script>no</script>'});h.run(`saveReview(${first.id})`);assert.equal(h.run('filteredBooks.length'),1);assert.equal(h.data().reviews[first.id].comment,'literal <script>no</script>');
});
test('active and paused sessions survive reload and stop exactly once',()=>{
    const h=harness();h.run('loadUserData();handleTimerPrimaryAction();timerState.startTime=Date.now()-5000;saveUserData();loadUserData();checkpointTimer();handleTimerPrimaryAction();');assert(h.run('timerState.paused'));assert(h.run('timerState.elapsedBeforePause>=5000'));const elapsed=h.run('timerState.elapsedBeforePause');h.run('loadUserData()');assert.equal(h.run('timerState.elapsedBeforePause'),elapsed);h.run('confirmStopReading()');assert(h.data().totalSeconds>=5);const total=h.data().totalSeconds;h.run('loadUserData();confirmStopReading()');assert.equal(h.data().totalSeconds,total);assert.equal(h.data().session,null);
});
test('midnight sessions allocate reading time to the correct dates',()=>{
    const h=harness();h.run(`userData=normalizeUserData({});timerState=emptyTimerState();timerState.active=true;timerState.startTime=new Date(2026,8,30,23,59,50).getTime();checkpointTimer(new Date(2026,9,1,0,0,10).getTime());timerState.paused=true;confirmStopReading()`);assert.equal(h.data().dailyProgress['2026-09-30'],10);assert.equal(h.data().dailyProgress['2026-10-01'],10);assert.equal(h.data().totalSeconds,20);
});
test('fractional seconds across midnight match the total timer display',()=>{
    const h=harness();h.run('userData=normalizeUserData({});timerState=emptyTimerState();timerState.active=true;timerState.startTime=new Date(2026,8,30,23,59,59,400).getTime();checkpointTimer(new Date(2026,9,1,0,0,0,600).getTime());timerState.paused=true;confirmStopReading()');assert.equal(h.data().totalSeconds,1);assert.equal(Object.values(h.data().dailyProgress).reduce((a,b)=>a+b,0),1);
});
test('local day splitting handles daylight-saving clock changes',()=>{
    for (const [month,day] of [[2,8],[10,1]]) {
        const h=harness();const start=new Date(2026,month,day).getTime();const end=new Date(2026,month,day+1).getTime();
        h.run(`userData=normalizeUserData({});timerState=emptyTimerState();timerState.active=true;timerState.startTime=${start};checkpointTimer(${end});timerState.paused=true;confirmStopReading()`);
        assert.equal(h.data().totalSeconds,(end-start)/1000);
        assert.equal(Object.keys(h.data().dailyProgress).length,1);
        if (process.env.TZ==='America/New_York') assert.equal((end-start)/3600000,month===2?23:25);
    }
});
test('failed stop saves retain session and do not double-count on retry',()=>{
    const h=harness();h.run('userData=normalizeUserData({});handleTimerPrimaryAction();timerState.startTime=Date.now()-5000;localStorage.setItem=()=>{throw Error("quota")};confirmStopReading()');assert.equal(h.data().totalSeconds,0);assert(h.run('timerState.active'));h.ctx.localStorage.setItem=(key,value)=>h.storage.set(key,value);h.run('confirmStopReading()');assert(h.data().totalSeconds>=5);assert(!h.run('timerState.active'));
});
test('daily streak honors the chosen target and yesterday grace period',()=>{
    const h=harness();h.run(`userData=normalizeUserData({});userData.minutesGoal=30;const today=getLocalYYYYMMDD(new Date());const yesterday=new Date();yesterday.setDate(yesterday.getDate()-1);const prior=new Date();prior.setDate(prior.getDate()-2);userData.dailyProgress[today]=600;userData.dailyProgress[getLocalYYYYMMDD(yesterday)]=1800;userData.dailyProgress[getLocalYYYYMMDD(prior)]=1800`);assert.equal(h.run('calculateStreak()'),2);h.run('userData.dailyProgress[today]=1800');assert.equal(h.run('calculateStreak()'),3);h.run('userData.minutesGoal=60');assert.equal(h.run('calculateStreak()'),0);
});
test('weekly and monthly streaks use the same period totals as goal progress',()=>{
    const h=harness();h.run(`userData=normalizeUserData({});userData.minutesGoal=60;userData.goalType='weekly';const date=new Date();date.setDate(date.getDate()-2);userData.dailyProgress[getLocalYYYYMMDD(date)]=3600;`);assert.equal(h.run('calculateStreak()'),3);assert.equal(h.run('getWeeklySeconds()'),3600);h.run("userData.goalType='monthly';userData.dailyProgress={};const start=new Date();start.setDate(1);userData.dailyProgress[getLocalYYYYMMDD(start)]=3600;");assert.equal(h.run('calculateStreak()'),new Date().getDate());
});
test('clearing a weekly/monthly goal returns to the ten-minute daily streak',()=>{
    const h=harness();h.run('userData=normalizeUserData({});userData.goalType="weekly";const date=new Date();date.setDate(date.getDate()-2);userData.dailyProgress[getLocalYYYYMMDD(date)]=600');assert.equal(h.run('calculateStreak()'),0);h.run('userData.goalType="monthly"');assert.equal(h.run('calculateStreak()'),0);
});
test('historical weekly/monthly totals respect year/month boundaries and exclude future dates',()=>{
    const h=harness();h.run('userData=normalizeUserData({dailyProgress:{"2025-12-30":300,"2025-12-31":600,"2026-01-01":900,"2026-01-02":1200}})');assert.equal(h.run('getWeeklySeconds(new Date(2026,0,1))'),1800);assert.equal(h.run('getMonthlySeconds(new Date(2026,0,1))'),900);assert.equal(h.run('getMonthlySeconds(new Date(2025,11,31))'),900);
});
test('HTML escaping treats hostile text as literal text',()=>{
    const h=harness();assert.equal(h.run('escapeHTML('+JSON.stringify('<img src=x onerror="evil()"> & \'test\'')+')'),'&lt;img src=x onerror=&quot;evil()&quot;&gt; &amp; &#39;test&#39;');
});
test('fallback disables the image error handler before assigning local asset',()=>{
    const h=harness();const removed=[];const img={onerror:()=>{},classList:{remove(x){removed.push(x)}},parentElement:{classList:{remove(x){removed.push(x)}}}};h.ctx.img=img;h.run('handleCoverError(img)');assert.equal(img.onerror,null);assert.equal(img.src,'Resources/Assets/cover-placeholder.svg');assert.deepEqual(removed,['opacity-0','shimmer-placeholder']);
});
console.log(`${passed} regression tests passed`);

test('extension schema preserves old totals without inventing dates or sessions',()=>{
 const h=harness({library_v14:JSON.stringify({read:[first.title],totalSeconds:7200})});h.run('loadUserData()');assert.equal(h.data().totalSeconds,7200);assert.deepEqual(h.data().sessions,[]);assert.deepEqual(h.data().completedDates,{});assert(h.data().achievements.first);
});
test('new completion dates persist and old history stays unknown',()=>{
 const h=harness();h.run(`loadUserData();toggleRead(${first.id});loadUserData()`);assert.equal(h.data().completedDates[first.id],h.run('getLocalYYYYMMDD(new Date())'));h.run(`toggleRead(${first.id})`);assert.equal(h.data().read.length,0);
});
test('saved sessions commit once and failed writes roll back sessions and unlocks',()=>{
 const h=harness();h.run('loadUserData();handleTimerPrimaryAction();timerState.startTime=Date.now()-36001000;localStorage.setItem=()=>{throw Error("quota")};confirmStopReading()');assert.equal(h.data().sessions.length,0);assert(!h.data().achievements['10-hours']);h.ctx.localStorage.setItem=(k,v)=>h.storage.set(k,v);h.run('confirmStopReading();confirmStopReading()');assert.equal(h.data().sessions.length,1);assert(h.data().achievements['10-hours']);
});
test('backup parser accepts v14 and complete envelope; rejects malformed/newer files',()=>{
 const h=harness();assert.equal(h.run('parseBackup(JSON.stringify({read:[],liked:[],totalSeconds:90})).data.totalSeconds'),90);
 for(const bad of ['null','[]','{bad','{}',JSON.stringify({version:16,read:[]}),JSON.stringify({read:{}}),JSON.stringify({version:15,read:['title']}),JSON.stringify({read:[],dailyProgress:{'2026-02-30':90}}),JSON.stringify({read:[],reviews:{1:{rating:6,comment:''}}}),JSON.stringify({read:[],personalGoals:[{text:9}]}),JSON.stringify({read:[],sessions:[{}]}),JSON.stringify({format:'bokasafn-backup',backupVersion:3,data:{read:[]}})])assert.throws(()=>h.run('parseBackup('+JSON.stringify(bad)+')'));
 const data=h.run('JSON.stringify(normalizeUserData({version:15,read:[1],sessions:[{id:"abc",date:"2026-01-01",seconds:60}]}))');assert.equal(h.run('parseBackup('+JSON.stringify(JSON.stringify({format:'bokasafn-backup',backupVersion:1,data:JSON.parse(data),preferences:{theme:'purple'}}))+').theme'),'purple');
});
test('safe merge is idempotent, retains conflicting existing reviews/goals and unknown titles',()=>{
 const h=harness();h.run(`const a=normalizeUserData({version:15,read:[1],reviews:{1:{rating:5,comment:'local'}},minutesGoal:30,totalSeconds:100,dailyProgress:{'2026-01-01':100},personalGoals:[{id:1,text:'one',completed:false}],sessions:[{id:'a',date:'2026-01-01',seconds:100}]});const b=normalizeUserData({version:15,read:[2],reviews:{1:{rating:1,comment:'old'},2:{rating:4,comment:'new'}},minutesGoal:10,totalSeconds:150,dailyProgress:{'2026-01-01':150},personalGoals:[{id:1,text:'two',completed:false}],sessions:[{id:'a',date:'2026-01-01',seconds:100}]});userData=mergeReadingData(a,b)`);assert.deepEqual(h.data().read,[1,2]);assert.equal(h.data().reviews[1].comment,'local');assert.equal(h.data().minutesGoal,30);assert.equal(h.data().totalSeconds,150);assert.equal(h.data().sessions.length,1);assert.equal(h.data().personalGoals.length,2);const before=h.data();h.run('userData=mergeReadingData(userData,b)');assert.deepEqual(h.data(),before);
});
test('longest streak, active days and current streak use goals and exclude future dates',()=>{
 const h=harness();h.run('userData=normalizeUserData({version:15,minutesGoal:20,dailyProgress:{"2025-12-30":1200,"2025-12-31":1200,"2026-01-01":1200,"2026-01-02":600,"2099-01-01":9000}})');const m=JSON.parse(h.run('JSON.stringify(activitySummary(new Date(2026,0,3)))'));assert.equal(m.longest,3);assert.equal(m.active,4);assert.equal(m.recordSeconds,1200);
});
test('achievements use completed pages and unlock permanently',()=>{
 const h=harness();h.run('userData=normalizeUserData({version:15,read:allBooks.map(b=>b.id),totalSeconds:36000});refreshMilestones()');assert(h.data().achievements['1000-pages']);assert(h.data().achievements['five-genres']);h.run('userData.read=[];refreshMilestones()');assert(h.data().achievements.first);
});
test('challenges count new completions and ignore unknown historical completion dates',()=>{
 const h=harness();h.run(`userData=normalizeUserData({version:15,read:[${first.id}],completedDates:{${first.id}:'2026-01-02'},challenges:[{id:'c',title:'books',kind:'books',target:1,start:'2026-01-01',end:'2026-01-31',baseline:[]}]});refreshMilestones()`);assert(h.data().challenges[0].completed);h.run('userData.completedDates={};userData.challenges[0].completed=null');assert.equal(h.run('challengeProgress(userData.challenges[0])'),0);
});
test('minute challenges subtract activity from before their start on the same day',()=>{
 const h=harness();h.run('userData=normalizeUserData({version:15,dailyProgress:{"2026-01-01":3600},challenges:[{id:"c",title:"minutes",kind:"minutes",target:30,start:"2026-01-01",baselineSeconds:3000}]})');assert.equal(h.run('challengeProgress(userData.challenges[0])'),10);
});
test('recommendations are deterministic, explainable and exclude read/disliked books',()=>{
 const h=harness();h.run('userData=normalizeUserData({version:15,read:[allBooks[0].id],reviews:{[allBooks[1].id]:{rating:1,comment:"no"}},liked:[allBooks[2].id]})');const rec=JSON.parse(h.run('JSON.stringify(recommendations())'));assert(rec.length);assert(rec.every(r=>r.book.id!==catalog[0].id&&r.book.id!==catalog[1].id));assert.equal(rec[0].book.id,catalog[2].id);assert.deepEqual(rec,JSON.parse(h.run('JSON.stringify(recommendations())')));h.run('userData=normalizeUserData({})');assert.equal(h.run('recommendations().length'),6);
});
test('advanced filters combine and random picker handles empty and singleton sets',()=>{
 const h=harness();h.run(`userData=normalizeUserData({version:15,read:[${first.id}],liked:[${first.id}],reviews:{${first.id}:{rating:5,comment:''}}})`);h.ctx.book=first;assert(h.run('matchesAdvanced(book,{state:"read",min:1,max:10000,rating:4,author:book.author,category:book.categories[0]})'));assert(!h.run('matchesAdvanced(book,{state:"unread"})'));assert.equal(h.run('chooseRandom([])'),null);assert.equal(h.run('chooseRandom([book],()=>0.99).id'),first.id);
});
console.log(`${passed} total regression tests passed`);
test('corrupt extension fields recover safely without losing valid legacy progress',()=>{
 const h=harness({library_v15:JSON.stringify({version:15,totalSeconds:90,read:[first.id],sessions:[null,{id:'bad',date:'wrong',seconds:90}],completedDates:{bad:'not-date'},challenges:[{},null],achievements:{first:'not-date'}})});h.run('loadUserData();updateStatsUI()');assert.equal(h.data().totalSeconds,90);assert.deepEqual(h.data().sessions,[]);assert.deepEqual(h.data().challenges,[]);assert(h.data().achievements.first);
});
test('weekly and monthly longest streaks match their goal definitions across boundaries',()=>{
 const h=harness();h.run('userData=normalizeUserData({version:15,minutesGoal:60,goalType:"weekly",dailyProgress:{"2025-12-30":3600}})');assert.equal(h.run('activitySummary(new Date(2026,0,3)).longest'),5);h.run('userData.goalType="monthly"');assert.equal(h.run('activitySummary(new Date(2026,0,3)).longest'),2);assert.equal(h.run('activitySummary(new Date(2026,0,3)).current'),0);
});
console.log(`${passed} total regression tests passed`);
test('built-in challenges block repeat joins, allow a new month and completed nonmonthly retries',()=>{
 const h=harness();h.run('userData=normalizeUserData({version:15,challenges:[{id:"c",title:"Þrjár bækur í þessum mánuði",kind:"books",target:3,start:"2026-10-01",end:"2026-10-31",baseline:[]}]})');assert(h.run('existingBuiltInChallenge("month",new Date(2026,9,6))'));assert.equal(h.run('existingBuiltInChallenge("month",new Date(2026,10,1))'),null);h.run('userData.challenges[0].completed="2026-10-06"');assert(h.run('existingBuiltInChallenge("month",new Date(2026,9,6))'));
 h.run('userData.challenges=[{id:"p",kind:"pages",title:"500 blaðsíður",target:500,start:"2026-10-06",end:null,baseline:[],completed:null}]');assert(h.run('existingBuiltInChallenge("pages")'));h.run('userData.challenges[0].completed="2026-10-06"');assert.equal(h.run('existingBuiltInChallenge("pages")'),null);assert.equal(h.run('existingBuiltInChallenge("invalid")'),null);
});
test('identical challenge cards group without deleting stored records or combining different progress',()=>{
 const h=harness();h.run('userData=normalizeUserData({version:15,challenges:[{id:"a",title:"Same",kind:"books",target:3,start:"2026-10-01",baseline:[1,2]},{id:"b",title:"Same",kind:"books",target:3,start:"2026-10-01",baseline:[2,1]},{id:"c",title:"Same",kind:"books",target:3,start:"2026-10-01",baseline:[1]},{id:"d",title:"Same",kind:"books",target:3,start:"2026-10-01",baseline:[1,2],completed:"2026-10-06"}]})');assert.equal(h.run('challengeDisplayGroups(userData.challenges).length'),3);assert.equal(h.run('challengeDisplayGroups(userData.challenges)[0].ids.length'),2);assert.equal(h.data().challenges.length,4);h.run('saveUserData();loadUserData()');assert.equal(h.data().challenges.length,4);
});
console.log(`${passed} total regression tests passed`);
test('first fantasy and author challenges recognise already-read legacy books without inventing dates',()=>{
 const h=harness();const fantasy=catalog.find(b=>b.categories.includes('Fantasía'));h.ctx.fantasy=fantasy;
 h.run('userData=normalizeUserData({version:15,read:[fantasy.id],challenges:[{id:"f",title:"Lestu fantasíubók",kind:"fantasy",target:1,start:"2026-10-06",baseline:[fantasy.id]},{id:"a",title:"Uppgötvaðu nýjan höfund",kind:"author",target:1,start:"2026-10-06",baseline:[fantasy.id]}]});refreshMilestones()');assert.equal(h.run('challengeProgress(userData.challenges[0])'),1);assert.equal(h.run('challengeProgress(userData.challenges[1])'),1);assert(h.data().challenges.every(c=>c.completed));assert.deepEqual(h.data().completedDates,{});h.run('saveUserData();loadUserData()');assert(h.data().challenges.every(c=>c.completed));
});
test('repeat discovery challenges need new reading and history mode survives backup and reload',()=>{
 const h=harness();const fantasy=catalog.find(b=>b.categories.includes('Fantasía'));h.ctx.fantasy=fantasy;
 h.run('userData=normalizeUserData({version:15,read:[fantasy.id],challenges:[{id:"f",title:"Lestu fantasíubók",kind:"fantasy",target:1,start:"2026-10-06",baseline:[fantasy.id],historyMode:"since-start"},{id:"a",title:"Uppgötvaðu nýjan höfund",kind:"author",target:1,start:"2026-10-06",baseline:[fantasy.id],historyMode:"since-start"}]});refreshMilestones()');assert(h.data().challenges.every(c=>!c.completed));h.run('saveUserData();loadUserData()');assert(h.data().challenges.every(c=>c.historyMode==='since-start'));assert.equal(h.run('parseBackup(JSON.stringify({format:"bokasafn-backup",backupVersion:1,data:userData})).data.challenges[0].historyMode'),'since-start');
 h.run('const next=allBooks.find(b=>b.author!==fantasy.author);userData.read.push(next.id);userData.completedDates[next.id]=getLocalYYYYMMDD(new Date());refreshMilestones()');assert(h.data().challenges[1].completed);
});
console.log(`${passed} total regression tests passed`);
test('one-line backups preserve full Unicode, unusual text, storage and versioned data exactly',()=>{
 const h=harness({'library_v14':'original \n Þæö 😀','library_v15_recovery_1':'{corrupt original}','bokasafn-extra':'"\\ weird"','unrelated':'keep'});h.ctx.payload='Þú átt ævintýri „æöðþ“ 😀 中文 \n\r\t " \\ \u2028\u2029 \u0000 \ud800';h.run('userData=normalizeUserData({version:15,read:[1],liked:[2],reviews:{1:{rating:5,comment:payload,date:"6.10.2026"}},personalGoals:[{id:1,text:payload,completed:true}],totalSeconds:123,dailyProgress:{"2026-10-06":123}});saveUserData();var snapshot=createReadingBackup();var line=encodeBackupLine(snapshot)');const line=h.run('line');assert(line.startsWith('BOKASAFN:1:'));assert.equal(line.startsWith('bokasafn:'),false);assert(!/[\r\n\u2028\u2029]/.test(line));assert.deepEqual(JSON.parse(h.run('decodeBackupLine(line)')),JSON.parse(h.run('JSON.stringify(snapshot)')));assert.equal(h.run('parseBackupLine(line).data.reviews[1].comment'),h.ctx.payload);assert.equal(h.run('parseBackupLine(line).raw.storage.local.library_v14'),'original \n Þæö 😀');assert(!h.run('Object.hasOwn(snapshot.storage.local,"unrelated")'));
});
test('integrity checks reject corrupted, incomplete, multiline and unsupported backups',()=>{
 const h=harness();h.run('userData=normalizeUserData({});var line=encodeBackupLine(createReadingBackup())');const line=h.run('line');for(const bad of ['', 'wrong',line.replace('BOKASAFN:', 'bokasafn:'),line.slice(0,-3),line.replace(':1:',':9:'),line+'\n',line+'=',line.replace(/:[0-9a-f]{8}:/,':00000000:'),line.slice(0,-1)+(line.endsWith('A')?'B':'A')])assert.throws(()=>h.run('parseBackupLine('+JSON.stringify(bad)+')'));
 h.run('var invalid=createReadingBackup();invalid.data.reviews={1:{rating:9,comment:"bad"}}');assert.throws(()=>h.run('parseBackupLine(encodeBackupLine(invalid))'));
});
test('large backups exceed old size limits without truncation',()=>{
 const h=harness();h.ctx.longText='Æ😀"\\\n'.repeat(800000);h.run('userData=normalizeUserData({version:15,reviews:{1:{rating:4,comment:longText}},personalGoals:[{id:1,text:longText,completed:false}]});var line=encodeBackupLine(createReadingBackup())');assert(h.run('line.length')>5000000);assert.equal(h.run('parseBackupLine(line).data.reviews[1].comment'),h.ctx.longText);assert.equal(h.run('parseBackupLine(line).data.personalGoals[0].text'),h.ctx.longText);
});
test('storage reset removes every app namespace and all recovery copies while leaving unrelated data',()=>{
 const h=harness({'library_v14':'old','library_v15':'saved','library_v15_recovery':'recover','library_import_backup_old':'backup','library_v99':'future','bokasafn-theme':'green','bokasafn-other':'future','unrelated':'keep'});h.run('clearAllUserStorage()');assert.equal(h.storage.size,1);assert.equal(h.storage.get('unrelated'),'keep');
});
test('reset failure restores removed data and does not claim success',()=>{
 const h=harness({'library_v14':'old','library_v15':'saved','unrelated':'keep'});h.ctx.localStorage.removeItem=k=>{if(k==='library_v15')throw Error('denied');h.storage.delete(k)};assert.throws(()=>h.run('clearAllUserStorage()'));assert.equal(h.storage.get('library_v14'),'old');assert.equal(h.storage.get('library_v15'),'saved');
});
test('full snapshots reject unrelated storage keys and older JSON files still import',()=>{
 const h=harness();h.run('userData=normalizeUserData({});var backup=createReadingBackup();backup.storage.local.unrelated="overwrite"');assert.throws(()=>h.run('parseBackup(JSON.stringify(backup))'));assert.equal(h.run('parseBackup(JSON.stringify({format:"bokasafn-backup",backupVersion:1,data:{version:15,read:[1]}})).data.read[0]'),1);assert.equal(h.run('parseBackup(JSON.stringify({read:[allBooks[0].title]})).data.read[0]'),first.id);
});
console.log(`${passed} total regression tests passed`);
test('a stale tab cannot resurrect user data after another tab deletes or replaces it',()=>{
 const h=harness();h.run('loadUserData();userData.read=[1];saveUserData();localStorage.removeItem(LIBRARY_STORAGE_KEY)');assert.equal(h.run('saveUserData()'),false);assert(!h.storage.has('library_v15'));h.storage.set('library_v15',JSON.stringify({version:15,read:[]}));assert.equal(h.run('saveUserData()'),false);assert.deepEqual(JSON.parse(h.storage.get('library_v15')).read,[]);
});
console.log(`${passed} total regression tests passed`);
