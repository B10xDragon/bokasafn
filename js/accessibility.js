let activeDialog = null;
const DIALOG_CONTENT_IDS = {
    'desc-modal': 'desc-modal-content',
    'recommend-modal': 'recommend-modal-content',
    'stop-confirm-modal': 'stop-confirm-modal-content'
};

function dialogFocusable(content) {
    return [...content.querySelectorAll('button, input, select, textarea, a[href], [tabindex="0"]')]
        .filter(element => !element.disabled && !element.closest('[inert]') && element.getClientRects().length);
}

function focusDialog(content) {
    // A mobile book dialog can be taller than the viewport. Focusing its review
    // textarea immediately scrolls past the title, cover and close control.
    if (content.id === 'desc-modal-content') {
        content.focus({ preventScroll: true });
        content.scrollTop = 0;
        return;
    }
    const target = content.querySelector('input, textarea') || dialogFocusable(content)[0] || content;
    target.focus();
}

function prepareDialog(modal, content) {
    if (!content || activeDialog?.modal === modal) return;
    // Background live regions are inert while a modal is open. Announce the
    // same validation/save messages inside the active dialog as well.
    if (!content.querySelector('[data-dialog-status]')) {
        const status = document.createElement('div');
        status.dataset.dialogStatus = '';
        status.className = 'sr-only';
        status.setAttribute('role', 'status');
        status.setAttribute('aria-live', 'polite');
        status.setAttribute('aria-atomic', 'true');
        content.appendChild(status);
    }
    const trigger = document.activeElement;
    document.getElementById('appearance-panel')?.classList.add('hidden');
    document.getElementById('nav-appearance')?.setAttribute('aria-expanded', 'false');
    const background = [...document.body.children].filter(element =>
        element !== modal && !['SCRIPT', 'STYLE'].includes(element.tagName));
    const previousInert = background.map(element => element.inert);
    background.forEach(element => { element.inert = true; });
    activeDialog = { modal, content, trigger, background, previousInert };
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
}

function restoreDialogFocus(modal) {
    if (activeDialog?.modal !== modal) return;
    const { trigger, background, previousInert } = activeDialog;
    background.forEach((element, index) => { element.inert = previousInert[index]; });
    activeDialog = null;
    document.body.style.overflow = '';
    // A filter may have removed the original card. Use the persistent search field.
    if (trigger?.isConnected && !trigger.closest('.hidden')) trigger.focus();
    else document.getElementById('book-search')?.focus();
    modal.setAttribute('aria-hidden', 'true');
}

document.addEventListener('keydown', event => {
    if (activeDialog) {
        if (event.key === 'Escape') {
            event.preventDefault();
            closeModal(activeDialog.modal.id, DIALOG_CONTENT_IDS[activeDialog.modal.id]);
        } else if (event.key === 'Tab') {
            const { content } = activeDialog;
            const elements = dialogFocusable(content);
            const first = elements[0] || content;
            const last = elements.at(-1) || content;
            if (event.shiftKey && (document.activeElement === first || document.activeElement === content)) {
                event.preventDefault(); last.focus();
            } else if (!event.shiftKey && (document.activeElement === last || !content.contains(document.activeElement))) {
                event.preventDefault(); first.focus();
            }
        }
        return;
    }
    if (event.key === 'Escape') {
        const appearance = document.getElementById('appearance-panel');
        if (!appearance.classList.contains('hidden')) {
            toggleAppearancePanel();
            document.getElementById('nav-appearance').focus();
        }
        const suggestions = document.getElementById('search-suggestions');
        if (suggestions.contains(document.activeElement)) document.getElementById('book-search').focus();
        suggestions.classList.add('hidden');
    }
    const target = event.target.closest('[role="button"]');
    if (target && (event.key === 'Enter' || event.key === ' ') && event.target === target) {
        event.preventDefault(); target.click();
    }
    if (event.key === 'ArrowDown' && event.target.id === 'book-search') {
        const suggestions = document.getElementById('search-suggestions');
        if (!suggestions.classList.contains('hidden')) {
            event.preventDefault(); suggestions.querySelector('[tabindex="0"]')?.focus();
        }
    }
    if (event.target.matches('#search-suggestions [role="button"]') && ['ArrowDown', 'ArrowUp'].includes(event.key)) {
        event.preventDefault();
        const next = event.key === 'ArrowDown' ? event.target.nextElementSibling : event.target.previousElementSibling;
        (next || document.getElementById('book-search')).focus();
    }
    if (event.key === 'Enter' && event.target.id === 'personal-goal-input') addPersonalGoal();
});

document.addEventListener('focusin', event => {
    if (activeDialog && !activeDialog.content.contains(event.target)) focusDialog(activeDialog.content);
});

// Keep focus on the equivalent control when filtering/sorting replaces cards.
function rememberBookFocus() {
    const element = document.activeElement;
    if (!element?.closest('#book-grid')) return null;
    return { id: element.closest('[data-book-id]')?.dataset.bookId,
        action: element.dataset.action || 'info' };
}
function restoreBookFocus(focus) {
    if (!focus) return;
    const card = [...document.querySelectorAll('#book-grid .book-card')]
        .find(card => card.dataset.bookId === focus.id);
    const target = card?.querySelector(`[data-action="${focus.action}"]`) || document.getElementById('book-search');
    target?.focus();
}
