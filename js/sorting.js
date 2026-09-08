(() => {
    const collator = new Intl.Collator('is', {
        sensitivity: 'base',
        numeric: true
    });

    let sortMode = 'default';

    function sortBooks(books) {
        const sorted = [...books];

        switch (sortMode) {
            case 'title-asc':
                return sorted.sort((a, b) => collator.compare(a.title, b.title));
            case 'title-desc':
                return sorted.sort((a, b) => collator.compare(b.title, a.title));
            case 'author-asc':
                return sorted.sort((a, b) => {
                    const authorCompare = collator.compare(a.author, b.author);
                    return authorCompare || collator.compare(a.title, b.title);
                });
            case 'pages-asc':
                return sorted.sort((a, b) => {
                    const aPages = Number(a.pages);
                    const bPages = Number(b.pages);
                    const aValid = Number.isFinite(aPages) && aPages > 0;
                    const bValid = Number.isFinite(bPages) && bPages > 0;

                    if (aValid && bValid) return aPages - bPages || collator.compare(a.title, b.title);
                    if (aValid) return -1;
                    if (bValid) return 1;
                    return collator.compare(a.title, b.title);
                });
            case 'pages-desc':
                return sorted.sort((a, b) => {
                    const aPages = Number(a.pages);
                    const bPages = Number(b.pages);
                    const aValid = Number.isFinite(aPages) && aPages > 0;
                    const bValid = Number.isFinite(bPages) && bPages > 0;

                    if (aValid && bValid) return bPages - aPages || collator.compare(a.title, b.title);
                    if (aValid) return -1;
                    if (bValid) return 1;
                    return collator.compare(a.title, b.title);
                });
            default:
                return sorted.sort((a, b) => Number(a.id) - Number(b.id));
        }
    }

    function installSorting() {
        if (typeof window.applyFilters !== 'function' || document.getElementById('book-sort')) return;

        const originalApplyFilters = window.applyFilters;

        window.applyFilters = function () {
            originalApplyFilters();
            filteredBooks = sortBooks(filteredBooks);
            renderBooks();
        };

        window.setBookSort = function (value) {
            sortMode = value;
            window.applyFilters();
        };

        const categoryFilters = document.getElementById('category-filters');
        if (!categoryFilters) return;

        const wrapper = document.createElement('div');
        wrapper.className = 'flex justify-center mt-5';
        wrapper.innerHTML = `
            <label class="inline-flex items-center gap-3 bg-white border border-slate-200/70 rounded-2xl px-4 py-2.5 shadow-sm">
                <span class="text-[10px] font-black text-slate-400 uppercase tracking-widest whitespace-nowrap">
                    <i class="fas fa-arrow-down-wide-short mr-2 text-indigo-500"></i>Raða eftir
                </span>
                <select id="book-sort" onchange="setBookSort(this.value)"
                    class="bg-transparent text-slate-700 text-xs font-bold outline-none cursor-pointer pr-2">
                    <option value="default">Sjálfgefin röð</option>
                    <option value="title-asc">Titill A–Ö</option>
                    <option value="title-desc">Titill Ö–A</option>
                    <option value="author-asc">Höfundur A–Ö</option>
                    <option value="pages-asc">Fæstar blaðsíður</option>
                    <option value="pages-desc">Flestar blaðsíður</option>
                </select>
            </label>`;

        categoryFilters.parentElement.appendChild(wrapper);

        window.applyFilters();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', installSorting);
    } else {
        installSorting();
    }
})();
