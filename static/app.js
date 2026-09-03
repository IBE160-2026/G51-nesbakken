// Sprint 2: just plumbing - render the real catalogue on a map, and let a
// tap place a visual start-point marker. No filtering or logic yet.

const NEWTOWN_CENTER = [-33.8977, 151.1793];
const POPUP_OPTIONS = { maxWidth: 260 };
const START_MARKER_OPTIONS = {
  radius: 10,
  color: "#e63946",
  fillColor: "#e63946",
  fillOpacity: 0.9,
  weight: 2,
};

const statusEl = document.getElementById("status");
const instructionsEl = document.getElementById("instructions");

const map = L.map("map", { zoomControl: false }).setView(NEWTOWN_CENTER, 15);

// Bottom-right is the standard thumb-reachable placement for one-handed
// phone use - Leaflet's default (top-left) assumes a desktop mouse.
L.control.zoom({ position: "bottomright" }).addTo(map);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

instructionsEl.textContent = "Tap the map to choose your starting point";

let startMarker = null;

map.on("click", (event) => {
  const { lat, lng } = event.latlng;
  if (startMarker) {
    startMarker.setLatLng([lat, lng]);
  } else {
    // A circle marker (Leaflet-native, no custom icon assets) is visually
    // distinct in both shape and colour from the default pin markers used
    // for stops below.
    startMarker = L.circleMarker([lat, lng], START_MARKER_OPTIONS)
      .addTo(map)
      .bindPopup("Start point", POPUP_OPTIONS);
  }
  startMarker.openPopup();
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
    const marker = L.marker([place.latitude, place.longitude]).addTo(map);
    marker.bindPopup(buildPopupContent(place), POPUP_OPTIONS);
  });
}

loadPlaces();
