---
title: 'Trip Setup inputs - starting point, time, and topic'
type: 'feature'
created: '2026-10-20'
status: 'review'
route: 'dispatch'
review_loop_iteration: 1
context: []
baseline_commit: '66938e50102ec6e3621cb82b886d7e5c328356ab'
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
- [x] `static/app.js` -- add `loadActiveTrip()`/`saveActiveTrip()` around a `jaunt_active_trip` key: `{schema_version:1, phase:"setting_up", setup_step:"starting_point", starting_point:{lat,lng,label}|null, available_minutes:60, topic:null, preference:0.5}`, where `setup_step` is one of `"starting_point"|"available_time"|"topic_at_rest"|"choose_topic"|"confirm_sheet"` and is updated on every screen transition. `loadActiveTrip()`: bad JSON or `schema_version` mismatch -> safe reset (fresh state, per AD-2). `saveActiveTrip()`: wrap only the write in try/catch -- a thrown `setItem` leaves the in-memory state exactly as it was and simply skips persisting; it must never trigger a reset
- [x] `static/app.js` -- screen-state machine for the 4 screens + confirm sheet; map click and the 3 named-start `<button>` chips both set `starting_point` and advance to the time screen
- [x] `templates/index.html` + `static/style.css` -- time screen: wheel-picker UI (30-120, step 5, default 60, `display-time` token on the selected value), "Continue" full-width button
- [x] `templates/index.html` + `static/style.css` -- topic-at-rest screen: "Choose Topic" (full-width-equivalent primary) and "Wild Jaunt" (equal-weight secondary, `icon` Jarrod crop) as a `flex:1` pair; preference slider control (visual + locally-captured value only)
- [x] `templates/index.html` + `static/style.css` -- Choose-Topic page: History/Architecture/Public Art pills only (no Heritage), none pre-selected; compact-pill "Start my [Topic] Jaunt" button, disabled until a pill is selected
- [x] `templates/index.html` + `static/style.css` -- confirm bottom sheet (triggered by Wild Jaunt directly, or by the Choose-Topic pill): `happy` Jarrod, full-width confirm button, "Wait, let me change that" dismiss link back to the triggering screen
- [x] `static/app.js` -- on confirm-sheet approval: finalize `topic` (`"surprise_me"` for Wild Jaunt) into the active-trip object and show a clearly-labeled temporary stub screen ("Setup complete - [topic], [minutes] min, [lat,lng]") proving end-to-end capture; stub is throwaway, replaced wholesale by Stories 1.4/1.5's real loading/review screens
- [x] Accessibility semantics by control type, not one blanket rule: discrete actions (chips, pills, Choose Topic/Wild Jaunt/Continue/confirm/dismiss) are real `<button>`s with `aria-label`s; the time picker and preference slider are native `<input type="range">` elements (or an equivalent ARIA `role="slider"` if a custom look is needed) so value, min/max, and step are programmatically exposed, not buttons. Topic/named-start pills expose their selected state via `aria-pressed` (or `aria-checked` in a `role="radiogroup"`), not color alone. Tab order follows visual order. The confirm bottom sheet moves focus to itself on open and returns focus to the control that opened it on dismiss or confirm (no focus left on a hidden element)
- [x] `static/` -- copy the sprite-sheet PNG in; port the 6 Jarrod crop classes verbatim from the mockup's CSS

**Acceptance Criteria:**
- Given a map tap outside the Newtown pilot boundary, when the user taps, then the point is still accepted as a valid start (no rejection) - boundary handling is Story 1.6's job, not this screen's
- Given dynamic-type/larger-text browser settings, when applied to the time value and compact pill labels, then nothing clips or overlaps
- Given keyboard-only navigation, when tabbing through every screen, then every control is reachable, has a real programmatic label, and is operable without a pointer

## Implementation Notes

