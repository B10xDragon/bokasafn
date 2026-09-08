/* BOKASAFN_THEME_SYSTEM */

const BOKASAFN_THEMES = [
    "system",
    "light",
    "green",
    "dark",
    "purple",
    "orange"
];

const BOKASAFN_SYSTEM_THEME = window.matchMedia('(prefers-color-scheme: dark)');

function resolveBokasafnTheme(theme) {
    if (theme === "system") {
        return BOKASAFN_SYSTEM_THEME.matches ? "dark" : "light";
    }

    return theme;
}

function ensureSystemThemeOption() {
    const firstThemeOption = document.querySelector('.theme-option');
    const container = firstThemeOption?.parentElement;

    if (!container || container.querySelector('[data-theme="system"]')) {
        return;
    }

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'theme-option';
    button.dataset.theme = 'system';
    button.textContent = 'Kerfi';
    button.addEventListener('click', () => setBokasafnTheme('system'));

    container.prepend(button);
}

function setBokasafnTheme(theme) {
    if (!BOKASAFN_THEMES.includes(theme)) {
        theme = "light";
    }

    document.body.dataset.theme = resolveBokasafnTheme(theme);

    localStorage.setItem("bokasafn-theme", theme);

    document.querySelectorAll(".theme-option").forEach(button => {
        button.classList.toggle(
            "active",
            button.dataset.theme === theme
        );
    });
}

function loadBokasafnTheme() {
    ensureSystemThemeOption();

    const saved =
        localStorage.getItem("bokasafn-theme") || "light";

    setBokasafnTheme(saved);
}

document.addEventListener("DOMContentLoaded", loadBokasafnTheme);

BOKASAFN_SYSTEM_THEME.addEventListener('change', () => {
    if (localStorage.getItem('bokasafn-theme') === 'system') {
        document.body.dataset.theme = resolveBokasafnTheme('system');
    }
});

// Load optional library enhancements after the main app has been defined.
const sortingScript = document.createElement("script");
sortingScript.src = "js/sorting.js";
sortingScript.defer = true;
document.head.appendChild(sortingScript);
