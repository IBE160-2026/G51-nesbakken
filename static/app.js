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
// User feedback 2026-10-21: "positron" explicitly strips POI labels (no
// restaurants/shops shown at any zoom) - switched to "liberty", OpenFreeMap's
// actively-maintained default (the other OpenMapTiles-derived styles,
// including positron, are abandoned upstream), which keeps POIs and colored
// land-use/park areas. Verified live: no change needed to the existing
// pitch:0/dragRotate:false lock already in place below - the map stays flat.
const MAP_STYLE = "https://tiles.openfreemap.org/styles/liberty";
const POPUP_OPTIONS = { maxWidth: "260px" };

const statusEl = document.getElementById("status");
const instructionsEl = document.getElementById("instructions");
const mapStageEl = document.getElementById("map-stage");
const screenSplashEl = document.getElementById("screen-splash");

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

// User's explicit choice (2026-10-21): the starting-point marker is
// Jarrod's own head (the same crop DESIGN.md/FR-14 already define for the
// live-position marker during a walk), not a plain colored dot - and
// definitely not red, which was never anyone's choice, just a Sprint-2
// placeholder that stuck around.
function buildStartMarkerElement() {
  const el = document.createElement("div");
  el.className = "jaunty jaunty-head-marker";
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

// Codex review 2026-10-21 (commit d79975c): these markers were never kept
// anywhere, so they could never be hidden again - Route Review ended up
// showing every catalogue pin alongside its own numbered stop circles.
// User feedback the same day went further: the plain default-pin "blue
// dots" look messy on the starting-point screen too, now that the base
// style itself shows real POIs when zoomed in - so these are never shown
// at all any more (kept, not deleted, for Story 2.4's muted
// background-amenities layer, FR-23, which will want this same fetched
// data rendered a different, deliberately subtle way).
const catalogueMarkers = [];

function setCatalogueMarkersVisible(visible) {
  catalogueMarkers.forEach((marker) => {
    marker.getElement().style.display = visible ? "" : "none";
  });
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
    const marker = new maplibregl.Marker()
      .setLngLat([place.longitude, place.latitude])
      .setPopup(popup)
      .addTo(map);
    catalogueMarkers.push(marker);
  });
  setCatalogueMarkersVisible(false);
}

// =====================================================================
// ROUTE REVIEW (Story 1.5, architecture AD-1) - the route line and the
// numbered stop circles are data-driven GeoJSON sources + paint layers,
// never one DOM marker per stop (that per-marker pattern is AD-1's
// explicitly-named "known non-compliant scaffolding" in loadPlaces() above
// - not a pattern to extend).
// =====================================================================

const ROUTE_LINE_SOURCE_ID = "route-line";
const ROUTE_STOPS_SOURCE_ID = "route-stops";
let mapStyleLoaded = false;

function emptyFeatureCollection() {
  return { type: "FeatureCollection", features: [] };
}

// User feedback 2026-10-21: stop markers should be small icons showing what
// kind of place it is, not "only the green dots" - and the stop list is
// "a bit boring without any" too, so the same icon is reused there.
// Deliberately plain geometric shapes (bars, a house, a dot cluster), not
// an attempt at detailed/photographic icon art. Shape-only fragments, fill
// color passed in separately so the map version (cream-on-forest) and the
// list version (forest-on-muted) share one source of truth for the shape.
const TOPIC_ICON_SHAPES = {
  history:
    '<rect x="4" y="5" width="16" height="2.4"/>' +
    '<rect x="6" y="9" width="2.4" height="9"/>' +
    '<rect x="11" y="9" width="2.4" height="9"/>' +
    '<rect x="16" y="9" width="2.4" height="9"/>' +
    '<rect x="3" y="18.5" width="18" height="2.2"/>',
  architecture:
    '<polygon points="12,3 4,10 20,10"/>' +
    '<rect x="6.5" y="10" width="11" height="9.5"/>',
  public_art:
    '<circle cx="9" cy="9" r="4.5"/>' +
    '<circle cx="16" cy="9" r="4.5"/>' +
    '<circle cx="12.5" cy="16" r="4.5"/>',
};
const DEFAULT_TOPIC_ICON = "history";

