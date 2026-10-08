function newDataId() {
  return (
    globalThis.crypto?.randomUUID?.() ||
    Date.now().toString(36) +
      "-" +
      Math.random().toString(36).slice(2) +
      "-" +
      Math.random().toString(36).slice(2)
  );
}
const BUILTIN_CHALLENGES = {
  month: ["books", 3, "Þrjár bækur í þessum mánuði", true],
  pages: ["pages", 500, "500 blaðsíður", false],
  fantasy: ["fantasy", 1, "Lestu fantasíubók", false],
  author: ["author", 1, "Uppgötvaðu nýjan höfund", false],
};

function existingBuiltInChallenge(type, now = new Date()) {
  const definition = BUILTIN_CHALLENGES[type];
  if (!definition) return null;
  const [kind, target, title, monthly] = definition;
  const start = getLocalYYYYMMDD(
    new Date(now.getFullYear(), now.getMonth(), 1),
  );
  const end = getLocalYYYYMMDD(
    new Date(now.getFullYear(), now.getMonth() + 1, 0),
  );
  return (
    userData.challenges.find(
      (c) =>
        c.kind === kind &&
        c.target === target &&
        c.title === title &&
        (monthly ? c.start === start && c.end === end : !c.completed && !c.end),
    ) || null
  );
}

