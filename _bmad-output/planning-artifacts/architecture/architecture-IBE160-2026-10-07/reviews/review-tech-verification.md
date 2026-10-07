---
name: review-tech-verification
reviews: ARCHITECTURE-SPINE.md (architecture-IBE160-2026-10-07)
lens: technical-claim verification (web-researched vs. asserted from training data)
date: 2026-10-07
method: Read-only review. Checked each named technology/version/claim against live web sources (search + direct fetch), and compared AD-1's description of "what's implemented" against the actual code in static/app.js and templates/index.html.
---

# Reviewer Gate — Technical Verification of ARCHITECTURE-SPINE.md

## Verdict

Every specific, checkable technical claim in the spine (MapLibre 5.6.1 is real; v6 drops the UMD bundle and is ESM-only; OpenFreeMap's public instance is free/keyless/limit-free; Flask 3.1.3 and Python 3.13 are real released versions; OpenRouteService's `foot-walking` profile is keyed) came back **true on independent web verification as of 2026-10-07** — these read as genuinely researched, not asserted from stale training data. The one real problem found is not a false technical claim but an **internal consistency gap**: AD-1's "Status" line describes the base layer as implemented with nothing yet violating the rule, but the existing `loadPlaces()` code in `static/app.js` already renders catalogue places as individual `maplibregl.Marker()` DOM markers — the exact "many-of-a-kind as individual DOM markers" anti-pattern AD-1's own rule prohibits — and the spine never flags this tension.

## Claim-by-claim verification

### 1. MapLibre GL JS 5.6.1 — real version? v6 ESM-only / UMD dropped?

**Verified true, on both counts.**

