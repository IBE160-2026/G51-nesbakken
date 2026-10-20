// Renders the real catalogue on a map, and drives the four-screen Trip Setup
// flow (starting point -> available time -> topic -> confirm) as client-side
// screen states layered over the map. Migrated from Leaflet to MapLibre GL JS
// (2026-10-07, architecture decision AD-1) - see ARCHITECTURE-SPINE.md. Base
// style is OpenFreeMap's "positron" (closest free out-of-the-box match to
// DESIGN.md's muted cream palette); a fully custom DESIGN.md-matched style is
// later, separate work, not part of this migration.
//
// Trip Setup (Story 1.1, architecture AD-2): captured values live in a
// localStorage-persisted "active trip" object, nothing is sent to the
// backend yet (no planning endpoint exists until Story 1.4).

const NEWTOWN_CENTER = [151.1793, -33.8977]; // MapLibre uses [lng, lat]
const MAP_STYLE = "https://tiles.openfreemap.org/styles/positron";
const POPUP_OPTIONS = { maxWidth: "260px" };
const START_MARKER_COLOR = "#e63946";

const statusEl = document.getElementById("status");
const instructionsEl = document.getElementById("instructions");
const mapStageEl = document.getElementById("map-stage");

const map = new maplibregl.Map({
  container: "map",
  style: MAP_STYLE,
  center: NEWTOWN_CENTER,
  zoom: 15,
  // Also disables drag-to-pitch - MapLibre ties pitch to the same
  // right-click/two-finger-drag gesture as rotation.
  dragRotate: false,
});
// NavigationControl({showCompass:false}) above only hides the compass
// *button* - the touch two-finger-rotate gesture is a separate handler
// and stays live unless disabled explicitly here too.
map.touchZoomRotate.disableRotation();
map.keyboard.disable();

// Bottom-right is the standard thumb-reachable placement for one-handed
// phone use - MapLibre's default (top-left) assumes a desktop mouse.
// Compass/pitch are switched off above: Jaunt's map stays flat and
// north-up, matching DESIGN.md's flat "Quiet Streets" treatment rather
// than a tiltable 3D view.
map.addControl(
  new maplibregl.NavigationControl({ showCompass: false }),
  "bottom-right"
);

map.on("error", (event) => {
  statusEl.textContent = "Map failed to load. Please try again.";
  console.error("MapLibre error:", event?.error || event);
});

instructionsEl.textContent = "Tap the map to choose your starting point";

// A small round div (not MapLibre's default pin) to match the original
// circle-marker look, and so it's visually distinct in both shape and
// colour from the default pin markers used for catalogue stops below.
function buildStartMarkerElement() {
  const el = document.createElement("div");
  el.style.width = "20px";
  el.style.height = "20px";
  el.style.borderRadius = "50%";
  el.style.background = START_MARKER_COLOR;
  el.style.opacity = "0.9";
  el.style.border = `2px solid ${START_MARKER_COLOR}`;
  el.style.boxSizing = "border-box";
  return el;
}

let startMarker = null;

function placeStartMarker(lat, lng) {
  if (startMarker) {
    startMarker.setLngLat([lng, lat]);
  } else {
    startMarker = new maplibregl.Marker({ element: buildStartMarkerElement() })
      .setLngLat([lng, lat])
      .setPopup(new maplibregl.Popup(POPUP_OPTIONS).setText("Start point"))
      .addTo(map);
  }
}

// Builds popup content via DOM APIs rather than interpolating catalogue
// strings into an HTML string, so a place name or topic can never be
// interpreted as markup.
function buildPopupContent(place) {
  const container = document.createElement("div");

  const name = document.createElement("strong");
  name.textContent = place.name || "Unnamed place";
  container.appendChild(name);

  const topics = document.createElement("div");
  topics.textContent = (place.topics || []).join(", ");
  container.appendChild(topics);

  const source = document.createElement("em");
  source.textContent = place.source_type
    ? `Source: ${place.source_type}`
    : "Source: unknown";
  container.appendChild(source);

  return container;
}

