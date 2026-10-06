// Both portable formats share one complete envelope and the existing validator.
let deleteConfirmationOpen = false;
let backupEditGeneration = 0;
function isUserStorageKey(key) {
  return typeof key === "string" && /^(library_|bokasafn[-_])/.test(key);
}
function userStorageSnapshot(storage) {
  const snapshot = Object.create(null);
  for (let i = 0; i < storage.length; i++) {
    const key = storage.key(i);
    if (isUserStorageKey(key)) snapshot[key] = storage.getItem(key);
  }
  return snapshot;
}
function createReadingBackup() {
  checkpointTimer();
  const { interval, ...session } = timerState;
  return {
    format: "bokasafn-backup",
    backupVersion: 2,
    exportedAt: new Date().toISOString(),
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    data: JSON.parse(
      JSON.stringify({
        ...userData,
        session: timerState.active ? session : null,
      }),
    ),
    preferences: { theme: bokasafnThemePreference },
    storage: {
      local: userStorageSnapshot(localStorage),
      session: userStorageSnapshot(sessionStorage),
    },
  };
}
function crc32(bytes) {
  let crc = 0xffffffff;
  for (const byte of bytes) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit++)
      crc = (crc >>> 1) ^ (crc & 1 ? 0xedb88320 : 0);
  }
  return ((crc ^ 0xffffffff) >>> 0).toString(16).padStart(8, "0");
}
function bytesToBase64URL(bytes) {
  const chunks = [];
  for (let i = 0; i < bytes.length; i += 32768)
    chunks.push(String.fromCharCode(...bytes.subarray(i, i + 32768)));
  return btoa(chunks.join(""))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}
