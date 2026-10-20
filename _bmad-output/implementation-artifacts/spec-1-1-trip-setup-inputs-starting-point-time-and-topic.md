---
title: 'Trip Setup inputs - starting point, time, and topic'
type: 'feature'
created: '2026-10-20'
status: 'ready-for-dev'
route: 'dispatch'
review_loop_iteration: 1
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
| Reload mid-setup | Valid `jaunt_active_trip` with `phase:"setting_up"` and a `setup_step` | Resumes the exact screen named by `setup_step` (not inferred from which fields are filled), prior values pre-filled | N/A |
| Corrupted/mismatched state on load | Bad JSON, or `schema_version` != current, on `loadActiveTrip()` | Safe reset: treat as fresh, start over, never crash | Caught, logged to console only |
| Save fails mid-setup | `localStorage.setItem` throws (private mode, quota) | Current in-memory values are kept and the flow continues normally; persistence is silently skipped, not treated as corruption | Caught; no reset, no user-facing error |
| Map tap vs named chip | Either sets `starting_point` | Advances immediately to Available Time screen with recap label set | N/A |
| Keyboard-only run-through | Tab/Enter/Space/arrows only, no mouse/touch | Every control (chips, pills, picker, both button types, slider handle) reachable and operable | N/A |
| Choose-Topic page, no topic yet picked | No pill selected | "Start my Jaunt" pill disabled, no topic name in its label | N/A |
| Back / confirm-sheet dismissal | "‹" back on any screen, or "Wait, let me change that" | `setup_step` moves back one screen (back) or returns to the exact screen that opened the sheet (dismiss); already-entered values for later steps are kept, not cleared; focus returns to the control that triggered navigation | N/A |

</frozen-after-approval>

## Code Map

- `templates/index.html` -- currently one bare map div; needs the Trip Setup screen shells (header/back/recap, map overlay panel, time-picker card, topic content, confirm sheet) added as hidden/shown sections, screen visibility toggled by `app.js`, not by navigation.
- `static/app.js` -- keep `map` init, `loadPlaces()`, and the MapLibre click handler (just extend it to set `starting_point` + advance screens instead of only dropping a marker); this is where the new screen-state machine, AD-2 persistence, and all new control wiring goes.
- `static/style.css` -- currently minimal (`#status`/`#instructions` only); add design tokens (forest `#1E4A3A`, cream `#F6F4EC`, sage `#AFC29A`, surface-muted `#EDEAE2`, ink `#16302A`) and component styles ported from `mockups/flow-01-setup.html`'s CSS (pill = `inline-flex; width:auto`, full-width = `width:100%`; chip/pill `.selected` = forest-fill/cream-text).
- `_bmad-output/planning-artifacts/ux-designs/ux-IBE160-2026-10-02/mockups/flow-01-setup.html` -- source of truth for **visual reference only**: screen layout, copy strings, and the 6 Jarrod pose crops (`wave-sm`, `wave-md`, `wave`, `icon`, `walk-lg`, `happy`) with their exact `background-position`/`background-size` values - port the CSS, don't re-derive crops. **Precedence when the mockup conflicts with current requirements:** the final epics.md AC and the architecture spine govern actual behavior; this mockup is a point-in-time snapshot (it still shows a 4th "Heritage" pill and a current-location button this story excludes - see Boundaries). Treat any further mockup detail not confirmed by epics.md/the architecture spine as a visual suggestion, not a requirement.
- `_bmad-output/planning-artifacts/ux-designs/ux-IBE160-2026-10-02/imports/jaunty-mascot-sheet-v2-eyes-transparent.png` -- copy into `static/` for serving.
- `data/sydney_places.json` (id `heritage/5012123`, lat/lng `-33.89778906, 151.18001972`) and `data/geocode_cache.json` ("King St, Newtown..." `-33.8982025, 151.1783569`) -- real coordinates for 2 of the 3 named-start chips; Camperdown Park has no catalogue entry, use `-33.8905, 151.1795` (real-world park centroid, looked up, not a guess at precision-critical data).
- `planner.py` topic strings (`"history"`, `"architecture"`, `"public_art"`, `"surprise_me"`) -- match exactly; don't invent new slugs.

