---
title: 'Manually remove or replace a stop'
type: 'feature'
created: '2026-10-22'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
context: []
baseline_commit: '0012b66c4d2e96727a8ded7fe064bb3ecd388b36'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Re-Jaunt deliberately rejects a whole route. A user who dislikes just one stop cannot replace it while keeping the other places.

**Approach:** Add a separate remove/replace control to each Route Review stop row. Exclude only the selected stop, retain every other stop, and search for exactly one replacement. Recompute walking order, geometry and walking-plus-dwell time before approval. Use the existing AI selection over constrained, time-feasible options. If none is suitable, keep the remaining stops as a shorter Jaunt and show an inline explanation; never redirect to the ordinary honest-fallback screen or regenerate the entire walk.

**Decision (2026-10-22, user-approved):** AI chooses only from feasible options containing every retained stop plus exactly one replacement; it may honestly reject all options.

**Decision (2026-10-22, user-approved):** When no suitable replacement exists, remove only the selected stop, preserve the remaining Jaunt, and show “No suitable replacement could be found with these settings.” in the stop-list position where the replacement would appear. Allow continuing with the shorter walk, or choosing Re-Jaunt. Do not add an unsuitable stop just to fill the gap.

**Decision (2026-10-22, user-approved):** These editing controls exist only in Route Review before Start my jaunt. When one stop remains, removal is disabled but a clearly labelled Replace action remains possible. This is a replacement-only attempt, not permission to remove the last stop unconditionally.

**Decision (2026-10-22, user-approved):** Replace means rejecting the selected stop, not keeping it as a backup. If that was the final remaining stop and no suitable replacement exists, show the existing sad-Jarrod honest fallback with input-adjustment options. Do not restore the rejected stop or offer an empty walk. When other accepted stops remain, keep the shorter Jaunt and inline explanation as decided above.

## Boundaries & Constraints

**Always:** preserve AD-2 stateless requests, AD-5 accumulated hard exclusions, AD-7 prevalidated option menus, source-grounded content, approved visuals and keyboard/focus behaviour. Every successful replacement contains all retained IDs plus exactly one new ID and the same stop count. Route order may change to remain time-feasible; retaining a stop does not lock its position. Keep retained places available even if refilling the nearest-place shortlist would otherwise displace them at its cap. Total shortlist size remains bounded. When no replacement is found and accepted stops remain, they keep their relative order and existing content/attribution. Refresh geometry, numbering and walking-plus-dwell totals for the shorter walk before enabling approval; do not leave the removed stop in the path or reuse the old totals. A two-stop walk can become a one-stop walk: this is an explicit removal-only exception to the existing minimum of two for newly generated routes, not a relaxation of ordinary planning.

**Never:** silently replace additional stops, claim a replacement was found when the result is a shorter walk, allow approval while planning, trust client-supplied place coordinates over the catalogue, treat retained IDs as a prompt-only hint, or add server sessions, frameworks, dependencies or a build step. No persistent cross-trip rejection UI (Story 3.3), photos, preference weighting, or general planner rewrite.

## I/O & Edge-Case Matrix

