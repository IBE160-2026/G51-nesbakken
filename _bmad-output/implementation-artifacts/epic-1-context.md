# Epic 1 Context: Plan and Review a Trustworthy Walk

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

A user sets a starting point, available time, and topic (or "surprise me," or a landmark/hidden-gem preference), and gets back a real, source-grounded, time-feasible proposed walk with inspectable per-stop content and visible attribution. They can adjust it (remove/replace a stop, ask for a different one) before explicitly approving it, and if nothing suitable exists, get an honest, non-dead-end explanation instead of a weak result. This is V1's Must-tier core plus its directly-attached Should-tier refinements: the entire Trip-Setup/Route-Review frontend, and the AI content-generation + grounding pipeline that review depends on. It matters because it's the first point the product has to prove it isn't just assembling plausible-sounding nonsense - every later epic (walking, remembering, expanding) assumes this planning/review loop already works and is trustworthy.

## Stories

- Story 1.1: Trip Setup inputs - starting point, time, and topic (Must)
- Story 1.2: Catalogue topic coverage for History and Architecture (Must)
- Story 1.3: AI content generation, grounded and checked (Must)
- Story 1.4: Generate a proposed Route via a new planning endpoint (Must, backend-only)
- Story 1.5: Review and approve the proposed Route (Must)
- Story 1.6: Honest fallback when no suitable Route exists (Must)
- Story 1.7: Re-Jaunt (Should)
- Story 1.8: Manually remove or replace a stop (Should)
- Story 1.9: Landmark <-> hidden-gem preference (Should)
- Story 1.10: Use current location for starting point (Should)
- Story 1.11: Stop photo, shown only when rights-cleared (Should)

## Requirements & Constraints

- Starting point accepts any map tap or a named-start chip, with no boundary rejection; a point too far from any real stop is handled by the honest fallback (not a separate error). "Use my current location" is a one-shot, explicitly-permissioned alternative that falls back cleanly to map-tap/named starts on denial or failure, and is independent of any continuous-tracking work.
- Available time is 30-120 minutes in 5-minute increments; a proposed route's walking time plus per-stop dwell time must never exceed it.
- Topic is exactly history, architecture, public art, or "surprise me" (surprise-me keeps all topics eligible, never pre-filters to one); heritage is never a user-facing topic choice. History and architecture each need real catalogue coverage (>=2 ready stops) for these choices to actually work.
- An optional landmark <-> hidden-gem preference shapes ranking only - it never excludes a genuinely interesting stop outright.
- A proposed route has a minimum of 2 stops and a per-request dynamic maximum (never a fixed ceiling, never padded just to fill time); every stop is `ready` status.
- Before approving, the user must be able to inspect each stop's AI-generated content and its source, see the total estimated time on screen, and see attribution for every source actually used - plus a standing, sitewide credit naming OSM, the routing provider, Wikipedia, NSW Heritage, and Inner West Council. Approval requires one explicit affirmative action; nothing becomes an active walk without it.
- When no feasible or sufficiently relevant route exists, the response is an honest, plain-language explanation with a way back - never a weak result, never a dead end, never framed as the user's fault, and a suggested time adjustment only ever offers more time. A genuine technical/service failure must look and read differently from an honest "no suitable walk."
- Re-Jaunt and stop removal/replacement both re-validate time feasibility before re-approval is allowed.
- All generated content must be grounded in a stop's source excerpt and/or an approved contextual source, backed by both an automated check and ongoing manual spot-checking - never passed through ungrounded.
- A stop photo is shown only when a rights-cleared image exists; otherwise there is no photo and no placeholder.
- No account or login is required; nothing from this epic is persisted server-side beyond the single planning request/response. The app is built and tested mobile-first. The existing automated test suite must keep passing as these stories land.
- Success is ultimately judged by: a suitable result for real inputs, a route that's viewable/followable from a phone, a walk finishable close to the requested time, stops that are genuinely real and relevant, content consistent with its sources, users understanding why a stop was included, and an honest response when nothing suitable exists.

## Technical Decisions