async function loadPlaces() {
  statusEl.textContent = "Loading places…";

  let places;
  try {
    const response = await fetch("/api/places");
    if (!response.ok) {
      throw new Error(`request failed with status ${response.status}`);
    }
    places = await response.json();
  } catch (err) {
    statusEl.textContent = "Couldn't load places. Please try again.";
    return;
  }

  if (places.length === 0) {
    statusEl.textContent = "No places found for this area yet.";
  } else {
    statusEl.textContent = "";
  }

  places.forEach((place) => {
    const popup = new maplibregl.Popup(POPUP_OPTIONS).setDOMContent(
      buildPopupContent(place)
    );
    new maplibregl.Marker()
      .setLngLat([place.longitude, place.latitude])
      .setPopup(popup)
      .addTo(map);
  });
}

map.on("load", loadPlaces);

// =====================================================================
// TRIP SETUP - active-trip persistence (architecture AD-2)
// =====================================================================

const STORAGE_KEY = "jaunt_active_trip";
const SCHEMA_VERSION = 1;
const SETUP_STEPS = [
  "starting_point",
  "available_time",
  "topic_at_rest",
  "choose_topic",
  "confirm_sheet",
];
const VALID_TOPICS = ["history", "architecture", "public_art", "surprise_me"];
const TOPIC_LABELS = { history: "History", architecture: "Architecture", public_art: "Public Art" };

// Real coordinates for 2 of the 3 named-start chips (catalogue/geocode cache);
// Camperdown Park has no catalogue entry, so its centroid is a looked-up
// real-world value, not a guess at precision-critical data.
const NAMED_STARTS = {
  newtown_station: { lat: -33.89778906, lng: 151.18001972, label: "Newtown Station" },
  king_st: { lat: -33.8982025, lng: 151.1783569, label: "King St" },
  camperdown_park: { lat: -33.8905, lng: 151.1795, label: "Camperdown Park" },
};

function defaultTrip() {
  return {
    schema_version: SCHEMA_VERSION,
    phase: "setting_up",
    setup_step: "starting_point",
    starting_point: null,
    available_minutes: 60,
    topic: null,
    preference: 0.5,
  };
}

// Basic shape validation beyond the schema_version check (architecture AD-2:
// "a payload that fails basic shape validation is treated as unusable and
// triggers a safe reset"). Keeps a partially-corrupted object from reaching
// the screen logic and crashing it.
function isValidTrip(candidate) {
  if (!candidate || typeof candidate !== "object") return false;
  if (candidate.schema_version !== SCHEMA_VERSION) return false;
  if (candidate.phase !== "setting_up") return false;
  if (!SETUP_STEPS.includes(candidate.setup_step)) return false;
  if (
    !Number.isInteger(candidate.available_minutes) ||
    candidate.available_minutes < 30 ||
    candidate.available_minutes > 120 ||
    candidate.available_minutes % 5 !== 0
  ) {
    return false;
  }
  if (
    !Number.isFinite(candidate.preference) ||
    candidate.preference < 0 ||
    candidate.preference > 1
  ) {
    return false;
  }
  if (candidate.topic !== null && !VALID_TOPICS.includes(candidate.topic)) {
    return false;
  }
  if (candidate.starting_point !== null) {
    const sp = candidate.starting_point;
    if (
      typeof sp !== "object" ||
      sp === null ||
      !Number.isFinite(sp.lat) ||
      !Number.isFinite(sp.lng) ||
      sp.lat < -90 ||
      sp.lat > 90 ||
      sp.lng < -180 ||
      sp.lng > 180 ||
      typeof sp.label !== "string"
    ) {
      return false;
    }
  }
  // Every step past the first one requires a starting point to already
  // be set; the confirm sheet additionally requires a candidate topic
  // (needed to know which screen it was opened over).
  if (candidate.setup_step !== "starting_point" && candidate.starting_point === null) {
    return false;
  }
  if (candidate.setup_step === "confirm_sheet" && candidate.topic === null) {
    return false;
  }
  return true;
}

function loadActiveTrip() {
  let raw;
  try {
    raw = localStorage.getItem(STORAGE_KEY);
  } catch (err) {
    // Reading can throw too (e.g. storage blocked entirely) - treat the
    // same as "nothing stored" rather than crashing.
    console.error("Could not read active trip from storage, starting fresh:", err);
    return defaultTrip();
  }
  if (!raw) return defaultTrip();

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (err) {
    console.error("Stored active trip is not valid JSON, starting fresh:", err);
    return defaultTrip();
  }

  if (!isValidTrip(parsed)) {
    console.error("Stored active trip failed schema/shape validation, starting fresh.");
    return defaultTrip();
  }
  return parsed;
}

