---
stepsCompleted: [1, 2, 3]
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-IBE160-2026-09-29/prd.md
  - _bmad-output/planning-artifacts/prds/prd-IBE160-2026-09-29/addendum.md
  - _bmad-output/planning-artifacts/architecture/architecture-IBE160-2026-10-07/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/ux-designs/ux-IBE160-2026-10-02/DESIGN.md
  - _bmad-output/planning-artifacts/ux-designs/ux-IBE160-2026-10-02/EXPERIENCE.md
  - docs/architecture-plan.md
  - docs/product-brief.md
---

# Jaunt - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Jaunt, decomposing the requirements from the PRD, UX Design spine pair, and Architecture spine into implementable stories.

## Requirements Inventory

### Functional Requirements

FR-1: User selects a starting point by tapping the map or choosing from predefined named starts; any tapped point is accepted regardless of the Pilot Area's catalogue boundary - revised 2026-10-18 after confirming no runtime boundary check exists in the code; a start too far from any real Stop is naturally handled by the existing honest-fallback mechanism (FR-9), not a separate rejection. (Must)
FR-2: User sets total available time, 30-120 minutes; the Planner never proposes a Route whose Dwell-Time-inclusive total exceeds it. (Must)
FR-3: User selects one Topic (history, architecture, public art) or "surprise me"; surprise-me keeps candidates across all Topics rather than filtering to one. Revised 2026-10-18: heritage dropped as a user-facing Topic (a legal/administrative designation, not a subject to walk for) - its records are retagged into history/architecture instead (see Epic 1 Story 1.2, promoted to Must). (Must)
FR-4: User can express a landmark <-> lesser-known preference that influences stop selection without excluding genuinely interesting "hidden gem" stops. (Should)
FR-5: System generates a feasible, time-bounded Route (minimum 2 stops, no fixed maximum - revised 2026-10-18, see Additional Requirements; all Record Status `ready`) from start point, time, and topic via the existing Planner + AI selection pipeline. (Must)
FR-6: The Route and its Stops are shown on the map with an expandable stop list and the estimated total time; full walking-path display depends on route-geometry work not yet built. (Must)
FR-7: User can open each Stop's AI-generated content and its source before deciding whether to approve the Route. (Must)
FR-8: User must take an explicit approval action before a Route becomes an active walk. (Must)
FR-9: When no feasible/relevant Route can be built, the system says so plainly, explains why, and always offers a way back - never a weak Route or a dead end; a suggested time adjustment always offers more time, never less; a technical/service failure is distinguished from an honest "no suitable walk" result. (Must)
FR-10: User can request a new proposed Route (Re-Jaunt) using the same inputs; returns a different Route when a feasible alternative exists in the Option Menu, else falls back to FR-9. (Should)
FR-11: Before approving, user can remove or replace an individual Stop; this re-validates the Route's time feasibility before it can be approved again. (Should)
FR-12: Each approved Stop's content remains available during the walk; opening it is always optional and never nagged. (Must)
FR-13: User can explicitly affirm they were physically at a Stop, only actionable during an active walk - distinct from, and never satisfied merely by, opening its content. (Should)
FR-14: User's current position is shown on the map during an active walk, subject to explicit, revocable permission; never requested/shown silently; no position data sent to or stored on a server. (Should)
FR-15: When live position is near an unvisited Stop, user receives a prompt inviting them to open its content; only fires when FR-14 is active and permitted. (Could, depends on FR-14)
FR-16: After finishing, user receives a short AI-generated summary grounded strictly in Stops marked Visited/Completed - never Proposed or merely Opened/Engaged stops; zero Visited stops produces no summary or an honest message. (Should)
FR-17: User's Visit History (per-Stop Engagement State: Proposed / Opened-Engaged / Visited-Completed) and Favourites are stored locally without an account; the four Engagement States are stored distinctly, never collapsed to one "seen" flag. (Should)
FR-18: Future Route generation varies Stop selection based on Engagement State (stronger engagement -> stronger deprioritization), while Favourites are never excluded by that rule. (Should)
FR-19: AI-generated Stop content and walk summaries are grounded in a Stop's Source Excerpt, a Contextual Source, or both; requires BOTH an automated grounding check (with a defined fallback on failure) AND continued manual spot-checking - neither layer alone is sufficient. (Must)
FR-20: Each Stop's content is shown alongside a reference to where it came from (Wikipedia, OSM tags, council dataset, NSW Heritage); required attribution for OSM, the routing provider, Wikipedia, NSW Heritage, and Inner West Council appears somewhere in the UI. (Must)
FR-21: A small refactor moves Newtown/English-specific hard-coded values into configuration, then the import pipeline is pointed at a second Sydney-area bounding box to produce a working, demonstrable Catalogue, without modifying planner.py/ai.py/the frontend. (Should, explicit stretch goal - never allowed to delay the Newtown end-to-end flow)
FR-22: A Stop's content/list display may include a photo only when sourced from material the user has confirmed rights to use; a Stop without a qualifying image simply has no photo, never a placeholder. (Should)
FR-23: When zoomed in sufficiently, the map shows nearby general points of interest as a muted, secondary, display-only reference layer, always visually subordinate to the Route/Stops and never fed into the Planner or AI selection. (Should)
FR-24: Alongside map-tap and named starts, user can tap "use my current location" for a one-time, explicit-permission geolocation request; a denied/failed request falls back cleanly to map-tap/named starts. (Should)

### NonFunctional Requirements