**Files changed:** `templates/index.html` (full rewrite - added the 4 setup screens + confirm sheet + stub as hidden/shown sections, kept `#map`/`#status`/`#instructions` wrapped in a new `#map-stage`), `static/style.css` (full rewrite - design tokens, shared screen chrome, Jarrod crop classes ported verbatim from the mockup, chip/pill/button/slider components, confirm sheet), `static/app.js` (full rewrite - kept `map` init/`loadPlaces()`/catalogue marker rendering unchanged, added the active-trip persistence layer and the full screen-state machine), `static/jaunty-mascot-sheet-v2-eyes-transparent.png` (new, copied in from the UX imports folder).

**Design calls made where the spec left room:**
- The map-tap start point has no catalogue match, so its recap label is the literal string `"Dropped pin"` (not invented precision data, just a plain label).
- The confirm sheet's origin screen (needed to know where "Wait, let me change that" and reload-mid-sheet should return to) isn't a separate schema field - it's derived from `trip.topic`: `"surprise_me"` -> topic-at-rest, any named topic -> Choose Topic. This is exact and lossless given the two paths that can open the sheet, so no extra persisted field was needed.
- `loadActiveTrip()` does basic shape validation beyond just `schema_version` (step is a known value, `starting_point` present whenever a later step requires it, topic is one of the four valid slugs, minutes/preference in range) per architecture AD-2's own text ("a payload that fails basic shape validation... triggers a safe reset"), not just a schema-version-number check.
- The time picker is a native `<input type="range">` with a large `display-time` numeral above it, not a literal scrolling wheel-of-numbers widget - the spec's own accessibility correction (native range/slider semantics, not buttons) takes precedence over the mockup's purely-visual wheel per the Code Map's explicit mockup-precedence note, and a real snapping wheel widget with equivalent native semantics would have been meaningfully more complex for no behavioral difference.
- The preference control appears on both the topic-at-rest and Choose-Topic screens as two separate `<input type="range">` elements kept in sync (both read/write the same `trip.preference` value) - matching the mockup's "repeats on the Choose-Topic page for visibility" note in EXPERIENCE.md's Component Patterns table.
- Confirm-sheet background isolation uses the standard `inert` attribute on the host screen (removes it from tab order and the accessibility tree while the sheet is open, restored on dismiss/confirm) rather than manual tabindex juggling - verified working for both mouse and real keyboard Tab navigation.

**Bugs found and fixed during verification (not left in):** the `hidden` attribute wasn't actually hiding the four full-screen panels, because `.setup-screen--full { display: flex; }` (an author rule) silently out-prioritized the browser's default `[hidden]{display:none}` rule at equal specificity - added explicit `.setup-screen--full[hidden] { display: none; }`. The Wild Jaunt confirm sheet read "Ready for your Wild Jaunt Jaunt?" (the word "Jaunt" doubled) - fixed the copy-generation helper to special-case the already-complete "Wild Jaunt" phrase instead of always appending "Jaunt" to a topic label.

**Verified:** `flask --app app run` serves the page with no console errors; a scripted Playwright pass covered named-chip and map-tap starts, keyboard-only Tab/arrow operation of both range inputs, reload-resume on each of the 5 `setup_step` values (including a reload mid-confirm-sheet, which correctly re-derives the origin screen and reopens the sheet), back-button and dismiss-link navigation (both correctly restore focus to the exact triggering control and keep later-step values intact), a blocked-`localStorage` run (flow completes in-memory, no reset, no thrown error), and corrupted-JSON recovery (safe reset to a fresh trip). Touch targets (chips, pills, both button types, both range-input thumbs) are sized to a real 44px via CSS, not just padding.

**Left incomplete / out of scope (by design, not an oversight):** no "use my current location" button (Story 1.10); no real preference-slider or current-location wiring into route selection (Stories 1.9/1.10); the stub completion screen is intentionally throwaway and does not persist a dedicated reload state of its own beyond the last-saved `confirm_sheet` step, since Stories 1.4/1.5 replace it wholesale. No automated test suite exists for this project yet (no pytest/JS test runner configured) - verification was the manual/CLI checks this spec's own Verification section calls for, plus the scripted browser pass described above; a durable automated regression test for this flow is not yet in place.

