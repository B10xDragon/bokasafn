let allBooks = [];
const BOOK_BATCH_SIZE = 60;
let renderedBookLimit = BOOK_BATCH_SIZE;
let bookFilterSignature = '';
let bookRenderSuspended = 0;
        let filteredBooks = [];
        let searchQuery = '';
        let activeCategories = [];
        let currentRating = 0;
        
        let userData = { 
            liked: [], 
            read: [], 
            totalSeconds: 0, 
            dailyProgress: {},
            minutesGoal: 0,
            goalType: 'daily',
            personalGoals: [],
            reviews: {}
        };
        
        let timerState = emptyTimerState();
        let appReady = false;
        const startupRegions = [document.querySelector('nav'), document.querySelector('main')].filter(Boolean);
        startupRegions.forEach(region => {
            region.inert = true;
            region.setAttribute('aria-busy', 'true');
        });

        // --- Defensive Safe DOM Manipulation Utilities ---
        const setInnerHTML = (id, html) => {
            const el = document.getElementById(id);
            if (el) {
                el.innerHTML = html;
            } else {
                console.warn(`Element with ID '${id}' was not found in DOM.`);
            }
        };

        const setInnerText = (id, text) => {
            const el = document.getElementById(id);
            if (el) {
                el.innerText = text;
            } else {
                console.warn(`Element with ID '${id}' was not found in DOM.`);
            }
        };

        const safeToggleClass = (id, className, force) => {
            const el = document.getElementById(id);
            if (el) {
                el.classList.toggle(className, force);
            }
        };

        window.onload = async () => {
            const catalogLoaded = await fetchBooks();
            loadUserData();
            if (catalogLoaded) applyFilters();
            syncGoalUI();
            updateStatsUI();
            appReady = true;
            startupRegions.forEach(region => {
                region.inert = false;
                region.setAttribute('aria-busy', 'false');
            });
        };

        function getLocalYYYYMMDD(d) {
            const year = d.getFullYear();
            const month = String(d.getMonth() + 1).padStart(2, '0');
            const day = String(d.getDate()).padStart(2, '0');
            return `${year}-${month}-${day}`;
        }

        function shuffleArray(array) {
            for (let i = array.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [array[i], array[j]] = [array[j], array[i]];
            }
        }

        // Streak útreikningur
        function calculateStreak() {
            if (typeof activitySummary === 'function') return activitySummary().current;
            // Weekly targets retain their rolling-seven-day meaning. Monthly targets
            // use calendar-month-to-date totals. The streak counts days meeting the
            // selected period target, rather than silently imposing a daily target.
            const threshold = userData.minutesGoal > 0 ? userData.minutesGoal * 60 : 600;
            function reached(date) {
                if (userData.minutesGoal > 0 && userData.goalType === 'weekly') return getWeeklySeconds(date) >= threshold;
                if (userData.minutesGoal > 0 && userData.goalType === 'monthly') return getMonthlySeconds(date) >= threshold;
                return (userData.dailyProgress[getLocalYYYYMMDD(date)] || 0) >= threshold;
            }
            let date = new Date();
            let streak = 0;
            if (!reached(date)) date.setDate(date.getDate() - 1);
            // Every qualifying period must contain a saved reading day.
            const dates = Object.keys(userData.dailyProgress).sort();
            if (!dates.length) return 0;
            const earliest = dates[0];
            while (getLocalYYYYMMDD(date) >= earliest && reached(date)) {
                streak++;
                date.setDate(date.getDate() - 1);
            }
            return streak;
        }

        function getWeeklySeconds(now = new Date()) {
            let total = 0;
            for (let i = 0; i < 7; i++) {
                const d = new Date(now);
                d.setDate(now.getDate() - i);
                const ds = getLocalYYYYMMDD(d);
                total += userData.dailyProgress[ds] || 0;
            }
            return total;
        }

        function getMonthlySeconds(now = new Date()) {
            let total = 0;
            const currentMonth = now.getMonth();
            const currentYear = now.getFullYear();
            for (const dateStr in userData.dailyProgress) {
                const [year, month, day] = dateStr.split('-').map(Number);
                if (year === currentYear && (month - 1) === currentMonth && dateStr <= getLocalYYYYMMDD(now)) {
                    total += userData.dailyProgress[dateStr];
                }
            }
            return total;
        }

        async function fetchBooks() {
            try {
                const response = await fetch('Resources/books.json', { cache: 'no-store' });
                if (!response.ok) throw new Error(`HTTP ${response.status}`);

                const books = await response.json();

if (!Array.isArray(books)) {
    throw new Error('books.json verður að innihalda fylki af bókum.');
}

books.sort((a, b) => Number(a.id) - Number(b.id));
                allBooks = books.filter(book => book && Number.isSafeInteger(Number(book.id)) && Number(book.id) >= 0).map(book => ({
                    id: Number(book.id),
                    title: String(book.title || '').trim(),
                    author: String(book.author || '').trim(),
                    categories: Array.isArray(book.categories) && book.categories.length
                        ? [...new Set(book.categories.map(c => String(c).trim()).map(c => c === 'Fantasia' ? 'Fantasía' : c).filter(Boolean))]
                        : ['Almennt'],
                    description: String(book.description || '').trim(),
                    cover: String(book.cover || '').trim(),
                    pages: Number.isFinite(Number(book.pages)) && Number(book.pages) > 0 ? Number(book.pages) : '',
                    publicationYear: Number.isInteger(book.publicationYear) ? book.publicationYear : null,
                    sourceURL: typeof book.sourceURL === 'string' ? book.sourceURL : '',
                    searchText: (String(book.title || '') + '\n' + String(book.author || '')).normalize('NFC').toLocaleLowerCase('is')
                })).filter(book => book.title);


                renderCategories();
                applyFilters();
                return true;
            } catch (error) {
                console.error('Villa við að hlaða Resources/books.json:', error);
                setInnerHTML('book-grid', `
                    <div class="col-span-full py-20 text-center">
                        <p class="text-rose-500 font-bold">Ekki tókst að hlaða bókunum.</p>
                        <p class="text-slate-400 text-sm mt-2">Athugaðu að <code>Resources/books.json</code> sé til staðar og gilt JSON.</p>
                    </div>`);
                return false;
            }
        }

        // Flokkarnir búnir til á fljótlegan hátt
        function renderCategories() {
            let cats = new Set();
            allBooks.forEach(b => b.categories.forEach(c => cats.add(c)));
            const sortedCats = ['Allir', '❤️ Óskalisti', '✅ Lesið', ...Array.from(cats).sort()];
            const container = document.getElementById('category-filters');
            if (!container) return;
            
            container.innerHTML = sortedCats.map(cat => {
                const isAllSelected = cat === 'Allir' && activeCategories.length === 0;
                const isSelected = activeCategories.includes(cat);
                const isActive = isAllSelected || isSelected;
                
                return `
                    <button onclick="toggleCategory(this.dataset.category)" data-category="${escapeHTML(cat)}" aria-pressed="${isActive}"
                        class="category-btn px-4 md:px-5 py-2 md:py-2.5 rounded-xl md:rounded-2xl text-[11px] md:text-xs font-bold transition-all duration-200 shadow-sm ${isActive ? 'bg-indigo-600 text-white shadow-indigo-200' : 'bg-white text-slate-600 hover:bg-slate-50 border border-slate-200/50'}">
                        ${escapeHTML(cat)}
                    </button>
                `;
            }).join('');
        }

        function updateCategoryButtonsUI() {
            const buttons = document.querySelectorAll('.category-btn');
            buttons.forEach(btn => {
                const cat = btn.getAttribute('data-category');
                const isAllSelected = cat === 'Allir' && activeCategories.length === 0;
                const isSelected = activeCategories.includes(cat);
                const isActive = isAllSelected || isSelected;
                
                btn.setAttribute('aria-pressed', String(isActive));
                if (isActive) {
                    btn.className = "category-btn px-4 md:px-5 py-2 md:py-2.5 rounded-xl md:rounded-2xl text-[11px] md:text-xs font-bold transition-all duration-200 shadow-sm bg-indigo-600 text-white shadow-indigo-200";
                } else {
                    btn.className = "category-btn px-4 md:px-5 py-2 md:py-2.5 rounded-xl md:rounded-2xl text-[11px] md:text-xs font-bold transition-all duration-200 shadow-sm bg-white text-slate-600 hover:bg-slate-50 border border-slate-200/50";
                }
            });
        }

        function toggleCategory(cat) {
            if (cat === 'Allir') {
                activeCategories = [];
            } else {
                const index = activeCategories.indexOf(cat);
                if (index > -1) {
                    activeCategories.splice(index, 1);
                } else {
                    activeCategories.push(cat);
                }
            }
            updateCategoryButtonsUI();
            applyFilters();
        }

        function resetBookPagination() {
            renderedBookLimit = BOOK_BATCH_SIZE;
            bookFilterSignature = '';
        }

        function applyFilters() {
            const signature = JSON.stringify([searchQuery, activeCategories,
                typeof filtersValue === 'function' ? filtersValue() : null,
                document.getElementById('book-sort')?.value || 'default']);
            if (signature !== bookFilterSignature) renderedBookLimit = BOOK_BATCH_SIZE;
            bookFilterSignature = signature;
            filteredBooks = allBooks.filter(b => {
                const search = (b.searchText || (b.title + '\n' + b.author).normalize('NFC').toLocaleLowerCase('is')).includes(searchQuery);
                
                if (activeCategories.length === 0) {
                    return search;
                }
                
                const matchesCategories = activeCategories.every(cat => {
                    if (cat === '❤️ Óskalisti') return userData.liked.includes(b.id);
                    if (cat === '✅ Lesið') return userData.read.includes(b.id);
                    return b.categories.includes(cat);
                });
                
                return search && matchesCategories;
            });
            renderBooks();
        }

        function showMoreBooks() {
            const previous = Math.min(renderedBookLimit, filteredBooks.length);
            renderedBookLimit += BOOK_BATCH_SIZE;
            renderBooks();
            document.querySelectorAll('#book-grid .book-card')[previous]?.querySelector('[data-action="info"]')?.focus({ preventScroll: true });
        }

        function renderBooks() {
            if (bookRenderSuspended) return;
            const container = document.getElementById('book-grid');
            if (!container) return;
            const rememberedFocus = rememberBookFocus();

            if (filteredBooks.length === 0) {
                container.innerHTML = `
                    <div class="col-span-full py-20 text-center text-slate-400 font-bold italic">
                        Engin bók fannst í þessari samsetningu...
                    </div>`;
                restoreBookFocus(rememberedFocus);
                return;
            }
            container.innerHTML = filteredBooks.slice(0, renderedBookLimit).map(b => {
                const isLiked = userData.liked.includes(b.id);
                const isRead = userData.read.includes(b.id);
                const review = userData.reviews[b.id];
                
                return `
                    <div class="book-card group relative" data-book-id="${b.id}">
                        <div class="absolute top-2 right-2 md:top-3 md:right-3 flex flex-col gap-2 z-20 transform translate-x-3 opacity-0 group-hover:translate-x-0 group-hover:opacity-100 group-focus-within:translate-x-0 group-focus-within:opacity-100 transition-all duration-300">
                            <button onclick="event.stopPropagation(); toggleRead(${b.id})" data-action="read" aria-label="Merkja ${escapeHTML(b.title)} sem lesna" aria-pressed="${isRead}" class="w-8 h-8 rounded-xl bg-white/95 backdrop-blur-md flex items-center justify-center shadow-lg hover:scale-110 transition-all">
                                <i aria-hidden="true" class="${isRead ? 'fas fa-circle-check text-emerald-500' : 'far fa-circle-check text-slate-300'} text-lg"></i>
                            </button>
                            <button onclick="event.stopPropagation(); toggleLike(${b.id})" data-action="like" aria-label="Setja ${escapeHTML(b.title)} á óskalista" aria-pressed="${isLiked}" class="w-8 h-8 rounded-xl bg-white/95 backdrop-blur-md flex items-center justify-center shadow-lg hover:scale-110 transition-all">
                                <i aria-hidden="true" class="${isLiked ? 'fas fa-heart text-rose-500' : 'far fa-heart text-slate-300'} text-lg"></i>
                            </button>
                        </div>
                        <div data-action="info" role="button" tabindex="0" data-book-id="${b.id}" aria-label="Upplýsingar um ${escapeHTML(b.title)}" onclick="openBookInfo(${b.id}, event)" class="cursor-pointer">
                            <!-- Bætt við async decoding og lazy loading á myndir til að gera skrun 100% lagg-frítt -->
                            <div class="book-img-container aspect-[3/4.5] relative mb-2 md:mb-3 shimmer-placeholder">
                                <img src="${escapeHTML(b.cover || COVER_PLACEHOLDER)}" alt="Bókarkápa: ${escapeHTML(b.title)}"
                                     class="w-full h-full object-cover transition-opacity duration-500 opacity-0" 
                                     decoding="async"
                                     loading="lazy"
                                     onload="finishCoverLoading(this)"
                                     onerror="handleCoverError(this)">
                                <div class="absolute inset-0 img-gradient opacity-60"></div>
                                ${review ? `
                                    <div class="absolute bottom-2 left-2 bg-amber-400 text-white text-[8px] font-black px-2 py-0.5 rounded-lg shadow-lg flex items-center gap-1">
                                        <i aria-hidden="true" class="fas fa-star"></i>${review.rating}
                                    </div>
                                ` : ''}
                            </div>
                            <div class="px-1 text-center">
                                <h3 class="font-bold text-slate-900 text-[10px] md:text-[11px] leading-tight mb-0.5 uppercase tracking-tighter line-clamp-2">${escapeHTML(b.title)}</h3>
                                <p class="text-indigo-400 text-[8px] font-black uppercase tracking-widest">${escapeHTML(b.author)}</p>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
            if (filteredBooks.length > BOOK_BATCH_SIZE) {
                const shown = Math.min(renderedBookLimit, filteredBooks.length);
                container.insertAdjacentHTML('beforeend', `<div class="col-span-full text-center py-6"><p role="status" class="feature-note">Sýnir ${shown} af ${filteredBooks.length} bókum</p>${shown < filteredBooks.length ? '<button type="button" class="feature-button secondary" aria-controls="book-grid" onclick="showMoreBooks()">Sýna fleiri bækur</button>' : ''}</div>`);
            }
            restoreBookFocus(rememberedFocus);
        }

        // --- Útfærsla á mýkri gluggum (Fluid Modal API) ---
        function openModal(modalId, contentId) {
            const modal = document.getElementById(modalId);
            const content = document.getElementById(contentId);
            if (!modal) return;
            
            modal.classList.remove('hidden');
            prepareDialog(modal, content);
            // Gildi uppfært í næsta ramma til að kveikja á CSS transition hreyfingu
            requestAnimationFrame(() => {
                if (activeDialog?.modal !== modal) return;
                modal.classList.remove('opacity-0', 'pointer-events-none');
                modal.classList.add('opacity-100', 'pointer-events-auto');
                if (content) {
                    content.classList.remove('scale-95', 'translate-y-4');
                    content.classList.add('scale-100', 'translate-y-0');
                    if (activeDialog?.modal === modal) focusDialog(content);
                }
            });
        }

        function closeModal(modalId, contentId) {
            const modal = document.getElementById(modalId);
            const content = document.getElementById(contentId);
            if (!modal) return;
            
            restoreDialogFocus(modal);
            modal.classList.remove('opacity-100', 'pointer-events-auto');
            modal.classList.add('opacity-0', 'pointer-events-none');
            if (content) {
                content.classList.remove('scale-100', 'translate-y-0');
                content.classList.add('scale-95', 'translate-y-4');
            }
            // Beðið eftir að hreyfingu ljúki áður en frumefni er falið með hidden
            setTimeout(() => {
                if (modal.classList.contains('opacity-0')) {
                    modal.classList.add('hidden');
                }
            }, 300); // 300ms passar við duration-300 á transition
        }

        // Opnar bókaupplýsingar í öruggum fixed glugga með mjúkri hreyfingu
        function openBookInfo(id, event) {
            id = canonicalBookId(id);
            const b = historyBook(id); if (!b) return;
            const rev = userData.reviews[b.id] || { rating: 0, comment: '' };
            currentRating = rev.rating;
            
            setInnerHTML('modal-inner-content', `
                <div class="flex flex-col md:flex-row gap-6 md:gap-10 items-start">
                    <div class="w-full md:w-[180px] shrink-0 mx-auto">
                        <div class="shimmer-placeholder aspect-[3/4.5] rounded-2xl shadow-xl overflow-hidden">
                            <img src="${escapeHTML(b.cover || COVER_PLACEHOLDER)}" alt="Bókarkápa: ${escapeHTML(b.title)}" class="w-full h-full object-cover transition-opacity duration-300 opacity-0" decoding="async" onload="finishCoverLoading(this)" onerror="handleCoverError(this)">
                        </div>
                        <div class="mt-4 flex flex-wrap gap-1 justify-center">
                            ${b.categories.map(c => `<span class="bg-indigo-50 text-indigo-600 px-2.5 py-1 rounded-lg text-[9px] font-black uppercase border border-indigo-100/50">${escapeHTML(c)}</span>`).join('')}
                        </div>
                    </div>
                    <div class="flex-grow min-w-0 space-y-6 w-full">
                        <div>
                            ${b.archived ? '<p class="text-xs font-bold">Varðveitt bók úr eldra safni. Lestrarsaga og umsagnir eru varðveittar.</p>' : ''}
                            <h2 id="book-dialog-title" class="text-2xl font-black text-slate-900 tracking-tighter leading-tight">${escapeHTML(b.title)}</h2>
                            <div class="flex flex-wrap items-center gap-x-4 gap-y-1 text-slate-400 font-bold uppercase tracking-widest text-[9px] mt-2">
                                <span>Höfundur: ${escapeHTML(b.author)}</span>
                                <span>|</span>
                                <span class="text-indigo-500 font-black"><i aria-hidden="true" class="fas fa-file-lines"></i> ${b.pages ? b.pages + ' bls' : 'Óþekkt'}</span>
                            </div>
                        </div>
                        <div class="bg-slate-50 p-5 rounded-2xl border border-slate-100">
                            <h5 class="text-[9px] font-black text-slate-400 uppercase tracking-[0.2em] mb-2">Um bókina</h5>
                            <p class="text-slate-600 text-sm leading-relaxed">${escapeHTML(b.description || 'Engin lýsing fannst.')}</p>
                        </div>
                        
                        <div class="p-6 rounded-2xl space-y-4 border border-indigo-100/50">
                            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                                <h4 class="text-[10px] font-black text-slate-400 uppercase tracking-widest">Gefðu bókinni stjörnugjöf</h4>
                                <div role="group" aria-label="Stjörnugjöf" class="star-rating text-xl flex gap-1.5" id="modal-stars">
                                    ${[1,2,3,4,5].map(i => `<button type="button" aria-label="${i} stjörnur" aria-pressed="${i === currentRating}" class="cursor-pointer transition-transform hover:scale-110" onclick="setRating(${i})"><i aria-hidden="true" class="${i <= currentRating ? 'fas text-amber-400' : 'far text-slate-200'} fa-star"></i></button>`).join('')}
                                </div>
                            </div>
                            <textarea aria-label="Umsögn um bókina" id="review-text" class="w-full bg-white border-2 border-slate-100 rounded-2xl p-4 text-sm font-semibold outline-none focus:border-indigo-400 shadow-sm min-h-[100px] transition-all" placeholder="Hvernig fannst þér bókin?">${escapeHTML(rev.comment)}</textarea>
                            
                            <button onclick="saveReview(${b.id}, event)" id="save-review-btn" class="w-full bg-indigo-600 text-white font-black py-3.5 rounded-xl shadow-lg transition-all text-[11px] uppercase tracking-widest active:scale-95">
                                <i aria-hidden="true" class="fas fa-floppy-disk mr-2"></i> Vista umsögn
                            </button>
                        </div>
                    </div>
                </div>`);
            
            openModal('desc-modal', 'desc-modal-content');
        }

        function handleCloseModal() {
            closeModal('desc-modal', 'desc-modal-content');
        }

        // Opnar meðmælakerfi í fixed glugga með transition
        function openRecommendModal() {
            openModal('recommend-modal', 'recommend-modal-content');
            
            const titleInput = document.getElementById('rec-title');
            const authorInput = document.getElementById('rec-author');
            const ideasInput = document.getElementById('rec-ideas');
            
            if (titleInput) titleInput.value = '';
            if (authorInput) authorInput.value = '';
            if (ideasInput) ideasInput.value = '';
        }

        function closeRecommendModal() {
            closeModal('recommend-modal', 'recommend-modal-content');
        }

        function submitRecommendation() {
            const titleEl = document.getElementById('rec-title');
            const title = titleEl ? titleEl.value.trim() : '';
            const authorEl = document.getElementById('rec-author');
            const author = authorEl ? authorEl.value.trim() : '';
            const ideasEl = document.getElementById('rec-ideas');
            const ideas = ideasEl ? ideasEl.value.trim() : '';
            
            if (!title) {
                if (titleEl) {
                    titleEl.classList.add('shake-element');
                    setTimeout(() => titleEl.classList.remove('shake-element'), 300);
                }
                showToast("Þú verður að fylla út heiti bókar!", "error");
                return;
            }
            
            const email = "OdIG01@gskolar.is";
            const subject = encodeURIComponent("Bókameðmæli frá Bókasafni Unglingadeildar");
            let bodyText = `Hæ!\n\nÉg vil mæla með eftirfarandi bók fyrir bókasafnið:\n\n`;
            bodyText += `Heiti bókar: ${title}\n`;
            if (author) {
                bodyText += `Höfundur: ${author}\n`;
            }
            if (ideas) {
                bodyText += `Hugmyndir / umsögn: ${ideas}\n`;
            }
            
            const body = encodeURIComponent(bodyText);
            const mailtoUrl = `mailto:${email}?subject=${subject}&body=${body}`;
            
            window.location.href = mailtoUrl;
            
            closeRecommendModal();
            showToast("Tillagan þín hefur verið undirbúin í tölvupósti!");
        }

        function setRating(r) {
            currentRating = r;
            const starContainer = document.getElementById('modal-stars');
            if (starContainer) {
                const stars = starContainer.children;
                for (let i = 0; i < 5; i++) {
                    stars[i].setAttribute('aria-pressed', String(i + 1 === r));
                    stars[i].firstElementChild.className = (i < r ? 'fas text-amber-400' : 'far text-slate-200') + ' fa-star';
                }
            }
        }

        function showToast(msg, type = 'success') {
            const t = document.getElementById('success-toast');
            const icon = document.getElementById('success-icon');
            const msgEl = document.getElementById('success-message');
            if (!t) return;
            
            if (type === 'error') {
                t.classList.remove('bg-emerald-600'); t.classList.add('bg-rose-600');
                if (icon) icon.className = 'fas fa-exclamation-circle';
            } else {
                t.classList.remove('bg-rose-600'); t.classList.add('bg-emerald-600');
                if (icon) icon.className = 'fas fa-check';
            }
            if (msgEl) msgEl.innerText = msg;
            if (typeof activeDialog !== 'undefined' && activeDialog) {
                const status = activeDialog.content.querySelector('[data-dialog-status]');
                if (status) status.textContent = msg;
            }
            t.classList.remove('translate-y-48', 'opacity-0');
            t.classList.add('translate-y-0', 'opacity-100');
            setTimeout(() => {
                t.classList.remove('translate-y-0', 'opacity-100');
                t.classList.add('translate-y-48', 'opacity-0');
            }, 3000);
        }

        function saveReview(id, event) {
            const btn = document.getElementById('save-review-btn');
            const reviewEl = document.getElementById('review-text');
            const comment = reviewEl ? reviewEl.value.trim() : '';
            id = canonicalBookId(id);
            if (!historyBook(id)) return;
            if (!Number.isInteger(currentRating) || currentRating < 1 || currentRating > 5) {
                if (btn) {
                    btn.classList.add('shake-element'); 
                    setTimeout(() => btn.classList.remove('shake-element'), 300);
                }
                showToast("Veldu stjörnur fyrst!", "error"); return;
            }
            
            // Vista umsögn í gagnagrunn / localStorage
            userData.reviews[id] = { rating: currentRating, comment, date: new Date().toLocaleDateString('is-IS') };
            
            // Marka bókina sjálfkrafa sem lesna (grænt hak) ef hún er ekki þegar merkt
            if (!userData.read.includes(id)) {
                userData.read.push(id);
                if (userData.completedDates) userData.completedDates[id] = getLocalYYYYMMDD(new Date());
            }
            
            const saved = saveUserData();
            openBookInfo(id, event);
            updateStatsUI();
            applyFilters();
            if (saved) showToast("Umsögnin þín hefur verið vistuð");
        }

        function handleTimerPrimaryAction() {
            if (!appReady) return;
            if (!timerState.active) {
                timerState = emptyTimerState();
                timerState.active = true;
                timerState.startTime = Date.now();
                timerState.interval = setInterval(updateTimerDisplay, 1000);
            } else if (!timerState.paused) {
                checkpointTimer();
                timerState.paused = true;
                clearInterval(timerState.interval);
            } else {
                timerState.paused = false;
                timerState.startTime = Date.now();
                timerState.interval = setInterval(updateTimerDisplay, 1000);
            }
            saveUserData();
            updateTimerDisplay();
            updateTimerUI();
        }

        function updateTimerDisplay() {
            const ms = timerState.elapsedBeforePause + (timerState.active && !timerState.paused ? Math.max(0, Date.now() - timerState.startTime) : 0);
            const sT = Math.floor(ms / 1000);
            const h = Math.floor(sT / 3600).toString().padStart(2, '0');
            const m = Math.floor((sT % 3600) / 60).toString().padStart(2, '0');
            const s = (sT % 60).toString().padStart(2, '0');
            setInnerText('main-timer-display', `${h}:${m}:${s}`);
        }

        // Opnar staðfestingarglugga á miðjum skjánum á öruggan hátt með transition
        function showStopConfirmation() { 
            openModal('stop-confirm-modal', 'stop-confirm-modal-content');
        }
        
        function closeStopConfirmation() { 
            closeModal('stop-confirm-modal', 'stop-confirm-modal-content');
        }

        function confirmStopReading() {
            if (!timerState.active) { closeStopConfirmation(); return; }
            checkpointTimer();
            const previousMilestones = JSON.stringify({achievements:userData.achievements,challenges:userData.challenges});
            const previousTotal = userData.totalSeconds;
            const previousProgress = { ...userData.dailyProgress };
            const session = timerState;
            const dates = Object.entries(session.dailyMilliseconds).sort(([a], [b]) => a.localeCompare(b));
            const totalSeconds = Math.floor(session.elapsedBeforePause / 1000);
            let remainingSeconds = totalSeconds;
            for (const [index, [date, ms]] of dates.entries()) {
                // Carry fractional seconds across midnight instead of losing a
                // second for each date crossed. Totals match the timer display.
                const seconds = index === dates.length - 1 ? remainingSeconds : Math.floor(ms / 1000);
                remainingSeconds -= seconds;
                userData.totalSeconds += seconds;
                userData.dailyProgress[date] = (userData.dailyProgress[date] || 0) + seconds;
            }
            const previousSessions = [...(userData.sessions || [])];
            if (userData.sessions && totalSeconds > 0) userData.sessions.push({id: newDataId(),date:getLocalYYYYMMDD(new Date()),seconds:totalSeconds});
            timerState = emptyTimerState();
            // Commit the totals and removal of the session in one storage write.
            if (!saveUserData()) {
                Object.assign(userData,JSON.parse(previousMilestones));
                if (userData.sessions) userData.sessions = previousSessions;
                userData.totalSeconds = previousTotal;
                userData.dailyProgress = previousProgress;
                timerState = session;
                return;
            }
            clearInterval(session.interval);
            updateTimerDisplay();
            updateTimerUI();
            updateStatsUI();
            closeStopConfirmation();
            showToast("Tími vistaður!");
        }

        function updateTimerUI() {
            const w = document.getElementById('timer-widget');
            const pI = document.getElementById('timer-primary-icon');
            const pB = document.getElementById('timer-primary-btn');
            const sB = document.getElementById('timer-stop-btn');
            const sL = document.getElementById('timer-status-label');
            if (pB) pB.setAttribute('aria-label', !timerState.active ? 'Hefja lestur' : timerState.paused ? 'Halda lestri áfram' : 'Gera hlé á lestri');
            if (!timerState.active) {
                if (sL) sL.innerText = "Hefja lestur"; 
                if (pI) pI.className = "fas fa-play ml-1";
                if (pB) pB.className = "w-14 h-14 md:w-16 md:h-16 bg-gradient-to-tr from-indigo-600 to-indigo-500 text-white rounded-2xl md:rounded-3xl flex items-center justify-center transition shadow-lg shadow-indigo-100";
                if (sB) sB.classList.add('hidden'); 
                if (w) w.classList.remove('timer-active-glow');
            } else if (!timerState.paused) {
                if (sL) sL.innerText = "Lestur í gangi"; 
                if (pI) pI.className = "fas fa-pause";
                if (pB) pB.className = "w-14 h-14 md:w-16 md:h-16 bg-gradient-to-tr from-amber-500 to-orange-500 text-white rounded-2xl md:rounded-3xl flex items-center justify-center transition shadow-lg shadow-amber-100";
                if (sB) sB.classList.remove('hidden'); 
                if (w) w.classList.add('timer-active-glow');
            } else {
                if (sL) sL.innerText = "Pása"; 
                if (pI) pI.className = "fas fa-play ml-1";
                if (pB) pB.className = "w-14 h-14 md:w-16 md:h-16 bg-gradient-to-tr from-indigo-600 to-indigo-500 text-white rounded-2xl md:rounded-3xl flex items-center justify-center transition shadow-lg shadow-indigo-100";
                if (sB) sB.classList.remove('hidden'); 
                if (w) w.classList.remove('timer-active-glow');
            }
        }

        function syncGoalUI() {
            const minInput = document.getElementById('target-minutes-input');
            const goalSelect = document.getElementById('goal-type-select');
            if (minInput) minInput.value = userData.minutesGoal || '';
            if (goalSelect) goalSelect.value = userData.goalType || 'daily';
        }

        function setMinutesGoal() {
            const minInput = document.getElementById('target-minutes-input');
            const goalSelect = document.getElementById('goal-type-select');
            const rawVal = minInput ? Number(minInput.value) : 0;
            userData.minutesGoal = Number.isFinite(rawVal) ? Math.max(0, rawVal) : 0;
            userData.goalType = ['daily', 'weekly', 'monthly'].includes(goalSelect?.value) ? goalSelect.value : 'daily';
            saveUserData();
            updateStatsUI();
        }

        function addPersonalGoal() {
            const i = document.getElementById('personal-goal-input');
            if (i && i.value.trim()) { 
                let id = Date.now();
                while (userData.personalGoals.some(goal => goal.id === id)) id++;
                userData.personalGoals.push({ id, text: i.value.trim(), completed: false });
                i.value = ''; 
                saveUserData(); 
                updateStatsUI(); 
            }
        }
        function togglePersonalGoal(id) { const g = userData.personalGoals.find(x => x.id === id); if (g) { g.completed = !g.completed; saveUserData(); updateStatsUI(); } }
        function deletePersonalGoal(id) { userData.personalGoals = userData.personalGoals.filter(x => x.id !== id); saveUserData(); updateStatsUI(); }

        function toggleLike(id) {
            if (!allBooks.some(book => book.id === id)) return;
            const index = userData.liked.indexOf(id);
            if (index > -1) userData.liked.splice(index, 1); else userData.liked.push(id);
            saveUserData(); applyFilters(); updateStatsUI();
        }
        function toggleRead(id) {
            if (!allBooks.some(book => book.id === id)) return;
            const index = userData.read.indexOf(id);
            if (index > -1) userData.read.splice(index, 1); else { userData.read.push(id); if(userData.completedDates) userData.completedDates[id]=getLocalYYYYMMDD(new Date()); }
            saveUserData(); applyFilters(); updateStatsUI();
        }

        // Uppfærir tölfræðiviðmótið á síðunni „Lesturinn minn“
        function updateStatsUI() {
            const ts = userData.totalSeconds;
            setInnerText('stat-hours', Math.floor(ts / 3600));
            setInnerText('stat-minutes', Math.floor((ts % 3600) / 60));
            setInnerText('stat-seconds', ts % 60);
            
            const streak = calculateStreak();
            setInnerText('stat-streak', streak);
            setInnerText('streak-banner-description', userData.minutesGoal > 0
                ? `Þú hefur náð ${userData.goalType === 'weekly' ? 'vikumarkmiðinu' : userData.goalType === 'monthly' ? 'mánaðarmarkmiðinu' : 'dagsmarkmiðinu'} í ${streak} daga í röð.`
                : `Þú hefur lesið í minnst 10 mínútur í ${streak} daga í röð.`);
            
            const banner = document.getElementById('streak-banner');
            if (banner) {
                if (streak >= 2) { 
                    banner.classList.remove('hidden'); 
                    banner.classList.add('flex'); 
                } else {
                    banner.classList.add('hidden');
                }
            }

            const progressContainer = document.getElementById('minutes-goal-progress-container');
            if (userData.minutesGoal > 0) {
                if (progressContainer) progressContainer.classList.remove('hidden');
                
                let currentSecs = 0;
                let periodText = "";
                
                if (userData.goalType === 'weekly') {
                    currentSecs = getWeeklySeconds();
                    periodText = "vikumarkmiði";
                } else if (userData.goalType === 'monthly') {
                    currentSecs = getMonthlySeconds();
                    periodText = "mánaðarmarkmiði";
                } else {
                    currentSecs = (userData.dailyProgress[getLocalYYYYMMDD(new Date())] || 0);
                    periodText = "dagsmarkmiði";
                }

                const currentMins = Math.floor(currentSecs / 60);
                setInnerText('target-minutes-display', userData.minutesGoal);
                setInnerText('current-minutes-reached', currentMins);
                const pct = Math.min(100, (currentSecs / (userData.minutesGoal * 60)) * 100);
                
                const goalBar = document.getElementById('minutes-goal-bar');
                if (goalBar) goalBar.style.width = pct + '%';
                
                const remaining = Math.ceil(Math.max(0, userData.minutesGoal * 60 - currentSecs) / 60);
                setInnerText('minutes-goal-status', pct >= 100 ? "Markmiði náð! 🎉" : `Þú ert ${remaining} mín frá ${periodText}!`);
            } else {
                if (progressContainer) progressContainer.classList.add('hidden');
            }

            const goalsHtml = userData.personalGoals.map(g => `
                <div class="flex items-center gap-3 p-4 bg-white rounded-2xl border border-slate-100 shadow-sm transition-all duration-300">
                    <button onclick="togglePersonalGoal(${g.id})" aria-label="Ljúka markmiði: ${escapeHTML(g.text)}" aria-pressed="${g.completed}" class="shrink-0 w-6 h-6 rounded-lg border-2 ${g.completed ? 'bg-indigo-600 border-indigo-600 text-white' : 'border-slate-200 bg-white'} flex items-center justify-center transition-all">
                        ${g.completed ? '<i aria-hidden="true" class="fas fa-check text-[10px]"></i>' : ''}
                    </button>
                    <span class="flex-grow font-bold text-xs ${g.completed ? 'text-slate-400 line-through' : 'text-slate-700'}">${escapeHTML(g.text)}</span>
                    <button onclick="deletePersonalGoal(${g.id})" aria-label="Eyða markmiði: ${escapeHTML(g.text)}" class="text-slate-300 hover:text-rose-500 transition-colors"><i aria-hidden="true" class="fas fa-trash-can text-sm"></i></button>
                </div>`).join('') || '<p class="text-center py-4 text-slate-300 font-bold italic text-[10px]">Engin markmið skráð.</p>';
            setInnerHTML('personal-goals-list', goalsHtml);
            
            const reviewsHtml = Object.keys(userData.reviews).map(t => {
                const r = userData.reviews[t]; const b = historyBook(Number(t));
                return `
                    <div class="bg-white p-5 rounded-3xl border border-slate-100 flex gap-4 shadow-sm cursor-pointer transition-all hover:scale-[1.01]" role="button" tabindex="0" data-book-id="${b?.id ?? ''}" aria-label="Opna umsögn" onclick="openBookInfo(${b?.id}, event)">
                        <div class="w-12 h-18 shimmer-placeholder rounded-xl shrink-0 overflow-hidden shadow-md">
                            <img src="${escapeHTML(b?.cover || COVER_PLACEHOLDER)}" alt="Bókarkápa: ${escapeHTML(b?.title || 'Óþekkt bók')}" class="w-full h-full object-cover transition-opacity duration-300 opacity-0" loading="lazy" decoding="async" onload="finishCoverLoading(this)" onerror="handleCoverError(this)">
                        </div>
                        <div>
                            <h4 class="text-[11px] font-black line-clamp-1 mb-1">${escapeHTML(b?.title || 'Bók ekki í safninu')}</h4>
                            <div role="img" aria-label="${r.rating} af 5 stjörnum" class="flex gap-0.5 mb-2">${Array(5).fill(0).map((_, i) => `<i aria-hidden="true" class="${i < r.rating ? 'fas text-amber-400' : 'far text-slate-200'} fa-star text-[9px]"></i>`).join('')}</div>
                            <p class="text-[9px] text-slate-500 font-medium italic line-clamp-2">"${escapeHTML(r.comment)}"</p>
                        </div>
                    </div>`;
            }).join('') || '<p class="col-span-full text-center py-10 text-slate-300 font-bold italic text-[10px]">Engar umsagnir ennþá.</p>';
            const conflictsHtml = (userData.reviewConflicts || []).map(r => {
                const b = historyBook(r.bookId);
                return `<div class="bg-white p-5 rounded-3xl border border-slate-100"><h4 class="text-xs font-bold">${escapeHTML(b?.title || 'Varðveitt bók')} · Varðveitt umsögn</h4><p>${r.rating} / 5</p><p class="text-xs">${escapeHTML(r.comment)}</p><p class="text-xs">${escapeHTML(r.date)}</p></div>`;
            }).join('');
            setInnerHTML('reviews-archive', reviewsHtml + conflictsHtml);
            
            setInnerText('total-read-books-badge', userData.read.length);
            
            const readItemsHtml = historyBooks().filter(b => userData.read.includes(b.id)).map(b => `
                <div class="flex items-center gap-4 p-3 bg-white/5 rounded-2xl hover:bg-white/10 transition cursor-pointer" role="button" tabindex="0" data-book-id="${b.id}" aria-label="Upplýsingar um ${escapeHTML(b.title)}" onclick="openBookInfo(${b.id}, event)">
                    <div class="w-10 h-14 shimmer-placeholder rounded-lg shrink-0 overflow-hidden">
                        <img src="${escapeHTML(b.cover || COVER_PLACEHOLDER)}" alt="Bókarkápa: ${escapeHTML(b.title)}" class="w-full h-full object-cover transition-opacity duration-300 opacity-0" loading="lazy" decoding="async" onload="finishCoverLoading(this)" onerror="handleCoverError(this)">
                    </div>
                    <div class="flex-grow overflow-hidden">
                        <p class="font-bold text-xs line-clamp-1">${escapeHTML(b.title)}${b.archived ? ' · Varðveitt bók' : ''}</p>
                        <p class="text-[8px] font-black opacity-50 uppercase tracking-widest">${escapeHTML(b.author)}</p>
                    </div>
                </div>`).join('');
            setInnerHTML('read-items', readItemsHtml);
            
            const wishlistHtml = historyBooks().filter(b => userData.liked.includes(b.id)).map(b => `
                <div class="flex items-center gap-4 p-3 bg-white rounded-2xl hover:bg-slate-50 transition cursor-pointer border border-slate-100" role="button" tabindex="0" data-book-id="${b.id}" aria-label="Upplýsingar um ${escapeHTML(b.title)}" onclick="openBookInfo(${b.id}, event)">
                    <div class="w-10 h-14 shimmer-placeholder rounded-lg shrink-0 overflow-hidden">
                        <img src="${escapeHTML(b.cover || COVER_PLACEHOLDER)}" alt="Bókarkápa: ${escapeHTML(b.title)}" class="w-full h-full object-cover transition-opacity duration-300 opacity-0" loading="lazy" decoding="async" onload="finishCoverLoading(this)" onerror="handleCoverError(this)">
                    </div>
                    <div class="flex-grow overflow-hidden">
                        <p class="font-bold text-xs text-slate-900 line-clamp-1">${escapeHTML(b.title)}${b.archived ? ' · Varðveitt bók' : ''}</p>
                        <p class="text-[8px] font-black text-indigo-400 uppercase tracking-widest">${escapeHTML(b.author)}</p>
                    </div>
                </div>`).join('');
            setInnerHTML('wishlist-items', wishlistHtml);

            renderVisualStats();
            renderMonthlyStats();
        }

        // Teiknar tölfræði yfir flokka og höfunda
        function renderVisualStats() {
            const readBooks = historyBooks().filter(b => userData.read.includes(b.id));
            const catContainer = document.getElementById('visual-stats-categories');
            const authContainer = document.getElementById('visual-stats-authors');

            if (!catContainer || !authContainer) return;

            if (readBooks.length === 0) {
                catContainer.innerHTML = `<p class="text-xs italic text-slate-400 py-4">Hakaðu við lesnar bækur til að sjá tölfræði!</p>`;
                authContainer.innerHTML = `<p class="text-xs italic text-slate-400 py-4">Hakaðu við lesnar bækur til að sjá tölfræði!</p>`;
                return;
            }

            let catCounts = Object.create(null);
            let authCounts = Object.create(null);

            readBooks.forEach(b => {
                b.categories.forEach(c => {
                    catCounts[c] = (catCounts[c] || 0) + 1;
                });
                authCounts[b.author] = (authCounts[b.author] || 0) + 1;
            });

            const topCats = Object.entries(catCounts).sort((a,b) => b[1] - a[1]).slice(0, 5);
            const topAuths = Object.entries(authCounts).sort((a,b) => b[1] - a[1]).slice(0, 5);

            const maxCat = topCats[0] ? topCats[0][1] : 1;
            const maxAuth = topAuths[0] ? topAuths[0][1] : 1;

            catContainer.innerHTML = topCats.map(([cat, count]) => {
                const pct = (count / maxCat) * 100;
                return `
                    <div class="space-y-1">
                        <div class="flex justify-between text-[11px] font-bold text-slate-700">
                            <span>${escapeHTML(cat)}</span>
                            <span class="text-slate-500">${count} bók${count > 1 ? 'ur' : ''}</span>
                        </div>
                        <div class="w-full bg-slate-100 h-3 rounded-full overflow-hidden p-0.5 shadow-inner">
                            <div class="bg-gradient-to-r from-indigo-500 to-indigo-600 h-full rounded-full transition-all duration-700" style="width: ${pct}%"></div>
                        </div>
                    </div>
                `;
            }).join('');

            authContainer.innerHTML = topAuths.map(([auth, count]) => {
                const pct = (count / maxAuth) * 100;
                return `
                    <div class="space-y-1">
                        <div class="flex justify-between text-[11px] font-bold text-slate-700">
                            <span>${escapeHTML(auth)}</span>
                            <span class="text-slate-500">${count} bók${count > 1 ? 'ur' : ''}</span>
                        </div>
                        <div class="w-full bg-slate-100 h-3 rounded-full overflow-hidden p-0.5 shadow-inner">
                            <div class="bg-gradient-to-r from-violet-500 to-violet-600 h-full rounded-full transition-all duration-700" style="width: ${pct}%"></div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        // Teiknar mánaðarlega tölfræðitöflu
        function renderMonthlyStats() {
            const container = document.getElementById('monthly-history-container');
            if (!container) return;

            const monthsIs = [
                'Janúar', 'Febrúar', 'Mars', 'Apríl', 'Maí', 'Júní',
                'Júlí', 'Ágúst', 'September', 'Október', 'Nóvember', 'Desember'
            ];

            const monthlyData = {};
            const now = new Date();

            for (let i = 5; i >= 0; i--) {
                const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
                const year = d.getFullYear();
                const monthIdx = d.getMonth();
                const key = `${year}-${String(monthIdx + 1).padStart(2, '0')}`;
                monthlyData[key] = {
                    label: `${monthsIs[monthIdx]}`,
                    seconds: 0
                };
            }

            for (const dateStr in userData.dailyProgress) {
                const seconds = userData.dailyProgress[dateStr] || 0;
                if (seconds === 0) continue;
                
                const [year, month] = dateStr.split('-');
                const key = `${year}-${month}`;
                
                if (monthlyData[key]) {
                    monthlyData[key].seconds += seconds;
                }
            }

            const sortedMonths = Object.entries(monthlyData)
                .sort((a, b) => a[0].localeCompare(b[0]));

            const maxSeconds = Math.max(...sortedMonths.map(m => m[1].seconds), 1);
            const totalActivity = sortedMonths.reduce((sum, m) => sum + m[1].seconds, 0);

            if (totalActivity === 0) {
                container.innerHTML = `
                    <p class="text-xs italic text-slate-400 py-4">Ræstu lestrarklukkuna þegar þú lest til að safna mánaðarlegri tölfræði!</p>
                `;
                return;
            }

            container.innerHTML = sortedMonths.map(([key, data]) => {
                const totalMins = Math.floor(data.seconds / 60);
                const hours = Math.floor(totalMins / 60);
                const mins = totalMins % 60;
                const pct = (data.seconds / maxSeconds) * 100;

                let timeText = "0 mín";
                if (data.seconds > 0) {
                    if (hours > 0) {
                        timeText = `${hours} klst og ${mins} mín`;
                    } else {
                        timeText = `${mins} mín`;
                    }
                }

                return `
                    <div class="space-y-1">
                        <div class="flex justify-between text-[11px] font-bold text-slate-700">
                            <span>${data.label}</span>
                            <span class="text-pink-600 font-extrabold">${timeText}</span>
                        </div>
                        <div class="w-full bg-slate-100 h-3 rounded-full overflow-hidden p-0.5 shadow-inner">
                            <div class="bg-gradient-to-r from-pink-500 to-pink-600 h-full rounded-full transition-all duration-1000" style="width: ${data.seconds > 0 ? Math.max(5, pct) : 0}%"></div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        // Fínstillt og vélbúnaðar-hröðuð síðuskipti (Perfect Crossfade)
        function showPage(p) {
            const libPage = document.getElementById('library-page');
            const statsPage = document.getElementById('stats-page');
            const targetPage = p === 'library' ? libPage : statsPage;
            const currentActivePage = p === 'library' ? statsPage : libPage;

            if (!targetPage || !currentActivePage) return;
            if (targetPage.classList.contains('active') && !targetPage.classList.contains('hidden')) return;

            // Dofna virku síðuna mjúklega út
            currentActivePage.classList.remove('active');
            
            setTimeout(() => {
                currentActivePage.classList.add('hidden');
                targetPage.classList.remove('hidden');
                
                // Endurkalla flæði á skjánum (Force reflow)
                targetPage.offsetHeight;
                
                // Birta nýju síðuna mjúklega inn með risi
                targetPage.classList.add('active');
            }, 180); // Skilar fullkomlega smurðum og liprum hreyfingum

            const libBtn = document.getElementById('nav-library'); 
            const statBtn = document.getElementById('nav-stats');
            
            if (libBtn) {
                libBtn.className = p === 'library' 
                    ? "px-4 md:px-6 py-2.5 rounded-[1.5rem] bg-white shadow-md text-indigo-600 font-bold transition-all whitespace-nowrap" 
                    : "px-4 md:px-6 py-2.5 rounded-[1.5rem] text-slate-600 hover:text-indigo-600 font-bold transition-all whitespace-nowrap";
            }
            if (statBtn) {
                statBtn.className = p === 'stats' 
                    ? "px-4 md:px-6 py-2.5 rounded-[1.5rem] bg-white shadow-md text-indigo-600 font-bold transition-all whitespace-nowrap" 
                    : "px-4 md:px-6 py-2.5 rounded-[1.5rem] text-slate-600 hover:text-indigo-600 font-bold transition-all whitespace-nowrap";
            }
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        function handleSearch() {
            const searchInput = document.getElementById('book-search');
            searchQuery = searchInput ? searchInput.value.normalize('NFC').toLocaleLowerCase('is') : '';
            if (searchQuery) showPage('library');
            applyFilters();
            
            const sBox = document.getElementById('search-suggestions');
            if (!sBox) return;
            
            if (!searchQuery) { 
                sBox.classList.add('hidden'); 
                return; 
            }
            
            let matchT = allBooks.filter(b => (b.searchText || (b.title + '\n' + b.author).normalize('NFC').toLocaleLowerCase('is')).includes(searchQuery)).slice(0,5);
            if (matchT.length) {
                sBox.innerHTML = matchT.map(b => `<li role="button" tabindex="0" onclick="selectSug(${b.id})" class="px-6 py-4 hover:bg-indigo-50 cursor-pointer text-sm font-bold border-b border-slate-50 flex items-center gap-4"><i aria-hidden="true" class="fas fa-book text-indigo-400"></i> ${escapeHTML(b.title)}</li>`).join('');
                sBox.classList.remove('hidden');
            } else {
                sBox.classList.add('hidden');
            }
        }

        function selectSug(id) {
            const searchInput = document.getElementById('book-search');
            const book = allBooks.find(book => book.id === id);
            if (searchInput && book) searchInput.value = book.title;
            handleSearch();
            safeToggleClass('search-suggestions', 'hidden', true);
            searchInput?.focus();
        }

        document.addEventListener('click', e => { 
            const searchContainer = document.getElementById('search-container');
            if (searchContainer && !searchContainer.contains(e.target)) {
                safeToggleClass('search-suggestions', 'hidden', true); 
            }
        });


        window.addEventListener('pagehide', () => { checkpointTimer(); saveUserData(); });
        document.addEventListener('visibilitychange', () => {
            if (document.visibilityState === 'hidden') { checkpointTimer(); saveUserData(); }
        });