NFR-1 (Privacy - no account): No account creation or login is required for any V1 feature, including Favourites and Visit History.
NFR-2 (Privacy - local-only in V1, revised 2026-10-07): Visit History, Favourites, and mark-visited state are stored locally on the device for V1; nothing is persisted server-side in V1; a planning request may transmit the minimal signal needed for that one computation (same transient posture as the one-shot location coordinate). This is a V1 implementation fact, not a permanent promise - it does not foreclose a future server-side account system.
NFR-3 (Privacy - live position): The continuous GPS stream during a walk is never transmitted to or stored on a server - it only drives the client's own map display; a one-shot "use my current location" coordinate is, by design, sent to the routing/planning service, same as any other chosen starting coordinate.
NFR-4 (Source integrity): AI never originates a Stop's existence - only the verified catalogue does; AI never generates content without grounding; both an automated grounding check and manual spot-checking are required, not either alone.
NFR-5 (Extensibility): Language and Pilot Area boundary must be kept as configuration, not inline literals, so a second area or language is additive, not a rewrite - an architectural posture for V1, not a commitment to build it now. Served by Epic 4 Story 4.1 (promoted to Must-tier 2026-10-20 - this is a V1 codebase property, not contingent on Story 4.2's optional second-area demonstration).
NFR-6 (Platform): Mobile-first web app, phone browser primary, desktop secondary; built and tested mobile-first from the start, not retrofitted.
NFR-7 (Reliability/regression): The existing automated test suite (169/169 passing as of 2026-10-07) must continue passing as V1 features are added; new Must/Should features get their own tests.

### Additional Requirements

(From ARCHITECTURE-SPINE.md - architecture-IBE160-2026-10-07, binding decisions AD-1 through AD-6, plus required code changes and confirmed defects)

- No starter template applies - this is a brownfield project; the existing Flask (Python) backend + vanilla-JS/MapLibre frontend stack is retained as-is.
- AD-1: Map rendering uses MapLibre GL JS pinned to 5.6.1 (not @latest - v6 drops the plain-script-tag bundle this buildless project relies on), base style OpenFreeMap `positron` (free, no API key, no request limit) - base layer already implemented and user-verified. Many-of-a-kind, data-driven map features (route line, background amenity points FR-23, park fills, numbered stop circles with no photo) must render as GeoJSON sources + MapLibre paint layers, never individual DOM markers. One-off features needing real image content (the live-position marker - a crop of Jarrod's head; a rights-cleared photo stop pin) use `maplibregl.Marker({element})`, the same pattern the existing start-point marker already uses. Every stop-related map feature carries the same place `id` as its addressable key regardless of rendering mechanism. The existing catalogue-pin loop (one DOM marker per place) is known, accepted non-compliant scaffolding ported 1:1 from Leaflet - not required to change retroactively.
- AD-2: Backend is fully stateless - one planning request returns the complete route+stops+content; follow-up actions (replace a stop, mark visited) are separate stateless requests. The frontend persists the active trip to its own `localStorage` key; an explicit "end trip" action clears it, but only once the end-of-walk catch-up/summary wrap-up sequence actually finishes (or the user returns to setup) - never at the initial "End Jaunt" tap, so a refresh mid-wrap-up still recovers. The Visited control (FR-13) must be context-gated: disabled/hidden outside an active walk, since the same stop-info overlay is also shown during pre-walk preview (FR-7).
- AD-3: AI content generation for every stop in the chosen route runs synchronously at plan time (not lazily per stop), so the whole trip payload is complete and cacheable before the walk starts. Each stop in that payload carries its own `id`, order position, generated `content`, and a structured attribution reference (`source_type`/`source_title`/`source_url`) - never a flat content string with no attribution field (FR-20). A per-stop grounding-check failure (FR-19) falls back to that stop's raw `source_excerpt` rather than discarding the whole otherwise-feasible route.
- AD-4: The FR-4 preference value passes directly into AI's existing selection prompt as a single continuous numeric value (matching the mock's slider, not a 3-value enum) - no new Python-computed "prominence" heuristic. Required code change, not yet true: `planner.py`'s `_build_ai_options()` currently sends only `id`/`name`/`topics`/`source_excerpt` to AI - `source_type` and `source_title` must be added to that payload for AI to have anything to judge "well-known-ness" from.
- AD-5: `planner.py`'s selection path needs an `excluded_ids` parameter - a hard filter, session-local to the current trip (lives in the active-trip `localStorage` object, cleared by end-trip). Replacing a stop or Re-Jaunting re-runs with the rejected stop(s) excluded, re-validating feasibility before re-approval (FR-11). Since the backend is stateless, the frontend resends the full accumulated `excluded_ids` list every call, never a delta. Deliberate, accepted trade-off: Re-Jaunt excludes every stop of the rejected route (not just that specific combination), which is stricter than FR-10's literal wording requires but is an intentional "clean break" design choice, not a gap.
- AD-6: Visit history/favourites live in a `localStorage` key SEPARATE from the active trip (AD-2), so "end trip" never touches it. Schema: a list of `{id, state, favourited}` where `state` is one of `proposed`/`opened_engaged`/`visited_completed` (the three ordinal Engagement States; `favourited` is an independent boolean) - never collapsed to a single flag (FR-17). Sent with the planning request as a transient, soft AI-weighting signal only (never a hard filter - a favourite can always resurface, per EXPERIENCE.md); nothing is stored server-side in V1 (NFR-2).
- Required code change, not yet built: `planner.py`'s `plan_route()` currently returns the identical `{"feasible": false, "reason": ...}` shape for a genuine `ai.AiFatalError` (invalid credentials, exhausted quota) as it does for ordinary infeasibility. Before the planning endpoint is built, it must stop swallowing fatal AI/service failures into that shape - re-raise them (mirroring `app.py`'s existing `CatalogueError` pattern) so the endpoint can map them to a real non-2xx status without parsing free-text `reason` (needed for FR-9's "technical failure vs. honest no-route" distinction).
- FR-19's automated grounding-check mechanism is new, substantial, unbuilt logic - NOT a small extension of `ai.py`'s existing `select_stops()` validation, which only checks that JSON parses and the chosen key was actually offered (pure structural validation, no ability to judge whether prose is supported by source text). Recommended as an early Must-tier prototype task with real supported/unsupported examples and documented limitations, applied to walk summaries (FR-16) too, not just per-stop content.
- Route-geometry fetch (FR-6, Sprint 8) needs a new function in `services.py` alongside the existing `fetch_duration_matrix()`, following the same ORS-auth pattern.
- Confirmed, already-fixed code defects (2026-10-07, kept here for traceability): `ai.py`'s `select_stops()` raised an uncaught `TypeError` on a `choices: null` OpenAI response envelope (fixed, regression test added); `static/app.js`'s map rotation/pitch gestures were still live by default despite a comment claiming otherwise (fixed via `dragRotate: false`, `touchZoomRotate.disableRotation()`, `keyboard.disable()`), and there was no `map.on('error', ...)` handler for a failed style load (fixed).
- Logging strategy is not addressed anywhere in the architecture - a real, open gap, not a settled "none needed."
- Catalogue topic-coverage gap (confirmed via direct query, 2026-10-07): exactly 1 ready `history` stop and 1 ready `architecture` stop exist against the Planner's 2-stop minimum - those two Topics cannot produce any Route today. PRD Open Question 18's approved fix, revised 2026-10-18: AI reads each of the 29 ready Heritage records' Statement of Significance and assigns Topics (history/architecture) only where the source text actually supports it, with a human-reviewed approval pass before storing - not a blanket re-tagging shortcut, and no Planner changes needed. This now REPLACES each record's heritage tag rather than adding to it, since heritage is dropped as a user-facing Topic entirely (FR-3) - a heritage listing is a legal/administrative designation, not a subject someone walks for. `import_heritage.py` keeps importing from the heritage register as a catalogue source; only the user-facing Topic list changes.
- Deployment is local-only for V1 (`python3 app.py`) - no hosting/infra provider needed.
- No start-point geofencing (2026-10-18, checked against the real code): `planner.py` has no runtime Pilot Area boundary check - `import_places.py`'s `PILOT_BBOX` is import-time only. FR-1's Trip Setup story does not need to build one; a start point far from any real Stop is already handled by the existing `len(shortlist) < MIN_STOPS` honest-fallback path.
- Dynamic stop-count ceiling (2026-10-18, FR-5): `planner.py`'s fixed `MAX_STOPS=5` is replaced by `ABSOLUTE_MAX_STOPS=7` (a measured safety ceiling, not a target) plus a new `max_stops_for_request(requested_minutes, dwell_minutes_per_stop)` helper computing `min(7, requested_minutes // dwell_minutes_per_stop)` per request. Brute-force ordering cost was measured directly, not assumed: ~0.06s/0.45s/2.9s at 5/6/7 stops against a 12-candidate shortlist - 8+ stops would need a real ordering-heuristic change, out of scope here.

### UX Design Requirements

(From DESIGN.md + EXPERIENCE.md, ux-IBE160-2026-10-02, both status: final)

UX-DR1: Implement the full color token set (20 tokens: forest, sage, sage-light, cream, paper, ink, ink-soft, ink-faint, surface, surface-muted, sheet-handle, road, road-main, building-light, building-dark, tree-dark, tree-light, water, house-wall, logo-field) exactly per DESIGN.md's frontmatter - no invented colors, no dark-mode variant (none exists), no error/destructive color (none has been established; failure states use Jarrod's sad pose + plain text, never a red/alert treatment).
UX-DR2: Implement the 8 typography roles (display-time 27px/800, heading 15px/700, bubble 13.5px/700, stop-name 12.5px/700, stop-name-detail 17px/700, body 12.5px/400, label-caps 10.5px/700 uppercase, button 13px/700, caption 11px/600) using only the native system-font stack - no custom typeface.
UX-DR3: Implement the 8-step corner-radius scale (xs 9px, sm 11px, DEFAULT 14px, md 16px, lg 18px, xl 22px, 2xl 24px, full 28px) mapped to components exactly per DESIGN.md's Shapes section; the map itself is the one deliberate exception (flat, unrounded geometry).
UX-DR4: Primary button (full-width) component - forest fill, cream text, used only when exactly one dominant action exists on a screen.
UX-DR5: Compact pill button (auto-width) component - visually and structurally distinct from the primary button (inline-flex, width:auto, rounded-full). This exact distinction has caused the single most-repeated bug in this project (a short-label button inheriting full-width/flex:1 styling) - treat as two genuinely separate components, never interchangeable variants, and specifically test "Start my [Topic] Jaunt" and "Back to start" for this regression.
UX-DR6: Equal-weight button pair component - two flex:1 buttons, used only for genuinely co-equal choices ("Choose Topic"/"Wild Jaunt"; "Re-Jaunt"/"Start my jaunt"), never for a single short-label action.
UX-DR7: Chip/pill component (named-start chips, topic pills) - horizontally scrollable with hidden scrollbar; selected state is a fill inversion (forest fill/cream text), never a border or checkmark addition.
UX-DR8: Preference control component (landmark <-> hidden-gem slider, FR-4) - continuous sage track with a forest circular handle, a floating "Balanced" tag at the default center position, "Well-known"/"Hidden gems" end labels. Appears beneath both buttons on the Topic-at-rest screen and repeats on the Choose-Topic page; deliberately absent from the Wild Jaunt path's own confirmation sheet (Wild Jaunt stays a true one-tap action, though the Balanced default still applies to it).
UX-DR9: Small badge/recap pill component - sized to its own content, never stretched; used for the header recap ("Newtown - 60 min"), the route-review time total, and the in-walk "~X min left" pill.
UX-DR10: Speech bubble component - always paired with a Jarrod pose, bold text only, never a standalone tooltip/toast.
UX-DR11: Bottom sheet component - one structural pattern reused for the Route Review stop list, the pre-generation confirmation, and the end-of-walk catch-up list; dismissed by swipe-down. A taller, near-full-screen variant is the stop-info overlay.
UX-DR12 (amended 2026-10-21, user's explicit choice, corrected 2026-10-21 per Codex review - see UX-DR13's own correction note): Stop row (list item) component - a numbered circle marker alongside a small place-type icon, not a photo-thumbnail in the row. A rights-cleared photo (FR-22, Story 1.11), where it exists, shows inside the stop's own content overlay instead, not as a row thumbnail - see UX-DR13.
UX-DR13 (amended 2026-10-21, user's explicit choice - overrides the original "plain circle, never per-stop iconography" decision below; corrected 2026-10-21 per Codex review, which caught that this entry's own first amendment had already gone stale after a second round of user feedback): Map stop marker is a white-plate circle carrying both the order number (restored after the user's follow-up - icons did not end up replacing it) and a small place-type icon on top. The icon is picked by the stop's own name first (a real keyword - "church"/"chapel"/"cathedral", "railway"/"station", "hotel" - checked against the actual catalogue, which has real, common examples of each), falling back to a topic-level icon (architecture->house, history->church, public_art->three colored paint dots) only when no name keyword matches. A rights-cleared photo (FR-22, Story 1.11), where it exists, shows inside the stop's own content overlay when tapped/clicked - "over the text" - not as the map pin itself. Still explicitly rejected, unchanged: Jarrod standing at the stop with a speech bubble as an individual marker. This entry is the live source of truth for marker appearance - EXPERIENCE.md's own marker description and UX-DR19's "forest-filled/sage-ringed" wording below are now superseded by this entry, not the other way around, and have not themselves been rewritten (no need to regenerate the historical mocks that originated them).
UX-DR14: Live position marker (FR-14) - Jarrod's head alone (~30px crop at the real alpha-channel gap between head and torso), never a generic dot and never his full figure. When this layer is absent (GPS off/denied/not attempted), the map shows no marker at all - this is the Must-tier clean-degradation baseline every walk must hit, explicitly not an error state.
UX-DR15: Off-canvas drawer component - full-height white panel from the left (~78% width) over a dimmed scrim, hamburger-triggered. Currently holds only "End Jaunt"; two named Post-V1 rows (weather-rerouting, mid-walk re-route) are reserved but must stay explicitly empty - do not add rows for features that don't exist yet.
UX-DR16: Visited checkbox badge component - bordered square + "Visited" label, floating top-right on the stop-info overlay, visually and interactionally separate from the content below; opening/reading the story never toggles this.
UX-DR17: Catch-up row component - checkbox-style per stop, pre-checked if marked Visited during the walk, tappable to catch up retroactively; a retroactive tap is still an explicit Visited/Completed action, never inferred.
UX-DR18: Jarrod character rendering - every appearance is a real cropped/composited region of the two source PNGs (`jaunty-mascot-sheet-v2-eyes-transparent.png`, `jaunty-sad-transparent.png`) - never hand-drawn, redrawn, or regenerated from a text description (this produced an unrecognizable result twice before the rule was adopted, applies to the shipped app's asset pipeline, not just mocks). Body always solid forest color (non-negotiable); accessories (cap, backpack) may carry other colors. Prominence scales inversely with screen content density: 150-168px on sparse screens down to a 30px head-only marker during active walking.
UX-DR19: Map component visual spec (distinct from Architecture's AD-1 library choice) - forest route line (6.5-7px), sage park fills with a tree-cluster device clipped strictly to real polygon boundaries, muted/low-opacity (0.7) background amenity dots (FR-23) always visually subordinate to the route and stops. Stop markers: see UX-DR13 (amended 2026-10-21) for the current, live design - this entry's own original "forest-filled/sage-ringed stop circles or photo-thumbnail pins" wording is superseded, not current. Base style: `liberty` (changed 2026-10-21 from `positron`, which explicitly strips POI labels - see AD-1), which already ships colored parks/landuse out of the box; exact-palette matching to this entry's park-fill spec is still separate follow-up work.
UX-DR20: Implement the full 12-surface information architecture exactly as sequenced (Launch splash -> Starting point -> Available time -> Topic-at-rest/Choose-Topic page -> Confirmation sheet -> Loading -> Route Review or Honest fallback -> Active walking -> Off-canvas drawer -> Stop info overlay -> End-of-walk catch-up -> Summary or Jaunt-complete) - a single forward-moving funnel, no tab bar, no persistent bottom nav; each sheet/overlay is dismissed before the next appears.
UX-DR21: Apply the Voice & Tone Do/Don't microcopy table - plain, warm, topic-specific copy ("Where are we jaunting from?", "Concocting your jaunt...", "Jarrod was unable to make a 30-minute History Jaunt from here.") - never generic form-field language, progress percentages, or "Error:"/"No results found" framing. The "Jaunt complete"/"Nice walk!" copy is explicitly draft, not locked.
UX-DR22: Touch targets must meet or exceed a ~44x44pt-equivalent size on every tappable control (chips, pills, the Visited checkbox, the remove "X", catch-up rows) - a commitment to test against, not yet measured.
UX-DR23: Run an actual WCAG contrast check on the ink-on-cream/surface text pairing before shipping - not yet calculated or tested anywhere in this project.
UX-DR24: Every state must be signaled by more than color alone - selected chips keep a readable label (not color-only), the Visited badge pairs a shape with the word "Visited," no failure state relies on color (no error color exists in the system).
UX-DR25: Add a visible, tappable close control alongside swipe-down-to-dismiss on every sheet/overlay - currently a real, flagged gap (only the Must-tier skeleton's stop overlay has an explicit "X"; every other sheet relies on a text hint alone).
UX-DR26: Verify the two location-permission moments (FR-24 one-shot, FR-14 continuous) actually present accessibly via the browser's native dialog - not yet separately verified for this product.
UX-DR27: Test dynamic type/text scaling against tightly-sized short-text labels (the time pill, compact pills) before treating current sizing as settled.
UX-DR28: Enforce the interaction-primitive rules - tap as the universal primary action; horizontal swipe/scroll on chip/pill rows; vertical swipe/scroll on the time wheel-picker (5-minute increments); swipe-down-to-dismiss on every sheet; stop removal is a direct tap on its own "X," never swipe-to-delete; marking Visited, approving a Route, and favouriting a stop are each their own explicit affirmative tap, never inferred from another action.
UX-DR29: Enforce the "never happens by deliberate decision" list as negative acceptance criteria: opening a stop's content never auto-marks it Visited; a missing photo never shows a placeholder box; a fallback/infeasible message never suggests less time; the honest fallback and the no-summary ending are never dead ends; live position is never simulated from a non-GPS signal and the continuous stream is never sent to or stored on a server.
UX-DR30: Build and keep a genuine Must-tier-only baseline (matching `key-must-tier-skeleton.html`) that every Should/Could feature can cleanly degrade to, per the Scope Tiers table - no Should/Could feature may be load-bearing for the Must-tier flow to complete end to end. Treat "disable every Should/Could capability and confirm the flow still completes" as an acceptance test in its own right.

### FR Coverage Map

FR-1: Epic 1 - Choose a starting point (Trip Setup)
FR-2: Epic 1 - Choose available time (Trip Setup)
FR-3: Epic 1 - Choose a topic (Trip Setup); Story 1.2 (catalogue coverage, Must) is a hard prerequisite for History/Architecture to actually work
FR-4: Epic 1 - Landmark <-> hidden-gem preference (Trip Setup)
FR-5: Epic 1 - Generate a proposed Route
FR-6: Epic 1 - Display the proposed Route, including real route geometry
FR-7: Epic 1 - Inspect stop content before approving
FR-8: Epic 1 - Explicitly approve the Route
FR-9: Epic 1 - Honest fallback when no suitable Route exists
FR-10: Epic 1 - Re-Jaunt
FR-11: Epic 1 - Manually remove or replace a stop
FR-12: Epic 2 - Access stop content during the walk
FR-13: Epic 2 - Mark a stop Visited/Completed
FR-14: Epic 2 - Show live position during the walk
FR-15: Epic 2 - Automatic arrival notification
FR-16: Epic 3 - AI-generated walk summary
FR-17: Epic 3 - Local visit history and favourites
FR-18: Epic 3 - Repeat-use route variety
FR-19: Epic 1 - AI content generation, grounded and checked
FR-20: Epic 1 - Source attribution shown to the user
FR-21: Epic 4, Story 4.2 - Second pilot-area demonstration (Should/stretch); NFR-5's configuration work itself is Epic 4 Story 4.1 (Must)
FR-22: Epic 1 - Stop photo, rights-cleared only
FR-23: Epic 2 - Muted background amenities at high zoom
FR-24: Epic 1 - Use current location for starting point

NFRs and the Additional/UX Design Requirements are cross-cutting rather than tied to one epic - each is satisfied incrementally within whichever epic's stories first touch the relevant screens/files (e.g. the stateless-backend/privacy NFRs are foundational to Epic 1's new planning endpoint; accessibility UX-DRs are applied wherever each component is first built, starting in Epic 1).

## Epic List

### Epic 1: Plan and Review a Trustworthy Walk
A user can set a starting point, available time, and topic (or "surprise me," or a landmark/hidden-gem preference); see a real, source-grounded, time-feasible proposed Route with inspectable per-stop content and visible attribution; adjust it (remove/replace a stop, Re-Jaunt for a different one) before approving; and, if nothing suitable exists, get an honest, non-dead-end explanation instead of a weak result. This is V1's Must-tier core plus its directly-attached Should-tier refinements - the entire unscheduled Trip-Setup/Route-Review frontend the PRD itself flags as real, unsized work, plus the AI content-generation and grounding-check pipeline that review depends on. The Must-tier path (Stories 1.1-1.6) is sequenced so backend capabilities (catalogue coverage, content generation, the planning endpoint) are built and independently tested before the frontend stories that consume them - no Must-tier story depends on a Should/Could story, and none depend on Epic 2, 3, or 4. Standalone: delivers a complete, demoable "plan and approve a real walk" experience on its own.
**FRs covered:** FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-7, FR-8, FR-9, FR-10, FR-11, FR-19, FR-20, FR-22, FR-24

### Epic 2: Walk It
A user can actually walk the approved Route: open any stop's content at any time without being nagged about it, see their live position (Jarrod's head marker) on the map when permission is granted and a calm non-error fallback when it isn't, explicitly mark a stop Visited while walking (distinct from merely opening its content), and see a muted, clearly-subordinate layer of nearby cafes/amenities when zoomed in. Reuses the real route geometry Epic 1 already fetches - no new geometry work here, only rendering it during the walk. Standalone: a user can complete a full walk end to end; does not require Epic 3 or 4.
**FRs covered:** FR-6 (reused), FR-12, FR-13, FR-14, FR-15, FR-23 (Story 2.6 adds the PRD-required real-world validation pass, not tied to one FR - added 2026-10-18)

### Epic 3: Remember and Vary
After finishing, a user gets a short, honest AI-generated summary of only the stops they actually confirmed visiting (never a stop they merely saw proposed or previewed) with a favourite-heart on each; their visit history and favourites are remembered locally across sessions without an account; and future Jaunts vary what they're shown based on that real history, while a favourite can always resurface. Standalone: depends on Epic 2 producing real Visited/Completed data, but delivers its own complete "remember and come back" value without needing Epic 4.
**FRs covered:** FR-16, FR-17, FR-18

### Epic 4: Expand to a Second Area
Once the Newtown experience works end to end, the same app can be pointed at a second Sydney-area bounding box and produce a real, working Catalogue there too - proving the architecture's configuration-not-hard-coding posture (NFR-5) actually holds. Story 4.2 (the actual demonstration) is an explicit stretch goal, deliberately last, never allowed to delay Epics 1-3; Story 4.1 (the configuration refactor, NFR-5) is Must-tier and doesn't wait for it (2026-10-20). Standalone: touches only the offline import pipeline (`import_places.py`, `import_street_art.py`, a second area's heritage source), not `planner.py`, `ai.py`, or the frontend.
**FRs covered:** FR-21 (Story 4.2)

---

## Epic 1: Plan and Review a Trustworthy Walk

A user can set a starting point, available time, and topic (or "surprise me," or a landmark/hidden-gem preference); see a real, source-grounded, time-feasible proposed Route with inspectable per-stop content and visible attribution; adjust it before approving; and, if nothing suitable exists, get an honest, non-dead-end explanation instead of a weak result.

**FRs covered:** FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-7, FR-8, FR-9, FR-10, FR-11, FR-19, FR-20, FR-22, FR-24

### Story 1.1: Trip Setup inputs - starting point, time, and topic (Must)

As a user opening Jaunt,
I want to choose where I'm starting, how much time I have, and what I'm interested in,
So that Jaunt knows what kind of walk to propose.

**Acceptance Criteria:**

**Given** the Trip Setup starting-point screen
**When** I tap any point on the map, inside or outside the Newtown catalogue boundary
**Then** that point is accepted and used as the Route's start/end point - there is no separate "outside Pilot Area" rejection; a start too far from any real Stop is handled by Story 1.6's honest fallback instead, once the planning request actually runs (FR-1, revised 2026-10-18)

**Given** the starting-point screen
**When** I select one of the predefined named-start chips instead of tapping the map
**Then** that named location is used as the start point (FR-1)

**Given** the available-time screen
**When** I adjust the time wheel-picker
**Then** I can select any value from 30 to 120 minutes in 5-minute increments, with the selected value shown using the `display-time` typography token - a vertical swipe/scroll gesture, tap elsewhere for chip/pill selection, per the project's interaction primitives (UX-DR28)

**Given** short-label single-action buttons on these screens (e.g. "Start my [Topic] Jaunt")
**When** they are built
**Then** they use the compact auto-width pill component, never inheriting the full-width-primary or `flex:1` styling meant for a different context - this exact mistake has recurred at least twice already in this project and must be explicitly tested for here, not just avoided by habit (UX-DR4, UX-DR5)

**Given** the topic screen (at-rest or Choose Topic page)
**When** I view the topic options
**Then** exactly history, architecture, and public art are offered as named Topics, plus "surprise me"/Wild Jaunt - heritage is never shown as a selectable Topic (FR-3, revised 2026-10-18)

**Given** I select Wild Jaunt
**When** the request is later sent for Route generation
**Then** candidates are not filtered to a single Topic - all Topics remain eligible (FR-3)

**Given** I have completed starting point, time, and topic
**When** I proceed
**Then** all three values are held in the browser's in-progress trip state, not yet sent to the server, ready for the next step

**Given** any Jarrod appearance on these screens
**When** it is rendered
**Then** it is a real cropped/composited region of the two source PNGs - never hand-drawn, redrawn, or AI-regenerated from a text description. This produced an unrecognizable result twice before the rule was adopted, and applies to the shipped app's own asset pipeline, not just design mocks (UX-DR18, UX-DR29)

**Given** any copy written for these screens
**When** it is written
**Then** it follows the Voice & Tone Do/Don't table - plain, warm, topic-specific where a real variable is known, never generic form-field language or alarm-coded failure framing (UX-DR21). This rule applies to every subsequent story's copy too, not only Trip Setup's.

**Given** every tappable control on these screens (named-start chips, topic pills, the preference-slider handle, compact pill buttons, the time wheel-picker)
**When** it is built
**Then** it meets or exceeds a ~44x44pt-equivalent touch target - checked directly against the real rendered size, not assumed from the padding values alone (UX-DR22). This is the first story to introduce these control types; later stories reusing the same component (chips, pills) inherit this check rather than re-deriving it.

**Given** short, tightly-sized labels on this screen (e.g. the selected time value, compact pill text)
**When** dynamic type / larger text settings are tested against them
**Then** the layout is checked to confirm it doesn't clip or overlap - not yet verified anywhere in this project, so this story is where that first real check happens (UX-DR27)

**Given** this screen is the app's only real form (starting point, time, topic), confirmed required by the course's own grading rubric (Sensorveiledning, criterion 4: "tastaturnavigasjon, alternativtekst og fornuftige skjemaetiketter") and not previously covered by any story in this document
**When** it is built
**Then** every input is reachable and operable via keyboard alone (tab order, Enter/Space activation, arrow-key operation of the time wheel-picker) and carries a real programmatic label (e.g. an `aria-label` naming what each chip/pill/control actually is), not just visible text with no semantic association. The map-tap starting-point control is the one exception needing its own documented keyboard-accessible alternative (e.g. a text/named-start fallback), since tapping a map has no natural keyboard equivalent.

### Story 1.2: Catalogue topic coverage for History and Architecture (Must - promoted from Should)

**Why Must, not Should:** FR-3 is Must-tier and commits to three selectable named Topics. Today, History and Architecture have exactly 1 ready stop each against the Planner's 2-stop minimum - those two Topics are selectable but non-functional 100% of the time. A Must-tier commitment that silently never works for two of its three options isn't met by "selectable" alone - this fix is required for FR-3 to actually be true, not an optional data improvement.

As a user choosing History or Architecture as my topic,
I want Jaunt to actually have enough real stops to build a walk,
So that these Must-tier topic choices work, not just appear selectable.

**Acceptance Criteria:**

**Given** the 29 `ready` Heritage-sourced catalogue records
**When** each record's Statement of Significance is reviewed
**Then** AI assigns `history` and/or `architecture` Topic tags only where that record's own source text actually supports that specific Topic - never a blanket "tag every record as both" shortcut (PRD Open Question 18)

**Given** AI's proposed Topic assignments
**When** they are produced
**Then** a human reviews and approves each one before it is stored - no assignment reaches the catalogue unreviewed

**Given** an approved assignment
**When** it is stored
**Then** it replaces that record's `heritage` tag (heritage is dropped as a Topic any record carries - FR-3, revised 2026-10-18) rather than being added alongside it, and the record's original source text is never rewritten

**Given** `import_heritage.py` rebuilds all 29 records from ArcGIS on every run (its own documented, intentional behavior)
**When** this story is implemented
**Then** the approved Topic assignments are NOT just a one-off edit to the generated `data/sydney_places.json` - they are persisted in a maintained override input the importer itself reads and applies (the same pattern `data/heritage_source_text.json` already establishes for Statement-of-Significance text), so a routine rerun of the importer does not silently discard the Must-tier coverage fix (confirmed real risk, Codex review 2026-10-18: `build_record()` unconditionally sets `topics: ["heritage"]` and `main()` overwrites existing records wholesale)

**Given** the override file exists
**When** the importer is rerun end to end
**Then** the approved History/Architecture tags are still present afterward - this rerun-survives check is part of this story's acceptance, not assumed from "it's stored somewhere"

**Given** the retagging is complete
**When** the `ready` catalogue is queried by Topic
**Then** both `history` and `architecture` have at least 2 `ready` stops, so FR-3's History and Architecture choices can actually produce a Route

**Given** this story is complete
**When** `planner.py` runs unchanged
**Then** no Planner code changes were needed - it already supports multi-Topic Stops

### Story 1.3: AI content generation, grounded and checked (Must)

As a user reading a Stop's content,
I want to trust that it's grounded in something real and automatically checked,
So that I never get fabricated information.

**Acceptance Criteria:**

**Given** a Stop with a real Source Excerpt
**When** AI generates its content (a story, fact, task, or prompt)
**Then** the generated content is grounded in that Source Excerpt, a Contextual Source, or both - never invented detail with no source basis (FR-19)

**Given** AI has generated content for a Stop
**When** that content is produced
**Then** an automated grounding check runs against it before it is returned to the planning pipeline (FR-19)

**Given** a Stop's generated content fails its automated grounding check, OR the content-generation call itself fails or times out for that stop
**When** this happens
**Then** that one Stop's content falls back to its raw Source Excerpt rather than being silently passed through or failing the whole Route - broadened 2026-10-20 (user-caught gap): the original wording only covered a failed grounding check, not a failed/timed-out generation call itself, but both need the same fallback (architecture AD-3)

**Given** AI content generation and the automated grounding check need real mechanism decisions, not just a described contract (resolved 2026-10-20, grounded in real timing measurements - see architecture AD-3)
**When** this story is built
**Then** content generation is one batched call per route (all the route's stops in one request), not one call per stop - at ~2s per real OpenAI call, N sequential calls would add real, avoidable latency and complexity; and the grounding check is a rule-based (non-LLM) check by default, not a second model call - this prototype's own thin/rich test pass (below) is where that default gets validated, escalating to a model call only if it proves insufficient there

**Given** a Stop's content blends its own Source Excerpt with Contextual Source material
**When** the content is generated
**Then** the Contextual Source's general information is never phrased or implied as something specifically known about that particular Stop (FR-19)

**Given** "a reliable Contextual Source" needed a concrete mechanism, not just a description (resolved 2026-10-20, user's explicit call: a few approved sources is enough for now)
**When** this story is built
**Then** Contextual Sources are drawn from a small, human-curated seed file (`data/contextual_sources.json`), following the same maintained pattern `data/heritage_source_text.json` already establishes - each entry real, verbatim text with its own source_type/source_title/source_url, reviewed before being added, never AI-generated or live-searched (PRD Open Question 13, resolved 2026-10-20)

**Given** the user's explicit forward-compatibility request - V1 ships a small curated set, but Jaunt should be able to grow into Jarrod actively researching/retrieving sources later "without redoing everything" (2026-10-20, see addendum.md's Post-V1 vision)
**When** this story is built
**Then** the seed-file lookup lives behind its own function with a fixed contract (given a Stop and the requested Topic, return a list of candidate `{source_type, source_title, source_url, text}` entries) - content generation calls that one function and never reads `data/contextual_sources.json` directly itself. This is the seam a future real retrieval system replaces; everything downstream (generation, the grounding check, the payload shape, the UI) stays unchanged either way (architecture AD-3)

**Given** content blends a Stop's own Source Excerpt with a Contextual Source (confirmed real gap, Codex review 2026-10-18, user's explicit choice: support this properly rather than constraining V1 to single-source content)
**When** the attribution reference is produced
**Then** it is a list of `{source_type, source_title, source_url}` entries, one per source actually drawn from - never a single triple that can only represent one source (architecture AD-3, corrected 2026-10-18). The grounding check runs against every source in that list, not just the first one.

**Given** generated content exists
**When** it is reviewed as part of normal QA
**Then** manual spot-checking against source material continues as a required second layer - documented as a process commitment, not replaced by the automated check (FR-19)

**Given** a small test set of example generated texts, some genuinely supported by a source excerpt and some not
**When** the automated grounding check runs against each
**Then** it correctly flags the unsupported examples and passes the supported ones, with its known limitations documented (architecture spine's recommended early prototype task)

**Given** the test set must include real catalogue examples, not just hypothetical ones (confirmed necessary, Codex review 2026-10-18: some real `ready` source excerpts are extremely thin, e.g. the actual catalogue entries "By Michael Snape." and "church in Newtown, New South Wales.")
**When** the prototype is built
**Then** it is run against both thin, real excerpts like these and richer ones, checking two separate things, not just one: (a) does generated content stay factually supported - richer prose is exactly where an unsupported detail could slip in; (b) is content built from a thin excerpt actually worth reading, or merely technically grounded. A thin source passing the grounding check is not the same as it producing good content - this story's prototype pass must look at both before the full content-generation flow is built on top of it

**Given** the grounding-check mechanism is built
**When** it is designed
**Then** it is written so it can also check FR-16's walk-summary content later (Epic 3), not only per-stop content

### Story 1.4: Generate a proposed Route via a new planning endpoint (Must)

**Backend-only, no UI** - split out from an earlier, over-large combined story so it can be built and verified (automated tests + direct API calls) before any Route Review screen consumes it. Depends only on Story 1.2 (catalogue coverage) and Story 1.3 (content generation); does not depend on Story 1.1's UI.

As a user who has set up a trip,
I want one request that returns a complete, time-feasible Route with real content and geometry, or a clearly-distinguishable failure,
So that the review screen can get everything it needs without multiple round trips.

**Acceptance Criteria:**

**Given** valid start point, time, and topic
**When** a new stateless planning endpoint receives them
**Then** it wraps the existing Planner+AI pipeline and returns a Route of at least 2 Stops, each `ready` Record Status, whose shortest feasible ordering plus Dwell Time fits within the requested time (FR-5)

**Given** a request's available time
**When** the Route is generated
**Then** the maximum stop count is computed per request as `min(7, requested_minutes // dwell_minutes_per_stop)` rather than a fixed ceiling - measured directly (brute-force ordering cost: ~0.06s at 5 stops, ~0.45s at 6, ~2.9s at 7 against a 12-candidate shortlist) rather than assumed safe; no Stop is ever added just to use up remaining time (FR-5, revised 2026-10-18)

**Given** a feasible Route is found
**When** the response is built
**Then** a new `services.py` function fetches the real route geometry (polyline) for the chosen stop order and includes it in the response - not just point-to-point durations (FR-6)

**Given** a feasible Route is found
**When** the response is built
**Then** Story 1.3's content generation runs for every stop in the chosen route before the response returns, and each stop carries its own id, order, generated content, and a structured attribution **list** (each entry `source_type`/`source_title`/`source_url`, one entry per source actually used - usually one, more when content blends a Contextual Source per Story 1.3) - never a flat content string, never a single triple that can't represent a blended stop (architecture AD-3, corrected 2026-10-18)

**Given** the endpoint returns a response
**When** it does
**Then** the server retains no memory of this request afterward - the response itself is the only record of this planning result (architecture AD-2)

**Given** zero feasible Stop combinations exist for the request
**When** the endpoint runs
**Then** it returns the existing `{"feasible": false, "reason": ...}` shape as a normal 200 response - an ordinary business outcome, not an error

**Given** the AI service fails with a genuine, non-retryable error (invalid credentials, exhausted quota) rather than ordinary infeasibility
**When** this happens
**Then** `planner.py` no longer returns the same `{"feasible": false}` shape used for ordinary infeasibility - it raises/propagates the failure distinctly, and the endpoint maps it to a real non-2xx status (required architecture fix, enables FR-9's technical-vs-honest distinction)

**Given** every offered option in the Option Menu is mathematically feasible but none is genuinely relevant/interesting for the requested topic (confirmed real gap, Codex review 2026-10-18: today's `SELECTION_SCHEMA` has no escape from picking one of the offered keys)
**When** AI judges this
**Then** it can return an explicit `none_suitable` outcome instead of being forced to pick a weak option, and the endpoint treats this as FR-9's relevance-based honest fallback - distinct from "zero feasible combinations" (caught before AI is ever called) and distinct from a genuine AI-service failure (architecture AD-7)

**Given** the menu AI is actually offered
**When** it is built
**Then** every Stop appearing in at least one feasible combination appears in at least one offered menu option, before the remaining slots are filled by budget-usage ratio as today - a plain top-N-by-ratio slice can otherwise let a worthwhile Stop disappear from every option AI ever sees, which would also starve Story 1.9's preference and Story 3.4's variety of any real Stops to act on (architecture AD-7)

**Given** the full request (routing matrix + AI selection + content generation + grounding check, once all exist)
**When** it runs
**Then** it targets roughly 30-45 seconds end-to-end for the typical case - revised 2026-10-20 against real measurements (the earlier 90s figure was an unfounded guess, correctly challenged by the user): `fetch_duration_matrix()` ≈1.8s, `ai.select_stops()` ≈1.9-2.6s per real call, so the already-built pieces alone run in ≈4-5s; content generation (one batched call per route, per Story 1.3) and a rule-based grounding check (near-instant, not a second model call) are the remaining unknowns this estimate accounts for. Still provisional until Story 1.3 is actually built and timed end to end - any per-call retry budget is bounded by what's left of the overall deadline, not stacked independently

**Given** malformed or invalid input (a non-numeric or out-of-range coordinate, a time outside 30-120, an unrecognized topic string, or an oversized/malformed request body)
**When** the endpoint receives it
**Then** it is rejected immediately with a clear error, before any routing-provider or AI call is made and before any expensive computation runs - not yet defined anywhere in this story before this correction (Codex review 2026-10-18)

### Story 1.5: Review and approve the proposed Route (Must)

Frontend story, depends on Story 1.1 (trip setup values) and Story 1.4 (the endpoint).

As a user who has set up a trip,
I want to see the proposed Route on a map with its stop list, inspect each stop's content and source, and explicitly approve it,
So that I know exactly what I'm about to walk before committing.

**Acceptance Criteria:**

**Given** a successful planning response from Story 1.4
**When** Route Review loads
**Then** the map shows the full walking path and every Stop's location, and an expandable stop list shows each Stop's name and Topic (FR-6)

**Given** a Stop is shown on the map
**When** it is rendered
**Then** it uses the resolved marker decision: an order-number badge plus a small place-type icon (picked from the stop's own name where a real keyword matches, otherwise its topic) on a white-plate circle - never Jarrod standing at the stop with a speech bubble as an individual marker, an alternative explicitly rejected and not to be reintroduced (UX-DR13, amended/corrected 2026-10-21). A rights-cleared photo (Story 1.11), where it exists, shows inside the Stop's own content overlay instead, not as the map pin

**Given** a generated Route
**When** Route Review loads
**Then** the estimated total time (walking + Dwell Time) is shown on screen, not only used internally (FR-6)

**Given** Route Review is showing a Stop
**When** I tap into that Stop
**Then** I can read its AI-generated content from the review screen before deciding whether to approve (FR-7)

**Given** a Stop's content is shown
**When** I view it
**Then** a visible reference to where it came from (Wikipedia, OSM tags, council dataset, or NSW Heritage) is shown alongside the content, not only available on request (FR-20) - every source in the stop's attribution list is shown when more than one was used (architecture AD-3, corrected 2026-10-18), never only the first

**Given** FR-20 also requires attribution for OSM, the routing provider, Wikipedia, NSW Heritage, and Inner West Council as providers of the app's data generally, not just per-stop (confirmed gap, Codex review 2026-10-18: this story only specified per-stop source references)
**When** this story is built
**Then** a shared attribution/credits UI element (e.g. a footer or an accessible "about this data" panel) names all five providers somewhere in the app, not only inferred from individual stop citations

**Given** I am satisfied with the proposed Route
**When** I tap the explicit approval action
**Then** the Route becomes an active walk; no walk begins without this explicit action (FR-8)

**Given** the planning response is received
**When** it is
**Then** the complete route+stops+content is persisted to the browser's own active-trip `localStorage` key, tagged with an explicit `phase: "reviewing"` and a `schema_version` (architecture AD-2, corrected 2026-10-18) - "saves the payload" alone doesn't define refresh recovery; a refresh here must re-show Route Review, not guess

**Given** a saved trip is loaded back from `localStorage` on refresh
**When** its `schema_version` doesn't match, or its shape fails basic validation
**Then** it is treated as unusable and triggers a safe reset to a fresh trip - never a crash, and never a silently wrong recovery screen (architecture AD-2)

**Given** the interactive controls on this screen (the stop list, the approve button, the map)
**When** they are built
**Then** basic keyboard operability is checked (tab order reaches every control, Enter/Space activates it) and every informational image (a stop's rights-cleared photo) carries real alt text describing the place, not the filename or a generic label - confirmed required by the course's own grading rubric (Sensorveiledning, criterion 4: "tastaturnavigasjon, alternativtekst og fornuftige skjemaetiketter"), not yet covered by any UX-DR or prior story in this document

**Given** the stop-list bottom sheet (UX-DR11) is this project's first real use of the ink-on-cream/surface text pairing at reading length (not just short labels)
**When** this story is built
**Then** an actual WCAG contrast ratio is calculated for that pairing and recorded - not yet done anywhere in this project, so this is where it first gets checked rather than assumed (UX-DR23)

**Given** the stop-list bottom sheet (and the stop-info overlay it opens into)
**When** either is shown
**Then** a visible, tappable close control exists alongside swipe-down-to-dismiss - a real, flagged gap today (only the Must-tier skeleton's stop overlay has one). Later stories reusing the bottom-sheet pattern (the confirmation sheet, the catch-up sheet, the off-canvas drawer) apply this same fix rather than re-deriving it (UX-DR25)

### Story 1.6: Honest fallback when no suitable Route exists (Must)

Depends on Story 1.4's distinct response shapes; this story is the UI/copy treatment that consumes them.

As a user whose request can't be satisfied,
I want Jaunt to tell me plainly and offer a way forward,
So that I never get a weak result or a dead end.

**Acceptance Criteria:**

**Given** Story 1.4's endpoint returns `{"feasible": false}` (zero feasible Stop combinations exist at all)
**When** this happens
**Then** the honest fallback message is shown instead of a weak Route, using Jarrod's dedicated sad pose and plain language (FR-9)

**Given** Story 1.4's endpoint instead returns AD-7's `none_suitable` outcome (feasible combinations exist, but AI judged none of them genuinely relevant/interesting for the requested topic)
**When** this happens
**Then** the same honest fallback screen is shown - this is also FR-9's "or sufficiently relevant" case, not a separate UI, though the copy may differ slightly from the zero-feasible case (e.g. a different-Topic suggestion is the natural fix here, more directly than a time adjustment - the walk was already time-feasible)

**Given** the fallback suggests a time adjustment
**When** that suggestion is shown
**Then** it always offers more time, never less (FR-9)

**Given** the fallback has a different-Topic suggestion available
**When** it is shown
**Then** that suggestion is valid and offered regardless of the original request's time (FR-9)

**Given** the fallback is shown, with or without a specific alternative
**When** I view it
**Then** I always have a way back to change my inputs - it is never a dead end (FR-9)

**Given** Story 1.4's endpoint instead returns a non-2xx technical-failure status
**When** this happens
**Then** a visibly different technical/service-failure message is shown - it never shares copy with the honest "no suitable walk" message (FR-9)

**Given** either message is shown
**When** I view it
**Then** no red/alert color treatment is used (none exists in the design system) and the result is never framed as the user's mistake - the failure state is signaled by Jarrod's sad pose and plain language, never color alone (UX-DR24)

### Story 1.7: Re-Jaunt (Should)

Depends on Story 1.4 (planning endpoint) and 1.5 (review screen). Consumes Must-tier capability; never a dependency of it.

As a user who isn't happy with the proposed Route,
I want to ask for a different one without starting over,
So that I can see another option before giving up.

**Acceptance Criteria:**

**Given** a displayed proposed Route
**When** I tap Re-Jaunt
**Then** the system re-runs route generation with the just-rejected Route's stops added to an `excluded_ids` list, and returns a different feasible Route when one exists in the Option Menu (FR-10)

**Given** no feasible alternative exists after exclusion
**When** Re-Jaunt is requested
**Then** it falls back to Story 1.6's honest fallback message (FR-10)

**Given** Re-Jaunt excludes stops
**When** this happens
**Then** every stop from the rejected route is excluded, not just that specific combination - a deliberate "clean break" design choice (architecture AD-5), not a bug

**Given** the backend is stateless
**When** Re-Jaunt is requested again after an earlier one
**Then** the frontend resends the full accumulated `excluded_ids` list, never a delta (architecture AD-5)

**Given** Route Review is shown
**When** Re-Jaunt and "Start my jaunt" are displayed
**Then** they appear as an equal-weight button pair, never one buried beneath the other (UX-DR6)

### Story 1.8: Manually remove or replace a stop (Should)

**Amendment, user-approved 2026-10-22:** Constrained AI selection keeps every other stop plus one replacement. If none is suitable, stay in review with the remaining stops, updated route/time and an inline explanation; allow the shorter walk, including one stop. UI revision approved later on 2026-10-22: no separate Remove control is shown; a Replace button sits inside each full-width beige stop card and remains available at one stop. The older X/remove-affordance wording below is superseded by this Replace-only control. Replace rejects that stop: no suitable final replacement shows sad Jarrod, never an empty walk. These controls are pre-walk only. This resolves the replacement-strategy/no-completion questions below; see the Story 1.8 spec for the implemented contract.

Depends on Story 1.5 (review screen). PRD Open Question 2 (replacement strategy) is genuinely open - this story must make and document a concrete choice, not leave it ambiguous in code.

As a user who's lukewarm on one proposed stop,
I want to remove it and get a replacement, without rejecting the whole Route,
So that I can fine-tune a Route I otherwise like.

**Acceptance Criteria:**

**Given** Route Review is showing the stop list
**When** I tap a stop's "X" remove affordance
**Then** that specific stop is excluded and a replacement search runs against the remaining shortlist (FR-11, UX-DR12, EXPERIENCE.md State Patterns)

**Given** the other stops in the Route that I did not remove (confirmed real gap, Codex review 2026-10-18: `excluded_ids` alone only stops the rejected stop from reappearing - it doesn't stop an unconstrained re-search from dropping everything else too)
**When** the replacement search runs
**Then** those stops are passed as `retained_ids` and the search looks only for a feasible combination containing every retained stop plus one replacement - not a fresh, unconstrained route generation that happens to exclude one id (architecture AD-5, corrected 2026-10-18)

**Given** a stop is removed/replaced
**When** this happens
**Then** the Route's time feasibility is re-validated before approval is allowed again (FR-11)

**Given** the replacement-selection strategy is genuinely undecided in the PRD (Open Question 2: fresh AI suggestion vs. next-best remaining Shortlist candidate)
**When** this story is implemented
**Then** it picks one approach and documents the choice explicitly - this is not left for a developer to silently decide

**Given** the replacement search finds no feasible completion
**When** this happens
**Then** the result is explicit and documented (e.g. falls back to Story 1.6's honest message) - not silently left undefined

### Story 1.9: Landmark <-> hidden-gem preference (Should)

Depends on Story 1.4 (the planning endpoint's AI-selection call, which this story adds fields to) and Story 1.1 (Trip Setup screens, where the control lives).

As a user with an opinion about well-known vs. lesser-known places,
I want to express that preference,
So that the stops Jaunt picks actually match what I'm looking for.

**Acceptance Criteria:**

**Given** the Topic-at-rest screen
**When** I view it
**Then** a landmark <-> hidden-gem preference control (continuous slider, Balanced default) appears beneath both buttons, and repeats on the Choose-Topic page (UX-DR8)

**Given** I tap Wild Jaunt directly from the at-rest screen
**When** the confirmation sheet appears
**Then** no preference control is shown there, though the Balanced default still applies to the request (UX-DR8)

**Given** I move the slider
**When** the request is submitted
**Then** its exact continuous position is sent, not quantized into a 3-value enum (architecture AD-4)

**Given** the preference value reaches the backend
**When** the planning endpoint runs AI stop selection
**Then** `source_type` and `source_title` (not currently sent to AI) are added to the candidate payload, and the preference value is included in AI's prompt as plain-language guidance (architecture AD-4, required code change)

**Given** this story is complete
**When** stop selection runs
**Then** no new Python-computed "prominence" field exists anywhere - AI alone judges well-known-ness from the real content it's given (architecture AD-4)

**Given** a strong hidden-gem preference
**When** selection runs
**Then** genuinely interesting hidden-gem stops remain eligible - the preference shapes ranking, it never excludes a stop outright (FR-4)

### Story 1.10: Use current location for starting point (Should)

Depends on Story 1.1 (same screen). Fully independent of Epic 2's continuous-tracking work (FR-14) - a one-shot read only, with no dependency on Story 2.2. Real-device verification needs a phone-accessible HTTPS setup (Geolocation is secure-context-only on every modern browser), not just a LAN-reachable dev server - the same environment fact Story 2.2 also notes, each independently.

As a user who doesn't know or can't find a landmark to tap,
I want to use my current location as my starting point,
So that I don't have to hunt for a map reference I don't have.

**Acceptance Criteria:**

**Given** the starting-point screen
**When** I tap "use my current location"
**Then** a one-time (not continuous) browser geolocation request fires with its own explicit, revocable permission prompt (FR-24)

**Given** this is the first of two separately-scoped location-permission moments in the product (the second is Story 2.2's continuous tracking)
**When** this prompt appears
**Then** it is the browser's own native permission dialog, not a custom UI - confirmed, not assumed, to behave accessibly, since this hasn't been separately verified for this product before (UX-DR26). Story 2.2's prompt relies on the same browser-native behavior rather than re-verifying it.

**Given** location permission is denied or the request fails
**When** this happens
**Then** it falls back cleanly to map-tap/named starts - never a dead end (FR-24)

**Given** this is a one-shot read
**When** it completes
**Then** it does not depend on FR-14's continuous-tracking plumbing (Epic 2) being built first (FR-24)

**Given** a location is obtained this way
**When** the trip request is sent
**Then** this one-time coordinate is sent to the routing/planning service like any other chosen starting coordinate - this is not the continuous GPS stream NFR-3 keeps device-only

### Story 1.11: Stop photo, shown only when rights-cleared (Should)

Depends on Story 1.5 (Stop row component). PRD Open Question 16 (real coverage) must be checked before this is treated as more than a nice-to-have.

As a user looking at a stop,
I want to see a real photo of it when one is legitimately available,
So that I get a better sense of the place without Jaunt showing anything it doesn't have the rights to.

**Acceptance Criteria:**

**Given** a Stop has a confirmed rights-cleared source image (e.g. an appropriately-licensed Wikidata/Wikimedia Commons image)
**When** it is displayed in the stop list or content view
**Then** its photo is shown with a checkable license type, source, and attribution (FR-22)

**Given** a Stop has no qualifying image
**When** it is displayed
**Then** no photo is shown - the text simply takes the full row width, never a placeholder/blank-image box (FR-22, UX-DR12)

**Given** this story begins
**When** real catalogue coverage is assessed
**Then** the fraction of `ready` Stops that actually have a qualifying rights-cleared image is checked and documented before this feature is treated as more than a nice-to-have for the Stops that happen to qualify (PRD Open Question 16)

---

## Epic 2: Walk It

A user can actually walk the approved Route: open any stop's content at any time without being nagged about it, see their live position on the map when permission is granted and a calm non-error fallback when it isn't, explicitly mark a stop Visited while walking, and see a muted, subordinate layer of nearby amenities when zoomed in.

**FRs covered:** FR-6 (reused), FR-12, FR-13, FR-14, FR-15, FR-23

### Story 2.1: The active walking screen (Must)

Depends on Story 1.5 (approval transitions here) and reuses Story 1.4's already-fetched route geometry - no new fetch. This is the foundational Must-tier story everything else in this epic builds on.

As a user who has approved a Route,
I want to walk it with my stops visible and their content available whenever I want it,
So that I can follow my walk at my own pace without being pressured.

**Acceptance Criteria:**

**Given** I approve a Route (Story 1.5)
**When** approval completes
**Then** the active-walking screen loads, showing the map with the route and stop markers, reusing the geometry Story 1.4 already fetched - no new fetch (FR-6, reused)

**Given** the active-walking screen
**When** I tap a stop marker or its row
**Then** its content overlay opens - the same overlay Story 1.5 already built for pre-walk review

**Given** a stop's content overlay is open
**When** I close it without interacting further
**Then** nothing further is required of me - the app never nags or blocks me for not opening a stop's content (FR-12)

**Given** the off-canvas drawer (UX-DR15) this screen introduces
**When** it is open
**Then** it gets the same visible close control Story 1.5 already established for the bottom sheet/stop overlay - applying that fix, not re-deriving it (UX-DR25)

**Given** the hamburger icon and other icon-only controls on this screen
**When** they are built
**Then** they meet the same ~44x44pt touch-target check Story 1.1 already established (UX-DR22)

**Given** I complete the walk without opening any stop's content
**When** this happens
**Then** the walk is still considered complete - opening content is always optional (FR-12)

**Given** I want to stop walking before Epic 3's catch-up/summary flow exists
**When** I tap the hamburger and end the walk
**Then** I'm returned to a fresh Trip Setup screen and the active-trip `localStorage` key is cleared (architecture AD-2's "end trip" action) - visit history (AD-6, Epic 3) is untouched. This minimal exit must work standalone, without Epic 3 built yet; Epic 3 later enriches this same exit point with catch-up and a summary, it does not replace or block it.

### Story 2.2: Show live position during the walk (Should)

Depends on Story 2.1.

**Testing prerequisite, confirmed real (Codex review 2026-10-18):** this story cannot be verified on a real phone without two things resolved first, neither of which is production hosting. (1) The dev server must bind `host="0.0.0.0"`, not Flask's default loopback-only `127.0.0.1` - a phone on the same network cannot reach a laptop's `127.0.0.1` at all. (2) The Geolocation API requires a secure context (HTTPS, or literally `localhost`) in every modern browser - a phone loading the laptop's plain-HTTP LAN address will have `navigator.geolocation` silently blocked, confirmed against the current W3C spec and Chrome/Firefox's documented behavior, not assumed. A small phone-accessible HTTPS setup (e.g. a tunnel tool, or a `mkcert`-signed local certificate for the LAN IP) must be established and documented before this story - or Story 1.10 - can be tested on a real device, not deferred until "later."

As a user walking an approved Route,
I want to see my live position on the map when I grant permission,
So that I can see where I am relative to the stops.

**Acceptance Criteria:**

**Given** the active-walking screen
**When** I'm asked for location permission
**Then** it's an explicit, revocable prompt - never automatic or silent (FR-14)

**Given** permission is granted
**When** my position updates
**Then** Jarrod's head-only marker (not a generic dot, not his full figure) moves along the route in real time (UX-DR14)

**Given** permission is denied, deferred, or never attempted
**When** this happens
**Then** a calm "Location off" pill replaces the marker - the static map/route/stops are otherwise identical, and this is explicitly not an error state, it is the Must-tier baseline every walk must degrade to cleanly (UX-DR14)

**Given** permission was already granted and position was updating
**When** the user revokes permission mid-walk (browser/OS settings) or the GPS signal is lost (e.g. indoors)
**Then** the live marker is removed and the same calm "Location off" pill appears - the rest of the walking screen (map, route, stops, content access) keeps working exactly as if GPS had never been granted; this is never shown as an error or a dead end, and degrading to this state mid-walk is treated the same as never having GPS at all

**Given** the pill is shown after a mid-walk loss
**When** permission or signal is restored
**Then** the live marker resumes automatically - no special re-grant flow beyond what the browser itself provides

**Given** the continuous position stream
**When** it updates
**Then** it is never transmitted to or stored on a server - it only drives the client's own map display (NFR-3)

**Given** the live-position marker renders
**When** it is drawn
**Then** it uses a DOM Marker with a real ~30px head-crop image, not a GeoJSON layer - one-off image content per architecture AD-1's rule, the same pattern as the existing start-point marker

**Given** `GeolocationCoordinates.heading` is a real, non-null value (the browser's own GPS-course-over-ground, from the same permission already granted for FR-14 - no separate compass/`DeviceOrientationEvent` permission requested)
**When** this is true
**Then** a small directional arrow overlays Jarrod's head marker, pointing the way he's actually heading

**Given** `heading` is `null`/`NaN` (the device is stationary, or heading can't be determined - the common case whenever a user pauses to read a stop's content)
**When** this is true
**Then** the arrow is not shown - just the plain head marker, never a guessed or stale direction (verified directly: this is the documented, spec-correct behavior of the API, not an edge case to special-case around)

### Story 2.3: Mark a stop Visited/Completed (Should)

Depends on Story 2.1. Must respect architecture AD-2's context-gating rule (the same overlay exists pre-walk via Story 1.5, where this control must stay disabled).

As a user who has actually reached a stop during my walk,
I want to explicitly confirm I was there,
So that my walk summary later only reflects what I genuinely did.

**Acceptance Criteria:**

**Given** I'm viewing a stop's content overlay during an active walk
**When** I tap the Visited checkbox (top-right, a separate tap from reading content)
**Then** that stop is recorded as Visited/Completed (FR-13)

**Given** the Visited checkbox badge (UX-DR16) this story introduces
**When** it is built
**Then** it signals its state with a bordered checkbox shape plus the word "Visited," never a color change alone, and meets the same ~44x44pt touch-target check established in Story 1.1 (UX-DR22, UX-DR24)

**Given** I view the same stop's content overlay before the walk starts (Story 1.5's pre-walk preview)
**When** I view it
**Then** the Visited checkbox is disabled/hidden - it is only actionable during an active walk (FR-13, architecture AD-2)

**Given** I merely open a stop's content without tapping Visited
**When** this happens, during or before the walk
**Then** it is never recorded as Visited/Completed - opening content and marking Visited are two separate explicit actions (FR-13)

**Given** a stop is marked Visited
**When** this happens
**Then** it is stored in the browser's active-trip `localStorage` object under the Engagement State schema Epic 3 later reads (architecture AD-6 - `state: "visited_completed"`)

**Given** I mark a stop Visited during an active walk
**When** I then refresh the page
**Then** that stop's Visited/Completed status is still shown as checked - it survives the refresh via the same active-trip `localStorage` persistence Story 1.5 already established (architecture AD-2) for the rest of the trip, not just the original plan contents

### Story 2.4: Muted background amenities at high zoom (Should)

Depends on Story 2.1. The data source is genuinely open (PRD Open Question 17) and must be decided, not assumed.

As a user zoomed into the map during my walk,
I want to see nearby cafes/amenities for orientation without them competing with my route,
So that the map stays oriented around my walk, not a general directory.

**Acceptance Criteria:**

**Given** I zoom in sufficiently
**When** amenity points are shown
**Then** they render as small (5px), low-opacity (0.7) muted dots with simple generic glyphs - visually subordinate to the route and stops at every zoom level where they appear (FR-23, UX-DR19)

**Given** amenity points are shown
**When** they are rendered
**Then** they use a GeoJSON source + MapLibre paint layer, not individual DOM markers, per architecture AD-1's rule for many-of-a-kind data

**Given** amenity points exist
**When** anything uses them
**Then** they are display-only - never stored as Stops, never fed into the Planner or AI selection (FR-23)

**Given** this story is implemented
**When** the data source is chosen
**Then** it is explicitly decided and documented (e.g. a live Overpass amenity query vs. a bundled/pre-fetched set) - PRD Open Question 17 leaves this genuinely open, not a given

### Story 2.5: Automatic arrival notification (Could)

Depends on Story 2.2 (live position) - explicitly, per the PRD itself ("Could, depends on FR-14"). The only Could-tier story in this epic.

As a user walking with live position enabled,
I want a gentle nudge when I'm near an unvisited stop,
So that I don't accidentally walk past something without noticing it.

**Acceptance Criteria:**

**Given** live position is active and permitted
**When** I come near an unvisited Stop
**Then** I receive a prompt inviting me to open its content (FR-15)

**Given** live position is not active (denied or never attempted)
**When** this happens
**Then** no such prompt ever fires - it is never simulated from a non-GPS signal (FR-15)

**Given** this feature doesn't exist
**When** the Must/Should path (Stories 2.1-2.4) is tested
**Then** nothing about it depends on this story - confirmed Could-tier, safely omittable

**Given** an arrival notification fires
**When** it is shown
**Then** it is subtle and non-intrusive - a quiet visual signal (e.g. a pill/badge), no sound or vibration by default, never a modal or alert that interrupts the walk. Exact visual treatment is genuinely undesigned (Scope Tiers table lists FR-15 as "not designed in detail") - this constraint (subtle, never intrusive) is the one firm requirement to decide it against when the story is actually built

### Story 2.6: Real-world validation - tester sessions and an outdoor walk (Must)

Added 2026-10-18 (Codex review: confirmed real gap - `prd.md`'s own §8 explicitly makes this part of V1 Must-tier completion, "not a free afterthought," but no story in this document assigned it or its evidence before this correction). Depends on Epic 1's Must-tier stories (1.1-1.6) and Epic 2's Story 2.1 - the full setup-through-walk path must exist first. Not tied to one FR; validates SM-1, SM-2, SM-3, SM-5, SM-6, SM-7 directly.

As the team preparing to submit V1,
I want real tester sessions and an actual outdoor walk against the app, not just passing automated tests,
So that the course's required validation evidence actually exists, and timing/relevance problems surface before submission, not after.

**Acceptance Criteria:**

**Given** the Must-tier flow is built and reachable on a real phone (Story 2.2's testing prerequisite resolved)
**When** at least one real outdoor walk is completed end to end
**Then** actual elapsed time is compared against the requested time, against SM-2's asymmetric tolerance (up to 25% under is acceptable, more than 10% over is not) - this is the first time this gets checked against real walking, not the routing provider's own estimate

**Given** `docs/ai-development-log.md` already records the routing provider's duration estimates running roughly 20-30% optimistic against comparison apps
**When** the real-world walk's actual-vs-estimated gap is measured
**Then** this is treated as a flag to investigate (and recalibrate the time budget if confirmed), not as proof of an error on its own - the PRD's own framing (SM-C1) warns against over-indexing on a single metric

**Given** the walk is completed
**When** the experience is assessed
**Then** stop relevance (SM-3, SM-5: can a tester say why each stop was included, without prompting) and content accuracy (SM-4: does generated content hold up against its real source on spot-check) are evaluated alongside timing, not just timing alone

**Given** tester sessions are run (not only the person who built the app)
**When** they happen
**Then** at least one tester completes the full flow - setup through an approved, walkable route - on a phone browser (SM-7), and rates the completed walk as "worth taking" (SM-1)

**Given** a deliberately infeasible test request (SM-6)
**When** it is tried during this validation pass
**Then** the honest fallback (Story 1.6) is confirmed to behave correctly against a real request, not just the automated test suite's fixtures

---

## Epic 3: Remember and Vary

After finishing, a user gets a short, honest AI-generated summary of only the stops they actually confirmed visiting; their visit history and favourites are remembered locally across sessions without an account; and future Jaunts vary what they're shown based on that real history, while a favourite can always resurface. All Should-tier, matching the PRD's own tiering - no Must or Could items in this epic.

**FRs covered:** FR-16, FR-17, FR-18

### Story 3.1: Catch-up before summarizing (Should)

Depends on Epic 2's Story 2.1 (the "End Jaunt" exit) and Story 2.3 (the Visited-marking mechanism). Inserts new screens *before* the state-clearing step Story 2.1 built standalone - it doesn't change what that clearing does, only delays it until this richer wrap-up finishes, consistent with architecture AD-2's "end trip fires at wrap-up completion, not the initial hamburger tap" rule.

As a user ending my walk,
I want to review and retroactively mark any stops I forgot to check off,
So that my eventual summary reflects everywhere I actually went.

**Acceptance Criteria:**

**Given** I tap "End Jaunt"
**When** the catch-up screen loads instead of immediately clearing state and returning to setup
**Then** every stop in my route is shown as checked or unchecked based on its current Visited status

**Given** an unchecked stop
**When** it is shown on the catch-up screen
**Then** it carries a soft "forgot?" hint, not a demand

**Given** the catch-up row's (UX-DR17) own checkbox-style tap target
**When** it is built
**Then** it meets the same ~44x44pt touch-target check established in Story 1.1, and the sheet gets the same visible close control established in Story 1.5 (UX-DR22, UX-DR25)

**Given** I tap an unchecked stop on the catch-up screen
**When** I do
**Then** it becomes Visited/Completed - still an explicit action, not inferred (FR-13's rule extended to retroactive catch-up)

**Given** the catch-up screen
**When** I've reviewed it
**Then** I can proceed to either "Create summary of visited stops" (Story 3.2) or the quiet secondary "end without a summary" link

**Given** I proceed from catch-up, either path
**When** this happens
**Then** the active-trip `localStorage` state is not cleared yet - it stays alive through whichever path comes next, consistent with architecture AD-2

### Story 3.2: AI-generated walk summary (Should)

Depends on Story 3.1 (needs confirmed Visited stops) and reuses Epic 1 Story 1.3's grounding-check infrastructure (that story was explicitly built to be reusable here).

As a user who finished a walk and confirmed what I actually visited,
I want a short, honest AI summary of just those stops,
So that I get a meaningful recap grounded in what I really did.

**Acceptance Criteria:**

**Given** I tap "Create summary of visited stops"
**When** the summary is generated
**Then** it is grounded strictly in Stops marked Visited/Completed - never a Stop that was only Proposed or merely Opened/Engaged (FR-16)

**Given** zero stops are marked Visited/Completed
**When** I reach this point
**Then** no summary is generated - an honest "nothing confirmed" message is shown instead of fabricating one from Proposed/Opened stops (FR-16)

**Given** the summary is generated
**When** it is
**Then** it reuses the same automated grounding-check mechanism Story 1.3 built for per-stop content - no new detector is built from scratch (FR-16, FR-19)

**Given** the summary is shown
**When** each visited stop appears in it
**Then** it carries its own favourite-heart tap target (feeds Story 3.3/3.4)

**Given** summary generation fails for a technical reason, with at least one Stop genuinely marked Visited/Completed
**When** this happens
**Then** the result is NOT the same "Jaunt complete" no-summary ending as the zero-Visited case - the user still sees a plain, non-AI list of the Stops they actually confirmed visiting, each still carrying its own favourite-heart target, so favouriting never depends on AI succeeding (FR-16, revised 2026-10-18)

**Given** summary generation fails AND zero Stops are marked Visited/Completed
**When** this happens
**Then** the genuinely-empty-walk ending applies (the honest "nothing confirmed" message) - that is the one case these two endings still share

**Given** the "Back to start" button on the no-summary "Jaunt complete" ending
**When** it is built
**Then** it uses the compact auto-width pill component, never the full-width-primary treatment - this exact button previously made exactly this mistake once already; explicitly test for the regression here too (UX-DR4, UX-DR5)

### Story 3.3: Local visit history and favourites (Should)

Depends on Epic 1 Story 1.5 (where a Stop first becomes Proposed/Opened-Engaged) and Epic 2 Stories 2.1/2.3 (where it may become Opened-Engaged/Visited-Completed during the walk) and Story 3.2 (the favourite-heart tap target). **Important integration note:** this story is not purely additive to Epic 3's own screens - it hooks into interactions already built in Epic 1 and Epic 2, which must each start emitting a history-recording side-effect once this story exists.

As a user who has walked before,
I want my visit history and favourites remembered locally without an account,
So that future Jaunts can recognize places I've already experienced.

**Acceptance Criteria:**

**Given** a Stop is shown in a proposed Route (Story 1.5) or during the walk (Epic 2)
**When** this happens
**Then** it is recorded with Engagement State `proposed` if it has no stronger state yet, live as Epic 1/2's existing screens are used - not only retroactively at the end-of-walk catch-up/summary flow

**Given** this story keys history/favourites on a Stop's catalogue `id` (architecture AD-6), and some of those ids (public_art records imported from the street-art spreadsheet) are derived from the source sheet's row number rather than a stable identifier (a known, already-accepted limitation from Sprint 5 - `import_street_art.py`)
**When** this story is built
**Then** that fragility is noted explicitly here as now consequential, not just a data-import footnote: a resorted or edited source sheet could silently shift which real place an existing history/favourite entry points to. Not required to be fixed by this story (the source file is a frozen snapshot today), but the risk must be documented where it's actually relevant - a future refresh of the street-art data needs stable source-to-place identities first, not after favourites already depend on today's row numbers

**Given** a Stop's content is then opened, pre-walk or during the walk
**When** this happens
**Then** its state upgrades to `opened_engaged`, never downgrading an existing stronger state (e.g. `visited_completed`)

**Given** any of this activity, or a Favourite tap
**When** it happens
**Then** it is written to the separate `localStorage` key from the active trip (architecture AD-6) immediately, as the interaction happens - not batched or deferred to when the walk ends. Revised 2026-10-18: an earlier draft of this story said "when the walk ends," which contradicted the two ACs above (live updates) and would also lose history if the browser closed mid-walk. The schema is exactly `{id, state, favourited, rejected}` (added 2026-10-20: `rejected`, see below), the three ordinal Engagement States stored distinctly, never collapsed into one "seen" flag (FR-17)

**Given** no account exists
**When** any of this happens
**Then** no login or account creation is ever required to use Favourites or Visit History (FR-17)

**Given** a Stop the user genuinely isn't interested in - not merely one they've visited (added 2026-10-20, user's explicit instruction)
**When** they take a dedicated "not interested" action on it (distinct from marking Visited or Favouriting - the exact control/placement is this story's own decision to make, not specified here)
**Then** `rejected` is set `true` for that Stop's `id`, and from then on `planner.py` filters it out of the candidate shortlist entirely before `ai.py` ever sees it (architecture AD-6) - a hard exclusion in every future Route regardless of Topic, never a soft weighting like the other signals above, and never expiring

**Given** this story is built
**When** retention/reset behaviour is decided
**Then** whether history ever expires and whether a user-facing clear control exists is explicitly decided and documented - PRD Open Question 7 is genuinely open, not assumed either way. If a clear/reset control is built, it should state plainly whether it also clears `rejected` Stops, since that reset is more consequential (bringing back something the user explicitly said they didn't want) than clearing ordinary visit history

### Story 3.4: Repeat-use route variety (Should)

Depends on Story 3.3 (history must exist to be used) and Epic 1 Story 1.4 (the planning endpoint, which this story adds the history signal to).

As a user planning a new Jaunt after previous ones,
I want future routes to favour places I haven't experienced yet,
So that repeat use doesn't just show me the same things.

**Acceptance Criteria:**

**Given** stored visit history exists
**When** a new planning request is sent
**Then** it includes this history as a transient, soft AI-weighting signal (architecture AD-6) - never persisted server-side in V1 (NFR-2)

**Given** a Stop marked Visited/Completed
**When** future selection runs
**Then** it is deprioritized more strongly than one that was only Proposed or Opened/Engaged - a merely-Proposed Stop is never penalized as if genuinely experienced (FR-18)

**Given** a Favourited Stop
**When** future selection runs
**Then** it is never excluded by the deprioritization rule, regardless of its other Engagement State - it can always resurface (FR-18)

**Given** a Favourited Stop and a genuinely new Stop with no prior engagement are both real candidates for the same Route
**When** selection runs
**Then** the new Stop is still generally preferred, all else equal - "never excluded" cancels the Visited/Opened penalty, it does not add a preference of its own on top (FR-18, clarified 2026-10-18, also architecture AD-6)

**Given** this story is built
**When** the exact weighting between Engagement States is decided
**Then** it is documented as a tuning/design choice, not assumed - PRD Open Question 9 leaves the precise weighting open; only the direction (stronger engagement -> stronger deprioritization) is fixed

**Given** no history exists yet (a first-time user)
**When** a request is sent
**Then** selection behaves exactly as it does today - this signal is additive, never required

---

## Epic 4: Expand to a Second Area

Once the Newtown experience works end to end, the same app can be pointed at a second Sydney-area bounding box and produce a real, working Catalogue there too - proving the architecture's configuration-not-hard-coding posture (NFR-5) actually holds. The actual second-area demonstration (Story 4.2) is an explicit stretch goal, deliberately last, never allowed to delay Epics 1-3; the configuration refactor itself (Story 4.1) is Must-tier and does not wait for the rest of this epic (clarified 2026-10-20, promoted from Should - see Story 4.1). Touches only the offline import pipeline, not `planner.py`, `ai.py`, or the frontend.

**FRs covered:** FR-21 (Story 4.2 only - Story 4.1 serves NFR-5 directly, see below)

### Story 4.1: Move Newtown/English-specific values into configuration (Must - promoted from Should, 2026-10-20)

**Why Must, not Should:** this story serves NFR-5 directly ("Language and Pilot Area boundary must be kept as configuration... an architectural posture for V1"), which reads as a V1 codebase property, not something contingent on whether a second area ever gets demonstrated. Bundling it inside an explicitly-optional, deliberately-last epic (clarified 2026-10-18, promoted 2026-10-20 at the user's request) risked it being skipped along with everything else in Epic 4 if time runs short - exactly the outcome NFR-5 is meant to prevent. It's a small, cheap, self-contained refactor (only touches `import_places.py`, depends on nothing in Epics 1-3) - keep it simple, do it early. Only Story 4.2 (the actual second-area demonstration) stays the genuinely optional, deferrable part.

As a developer preparing to support a second area,
I want Newtown-specific and English-specific values extracted into configuration,
So that pointing the pipeline at a new area doesn't require code changes.

**Acceptance Criteria:**

**Given** `import_places.py`'s `PILOT_BBOX` and any other Newtown-specific hard-coded value
**When** this story is complete
**Then** these values are read from configuration rather than inline literals (FR-21 phase 1)

**Given** `import_places.py`'s English-only Wikipedia-language assumption (a known limitation since Sprint 1)
**When** this story is complete
**Then** the language prefix is also configuration-driven, not hard-coded - even though no second language is being built now (§7 extensibility NFR)

**Given** this refactor
**When** it is complete
**Then** it changes no behavior for the existing Newtown/English configuration - running the importers unchanged still produces the same catalogue (regression-safe, 174/174 tests still pass)

### Story 4.2: Second pilot-area demonstration catalogue (Should)

Depends on Story 4.1.

As a developer validating Jaunt's extensibility claim,
I want to run the existing import pipeline against a second Sydney-area boundary,
So that FR-21's stretch goal is actually demonstrated, not just architecturally possible.

**Acceptance Criteria:**

**Given** Story 4.1's configuration refactor
**When** the OSM-based and street-art importers are pointed at a new bounding box
**Then** they produce `ready` Stops for the new area without modifying `planner.py`, `ai.py`, or the frontend (FR-21 phase 2)

**Given** the new area's heritage-topic coverage
**When** it is attempted
**Then** the same automated OSM+Wikidata path used for history/architecture is tried first - manual curation (`import_heritage.py`'s current approach) is a fallback, not the default, for a second area

**Given** the exact second-area boundary is not yet confirmed
**When** this story begins
**Then** the boundary is explicitly chosen and documented (Surry Hills is suggested by feasibility research - denser OSM coverage, no language change needed - but not committed) - PRD Open Question 5

**Given** this is an explicit stretch goal
**When** Epics 1-3 and this epic compete for time
**Then** this epic is never allowed to delay the Newtown end-to-end flow
