---
title: 'Only recenter on resize when the start panel genuinely changed size'
type: 'bugfix'
created: '2026-10-25'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
baseline_commit: '3b210a5'
context: ['spec-map-tap-keeps-camera.md']
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

User reports the map still moves when dropping a starting pin, on a phone, even though spec-map-tap-keeps-camera.md's fix (commit e530c55) already made the tap handler itself leave the camera still. Root cause is a second path from the same commit: the `window resize` listener unconditionally recenters on the pending pin whenever resize fires, and mobile browsers fire resize for reasons unrelated to the start panel (address bar collapsing on scroll/tap, keyboard appearing/disappearing) - the user's tap can indirectly trigger this. Fix must distinguish a resize that actually changed the start panel's height (keep recentering - this is the legitimate case spec-map-tap-keeps-camera.md explicitly kept available) from one that didn't (skip the recenter). No change to the tap handler itself, to GPS/named-start focusing (which call focusPendingPin() directly and must keep recentering unconditionally), or to map.resize() always running on resize.

</frozen-after-approval>

## Implementation Notes

Added a `pendingPinPanelHeight` baseline, snapshotted in `showPendingPin()` without moving the camera (so a plain tap still leaves the camera untouched) and refreshed whenever `focusPendingPin()` actually runs. The resize handler now always calls `map.resize()` (unrelated to this bug, must keep working per the comment at that call site about stale canvas dimensions) but only calls `focusPendingPin()` when the panel's current height differs from that baseline. Extracted `currentPanelHeight()` since it's now read in two places. Only `static/app.js` and `tests/frontend-recovery.test.cjs` changed.

## Verification

Added 3 new node:test cases (extending the harness with a capturable `window.addEventListener('resize', ...)` hook, a settable `.start-panel` height, and a `fireResize()` helper): a resize with unchanged panel height leaves the camera untouched after a manual drop; a resize that genuinely changes the panel height still recenters on the pending pin; a resize does nothing once there's no pending pin or the step has moved past starting_point. All pass, alongside the pre-existing 4 "manual pin placement leaves the camera unchanged" tests (unaffected - they never fire resize) and the full suite (79/79 frontend, 311/311 Python).

Live-verified against a running server with real DOM/map state: dispatched a plain `resize` event after a real map-click pin drop with no layout change - camera center unchanged (previously, before this fix, the same dispatch moved the camera from `-33.8977` to `-33.8986` as documented in the diagnosis that led to this spec). Then changed the start panel's actual rendered height (via `padding-bottom`, simulating a keyboard/layout push) and re-dispatched resize - camera did recenter onto the pending pin, confirming the legitimate case from spec-map-tap-keeps-camera.md still works.
