---
title: 'Epic 3: Remember and Vary (Stories 3.1-3.4)'
type: 'feature'
created: '2026-10-26'
status: 'done'
route: 'batched'
review_loop_iteration: 0
baseline_commit: 'e753dd2'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

User requested Epic 3 (all 4 stories) built as one combined pass, same approach as Epic 2, given reduced available time for story-by-story review - an explicit, repeated process choice, not a default.

**Scope per `_bmad-output/planning-artifacts/epics.md`'s Epic 3 (lines 837-986), all Should-tier:**
- **3.1:** catch-up before summarizing - a sheet shown when "End Jaunt" is tapped, retroactively marking forgotten stops Visited, before any state clears.
- **3.2:** AI-generated walk summary - grounded strictly in Visited stops, reusing Story 1.3's grounding-check infrastructure; a plain-list fallback when generation fails, an honest empty message when nothing was Visited.
- **3.3:** local visit history and favourites - the full AD-6 Engagement State lifecycle (proposed/opened_engaged/visited_completed), favouriting, and a "not interested" hard-rejection action - extending Story 2.3's existing `jaunt_visit_history` key and schema.
- **3.4:** repeat-use route variety - visit history sent as a soft AI-weighting signal on every planning request, deprioritizing previously-visited places without ever excluding a favourite.

</frozen-after-approval>

## Design decisions made during this build (genuinely open per the stories themselves)

- **Story 3.1's "proceed to either Create summary or end without a summary":** both paths converge on the exact same next step - `finishWrapUp(attemptSummary)` - differing only in whether the AI call is attempted. "End without a summary" with >=1 Visited stop still shows the plain list (the same screen Story 3.2's generation-failure case uses), not a bare acknowledgment - the user still gets to see and favourite what they visited without spending an AI call. Zero Visited stops shows the honest empty message regardless of which button was tapped.
- **Story 3.1's catch-up sheet is a pure modal**, not a phase transition - closing it (the X) leaves `trip.phase` at `"walking"` unchanged, exactly like every other sheet in this app (stop-list, credits). `trip.phase` only moves to `"wrapping_up"` once the user actually commits to ending (either catch-up button), matching AD-2's "end trip fires at wrap-up completion, not the initial hamburger-tap" instruction precisely - the hamburger tap only opens a dismissible sheet.
- **AD-2's "a refresh mid-wrap-up still recovers correctly" is honored by falling back, not by full-fidelity resume.** A reload while `trip.phase === "wrapping_up"` (the brief window between a catch-up button and the walk-complete screen - normally a few seconds, one AI call) resumes to the walking screen, not the exact sub-screen that was showing. The full trip (stops, geometry, visited state) is never at risk of loss either way - only the "which wrap-up sub-screen" position is lost on this rare reload. Building full snapshot-based resume for a multi-second window was judged disproportionate scope.
- **Story 3.2's `/api/summary` is a new, separate, stateless endpoint** (not folded into `/api/plan`) - the frontend sends the Visited stops' own data (already held client-side from the original plan response), matching AD-2's stateless-backend rule exactly the same way `/api/plan` itself never remembers a prior request.
- **Story 3.3's "not interested" control placement** (explicitly left open by the story) is a quiet text-link at the very end of the stop-content overlay, deliberately separated from the Visited badge near the top, so the two can never be confused or mis-tapped together. Available in every context the overlay is shown (pre-walk preview or during a walk) - unlike Visited, which stays context-gated to an active walk only. A real toggle, not one-way, matching the Visited control's own established pattern (user's explicit preference, Story 2.3's fix).
- **Story 3.3's retention/reset decision (PRD Open Question 7, required to be explicitly decided):** visit history never expires, and no user-facing clear/reset control is built in V1. Nothing in any story's AC asks for one; building it anyway would be scope invention.
- **Story 3.3's `rejected` ids are merged into the existing `excluded_ids` field**, not sent as a separate backend field - from the backend's perspective both are just "ids to hard-exclude," the exact same mechanism AD-5/AD-6 both describe. This reuses Story 1.7's already-proven exclusion path entirely; no backend change was needed for `rejected` specifically.
- **Story 3.4's `visit_history` signal only reaches `ai.select_stops()`/`build_prompt()`**, not `ai.discover_candidates()` - the latter has its own separate, simpler prompt shape and doesn't call `build_prompt()` at all; forcing the signal in there would mean inventing a second prompt-injection point the existing code has no real hook for.

## Implementation Notes

**Backend (`ai.py`, `planner.py`, `app.py`) - Story 3.2 and 3.4 only; 3.1 and most of 3.3 are frontend-only.**

- `ai.py`: `build_prompt()`/`select_stops()` gained a `visit_history` parameter, threaded exactly like `preference` already is, with its own guidance paragraph (deprioritize `visited_completed` more than `opened_engaged`/`proposed`; a favourite is never excluded but "never excluded" is not "preferred"). New `generate_walk_summary(visited_stops)` reuses `check_grounding_semantic()` **unchanged** (its own docstring already said "Epic 3 can call unchanged for a single walk summary" - confirmed this was deliberately prepared, not retrofitted) via a new `_call_walk_summary()` following the exact same HTTP/schema/error pattern as every other call in the module.
- `planner.py`: `plan_route()`/`_plan_shortlist()` gained `visit_history`, threaded through to `ai.select_stops()` the same way `preference` is, including through the discovery-recovery retry path.
- `app.py`: `_validate_plan_request()` gained `visit_history` validation (list of `{id, state, favourited}`, bounded the same defensive way `excluded_ids` already is; `rejected` is deliberately read by the frontend instead, see above). New `/api/summary` endpoint + `_validate_summary_request()`, same `PlanRequestError`/400-before-any-AI-call contract as `/api/plan`. `MAX_CONTENT_LENGTH` raised from 4096 to 65536 bytes to accommodate both the larger `visit_history` field and the new endpoint's stop content.

