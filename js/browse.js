// Discovery indexes are derived only from the active catalog. No user schema changes.
function browseFold(value) {
    return String(value ?? '').normalize('NFKD').toLocaleLowerCase('is')
        .replace(/\p{M}/gu, '').replace(/ð/g, 'd').replace(/þ/g, 'th').replace(/æ/g, 'ae');
}
function authorIdentityKey(value) {
    return String(value).normalize('NFKC').toLocaleLowerCase('is').replace(/[^\p{L}\p{N}]/gu, '');
}
let browseIndex = {series: new Map(), authors: new Map()};
let browseState = {kind: 'series', id: '', limit: 36};
function buildBrowseIndex(books = allBooks, registry = globalThis.BOKASAFN_AUTHORS || []) {
    const index = {series: new Map(), authors: new Map()};
    const known = new Map(registry.flatMap(a => [a.name, ...(a.aliases || [])].map(n => [authorIdentityKey(n), a])));
    for (const b of books) {
        const names = b.author.split(', ').filter(Boolean);
        for (const [i, name] of names.entries()) {
            const a = known.get(authorIdentityKey(name));
            const id = b.authorIds?.[i] || a?.id || authorIdentityKey(name);
            if (!index.authors.has(id)) index.authors.set(id, {id, name: a?.name || name, aliases: a?.aliases || [], books: []});
            const entry = index.authors.get(id);
            if (!entry.books.some(x => x.id === b.id)) entry.books.push(b);
        }
        if (b.series) {
            if (!index.series.has(b.series.id)) index.series.set(b.series.id, {...b.series, books: []});
            index.series.get(b.series.id).books.push(b);
        }
    }
    for (const s of index.series.values()) s.books.sort(seriesBookOrder);
    browseIndex = index;
    return index;
}
function seriesBookOrder(a, b) {
    return (a.series?.number ?? Infinity) - (b.series?.number ?? Infinity) || a.title.localeCompare(b.title, 'is') || a.id - b.id;
}
function seriesProgress(series, data = userData) {
    const read = new Set(data.read);
    return {read: series.books.filter(b => read.has(b.id)).length, available: series.books.length};
}
function availableBookCount(count) { return `${count} ${count === 1 ? 'bók' : 'bækur'} í safninu`; }
function seriesProgressText(progress) { return `${progress.read} af ${progress.available} ${progress.available === 1 ? 'bók lesin' : 'bókum lesnar'}`; }
function seriesNeighbors(book) {
    if (!book?.series || book.series.number == null) return {};
    const books = browseIndex.series.get(book.series.id)?.books.filter(b => b.series.number != null) || [];
    const i = books.findIndex(b => b.id === book.id);
    return i < 0 ? {} : {previous: books[i-1], next: books[i+1]};
}
function catalogMatchesSearch(book, query) {
    return browseFold(book.title + '\n' + book.author + '\n' + (book.series?.name || '')).includes(browseFold(query));
}
function browseSuggestions(query) {
    const q = browseFold(query).trim();
    if (!q) return [];
    return [
        ...allBooks.filter(b => catalogMatchesSearch(b, q)).slice(0,5).map(b => ({type:'book', id:b.id, name:b.title, label:'Bók'})),
        ...[...browseIndex.series.values()].filter(s => browseFold(s.name).includes(q)).slice(0,3).map(s => ({type:'series',id:s.id,name:s.name,label:'Bókaflokkur'})),
        ...[...browseIndex.authors.values()].filter(a => browseFold([a.name,...a.aliases].join(' ')).includes(q)).slice(0,3).map(a => ({type:'author',id:a.id,name:a.name,label:'Höfundur'}))
    ];
}
function renderBrowseSuggestions(box, query) {
    const results = browseSuggestions(query);
    box.innerHTML = results.map(r => `<li role="button" tabindex="0" data-result-type="${r.type}" data-result-id="${escapeHTML(r.id)}" onclick="selectBrowseSuggestion(this)" class="px-6 py-4 hover:bg-indigo-50 cursor-pointer text-sm font-bold border-b border-slate-50"><span class="browse-result-type">${r.label}</span> ${escapeHTML(r.name)}</li>`).join('');
    box.classList.toggle('hidden', !results.length);
}
function selectBrowseSuggestion(node) {
    if (node.dataset.resultType === 'book') selectSug(Number(node.dataset.resultId));
    else openBrowse(node.dataset.resultType, node.dataset.resultId);
    document.getElementById('search-suggestions').classList.add('hidden');
}
function browseURL(kind, id = '') {
    const url = new URL(location.href);
    for (const key of ['book','series','author','browse']) url.searchParams.delete(key);
    url.searchParams.set(id ? kind : 'browse', id || kind);
    return url;
}
function openBrowse(kind, id = '', push = true) {
    if (!['series','author'].includes(kind)) return;
    if (activeDialog) {
        const before = routeChange; routeChange = true;
        closeModal(activeDialog.modal.id, DIALOG_CONTENT_IDS[activeDialog.modal.id]); routeChange = before;
    }
    if (push) history.pushState(null, '', browseURL(kind,id));
    browseState = {kind,id,limit:36};
    showPage('browse');
    const entry = id && browseIndex[kind === 'series' ? 'series' : 'authors'].get(id);
    const title = id ? entry?.name || 'Fannst ekki' : kind === 'series' ? 'Bókaflokkar' : 'Höfundar';
    document.getElementById('browse-title').textContent = title;
    document.getElementById('browse-intro').textContent = id ? entry ? availableBookCount(entry.books.length) : 'Þessi tengill fannst ekki í safninu.' : 'Finndu næstu bók eftir höfundi eða bókaflokki.';
    document.getElementById('browse-controls').innerHTML = `${id ? `<button type="button" class="feature-button secondary" onclick="openBrowse('${kind}')">${kind === 'series' ? 'Allir bókaflokkar' : 'Allir höfundar'}</button>` : ''}<label class="feature-field">${id ? 'Leita í bókum' : kind === 'series' ? 'Leita að bókaflokki' : 'Leita að höfundi'}<input id="browse-search" type="search" oninput="refreshBrowse(true)"></label>${id ? `<label class="feature-field">Lestrarstaða<select id="browse-state" onchange="refreshBrowse(true)"><option value="">Allar bækur</option><option value="read">Lesið</option><option value="unread">Ólesið</option><option value="wishlist">Óskalisti</option></select></label><label class="feature-field">Flokkur<select id="browse-category" onchange="refreshBrowse(true)"><option value="">Allir flokkar</option>${[...new Set((entry?.books || []).flatMap(b => b.categories))].sort((a,b)=>a.localeCompare(b,'is')).map(c=>`<option>${escapeHTML(c)}</option>`).join('')}</select></label><label class="feature-field">Röðun<select id="browse-sort" onchange="refreshBrowse(true)">${kind==='series'?'<option value="series">Lestrarröð</option>':''}<option value="title">Titill</option><option value="pages-asc">Fæstar blaðsíður</option><option value="pages-desc">Flestar blaðsíður</option></select></label>` : ''}`;
    refreshBrowse();
    if (push) document.getElementById('browse-title').focus();
}
function browseBookCards(books) {
    return books.map(b => `<article class="browse-book" data-browse-book="${b.id}"><button class="browse-cover" type="button" onclick="openBookInfo(${b.id})" aria-label="Opna ${escapeHTML(b.title)}"><img src="${escapeHTML(b.cover)}" alt="Bókarkápa: ${escapeHTML(b.title)}" loading="lazy" decoding="async" onerror="handleCoverError(this)"></button><div><h3><button type="button" onclick="openBookInfo(${b.id})">${escapeHTML(b.title)}</button></h3><p>${escapeHTML(b.author)}</p>${b.series?`<p>${b.series.number==null?'Bókaröð óstaðfest':`Bók ${b.series.number}`}</p>`:''}<div class="feature-actions"><button type="button" class="feature-button secondary" data-browse-action="read" data-book-id="${b.id}" aria-pressed="${userData.read.includes(b.id)}" onclick="toggleRead(${b.id})">${userData.read.includes(b.id)?'Lesið':'Merkja lesið'}</button><button type="button" class="feature-button secondary" data-browse-action="like" data-book-id="${b.id}" aria-pressed="${userData.liked.includes(b.id)}" onclick="toggleLike(${b.id})">Óskalisti</button></div></div></article>`).join('');
}
function refreshBrowse(reset = false) {
    const container = document.getElementById('browse-results');
    if (!container) return;
    if (reset) browseState.limit = 36;
    const {kind,id} = browseState;const query=browseFold(document.getElementById('browse-search')?.value || '');
    const entries=browseIndex[kind==='series'?'series':'authors'];let items;
    const entry=entries.get(id);
    if (id) {
        const state=document.getElementById('browse-state')?.value;const category=document.getElementById('browse-category')?.value;const sort=document.getElementById('browse-sort')?.value;
        items=(entry?.books || []).filter(b=>catalogMatchesSearch(b,query) && (!category || b.categories.includes(category)) && (!state || state==='read' && userData.read.includes(b.id) || state==='unread' && !userData.read.includes(b.id) || state==='wishlist' && userData.liked.includes(b.id))).slice();
        items.sort((a,b)=>sort==='series'?seriesBookOrder(a,b):sort?.startsWith('pages')?(!a.pages)-(!b.pages) || (sort==='pages-desc'?-1:1)*((Number(a.pages)||0)-(Number(b.pages)||0)) || a.id-b.id:a.title.localeCompare(b.title,'is') || a.id-b.id);
        container.innerHTML=browseBookCards(items.slice(0,browseState.limit));
        const related=document.getElementById('browse-related');
        if(kind==='series' && entry) {
            const progress=seriesProgress(entry);const names=[...new Set(entry.books.flatMap(b=>b.author.split(', ')))];
            related.innerHTML=`<p>${escapeHTML(names.join(' · '))}</p><p role="status">${seriesProgressText(progress)} í safninu</p><progress max="${progress.available}" value="${progress.read}" aria-label="Lestrarframvinda"></progress><p class="feature-note">${entry.total?`Forlagið tilgreinir ${entry.total} bækur í þessum bókaflokki. `:''}Hér birtast aðeins bækur sem eru í safninu.${entry.books.some(b=>b.series.number==null)?' Bækur með óstaðfesta röð birtast aftast; ekki er gert ráð fyrir röðun þeirra.':''}</p>`;
        } else related.innerHTML=entry?`<h3>Bókaflokkar höfundar</h3><div class="feature-actions">${[...new Set(entry.books.filter(b=>b.series).map(b=>b.series.id))].map(s=>browseLink('series',s,browseIndex.series.get(s).name)).join('') || '<p>Enginn staðfestur bókaflokkur í safninu.</p>'}</div>`:'';
    } else {
        items=[...entries.values()].filter(x=>browseFold([x.name,...(x.aliases || [])].join(' ')).includes(query)).sort((a,b)=>a.name.localeCompare(b.name,'is'));
        document.getElementById('browse-related').innerHTML='';
        container.innerHTML=items.slice(0,browseState.limit).map(x=>{const p=kind==='series'?seriesProgress(x):null;return `<article class="browse-tile"><div class="browse-cover-stack" aria-hidden="true">${x.books.slice(0,3).map(b=>`<img alt="" src="${escapeHTML(b.cover)}" loading="lazy" decoding="async" onerror="handleCoverError(this)">`).join('')}</div><h3>${browseLink(kind,x.id,x.name)}</h3><p>${availableBookCount(x.books.length)}</p>${p?`<p>${escapeHTML([...new Set(x.books.map(b=>b.author))].join(' · '))}</p><p>${seriesProgressText(p)}</p>`:''}</article>`;}).join('');
    }
    document.getElementById('browse-count').textContent=`Sýnir ${Math.min(items.length,browseState.limit)} af ${items.length} ${id?'bókum':kind==='series'?'bókaflokkum':'höfundum'}`;
    if (!items.length) container.innerHTML='<p>Engar niðurstöður. Prófaðu aðra leit eða síur.</p>';
    document.getElementById('browse-more').hidden=items.length<=browseState.limit;
}
function browseLink(kind,id,name) {
    return `<a class="browse-link" href="?${kind}=${encodeURIComponent(id)}" data-browse-kind="${kind}" data-browse-id="${escapeHTML(id)}" onclick="if(!event.ctrlKey&&!event.metaKey&&!event.shiftKey&&!event.altKey){event.preventDefault();openBrowse(this.dataset.browseKind,this.dataset.browseId)}">${escapeHTML(name)}</a>`;
}
function decorateBrowseBook(id) {
    const book=allBooks.find(b=>b.id===id);if(!book)return;
    const authors=(book.authorIds || []).map(id=>browseIndex.authors.get(id)).filter(Boolean);
    let html=`<section class="book-browse-links" aria-label="Höfundar og bókaflokkur"><div class="feature-actions">${authors.map(a=>browseLink('author',a.id,a.name)).join('')}</div>`;
    if(book.series) {
        const s=book.series;const n=seriesNeighbors(book);
        html+=`<p>Bókaflokkur: ${browseLink('series',s.id,s.name)}${s.number!=null?` — Bók ${s.number}${s.total?` af ${s.total}`:''}`:' — Bókaröð óstaðfest'}</p><div class="feature-actions">${n.previous?`<button type="button" class="feature-button secondary" onclick="openBookInfo(${n.previous.id})">Fyrri bók í safninu: ${escapeHTML(n.previous.title)}</button>`:''}${n.next?`<button type="button" class="feature-button secondary" onclick="openBookInfo(${n.next.id})">Næsta bók í safninu: ${escapeHTML(n.next.title)}</button>`:''}</div>`;
    }
    document.getElementById('modal-inner-content').insertAdjacentHTML('beforeend',html+'</section>');
}
function applyBrowseRoute() {
    const params=new URL(location.href).searchParams;const kind=params.has('series')?'series':params.has('author')?'author':params.get('browse');
    if(['series','author'].includes(kind))openBrowse(kind,params.get(kind)||'',false);
    else if(document.getElementById('browse-page')?.classList.contains('active'))showPage('library');
}
function installBrowse() {
    if (!window.featuresReady) {setTimeout(installBrowse,50);return;}
    buildBrowseIndex();
    const page=document.createElement('section');page.id='browse-page';page.className='page-container hidden';
    page.innerHTML='<div class="feature-panel"><h2 id="browse-title" tabindex="-1"></h2><p id="browse-intro"></p><div id="browse-controls" class="feature-fields"></div><div id="browse-related"></div><p id="browse-count" role="status" aria-live="polite"></p><div id="browse-results" class="browse-grid"></div><button type="button" id="browse-more" class="feature-button" onclick="browseState.limit+=36;refreshBrowse()">Sýna fleiri</button></div>';
    document.querySelector('main').appendChild(page);
    const originalStats=window.updateStatsUI;
    window.updateStatsUI=function(){
        const focused=document.activeElement?.dataset?.browseAction;const id=document.activeElement?.dataset?.bookId;
        originalStats();
        if(document.getElementById('browse-page').classList.contains('active')) {
            refreshBrowse();
            if(focused && id)document.querySelector(`[data-browse-action="${focused}"][data-book-id="${id}"]`)?.focus({preventScroll:true});
        }
    };
    window.browseReady=true;applyBookRoute();
}
document.addEventListener('DOMContentLoaded',installBrowse);
