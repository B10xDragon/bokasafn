// Version 15 uses stable catalog IDs. Keep library_v14 untouched as a backup.
const LIBRARY_STORAGE_KEY = 'library_v15';
let storageWritable = true;
let userDataLoaded = false;
let lastStorageWarning = 0;

function escapeHTML(value) {
    return String(value ?? '').replace(/[&<>"']/g, character => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[character]);
}

function isRecord(value) {
    return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function nonnegativeNumber(value, fallback = 0) {
    return typeof value === 'number' && Number.isFinite(value) && value >= 0 ? value : fallback;
}

function validDateKey(value) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
    const date = new Date(value + 'T12:00:00');
    return Number.isFinite(date.getTime()) && getLocalYYYYMMDD(date) === value;
}

function normalizeProgress(value) {
    const result = Object.create(null);
    if (isRecord(value)) {
        for (const [date, seconds] of Object.entries(value)) {
            if (validDateKey(date)) result[date] = Math.floor(nonnegativeNumber(seconds));
        }
    }
    return result;
}

function emptyTimerState() {
    return { active: false, paused: false, startTime: null, elapsedBeforePause: 0,
        dailyMilliseconds: Object.create(null), interval: null };
}

function normalizeSession(value) {
    const state = emptyTimerState();
    if (!isRecord(value) || value.active !== true) return state;
    if (!Number.isFinite(value.startTime) || value.startTime < 0 || value.startTime > Date.now()) return state;
    state.active = true;
    state.paused = value.paused === true;
    state.startTime = value.startTime;
    state.dailyMilliseconds = normalizeProgress(value.dailyMilliseconds);
    state.elapsedBeforePause = Object.values(state.dailyMilliseconds).reduce((sum, ms) => sum + ms, 0);
    return state;
}

function normalizeUserData(raw) {
    const source = isRecord(raw) ? raw : {};
    const legacy = source.version !== 15;
    const unresolved = isRecord(source.unresolved) ? source.unresolved : {};
    const result = { version: 15, liked: [], read: [], reviews: Object.create(null),
        totalSeconds: Math.floor(nonnegativeNumber(source.totalSeconds)),
        dailyProgress: normalizeProgress(source.dailyProgress),
        minutesGoal: nonnegativeNumber(source.minutesGoal),
        goalType: ['daily', 'weekly', 'monthly'].includes(source.goalType) ? source.goalType : 'daily',
        personalGoals: [], unresolved: { liked: [], read: [], reviews: Object.create(null) },
        session: legacy ? null : source.session };

    // Unknown titles are retained and retried on future loads; never silently discard them.
    function resolve(reference, titleReference) {
        if (titleReference && typeof reference === 'string') {
            const book = allBooks.find(book => book.title === reference);
            return book ? book.id : null;
        }
        return Number.isSafeInteger(reference) && reference >= 0 ? reference : null;
    }
    for (const field of ['liked', 'read']) {
        for (const reference of Array.isArray(source[field]) ? source[field] : []) {
            const id = resolve(reference, legacy);
            if (id !== null) result[field].push(id);
            else if (typeof reference === 'string') result.unresolved[field].push(reference);
        }
        for (const title of Array.isArray(unresolved[field]) ? unresolved[field] : []) {
            const id = resolve(title, true);
            if (id !== null) result[field].push(id);
            else if (typeof title === 'string') result.unresolved[field].push(title);
        }
        result[field] = [...new Set(result[field])];
        result.unresolved[field] = [...new Set(result.unresolved[field])];
    }
    function addReviews(reviews, titleReference) {
        if (!isRecord(reviews)) return;
        for (const [reference, review] of Object.entries(reviews)) {
            if (!isRecord(review) || !Number.isInteger(review.rating) || review.rating < 1 || review.rating > 5) continue;
            const clean = { rating: review.rating, comment: typeof review.comment === 'string' ? review.comment : '',
                date: typeof review.date === 'string' ? review.date : '' };
            const id = resolve(titleReference ? reference : (/^\d+$/.test(reference) ? Number(reference) : null), titleReference);
            if (id !== null) {
                if (!Object.hasOwn(result.reviews, id)) result.reviews[id] = clean;
            } else if (titleReference) result.unresolved.reviews[reference] = clean;
        }
    }
    addReviews(source.reviews, legacy);
    addReviews(unresolved.reviews, true);
    const goalIds = new Set();
    for (const goal of Array.isArray(source.personalGoals) ? source.personalGoals : []) {
        if (!isRecord(goal) || typeof goal.text !== 'string') continue;
        let id = Number.isSafeInteger(goal.id) && goal.id >= 0 ? goal.id : Date.now();
        while (goalIds.has(id)) id++;
        goalIds.add(id);
        result.personalGoals.push({ id, text: goal.text, completed: goal.completed === true });
    }
    return typeof normalizeExtensions === 'function' ? normalizeExtensions(source, result) : result;
}

function warnStorage() {
    if (!lastStorageWarning || Date.now() - lastStorageWarning > 10000) {
        showToast('Ekki tókst að vista gögn. Haltu síðunni opinni og athugaðu vafrageymsluna.', 'error');
        lastStorageWarning = Date.now();
    }
}

function saveUserData() {
    // Leaving or interacting with a page before its catalog loads must never
    // replace saved progress with the initial empty in-memory state.
    if (!userDataLoaded) return false;
    if (!storageWritable) { warnStorage(); return false; }
    if (typeof refreshMilestones === 'function') refreshMilestones();
    const { interval, ...session } = timerState;
    userData.session = timerState.active ? session : null;
    try {
        localStorage.setItem(LIBRARY_STORAGE_KEY, JSON.stringify(userData));
        return true;
    } catch (error) {
        console.warn('Ekki hægt að vista í LocalStorage.', error);
        warnStorage();
        return false;
    }
}

function loadUserData() {
    let raw = null;
    try {
        const saved = localStorage.getItem(LIBRARY_STORAGE_KEY);
        const legacy = localStorage.getItem('library_v14');
        if (saved !== null) {
            try {
                raw = JSON.parse(saved);
                if (isRecord(raw) && raw.version > 15) {
                    storageWritable = false;
                    warnStorage();
                    raw = legacy !== null ? JSON.parse(legacy) : {};
                } else if (!isRecord(raw) || raw.version !== 15) throw new Error('Óþekkt gagnasnið');
            } catch (error) {
                // Preserve unreadable/newer data before recovering the old copy.
                const recoveryKey = localStorage.getItem('library_v15_recovery') === null
                    ? 'library_v15_recovery' : 'library_v15_recovery_' + Date.now();
                localStorage.setItem(recoveryKey, saved);
                raw = legacy !== null ? JSON.parse(legacy) : {};
                showToast('Vistað afrit var endurheimt. Ólesanleg gögn eru varðveitt í vafranum.', 'error');
            }
        } else if (legacy !== null) raw = JSON.parse(legacy);
    } catch (error) {
        storageWritable = false;
        warnStorage();
    }
    userData = normalizeUserData(raw);
    userDataLoaded = true;
    timerState = normalizeSession(userData.session);
    if (timerState.active && !timerState.paused) timerState.interval = setInterval(updateTimerDisplay, 1000);
    updateTimerDisplay();
    updateTimerUI();
    // Persist the migration immediately, without altering the old backup.
    if (storageWritable) saveUserData();
}

// Split elapsed time at local midnight, including DST changes.
function checkpointTimer(now = Date.now()) {
    if (!timerState.active || timerState.paused) return;
    let cursor = timerState.startTime;
    if (!Number.isFinite(cursor) || now < cursor) { timerState.startTime = now; return; }
    while (cursor < now) {
        const date = new Date(cursor);
        const midnight = new Date(date.getFullYear(), date.getMonth(), date.getDate() + 1).getTime();
        const end = Math.min(now, midnight);
        const key = getLocalYYYYMMDD(date);
        timerState.dailyMilliseconds[key] = (timerState.dailyMilliseconds[key] || 0) + end - cursor;
        timerState.elapsedBeforePause += end - cursor;
        cursor = end;
    }
    timerState.startTime = now;
}

const COVER_PLACEHOLDER = 'Resources/Assets/cover-placeholder.svg';
function finishCoverLoading(image) {
    image.classList.remove('opacity-0');
    image.parentElement?.classList.remove('shimmer-placeholder');
}
function handleCoverError(image) {
    image.onerror = null; // Even a missing fallback cannot trigger a retry loop.
    image.src = COVER_PLACEHOLDER;
    finishCoverLoading(image);
}