- `5.6.1` is a real, specific patch release. Found via OpenStreetMap's own dependency-bump PRs (`maplibre-gl` bumped 5.6.0→5.6.1, then 5.6.1→5.6.2).
- Direct fetch of `https://unpkg.com/maplibre-gl@5.6.1/dist/maplibre-gl.js` (the exact URL `templates/index.html` loads) returns a real UMD bundle — the file opens with the standard UMD wrapper (`typeof exports === 'object' ... define.amd ... global.maplibregl = factory()`) and self-identifies as MapLibre GL JS 5.6.1, BSD-3-Clause. So the pin is not just plausible, it's confirmed to work as a plain `<script>` tag today.
- MapLibre GL JS **v6.0.0 was released 2026-07-22** (confirmed via the GitHub release and the project's own v5→v6 migration guide). The migration guide states verbatim: *"MapLibre GL JS v6 ships as ES modules only. The UMD bundle, the separate CSP build, and the CommonJS (`require('maplibre-gl')`) entry from v5 are all gone."* Consumers using a plain `<script src="...">` tag must switch to `<script type="module">`. This exactly matches the spine's stated reason for pinning.
- Notably, v6 was already released **before** this spine was written (2026-10-07 vs. 2026-07-22 release), so this isn't a hedge against a hypothetical future break — a careless "latest" install today would already pull the breaking ESM-only version. The spine's justification is current and accurate, and reads like it was actually checked against the live npm/CDN state rather than recalled from training data (MapLibre v6 postdates most training cutoffs).

Sources: https://lists.openstreetmap.org/pipermail/rails-dev/2025-July/042801.html , https://lists.openstreetmap.org/pipermail/rails-dev/2025-August/043339.html , https://maplibre.org/maplibre-gl-js/docs/guides/v5-to-v6-migration-guide/ , https://github.com/maplibre/maplibre-gl-js/releases/tag/v6.0.0 , https://unpkg.com/maplibre-gl@5.6.1/dist/maplibre-gl.js

### 2. OpenFreeMap "positron" — still free, no API key, no request limit?

**Verified true.** Direct fetch of https://openfreemap.org today confirms, in the site's own words: *"Using our public instance is completely free: there are no limits on the number of map views or requests."* and *"no registration, no user database, no API keys, and no cookies."* Five styles are offered including `positron`, matching the spine's choice. This matches the spine's claim exactly, word for word almost.

**Soft risk not raised by the spine (worth a note, not a correction):** OpenFreeMap's public instance is funded by donations with no stated SLA/uptime guarantee — it's a goodwill free tier, not a contracted service. The spine states the claim correctly for today, but doesn't flag that "free, no key, no limit" is a *current, revocable* policy rather than a guarantee, which matters slightly for a course project that will be graded by live demo. Low severity — informational, not a factual error.

Source: https://openfreemap.org

### 3. OpenRouteService — foot-walking profile, keyed

**Verified true.** `foot-walking` is a real, documented OpenRouteService Directions API profile (confirmed via ORS community docs and API examples). The free public tier does require account registration/API key (~8,000 requests/day, per ORS's own restrictions page), which matches the spine's "keyed, server-side only" description — the spine doesn't claim ORS is limit-free, so there's no overclaim here, just an unstated daily cap that a future builder should be aware of if the course demo involves heavy repeated testing.

Source: https://openrouteservice.org/restrictions/ , https://ask.openrouteservice.org/t/foot-walking-profile-doesnt-seem-to-avoid-highway-trunk/4171

### 4. Flask 3.1.3, Python 3.13

**Both verified as real, currently-installable versions.**

- Flask 3.1.3 is a real PyPI release (security-fix release addressing GHSA-68rp-wp8r-4726), released 2026-02-19, with proper PyPI trusted-publishing attestation. Confirmed on pypi.org directly.
- Python 3.13 is a real, still-supported release line (now in maintenance mode; 3.13.16 was its last full maintenance release, with 3.13.14-era patches still being issued as of mid-2026). Python 3.14 (released 2025-10-07) is now the current feature release, but the spine never claims 3.13 is "latest" — it's stated as the stack version in use, which is accurate and still a reasonable, supported choice. Not a factual error, just worth knowing 3.13 is one release behind current for a reader deciding whether to upgrade later.

Sources: https://pypi.org/project/Flask/3.1.3/ , https://www.python.org/downloads/release/python-31316/

## Code-vs-spine check: does the implementation match AD-1's description?

Read `static/app.js` and `templates/index.html` directly.

**Matches confirmed:**
- `templates/index.html` loads MapLibre pinned to `5.6.1` consistently in both the CSS (`unpkg.com/maplibre-gl@5.6.1/dist/maplibre-gl.css`) and JS (`.../maplibre-gl.js`) tags — no version drift between the two.
- The one-off, custom-DOM-element marker pattern AD-1 describes ("the live-position marker... use `maplibregl.Marker({element})` with a custom DOM element, the same pattern already established for the start-point marker") is real and present: `app.js` lines 38–48 build a custom circular `<div>` and lines 57–61 instantiate it via `new maplibregl.Marker({ element: buildStartMarkerElement() })`. This part of the spine's description is accurate.

**Gap found — AD-1's status line doesn't mention an existing contradiction:**

AD-1's rule explicitly bans drawing "many-of-a-kind" data-driven features (its own examples: route line, background amenity points / FR-23, numbered stop circles) as individual DOM markers, mandating GeoJSON sources + MapLibre paint layers instead. AD-1's status note then says: *"the route line, stop markers, live-position marker, and amenity dots below are not yet built"* — implying the rule has nothing yet to conflict with.

But `app.js`'s `loadPlaces()` function (lines 89–119) already fetches the full catalogue from `/api/places` and renders **every place as an individual `new maplibregl.Marker()`** (lines 110–118) — i.e., exactly the many-of-a-kind-as-individual-DOM-markers pattern the rule was written to prevent. Whether this is meant as throwaway debug/demo code (visualizing the catalogue before the real trip UI exists) or an early version of the FR-23 "amenity dots" feature, the spine's status line doesn't acknowledge it either way. A future builder who trusts "base layer implemented, nothing else built yet" at face value could reasonably assume there's no AD-1 conflict to resolve, when in fact there's existing code that will need to be replaced (or explicitly exempted as temporary) to comply with the rule just adopted.

**Severity: Medium.** Not a false claim about external technology, but exactly the kind of "spine says X, code says Y" mismatch a Reviewer Gate exists to catch, and it's cheap to fix: either note in AD-1's status line that `loadPlaces()`'s current per-place markers are temporary/non-compliant scaffolding to be replaced by the GeoJSON layer, or acknowledge the tension explicitly.

## Summary table

| Claim | Verdict | Confidence |
|---|---|---|
| MapLibre GL JS 5.6.1 is a real version | True | High (fetched the actual file) |
| MapLibre v6 drops UMD, becomes ESM-only | True | High (official migration guide + release notes) |
| OpenFreeMap positron: free, no key, no limit | True | High (fetched the live site today) |
| OpenRouteService foot-walking profile, keyed | True | High |
| Flask 3.1.3 real release | True | High (PyPI direct) |
| Python 3.13 real, supported release | True | Medium-High (now one behind 3.14, not "latest" but not wrong) |
| AD-1 status line accurately describes current code | **Partially false** — omits existing `loadPlaces()` per-place DOM markers that pre-empt AD-1's own anti-pattern rule | Medium severity |

## Sources checked

- https://lists.openstreetmap.org/pipermail/rails-dev/2025-July/042801.html
- https://lists.openstreetmap.org/pipermail/rails-dev/2025-August/043339.html
- https://maplibre.org/maplibre-gl-js/docs/guides/v5-to-v6-migration-guide/
- https://github.com/maplibre/maplibre-gl-js/releases/tag/v6.0.0
- https://unpkg.com/maplibre-gl@5.6.1/dist/maplibre-gl.js
- https://openfreemap.org
- https://openrouteservice.org/restrictions/
- https://ask.openrouteservice.org/t/foot-walking-profile-doesnt-seem-to-avoid-highway-trunk/4171
- https://pypi.org/project/Flask/3.1.3/
- https://www.python.org/downloads/release/python-31316/
