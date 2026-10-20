---
title: 'Trip Setup inputs - starting point, time, and topic'
type: 'feature'
created: '2026-10-20'
status: 'ready-for-dev'
route: 'dispatch'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `app.py`/`templates/index.html`/`static/app.js` are still the Sprint-2 proof-of-plumbing build - a bare MapLibre map with no way to choose a starting point for real, set available time, or pick a topic. Jaunt has no Trip Setup flow at all yet.

**Approach:** Build the four-screen Trip Setup flow (starting point -> available time -> topic -> confirm) as client-side screen states over the existing MapLibre map, following `mockups/flow-01-setup.html` for structure/copy/visuals. Captured values live in a new `localStorage`-persisted active-trip object (AD-2); nothing is sent to the backend yet (no planning endpoint exists until Story 1.4).

## Boundaries & Constraints

**Always:** Keyboard-operable + `aria-label`ed controls on every input; compact-pill vs full-width button components stay visually and structurally distinct (recurring bug); chip/pill selection is fill inversion only; Jarrod is always a real cropped region of `jaunty-mascot-sheet-v2-eyes-transparent.png`, never new/regenerated art; copy matches the mockup's plain/warm voice verbatim; existing `/api/places` catalogue-marker rendering keeps working unchanged.

**Never:** No call to any backend planning endpoint (doesn't exist yet - Story 1.4); no "use my current location" button (Story 1.10's scope - absent from this story's own touch-target AC list, so excluded here); no real preference-slider *wiring* (Story 1.9 wires it - 1.1 only builds the control and captures its raw value locally); no Heritage topic pill (stale in the mockup - dropped per revised FR-3/this story's AC, which names exactly History/Architecture/Public Art + Wild Jaunt).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Fresh load, no stored trip | `localStorage` empty | Starting-point screen shown, no recap chips | N/A |
| Reload mid-setup | Valid `jaunt_active_trip` with `phase:"setting_up"` | Resumes the correct screen with prior values pre-filled | N/A |
| Corrupted/mismatched state | Bad JSON, or `schema_version` != current | Safe reset: treat as fresh, start over, never crash | Caught, logged to console only |
| `localStorage` blocked (private mode) | `setItem`/`getItem` throws | Flow still works in-memory for this session | Caught; no user-facing error |
| Map tap vs named chip | Either sets `starting_point` | Advances immediately to Available Time screen with recap label set | N/A |
| Keyboard-only run-through | Tab/Enter/Space/arrows only, no mouse/touch | Every control (chips, pills, picker, both button types, slider handle) reachable and operable | N/A |
| Choose-Topic page, no topic yet picked | No pill selected | "Start my Jaunt" pill disabled, no topic name in its label | N/A |

</frozen-after-approval>

## Code Map

- `templates/index.html` -- currently one bare map div; needs the Trip Setup screen shells (header/back/recap, map overlay panel, time-picker card, topic content, confirm sheet) added as hidden/shown sections, screen visibility toggled by `app.js`, not by navigation.
- `static/app.js` -- keep `map` init, `loadPlaces()`, and the MapLibre click handler (just extend it to set `starting_point` + advance screens instead of only dropping a marker); this is where the new screen-state machine, AD-2 persistence, and all new control wiring goes.
- `static/style.css` -- currently minimal (`#status`/`#instructions` only); add design tokens (forest `#1E4A3A`, cream `#F6F4EC`, sage `#AFC29A`, surface-muted `#EDEAE2`, ink `#16302A`) and component styles ported from `mockups/flow-01-setup.html`'s CSS (pill = `inline-flex; width:auto`, full-width = `width:100%`; chip/pill `.selected` = forest-fill/cream-text).
- `_bmad-output/planning-artifacts/ux-designs/ux-IBE160-2026-10-02/mockups/flow-01-setup.html` -- source of truth for screen structure, copy, and the 6 Jarrod pose crops (`wave-sm`, `wave-md`, `wave`, `icon`, `walk-lg`, `happy`) with their exact `background-position`/`background-size` values - port the CSS, don't re-derive crops.
- `_bmad-output/planning-artifacts/ux-designs/ux-IBE160-2026-10-02/imports/jaunty-mascot-sheet-v2-eyes-transparent.png` -- copy into `static/` for serving.
- `data/sydney_places.json` (id `heritage/5012123`, lat/lng `-33.89778906, 151.18001972`) and `data/geocode_cache.json` ("King St, Newtown..." `-33.8982025, 151.1783569`) -- real coordinates for 2 of the 3 named-start chips; Camperdown Park has no catalogue entry, use `-33.8905, 151.1795` (real-world park centroid, looked up, not a guess at precision-critical data).
- `planner.py` topic strings (`"history"`, `"architecture"`, `"public_art"`, `"surprise_me"`) -- match exactly; don't invent new slugs.

