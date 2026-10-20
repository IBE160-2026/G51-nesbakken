---
title: 'Generate a proposed Route via a new planning endpoint'
type: 'feature'
created: '2026-10-21'
status: 'review'
route: 'dispatch'
review_loop_iteration: 0
context: []
baseline_commit: '302c49b2f011503229eb3d27557decccc4c47b15'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `planner.py`'s `plan_route()` already does real stop selection, but nothing wraps it into one HTTP request/response: there's no route geometry, no content generation wired in, no `none_suitable` honest-fallback outcome (AD-7's schema was never actually built), and a real bug - `plan_route()` currently swallows a genuine `ai.AiFatalError` into the same shape as ordinary infeasibility, so a real credentials/quota failure would look identical to "no suitable walk" to any caller.

**Approach:** A new stateless `POST /api/plan` endpoint in `app.py` that validates input immediately, calls `planner.plan_route()` (fixed to re-raise `AiFatalError`), fetches real route geometry from a new `services.py` function, runs `ai.generate_stop_content()` for the chosen stops, and returns one complete response - or a clearly-distinguishable honest/technical failure. Three outcomes, verified against the real ORS API before being written here (not assumed): zero feasible combinations and AI's `none_suitable` both return the same honest `200 {"feasible": false, "reason": ...}` shape (a real `reason` string is what actually distinguishes them to a reader - nothing in this story's AC asks for a separate machine-readable field between these two honest cases); a genuine AI/service failure is a real non-2xx, never collapsed into that shape.

## Boundaries & Constraints

**Always:** Malformed/invalid input (non-numeric or out-of-range coordinate, time outside 30-120, unrecognized topic, oversized/malformed body) is rejected before `plan_route()` is called at all - before any routing-provider or AI call. The endpoint is fully stateless - no server memory of a request survives past its response (architecture AD-2). Content generation runs for every stop in the chosen route, synchronously, before the response returns (architecture AD-3) - `ai.generate_stop_content()` never raises, so this can't itself become a new failure mode. `AiFatalError` is a real non-2xx status, never the `{"feasible": false}` shape. A route-geometry fetch failure, by contrast, never fails the request (user's explicit choice, 2026-10-21) - it degrades to `geometry: null` on an otherwise-normal `200` success response, caught and logged, never raised.

**Never:** No change to `ai.py`'s content-generation functions (Story 1.3, done) beyond calling them. No Trip Setup UI, Route Review UI, or any other frontend work - backend-only, matching the story's own explicit split. No change to the catalogue import pipeline. No new persistent storage anywhere - the response is the only record of this result.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Valid request, feasible route | Real start point, time, topic | `200`, complete route: stops in walking order, each with generated content + attribution list, real route geometry, total time | N/A |
| Zero feasible stop combinations | e.g. start point far from any candidate, or time too short for 2 stops | `200`, `{"feasible": false, "reason": "..."}` | N/A |
| AI judges every feasible option irrelevant | All offered options time-feasible, none relevant to the topic | `200`, `{"feasible": false, "reason": "..."}` - AI's own `none_suitable_reason`, not a generic message | N/A |
| Genuine AI/service failure | Invalid credentials, exhausted quota (`ai.AiFatalError`) | Real non-2xx status, distinct shape from the two honest cases above | N/A |
| Malformed coordinate | Non-numeric, or outside real lat/lng bounds | Rejected immediately, before `plan_route()` runs | `400`-class response, no routing/AI call made |
| Time outside 30-120 | e.g. `20` or `150` | Rejected immediately | Same as above |
| Unrecognized topic string | Not one of history/architecture/public_art/surprise_me | Rejected immediately | Same as above |
| Oversized/malformed request body | Not valid JSON, or absurdly large | Rejected immediately | Same as above |
| Route geometry fetch fails after a feasible route is found | ORS directions call errors (network, rate limit) | **Resolved, user's explicit choice (2026-10-21):** the request still succeeds - `200` with the real stops/content/total-time intact and `geometry: null`. Matches AD-3's existing "never fail an otherwise-good route over one add-on piece failing" philosophy | Caught, logged; never raised to the caller |

</frozen-after-approval>

## Code Map