// Only the write is guarded: a thrown setItem (private mode, quota) leaves
// the in-memory trip exactly as it was and simply skips persisting - it
// must never trigger a reset.
function saveActiveTrip(tripState) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(tripState));
  } catch (err) {
    console.error("Could not persist active trip; continuing in-memory only:", err);
  }
}

let trip = loadActiveTrip();

// =====================================================================
// TRIP SETUP - screen-state machine
// =====================================================================

const screenStartingPoint = document.getElementById("screen-starting-point");
const screenAvailableTime = document.getElementById("screen-available-time");
const screenTopicAtRest = document.getElementById("screen-topic-at-rest");
const screenChooseTopic = document.getElementById("screen-choose-topic");
const screenStub = document.getElementById("screen-stub");

const startingPointTitleEl = document.getElementById("starting-point-title");
const startChipEls = Array.from(document.querySelectorAll(".start-chip"));
const pendingPinRowEl = document.getElementById("pending-pin-row");
const confirmStartBtn = document.getElementById("confirm-start-btn");

const availableTimeBackBtn = document.getElementById("available-time-back-btn");
const availableTimeTitleEl = document.getElementById("available-time-title");
const recapAvailableTimeEl = document.getElementById("recap-available-time");
const timePickerListEl = document.getElementById("time-picker-list");
const continueBtn = document.getElementById("continue-btn");

const topicAtRestBackBtn = document.getElementById("topic-at-rest-back-btn");
const topicAtRestTitleEl = document.getElementById("topic-at-rest-title");
const recapTopicAtRestEl = document.getElementById("recap-topic-at-rest");
const chooseTopicBtn = document.getElementById("choose-topic-btn");
const wildJauntBtn = document.getElementById("wild-jaunt-btn");
const prefRangeRestEl = document.getElementById("preference-range-rest");

const chooseTopicBackBtn = document.getElementById("choose-topic-back-btn");
const chooseTopicTitleEl = document.getElementById("choose-topic-title");
const recapChooseTopicEl = document.getElementById("recap-choose-topic");
const topicPillEls = Array.from(document.querySelectorAll(".topic-pill"));
const prefRangeChooseEl = document.getElementById("preference-range-choose");
const startJauntBtn = document.getElementById("start-jaunt-btn");
const prefBalancedTagEls = Array.from(document.querySelectorAll(".pref-balanced-tag"));

const confirmSheetWrapEl = document.getElementById("confirm-sheet-wrap");
const confirmSheetEl = document.getElementById("confirm-sheet");
const confirmHeadingEl = document.getElementById("confirm-sheet-heading");
const confirmBtn = document.getElementById("confirm-btn");
const dismissLink = document.getElementById("dismiss-link");

const stubHeadingEl = document.getElementById("stub-heading");
const stubDetailEl = document.getElementById("stub-detail");

// Which screen's control led into a given step - used to send keyboard/
// screen-reader focus back to the exact control that triggered navigation
// when the user goes back or dismisses the confirm sheet.
const triggerElementByStep = {};
let confirmSheetHostEl = null;
let confirmSheetTriggerEl = null;

const PREV_STEP = {
  available_time: "starting_point",
  topic_at_rest: "available_time",
  choose_topic: "topic_at_rest",
};

// The "Balanced" tag shows only near the slider's default center - it
// comes and goes as the value moves away from the middle, rather than
// permanently floating above the handle.
const PREF_BALANCED_DEADZONE = 0.04;

function updatePrefBalancedTags() {
  const isBalanced = Math.abs(trip.preference - 0.5) <= PREF_BALANCED_DEADZONE;
  prefBalancedTagEls.forEach((el) => {
    el.hidden = !isBalanced;
  });
}

// =====================================================================
// TRIP SETUP - available-time wheel picker (a real vertical scroll-snap
// list, not a horizontal range input - matches the agreed interaction).
// The list is also a real role="slider" so arrow keys work with no
// pointer at all; aria-valuenow/valuetext track whichever row is
// centered, the same value a scroll/swipe or a row tap would land on.
// =====================================================================

const TIME_MIN = 30;
const TIME_MAX = 120;
const TIME_STEP = 5;
const TIME_ROW_HEIGHT = 44;
const TIME_VALUES = [];
for (let m = TIME_MIN; m <= TIME_MAX; m += TIME_STEP) TIME_VALUES.push(m);

const timePickerRowEls = [];