## Tasks & Acceptance

**Execution:**
- [ ] `static/app.js` -- add `loadActiveTrip()`/`saveActiveTrip()` around a `jaunt_active_trip` key: `{schema_version:1, phase:"setting_up", starting_point:{lat,lng,label}|null, available_minutes:60, topic:null, preference:0.5}`; wrap both in try/catch, treat any failure or shape/version mismatch as "start fresh" -- AD-2's safe-reset rule
- [ ] `static/app.js` -- screen-state machine for the 4 screens + confirm sheet; map click and the 3 named-start `<button>` chips both set `starting_point` and advance to the time screen
- [ ] `templates/index.html` + `static/style.css` -- time screen: wheel-picker UI (30-120, step 5, default 60, `display-time` token on the selected value), "Continue" full-width button
- [ ] `templates/index.html` + `static/style.css` -- topic-at-rest screen: "Choose Topic" (full-width-equivalent primary) and "Wild Jaunt" (equal-weight secondary, `icon` Jarrod crop) as a `flex:1` pair; preference slider control (visual + locally-captured value only)
- [ ] `templates/index.html` + `static/style.css` -- Choose-Topic page: History/Architecture/Public Art pills only (no Heritage), none pre-selected; compact-pill "Start my [Topic] Jaunt" button, disabled until a pill is selected
- [ ] `templates/index.html` + `static/style.css` -- confirm bottom sheet (triggered by Wild Jaunt directly, or by the Choose-Topic pill): `happy` Jarrod, full-width confirm button, "Wait, let me change that" dismiss link back to the triggering screen
- [ ] `static/app.js` -- on confirm-sheet approval: finalize `topic` (`"surprise_me"` for Wild Jaunt) into the active-trip object and show a clearly-labeled temporary stub screen ("Setup complete - [topic], [minutes] min, [lat,lng]") proving end-to-end capture; stub is throwaway, replaced wholesale by Stories 1.4/1.5's real loading/review screens
- [ ] All new interactive elements -- real `<button>`s (not `<div>`s) with `aria-label`s; tab order follows visual order; time picker operable via arrow keys
- [ ] `static/` -- copy the sprite-sheet PNG in; port the 6 Jarrod crop classes verbatim from the mockup's CSS

**Acceptance Criteria:**
- Given a map tap outside the Newtown pilot boundary, when the user taps, then the point is still accepted as a valid start (no rejection) - boundary handling is Story 1.6's job, not this screen's
- Given dynamic-type/larger-text browser settings, when applied to the time value and compact pill labels, then nothing clips or overlaps
- Given keyboard-only navigation, when tabbing through every screen, then every control is reachable, has a real programmatic label, and is operable without a pointer

## Implementation Notes

## Spec Change Log

## Review Triage Log

## Design Notes

AD-2 ("Binds: every ... screen across the multi-step flow (setup, loading, ...)") doesn't enumerate a setup-stage `phase` value alongside its adopted `reviewing`/`walking`/`wrapping_up` - this spec adds `"setting_up"` as the natural, low-risk completion of that already-adopted pattern (AD-2 explicitly says it binds "setup"), not a new architectural decision.

The mockup's starting-point-screen "map" is a static SVG illustration (it's a no-JS visual mockup). The real app already has a working interactive MapLibre map (AD-1) with real catalogue pins - keep that, and layer the mockup's chip panel/Jarrod bubble/header on top of it rather than replacing working functionality with a fake static drawing.

## Verification

**Commands:**
- `python3 -m http.server` or `flask --app app run` -- expected: app serves, Trip Setup flow loads with no console errors
- Manual keyboard-only pass (Tab/Shift+Tab/Enter/Space/arrows, no mouse) across all 4 screens + confirm sheet -- expected: every control reachable and operable
- Browser dev-tools text-size override (e.g. 200%) on the time and Choose-Topic screens -- expected: no clipped/overlapping labels

**Manual checks (if no CLI):**
- Visually confirm compact-pill buttons never stretch full-width and vice versa, at actual rendered size
- Confirm Jarrod crops render as the correct pose in each of the 6 locations, pixel-aligned (no stretching/distortion)