**Frontend (`static/app.js`, `templates/index.html`, `static/style.css`).**

- Story 3.3: `recordEngagement(id, minState)` (upgrade-only, ordinal-ranked) now runs on every successful plan (each stop -> at least `proposed`) and every `openStopOverlay()` call (-> at least `opened_engaged`), live as those screens are used - distinct from `setStopVisited()`'s existing explicit, both-directions toggle. New `isStopFavourited`/`setStopFavourited`, `isStopRejected`/`setStopRejected`/`rejectedStopIds()`. `startRoutePlanning()`'s payload now merges `rejectedStopIds()` into `excluded_ids` and sends `visit_history` (state + favourited only, rejected entries dropped since they're already hard-excluded).
- Story 3.1: new `#catchup-sheet-wrap` (reuses the existing `.sheet-wrap`/`.confirm-sheet` shell), `renderCatchupList()` builds one toggleable row per stop (checked/unchecked + "forgot?" hint, ported from the approved mockup's own catch-up-row markup/CSS).
- Story 3.2: new `#screen-walk-complete`, one shell for all three endings (`showWalkComplete(outcome, {summary, visitedStops})`). `finishWrapUp(attemptSummary)` is the single function both catch-up buttons call. Heart button markup/behavior ported from the approved mockup (`flow-03-walk.html`) - fill `none`/`#1E4A3A` is the entire state difference, no new icon.
- `isValidReviewingShape()`/`isValidTrip()` extended to accept `phase === "wrapping_up"` (AD-2's own named third phase value), reusing the identical shape `"reviewing"`/`"walking"` already use - no new required fields were added to the trip object for Epic 3 (summary text/outcome are never persisted; see the resume-simplification decision above).

## Real bugs found and fixed during this build (before any user review)

1. **`buildHeartButton()`'s toggle handler called `btn.querySelector("path")`**, which doesn't exist on a dynamically-`innerHTML`'d element in the test harness (and is generally a fragile pattern). Caught while writing the regression test for heart-toggling, not live. Fixed by extracting `heartSvgMarkup(favourited)` and re-setting `innerHTML` wholesale on toggle instead of mutating a queried child - simpler and avoids the dependency entirely.

## Verification

Added 33 new tests across the suite: 11 in `tests/test_ai.py` (visit_history embedding/guidance in `build_prompt`, threading through `select_stops`, `generate_walk_summary`'s grounding/failure/empty-input paths, `_call_walk_summary`'s HTTP-boundary behavior), 2 in `tests/test_planner.py` (visit_history threads through `plan_route` to `ai.select_stops`, normalizes `None` to `[]`), 8 in `tests/test_app.py` (`visit_history` validation on `/api/plan`, `rejected` stripped before reaching `planner.plan_route`, the new `TestApiSummary` class), 12 in `tests/frontend-recovery.test.cjs` (proposed-on-plan/opened_engaged-on-open/never-downgrades-Visited, Not-Interested toggle across both phases, rejected-merged-into-excluded_ids-and-dropped-from-visit_history, catch-up row toggle, AI-summary-success/generation-failure/network-failure/zero-visited-skips-the-call, favourite-persists-and-reaches-the-next-request, and a UX-DR4/UX-DR5 regression check using this project's own established raw-HTML-string pattern for verifying a static CSS class, since the harness's generic element stubs don't track real `class` attributes). All 332 Python tests and 112 frontend tests pass (up from 311/99 before this epic).

Required two test-harness extensions beyond what Story 1-2's work already added: a `/api/summary` branch in the shared `fetch` stub (mirroring the existing `/api/plan`/`/api/places` branches, with its own `respondSummary`/`summaryNetworkError`/`summaryRequests` helpers) and nothing else - the existing `visitHistorySeed`/localStorage machinery from Epic 2 covered everything else needed.

Live-verified end to end via Playwright against the running LAN server, including the full real user flow: approved a route, marked one of two stops Visited directly and left the other un-marked, opened the hamburger menu, tapped End Jaunt (confirmed the catch-up sheet opens with the correct checked/unchecked-with-"forgot?" state per stop and that nothing is cleared yet - `trip.phase` still `"walking"`), tapped the unchecked row to retroactively mark it Visited, tapped "Create summary of visited stops" with `/api/summary` intercepted client-side to avoid spending a real AI credit (confirmed the real text renders, both stops appear with their own favourite-heart button, "Jaunt complete" heading, `.btn-pill` "Back to start" not `.btn-full`), favourited one stop and confirmed `isStopFavourited()` reflects it, tapped "Back to start" and confirmed the active trip fully resets to a fresh default while the favourite survives in the separate `jaunt_visit_history` key. Separately verified the zero-Visited path end to end (End Jaunt -> catch-up with nothing checked -> "End without a summary" -> the honest "Nothing was marked Visited this time" message, no stop list, no AI call attempted) and the `rejected`-merges-into-`excluded_ids` logic directly.

Not yet done: a real (non-intercepted) `/api/summary` call against the live OpenAI-backed endpoint - avoided to not spend additional provider credits beyond what this session's debugging already used, consistent with this project's established pattern for this kind of verification. The endpoint's own correctness (request validation, `ai.generate_walk_summary()`'s grounding/fallback behavior) is covered by the Python test suite instead, which mocks only the HTTP boundary (`requests.post`), not the orchestration logic above it.
