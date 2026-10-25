---
title: 'Skip redundant photo reset/reload when the catalogue agrees with what is already shown'
type: 'bugfix'
created: '2026-10-25'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
baseline_commit: '74522a8'
context: ['spec-refresh-saved-stop-photos.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

User reported, testing live over the phone tunnel after spec-refresh-saved-stop-photos.md shipped, that photos previously showing had disappeared, alongside noticeably slower loading. Root cause: `renderStopPhoto()` unconditionally resets (hides figure, clears `src`) and reassigns `src` every time it runs, including the automatic re-render `loadPlaces()` fires once the catalogue finishes loading for whichever stop overlay is currently open (spec-refresh-saved-stop-photos.md's own feature). When the catalogue's photo for that stop is the exact one already showing - the common case, since a fresh `/api/plan` response already carries the same server-side photo data the catalogue will later confirm - this reset-and-reassign forces a real reload even from the browser's own cache, hiding an already-correct photo for a beat. On a fast local connection that beat is a near-invisible flicker; over the phone tunnel's much slower connection it was long enough to look permanently gone. Fix must only affect the catalogue's own late re-render path - `openStopOverlay()`'s own direct call must keep its existing always-reset behaviour unchanged (an existing test depends on this).

</frozen-after-approval>

## Implementation Notes

`renderStopPhoto(stop, options)` now takes an optional `{ skipIfUnchanged }` flag. Only `loadPlaces()`'s late-arrival call passes `skipIfUnchanged: true`; `openStopOverlay()`'s own call is unchanged (no options, always resets). When set and the resolved photo's `url` already matches the `<img>`'s current `src` attribute and the figure isn't currently hidden, `renderStopPhoto()` returns immediately without touching anything. Required adding a `getAttribute` stub to the test harness's generic mock element (it already aliased `setAttribute`/direct property writes to the same backing property, so this was a one-line addition).

## Review Triage Log

Found and fixed directly by the same agent (Claude) picking up the user's live report, not via a separate formal review pass - a narrowly-scoped, well-understood regression in code from the immediately preceding spec. Reproduced live via Playwright before fixing (confirmed a figure that was visible went hidden and stayed hidden after simulating the catalogue resolving to an identical photo) and re-verified after (figure stayed visible, generation counter did not increment, confirming no reset occurred). One self-caught issue during the fix: an initial unscoped version of the guard broke the pre-existing "photo lifecycle" test, which relies on `openStopOverlay()` always performing a full reset even when reopening the same already-shown stop - fixed by scoping the guard to the `skipIfUnchanged` flag, used only by `loadPlaces()`.

## Verification

Added 1 new node:test case (`a catalogue resolving to the exact photo already showing does not reset or reload it`) plus a required `getAttribute` addition to the shared test harness. All 80 frontend tests pass (79 pre-existing + 1 new), full Python suite unaffected (311/311).

Live-verified against the running local server: seeded a trip whose stop already had a valid, loaded, visible photo (simulating a fresh `/api/plan` response); confirmed the figure was visible. Then simulated the catalogue finishing to load with the identical photo for that stop - confirmed the figure stayed visible throughout with no intermediate hidden state and the generation counter unchanged (proving `resetStopPhoto()` was never called). Confirmed the opposite case still works: a catalogue resolving to a genuinely *different* photo for the open stop still correctly resets and reloads. Confirmed via `curl` through the live phone tunnel that the fix was already being served (no server restart needed - this is a static-file-only change).

Not separately investigated: the user's "slower to load" observation beyond the photo flicker. This is expected given the test setup (an SSH tunnel plus a password-protected gateway wrapping the app, both adding real latency on top of the phone's own network) rather than a code regression, and wasn't treated as one.

