# Epic 1 Context: Plan and Review a Trustworthy Walk

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

A user sets a starting point, available time, and topic (or "surprise me," or a landmark/hidden-gem preference), and gets back a real, source-grounded, time-feasible proposed walk with inspectable per-stop content and visible attribution. They can adjust it (remove/replace a stop, ask for a different one) before explicitly approving, and if nothing suitable exists they get an honest, non-dead-end explanation instead of a weak result. This is V1's Must-tier core plus its directly-attached Should-tier refinements. Stories 1.1-1.3 (trip-setup UI, catalogue topic coverage, grounded content generation) are built; the next piece, Story 1.4, is the stateless planning endpoint that wires the already-built Planner + AI selection + content generation into one request/response contract the later review and fallback stories consume. It matters because the product's stated differentiator is choosing an honest alternative over a fabricated-looking answer - this epic is where that promise becomes real, and every later epic assumes this planning/review loop already works.

## Stories

- Story 1.1: Trip Setup inputs - starting point, time, and topic (Must) - built
- Story 1.2: Catalogue topic coverage for History and Architecture (Must) - built
- Story 1.3: AI content generation, grounded and checked (Must) - built
- Story 1.4: Generate a proposed Route via a new planning endpoint (Must, backend-only) - next
- Story 1.5: Review and approve the proposed Route (Must)
- Story 1.6: Honest fallback when no suitable Route exists (Must)
- Story 1.7: Re-Jaunt (Should)
- Story 1.8: Manually remove or replace a stop (Should)
- Story 1.9: Landmark <-> hidden-gem preference (Should)
- Story 1.10: Use current location for starting point (Should)
- Story 1.11: Stop photo, shown only when rights-cleared (Should)

## Requirements & Constraints

- Starting point: any map tap (no boundary rejection) or a named-start chip; "use current location" is one-shot, falling back cleanly on denial/failure. A start far from any real stop is handled by the honest fallback, not a separate rejection.
- Time: 30-120 min, 5-min increments; walking plus dwell time must never exceed it. Max stop count per request is computed dynamically (`min(7, requested_minutes // dwell_minutes_per_stop)`), never a fixed ceiling, and no stop is ever added just to use up remaining time.
- Topic: history, architecture, public art, or "surprise me" (all topics stay eligible, never filtered to one); heritage is never user-facing. An optional landmark<->hidden-gem preference shapes ranking only, never excludes a stop.
- A route has a minimum of 2 stops, every stop `ready` status, and the shortest feasible ordering plus dwell time within the requested time.
- Malformed/invalid input (bad coordinate, time outside 30-120, unrecognized topic, oversized body) is rejected immediately, before any routing/AI call or other expensive work.
- Three planning outcomes must stay distinct, never conflated: (1) zero feasible stop combinations at all; (2) feasible combinations exist but AI judges none genuinely relevant/interesting for the topic; (3) a genuine AI/service failure (bad credentials, exhausted quota). (1) and (2) are both honest `200`s with different reasons; (3) is a real non-2xx and must never share a response shape with (1)/(2).
- Before approving: inspect each stop's content and source, see the total estimated time, see attribution for every source actually used (a list, since content may blend sources), plus a sitewide credit naming OSM, the routing provider, Wikipedia, NSW Heritage, and Inner West Council.
- Re-Jaunt and remove/replace both re-validate time feasibility before re-approval.
- No account/login; nothing persists server-side beyond the single request/response. End-to-end target is roughly 30-45s typical.

## Technical Decisions