| Scenario | Input/state | Expected behaviour |
|---|---|---|
| Replace B | Current A/B/C, existing exclusions X | Request excludes X+B, retains A+C; successful result A+C+D in any feasible order |
| Replace again | Current A/C/D | Accumulated exclusions remain; only the newly selected stop is additionally rejected |
| Two-stop route | Retain one of two places | Search for that retained place plus one replacement; if none is suitable, allow the verified one-stop walk |
| One-stop route | User requests replacement of the final stop | Removal is disabled; reject the old stop and search for exactly one new stop. If none is suitable, show sad Jarrod; never restore the rejected stop or approve an empty walk |
| Maximum-size route | Retain six of seven | No eighth stop; revalidate the complete seven-stop walk |
| Retained place falls outside new nearest shortlist | Refilling after removal changes ranking | Keep that retained place within the bounded candidate set |
| Malformed retention | Non-array, duplicates, invalid IDs or excluded/retained overlap | Controlled 400 before provider calls; absent replacement intent preserves ordinary planning. Final-stop replacement requires an explicit replacement-mode signal: empty retained_ids must not accidentally trigger ordinary multi-stop generation |
| No time-feasible/relevant completion | Valid constrained search cannot return a suitable full route | If accepted stops remain, stay in Route Review with only the selected stop removed, remaining order/content preserved, updated path/time and an inline message; allow Start or Re-Jaunt. If none remain, show sad-Jarrod honest fallback |
| Technical failure | Non-2xx/network/parse failure | Do not claim no replacement exists; preserve the retained draft and retry constraints. Do not approve an unverified shorter path/time |
| Reload | Pending replacement or completed shorter route | Pending work recovers valid setup without an automatic request; a completed verified shorter walk resumes review without restoring the removed stop |
| Leave replacement recovery for setup/topic change | User deliberately changes inputs | Cancel retained-only replacement intent; preserve trip-wide exclusions |

</frozen-after-approval>

## Code Map

- `planner.py`: shortlist_candidates, plan_route, _enumerate_feasible_combinations and _build_ai_options. Add optional retained_ids and explicit replacement intent; reserve shortlist slots for retained catalogue records, then fill eligible alternatives. Limit constrained enumeration to retained-count+1, checking retention before route-order calculations; leave ordinary enumeration unchanged. Explicit replacement intent with zero retained IDs searches for exactly one new stop, not an ordinary multi-stop route. If no replacement is time-feasible or AI returns none_suitable, calculate the retained-only shorter route when retained stops exist, using the same authoritative routing data and preserving their relative order; allow the editing-only one-stop case. With zero retained stops, return honest infeasibility for sad-Jarrod fallback instead. Never convert a provider error into an honest no-replacement result.
- `app.py`: _validate_plan_request and api_plan. Validate replacement-mode type, retention cardinality (zero to six in replacement mode), unique known ready IDs, exclusions conflict and request size. Thread optional retention to planner; preserve ordinary planning/Re-Jaunt response shapes. Replacement mode needs an explicit machine-readable distinction between replacement-found and retained-only-shorter success, with canonical stops/geometry/totals for either; do not classify by parsing reason text.
- `static/app.js`: renderStopList, startRoutePlanning, prepareSetupState and recovery handlers. Separate row details and replacement buttons (siblings, not nested buttons). Capture rejected/retained IDs and content before starting. Replacement-found updates the route; retained-only success updates the existing review with the shorter walk and inline message instead of showHonestFallback(). Honest failure with no retained stops uses showHonestFallback(). Accumulate the rejected final stop in exclusions before attempting replacement, just like other rejected stops. Persist verified shorter review state so reload is valid. Keep retry constraints without restoring a rejected route; deliberately editing setup cancels replacement intent. Coordinate overlays so the inline explanation is actually visible to the user.
- `static/style.css`: extend current stop-row layout with a ~44px labelled remove/replace target using existing tokens. Add the inline no-replacement text in the relevant row position, announced accessibly without a fake stop, photo placeholder or broken marker. Keep details opening, sheet dismissal and focus restoration working.
- `tests/test_planner.py`, `tests/test_app.py`, `tests/frontend-recovery.test.cjs`: constrained search, validation and real frontend event/storage/request regressions.

## Tasks & Acceptance

**Execution:**
- [x] `planner.py` — implement constrained AI selection and retained-only feasibility/route calculation without losing retained places to the shortlist cap or weakening ordinary minimum-stop rules.
- [x] `app.py` — validate/thread retention and expose an explicit retained-only outcome in replacement mode; ordinary responses stay compatible.
- [x] `static/app.js`, `static/style.css` — add accessible replacement controls and the inline retained-only outcome, updated route/time, approval gating and valid review/reload persistence. Reflect the removal-only one-stop rule in frontend validation.
- [x] Python and native Node tests — cover the matrix, ordinary planning/Re-Jaunt compatibility and recovery; update test instructions if needed.

