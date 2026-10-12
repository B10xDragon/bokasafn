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
function bookGenres(book) {
    // Active records are already validated. Archived records retain their raw data,
    // but spelling aliases can be interpreted without counting age/language as genres.
    if (book.classification) return book.categories || [];
    return [...new Set((Array.isArray(book.categories) ? book.categories : [])
        .map(normalizeGenreFilter).filter(name => genreNames.has(name)))];
}
function matchesGenre(book, query) {
    if (!query) return true;
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