## Tasks & Acceptance

**Execution:**
- [ ] `static/app.js` -- add `loadActiveTrip()`/`saveActiveTrip()` around a `jaunt_active_trip` key: `{schema_version:1, phase:"setting_up", setup_step:"starting_point", starting_point:{lat,lng,label}|null, available_minutes:60, topic:null, preference:0.5}`, where `setup_step` is one of `"starting_point"|"available_time"|"topic_at_rest"|"choose_topic"|"confirm_sheet"` and is updated on every screen transition. `loadActiveTrip()`: bad JSON or `schema_version` mismatch -> safe reset (fresh state, per AD-2). `saveActiveTrip()`: wrap only the write in try/catch -- a thrown `setItem` leaves the in-memory state exactly as it was and simply skips persisting; it must never trigger a reset
- [ ] `static/app.js` -- screen-state machine for the 4 screens + confirm sheet; map click and the 3 named-start `<button>` chips both set `starting_point` and advance to the time screen
- [ ] `templates/index.html` + `static/style.css` -- time screen: wheel-picker UI (30-120, step 5, default 60, `display-time` token on the selected value), "Continue" full-width button
- [ ] `templates/index.html` + `static/style.css` -- topic-at-rest screen: "Choose Topic" (full-width-equivalent primary) and "Wild Jaunt" (equal-weight secondary, `icon` Jarrod crop) as a `flex:1` pair; preference slider control (visual + locally-captured value only)
- [ ] `templates/index.html` + `static/style.css` -- Choose-Topic page: History/Architecture/Public Art pills only (no Heritage), none pre-selected; compact-pill "Start my [Topic] Jaunt" button, disabled until a pill is selected
- [ ] `templates/index.html` + `static/style.css` -- confirm bottom sheet (triggered by Wild Jaunt directly, or by the Choose-Topic pill): `happy` Jarrod, full-width confirm button, "Wait, let me change that" dismiss link back to the triggering screen
- [ ] `static/app.js` -- on confirm-sheet approval: finalize `topic` (`"surprise_me"` for Wild Jaunt) into the active-trip object and show a clearly-labeled temporary stub screen ("Setup complete - [topic], [minutes] min, [lat,lng]") proving end-to-end capture; stub is throwaway, replaced wholesale by Stories 1.4/1.5's real loading/review screens
- [ ] Accessibility semantics by control type, not one blanket rule: discrete actions (chips, pills, Choose Topic/Wild Jaunt/Continue/confirm/dismiss) are real `<button>`s with `aria-label`s; the time picker and preference slider are native `<input type="range">` elements (or an equivalent ARIA `role="slider"` if a custom look is needed) so value, min/max, and step are programmatically exposed, not buttons. Topic/named-start pills expose their selected state via `aria-pressed` (or `aria-checked` in a `role="radiogroup"`), not color alone. Tab order follows visual order. The confirm bottom sheet moves focus to itself on open and returns focus to the control that opened it on dismiss or confirm (no focus left on a hidden element)
- [ ] `static/` -- copy the sprite-sheet PNG in; port the 6 Jarrod crop classes verbatim from the mockup's CSS

**Acceptance Criteria:**
- Given a map tap outside the Newtown pilot boundary, when the user taps, then the point is still accepted as a valid start (no rejection) - boundary handling is Story 1.6's job, not this screen's
- Given dynamic-type/larger-text browser settings, when applied to the time value and compact pill labels, then nothing clips or overlaps
- Given keyboard-only navigation, when tabbing through every screen, then every control is reachable, has a real programmatic label, and is operable without a pointer

## Implementation Notes

## Spec Change Log

