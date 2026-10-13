// Literary categories are separate from audience, translation and physical format.
const genreRegistry = globalThis.BOKASAFN_GENRES || {genres:[], aliases:{}, legacyFacets:{}};
const genreKey = value => typeof value === 'string' ? value.normalize('NFC').trim().toLocaleLowerCase('is') : '';
const genreNames = new Set(genreRegistry.genres.map(g => g.name));
const genreQueries = new Map([
    ...genreRegistry.genres.map(g => [genreKey(g.name), g.name]),
    ...Object.entries(genreRegistry.aliases).map(([old, current]) => [genreKey(old), current]),
    ...Object.keys(genreRegistry.legacyFacets).map(old => [genreKey(old), old])
]);
function normalizeGenreFilter(value) {
    return genreQueries.get(genreKey(value)) || (typeof value === 'string' ? value.normalize('NFC').trim() : '');
}
function normalizeGenreSelection(value) {
    // Historical mystery queries cover crime and non-crime mysteries without
    // claiming that every police investigation is a horror story.
    return ['leyndardómar','ráðgáta'].includes(genreKey(value)) ? 'Leyndardómar' : normalizeGenreFilter(value);
}
function bookGenres(book) {
    // Active records are already validated. Archived records retain their raw data,
    // but spelling aliases can be interpreted without counting age/language as genres.
    return [...new Set((Array.isArray(book.categories) ? book.categories : [])
        .map(c => ['leyndardómar','ráðgáta'].includes(genreKey(c)) && book.categories.some(x => ['glæpasögur','glæpir','glæpasaga'].includes(genreKey(x))) ? 'Spenna og glæpasögur' : normalizeGenreFilter(c)).filter(name => genreNames.has(name)))];
}
function matchesGenre(book, query) {
    if (!query) return true;
    if (['leyndardómar','ráðgáta'].includes(genreKey(query))) {
        const details = book.classification?.detailedGenres || book.categories || [];
        return details.some(c => ['leyndardómar','ráðgáta'].includes(genreKey(c))) || (!book.classification?.detailedGenres && bookGenres(book).includes('Hrollvekjur og ráðgátur'));
    }
    const name = normalizeGenreFilter(query), facet = genreRegistry.legacyFacets[name];
    if (!facet) return bookGenres(book).includes(name);
    const metadata = book.classification;
    if (!metadata) return (book.categories || []).some(c => genreRegistry.legacyFacets[normalizeGenreFilter(c)] === facet || (facet === 'fiction' && genreRegistry.legacyFacets[normalizeGenreFilter(c)] === 'novel'));
    if (facet === 'audience') return Boolean(metadata.audienceTags?.includes('Ungmenni'));
    if (facet === 'translation') return metadata.translated;
    if (facet === 'novel') return metadata.literaryForm === 'novel' || Boolean(metadata.legacyFacets?.includes('Skáldsögur'));
    if (metadata.legacyFacets?.includes('Skáldverk')) return true;
    return ['novel','short-stories','poetry','drama','mixed','fiction'].includes(metadata.literaryForm);
}
