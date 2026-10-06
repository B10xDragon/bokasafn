// UI extensions use the existing catalog, storage, theme and accessible dialogs.
const featureButton = (text, action) =>
  `<button type="button" class="feature-button" onclick="${action}">${text}</button>`;
const field = (id, label, type = "number", extra = "") =>
  `<label class="feature-field">${label}<input id="${id}" type="${type}" ${extra}></label>`;
let pendingImport = null;
let routeChange = false;
function featureDialog(title, html) {
  if (activeDialog)
    closeModal(
      activeDialog.modal.id,
      DIALOG_CONTENT_IDS[activeDialog.modal.id],
    );
  document.getElementById("feature-dialog-title").textContent = title;
  document.getElementById("feature-dialog-body").innerHTML = html;
  openModal("feature-modal", "feature-modal-content");
}
function filtersValue(prefix = "filter") {
  return {
    state: document.getElementById(prefix + "-state")?.value || "",
    min: Number(document.getElementById(prefix + "-min")?.value) || 0,
    max: Number(document.getElementById(prefix + "-max")?.value) || 0,
    rating: Number(document.getElementById(prefix + "-rating")?.value) || 0,
    author: document.getElementById(prefix + "-author")?.value || "",
    category: document.getElementById(prefix + "-category")?.value || "",
  };
}
function filterFields(prefix, random = false) {
  const categories = [...new Set(allBooks.flatMap((b) => b.categories))].sort(
    (a, b) => a.localeCompare(b, "is"),
  );
  const authors = [...new Set(allBooks.map((b) => b.author))].sort((a, b) =>
    a.localeCompare(b, "is"),
  );
  return `<div class="feature-fields"><label class="feature-field">Lestrarstaða<select id="${prefix}-state" ${random ? "" : 'onchange="applyFilters()"'}><option value="">Allar bækur</option><option value="unread" ${random ? "selected" : ""}>Ólesið</option><option value="read">Lesið</option><option value="wishlist">Óskalisti</option></select></label>
    ${field(prefix + "-min", "Minnst blaðsíður", "number", 'min="0" ' + (random ? "" : 'oninput="applyFilters()"'))}${field(prefix + "-max", "Mest blaðsíður", "number", 'min="0" ' + (random ? "" : 'oninput="applyFilters()"'))}
    <label class="feature-field">Flokkur<select id="${prefix}-category" ${random ? "" : 'onchange="applyFilters()"'}><option value="">Allir flokkar</option>${categories.map((c) => `<option>${escapeHTML(c)}</option>`).join("")}</select></label>
    ${random ? "" : `<label class="feature-field">Lágmarksstjörnur<select id="filter-rating" onchange="applyFilters()"><option value="">Allar einkunnir</option>${[1, 2, 3, 4, 5].map((n) => `<option value="${n}">${n} stjörnur</option>`).join("")}</select></label><label class="feature-field">Höfundur<select id="filter-author" onchange="applyFilters()"><option value="">Allir höfundar</option>${authors.map((a) => `<option>${escapeHTML(a)}</option>`).join("")}</select></label>`}</div>`;
}
function resetAdvancedFilters() {
  document
    .querySelectorAll("#advanced-filters input, #advanced-filters select")
    .forEach((n) => (n.value = ""));
  applyFilters();
}
function openRandomPicker() {
  featureDialog(
    "Hvað á ég að lesa?",
    `<p>Veldu það sem hentar þér og leyfðu tilviljuninni að ráða.</p>${filterFields("random", true)}${featureButton("Velja bók", "pickRandomBook()")}<div id="random-result" role="status" aria-live="polite"></div>`,
  );
}
function pickRandomBook() {
  const b = chooseRandom(
    allBooks.filter((b) => matchesAdvanced(b, filtersValue("random"))),
  );
  document.getElementById("random-result").innerHTML = b
    ? `<div class="feature-result"><p>Næsta ævintýri þitt</p><h3>${escapeHTML(b.title)}</h3><p>${escapeHTML(b.author)} · ${b.pages || "?"} bls.</p>${featureButton("Skoða bókina", `openBookInfo(${b.id})`)}</div>`
    : "<p>Engin bók passar. Prófaðu að víkka leitina.</p>";
}
function exportReadingData() {
  checkpointTimer();
  const { interval, ...session } = timerState;
  const backup = {
    format: "bokasafn-backup",
    backupVersion: 1,
    exportedAt: new Date().toISOString(),
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    data: { ...userData, session: timerState.active ? session : null },
    preferences: { theme: bokasafnThemePreference },
    legacy: null,
    storedData: null,
    recovery: {},
  };
  try {
    backup.storedData = localStorage.getItem(LIBRARY_STORAGE_KEY);
    backup.legacy = localStorage.getItem("library_v14");
    for (let i = 0; i < localStorage.length; i++) {
      const k = localStorage.key(i);
      if (
        k.startsWith("library_v15_recovery") ||
        k.startsWith("library_import_backup")
      )
        backup.recovery[k] = localStorage.getItem(k);
    }
  } catch (error) {
    showToast("Ekki tókst að lesa öll eldri afrit.", "error");
  }
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(backup, null, 2)], { type: "application/json" }),
  );
  const a = document.createElement("a");
  a.href = url;
  a.download = "bokasafn-" + getLocalYYYYMMDD(new Date()) + ".json";
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
async function previewImport(input) {
  const file = input.files?.[0];
  if (!file) return;
  try {
    if (file.size > 5000000) throw Error("Afritið er of stórt (hámark 5 MB).");
    pendingImport = parseBackup(await file.text());
    const d = pendingImport.data;
    featureDialog(
      "Flytja inn afrit",
      `<p>${d.read.length} lesnar bækur · ${d.liked.length} á óskalista · ${Math.floor(d.totalSeconds / 60)} mínútur</p>
        <p><strong>Sameina:</strong> núverandi umsagnir, markmið og útlit hafa forgang. Sami dagur notar meiri lestímann, ekki summu, til að forðast tvítalningu. Óháður lestur sama dags gæti því þurft handvirka yfirferð.</p>
        <p><strong>Skipta út:</strong> öll núverandi lestrargögn og útlit víkja fyrir afritinu. Afrit af núverandi gögnum verður varðveitt í vafranum.</p>
        <p>Virk lestrarlota verður ekki flutt inn. Ljúktu núverandi lotu áður en þú flytur inn.</p>
        <div class="feature-actions">${featureButton("Sameina örugglega", "applyImport('merge')")}${featureButton("Skipta út gögnum", "confirmImportReplace()")}${featureButton("Hætta við", "closeModal('feature-modal','feature-modal-content')")}</div>`,
    );
  } catch (error) {
    pendingImport = null;
    showToast("Ekki hægt að flytja inn: " + error.message, "error");
  }
  input.value = "";
}
function confirmImportReplace() {
  document.getElementById("feature-dialog-body").innerHTML =
    `<p>Viltu örugglega skipta út núverandi gögnum? Vistaðu útflutningsafrit fyrst ef þú vilt halda því á öðrum stað.</p>${featureButton("Já, skipta út", "applyImport('replace')")}${featureButton("Hætta við", "closeModal('feature-modal','feature-modal-content')")}`;
  focusDialog(document.getElementById("feature-modal-content"));
}
function applyImport(mode) {
  if (!pendingImport || !storageWritable)
    return showToast("Ekki hægt að flytja inn í þessa geymslu.", "error");
  if (timerState.active)
    return showToast("Vistaðu virku lestrarlotuna fyrst.", "error");
  const next =
    mode === "merge"
      ? mergeReadingData(userData, pendingImport.data)
      : normalizeUserData(pendingImport.data);
  next.session = null;
  const before = userData;
  try {
    const key = "library_import_backup_" + newDataId();
    localStorage.setItem(
      key,
      JSON.stringify({
        format: "bokasafn-backup",
        backupVersion: 1,
        data: before,
        preferences: { theme: bokasafnThemePreference },
        legacy: localStorage.getItem("library_v14"),
      }),
    );
    // Preserve auxiliary historic/recovery data before the atomic data write.
    localStorage.setItem(key + "_source", JSON.stringify(pendingImport.raw));
    userData = next;
    if (!saveUserData()) {
      userData = before;
      return;
    }
    if (mode === "replace" && pendingImport.theme)
      setBokasafnTheme(pendingImport.theme);
    pendingImport = null;
    syncGoalUI();
    applyFilters();
    updateStatsUI();
    closeModal("feature-modal", "feature-modal-content");
    showToast("Afrit flutt inn.");
  } catch (error) {
    userData = before;
    showToast("Innflutningur mistókst. Athugaðu vafrageymsluna.", "error");
  }
}
function addChallenge(kind, target, title, monthly = false) {
  const now = new Date(),
    start = getLocalYYYYMMDD(
      monthly ? new Date(now.getFullYear(), now.getMonth(), 1) : now,
    ),
    end = monthly
      ? getLocalYYYYMMDD(new Date(now.getFullYear(), now.getMonth() + 1, 0))
      : null;
  userData.challenges.push({
    id: newDataId(),
    title,
    kind,
    target,
    start,
    end,
    baseline: monthly
      ? userData.read.filter(
          (id) =>
            !userData.completedDates[id] || userData.completedDates[id] < start,
        )
      : [...userData.read],
    baselineSeconds: userData.dailyProgress[start] || 0,
    completed: null,
  });
  saveUserData();
  renderInsights();
}
function addBuiltInChallenge(kind) {
  const d = BUILTIN_CHALLENGES[kind];
  if (!d) return;
  if (existingBuiltInChallenge(kind)) {
    showToast("Þú ert þegar með þessa áskorun.");
    return;
  }
  addChallenge(...d);
}
function createPersonalChallenge() {
  const title = document.getElementById("challenge-title").value.trim(),
    kind = document.getElementById("challenge-kind").value,
    target = Number(document.getElementById("challenge-target").value);
  if (!title || !Number.isSafeInteger(target) || target < 1 || target > 1000000)
    return showToast("Skrifaðu heiti og gilt markmið (1–1.000.000).", "error");
  addChallenge(kind, target, title);
  document.getElementById("challenge-title").value = "";
}
function removeChallenge(id) {
  const group = challengeDisplayGroups(userData.challenges).find((g) =>
    g.ids.includes(id),
  );
  const ids = new Set(group ? group.ids : [id]);
  userData.challenges = userData.challenges.filter((c) => !ids.has(c.id));
  saveUserData();
  renderInsights();
}
function renderInsights() {
  if (!userData.achievements || !document.getElementById("reading-insights"))
    return;
  const m = readingMetrics(),
    today = getLocalYYYYMMDD(new Date());
  const metric = (title, value) =>
    `<div class="feature-metric"><span>${title}</span><strong>${value}</strong></div>`;
  document.getElementById("extended-metrics").innerHTML =
    metric("Lokið við bækur", m.books) +
    metric("Blaðsíður í loknum bókum", m.pages) +
    metric("Lestrartími", Math.floor(m.seconds / 60) + " mín.") +
    metric("Meðaleinkunn", m.averageRating?.toFixed(1) || "—") +
    metric(
      "Meðallengd vistaðrar lotu",
      m.averageSession == null
        ? "—"
        : (m.averageSession / 60).toFixed(1) + " mín.",
    ) +
    metric("Núverandi markmiðaruna", m.current) +
    metric("Lengsta markmiðaruna", m.longest) +
    metric("Virkir lestrardagar", m.active) +
    metric("Met á einum degi", Math.floor(m.recordSeconds / 60) + " mín.") +
    metric(
      "Lengsta vistaða lota",
      Math.floor(
        userData.sessions.reduce((max, s) => Math.max(max, s.seconds), 0) / 60,
      ) + " mín.",
    );
  const heat = document.getElementById("activity-heatmap"),
    date = new Date();
  date.setHours(12, 0, 0, 0);
  date.setDate(date.getDate() - 364);
  date.setDate(date.getDate() - ((date.getDay() + 6) % 7));
  const cells = [];
  for (; getLocalYYYYMMDD(date) <= today; date.setDate(date.getDate() + 1)) {
    const d = getLocalYYYYMMDD(date),
      minutes = (userData.dailyProgress[d] || 0) / 60,
      level =
        minutes <= 0
          ? 0
          : minutes < 10
            ? 1
            : minutes < 30
              ? 2
              : minutes < 60
                ? 3
                : 4;
    cells.push(
      `<button type="button" class="heat-cell level-${level}" data-date="${d}" tabindex="${d === today ? 0 : -1}" aria-label="${d}: ${minutes.toFixed(1)} mínútur" title="${d}: ${minutes.toFixed(1)} mínútur" onclick="showActivityDay(this.dataset.date)"></button>`,
    );
  }
  heat.innerHTML = cells.join("");
  heat.onkeydown = (event) => {
    const delta = { ArrowLeft: -7, ArrowRight: 7, ArrowUp: -1, ArrowDown: 1 }[
      event.key
    ];
    if (delta === undefined) return;
    event.preventDefault();
    const nodes = [...heat.children],
      index = nodes.indexOf(document.activeElement),
      next = nodes[Math.max(0, Math.min(nodes.length - 1, index + delta))];
    if (next) {
      nodes.forEach((n) => (n.tabIndex = -1));
      next.tabIndex = 0;
      next.focus();
      showActivityDay(next.dataset.date);
    }
  };
  document.getElementById("achievement-list").innerHTML = ACHIEVEMENTS.map(
    ([id, title, field, target]) => {
      const unlocked = userData.achievements[id];
      return `<article class="feature-achievement ${unlocked ? "unlocked" : ""}"><h3>${unlocked ? "✓" : "○"} ${title}</h3><p>${unlocked ? "Opnað " + unlocked : Math.min(m[field], target) + " / " + target}</p><progress aria-label="${title}" value="${unlocked ? target : Math.min(m[field], target)}" max="${target}"></progress></article>`;
    },
  ).join("");
  document.getElementById("challenge-list").innerHTML =
    challengeDisplayGroups(userData.challenges)
      .map(
        ({ challenge: c }) =>
          `<article class="feature-achievement"><h3>${escapeHTML(c.title)}</h3><p>${c.completed ? "Lokið " + c.completed : c.end && c.end < today ? "Tímabili lokið" : "Í gangi"} · ${Math.min(challengeProgress(c), c.target)} / ${c.target}</p><p>Frá ${c.start}${c.end ? " til " + c.end : ""}</p><progress aria-label="${escapeHTML(c.title)}" max="${c.target}" value="${Math.min(challengeProgress(c), c.target)}"></progress><button type="button" class="feature-button secondary" data-id="${escapeHTML(c.id)}" onclick="removeChallenge(this.dataset.id)" aria-label="Eyða áskorun: ${escapeHTML(c.title)}">Eyða</button></article>`,
      )
      .join("") ||
    "<p>Veldu áskorun til að byrja. Aðeins lestur eftir upphaf áskorunar telst með.</p>";
  document.getElementById("personal-recommendations").innerHTML =
    recommendations()
      .map(
        ({ book: b, reason }) =>
          `<button type="button" class="feature-recommendation" onclick="openBookInfo(${b.id})"><strong>${escapeHTML(b.title)}</strong><span>${escapeHTML(b.author)}</span><small>${reason}</small></button>`,
      )
      .join("") || "<p>Þú hefur lokið við allar bækur safnsins.</p>";
  const monthly = {},
    weekly = {};
  for (const [d, s] of Object.entries(userData.dailyProgress)) {
    if (d > today) continue;
    monthly[d.slice(0, 7)] = (monthly[d.slice(0, 7)] || 0) + s;
    const monday = new Date(d + "T12:00:00");
    monday.setDate(monday.getDate() - ((monday.getDay() + 6) % 7));
    const w = getLocalYYYYMMDD(monday);
    weekly[w] = (weekly[w] || 0) + s;
  }
  function bars(data) {
    const entries = Object.entries(data)
        .sort(([a], [b]) => a.localeCompare(b))
        .slice(-12),
      max = Math.max(1, ...entries.map(([, s]) => s));
    return (
      entries
        .map(
          ([d, s]) =>
            `<div class="feature-bar"><span>${d}</span><div><i style="width:${(s / max) * 100}%"></i></div><span>${(s / 60).toFixed(1)} mín.</span></div>`,
        )
        .join("") || "<p>Enginn vistaður lestími enn.</p>"
    );
  }
  document.getElementById("weekly-chart").innerHTML = bars(weekly);
  document.getElementById("monthly-chart").innerHTML = bars(monthly);
}
function showActivityDay(date) {
  document.getElementById("heatmap-detail").textContent =
    date +
    ": " +
    ((userData.dailyProgress[date] || 0) / 60).toFixed(1) +
    " mínútur";
}
function copyBookLink(id) {
  const url = new URL(location.href);
  url.searchParams.set("book", id);
  if (navigator.clipboard?.writeText)
    navigator.clipboard
      .writeText(url.href)
      .then(() => showToast("Bókatengill afritaður."))
      .catch(() =>
        featureDialog(
          "Bókatengill",
          field(
            "share-url",
            "Afritaðu tengil",
            "text",
            `readonly value="${escapeHTML(url.href)}"`,
          ),
        ),
      );
  else
    featureDialog(
      "Bókatengill",
      field(
        "share-url",
        "Afritaðu tengil",
        "text",
        `readonly value="${escapeHTML(url.href)}"`,
      ),
    );
}
function applyBookRoute() {
  const value = new URL(location.href).searchParams.get("book");
  routeChange = true;
  if (
    value !== null &&
    /^\d+$/.test(value) &&
    allBooks.some((b) => b.id === Number(value))
  )
    openBookInfo(Number(value));
  else {
    if (activeDialog?.modal.id === "desc-modal")
      closeModal("desc-modal", "desc-modal-content");
    if (value !== null) showToast("Bókin fannst ekki.", "error");
  }
  routeChange = false;
}
function installFeatures() {
  if (!appReady) {
    setTimeout(installFeatures, 50);
    return;
  }
  const library = document.getElementById("library-page");
  const block = document.createElement("section");
  block.className = "feature-panel";
  block.innerHTML = `<div class="feature-heading"><h2>Mælt með fyrir þig</h2>${featureButton("Hvað á ég að lesa?", "openRandomPicker()")}</div><p class="feature-note">Tillögur byggja á þínum einkunnum, höfundum, flokkum og óskalista. Bækur með 1–2 stjörnur eru útilokaðar.</p><div id="personal-recommendations" class="feature-grid"></div>`;
  library.insertBefore(block, document.getElementById("book-grid"));
  const filters = document.createElement("details");
  filters.id = "advanced-filters";
  filters.className = "feature-panel";
  filters.innerHTML = `<summary>Ítarlegar síur</summary>${filterFields("filter")}${featureButton("Hreinsa ítarlegar síur", "resetAdvancedFilters()")}`;
  block.before(filters);
  const stats = document.createElement("section");
  stats.id = "reading-insights";
  stats.className = "feature-panel";
  stats.innerHTML = `<h2>Lestrarferðin þín</h2><div id="extended-metrics" class="feature-grid"></div><h3>Lestrarvirkni síðustu tólf mánaða</h3><p class="feature-note">Dekkri reitur merkir fleiri lestrarmínútur. Dagsetningar miðast við staðartíma þegar lestur var vistaður.</p><div class="heat-scroll"><div id="activity-heatmap"></div></div><p class="feature-note">Enginn lestur · &lt;10 · 10–29 · 30–59 · 60+ mínútur</p><p id="heatmap-detail" role="status">Veldu dag til að sjá mínútur.</p><p class="feature-note">Markmiðarunur nota valið markmið: daglega, síðustu sjö daga eða mánuðinn til dagsins í dag. Breytt markmið endurreiknar sögulegar runur. Án markmiðs gilda 10 mínútur daglega.</p><h3>Lestrartími eftir viku (frá mánudegi)</h3><div id="weekly-chart"></div><h3>Lestrartími eftir mánuði</h3><div id="monthly-chart"></div><p class="feature-note">Meðallengd og lengsta lota nota aðeins lotur vistaðar eftir þessa uppfærslu; eldri heildartími varðveitist.</p><h3>Afrek</h3><div id="achievement-list" class="feature-grid"></div><h3>Lestraráskoranir</h3><div class="feature-actions">${featureButton("3 bækur í þessum mánuði", "addBuiltInChallenge('month')")}${featureButton("500 blaðsíður", "addBuiltInChallenge('pages')")}${featureButton("Fantasíubók", "addBuiltInChallenge('fantasy')")}${featureButton("Nýr höfundur", "addBuiltInChallenge('author')")}</div><div id="challenge-list" class="feature-grid"></div><details><summary>Búa til eigin áskorun</summary><div class="feature-fields">${field("challenge-title", "Heiti", "text", 'maxlength="500"')}<label class="feature-field">Mælikvarði<select id="challenge-kind"><option value="books">Bækur</option><option value="pages">Blaðsíður í loknum bókum</option><option value="minutes">Lestrarmínútur</option></select></label>${field("challenge-target", "Markmið", "number", 'min="1" max="1000000" value="3"')}</div>${featureButton("Bæta við áskorun", "createPersonalChallenge()")}</details><h3>Afrit og flutningur gagna</h3><p>Gögnin þín eru geymd í þessum vafra. Vistaðu afrit til að flytja þau á annað tæki.</p><div class="feature-actions">${featureButton("Sækja JSON-afrit", "exportReadingData()")}<label class="feature-button">Flytja inn JSON-afrit<input id="backup-file" type="file" accept="application/json,.json" onchange="previewImport(this)"></label></div>`;
  document.querySelector("#stats-page > div").appendChild(stats);
  const modal = document.createElement("div");
  modal.id = "feature-modal";
  modal.setAttribute("aria-hidden", "true");
  modal.className =
    "fixed inset-0 z-[120] flex items-center justify-center bg-slate-900/40 backdrop-blur-sm p-4 hidden opacity-0 pointer-events-none transition-all duration-300";
  modal.onclick = (e) => {
    if (e.target === modal)
      closeModal("feature-modal", "feature-modal-content");
  };
  modal.innerHTML = `<div id="feature-modal-content" class="feature-panel feature-dialog scale-95 translate-y-4 transition-all duration-300" role="dialog" aria-modal="true" aria-labelledby="feature-dialog-title" tabindex="-1"><div class="feature-heading"><h2 id="feature-dialog-title"></h2>${featureButton("Loka", "closeModal('feature-modal','feature-modal-content')")}</div><div id="feature-dialog-body"></div></div>`;
  document.body.appendChild(modal);
  DIALOG_CONTENT_IDS["feature-modal"] = "feature-modal-content";
  const originalFilter = window.applyFilters;
  window.applyFilters = function () {
    if (!allBooks.length) return;
    originalFilter();
    filteredBooks = filteredBooks.filter((b) =>
      matchesAdvanced(b, filtersValue()),
    );
    const mode = document.getElementById("book-sort")?.value;
    if (mode === "rating-desc")
      filteredBooks.sort(
        (a, b) =>
          (userData.reviews[b.id]?.rating || 0) -
            (userData.reviews[a.id]?.rating || 0) || a.id - b.id,
      );
    if (mode === "recent-read")
      filteredBooks.sort(
        (a, b) =>
          (userData.completedDates[b.id] || "").localeCompare(
            userData.completedDates[a.id] || "",
          ) || a.id - b.id,
      );
    renderBooks();
  };
  document
    .getElementById("book-sort")
    .insertAdjacentHTML(
      "beforeend",
      '<option value="rating-desc">Hæsta einkunn</option><option value="recent-read">Nýlega lesið</option>',
    );
  const originalStats = window.updateStatsUI;
  window.updateStatsUI = function () {
    originalStats();
    renderInsights();
  };
  const originalOpen = window.openBookInfo;
  window.openBookInfo = function (id, event) {
    if (!allBooks.some((b) => b.id === id)) return;
    if (activeDialog && activeDialog.modal.id !== "desc-modal")
      closeModal(
        activeDialog.modal.id,
        DIALOG_CONTENT_IDS[activeDialog.modal.id],
      );
    originalOpen(id, event);
    const content = document.getElementById("modal-inner-content");
    content.insertAdjacentHTML(
      "beforeend",
      featureButton("Afrita bókatengil", `copyBookLink(${id})`),
    );
    if (
      !routeChange &&
      new URL(location.href).searchParams.get("book") !== String(id)
    ) {
      const url = new URL(location.href);
      url.searchParams.set("book", id);
      history.pushState({ bokasafnBook: true }, "", url);
    }
  };
  const originalClose = window.closeModal;
  window.closeModal = function (modalId, contentId) {
    originalClose(modalId, contentId);
    if (
      modalId === "desc-modal" &&
      !routeChange &&
      new URL(location.href).searchParams.has("book")
    ) {
      const url = new URL(location.href);
      url.searchParams.delete("book");
      history.pushState(null, "", url);
    }
  };
  window.addEventListener("popstate", () => {
    applyBookRoute();
  });
  refreshMilestones();
  saveUserData();
  renderInsights();
  applyFilters();
  applyBookRoute();
  window.featuresReady = true;
}
document.addEventListener("DOMContentLoaded", installFeatures);