**Acceptance Criteria:**
- Given A/B/C, when B is replaced, then A and C remain, B is excluded and exactly one new stop appears.
- Given a replacement result, when approval is offered, then its full walking-plus-dwell time fits the same requested budget.
- Given A/B/C, when B is removed and no suitable replacement exists, then review keeps A/C in their existing relative order and content, shows the inline explanation, updates geometry/time, and allows Start or Re-Jaunt without ordinary fallback navigation.
- Given a two-stop walk, when one is removed without replacement, then the verified one-stop walk can be approved and survives reload.
- Given one remaining stop, when reviewing it, then Remove is disabled and Replace remains keyboard-accessible.
- Given replacement of the final stop, when no suitable new stop is found, then the rejected stop stays excluded and sad Jarrod appears without a startable empty walk.
- Given a technical failure, when retrying, then retained/excluded constraints survive and no unsupported no-replacement claim or unverified approval is offered.
- Given only keyboard interaction, when navigating a stop row, then details and replacement controls are separately reachable, clearly labelled and operable without activating each other.

## Implementation Notes

Implementation contract: `replacement_mode: true` explicitly requests exactly one new stop alongside ordered `retained_ids` (zero to six). Successful replacement responses include `replacement_outcome: "replacement_found"` or `"retained_only"`; ordinary response fields are unchanged. Retained-only order follows the supplied retained IDs, with catalogue coordinates, matrix-derived walking-plus-dwell totals and freshly requested geometry. Replacement geometry failures remain technical errors so approval never uses an unverified shorter path. Pending replacement state persists retained content and intent in the existing setup phase; verified shorter results persist in review.

Planning context (before implementation): existing build/architecture/source review established the seams above. Proposed implementation keeps retained stop stories/attribution visible unchanged on success by merging those two fields by retained ID from the current in-memory route snapshot; other metadata/order/timing/geometry come from the new canonical backend result. Reuse the existing backend content pipeline initially rather than introducing a content cache or trusting client text. If this creates meaningful implementation scope or changes desired content behaviour, resolve before coding.

The user's revised failure policy supersedes the initial fallback proposal. Retained-only review is now an intentional user-facing outcome, not an incomplete replacement masquerading as a full route. No new persistent phase is required, but one-stop review validation, response metadata and notice persistence must be handled explicitly. Keep general Re-Jaunt recovery unchanged. The user has resolved last-stop handling. The user approved implementation on 2026-10-22; completion evidence is recorded below.

## Spec Change Log

2026-10-22: User approved constrained AI selection and replaced the ordinary-fallback proposal with a shorter Jaunt plus inline notice. Updated intent, matrix, API/planner/frontend seams and acceptance criteria together; removed the superseded two choices. Identified the final-stop boundary as the remaining question. Planning only; no feature code changed.

## Verification

Run Python unittest, native Node frontend tests, node --check and diff checks. Add fixtures with an excluded nearest place displacing a retained stop at the shortlist cap, two-to-one and final-stop boundaries, seven-stop routes, time-infeasible and AI-none_suitable replacement results, retained-only path/time/order correctness and reload, technical failures distinguished from honest lack of replacement, infeasible retained combinations, overlap/duplicates, repeated replacement, ordinary Re-Jaunt, technical retry and reload. Perform real browser checks for row hit targets, keyboard/focus, scrolling and successful route rendering; do not infer these from Python checks. No paid API test runs before implementation approval.

2026-10-22 clarification: user approved disabling final-stop removal while permitting final-stop replacement. The earlier proposal to disable all further changes at one stop is superseded. Final replacement has zero retained stops, so its request mode must be explicit and its search must still produce exactly one new stop rather than invoke ordinary >=2-stop generation. Sad-Jarrod fallback when that replacement fails was proposed by the user as a question and awaits confirmation.

