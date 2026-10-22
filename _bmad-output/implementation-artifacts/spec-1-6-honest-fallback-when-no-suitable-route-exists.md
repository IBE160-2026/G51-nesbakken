---
title: 'Honest fallback when no suitable Route exists'
type: 'feature'
created: '2026-10-21'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
context: []
baseline_commit: 'f0b69b8b1e7aaf3fcf8bb8f79f836f391afd7845'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Story 1.5 shipped a deliberately minimal, identical-looking placeholder for all three non-feasible `/api/plan` outcomes (zero feasible combinations, AI's `none_suitable` judgment, and a genuine technical failure) - a bare heading, one line of raw backend text, and a "Back" button. Nothing differentiates "no suitable walk" from a real service failure, and there is no way forward other than starting Trip Setup over.

**Approach:** Replace the placeholder with the real honest-fallback screen for the two `feasible: false` cases (Jarrod's dedicated sad pose, a warm Jarrod-voiced explanation - not the backend's raw `reason` string - and up to two concrete alternative-action chips: "Try `{available_minutes + 15}` minutes" and "Try a different topic"), and a visibly distinct, simpler technical-failure screen for the non-2xx case (a "Try again" retry of the exact same request, no parameter-adjusting chips, since adjusting time/topic can't fix a service outage but a transient one can resolve itself on retry). Both keep a clear way back to Trip Setup.

**Decision (2026-10-21, human-approved):** the technical-failure screen reuses the same Jarrod-sad-pose shell as the honest-fallback screen - same figure and layout, different copy, no parameter-adjusting chips. No new visual language invented for a screen EXPERIENCE.md itself flags as undesigned; the two stay distinguishable by copy and which actions are offered, not by a second character treatment.

**Decision (2026-10-21, human-approved):** the honest-fallback screen never shows the backend's raw `reason` string to the user (it stays in `console.error` only, as it already does for technical failures). Instead, Jarrod explains the outcome in a short, warm, plain-language line - e.g. "Jarrod couldn't scout up enough interesting stops to fill the time" - not technical phrasing like "only 1 candidate place(s) found." A light, slightly jokey tone fits the character; it is never framed as the user's fault.

**Decision (2026-10-21, human-approved):** the technical-failure screen includes a "Try again" button that re-sends the exact same request (no parameter change) - distinct from the honest-fallback chips, which change a parameter. A transient service hiccup can genuinely resolve itself on retry; this is not a claim that anything was fixed.

## Boundaries & Constraints

**Always:**
- The two `feasible: false` sub-cases (zero-feasible and `none_suitable`) share one screen template; a real technical failure (non-2xx) never shares copy with it (FR-9).
- The "more time" chip only ever proposes a larger value than the current request, and is omitted entirely once `available_minutes` is already at the 120-minute maximum (FR-9) - never shown as a dead/no-op suggestion.
- The "different topic" chip is offered regardless of the request's time value (FR-9).
- No red/alert color anywhere in either screen; the failure is signaled by Jarrod's pose and plain language only (UX-DR24) - reuse existing tokens, invent none.
- Jarrod's sad pose is the real `jaunty-sad-transparent.png` region, never redrawn or CSS-rotated (DESIGN.md).
- Both screens keep a working, focus-managed way back to Trip Setup, consistent with the existing `reviewUnavailableBackBtn` pattern.
- The honest-fallback screen's copy is a short, warm, hand-written line in Jarrod's voice - never the backend's raw `reason` string, which stays `console.error`-only (matching how technical failures already treat it).

**Never:**
- Do not add a structured field to `/api/plan`'s response to distinguish zero-feasible from `none_suitable` - out of this story's stated scope (it "consumes" 1.4's existing shapes) and not needed now that neither case's raw reason is shown.
- Do not build cross-request memory of which topics/times the user already tried - nothing in the AC asks for it, and a single extra suggestion per axis already satisfies "offers a way forward."
- Do not offer parameter-adjusting chips (time/topic) on the technical-failure screen - no adjustment the user makes can fix a genuine service error, and suggesting one would be misleading. A same-request "Try again" retry is not one of these (see Intent).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Zero feasible combinations | `{feasible:false, reason:"only 1 candidate place(s) found..."}` | Sad-pose screen, warm Jarrod-voiced copy (not the raw `reason`), both chips shown (time chip only if `available_minutes < 120`) | `reason` logged via `console.error`, never shown |
| AI judged none suitable | `{feasible:false, reason:"<none_suitable_reason>"}` | Same sad-pose screen/template and same warm copy (indistinguishable from the row above at the wire level - by design, see Design Notes) | `reason` logged via `console.error`, never shown |
| Already at max time | `{feasible:false, reason:"..."}`, `trip.available_minutes === 120` | Sad-pose screen with only the "different topic" chip, no time chip | N/A |
| Tap "Try N minutes" | User taps the time chip | `trip.available_minutes` updates to the shown value, persists, loading screen shows, a new `/api/plan` request fires immediately | Same three-outcome handling as the original request |
| Tap "Try a different topic" | User taps the topic chip | Navigates to Choose Topic (or Topic-at-rest for `surprise_me`), same as the existing back control - user picks, nothing is auto-selected | N/A |
| Non-2xx response | HTTP 503 (or any non-2xx) | Same sad-pose shell as the honest-fallback screen, distinct warm copy, no parameter-adjusting chips, a "Try again" button | Logged via `console.error`, never shown raw |
| Network/parse failure | `fetch` throws, or body isn't valid JSON | Same technical-failure screen as the row above | Logged via `console.error` |
| Tap "Try again" | User taps the retry button on the technical-failure screen | The exact same request (same `start_lat`/`start_lon`/`topic`/`requested_minutes`) is resent immediately, loading screen shows | Same three-outcome handling as the original request |

</frozen-after-approval>

## Code Map

- `static/jaunty-sad-transparent.png` -- does not exist yet in `static/`; copy verbatim from `_bmad-output/planning-artifacts/ux-designs/ux-IBE160-2026-10-02/imports/jaunty-sad-transparent.png` (same pattern as the main mascot sheet's own copy into `static/`). Real asset, 610x709 trimmed, already chroma-keyed transparent - never re-crop or re-derive.
- `_bmad-output/planning-artifacts/ux-designs/ux-IBE160-2026-10-02/.working/archive/key-generate-review-fallback.html:236-242,344-377,648-675` -- the only existing mock of the honest-fallback screen: `.jaunty-notice` (152x177 display size of the real asset, no cropping math - a standalone image, not a sprite-sheet cell), `.fallback-content`/`.fallback-copy`/`.fallback-sub`/`.alt-row`/`.alt-chip` layout and colors (all existing tokens: `#EDEAE2`/`--surface-muted`, `#16302A`/`--ink`, `#5C6D64`/`--ink-soft`). Port the shape and layout only - its copy ("Jarrod couldn't quite make a 30-minute History walk work...") is illustrative, not final; write the actual warm/jokey line fresh.
- `static/app.js:1181-1270` (`PLANNING_FAILURE_MESSAGE`/`PLANNING_HONEST_FALLBACK_MESSAGE`/`showReviewUnavailable()`/`startRoutePlanning()`) -- the current single-shared-placeholder logic this story replaces. Neither message constant carries the backend's `reason` forward into the UI any more (it's `console.error`-only, same as today's technical-failure path already does) - both become fixed, hand-written copy. `startRoutePlanning()` itself should be reusable for the new "Try again"/time-chip retries without duplicating its body (e.g. keep taking no new params, since `trip` already holds the current request's values).
- `static/app.js:582-...` `isValidStop`/`isValidTrip` -- read-only reference; this story never reaches `reviewing` phase, so no trip-shape change is needed. Confirm, don't assume.
- `static/app.js` -- `trip.available_minutes`, `trip.topic`, and the existing `choose_topic`/`topic_at_rest` screen-routing logic (`reviewUnavailableBackBtn`'s own handler, `static/app.js:1520-1523`) are the values/pattern the new chips reuse - no new state shape.
- `templates/index.html:312-321` -- `#screen-review-unavailable`, the placeholder markup this story rebuilds into two real screens sharing the same sad-pose shell (one with chips, one without) per the approved decision above.

## Tasks & Acceptance

**Execution:**
- [x] `static/jaunty-sad-transparent.png` -- copy the real sad-pose asset into `static/` -- needed before any CSS can reference it; nothing currently does
- [x] `static/style.css` -- add the honest-fallback screen's styles (sad-pose figure, bold copy, "Here's what might work instead" subtext, two-chip row) ported from the real mock, using only existing DESIGN.md tokens -- no new colors, no red/alert treatment
- [x] `static/style.css` -- add the technical-failure screen's styles -- same sad-pose shell/layout as the honest-fallback screen, distinct copy, a "Try again" button instead of the chip row
- [x] `templates/index.html` -- rebuild `#screen-review-unavailable` into two sections (honest-fallback with chips, technical-failure with a "Try again" button) sharing the same sad-pose markup shape -- the current single generic placeholder can't carry either
- [x] `static/app.js` -- split `showReviewUnavailable()`'s one path into two (honest-fallback vs. technical-failure) with fixed, warm, hand-written copy for each (no backend `reason` text in either); compute the time-chip's value and visibility (`min(available_minutes + 15, 120)`, hidden at the 120 cap); wire the time chip (update + persist + `startRoutePlanning()` again), the topic chip (navigate to Choose Topic/Topic-at-rest, reusing the existing back-handler's topic logic), and the technical-failure screen's "Try again" button (call `startRoutePlanning()` again unchanged, since `trip`'s values are untouched) -- three distinct behaviors, not just different text

**Acceptance Criteria:**
- Given a `{feasible:false}` response for either zero-feasible or `none_suitable`, when Route Review can't be shown, then the sad-pose screen appears with a short, warm, Jarrod-voiced line (never the raw backend `reason` string) and at least the "different topic" chip
- Given `trip.available_minutes` is already 120, when the honest-fallback screen renders, then no time-adjustment chip is shown
- Given the time chip is shown and tapped, when the tap registers, then `trip.available_minutes` increases (never decreases), persists, and a new planning request starts immediately
- Given the topic chip is tapped, when the tap registers, then the user lands on Choose Topic (or Topic-at-rest for `surprise_me`) with no topic silently pre-decided for them
- Given a non-2xx or network/parse failure, when the result is shown, then its copy is visibly different from the honest-fallback screen's copy, no parameter-adjusting chip is shown, and a "Try again" button is present
- Given "Try again" is tapped on the technical-failure screen, when the tap registers, then the exact same request is resent (no parameter changed) and the loading screen shows
- Given either failure screen is shown, when I view it, then no red/alert color is present and a working, focus-managed way back to Trip Setup exists

## Implementation Notes

**2026-10-22:** `screen-review-unavailable` split into `#screen-honest-fallback` (`showHonestFallback()`) and `#screen-technical-failure` (`showTechnicalFailure()`) in `static/app.js`, `templates/index.html`, `static/style.css`. `PLANNING_FAILURE_MESSAGE`/`PLANNING_HONEST_FALLBACK_MESSAGE` removed - copy is fixed text in the template (not JS constants), since it's never dynamic. Final copy (not frozen by Intent, written fresh per Design Notes): honest-fallback - "Jarrod couldn't scout up enough interesting stops to fill the time."; technical-failure - "Jarrod's map got the hiccups just now - not your fault. Mind trying again?". Verified live via Playwright against a running `flask run` instance with `fetch` stubbed at the response boundary: both `feasible:false` sub-cases, the 120-minute cap hiding the time chip, the time chip updating/persisting `trip.available_minutes` and re-firing the request, the topic chip routing to `choose_topic`/`topic_at_rest` per `trip.topic` (including `surprise_me`), a 503 response and a same-same-request "Try again" retry (payload byte-for-byte compared), focus landing on each screen's heading, the raw `reason` string never present in `document.body.innerText`, the real `jaunty-sad-transparent.png` loading at its 152x177 display size, and every computed `color`/`background-color` on both screens resolving to an existing DESIGN.md token (no red/alert color introduced). `node --check static/app.js` and the full `python3 -m unittest discover -s tests -q` (259 tests) both pass; no backend files touched.

**2026-10-22 (post-review fixes):** Codex's independent review (concurrent with the planning conversation, `AI-discussions.md`) caught two real defects in the first implementation pass, both confirmed directly before fixing - neither trusted on the write-up alone:

1. **Topic chip silently pre-decided the topic after all.** `fallback-topic-chip`'s handler reused the existing back-handler's `showStep(originStep)` navigation verbatim, which never clears `trip.topic` - so `refreshTopicPills()` kept the just-failed topic's pill selected and `startJauntBtn` enabled on arrival, directly violating the AC's "no topic silently pre-decided for them." Reproduced live (set `trip.topic = "history"`, tapped the chip, confirmed the History pill stayed selected and Start stayed enabled) before fixing. Fix: the handler now sets `trip.topic = null` and persists before navigating (computed `originStep` first, since it depends on the pre-clear value). `topic_at_rest` needed no special case - it renders two equal CTA buttons, never reflecting `trip.topic`. Re-verified live: topic clears, pill deselects, Start disables.
2. **Copy implied a specific, unverified cause.** The original line ("...couldn't scout up enough interesting stops to fill the time") named "not enough stops" as the cause (true for zero-feasible, not necessarily true for `none_suitable`) and implied a route must *fill* the requested time, when `planner.py` treats it as an upper bound only ("a route remains feasible purely by fitting within the maximum budget"). Changed to "Jarrod came up empty-handed this time - couldn't find a walk that felt right" - warm, honest, names no cause the UI hasn't actually verified.

A third, unrelated finding from the same review round (`static/app.js`'s map-marker-click overlay path leaving focus on a newly-hidden element after close, since `openStopOverlay()` always moves focus to the sheet on open regardless of trigger) was fixed in passing - confirmed live via `document.activeElement`, now correctly returns to `map.getCanvas()` (tabindex=0, confirmed focusable) instead of nowhere. This belongs to Story 1.5's code, not this story's scope, but was small and already verified broken, so fixed rather than left open. A fourth finding (epic-1-context.md understating the grounding pipeline as rule-based-only, omitting the real LLM semantic gate) was also corrected in that file directly.

One finding from the same round was stale by the time it was reviewed: the Design Notes paragraph it quoted as "still instructing raw-reason-verbatim copy" had already been corrected during the planning conversation (a real timing race, not a live defect) - confirmed by re-reading the current file, no raw `reason` paragraph remains anywhere in this spec.

All four execution tasks re-verified `[x]` after these fixes; the full I/O matrix re-run live end to end (zero-feasible, `none_suitable`, 120-min cap, time chip, topic chip, non-2xx, network failure, "Try again") - all 8 rows pass. `node --check` and the full 259-test suite still pass; no backend files touched.

## Spec Change Log

## Review Triage Log

**2026-10-22 - step-04 formal review (blind-hunter, edge-case-hunter, verification-gap, run in parallel against the full diff since baseline).** All verified directly against the real code/files before rendering a verdict, not trusted on the write-up alone.

1. **blind-hunter - no automated test coverage for new JS logic: real, `low`, grouped with the verification-gap findings below (same root cause - no JS test harness anywhere in this repo) - deferred, logged to `deferred-work.md`.**
2. **blind-hunter - spec file untracked/not part of this diff: `false`.** Not a defect - normal pre-commit state. This file will be committed with the rest of this story's changes at the usual commit point, same as every prior story's own spec file.
3. **blind-hunter - `jaunty-sad-transparent.png` (~167KB) oversized for its one 152x177 display use: `low`, rejected.** Confirmed against the other two PNGs already in `static/` (405KB mascot sheet, 178KB wordmark) - this matches the project's existing, established pattern of serving real source PNGs unoptimized (no asset pipeline anywhere in this codebase). Negligible on localhost; not worth introducing new asset-optimization practice for one file.
4. **blind-hunter - `#fallback-time-chip` has no static label, accessible name depends entirely on JS: `false`.** Disproven by reading `showHonestFallback()`: `textContent` is set synchronously before `screenHonestFallback.hidden = false` on every code path - there is no window where the button is visible without its label already set.
5. **blind-hunter - `.text-link`'s ink-soft-on-cream contrast (new on the fallback screens) never explicitly checked: real, `low`, patched.** Computed directly via the standard WCAG relative-luminance formula: 4.98:1 - clears AA (4.5:1) with a real margin, not a violation. Recorded in `style.css`'s existing contrast-check comment block for the same documentation discipline already applied to every other text/background pairing in this file.
6. **blind-hunter - `fallbackTopicChipBtn`'s handler calls `saveActiveTrip()` redundantly right before `showStep()` (which already persists for any real setup step): real, `low`, patched.** Removed the redundant call.
7. **blind-hunter - `epic-1-context.md`'s Stories list lost its per-story status annotations during regeneration: real, `low`, patched.** Confirmed via `git show` against the pre-regeneration version, which had them. Restored, refreshed to current `sprint-status.yaml` values (1.1-1.5 done, 1.6 in review, 1.7-1.11 backlog).
8. **blind-hunter - `sprint-status.yaml` still said `in-progress` for this story after its spec moved to `in-review`: real, `low`, patched.** Synced to `review` (the tracker's own vocabulary term), timestamp updated.
9. **edge-case-hunter - zero findings formally reported, but flagged one thing it deliberately chose not to report: `.fallback-copy`/`.fallback-sub` lost `text-align: center` versus the mock they were ported from, judged "an intentional design choice."** Disagreed after checking directly: the mock's own `.fallback-content` rule (`key-generate-review-fallback.html:354`) does set `text-align: center`, and the base `.content` class only centers children as flex items, not text within them - confirmed real, `low`, patched (added `text-align: center` to `.fallback-content`, matching the mock it was explicitly ported from).
10. **verification-gap - three findings (topic-clear, time-chip cap/hide, marker-focus-return, all in `static/app.js`), arrives pre-verified per that layer's own evidence rules: each traced correct as currently written; `defer` per its own filed disposition (same pre-existing no-JS-harness root cause).** Grouped into one `deferred-work.md` entry rather than three near-duplicates of the existing JS-harness entry.

## Design Notes

**Zero-feasible vs. `none_suitable` are not distinguished in the wire shape, and this story doesn't add a field to do it.** Both collapse into the same `{"feasible": false, "reason": "..."}` today (`planner.py`'s `_plan_failure()` is the single return path for both `_enumerate_feasible_combinations()` finding nothing and AI's `none_suitable` judgment) - there is no structured code to switch on without string-matching `reason`'s free text, which `ARCHITECTURE-SPINE.md`'s Consistency Conventions already rules out for the analogous 2xx/non-2xx question. Since the user-approved design also drops the raw `reason` text from the UI entirely (it's `console.error`-only - the copy is a fixed, warm, hand-written line instead), this isn't even a live problem: both sub-cases genuinely get the exact same screen and copy by design, not as a workaround for an unreadable field.

**Why both chips show regardless of which `feasible:false` sub-case occurred:** since the two can't be told apart (above), and both suggestions are harmless even when not the "natural" fix for that specific case (more time can't hurt; a different topic can't hurt), always offering both (minus the 120-cap exception) is simpler and more honest than guessing.

**The honest-fallback and technical-failure copy are both single, fixed lines, not a pool of randomized variants.** The user asked for warm/lighthearted tone, not necessarily varied wording each time; one well-written line per screen keeps the change small and avoids inventing a randomization mechanism nothing asked for. If repetition becomes noticeable in practice, adding variants is a cheap follow-up, not a reason to build it preemptively now.

## Verification

**Manual checks (if no CLI):**
- Live against the running app via Playwright (this project's established verification pattern): construct all three response shapes (mock `fetch` at the response boundary only, as Story 1.5's own step-03 audit did) and confirm the right screen, copy, chip visibility, and chip behavior for each; confirm the time chip is absent at `available_minutes === 120`; confirm tapping the topic chip lands on the correct topic screen without pre-selecting anything; confirm "Try again" resends the same request; confirm keyboard focus lands on each screen's heading; confirm the raw `reason` string never appears in the DOM, only in `console.error`.
- `node --check static/app.js` -- expected: no syntax errors
- `python3 -m unittest discover -s tests -q` -- expected: 259 tests still pass (no backend files touched)