function encodeBackupLine(backup) {
  const bytes = new TextEncoder().encode(JSON.stringify(backup));
  return `BOKASAFN:1:${bytes.length}:${crc32(bytes)}:${bytesToBase64URL(bytes)}`;
}
function decodeBackupLine(line) {
  if (typeof line !== "string" || !line)
    throw Error("Ógilt afrit: límdu alla afritslínuna.");
  if (/[\r\n\u2028\u2029]/.test(line))
    throw Error("Ógilt afrit: línan má ekki innihalda línuskipti.");
  const parts = line.split(":");
  if (parts[0] !== "BOKASAFN")
    throw Error("Ógilt afrit: merkið BOKASAFN vantar.");
  if (parts.length < 2)
    throw Error("Afritið er ófullkomið eða hefur verið stytt.");
  if (parts[1] !== "1") throw Error("Óstudd útgáfa af afritslínu.");
  if (parts.length !== 5 || !parts[4])
    throw Error("Afritið er ófullkomið eða hefur verið stytt.");
  const [, , length, checksum, payload] = parts;
  if (
    !/^(0|[1-9]\d*)$/.test(length) ||
    !Number.isSafeInteger(Number(length)) ||
    !/^[0-9a-f]{8}$/.test(checksum) ||
    !/^[A-Za-z0-9_-]+$/.test(payload) ||
    payload.length % 4 === 1
  )
    throw Error("Afritið er skemmt eða ófullkomið.");
  let bytes;
  try {
    const binary = atob(
      payload.replace(/-/g, "+").replace(/_/g, "/") +
        "=".repeat((4 - (payload.length % 4)) % 4),
    );
    bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0));
  } catch (error) {
    throw Error("Afritið er skemmt eða ófullkomið.");
  }
  if (bytes.length !== Number(length))
    throw Error("Afritið er ófullkomið: lengdin passar ekki.");
  if (crc32(bytes) !== checksum || bytesToBase64URL(bytes) !== payload)
    throw Error("Afritið er skemmt: prófsumman passar ekki.");
  try {
    return new TextDecoder("utf-8", { fatal: true }).decode(bytes);
  } catch (error) {
    throw Error("Afritið inniheldur ógilda textakóðun.");
  }
}
function parseBackupLine(line) {
  return parseBackup(decodeBackupLine(line));
}
function validateStorageSnapshot(value) {
  if (!isRecord(value) || !isRecord(value.local) || !isRecord(value.session))
    throw Error("Ógild vafragögn í afriti.");
  for (const source of [value.local, value.session])
    for (const [key, text] of Object.entries(source)) {
      if (!isUserStorageKey(key) || typeof text !== "string")
        throw Error("Ógild geymslufærsla í afriti.");
    }
  return value;
}
function restoreUserStorage(
  storage,
  snapshot,
  replace = false,
  keep = new Set(),
) {
  if (replace)
    for (const key of Object.keys(userStorageSnapshot(storage)))
      if (!keep.has(key)) storage.removeItem(key);
  for (const [key, value] of Object.entries(snapshot))
    if (!keep.has(key) && (replace || storage.getItem(key) === null))
      storage.setItem(key, value);
}
function rollbackUserStorage(storage, snapshot) {
  for (const key of Object.keys(userStorageSnapshot(storage)))
    if (!Object.hasOwn(snapshot, key)) storage.removeItem(key);
  for (const [key, value] of Object.entries(snapshot))
    if (storage.getItem(key) !== value) storage.setItem(key, value);
}
function clearAllUserStorage() {
  const originals = [
    { storage: localStorage, data: userStorageSnapshot(localStorage) },
    { storage: sessionStorage, data: userStorageSnapshot(sessionStorage) },
  ];
  try {
    for (const { storage, data } of originals)
      for (const key of Object.keys(data)) storage.removeItem(key);
  } catch (error) {
    for (const { storage, data } of originals)
      try {
        for (const [key, value] of Object.entries(data))
          storage.setItem(key, value);
      } catch (rollbackError) {
        console.warn(
          "Ekki tókst að endurheimta allar geymslufærslur.",
          rollbackError,
        );
      }
    throw Error(
      "Ekki tókst að eyða gögnunum. Athugaðu heimildir vafrageymslunnar.",
    );
  }
}
function openDeleteAllConfirmation() {
  featureDialog(
    "Eyða öllum gögnum?",
    `<p>Öllum lestrargögnum, umsögnum, einkunnum, markmiðum, afrekum, áskorunum, stillingum og endurheimtarafritum í þessum vafra verður eytt. Virk lestrarlota verður einnig fjarlægð.</p><p><strong>Þetta verður ekki afturkallað nema þú hafir vistað afrit utan vafrans.</strong> Bókaskráin og vefurinn verða áfram til staðar.</p><div class="feature-actions">${featureButton("Hætta við", "closeModal('feature-modal','feature-modal-content')")}<button type="button" class="feature-button destructive" onclick="confirmDeleteAllData()">Eyða öllum gögnum</button></div>`,
  );
  document.querySelector(
    "#feature-dialog-body button:not(.destructive)",
  ).dataset.dialogInitialFocus = "";
  deleteConfirmationOpen = true;
}
function confirmDeleteAllData() {
  if (!deleteConfirmationOpen || activeDialog?.modal.id !== "feature-modal")
    return;
  try {
    clearAllUserStorage();
  } catch (error) {
    showToast(
      "Ekki tókst að eyða gögnunum. Athugaðu heimildir vafrageymslunnar.",
      "error",
    );
    return;
  }
  clearInterval(timerState.interval);
  timerState = emptyTimerState();
  userData = normalizeUserData({});
  storageWritable = true;
  userDataLoaded = true;
  lastStorageWarning = 0;
  lastPersistedLibraryValue = null;
  pendingImport = null;
  deleteConfirmationOpen = false;
  backupEditGeneration++;
  currentRating = 0;
  searchQuery = "";
  activeCategories = [];
  document
    .querySelectorAll("#personal-goal-input,#rec-title,#rec-author,#rec-ideas")
    .forEach((node) => (node.value = ""));
  document.getElementById("book-search").value = "";
  document.getElementById("search-suggestions").innerHTML = "";
  document.getElementById("search-suggestions").classList.add("hidden");
  closeModal("feature-modal", "feature-modal-content");
  document.getElementById("feature-dialog-body").innerHTML = "";
  document.getElementById("modal-inner-content").innerHTML = "";
  document
    .querySelectorAll("#reading-insights input, #reading-insights textarea")
    .forEach((node) => (node.value = ""));
  document.getElementById("challenge-target").value = "3";
  document
    .querySelectorAll("#reading-insights details, #advanced-filters")
    .forEach((node) => (node.open = false));
  resetAdvancedFilters();
  document.getElementById("book-sort").value = "default";
  setBookSort("default");
  bokasafnThemePreference = "system";
  renderBokasafnTheme();
  syncGoalUI();
  updateTimerDisplay();
  updateTimerUI();
  updateCategoryButtonsUI();
  updateStatsUI();
  const url = new URL(location.href);
  url.searchParams.delete("book");
  history.replaceState(null, "", url);
  showPage("library");
  document.getElementById("book-search").focus();
  showToast("Öllum gögnum hefur verið eytt.");
}
function openTextBackup() {
  try {
    const line = encodeBackupLine(createReadingBackup());
    featureDialog(
      "Afrit í einni línu",
      `<p>Línan inniheldur einkagögn um lesturinn þinn. Geymdu hana á öruggum stað og deildu henni aðeins með þeim sem mega sjá gögnin.</p><label class="feature-field">Heildarafrit<textarea id="backup-line-output" readonly wrap="off" spellcheck="false" rows="4"></textarea></label><div class="feature-actions">${featureButton("Velja alla línuna", "selectBackupLine()")}${featureButton("Afrita línuna", "copyBackupLine()")}</div><p id="backup-line-copy-status" role="status" aria-live="polite"></p>`,
    );
    document.getElementById("backup-line-output").value = line;
  } catch (error) {
    showToast("Ekki tókst að búa til heilt afrit: " + error.message, "error");
  }
}
function selectBackupLine() {
  const field = document.getElementById("backup-line-output");
  field.focus();
  field.select();
}
async function copyBackupLine() {
  const generation = backupEditGeneration,
    line = document.getElementById("backup-line-output").value;
  try {
    if (navigator.clipboard?.writeText)
      await navigator.clipboard.writeText(line);
    else {
      selectBackupLine();
      if (!document.execCommand("copy")) throw Error("clipboard");
    }
    if (
      generation === backupEditGeneration &&
      document.getElementById("backup-line-copy-status")
    )
      document.getElementById("backup-line-copy-status").textContent =
        "Öll línan hefur verið afrituð.";
  } catch (error) {
    if (
      generation === backupEditGeneration &&
      document.getElementById("backup-line-output")
    ) {
      selectBackupLine();
      document.getElementById("backup-line-copy-status").textContent =
        "Sjálfvirk afritun tókst ekki. Afritaðu valda línu handvirkt.";
    }
  }
}
function openTextImport() {
  pendingImport = null;
  featureDialog(
    "Flytja inn afritslínu",
    `<p>Afritslínan getur innihaldið einkagögn. Límdu alla línuna hér; ekkert verður vistað fyrr en þú velur að sameina eða skipta út.</p><label class="feature-field">Afritslína<textarea id="backup-line-input" rows="5" wrap="off" spellcheck="false" oninput="invalidateBackupLine()"></textarea></label><p id="backup-line-status" role="status" aria-live="polite"></p><div class="feature-actions">${featureButton("Athuga afrit", "validateBackupLineInput()")}<button id="backup-line-import" type="button" class="feature-button" disabled onclick="previewTextImport()">Flytja inn</button></div>`,
  );
}
function invalidateBackupLine() {
  pendingImport = null;
  backupEditGeneration++;
  document.getElementById("backup-line-import").disabled = true;
  document.getElementById("backup-line-status").textContent =
    "Athugaðu afritið áður en þú flytur það inn.";
}
function validateBackupLineInput() {
  try {
    pendingImport = parseBackupLine(
      document.getElementById("backup-line-input").value,
    );
    document.getElementById("backup-line-status").textContent =
      "Afritið er gilt. Prófsumma og gögn standast athugun.";
    document.getElementById("backup-line-import").disabled = false;
    return true;
  } catch (error) {
    pendingImport = null;
    document.getElementById("backup-line-import").disabled = true;
    document.getElementById("backup-line-status").textContent = error.message;
    return false;
  }
}
function previewTextImport() {
  if (validateBackupLineInput()) showImportPreview();
}
function installBackupControls() {
  const section = document.createElement("div");
  section.className = "backup-controls";
  section.innerHTML = `<h3>Afrit í einni textalínu</h3><p class="feature-note">Afritið inniheldur sömu gögn og JSON-afritið, með lengdarathugun og prófsummu. Línan er ekki dulkóðuð og skal meðhöndla sem einkagögn.</p><div class="feature-actions">${featureButton("Búa til afritslínu", "openTextBackup()")}${featureButton("Líma afritslínu", "openTextImport()")}</div><h3>Eyða gögnum</h3><button type="button" class="feature-button destructive" onclick="openDeleteAllConfirmation()">Eyða öllum gögnum</button>`;
  document.getElementById("reading-insights").appendChild(section);
}

// Other open tabs stop their old timer before reloading the cleared library.
window.addEventListener("storage", (event) => {
  if (event.key === LIBRARY_STORAGE_KEY && event.newValue === null) {
    clearInterval(timerState.interval);
    timerState = emptyTimerState();
    userData = normalizeUserData({});
    userDataLoaded = false;
    if (window.featuresReady) pendingImport = null;
    location.reload();
  }
});