// Collapse identical cards only in the view. Every stored record stays in the
// backup, including IDs, baselines and completion dates from earlier versions.
function challengeDisplayGroups(challenges) {
  const groups = new Map();
  for (const challenge of challenges) {
    const key = JSON.stringify({
      title: challenge.title,
      kind: challenge.kind,
      target: challenge.target,
      start: challenge.start,
      end: challenge.end,
      baseline: [...new Set(challenge.baseline)].sort((a, b) => a - b),
      baselineSeconds: challenge.baselineSeconds,
      historyMode: challenge.historyMode,
      completed: challenge.completed,
    });
    if (!groups.has(key)) groups.set(key, { challenge, ids: [] });
    groups.get(key).ids.push(challenge.id);
  }
  return [...groups.values()];
}
// Additive v15 extensions: old totals stay authoritative; unknown history stays unknown.
function normalizeExtensions(source, result) {
  result.completedDates = Object.create(null);
  for (const [id, date] of Object.entries(
    isRecord(source.completedDates) ? source.completedDates : {},
  )) {
    if (/^\d+$/.test(id) && validDateKey(date))
      result.completedDates[id] = date;
  }
  result.sessions = [];
  const ids = new Set();
  for (const s of Array.isArray(source.sessions) ? source.sessions : []) {
    if (
      !isRecord(s) ||
      typeof s.id !== "string" ||
      s.id.length > 100 ||
      ids.has(s.id) ||
      !validDateKey(s.date) ||
      !Number.isSafeInteger(s.seconds) ||
      s.seconds <= 0
    )
      continue;
    ids.add(s.id);
    result.sessions.push({ id: s.id, date: s.date, seconds: s.seconds });
  }
  result.achievements = Object.create(null);
  for (const [id, date] of Object.entries(
    isRecord(source.achievements) ? source.achievements : {},
  ))
    if (validDateKey(date)) result.achievements[id] = date;
  result.challenges = [];
  const challengeIds = new Set();
  for (const c of Array.isArray(source.challenges) ? source.challenges : []) {
    if (
      !isRecord(c) ||
      typeof c.id !== "string" ||
      c.id.length > 100 ||
      challengeIds.has(c.id) ||
      typeof c.title !== "string" ||
      !["books", "pages", "minutes", "fantasy", "author"].includes(c.kind) ||
      !Number.isSafeInteger(c.target) ||
      c.target < 1 ||
      c.target > 1000000 ||
      !validDateKey(c.start)
    )
      continue;
    if (c.end != null && (!validDateKey(c.end) || c.end < c.start)) continue;
    challengeIds.add(c.id);
    result.challenges.push({
      id: c.id,
      title: c.title,
      kind: c.kind,
      target: c.target,
      start: c.start,
      end: c.end || null,
      baseline: Array.isArray(c.baseline)
        ? c.baseline.filter((x) => Number.isSafeInteger(x) && x >= 0)
        : [],
      baselineSeconds: Math.floor(nonnegativeNumber(c.baselineSeconds)),
      historyMode: ["all", "since-start"].includes(c.historyMode)
        ? c.historyMode
        : null,
      completed: validDateKey(c.completed) ? c.completed : null,
    });
  }
  return result;
}
function activitySummary(now = new Date()) {
  const today = getLocalYYYYMMDD(now);
  const keys = Object.keys(userData.dailyProgress)
    .filter((d) => d <= today && userData.dailyProgress[d] > 0)
    .sort();
  if (!keys.length)
    return { current: 0, longest: 0, active: 0, recordSeconds: 0 };
  let longest = 0,
    run = 0,
    yesterdayRun = 0,
    rolling = 0,
    monthTotal = 0,
    month = null;
  const windowSeconds = [];
  const cursor = new Date(keys[0] + "T12:00:00");
  for (
    ;
    getLocalYYYYMMDD(cursor) <= today;
    cursor.setDate(cursor.getDate() + 1)
  ) {
    const key = getLocalYYYYMMDD(cursor),
      daySeconds = userData.dailyProgress[key] || 0;
    rolling += daySeconds;
    windowSeconds.push(daySeconds);
    if (windowSeconds.length > 7) rolling -= windowSeconds.shift();
    if (key.slice(0, 7) !== month) {
      month = key.slice(0, 7);
      monthTotal = 0;
    }
    monthTotal += daySeconds;
    const target = userData.minutesGoal > 0 ? userData.minutesGoal * 60 : 600;
    const seconds =
      userData.minutesGoal > 0 && userData.goalType === "weekly"
        ? rolling
        : userData.minutesGoal > 0 && userData.goalType === "monthly"
          ? monthTotal
          : daySeconds;
    yesterdayRun = run;
    run = seconds >= target ? run + 1 : 0;
    longest = Math.max(longest, run);
  }
  return {
    current: run || yesterdayRun,
    longest,
    active: keys.length,
    recordSeconds: keys.reduce(
      (max, k) => Math.max(max, userData.dailyProgress[k]),
      0,
    ),
  };
}
function readingMetrics() {
  const books = historyBooks().filter((b) => userData.read.includes(b.id));
  const ratings = Object.values(userData.reviews).map((r) => r.rating);
  const sessions = userData.sessions || [];
  return {
    books: books.length,
    pages: books.reduce((n, b) => n + (Number(b.pages) || 0), 0),
    seconds: userData.totalSeconds,
    averageRating: ratings.length
      ? ratings.reduce((a, b) => a + b, 0) / ratings.length
      : null,
    averageSession: sessions.length
      ? sessions.reduce((n, s) => n + s.seconds, 0) / sessions.length
      : null,
    genres: new Set(books.flatMap((b) => b.categories)).size,
    ...activitySummary(),
  };
}
const ACHIEVEMENTS = [
  ["first", "Fyrsta bókin", "books", 1],
  ["ten-books", "Tíu bækur", "books", 10],
  ["twenty-books", "Tuttugu bækur", "books", 20],
  ["100-pages", "100 blaðsíður", "pages", 100],
  ["1000-pages", "1.000 blaðsíður", "pages", 1000],
  ["5000-pages", "5.000 blaðsíður", "pages", 5000],
  ["10-hours", "Tíu klukkustundir", "seconds", 36000],
  ["50-hours", "Fimmtíu klukkustundir", "seconds", 180000],
  ["seven-days", "Sjö daga markmiðaruna", "longest", 7],
  ["thirty-days", "Þrjátíu virkir lestrardagar", "active", 30],
  ["five-genres", "Fimm bókmenntaflokkar", "genres", 5],
];
function challengeProgress(c) {
  // The first discovery challenges recognise reading already completed, even
  // legacy read flags without dates. Repeat attempts require new reading.
  const definition = BUILTIN_CHALLENGES[c.kind];
  const includesHistory =
    ["fantasy", "author"].includes(c.kind) &&
    definition &&
    c.title === definition[2] &&
    c.target === definition[1] &&
    !c.end &&
    c.historyMode !== "since-start";
  const books = historyBooks().filter(
    (b) =>
      userData.read.includes(b.id) &&
      (includesHistory ||
        (!c.baseline.includes(b.id) &&
          userData.completedDates[b.id] >= c.start &&
          (!c.end || userData.completedDates[b.id] <= c.end))),
  );
  if (c.kind === "books") return books.length;
  if (c.kind === "pages")
    return books.reduce((n, b) => n + (Number(b.pages) || 0), 0);
  if (c.kind === "fantasy")
    return books.filter((b) => b.categories.includes("Fantasía")).length;
  if (c.kind === "author") {
    const previous = new Set(
      historyBooks()
        .filter((b) => !includesHistory && c.baseline.includes(b.id))
        .map((b) => b.author),
    );
    return new Set(
      books.filter((b) => !previous.has(b.author)).map((b) => b.author),
    ).size;
  }
  return Math.max(
    0,
    Math.floor(
      (Object.entries(userData.dailyProgress)
        .filter(([d]) => d >= c.start && (!c.end || d <= c.end))
        .reduce((n, [, s]) => n + s, 0) -
        (c.baselineSeconds || 0)) /
        60,
    ),
  );
}
function refreshMilestones() {
  if (!userData.achievements) return;
  const m = readingMetrics(),
    today = getLocalYYYYMMDD(new Date());
  for (const [id, , field, target] of ACHIEVEMENTS)
    if (m[field] >= target && !userData.achievements[id])
      userData.achievements[id] = today;
  for (const c of userData.challenges)
    if (!c.completed && challengeProgress(c) >= c.target) c.completed = today;
}
function recommendations(limit = 6) {
  const cats = new Map(),
    authors = new Map();
  for (const b of allBooks) {
    const rating = userData.reviews[b.id]?.rating;
    const weight = rating
      ? rating >= 4
        ? rating - 2
        : rating <= 2
          ? -4
          : 0
      : userData.liked.includes(b.id)
        ? 1
        : userData.read.includes(b.id)
          ? 0.25
          : 0;
    for (const c of b.categories) cats.set(c, (cats.get(c) || 0) + weight);
    authors.set(b.author, (authors.get(b.author) || 0) + weight * 2);
  }
  return allBooks
    .filter(
      (b) =>
        !userData.read.includes(b.id) && !(userData.reviews[b.id]?.rating <= 2),
    )
    .map((b) => {
      const genre = b.categories.reduce((n, c) => n + (cats.get(c) || 0), 0),
        author = authors.get(b.author) || 0,
        wish = userData.liked.includes(b.id) ? 4 : 0;
      return {
        book: b,
        score: genre + author + wish,
        reason: wish
          ? "Á óskalistanum þínum"
          : author > 0
            ? "Höfundur sem þér líkar"
            : genre > 0
              ? "Flokkar sem þú hefur áhuga á"
              : "Uppgötvaðu nýja bók",
      };
    })
    .sort((a, b) => b.score - a.score || a.book.id - b.book.id)
    .slice(0, limit);
}
function matchesAdvanced(b, f) {
  const pages = Number(b.pages) || 0,
    rating = userData.reviews[b.id]?.rating || 0;
  return (
    (!f.state ||
      (f.state === "unread" && !userData.read.includes(b.id)) ||
      (f.state === "read" && userData.read.includes(b.id)) ||
      (f.state === "wishlist" && userData.liked.includes(b.id))) &&
    (!f.min || pages >= f.min) &&
    (!f.max || (pages > 0 && pages <= f.max)) &&
    (!f.rating || rating >= f.rating) &&
    (!f.author || b.author === f.author) &&
    (!f.category || b.categories.includes(f.category))
  );
}
function chooseRandom(books, random = Math.random) {
  return books.length
    ? books[Math.min(books.length - 1, Math.floor(random() * books.length))]
    : null;
}
function parseBackup(text) {
  if (typeof text !== "string") throw Error("Ógilt afrit: texta vantar.");
  let raw;
  try {
    raw = JSON.parse(text);
  } catch (error) {
    throw Error("Ógilt afrit: gagnatextinn er ekki gilt JSON.");
  }
  if (!isRecord(raw)) throw Error("Ógilt afrit.");
  const envelope = raw.format === "bokasafn-backup";
  if (raw.format != null && !envelope) throw Error("Óþekkt afritssnið.");
  if (envelope && ![1, 2].includes(raw.backupVersion))
    throw Error("Þetta afrit er úr nýrri útgáfu.");
  const data = envelope ? raw.data : raw;
  if (
    !isRecord(data) ||
    (data.version != null && ![14, 15].includes(data.version))
  )
    throw Error("Óþekkt gagnasnið.");
  for (const field of [
    "liked",
    "read",
    "personalGoals",
    "sessions",
    "challenges",
  ])
    if (Object.hasOwn(data, field) && !Array.isArray(data[field]))
      throw Error("Ógilt gagnasvið: " + field);
  for (const field of [
    "reviews",
    "dailyProgress",
    "completedDates",
    "achievements",
    "unresolved",
  ])
    if (Object.hasOwn(data, field) && !isRecord(data[field]))
      throw Error("Ógilt gagnasvið: " + field);
  if (
    !["read", "liked", "dailyProgress", "reviews", "totalSeconds"].some((k) =>
      Object.hasOwn(data, k),
    )
  )
    throw Error("Engin lestrargögn fundust.");
  if (
    data.totalSeconds != null &&
    (!Number.isSafeInteger(data.totalSeconds) || data.totalSeconds < 0)
  )
    throw Error("Ógildur lestími.");
  for (const [d, s] of Object.entries(data.dailyProgress || {}))
    if (!validDateKey(d) || !Number.isSafeInteger(s) || s < 0)
      throw Error("Ógild lestrarsaga.");
  for (const r of Object.values(data.reviews || {}))
    if (
      !isRecord(r) ||
      !Number.isInteger(r.rating) ||
      r.rating < 1 ||
      r.rating > 5 ||
      (r.comment != null && typeof r.comment !== "string")
    )
      throw Error("Ógild umsögn.");
  for (const field of ['reviewConflicts', 'completionHistory']) {
    if (data[field] != null && !Array.isArray(data[field])) throw Error('Ógild varðveitt bókagögn.');
    for (const item of data[field] || []) {
      if (!isRecord(item) || !Number.isSafeInteger(item.bookId) || item.bookId < 0 ||
          !Number.isSafeInteger(item.sourceId) || item.sourceId < 0 ||
          (field === 'completionHistory' ? !validDateKey(item.date) :
            !Number.isInteger(item.rating) || item.rating < 1 || item.rating > 5 ||
            typeof item.comment !== 'string' || typeof item.date !== 'string'))
        throw Error('Ógild varðveitt bókagögn.');
    }
  }
  const legacy = data.version !== 15;
  for (const f of ["read", "liked"])
    for (const ref of data[f] || [])
      if (
        legacy ? typeof ref !== "string" : !Number.isSafeInteger(ref) || ref < 0
      )
        throw Error("Ógild bókatilvísun.");
  for (const g of data.personalGoals || [])
    if (
      !isRecord(g) ||
      typeof g.text !== "string" ||
      (g.completed != null && typeof g.completed !== "boolean")
    )
      throw Error("Ógilt persónulegt markmið.");
  if (
    data.minutesGoal != null &&
    (typeof data.minutesGoal !== "number" ||
      !Number.isFinite(data.minutesGoal) ||
      data.minutesGoal < 0)
  )
    throw Error("Ógilt markmið.");
  if (
    data.goalType != null &&
    !["daily", "weekly", "monthly"].includes(data.goalType)
  )
    throw Error("Ógilt tímabil.");
  for (const [id, d] of Object.entries(data.completedDates || {}))
    if (!/^\d+$/.test(id) || !validDateKey(d))
      throw Error("Ógild lokadagsetning.");
  for (const d of Object.values(data.achievements || {}))
    if (!validDateKey(d)) throw Error("Ógilt afrek.");
  if (
    !legacy &&
    Object.keys(data.reviews || {}).some(
      (id) => !/^\d+$/.test(id) || !Number.isSafeInteger(Number(id)),
    )
  )
    throw Error("Ógild umsagnartilvísun.");
  if (data.unresolved) {
    for (const f of ["read", "liked"])
      if (
        Object.hasOwn(data.unresolved, f) &&
        (!Array.isArray(data.unresolved[f]) ||
          data.unresolved[f].some((t) => typeof t !== "string"))
      )
        throw Error("Ógild eldri bókatilvísun.");
    if (
      Object.hasOwn(data.unresolved, "reviews") &&
      !isRecord(data.unresolved.reviews)
    )
      throw Error("Ógild eldri umsögn.");
    for (const r of Object.values(data.unresolved.reviews || {}))
      if (
        !isRecord(r) ||
        !Number.isInteger(r.rating) ||
        r.rating < 1 ||
        r.rating > 5 ||
        (r.comment != null && typeof r.comment !== "string")
      )
        throw Error("Ógild eldri umsögn.");
  }
  for (const c of data.challenges || []) {
    if (
      !isRecord(c) ||
      (c.historyMode != null &&
        !["all", "since-start"].includes(c.historyMode)) ||
      typeof c.title !== "string" ||
      (c.baseline != null &&
        (!Array.isArray(c.baseline) ||
          c.baseline.some((id) => !Number.isSafeInteger(id) || id < 0))) ||
      (c.baselineSeconds != null &&
        (!Number.isSafeInteger(c.baselineSeconds) || c.baselineSeconds < 0)) ||
      (c.completed != null &&
        (!validDateKey(c.completed) || c.completed < c.start))
    )
      throw Error("Ógild áskorun.");
  }
  if (envelope && raw.backupVersion === 2) {
    validateStorageSnapshot(raw.storage);
    if (data.session != null) {
      const session = data.session;
      if (
        !isRecord(session) ||
        typeof session.paused !== "boolean" ||
        !Number.isSafeInteger(session.startTime) ||
        !Number.isSafeInteger(session.elapsedBeforePause) ||
        session.elapsedBeforePause < 0 ||
        !isRecord(session.dailyMilliseconds)
      )
        throw Error("Ógild virk lestrarlota.");
      for (const [date, ms] of Object.entries(session.dailyMilliseconds))
        if (!validDateKey(date) || !Number.isSafeInteger(ms) || ms < 0)
          throw Error("Ógild saga virkrar lestrarlotu.");
      if (
        Object.values(session.dailyMilliseconds).reduce(
          (n, ms) => n + ms,
          0,
        ) !== session.elapsedBeforePause
      )
        throw Error("Ósamræmi í virkum lestíma.");
    }
    if (
      !["system", "light", "dark", "green", "purple", "orange"].includes(
        raw.preferences?.theme,
      )
    )
      throw Error("Ógild útlitsstilling.");
    if (
      data.session != null &&
      (!isRecord(data.session) ||
        data.session.active !== true ||
        !normalizeSession(data.session).active)
    )
      throw Error("Ógild virk lestrarlota.");
  }
  const normalized = normalizeUserData(data);
  if (
    (data.sessions || []).length !== normalized.sessions.length ||
    (data.challenges || []).length !== normalized.challenges.length
  )
    throw Error("Ógild lota eða áskorun.");
  return {
    data: normalized,
    theme:
      envelope &&
      ["system", "light", "dark", "green", "purple", "orange"].includes(
        raw.preferences?.theme,
      )
        ? raw.preferences.theme
        : null,
    raw,
  };
}
function mergeReadingData(existing, incoming) {
  const a = normalizeUserData(existing),
    b = normalizeUserData(incoming);
  a.read = [...new Set([...a.read, ...b.read])];
  a.liked = [...new Set([...a.liked, ...b.liked])];
  for (const [id, r] of Object.entries(b.reviews))
    if (!Object.hasOwn(a.reviews, id)) a.reviews[id] = r;
    else if (JSON.stringify(a.reviews[id]) !== JSON.stringify(r)) appendReviewConflict(a, id, id, r);
  for (const r of b.reviewConflicts) appendReviewConflict(a, r.bookId, r.sourceId, r);
  for (const h of b.completionHistory)
    if (!a.completionHistory.some(x => JSON.stringify(x) === JSON.stringify(h))) a.completionHistory.push(h);
  for (const [d, s] of Object.entries(b.dailyProgress))
    a.dailyProgress[d] = Math.max(a.dailyProgress[d] || 0, s);
  a.totalSeconds = Math.max(
    a.totalSeconds,
    b.totalSeconds,
    Object.values(a.dailyProgress).reduce((n, s) => n + s, 0),
  );
  for (const [id, date] of Object.entries(b.completedDates)) {
    if (a.completedDates[id] && a.completedDates[id] !== date) {
      for (const savedDate of [a.completedDates[id], date]) {
        const h = {bookId: Number(id), sourceId: Number(id), date: savedDate};
        if (!a.completionHistory.some(x => JSON.stringify(x) === JSON.stringify(h))) a.completionHistory.push(h);
      }
    }
    if (!a.completedDates[id] || date > a.completedDates[id]) a.completedDates[id] = date;
  }
  for (const [id, date] of Object.entries(b.achievements))
    if (!a.achievements[id] || date < a.achievements[id])
      a.achievements[id] = date;
  for (const field of ["sessions", "challenges"])
    for (const item of b[field]) {
      const existing = a[field].find((x) => x.id === item.id);
      if (!existing) a[field].push(item);
      else if (
        field === "challenges" &&
        item.completed &&
        !existing.completed &&
        JSON.stringify({ ...existing, completed: null }) ===
          JSON.stringify({ ...item, completed: null })
      )
        existing.completed = item.completed;
    }
  for (const g of b.personalGoals) {
    const same = a.personalGoals.find((x) => x.text === g.text);
    if (same) same.completed ||= g.completed;
    else {
      let id = g.id;
      while (a.personalGoals.some((x) => x.id === id)) id++;
      a.personalGoals.push({ ...g, id });
    }
  }
  for (const f of ["read", "liked"])
    a.unresolved[f] = [...new Set([...a.unresolved[f], ...b.unresolved[f]])];
  a.unresolved.reviews = { ...b.unresolved.reviews, ...a.unresolved.reviews };
  return a;
}
