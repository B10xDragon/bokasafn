function toggleAppearancePanel() {
    const panel = document.getElementById("appearance-panel");

    if (!panel) return;

    panel.classList.toggle("hidden");
    document.getElementById('nav-appearance')?.setAttribute('aria-expanded', String(!panel.classList.contains('hidden')));
    if (!panel.classList.contains('hidden')) panel.querySelector('button')?.focus();
}
