---
title: 'Re-Jaunt'
type: 'feature'
created: '2026-10-22'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
context: []
baseline_commit: '2a917f075e047f4233152902fcb4206f0fc2b209'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Route Review only ever offers one path forward - approve, or back out to Trip Setup entirely. A user who dislikes the specific proposed route but still wants the same starting point/time/topic has no way to ask for a different one without restarting Trip Setup from scratch.

**Approach:** Add a Re-Jaunt action, displayed as an equal-weight button pair with the existing approve action (architecture UX-DR6/DESIGN.md: forest-outline "Re-Jaunt" beside forest-fill "Start my jaunt" - replacing the current single full-width approve button in `.review-panel`). Tapping it adds every stop from the currently-displayed route to a new, accumulating `excluded_ids` list on the trip, re-runs planning with the same start/time/topic, and shows the result exactly like any other planning attempt - a new route on success, Story 1.6's existing honest-fallback screen when nothing feasible remains. `excluded_ids` is a real hard filter threaded through `planner.py`'s shortlisting (architecture AD-5) - this is this story's one backend change, everything else is frontend.

## Boundaries & Constraints

**Always:**
- `excluded_ids` is a hard filter applied in `shortlist_candidates()` before any routing/AI call sees the candidates - never a soft AI-prompt hint (AD-5).
- Re-Jaunt excludes every stop from the just-rejected route, not just that specific combination (AD-5's deliberate "clean break" - a looser alternative-search is explicitly not wanted here).
- The frontend resends the full accumulated `excluded_ids` list on every planning request once any exist, never a delta - the backend is stateless (AD-2/AD-5).
- `excluded_ids` lives in the active-trip `localStorage` object alongside the rest of the trip, validated the same way every other trip field already is (AD-2's existing safe-reset-on-bad-shape path covers it too, nothing new needed there).
- Re-Jaunt and the approve action render as a real equal-weight pair (two `flex: 1` buttons, same row) - never one visually dominant over the other (UX-DR6).
- Re-validates time feasibility the same way the original request did - this falls out naturally from re-running `plan_route()`, not a separate check.

**Never:**
- Do not build the separate "remove/replace one stop" feature (Story 1.8's own `retained_ids` mechanism) - Re-Jaunt only ever excludes the whole route, never a subset.
- Do not add any new UI for clearing `excluded_ids` manually - per AD-5 it clears only when the whole trip object resets (e.g. a fresh trip), not introduced or special-cased by this story.
- Do not change `/api/plan`'s existing required fields or response shape - `excluded_ids` is a new optional request field only.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| First Re-Jaunt tap | A displayed route with stops `[A,B,C]`, `trip.excluded_ids` empty/absent | `trip.excluded_ids` becomes `[A,B,C]`, persists, a new `/api/plan` call sends that list, loading screen shows | N/A |
| Second Re-Jaunt tap | New route `[D,E]` now displayed, `trip.excluded_ids` already `[A,B,C]` | `trip.excluded_ids` becomes `[A,B,C,D,E]` (accumulated, not replaced), full list resent | N/A |
| No feasible alternative after exclusion | `/api/plan` returns `{feasible:false, reason:"..."}` | Story 1.6's existing honest-fallback screen shows, unchanged | `reason` logged via `console.error`, never shown |
| `excluded_ids` omitted entirely (first-ever planning request, no Re-Jaunt yet) | Request has no `excluded_ids` field | Backend treats it as an empty exclusion list, behaves exactly as it does today | N/A |
| `excluded_ids` present but malformed (not a list of strings) | e.g. `excluded_ids: "abc"` or `[1,2]` | `400` with a clear validation error, same pattern as every other malformed field | N/A |
| Old `jaunt_active_trip` in localStorage predates this field | Stored trip has no `excluded_ids` key | `isValidTrip()` rejects it (now a required common field), existing safe-reset-to-fresh-trip path triggers | N/A |

</frozen-after-approval>

## Code Map

- `planner.py:73` `shortlist_candidates(start_lat, start_lon, topic, places=None)` -- add an `excluded_ids` parameter (default `None`/empty), filter `place["id"] in excluded_ids` out of `nearby` before the topic/distance filtering already there (or alongside it - order doesn't matter, both are simple membership/attribute filters over the same list).
- `planner.py:329` `plan_route(start_lat, start_lon, topic, requested_minutes, dwell_minutes_per_stop=...)` -- add `excluded_ids=None` parameter, pass through to `shortlist_candidates()`. Normalize `None` to `[]` at the top (callers/tests may pass either).
- `app.py:99` `_validate_plan_request()` -- extract optional `excluded_ids` from the request body; if present, must be a list of strings (reuse the existing `isinstance`/type-check style already used for every other field here); default to `[]` when absent. Returns it as a fifth tuple element.
- `app.py:151` `api_plan()` -- unpack the fifth value, pass `excluded_ids=excluded_ids` into `planner.plan_route()`.
- `static/app.js` `defaultTrip()` (~line 548) -- add `excluded_ids: []` to the initial shape.
- `static/app.js` `hasValidCommonFields()` (~line 641) -- add validation: `Array.isArray(candidate.excluded_ids) && candidate.excluded_ids.every(id => typeof id === "string")`.
- `static/app.js` `startRoutePlanning()` (~line 1245, Story 1.6's own rewrite) -- add `excluded_ids: trip.excluded_ids` to the request payload object already built there (`start_lat`/`start_lon`/`topic`/`requested_minutes`).
- `static/app.js` -- new Re-Jaunt handler: reads the currently-displayed route's stop ids (`trip.stops.map(s => s.id)`), appends them to `trip.excluded_ids` (dedupe not needed - a stop already excluded being excluded again is harmless, and AD-5 never asks for a set), persists, calls `startRoutePlanning()`. Mirrors Story 1.6's time-chip handler shape exactly (update trip, save, retry).
- `templates/index.html:239-251` `.review-panel` -- replace the single `#approve-route-btn` (`.btn-full`) with the equal-weight pair: a new `#re-jaunt-btn` (forest-outline) beside the existing approve button (relabeled "Start my jaunt" per `DESIGN.md`/`EXPERIENCE.md`'s own repeated, literal wording for this exact pair - its current "Approve & start walking" label predates this story but the approved design names this screen's button "Start my jaunt" specifically). `#change-jaunt-btn` stays as-is below the pair.
- `static/style.css` -- new button-pair styles ported from the real mock (`key-generate-review-fallback.html:323-341`, `.sheet-actions`/`.btn`/`.btn-primary`/`.btn-outline`): a `flex` row, `flex:1` buttons, forest-fill primary (reuses `--forest`/`--cream`, same colors `.btn-full` already uses) and a new forest-outline variant (`border: 2px solid var(--forest); color: var(--forest); background: transparent` - no new colors, just a new combination of existing tokens).
- `tests/test_planner.py` `TestShortlisting`, `TestPlanRoute` -- add cases for `excluded_ids` filtering out candidates and for `plan_route()` genuinely returning a different/no route when exclusions remove the only feasible combination.
- `tests/test_app.py` (the existing `_validate_plan_request` test class, ~line 253) -- add cases for a valid `excluded_ids` list, an absent one (defaults to `[]`), and malformed ones (`400`).

## Tasks & Acceptance

**Execution:**
- [x] `planner.py` -- add `excluded_ids` to `shortlist_candidates()` and `plan_route()`, hard-filtering candidates by `id` before any routing/AI call -- the actual enforcement point AD-5 requires
- [x] `app.py` -- validate and thread an optional `excluded_ids` field through `_validate_plan_request()`/`api_plan()` -- the request-side plumbing the frontend needs to call the new parameter
- [x] `static/app.js` -- add `excluded_ids: []` to `defaultTrip()`, validate it in `hasValidCommonFields()`, send it in `startRoutePlanning()`'s payload, and add the Re-Jaunt handler that accumulates the displayed route's stop ids before retrying -- the actual Re-Jaunt behavior
- [x] `templates/index.html` + `static/style.css` -- replace the single approve button with the Re-Jaunt/"Start my jaunt" equal-weight pair, relabeling the existing approve action -- UX-DR6's explicit display requirement
- [x] `tests/test_planner.py` + `tests/test_app.py` -- cover the I/O matrix's backend-observable rows (exclusion filtering, malformed `excluded_ids`, absent-defaults-to-empty)

**Acceptance Criteria:**
- Given a displayed route, when Re-Jaunt is tapped, then every one of that route's stop ids is added to `trip.excluded_ids`, a new planning request is sent with the full accumulated list, and a different feasible route is shown when one exists
- Given Re-Jaunt is tapped a second time after a first, when the new request is built, then it carries the union of both rejected routes' stop ids, not just the most recent one
- Given no feasible alternative exists after exclusion, when Re-Jaunt is requested, then Story 1.6's existing honest-fallback screen shows, unchanged
- Given Route Review is shown, when I look at the action buttons, then Re-Jaunt and the approve action appear as a real equal-weight pair (not one visually subordinate to the other)
- Given `excluded_ids` is sent malformed (not a list of strings), when `/api/plan` receives it, then it returns `400` with a clear reason, the same way every other malformed field already does

## Implementation Notes

**2026-10-22:** Implemented exactly per the Code Map, no deviations.

- `planner.py`: `shortlist_candidates()` gained `excluded_ids=None` (normalized to `[]`), filtering `place["id"] in excluded_ids` out of `nearby` alongside the existing status/lat-lon checks. `plan_route()` gained the same parameter, normalizes `None` to `[]`, and passes it straight through - no other logic in `plan_route()` changed.
- `app.py`: `_validate_plan_request()` now returns a 5-tuple; `excluded_ids` defaults to `[]` via `data.get("excluded_ids", [])` and is rejected with a `400` (`PlanRequestError`) unless it's a list of strings - same `isinstance`-chain style as every other field in that function. `api_plan()` unpacks the fifth value and passes it as `excluded_ids=excluded_ids` to `plan_route()`.
- `static/app.js`: `defaultTrip()` gained `excluded_ids: []`. `hasValidCommonFields()` now requires it to be an array of strings (so a pre-Story-1.7 stored trip fails validation and hits the existing safe-reset path - the I/O matrix's last row). `startRoutePlanning()`'s payload now includes `excluded_ids: trip.excluded_ids`. New `reJauntBtn` handler reads `trip.stops.map(s => s.id)`, concatenates onto `trip.excluded_ids` (no dedupe, as the spec allows), persists, and calls `startRoutePlanning()` - same update/persist/retry shape as `fallbackTimeChipBtn`.
- `templates/index.html` / `static/style.css`: `.review-panel`'s single `#approve-route-btn` (`.btn-full`) replaced with a `.sheet-actions` flex row holding `#re-jaunt-btn` (`.btn.btn-outline`) and `#approve-route-btn` (`.btn.btn-primary`, relabeled "Start my jaunt"). Both buttons are `flex: 1` - genuinely equal width, per UX-DR6. Styles ported from `key-generate-review-fallback.html`'s `.sheet-actions`/`.btn-primary`/`.btn-outline`, reusing only `--forest`/`--cream` - no new colors. `#change-jaunt-btn` left untouched below the pair.
- Tests: `tests/test_planner.py` gained `test_excluded_ids_filtered_out`/`test_excluded_ids_defaults_to_no_exclusion` (TestShortlisting), `test_excluded_ids_passed_through_to_shortlisting`/`test_excluded_ids_none_normalizes_to_empty_list` (TestPlanRoute), and a new `TestPlanRouteExcludedIdsEndToEnd` class that runs `plan_route()` with *real* (unmocked) shortlisting against `ONLY_ONE_FEASIBLE_MATRIX` to prove excluding the only feasible combination's stops genuinely removes it (not just that the parameter is threaded through). `tests/test_app.py` gained three cases in `TestApiPlanValidation`: omitted defaults to `[]`, a valid list is threaded through to `plan_route(excluded_ids=...)`, and four malformed shapes (`"abc"`, `[1, 2]`, a dict, `[None]`) each return `400` without calling `plan_route`.

Verified: `python3 -m unittest discover -s tests -q` - all 268 tests pass (up from 259 on Story 1.6's baseline). `node --check static/app.js` - no syntax errors. Did not additionally run the spec's Playwright manual-check path, since it's explicitly scoped "if no CLI" and the CLI verification above was available and green; the button-pair's equal-`flex:1` styling and the JS-level request-building logic (payload shape, accumulation, no-dedupe) were instead confirmed by direct code inspection against the Code Map and I/O matrix.

Nothing unfinished against this story's scope. One assumption worth flagging: the Design Notes' own called-out surprise (`excluded_ids` surviving a topic change via "Change your Jaunt") was left exactly as AD-5 specifies, per the spec's explicit instruction not to special-case around it.

**2026-10-22 (post-implementation live verification):** Did the live Playwright/curl manual checks the implementing pass skipped - this project's own established practice runs them regardless of CLI coverage, and doing so caught two real things the Python/`node --check` suite couldn't:

1. **The equal-weight button pair wasn't actually equal-width.** Measured live: 219px vs 215px, a reproducible 4px gap, not a one-off. Root cause: `.btn-outline`'s 2px border and `.btn-primary`'s `border: none` meant the two buttons had different border-box/content-box deltas, and this browser's flex algorithm gave each button's own content box an equal share before adding its (unequal) border on top - so only the bordered button grew. Two earlier fix attempts (`min-width: 0`, then `flex-basis: 0` instead of `0%`) were each verified live and found to not actually change the measured widths at all - left disproven rather than assumed to have worked. The real fix: give `.btn-primary` the same `2px solid transparent` border-width as `.btn-outline` (color only differs), removing `.btn-outline`'s now-unneeded compensating `padding: 11px 8px` override. Verified live afterward: both buttons measure 217px, diff 0.
2. **A real, unmocked `/api/plan` POST with a malformed `excluded_ids` returned `200` instead of the expected `400`.** Traced to the actual cause before assuming the code was wrong: the local Flask server (PID checked via `lsof -i :5050`) had been running since the previous day (`use_reloader=False`, no auto-reload) and was serving pre-Story-1.7 code, unrelated to anything in this diff. Restarted the server and re-ran the same request - `400` with the correct message, confirming the implementation was correct all along and the server process was just stale. Logged here as a reusable lesson, not a story defect: a long-lived dev server from an earlier session can silently invalidate live backend verification until restarted.

Also ran a real, fully unmocked end-to-end check against the restarted server: planned a real route, excluded all 4 of its returned stop ids in a second real request, and got back a genuinely different, non-overlapping set of 4 stops - confirms the hard filter works through the real catalogue/routing/AI pipeline, not just against test fixtures.

Full suite re-confirmed after the CSS fix: `python3 -m unittest discover -s tests -q` - 268 pass; `node --check static/app.js` - clean.

## Spec Change Log

## Review Triage Log

**2026-10-22 - step-04 formal review (blind-hunter, edge-case-hunter, verification-gap, run in parallel against the full diff since baseline).** All verified directly against the real code/live behavior before rendering a verdict.

1. **blind-hunter - AI-discussions.md's handover section self-contradicts this diff: real, `high`, patched.** The handover (written before this story was implemented) still said "zero code written" and "do not implement without approval" while sitting next to the complete implementation in the same diff. Rewritten to reflect the real current state, per the user's own explicit instruction to keep the handover current.
2. **blind-hunter - `sprint-status.yaml` left at `in-progress` instead of `review`: real, `low`, patched.** Synced.
3. **blind-hunter - no `ai-prompts.md` entry for this round: real, `low`, patched.** Added.
4. **blind-hunter - approve button's `aria-label` still says "Approve this route and start walking" after the visible text changed to "Start my jaunt": real, `low`, patched.** Updated to match, prefixed with the visible label so it's also announced first.
5. **blind-hunter - `excluded_ids` has no length/item-size bound unlike every other field in `_validate_plan_request()`: real, `low`, patched.** Added a 500-item/200-char-per-item cap, checked against the real catalogue size (226 places) to confirm it's generous, not arbitrary.
6. **blind-hunter - `place.get("id") in excluded_ids` is an O(n*m) list scan where a set would be O(1): real, `low`, patched.** Converted to a set at the top of `shortlist_candidates()`.
7. **blind-hunter - spec file untracked, not part of the diff/commit: `false`.** Same as Story 1.6's analogous finding - normal pre-commit state, will be committed with the rest at the usual commit point.
8. **blind-hunter - `.sheet-actions` dropped the mock's `padding-top`/`margin-top`/`border-top`: `false`.** Checked the mock directly - that divider styling was for a sticky footer below a *scrolling* stop list, a context this screen (`.review-panel`, not a scrolling sheet) doesn't have. `.review-panel`'s own existing `gap: 10px` already provides equivalent visual separation between its children, confirmed by reading its CSS.
9. **edge-case-hunter - text wrap at narrow viewports could grow one button taller than the other under flex stretch: `false`.** Checked live at real mobile widths down to 320px (the practical floor) - "Start my jaunt" never wraps even there. Also confirmed `.sheet-actions` has no `align-items` override, so the default `stretch` would equalize both buttons' heights to the taller one even if wrapping did occur - the claimed consequence can't happen either way.
10. **verification-gap - no findings filed** (confirmed the pre-existing JS-test-harness gap per its own exclusion rule, not a new issue this diff introduces).

Separately, two real things were found and fixed during this round's own live verification, before the formal review even ran - logged in Implementation Notes rather than here since they predate the step-04 pass: the equal-weight button pair not actually being equal width (a real CSS/flex engine quirk), and a stale local Flask server masking the real validation behavior during manual testing.

## Design Notes

**`excluded_ids` persists through "Change your Jaunt," not just through Re-Jaunt itself.** AD-5 says it's cleared "by end trip... along with the rest of that object" - and "Change your Jaunt" (Story 1.5) only changes `phase`/`setup_step`, it never resets the trip object. So if a user Re-Jaunts once, then changes their mind about the topic via "Change your Jaunt," the stops excluded under the old topic remain excluded under the new one too. This reads slightly surprising in isolation but is exactly what AD-5 specifies, and "end trip" is a distinct, not-yet-built Epic 2 concept - not something this story should redefine or special-case around. Flagging this explicitly rather than silently deviating from AD-5's literal rule or silently adding new clearing logic nothing asked for.

**The approve button's label changes from "Approve & start walking" to "Start my jaunt."** This is a pre-existing Story 1.5 label, not something this story would otherwise touch - but `DESIGN.md`, `EXPERIENCE.md`'s Component Patterns table, its State Patterns table, and its own persona walkthrough all independently name this exact button "Start my jaunt" in this exact context (the Re-Jaunt/approve pair), and the AC text itself says "Re-Jaunt and 'Start my jaunt' are displayed." Matching the literal, repeatedly-confirmed approved copy over keeping an unrelated earlier label.

## Verification

**Commands:**
- `python3 -m unittest discover -s tests -q` -- expected: all tests pass, including new `excluded_ids` coverage
- `node --check static/app.js` -- expected: no syntax errors

**Manual checks (if no CLI):**
- Live against the running app via Playwright: a real multi-stop route, tap Re-Jaunt, confirm the resent request body's `excluded_ids` contains every stop id from the just-displayed route; tap Re-Jaunt again on the new route, confirm the list is the union of both, not just the latest; confirm the button pair renders as genuinely equal-width/equal-weight; confirm a 400 response for a malformed `excluded_ids` is handled the same way any other validation failure already is.