function topicIconSvg(topic, fillColor) {
  const shapes = TOPIC_ICON_SHAPES[topic] || TOPIC_ICON_SHAPES[DEFAULT_TOPIC_ICON];
  return (
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="${fillColor}">` +
    shapes +
    "</svg>"
  );
}

// A stop can carry more than one real topic (e.g. a heritage building is
// often both history and architecture) - the first entry in its own
// topics array picks the icon, a simple, deterministic rule rather than a
// new priority system.
function pickTopic(topics) {
  const topic = Array.isArray(topics) ? topics.find((t) => TOPIC_ICON_SHAPES[t]) : null;
  return topic || DEFAULT_TOPIC_ICON;
}

function pickTopicIconName(topics) {
  return `topic-icon-${pickTopic(topics)}`;
}

// MapLibre's addImage() needs a decoded raster image, not an SVG string
// directly - converts each via an offscreen Image/canvas round-trip.
function loadTopicIcons() {
  const ICON_PX = 24;
  return Promise.all(
    Object.keys(TOPIC_ICON_SHAPES).map((topic) => {
      return new Promise((resolve) => {
        const img = new Image();
        img.onload = () => {
          const canvas = document.createElement("canvas");
          canvas.width = ICON_PX;
          canvas.height = ICON_PX;
          const ctx = canvas.getContext("2d");
          ctx.drawImage(img, 0, 0, ICON_PX, ICON_PX);
          // addImage() needs real decoded pixel data (ImageData), not the
          // canvas element itself - reproduced directly: passing the raw
          // canvas threw "mismatched image size. expected: 0 but got: ...".
          map.addImage(`topic-icon-${topic}`, ctx.getImageData(0, 0, ICON_PX, ICON_PX));
          resolve();
        };
        img.onerror = () => {
          // A missing icon must degrade (the symbol layer just skips that
          // feature) rather than block route rendering entirely - same
          // "best-effort, never fatal" philosophy as the label layer below.
          console.error(`Could not load topic icon for "${topic}"`);
          resolve();
        };
        // Cream fill reads clearly against the forest-green circle below it.
        img.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(topicIconSvg(topic, "#F6F4EC"));
      });
    })
  );
}

function setupRouteLayers() {
  map.addSource(ROUTE_LINE_SOURCE_ID, { type: "geojson", data: emptyFeatureCollection() });
  map.addSource(ROUTE_STOPS_SOURCE_ID, { type: "geojson", data: emptyFeatureCollection() });

  map.addLayer({
    id: "route-line-layer",
    type: "line",
    source: ROUTE_LINE_SOURCE_ID,
    layout: {
      "line-cap": "round",
      "line-join": "round",
    },
    paint: {
      "line-color": "#1E4A3A",
      "line-width": 4,
    },
  });

  map.addLayer({
    id: "route-stops-circle",
    type: "circle",
    source: ROUTE_STOPS_SOURCE_ID,
    paint: {
      "circle-radius": 12,
      "circle-color": "#1E4A3A",
      "circle-stroke-color": "#AFC29A",
      "circle-stroke-width": 2.5,
    },
  });

  // Codex review 2026-10-21: EXPERIENCE.md:137 promises a stop's content
  // opens from "a stop row or marker" - only the row worked. openStopOverlay
  // is defined later in this file, but by the time a real click fires this
  // listener (an async browser event), the whole script has already run.
  map.on("click", "route-stops-circle", (event) => {
    const feature = event.features && event.features[0];
    if (!feature) return;
    const stop = (trip.stops || []).find((s) => s.id === feature.properties.id);
    if (stop) openStopOverlay(stop);
  });
  map.on("mouseenter", "route-stops-circle", () => {
    map.getCanvas().style.cursor = "pointer";
  });
  map.on("mouseleave", "route-stops-circle", () => {
    map.getCanvas().style.cursor = "";
  });

  // Topic icon on top of each circle, replacing the old plain order-number
  // label (user feedback 2026-10-21: markers should show what kind of place
  // it is). Wrapped separately since a missing/unresolved icon image is a
  // real possibility (loadTopicIcons() degrades per-icon, not fatally) and
  // this layer must not block route rendering if that happens.
  try {
    map.addLayer({
      id: "route-stops-icon",
      type: "symbol",
      source: ROUTE_STOPS_SOURCE_ID,
      layout: {
        "icon-image": ["get", "topic_icon"],
        "icon-size": 0.58,
        "icon-allow-overlap": true,
      },
    });
  } catch (err) {
    console.error("Could not add stop-topic-icon layer:", err);
  }
}

// Rewrites both route sources from the current trip's stops/geometry.
// geometry is nullable (AD-3's degrade-don't-fail philosophy, carried into
// the frontend per this story's I/O matrix): when it's null, the stops
// still render as circles, just with no connecting line.
function updateRouteLayers() {
  const stops = Array.isArray(trip.stops) ? trip.stops : [];

  const stopFeatures = stops.map((stop) => ({
    type: "Feature",
    geometry: { type: "Point", coordinates: [stop.longitude, stop.latitude] },
    properties: { id: stop.id, order: stop.order, topic_icon: pickTopicIconName(stop.topics) },
  }));
  map.getSource(ROUTE_STOPS_SOURCE_ID).setData({
    type: "FeatureCollection",
    features: stopFeatures,
  });

  const hasGeometry = Array.isArray(trip.geometry) && trip.geometry.length > 1;
  if (hasGeometry) {
    map.getSource(ROUTE_LINE_SOURCE_ID).setData({
      type: "Feature",
      properties: {},
      geometry: { type: "LineString", coordinates: trip.geometry },
    });
  } else {
    map.getSource(ROUTE_LINE_SOURCE_ID).setData(emptyFeatureCollection());
  }

  // Codex review 2026-10-21: bounds must cover every point this screen
  // actually shows - the start point and the full walked geometry, not
  // only the stops - or an outlying one gets cropped out of the fitted
  // view. placeStartMarker() happens separately (showStep()'s "reviewing"
  // branch); this only needs the coordinate for bounds-fitting.
  const boundsPoints = stopFeatures.map((f) => f.geometry.coordinates);
  if (trip.starting_point) {
    boundsPoints.push([trip.starting_point.lng, trip.starting_point.lat]);
  }
  if (hasGeometry) {
    boundsPoints.push(...trip.geometry);
  }

  if (boundsPoints.length > 0) {
    const bounds = boundsPoints.reduce(
      (b, point) => b.extend(point),
      new maplibregl.LngLatBounds(boundsPoints[0], boundsPoints[0])
    );
    // Asymmetric padding: the fixed .review-panel sits over the bottom of
    // the map (roughly 150-180px on a phone viewport) - a flat padding
    // value would let fitBounds frame points that are then hidden behind
    // it, which plain top/left/right padding alone doesn't account for.
    map.fitBounds(bounds, {
      padding: { top: 60, bottom: 180, left: 60, right: 60 },
      maxZoom: 17,
      duration: 0,
    });
  }
}

// Clears both route sources back to empty - called whenever the trip
// returns to Trip Setup (Codex review 2026-10-21: nothing previously did
// this, so a route approved then backed out of stayed rendered on the map
// underneath the starting-point screen).
function clearRouteLayers() {
  if (!mapStyleLoaded) return;
  map.getSource(ROUTE_STOPS_SOURCE_ID).setData(emptyFeatureCollection());
  map.getSource(ROUTE_LINE_SOURCE_ID).setData(emptyFeatureCollection());
}

// The reviewing screen can be the very first thing shown (resuming a
// stored trip on reload) before the map's own "load" event has fired -
// guards against calling setData on a source that doesn't exist yet.
function refreshMapRouteLayers() {
  if (!mapStyleLoaded) return;
  updateRouteLayers();
}

map.on("load", () => {
  loadPlaces();
  // Icons must exist before setupRouteLayers() adds the symbol layer that
  // references them by name - awaited, not fire-and-forget.
  loadTopicIcons().then(() => {
    setupRouteLayers();
    mapStyleLoaded = true;
    if (trip.phase === "reviewing") updateRouteLayers();
  });
});

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
    // Populated from a successful POST /api/plan response once the trip
    // moves past Trip Setup (Story 1.5) - null throughout "setting_up".
    stops: null,
    geometry: null,
    total_minutes: null,
    unused_minutes: null,
  };
}

function isValidStartingPoint(sp) {
  return (
    typeof sp === "object" &&
    sp !== null &&
    Number.isFinite(sp.lat) &&
    Number.isFinite(sp.lng) &&
    sp.lat >= -90 &&
    sp.lat <= 90 &&
    sp.lng >= -180 &&
    sp.lng <= 180 &&
    typeof sp.label === "string"
  );
}

function isValidAttributionEntry(entry) {
  return (
    entry &&
    typeof entry === "object" &&
    (entry.source_type === null || typeof entry.source_type === "string") &&
    (entry.source_title === null || typeof entry.source_title === "string") &&
    (entry.source_url === null || typeof entry.source_url === "string")
  );
}

function isValidStop(stop) {
  return (
    stop &&
    typeof stop === "object" &&
    typeof stop.id === "string" &&
    Number.isInteger(stop.order) &&
    typeof stop.name === "string" &&
    Number.isFinite(stop.latitude) &&
    stop.latitude >= -90 &&
    stop.latitude <= 90 &&
    Number.isFinite(stop.longitude) &&
    stop.longitude >= -180 &&
    stop.longitude <= 180 &&
    Array.isArray(stop.topics) &&
    typeof stop.content === "string" &&
    Array.isArray(stop.attribution) &&
    stop.attribution.every(isValidAttributionEntry)
  );
}

// Points are [lng, lat] (GeoJSON order, matching how they're built elsewhere
// in this file - e.g. [stop.longitude, stop.latitude]).
function isValidGeometry(geometry) {
  if (geometry === null) return true;
  return (
    Array.isArray(geometry) &&
    geometry.every(
      (point) =>
        Array.isArray(point) &&
        point.length === 2 &&
        Number.isFinite(point[0]) &&
        point[0] >= -180 &&
        point[0] <= 180 &&
        Number.isFinite(point[1]) &&
        point[1] >= -90 &&
        point[1] <= 90
    )
  );
}

// Fields every phase shares, checked once regardless of which phase branch
// runs next.
function hasValidCommonFields(candidate) {
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
  if (candidate.starting_point !== null && !isValidStartingPoint(candidate.starting_point)) {
    return false;
  }
  return true;
}

function isValidSettingUpShape(candidate) {
  if (!SETUP_STEPS.includes(candidate.setup_step)) return false;
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

// Shared by "reviewing" and "walking" (Story 1.5 Implementation Notes: the
// "walking" phase's real shape is Epic 2's job - reusing this shape
// verbatim is the minimal thing that lets Approve do something real and
// keeps safe-reset working, pending that later story).
function isValidReviewingShape(candidate) {
  if (candidate.setup_step !== null) return false;
  if (candidate.starting_point === null) return false;
  if (candidate.topic === null) return false;
  if (!Array.isArray(candidate.stops) || candidate.stops.length === 0) return false;
  if (!candidate.stops.every(isValidStop)) return false;
  if (!isValidGeometry(candidate.geometry)) return false;
  if (!Number.isFinite(candidate.total_minutes)) return false;
  if (!Number.isFinite(candidate.unused_minutes)) return false;
  return true;
}

// Basic shape validation beyond the schema_version check (architecture AD-2:
// "a payload that fails basic shape validation is treated as unusable and
// triggers a safe reset"). Keeps a partially-corrupted object from reaching
// the screen logic and crashing it. Branches on `phase` (Story 1.5) since
// "reviewing"/"walking" payloads carry a genuinely different shape from
// "setting_up" - a single flat shape can't validate both honestly.
function isValidTrip(candidate) {
  if (!candidate || typeof candidate !== "object") return false;
  if (candidate.schema_version !== SCHEMA_VERSION) return false;
  if (!hasValidCommonFields(candidate)) return false;

  if (candidate.phase === "setting_up") {
    return isValidSettingUpShape(candidate);
  }
  if (candidate.phase === "reviewing" || candidate.phase === "walking") {
    return isValidReviewingShape(candidate);
  }
  return false;
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
const screenLoading = document.getElementById("screen-loading");
const screenReviewing = document.getElementById("screen-reviewing");
const screenReviewUnavailable = document.getElementById("screen-review-unavailable");
const screenWalkingStub = document.getElementById("screen-walking-stub");

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

const loadingHeadingEl = document.getElementById("loading-heading");

const reviewingTitleEl = document.getElementById("reviewing-title");
const reviewSummaryEl = document.getElementById("review-summary");
const openStopListBtn = document.getElementById("open-stop-list-btn");
const openCreditsBtn = document.getElementById("open-credits-btn");
const approveRouteBtn = document.getElementById("approve-route-btn");
const changeJauntBtn = document.getElementById("change-jaunt-btn");

const stopListSheetWrapEl = document.getElementById("stop-list-sheet-wrap");
const stopListSheetEl = document.getElementById("stop-list-sheet");
const stopListCloseBtn = document.getElementById("stop-list-close-btn");
const stopListEl = document.getElementById("stop-list");

const stopOverlayWrapEl = document.getElementById("stop-overlay-wrap");
const stopOverlaySheetEl = document.getElementById("stop-overlay-sheet");
const stopOverlayCloseBtn = document.getElementById("stop-overlay-close-btn");
const stopOverlayHeadingEl = document.getElementById("stop-overlay-heading");
const stopOverlayPhotoEl = document.getElementById("stop-overlay-photo");
const stopOverlayBodyEl = document.getElementById("stop-overlay-body");
const stopOverlayAttributionEl = document.getElementById("stop-overlay-attribution");

const creditsSheetWrapEl = document.getElementById("credits-sheet-wrap");
const creditsSheetEl = document.getElementById("credits-sheet");
const creditsCloseBtn = document.getElementById("credits-close-btn");

const reviewUnavailableHeadingEl = document.getElementById("review-unavailable-heading");
const reviewUnavailableDetailEl = document.getElementById("review-unavailable-detail");
const reviewUnavailableBackBtn = document.getElementById("review-unavailable-back-btn");

const walkingStubHeadingEl = document.getElementById("walking-stub-heading");
const walkingStubDetailEl = document.getElementById("walking-stub-detail");
const walkingStubBackBtn = document.getElementById("walking-stub-back-btn");

let stopOverlayTriggerEl = null;

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

// trip.preference keeps its own meaning (0 = well-known, 1 = hidden gems)
// regardless of layout; the labels read "Hidden gems" (left) -> "Well-known"
// (right), so the native range input's own left-to-right direction (0..100)
// is the inverse of trip.preference and needs converting both ways.
function prefToInputValue(pref) {
  return Math.round((1 - pref) * 100);
}
function inputValueToPref(value) {
  return 1 - Number(value) / 100;
}

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

// Visual classes (hence row font-size/color, via the CSS transition on
// .picker-row) update on every raw scroll event, live - a row grows as it
// scrolls into the grey highlight instead of only snapping to full size
// once scrolling stops. The actual commit (trip.available_minutes, ARIA,
// localStorage) stays debounced, so a fast swipe doesn't spam writes.
let timeScrollDebounce = null;
timePickerListEl.addEventListener("scroll", () => {
  const liveIndex = Math.round(timePickerListEl.scrollTop / TIME_ROW_HEIGHT);
  const liveClamped = Math.max(0, Math.min(TIME_VALUES.length - 1, liveIndex));
  syncTimePickerClasses(liveClamped);

  clearTimeout(timeScrollDebounce);
  timeScrollDebounce = setTimeout(() => {
    selectTimeIndex(liveClamped);
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
  screenLoading.hidden = true;
  screenReviewing.hidden = true;
  screenReviewUnavailable.hidden = true;
  screenWalkingStub.hidden = true;
}

// Shows one of the 4 real setup screens (the confirm sheet is a separate
// overlay, handled by openConfirmSheet/closeConfirmSheet below), updates
// setup_step + persists it, pre-fills every control from the current trip
// state, and moves focus to the new screen unless the caller is about to
// move it somewhere more specific itself (e.g. a recorded back-navigation
// trigger).
function showStep(step, { focusDefault = true } = {}) {
  hideAllScreens();

  // Only a real Trip Setup step is persisted as setup_step - "reviewing"/
  // "walking" (Story 1.5) aren't setup steps at all, and setup_step stays
  // null once the trip has moved past setup (Code Map, AD-2).
  if (SETUP_STEPS.includes(step)) {
    trip.setup_step = step;
    saveActiveTrip(trip);
    // Codex review 2026-10-21: returning to any setup step must leave
    // Route Review's own map state behind - a previously-approved route no
    // longer lingers on the map underneath the starting-point screen.
    // Catalogue markers themselves never reappear here - see
    // setCatalogueMarkersVisible()'s own comment (2026-10-21 UX feedback:
    // the default blue pins looked messy and are permanently off, not
    // phase-toggled).
    clearRouteLayers();
  }

  mapStageEl.hidden = step !== "starting_point" && step !== "reviewing";

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
    prefRangeRestEl.value = String(prefToInputValue(trip.preference));
    updatePrefBalancedTags();
    if (focusDefault) topicAtRestTitleEl.focus();
  } else if (step === "choose_topic") {
    screenChooseTopic.hidden = false;
    recapChooseTopicEl.textContent = buildRecap();
    prefRangeChooseEl.value = String(prefToInputValue(trip.preference));
    updatePrefBalancedTags();
    refreshTopicPills();
    if (focusDefault) chooseTopicTitleEl.focus();
  } else if (step === "reviewing") {
    screenReviewing.hidden = false;
    reviewSummaryEl.textContent = buildReviewSummary();
    // Codex review 2026-10-21: resuming straight into "reviewing" (e.g. a
    // reload) never ran the starting-point screen's own branch, so the
    // start pin was never (re)created on this path.
    if (trip.starting_point) {
      placeStartMarker(trip.starting_point.lat, trip.starting_point.lng);
    }
    refreshMapRouteLayers();
    if (focusDefault) reviewingTitleEl.focus();
  } else if (step === "walking") {
    screenWalkingStub.hidden = false;
    const stopCount = Array.isArray(trip.stops) ? trip.stops.length : 0;
    walkingStubDetailEl.textContent =
      `${stopCount} stop${stopCount === 1 ? "" : "s"} - Epic 2 builds the real walking screen here.`;
    if (focusDefault) walkingStubHeadingEl.focus();
  }
}

function buildReviewSummary() {
  const stopCount = Array.isArray(trip.stops) ? trip.stops.length : 0;
  // total_minutes/unused_minutes come from real walking-speed arithmetic
  // (distance / speed), so they're rarely whole numbers - round only for
  // this display, never for the stored/compared values.
  const total = Number.isFinite(trip.total_minutes) ? Math.round(trip.total_minutes) : "?";
  const unused = Number.isFinite(trip.unused_minutes) ? Math.round(trip.unused_minutes) : null;
  const stopsPart = `${stopCount} stop${stopCount === 1 ? "" : "s"}`;
  const timePart = unused !== null ? `${total} min walk - ${unused} min to spare` : `${total} min walk`;
  return `${stopsPart} - ${timePart}`;
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
  startRoutePlanning();
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
// ROUTE REVIEW (Story 1.5) - bridges Trip Setup's held values into the
// real POST /api/plan endpoint (Story 1.4). No other story's AC assigns
// this call explicitly (see spec's Design Notes); it's done here since
// this is the first screen that needs the response.
// =====================================================================

const PLANNING_FAILURE_MESSAGE =
  "Something went wrong finding your route. (Temporary placeholder - Story 1.6 builds the real experience.)";
const PLANNING_HONEST_FALLBACK_MESSAGE =
  "Jarrod couldn't find a route that fits this time. (Temporary placeholder - Story 1.6 builds the real experience.)";
// Codex review 2026-10-21: the original 60s figure only covered the
// ~30-45s *typical* end-to-end request. The backend's own worst case is
// much larger - services.py's routing calls time out at 30s each, and
// ai.py's selection/content-generation/grounding calls each time out at
// 60s, with up to 3 selection retries - a genuinely unlucky request can
// legitimately take ~30 + 3*60 + 60 + 60 = 360s server-side. 180s is a
// deliberate middle ground (the user's explicit choice): it comfortably
// covers the realistic worst case without literally waiting out the full
// 360s, and an abort here doesn't cancel the server-side work anyway (no
// cooperative cancellation exists) - a real shared time budget threaded
// through the retry loop is deferred, see deferred-work.md.
const PLANNING_REQUEST_TIMEOUT_MS = 180000;

function showLoadingScreen() {
  hideAllScreens();
  mapStageEl.hidden = true;
  screenLoading.hidden = false;
  loadingHeadingEl.focus();
}

// Both non-feasible response shapes (honest fallback and a real technical
// failure) land here - this story's only job for either is a minimal,
// clearly-temporary placeholder with a way back; Story 1.6 owns the real
// fallback copy/visuals.
function showReviewUnavailable(message) {
  hideAllScreens();
  mapStageEl.hidden = true;
  reviewUnavailableDetailEl.textContent = message;
  screenReviewUnavailable.hidden = false;
  reviewUnavailableHeadingEl.focus();
}

async function startRoutePlanning() {
  showLoadingScreen();

  const payload = {
    start_lat: trip.starting_point.lat,
    start_lon: trip.starting_point.lng,
    topic: trip.topic,
    requested_minutes: trip.available_minutes,
  };

  let response;
  try {
    response = await fetch("/api/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      // Without this, a hung request leaves the user stuck on the loading
      // screen indefinitely with no escape - an abort surfaces as a thrown
      // AbortError, caught by the same catch as any other network failure.
      signal: AbortSignal.timeout(PLANNING_REQUEST_TIMEOUT_MS),
    });
  } catch (err) {
    console.error("Planning request failed to send:", err);
    showReviewUnavailable(PLANNING_FAILURE_MESSAGE);
    return;
  }

  let data;
  try {
    data = await response.json();
  } catch (err) {
    console.error("Planning response was not valid JSON:", err);
    showReviewUnavailable(PLANNING_FAILURE_MESSAGE);
    return;
  }

  // Non-2xx is a real technical failure (app.py reserves it for genuine
  // service failures) - logged for debugging, never surfaced raw to the
  // user (I/O matrix).
  if (!response.ok) {
    console.error(`Planning request failed with status ${response.status}:`, data);
    showReviewUnavailable(PLANNING_FAILURE_MESSAGE);
    return;
  }

  // A 200 with feasible:false is the honest "no suitable walk" outcome,
  // distinct from a technical failure - same minimal placeholder here,
  // but logged with its own real reason.
  if (!data.feasible) {
    console.error("No feasible route:", data.reason);
    showReviewUnavailable(PLANNING_HONEST_FALLBACK_MESSAGE);
    return;
  }

  trip.phase = "reviewing";
  trip.setup_step = null;
  trip.stops = data.stops;
  trip.geometry = data.geometry ?? null;
  trip.total_minutes = data.total_minutes;
  trip.unused_minutes = data.unused_minutes;
  saveActiveTrip(trip);
  showStep("reviewing");
}

// =====================================================================
// ROUTE REVIEW - stop-list bottom sheet, stop-content overlay, and the
// shared credits panel. All three reuse the confirm-sheet's dim+sheet
// shell (.sheet-wrap/.dim-overlay/.confirm-sheet) and the same
// inert-the-screen-behind-it pattern already established for the confirm
// sheet above.
// =====================================================================

function humanizeSourceType(sourceType) {
  if (!sourceType) return "Source";
  return sourceType
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function renderStopList() {
  stopListEl.innerHTML = "";
  (trip.stops || []).forEach((stop) => {
    const li = document.createElement("li");

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "stop-list-btn";
    btn.setAttribute("aria-label", `View details for stop ${stop.order}, ${stop.name}`);

    const orderEl = document.createElement("span");
    orderEl.className = "stop-list-order";
    orderEl.textContent = String(stop.order);
    orderEl.setAttribute("aria-hidden", "true");

    // User feedback 2026-10-21: the list is "a bit boring without any
    // [icon]" - same topic icon as the map marker, forest-colored against
    // the row's own muted badge background rather than cream-on-forest.
    const iconEl = document.createElement("span");
    iconEl.className = "stop-list-icon";
    iconEl.setAttribute("aria-hidden", "true");
    iconEl.innerHTML = topicIconSvg(pickTopic(stop.topics), "#1E4A3A");

    const textWrap = document.createElement("span");
    textWrap.className = "stop-list-text";

    const nameEl = document.createElement("span");
    nameEl.className = "stop-list-name";
    nameEl.textContent = stop.name || "Unnamed stop";

    const topicsEl = document.createElement("span");
    topicsEl.className = "stop-list-topics";
    topicsEl.textContent = (stop.topics || []).join(", ");

    textWrap.appendChild(nameEl);
    textWrap.appendChild(topicsEl);
    btn.appendChild(orderEl);
    btn.appendChild(iconEl);
    btn.appendChild(textWrap);
    btn.addEventListener("click", () => {
      closeStopListSheet({ restoreFocus: false });
      openStopOverlay(stop);
    });

    li.appendChild(btn);
    stopListEl.appendChild(li);
  });
}

// A sheet open over the reviewing screen must also exclude the live map
// underneath from the tab order - #map-stage is a DOM sibling of
// #screen-reviewing, not a descendant, so toggling screenReviewing.inert
// alone never reaches the map's own NavigationControl zoom buttons, which
// would otherwise stay tabbable behind the dim overlay.
function setReviewSheetInert(isInert) {
  if ("inert" in screenReviewing) screenReviewing.inert = isInert;
  if ("inert" in mapStageEl) mapStageEl.inert = isInert;
}

function openStopListSheet() {
  setReviewSheetInert(true);
  renderStopList();
  stopListSheetWrapEl.hidden = false;
  stopListSheetEl.focus();
}

function closeStopListSheet({ restoreFocus = true } = {}) {
  stopListSheetWrapEl.hidden = true;
  setReviewSheetInert(false);
  if (restoreFocus) openStopListBtn.focus();
}

// Shows a stop's full generated content and every attribution entry (not
// only the first - AD-3) in the shared overlay shell.
function openStopOverlay(stop) {
  stopOverlayTriggerEl = openStopListBtn;
  setReviewSheetInert(true);

  stopOverlayHeadingEl.textContent = stop.name || "Stop";

  // Optional, not yet populated by any real backend response (Story 1.11's
  // own job) - degrades to hidden exactly like a missing attribution
  // entry would, never a broken image.
  if (stop.photo_url) {
    stopOverlayPhotoEl.src = stop.photo_url;
    stopOverlayPhotoEl.alt = stop.name ? `Photo of ${stop.name}` : "";
    stopOverlayPhotoEl.hidden = false;
  } else {
    stopOverlayPhotoEl.hidden = true;
    stopOverlayPhotoEl.removeAttribute("src");
  }

  stopOverlayBodyEl.textContent = stop.content || "";

  stopOverlayAttributionEl.innerHTML = "";
  (stop.attribution || []).forEach((entry) => {
    const li = document.createElement("li");
    const label = document.createTextNode(`${humanizeSourceType(entry.source_type)}: `);
    li.appendChild(label);
    if (entry.source_url) {
      const link = document.createElement("a");
      link.href = entry.source_url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = entry.source_title || entry.source_url;
      li.appendChild(link);
    } else {
      li.appendChild(document.createTextNode(entry.source_title || "unknown"));
    }
    stopOverlayAttributionEl.appendChild(li);
  });

  stopOverlayWrapEl.hidden = false;
  stopOverlaySheetEl.focus();
}

function closeStopOverlay() {
  stopOverlayWrapEl.hidden = true;
  setReviewSheetInert(false);
  if (stopOverlayTriggerEl) stopOverlayTriggerEl.focus();
  stopOverlayTriggerEl = null;
}

// The shared, app-wide credits element (FR-20) - names all five data
// providers regardless of which stops are in this particular route, and
// is reachable independently of any single stop's own citation.
function openCreditsSheet() {
  setReviewSheetInert(true);
  creditsSheetWrapEl.hidden = false;
  creditsSheetEl.focus();
}

function closeCreditsSheet() {
  creditsSheetWrapEl.hidden = true;
  setReviewSheetInert(false);
  openCreditsBtn.focus();
}

openStopListBtn.addEventListener("click", openStopListSheet);
stopListCloseBtn.addEventListener("click", () => closeStopListSheet());
stopOverlayCloseBtn.addEventListener("click", closeStopOverlay);
openCreditsBtn.addEventListener("click", openCreditsSheet);
creditsCloseBtn.addEventListener("click", closeCreditsSheet);

// Codex review 2026-10-21: UX-DR11/the spec's own Boundaries text promise
// swipe-down-to-dismiss alongside the close-x on every sheet - user's
// explicit choice was to build the real gesture rather than drop the
// requirement. Attached to each sheet's drag handle only (not the sheet
// body), so it never competes with scrolling the stop list or a long stop
// overlay body (both use .sheet-scroll).
const SWIPE_DISMISS_THRESHOLD_PX = 50;

function attachSwipeToDismiss(handleEl, onDismiss) {
  let startY = null;

  handleEl.addEventListener("pointerdown", (event) => {
    startY = event.clientY;
    // Caught, not just optionally-chained: the browser can refuse this
    // (e.g. no pointer it considers "active" for this id) and throws
    // synchronously rather than silently no-op-ing - verified directly,
    // not assumed. Capture is a drag-tracking nicety (keeps the gesture
    // live if the pointer strays off the handle); losing it only means
    // straying off-handle mid-drag won't dismiss, not that the gesture
    // breaks entirely.
    try {
      handleEl.setPointerCapture?.(event.pointerId);
    } catch (err) {
      /* no-op */
    }
  });
  handleEl.addEventListener("pointerup", (event) => {
    if (startY === null) return;
    const deltaY = event.clientY - startY;
    startY = null;
    if (deltaY > SWIPE_DISMISS_THRESHOLD_PX) onDismiss();
  });
  handleEl.addEventListener("pointercancel", () => {
    startY = null;
  });
}

attachSwipeToDismiss(document.querySelector("#confirm-sheet .handle"), () => {
  dismissLink.click();
});
attachSwipeToDismiss(document.querySelector("#stop-list-sheet .handle"), () => closeStopListSheet());
attachSwipeToDismiss(document.querySelector("#stop-overlay-sheet .handle"), () => closeStopOverlay());
attachSwipeToDismiss(document.querySelector("#credits-sheet .handle"), () => closeCreditsSheet());

approveRouteBtn.addEventListener("click", () => {
  trip.phase = "walking";
  saveActiveTrip(trip);
  showStep("walking");
});

// Codex review 2026-10-21: a successful review previously had no decline/
// change-inputs path at all - same phase-reset reasoning as
// walkingStubBackBtn below (trip.phase must go back to "setting_up" before
// showStep(originStep) persists a setup_step, or isValidTrip() would
// reject the stored trip on the next reload).
changeJauntBtn.addEventListener("click", () => {
  const originStep = trip.topic === "surprise_me" ? "topic_at_rest" : "choose_topic";
  trip.phase = "setting_up";
  showStep(originStep);
});

reviewUnavailableBackBtn.addEventListener("click", () => {
  const originStep = trip.topic === "surprise_me" ? "topic_at_rest" : "choose_topic";
  showStep(originStep);
});

// Unlike reviewUnavailableBackBtn above, trip.phase actually left
// "setting_up" to get here (Approve set it to "walking") - it must be put
// back before showStep(originStep) persists a setup_step, or the stored
// trip would carry phase:"walking" with a non-null setup_step, which
// isValidTrip() itself would reject on the next reload.
walkingStubBackBtn.addEventListener("click", () => {
  const originStep = trip.topic === "surprise_me" ? "topic_at_rest" : "choose_topic";
  trip.phase = "setting_up";
  showStep(originStep);
});

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
    trip.preference = inputValueToPref(input.value);
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
  if (trip.phase === "reviewing" || trip.phase === "walking") {
    showStep(trip.phase, { focusDefault: false });
    return;
  }
  if (trip.setup_step === "confirm_sheet") {
    const originStep = trip.topic === "surprise_me" ? "topic_at_rest" : "choose_topic";
    showStep(originStep, { focusDefault: false });
    const hostEl = originStep === "topic_at_rest" ? screenTopicAtRest : screenChooseTopic;
    openConfirmSheet(trip.topic, null, hostEl);
    return;
  }
  showStep(trip.setup_step, { focusDefault: false });
}

// Launch splash (EXPERIENCE.md): plays once per page load, then gets out of
// the way - never shown again until a fresh load. Auto-advances after a
// fixed duration (long enough to see the full reveal plus a little of the
// idle loop), but any tap/click/keypress skips it immediately - a purely
// decorative screen must never trap a keyboard/screen-reader user for a
// fixed few seconds with no way out.
const SPLASH_AUTO_ADVANCE_MS = 4800;

function dismissSplash() {
  if (screenSplashEl.hidden) return;
  screenSplashEl.hidden = true;
  initTripSetup();
}

// screenSplashEl itself (role="presentation", no tabindex) can never be the
// keydown target - listening on document is what actually makes "any key
// skips it" true, not just "any click inside this specific div."
screenSplashEl.addEventListener("click", dismissSplash);
document.addEventListener("keydown", dismissSplash);
setTimeout(dismissSplash, SPLASH_AUTO_ADVANCE_MS);
