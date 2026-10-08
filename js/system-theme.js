// Apply the preference before rendering; system changes only affect system mode.
const BOKASAFN_SYSTEM_THEME = window.matchMedia('(prefers-color-scheme: dark)');
const BOKASAFN_THEMES = ['system', 'light', 'green', 'dark', 'purple', 'orange'];
let bokasafnThemePreference = 'system';
try {
    const saved = localStorage.getItem('bokasafn-theme');
    if (BOKASAFN_THEMES.includes(saved)) bokasafnThemePreference = saved;
} catch (error) {
    console.warn('Ekki hægt að lesa útlitsstillingu.', error);
}
function resolveBokasafnTheme(theme) {
    return theme === 'system' ? (BOKASAFN_SYSTEM_THEME.matches ? 'dark' : 'light') : theme;
}
document.body.dataset.theme = resolveBokasafnTheme(bokasafnThemePreference);
BOKASAFN_SYSTEM_THEME.addEventListener('change', () => {
    if (bokasafnThemePreference === 'system') document.body.dataset.theme = resolveBokasafnTheme('system');
});