- **Statelessness (AD-2):** one planning request returns the complete route+stops+content; replace-a-stop, mark-visited, and Re-Jaunt are each separate stateless requests taking current state as input - the endpoint keeps no server memory of a prior request. All cross-request state lives in frontend `localStorage`: the active trip (tagged with an explicit `phase` and `schema_version`, so a refresh recovers the right screen and a mismatched/invalid payload safely resets instead of crashing) and a separate visit-history key, untouched by "end trip."
- **Exclusion vs. retention (AD-5):** the selection path needs two distinct parameters. `excluded_ids` is a hard filter - Re-Jaunt adds every stop of the whole just-rejected route (not only the specific combination), and since the backend is stateless the frontend resends the full accumulated list every call, never a delta; a deliberate "clean break," not a gap. `retained_ids` (the replace-one-stop path) instead constrains the search to a feasible combination containing every retained stop plus one replacement, rather than an unconstrained re-search. Both re-validate time feasibility before re-approval.
- **AI selection honesty and menu diversity (AD-7):** the selection schema must offer an explicit `none_suitable` outcome (with a required one-line reason) alongside real option keys, so a feasible-but-irrelevant menu can be honestly rejected instead of forcing a weak pick - the endpoint treats this as its own honest-fallback case, distinct from "zero feasible combinations" (caught before AI is called) and from a genuine AI-service failure. Menu construction must also guarantee every stop in at least one feasible combination appears in at least one offered option before filling remaining slots by budget-usage ratio as today - otherwise a worthwhile stop can silently vanish from every menu AI ever sees, starving later preference/variety features of anything to act on.
- **Data/error-shape convention:** JSON throughout; an ordinary "no suitable route" result (outcomes 1 and 2 above) is always a normal `200` carrying `{"feasible": false, "reason": ...}`. Non-2xx is reserved for genuine system failures, mirroring the existing `CatalogueError` -> `503` pattern. **Required code change for this story:** `planner.py`'s `plan_route()` currently collapses a real `ai.AiFatalError` into that same `{"feasible": false}` shape used for ordinary infeasibility - before the endpoint is built, it must stop swallowing that error and re-raise it (the same propagation shape `CatalogueError` already uses) so the endpoint can map it to a real non-2xx without parsing free-text `reason`.
- **Plugging in content generation (AD-3, built in Story 1.3):** the endpoint calls `ai.generate_stop_content(stops, topic)` synchronously, once per route (one batched call, not per stop), after stop selection and before the response returns. It never raises; every failure mode (a per-stop grounding failure, a failed/timed-out generation call, a response missing a stop's entry) falls back to that stop's raw `source_excerpt` rather than discarding an otherwise-feasible route. Each stop in the response carries its own `id`, order position, generated `content`, and an attribution **list** of `{source_type, source_title, source_url}` entries - one per source actually declared used, never every source merely offered, never a flat string or single triple.
- **Preference signal (AD-4, Story 1.9, not yet built):** out of scope here, but the same stop-selection call is the seam Story 1.9 later extends with the slider's continuous value plus `source_type`/`source_title` added to AI's candidate payload.
- **Secrets/config:** provider keys (OpenRouteService, OpenAI) are read server-side via the existing `.env`/`load_env()`/`get_api_key()` pattern `services.py`/`ai.py` already use; a new endpoint follows it, never invents a second secrets path or exposes a key to the browser.
- **Route geometry:** a new `services.py` function fetches the real polyline for the chosen stop order, following the existing `fetch_duration_matrix()`'s ORS-auth pattern.

## UX & Interaction Patterns

- The compact pill button and full-width primary button are genuinely separate components, never interchangeable - the project's most-repeated bug. Chips/pills signal selection via fill inversion, never a border/checkmark; every tappable control meets a ~44x44pt touch target.
- The stop list and stop-info overlay reuse one bottom-sheet pattern (swipe-down plus a real, visible close control). Every Jarrod appearance is a real cropped/composited region of the source PNGs, never hand-drawn or AI-regenerated; failure states use his sad pose plus plain language, never a red/alert color.
- First-time accessibility checks land in this epic: full keyboard operability with real `aria-label`s, alt text on stop photos, a WCAG contrast check on body-length ink-on-cream text, and dynamic-type checks on tightly-sized labels.

## Cross-Story Dependencies

- Backend before frontend: Stories 1.2 and 1.3 (both built) are hard prerequisites for 1.4; 1.4 is in turn a hard prerequisite for 1.5 and 1.6. Story 1.1 feeds 1.5's inputs but doesn't block 1.4.
- Should-tier sits on Must-tier: 1.7 and 1.8 need 1.4 and 1.5, and extend the request contract 1.4 must already support with `excluded_ids`/`retained_ids`; 1.9 needs 1.1's control plus 1.4's backend fields; 1.10 only needs 1.1 (independent of Epic 2's continuous tracking); 1.11 needs 1.5's stop-row component.
- Epic 1 is standalone: no dependency on Epic 2, 3, or 4.