function buildTimePicker() {
  const topSpacer = document.createElement("div");
  topSpacer.className = "picker-spacer";
  timePickerListEl.appendChild(topSpacer);

  TIME_VALUES.forEach((minutes) => {
    const row = document.createElement("div");
    row.className = "picker-row";
    row.dataset.minutes = String(minutes);
    row.textContent = String(minutes);
    const unit = document.createElement("span");
    unit.className = "unit";
    unit.textContent = "min";
    row.appendChild(unit);
    row.addEventListener("click", () => selectTimeIndex(TIME_VALUES.indexOf(minutes), { smooth: true }));
    timePickerListEl.appendChild(row);
    timePickerRowEls.push(row);
  });

  const bottomSpacer = document.createElement("div");
  bottomSpacer.className = "picker-spacer";
  timePickerListEl.appendChild(bottomSpacer);
}

function syncTimePickerClasses(index) {
  timePickerRowEls.forEach((row, i) => {
    const distance = Math.abs(i - index);
    row.classList.toggle("selected", distance === 0);
    row.classList.toggle("near", distance === 1);
  });
}

function selectTimeIndex(index, { smooth = false } = {}) {
  const clamped = Math.max(0, Math.min(TIME_VALUES.length - 1, index));
  const minutes = TIME_VALUES[clamped];
  trip.available_minutes = minutes;
  saveActiveTrip(trip);
  syncTimePickerClasses(clamped);
  timePickerListEl.setAttribute("aria-valuenow", String(minutes));
  timePickerListEl.setAttribute("aria-valuetext", `${minutes} minutes`);
  timePickerListEl.scrollTo({ top: clamped * TIME_ROW_HEIGHT, behavior: smooth ? "smooth" : "instant" });
}

function currentTimeIndex() {
  return Math.max(0, Math.min(TIME_VALUES.length - 1, TIME_VALUES.indexOf(trip.available_minutes)));
}

// Swipe/drag ends up here too - debounced so it only commits once
// scrolling has actually settled, not on every intermediate frame.
let timeScrollDebounce = null;
timePickerListEl.addEventListener("scroll", () => {
  clearTimeout(timeScrollDebounce);
  timeScrollDebounce = setTimeout(() => {
    const index = Math.round(timePickerListEl.scrollTop / TIME_ROW_HEIGHT);
    selectTimeIndex(index);
  }, 120);
});

timePickerListEl.addEventListener("keydown", (event) => {
  if (event.key === "ArrowUp" || event.key === "ArrowLeft") {
    event.preventDefault();
    selectTimeIndex(currentTimeIndex() - 1, { smooth: true });
  } else if (event.key === "ArrowDown" || event.key === "ArrowRight") {
    event.preventDefault();
    selectTimeIndex(currentTimeIndex() + 1, { smooth: true });
  } else if (event.key === "Home") {
    event.preventDefault();
    selectTimeIndex(0, { smooth: true });
  } else if (event.key === "End") {
    event.preventDefault();
    selectTimeIndex(TIME_VALUES.length - 1, { smooth: true });
  }
});

buildTimePicker();

function buildRecap() {
  const label = trip.starting_point ? trip.starting_point.label : "";
  return `${label} · ${trip.available_minutes} min`;
}

function hideAllScreens() {
  screenStartingPoint.hidden = true;
  screenAvailableTime.hidden = true;
  screenTopicAtRest.hidden = true;
  screenChooseTopic.hidden = true;
  screenStub.hidden = true;
}

// Shows one of the 4 real setup screens (the confirm sheet is a separate
// overlay, handled by openConfirmSheet/closeConfirmSheet below), updates
// setup_step + persists it, pre-fills every control from the current trip
// state, and moves focus to the new screen unless the caller is about to
// move it somewhere more specific itself (e.g. a recorded back-navigation
// trigger).
function showStep(step, { focusDefault = true } = {}) {
  hideAllScreens();
  trip.setup_step = step;
  saveActiveTrip(trip);

  mapStageEl.hidden = step !== "starting_point";

  if (step === "starting_point") {
    screenStartingPoint.hidden = false;
    // Re-show the already-confirmed marker on return (e.g. via back nav) -
    // already confirmed, so no pending-pin confirm row for it.
    if (trip.starting_point) {
      placeStartMarker(trip.starting_point.lat, trip.starting_point.lng);
    }
    clearPendingPin();
    if (focusDefault) startingPointTitleEl.focus();
  } else if (step === "available_time") {
    screenAvailableTime.hidden = false;
    recapAvailableTimeEl.textContent = trip.starting_point ? trip.starting_point.label : "";
    selectTimeIndex(currentTimeIndex(), { smooth: false });
    if (focusDefault) availableTimeTitleEl.focus();
  } else if (step === "topic_at_rest") {
    screenTopicAtRest.hidden = false;
    recapTopicAtRestEl.textContent = buildRecap();
    prefRangeRestEl.value = String(Math.round(trip.preference * 100));
    updatePrefBalancedTags();
    if (focusDefault) topicAtRestTitleEl.focus();
  } else if (step === "choose_topic") {
    screenChooseTopic.hidden = false;
    recapChooseTopicEl.textContent = buildRecap();
    prefRangeChooseEl.value = String(Math.round(trip.preference * 100));
    updatePrefBalancedTags();
    refreshTopicPills();
    if (focusDefault) chooseTopicTitleEl.focus();
  }
}

