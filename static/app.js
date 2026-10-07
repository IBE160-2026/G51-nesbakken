// Renders the real catalogue on a map, and lets a tap place a visual
// start-point marker. Migrated from Leaflet to MapLibre GL JS (2026-10-07,
// architecture decision AD-1) - see ARCHITECTURE-SPINE.md. Base style is
// OpenFreeMap's "positron" (closest free out-of-the-box match to DESIGN.md's
// muted cream palette); a fully custom DESIGN.md-matched style is later,
// separate work, not part of this migration.

const NEWTOWN_CENTER = [151.1793, -33.8977]; // MapLibre uses [lng, lat]
const MAP_STYLE = "https://tiles.openfreemap.org/styles/positron";
const POPUP_OPTIONS = { maxWidth: "260px" };
const START_MARKER_COLOR = "#e63946";

const statusEl = document.getElementById("status");
const instructionsEl = document.getElementById("instructions");

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

map.on("click", (event) => {
  const { lat, lng } = event.lngLat;
  if (startMarker) {
    startMarker.setLngLat([lng, lat]);
  } else {
    startMarker = new maplibregl.Marker({ element: buildStartMarkerElement() })
      .setLngLat([lng, lat])
      .setPopup(new maplibregl.Popup(POPUP_OPTIONS).setText("Start point"))
      .addTo(map);
  }
  startMarker.togglePopup();
  instructionsEl.textContent = "";
});

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
