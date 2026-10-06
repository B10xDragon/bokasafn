function toggleAppearancePanel() {
    const panel = document.getElementById("appearance-panel");

    if (!panel) return;

    panel.classList.toggle("hidden");
    document.getElementById('nav-appearance')?.setAttribute('aria-expanded', String(!panel.classList.contains('hidden')));
    if (!panel.classList.contains('hidden')) {
        positionAppearancePanel();
        panel.querySelector('button')?.focus();
    }
}

function positionAppearancePanel() {
    const panel = document.getElementById('appearance-panel');
    const nav = document.querySelector('nav');
    if (!panel || !nav) return;
    // The mobile navbar is taller than the desktop navbar; the old fixed 82px
    // position covered the toggle button and made the menu impossible to close.
    const top = Math.min(nav.getBoundingClientRect().bottom + 8, window.innerHeight - 96);
    panel.style.setProperty('top', Math.max(8, top) + 'px', 'important');
    panel.style.maxHeight = Math.max(80, window.innerHeight - top - 16) + 'px';
    panel.style.overflowY = 'auto';
}

window.addEventListener('resize', positionAppearancePanel);
document.addEventListener('click', event => {
    const panel = document.getElementById('appearance-panel');
    const button = document.getElementById('nav-appearance');
    if (panel && button && !panel.contains(event.target) && !button.contains(event.target)) {
        panel.classList.add('hidden');
        button.setAttribute('aria-expanded', 'false');
    }
});