function goBack(fromStep) {
  const prevStep = PREV_STEP[fromStep];
  const trigger = triggerElementByStep[fromStep];
  showStep(prevStep, { focusDefault: !trigger });
  if (trigger) trigger.focus();
}

function refreshTopicPills() {
  let anySelected = false;
  topicPillEls.forEach((btn) => {
    const isSelected = btn.dataset.topic === trip.topic;
    btn.classList.toggle("selected", isSelected);
    btn.setAttribute("aria-checked", String(isSelected));
    if (isSelected) anySelected = true;
  });

  if (anySelected) {
    const label = TOPIC_LABELS[trip.topic];
    startJauntBtn.disabled = false;
    startJauntBtn.textContent = `Start my ${label} Jaunt`;
    startJauntBtn.setAttribute("aria-label", `Start my ${label} Jaunt`);
  } else {
    startJauntBtn.disabled = true;
    startJauntBtn.textContent = "Start my Jaunt";
    startJauntBtn.setAttribute("aria-label", "Start my Jaunt - pick a topic first");
  }
}

// =====================================================================
// TRIP SETUP - confirmation bottom sheet
// =====================================================================

// "Wild Jaunt" already carries the word "Jaunt" (locked wording - never
// "Surprise me"), so it never gets a second "Jaunt" appended the way a real
// topic name does ("History" -> "History Jaunt").
function confirmSheetTopicLabel() {
  return trip.topic === "surprise_me" ? "Wild Jaunt" : TOPIC_LABELS[trip.topic];
}

function confirmSheetJauntPhrase() {
  const label = confirmSheetTopicLabel();
  return trip.topic === "surprise_me" ? label : `${label} Jaunt`;
}

function openConfirmSheet(topicValue, triggerEl, hostScreenEl) {
  trip.topic = topicValue;
  trip.setup_step = "confirm_sheet";
  saveActiveTrip(trip);

  confirmSheetHostEl = hostScreenEl;
  confirmSheetTriggerEl = triggerEl;
  if ("inert" in hostScreenEl) hostScreenEl.inert = true;

  const phrase = confirmSheetJauntPhrase();
  confirmHeadingEl.textContent = `Ready for your ${phrase}?`;
  confirmBtn.textContent = `Start my ${phrase}`;
  confirmBtn.setAttribute("aria-label", `Confirm and start my ${phrase}`);

  confirmSheetWrapEl.hidden = false;
  confirmSheetEl.focus();
}

function closeConfirmSheet({ restoreFocus = true } = {}) {
  confirmSheetWrapEl.hidden = true;
  if (confirmSheetHostEl && "inert" in confirmSheetHostEl) {
    confirmSheetHostEl.inert = false;
  }
  if (restoreFocus && confirmSheetTriggerEl) {
    confirmSheetTriggerEl.focus();
  }
  confirmSheetHostEl = null;
}

confirmBtn.addEventListener("click", () => {
  closeConfirmSheet({ restoreFocus: false });
  showStub();
});

dismissLink.addEventListener("click", () => {
  // The confirm sheet always opens from exactly one of two screens, fully
  // determined by which topic was chosen: Wild Jaunt (surprise_me) opens it
  // from topic-at-rest; any named topic opens it from Choose Topic.
  const originStep = trip.topic === "surprise_me" ? "topic_at_rest" : "choose_topic";
  const trigger = confirmSheetTriggerEl;
  closeConfirmSheet({ restoreFocus: false });
  showStep(originStep, { focusDefault: !trigger });
  if (trigger) trigger.focus();
});

