/* BOKASAFN_THEME_SYSTEM */
function ensureSystemThemeOption() {
    const first = document.querySelector('.theme-option');
    const container = first?.parentElement;
    if (!container || container.querySelector('[data-theme="system"]')) return;
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'theme-option';
    button.dataset.theme = 'system';
    button.textContent = 'Kerfi';
    button.addEventListener('click', () => setBokasafnTheme('system'));
    container.prepend(button);
}
function renderBokasafnTheme() {
    document.body.dataset.theme = resolveBokasafnTheme(bokasafnThemePreference);
    document.querySelectorAll('.theme-option').forEach(button => {
        const selected = button.dataset.theme === bokasafnThemePreference;
        button.classList.toggle('active', selected);
        button.setAttribute('aria-pressed', String(selected));
    });
}
function setBokasafnTheme(theme) {
    bokasafnThemePreference = BOKASAFN_THEMES.includes(theme) ? theme : 'system';
    renderBokasafnTheme();
    try {
        localStorage.setItem('bokasafn-theme', bokasafnThemePreference);
    } catch (error) {
        showToast('Útlitið breyttist en ekki tókst að vista stillinguna.', 'error');
    }
}
document.addEventListener('DOMContentLoaded', () => {
    ensureSystemThemeOption();
    renderBokasafnTheme();
});