- `planner.py` -- `plan_route()` (line ~292): the `except ai.AiFatalError as exc:` block (line ~357) currently calls `_plan_failure()`, collapsing it into the same shape as ordinary infeasibility - must instead re-raise (mirroring how `app.py`'s existing `CatalogueError` already propagates to its caller). `select_stops()`'s return value also needs to carry AI's `none_suitable` signal distinctly from a real `option_key` - see `ai.py` below. `MIN_REQUESTED_MINUTES`/`MAX_REQUESTED_MINUTES`/`ABSOLUTE_MAX_STOPS` (lines 29-30, 43) are the existing bounds to reuse for upfront validation, not reinvent.
- `ai.py` -- `SELECTION_SCHEMA`/`SYSTEM_PROMPT` (lines ~27-58, `select_stops()` line ~203): needs AD-7's `none_suitable` outcome. Add a `none_suitable_reason` string field (always present, strict-mode-compatible - empty when a real option is chosen, a real one-line reason when `selected_option` is the literal string `"none_suitable"`), instructed in `SYSTEM_PROMPT`. Matches the existing `used_evidence_ids` pattern from Story 1.3 (an always-present field whose meaning depends on another field's value). `_build_ai_options()` in `planner.py` (not `ai.py`) also needs AD-7's menu-diversity coverage pass - see below.
- `planner.py` -- `_build_ai_options()` (line ~254): currently a plain top-N-by-`budget_usage_ratio` slice of `feasible_combos`. AD-7 requires a coverage pass first - every stop appearing in at least one feasible combination must appear in at least one offered menu option, before the remaining slots fill by budget-usage ratio as today.
- `services.py` -- `fetch_duration_matrix()` (line 39) is the pattern to mirror for a new `fetch_route_geometry(ordered_points)`: same `.env`/`get_api_key()` plumbing, same `requests.post`/`raise_for_status()` shape. **Verified against the live ORS API before writing this spec** (not assumed): `POST https://api.openrouteservice.org/v2/directions/foot-walking/geojson` with `{"coordinates": [[lon,lat], ...]}` returns a real GeoJSON `FeatureCollection`; `body["features"][0]["geometry"]["coordinates"]` is the real walked `LineString` as `[lng, lat]` pairs - directly usable by the frontend's existing MapLibre/GeoJSON rendering approach (architecture AD-1), no polyline-decoding needed on either side. The plain (non-geojson) `/v2/directions/foot-walking` endpoint was also tested and returns an encoded polyline string instead - deliberately not used.
- `app.py` -- current state is Sprint-2-level (`/` and `/api/places` only, see `CatalogueError`/`503` pattern to mirror for the new `AiFatalError` -> non-2xx mapping). New `POST /api/plan` route goes here. No canonical topic-list constant exists anywhere in the Python code yet - add `VALID_TOPICS` to `planner.py` (where `shortlist_candidates()`'s topic semantics already live) for the endpoint to import and validate against, rather than inventing a second list.
- `planner.py` -- `plan_route()`'s existing return shape (`order`, `total_minutes`, `shortlist`, `selected_ids`, etc.) has no `content`/`attribution`/`geometry` fields - the endpoint layer (not `plan_route()` itself) calls `ai.generate_stop_content()` and the new geometry function after `plan_route()` succeeds, keeping `planner.py` focused on selection (as it already is) rather than growing new HTTP-response-shaping responsibilities.

## Tasks & Acceptance

**Execution:**
- [x] `planner.py` -- re-raise `ai.AiFatalError` from `plan_route()` instead of collapsing it into `_plan_failure()`
- [x] `planner.py` -- add `VALID_TOPICS = {"history", "architecture", "public_art", "surprise_me"}`
- [x] `ai.py` -- add `none_suitable_reason` to `SELECTION_SCHEMA`, update `SYSTEM_PROMPT` to instruct AI when/how to use the literal `"none_suitable"` value, update `select_stops()`'s return to carry both fields
- [x] `planner.py` -- `_build_ai_options()`: add the coverage pass (every stop in at least one feasible combo gets a guaranteed menu slot) before the existing budget-usage-ratio ranking fills the rest; `plan_route()`: handle `none_suitable` as its own honest-fallback branch, distinct in code from "zero feasible combinations" even though both produce the same wire shape
- [x] `services.py` -- `fetch_route_geometry(ordered_points)` using the verified GeoJSON directions endpoint, same auth/error-handling pattern as `fetch_duration_matrix()`
- [x] `app.py` -- request validation (coordinates, time range, topic, body shape) before calling `planner.plan_route()`; `POST /api/plan` orchestrates `plan_route()` -> (on success) `fetch_route_geometry()` + `ai.generate_stop_content()` -> final JSON response; maps a propagated `AiFatalError` (and a routing-provider failure) to a real non-2xx status
- [x] `tests/test_planner.py`/`tests/test_ai.py`/`tests/test_app.py`/`tests/test_services.py` -- 26 new tests (224 baseline -> 250): `AiFatalError` propagates out of `plan_route()` (not collapsed); `none_suitable` reaches `plan_route()` as its own outcome (not a retry); a hand-constructed coverage-pass case proves a low-ranked stop is rescued; each of the malformed-input cases rejected with the relevant external call never made; a genuine `AiFatalError` and a routing-provider failure both map to 503 at the endpoint; a successful response's exact shape (stops, content, attribution, geometry, total time); geometry-fetch failure degrades to `null` without failing the request

**Acceptance Criteria:**
- Given a real request end-to-end (live ORS + live OpenAI), when `POST /api/plan` is called, then the response includes real generated content, real attribution, and real route geometry - not mocked, verified directly
- Given the three outcome types, when each is triggered, then they are distinguishable exactly as specified: two honest `200`s (differing only in `reason` text) and one genuine non-2xx
- Given the full test suite after this story, when run, then it stays green

## Implementation Notes

**Files changed:** `ai.py` (`none_suitable_reason`, `NONE_SUITABLE` constant, `select_stops()` now returns a dict); `planner.py` (`AiFatalError` re-raised, `VALID_TOPICS`, AD-7 coverage pass in `_build_ai_options()`, `none_suitable` handling in `plan_route()`); `services.py` (new `fetch_route_geometry()`); `app.py` (new `POST /api/plan`, `_validate_plan_request()`/`PlanRequestError`); `tests/test_ai.py`, `tests/test_planner.py`, `tests/test_services.py`, `tests/test_app.py` (new/updated tests across all four, including fixing every existing test that mocked `ai.select_stops()`'s old bare-string return shape).

**Verified, not assumed:** full suite green at 250 tests (224 baseline + 26 new). A real end-to-end `POST /api/plan` against the running app with live ORS + OpenAI credentials returned a complete 7-stop route: real generated content and correct attribution per stop, a real GeoJSON walking-path LineString, `total_minutes` 59.97 against a 60-minute request. Separately verified live: the honest zero-feasible-combinations fallback (`200`, a real reason, requesting from a start point - Melbourne - with no nearby candidates) and all three malformed-input rejections (bad topic, out-of-range time, non-JSON body), confirming each returns `400` before any external call. The `none_suitable`/AD-7-coverage-pass/`AiFatalError`-propagation/geometry-degradation paths were verified via targeted mocked tests rather than live, since forcing AI to judge every real option unsuitable, or forcing a live credentials failure, isn't practically reproducible on demand - each has its own test asserting the exact mechanism (e.g. the coverage-pass test hand-constructs combos so the outcome is fully predictable, rather than relying on hard-to-predict real combinatorics).

**Design calls made where the spec left room:** `AiFatalError`/routing-provider failures both map to `503`, matching the existing `CatalogueError -> 503` convention already in `app.py` - no new status code invented. `select_stops()`'s return changed from a bare string to a dict (`{"selected_option", "none_suitable_reason"}`) - a real, deliberate break from its old shape, needed so `none_suitable_reason` could travel with the selection without inventing a second return channel; every existing caller/test was updated, not left on the old shape.

## Spec Change Log

## Review Triage Log

## Design Notes

**Why both honest-fallback outcomes share one wire shape.** epics.md's AC text for `none_suitable` says only that "the endpoint treats this as FR-9's relevance-based honest fallback - distinct from zero feasible combinations" - it does not ask for a new response field distinguishing the two. Re-using the existing `{"feasible": false, "reason": ...}` shape for both, with a real, specific `reason` string per case, is the minimal design that satisfies "distinct" without inventing a field no requirement asks for. If a future story needs to distinguish them programmatically (not just by reading `reason`), that's a real, separate decision to make then - not assumed here.

**Route geometry endpoint choice, verified live, not guessed.** OpenRouteService's plain directions endpoint returns an encoded polyline string by default; the `/geojson` variant returns a real GeoJSON LineString directly. Confirmed both against the live API before writing the Code Map above. The GeoJSON variant was chosen because it needs no decoding step on either side and matches the frontend's existing GeoJSON/MapLibre rendering approach (AD-1) exactly.

## Verification

**Commands:**
- `python3 -m unittest discover -s tests` -- expected: all tests pass
- A real (not mocked) `POST /api/plan` call against the running Flask app, with live ORS/OpenAI credentials -- expected: a complete, real response; manually inspect stop content, attribution, and geometry
- Trigger each of the three outcomes for real where practical (a request with an impossibly short time for zero-feasible; a genuine request for the honest-fallback/none_suitable path is harder to force live, so that one may need a mocked `ai.select_stops()` instead) and confirm the response shape/status code for each

**Manual checks (if no CLI):**
- Confirm a malformed request (bad topic string, out-of-range time) never reaches the ORS or OpenAI calls - check for their absence in logs/timing, not just the response code