**2026-10-20, real-device user testing round.** The user tested the implementation directly and found several concrete deviations from DESIGN.md/EXPERIENCE.md that the prior verification pass missed (it checked behavior and touch-target *presence* but never diffed exact CSS values against DESIGN.md's component tokens). Verified and fixed, each against the actual DESIGN.md prose (which the file itself says "wins on conflict" with the mockup CSS):
- **Preference-slider handle was 44px, not the spec's 18px** (DESIGN.md Components: "a circular forest-filled handle (18px)"). The touch-target AC was satisfied by over-correcting the *visual* size instead of giving the input a generous invisible hit-zone while rendering the handle at spec size - these are not the same thing. Fixed: thumb now renders at 18px; the input element itself stays a 44px-tall absolutely-positioned hit zone (tapping/dragging anywhere along a native range track moves the thumb, so the vertical click zone doesn't need to visually match the dot).
- **Thumb and track were vertically misaligned by 9px** ("the round button is off-centre and behind the line"). Root cause: `.pref-track-wrap` used `display:flex; align-items:center` to center the input, but `padding-top:18px` shrank the flex content-box the centering math used, while the decorative `.pref-track` line centered against the *full* box via `top:50%`. The two centered on different boxes. Fixed by making the input `position:absolute; top:50%` exactly like the track, so both share one centering line - confirmed by measuring `getBoundingClientRect()` before (9px offset) and after (0px offset).
- **"Balanced" tag was static** (always visible, fixed at 50%, floating above the track) instead of tracking proximity to center and sitting below the track. The user gave explicit new direction here (not previously specified in DESIGN.md, which only says it "centers itself above the handle at its default position" - doesn't by itself establish disappear-when-off-center behavior): show only within a small deadzone around Balanced, positioned in the `.pref-labels` row (CSS Grid, `1fr auto 1fr`, so it sits at the row's true center regardless of "Well-known" vs "Hidden gems" being different widths), hidden otherwise. Implemented and confirmed via `input` events at value 50 (visible) and 90 (hidden).
- **Compact-pill button radius was 18px, not DESIGN.md's 28px** (`{rounded.full}`) - inherited from the mockup's own CSS, which DESIGN.md explicitly flags as not authoritative on this exact point ("this file's prose wins on conflict"). Fixed.
- **Full-width button padding/font-size didn't match DESIGN.md** ("13-14px vertical, 8px horizontal"; button text role is 13px/700) - was 14px 16px / 14px. Fixed to 14px 8px / 13px.
- **label-caps text was 11px instead of DESIGN.md's 10.5px**, and the Well-known/Hidden-gems end labels were 11px instead of the spec's 10px. Fixed across `.panel-label`, `.pref-caption`, `.scroller-label`, `.pref-labels`.
- **Map tap advanced to the next screen immediately**, with no way to see/check the dropped pin first. Not a DESIGN.md deviation (this flow wasn't specified anywhere, mockup included - genuinely unaddressed in planning), but a direct, explicit user correction: added a "Confirm this spot" pill button that appears once a pin is dropped by a map tap; the pin is draggable (re-tappable) before confirming; `trip.starting_point` is only set and the screen only advances once Confirm is tapped. The 3 named-start chips are unchanged (exact known location, no ambiguity to confirm).
- Verified all of the above against real computed `getBoundingClientRect()`/`getComputedStyle()` measurements at a 390px mobile viewport (not just visual inspection), plus a real MapLibre `click` event (fired via `map.fire()`, since synthetic DOM `MouseEvent`s don't reach MapLibre's internal gesture handler) to confirm the new confirm-before-advance flow actually works end to end, not just that the code looks right.
- **Not changed:** the "use my current location" button's absence - this is a genuine scope question (epics.md: "Depends on Story 1.1 (same screen)" for Story 1.10, which owns both the button and its behavior) flagged back to the user rather than silently decided either way. The general "doesn't look designed for mobile" report was investigated: at an actual 390px viewport there's no horizontal overflow and the screens measure correctly; the most likely explanation is the user's desktop test window, where the real full-bleed map (intentionally edge-to-edge, matching DESIGN.md's "map-dominant" pattern) makes the centered ~480px-wide setup content look like a narrow strip in a wide desktop window - not a mobile-width bug, but flagged back for the user to confirm.

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