- **2026-10-20, Codex review (pre-implementation, iteration 1).** Findings and amendments:
  1. *Finding:* no field distinguished which of the 5 setup screens a reload should resume. *Amended:* added `setup_step` to the active-trip object (I/O Matrix, Tasks). *Avoids:* reload landing on the wrong screen, or inferring the step wrongly from which input fields happen to be filled.
  2. *Finding:* the edge-case matrix promised in-memory continuation on a blocked `localStorage`, while the execution task said any failure (including a save failure) triggers a full reset - a real contradiction that would erase the user's live inputs under exactly the blocked-storage condition the matrix was trying to protect. *Amended:* split load-time failure (bad JSON/version -> reset) from save-time failure (keep in-memory state, skip persistence silently) in both the matrix and the task. *Avoids:* wiping a user's in-progress setup every screen transition under private-mode/blocked storage.
  3. *Finding:* the Code Map called the mockup "source of truth" without qualifying that current requirements override it, inviting further stale mockup detail (beyond the already-caught Heritage pill and current-location button) to creep in uncaught. *Amended:* added an explicit precedence statement. *Avoids:* a developer trusting an unflagged stale mockup detail over epics.md/the architecture spine.
  4. *Finding:* "all new interactive elements are real buttons" is wrong for the time picker and preference slider (value controls need native range/slider semantics, not button semantics), and topic/start selection relied on color alone rather than a programmatic selected state. *Amended:* split accessibility guidance by control type; added `aria-pressed`/`role="radiogroup"` for selection state and defined confirm-sheet focus entry/return. *Avoids:* a screen reader being unable to perceive the picker's value or which topic is selected.
  5. *Finding:* `python3 -m http.server` was offered as an alternative verification command but cannot render this Flask app's Jinja templates or serve `/api/places` at all. *Amended:* removed it, kept only the Flask run command; added reload-per-step, blocked-storage, back/dismiss-navigation, and an explicit 44x44pt touch-target measurement to the manual checks (the AC already required the last one; Verification hadn't made it concrete).
  - *Not amended (out of this story's scope, tracked for Story 1.3 instead):* Codex's points on AD-3's rule-based grounding check needing real supported/unsupported validation examples, the source-gathering contract needing stable source identity + a place-specific/general-context distinction + a size bound before real retrieval lands, and batched-generation latency/partial-failure handling needing real measurement rather than extrapolation from `select_stops()`'s timings. These concern Story 1.3 (AI content generation) and AD-3, not Story 1.1's setup screens, which have no AI/content-generation code at all.

## Review Triage Log

## Design Notes

AD-2 ("Binds: every ... screen across the multi-step flow (setup, loading, ...)") doesn't enumerate a setup-stage `phase` value alongside its adopted `reviewing`/`walking`/`wrapping_up` - this spec adds `"setting_up"` as the natural, low-risk completion of that already-adopted pattern (AD-2 explicitly says it binds "setup"), not a new architectural decision.

The mockup's starting-point-screen "map" is a static SVG illustration (it's a no-JS visual mockup). The real app already has a working interactive MapLibre map (AD-1) with real catalogue pins - keep that, and layer the mockup's chip panel/Jarrod bubble/header on top of it rather than replacing working functionality with a fake static drawing.

## Verification

**Commands:**
- `flask --app app run` (serves real Jinja templates and `/api/places` - a bare static file server cannot render this app) -- expected: app serves, Trip Setup flow loads with no console errors

**Manual checks (if no CLI):**
- Keyboard-only pass (Tab/Shift+Tab/Enter/Space/arrows, no mouse) across all 4 screens + confirm sheet -- every control reachable and operable
- Reload the browser on each of the 5 `setup_step` values in turn -- each resumes on the exact same screen with prior values intact
- Block `localStorage` (devtools: disable storage, or private-mode-like throw) and run the full flow -- setup still completes in-memory, no crash, no silent reset mid-flow
- Back button and "Wait, let me change that" from the confirm sheet, at every step -- returns to the correct prior screen with later-step values still intact, focus lands back on the triggering control
- Browser dev-tools text-size override (e.g. 200%) on the time and Choose-Topic screens -- no clipped/overlapping labels
- Visually confirm compact-pill buttons never stretch full-width and vice versa, at actual rendered size
- Confirm Jarrod crops render as the correct pose in each of the 6 locations, pixel-aligned (no stretching/distortion)
- Measure every tappable control (chips, pills, slider handle, compact/full-width buttons) against a real ~44x44pt rendered size, not just its CSS padding values