// =====================================================================
// TRIP SETUP - stub completion screen (throwaway - Stories 1.4/1.5 replace
// this wholesale with the real loading/review screens)
// =====================================================================

function showStub() {
  hideAllScreens();
  mapStageEl.hidden = true;

  const label = confirmSheetTopicLabel();
  const lat = trip.starting_point.lat.toFixed(5);
  const lng = trip.starting_point.lng.toFixed(5);
  stubDetailEl.textContent =
    `Setup complete - ${label}, ${trip.available_minutes} min, ${lat}, ${lng}`;

  screenStub.hidden = false;
  stubHeadingEl.focus();
}

// =====================================================================
// TRIP SETUP - control wiring
// =====================================================================

// Starting point: a free-form map tap drops a movable pin that needs an
// explicit "Confirm this spot" tap before it becomes the trip's starting
// point - the user needs to see and check where they placed it first. The
// 3 named-start chips are already an unambiguous exact location, so they
// still set starting_point and advance immediately, with no confirm step.
let pendingPin = null;

function showPendingPin(lat, lng) {
  pendingPin = { lat, lng };
  placeStartMarker(lat, lng);
  pendingPinRowEl.hidden = false;
  instructionsEl.textContent = "Tap elsewhere to move the pin, or confirm below";
}

function clearPendingPin() {
  pendingPin = null;
  pendingPinRowEl.hidden = true;
}

map.on("click", (event) => {
  if (trip.setup_step !== "starting_point") return;
  const { lat, lng } = event.lngLat;
  showPendingPin(lat, lng);
});

confirmStartBtn.addEventListener("click", () => {
  if (!pendingPin) return;
  trip.starting_point = { lat: pendingPin.lat, lng: pendingPin.lng, label: "Dropped pin" };
  saveActiveTrip(trip);
  clearPendingPin();
  instructionsEl.textContent = "";
  showStep("available_time");
});

startChipEls.forEach((btn) => {
  btn.addEventListener("click", () => {
    const start = NAMED_STARTS[btn.dataset.startId];
    trip.starting_point = { lat: start.lat, lng: start.lng, label: start.label };
    saveActiveTrip(trip);
    placeStartMarker(start.lat, start.lng);
    clearPendingPin();
    triggerElementByStep.available_time = btn;
    showStep("available_time");
  });
});

availableTimeBackBtn.addEventListener("click", () => goBack("available_time"));

continueBtn.addEventListener("click", () => {
  triggerElementByStep.topic_at_rest = continueBtn;
  showStep("topic_at_rest");
});

topicAtRestBackBtn.addEventListener("click", () => goBack("topic_at_rest"));

chooseTopicBtn.addEventListener("click", () => {
  triggerElementByStep.choose_topic = chooseTopicBtn;
  showStep("choose_topic");
});

wildJauntBtn.addEventListener("click", () => {
  openConfirmSheet("surprise_me", wildJauntBtn, screenTopicAtRest);
});

[prefRangeRestEl, prefRangeChooseEl].forEach((input) => {
  input.addEventListener("input", () => {
    trip.preference = Number(input.value) / 100;
    saveActiveTrip(trip);
    prefRangeRestEl.value = input.value;
    prefRangeChooseEl.value = input.value;
    updatePrefBalancedTags();
  });
});

chooseTopicBackBtn.addEventListener("click", () => goBack("choose_topic"));

topicPillEls.forEach((btn) => {
  btn.addEventListener("click", () => {
    trip.topic = btn.dataset.topic;
    saveActiveTrip(trip);
    refreshTopicPills();
  });
});

startJauntBtn.addEventListener("click", () => {
  if (startJauntBtn.disabled || !trip.topic || trip.topic === "surprise_me") return;
  openConfirmSheet(trip.topic, startJauntBtn, screenChooseTopic);
});

// =====================================================================
// TRIP SETUP - initial boot: resume exactly the screen setup_step names
// =====================================================================

function initTripSetup() {
  if (trip.setup_step === "confirm_sheet") {
    const originStep = trip.topic === "surprise_me" ? "topic_at_rest" : "choose_topic";
    showStep(originStep, { focusDefault: false });
    const hostEl = originStep === "topic_at_rest" ? screenTopicAtRest : screenChooseTopic;
    openConfirmSheet(trip.topic, null, hostEl);
    return;
  }
  showStep(trip.setup_step, { focusDefault: false });
}

initTripSetup();