- The backend is fully stateless: one planning request returns the complete route + stops + generated content; Re-Jaunt, replace-a-stop, etc. are separate stateless requests. The frontend is the only place state lives, in two distinct `localStorage` keys: the active trip (tagged with `phase` and a `schema_version`, so a refresh re-shows the right screen rather than guessing, and an invalid/mismatched payload triggers a safe reset; this object also carries the session-local `excluded_ids` list used by Re-Jaunt/replace) and a separate visit-history key (favourites/engagement state, cross-trip, never cleared by "end trip").
- Route feasibility and ordering are both solved by brute-force permutation over a shortlist (cheap at this scale, provably optimal); the max stop count per request is `min(7, requested_minutes // dwell_minutes_per_stop)`, not a fixed constant. Feasible combinations are ranked into a bounded option menu by how fully they use the requested time, with a coverage pass guaranteeing every stop appearing in any feasible combination appears in at least one offered option (so preference/variety signals always have real stops to act on).
- AI's job is strictly relevance/taste: given the pre-vetted feasible menu, it picks the best-matching option, or returns an explicit `none_suitable` outcome when nothing offered is genuinely relevant - it never does routing arithmetic, and Python never overrides its relevance judgment. Three outcomes must stay visibly distinct: zero feasible combinations (plain `{"feasible": false}`, normal 200), AI's `none_suitable` (also a normal 200, different reason), and a genuine AI/service failure (invalid credentials, exhausted quota - re-raised and mapped to a non-2xx status, never collapsed into the ordinary infeasible shape).
- Content generation is one batched AI call per route (not per stop), run synchronously at plan time before the response returns. Grounding is a rule-based (non-LLM) check by default. A per-stop grounding failure or a failed/timed-out generation call both fall back to that stop's raw source excerpt - never silently passed through, never failing the whole otherwise-feasible route.
- A stop's attribution is a list of `{source_type, source_title, source_url}` entries (one per source actually used - usually one, more when content blends in a contextual source), never a flat string or a single fixed triple. Contextual sources are drawn from a small curated seed file, accessed only through one function with a fixed `{source_type, source_title, text, ...}` contract - the seam a future real retrieval system can replace without touching generation, the grounding check, or the UI.
- The preference slider sends its exact continuous value into AI's existing selection prompt as plain-language guidance (no new Python-computed "prominence" score); `source_type`/`source_title` are added to AI's candidate payload so it has real signal to judge well-known-ness from.
- Replacing one stop passes the kept stops as `retained_ids` (a constrained search for one replacement, not an unconstrained re-run); Re-Jaunt instead excludes every stop of the whole rejected route via a cumulative, frontend-resent `excluded_ids` list - a deliberate "clean break," not a bug.
- Malformed input (bad coordinates, out-of-range time, unknown topic, oversized body) is rejected immediately, before any routing or AI call. End-to-end target is roughly 30-45 seconds for a typical request.
- Map rendering: many-of-a-kind, data-driven features (route line, numbered stop circles, background amenity points) are GeoJSON sources + MapLibre paint layers, never one DOM marker per feature; only one-off image content (a rights-cleared photo pin) uses a real `maplibregl.Marker`. A stop marker is a photo-thumbnail pin when a qualifying image exists, otherwise a plain numbered circle - never a character-at-the-stop marker.
- The History/Architecture catalogue-coverage fix is stored in a maintained override file the importer itself reads (so a routine re-import can't silently discard it), replacing each record's heritage tag rather than adding to it, with every AI-proposed assignment human-reviewed before storage.

## UX & Interaction Patterns

- The compact pill button (auto-width) and the full-width primary button are genuinely separate components, never interchangeable variants - this has been the most-repeated bug in the project; explicitly verify short-label buttons like "Start my [Topic] Jaunt" never inherit full-width styling. Re-Jaunt/"Start my jaunt" and Choose-Topic/Wild-Jaunt are equal-weight button pairs, never one primary + one buried action.
- Chips and pills show selection via fill inversion (forest fill/cream text), never a border or checkmark addition; every tappable control meets a ~44x44pt touch target, checked against real rendered size.
- The preference slider is a continuous track with a "Balanced" default, shown beneath the buttons on the topic-at-rest and Choose-Topic screens, and deliberately absent from the Wild Jaunt confirmation sheet (though Balanced still applies to that request).
- The stop list and stop-info overlay reuse one bottom-sheet pattern, dismissed by swipe-down plus a real, visible close control (not swipe-only); a stop row's trailing "X" remove affordance appears only where remove/replace is in scope.
- Every Jarrod appearance must be a real cropped/composited region of the two existing source PNGs, never hand-drawn or AI-regenerated; failures use his sad pose plus plain language, never a red/alert color (none exists in this design system) and never color alone to signal state.
- Copy follows the project's plain, warm, topic-specific voice - never generic form-field language, progress percentages, or "Error:" framing.
- This epic is where several accessibility checks happen for the first time: full keyboard operability and real `aria-label`s on every Trip Setup and Route Review control (the map-tap start point needs a documented keyboard-alternative), informative alt text on any stop photo, an actual WCAG contrast check on body-length ink-on-cream text, and a dynamic-type/text-scaling check against tightly-sized labels (time value, compact pills).

## Cross-Story Dependencies

- Must-tier stories are sequenced so backend capability lands before the frontend that consumes it: 1.2 (catalogue coverage) and 1.3 (content generation) must exist before 1.4 (the planning endpoint); 1.4 is a hard prerequisite for 1.5 (review screen) and 1.6 (fallback UI). 1.1 (Trip Setup UI) feeds 1.5 but does not block 1.4 - the endpoint can be built and tested independently of any UI. No Must-tier story depends on a Should-tier story, and none depend on Epic 2, 3, or 4.
- Should-tier stories all sit on top of the Must-tier core: 1.7 (Re-Jaunt) and 1.8 (remove/replace) both need 1.4 and 1.5; 1.9 (preference slider) needs 1.1's control and 1.4's backend fields; 1.10 (current location) only needs 1.1 and is fully independent of Epic 2's continuous-tracking permission flow; 1.11 (stop photo) needs 1.5's stop-row component.
- Epic 1 is standalone: it delivers a complete, demoable plan-and-approve experience on its own, with no dependency on Epic 2, 3, or 4.