2026-10-22 final decision: user confirmed Replace rejects the selected stop. Removed the resolved Open Questions section and reconciled the final-stop matrix, request-mode seam, planner outcome and acceptance criteria. Zero retained IDs in explicit replacement mode requests one new stop; honest failure shows sad Jarrod. Existing ordinary planning minimum and shorter-route inline behaviour remain unchanged.

## Review Triage Log

2026-10-22, BMAD three-layer review; all layers ran independently against the staged diff. Each finding checked against actual code/tests. Final patches remained within the approved feature contract.

1. Blind: duplicate Remove/Replace operations — false as a correctness claim. The approved removal control attempts replacement; the user separately required final-stop Remove disabled with Replace still enabled. Both accessible labels/handlers implement those semantics. No unapproved change to direct-removal behaviour or last-stop controls made.
2. Blind: malformed replacement geometry accepted before content generation — medium, patched. Successful provider return values can be null/empty/invalid, not only exceptions. Validate nonempty finite in-range coordinate pairs and return 503 before generating content; endpoint regressions cover these cases. Ordinary geometry degradation remains unchanged.
3. Blind: replacement response-rejection branches unverified — medium, patched. Added missing-retained, excluded/duplicate/null stop, wrong count, reordered retained-only, missing geometry and over-budget response cases; each checks technical failure and identical retry constraints.
4. Blind: repeated editing not exercised — medium, patched. Consecutive replacement-found and retained-only edits now assert accumulated exclusions, retained snapshots/content and notice reset.
5. Blind: notice text/position/rerender unverified — medium, patched. DOM stub now clears children on innerHTML assignment; tests assert inline text, correct middle/end position and no duplication on rerender. Real Chrome check independently confirms placement and role=status.
6. Blind: browser evidence missing — medium, addressed. Isolated real headless Chrome with intercepted planning responses passed at 390x844 and 320x568: sibling details/Replace/Remove tab order, >=44px controls, list scrolling, no horizontal overflow, retained-only notice, review reload, last-stop control state, sad fallback, successful replacement and identical technical retry. No paid API calls or normal browser-profile changes.
7. Blind: stale task/artifact status — low, addressed during normal finalization. Marked completed tasks and distinguished historical planning notes from current completion evidence; frozen approved decisions unchanged.
8. Blind: README test inventory stale — low, patched. README now states 280 Python tests and 27 frontend tests with current coverage and layout limitations.
9. Edge: null stop dereferenced before validation — medium, patched. Validate result stop array/elements before reading IDs; null-stop regression reaches technical recovery rather than stranding loading.
10. Edge: retained record disappears/loses coordinates between request validation and planning — medium, patched. Check requested retained membership in the usable planning shortlist before provider calls. Regression covers missing and coordinate-less retained records, preventing an unrelated substitution or KeyError.
11. Verification gap: replacement geometry error branch not tested — medium, patched. Endpoint tests exercise network/malformed-provider exceptions and unusable geometry, require JSON 503 and assert no content-generation call; existing ordinary-degradation cases still pass.

No new issue deferred. Existing shared deadline, off-path-stop investigation, broader regression coverage and keyless-demo work remain separate.

## Completion Verification

280 Python tests and 27 native Node tests pass; node --check and diff checks pass. Test classes remain registered for both unittest discovery and direct execution. Matrix coverage: retained/exact-count and repeated-edit tests; two-to-one/final-stop/seven-stop tests; retained-shortlist-cap case; invalid/overlap/unknown retention cases; no-time-feasible and AI-none_suitable retained-only cases; technical/geometry failure and retry cases; pending/completed-shorter reload cases; setup-exit cancellation case. Real-browser keyboard/control/layout checks supplement, rather than replace, those automated tests.

Browser planning POSTs were intercepted with fixtures; backend behaviour was checked through Flask test-client/planner tests with mocked providers. No live-provider quality or real outdoor walk claimed. Temporary screenshot /private/tmp/jaunt-story18-phone.png was visually inspected; it is a local verification artifact, not a committed design asset.
