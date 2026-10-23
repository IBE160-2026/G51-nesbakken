---
title: 'Preview and confirm current-location start'
type: 'bugfix'
created: '2026-10-23'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
baseline_commit: 'ab2d2b491c0c059e17890573b2fcc05f0c84f578'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

User testing found that location advances before a pin can be inspected, map-pin instructions are missing/obscured, the location action blends into beige chips, and Or pick a spot is cramped. Current-location success must instead show a centred pending pin and visible Confirm this spot on Starting Point, just like a dropped pin. Only confirmation commits coordinates and advances; manual map adjustment remains possible. Restore a visible map-pin instruction within the panel, space the action from named-start choices, and use the existing forest pill styling rather than beige. User explicitly requested this revision; supersedes Story1.10 immediate-advance behaviour. Preserve named-start direct selection, deadlines/race guards, native permission and all other approved flows.

</frozen-after-approval>

## Implementation Notes

Small reversible revision in static/app.js, templates/index.html, static/style.css and existing frontend tests. Reuse pendingPin/showPendingPin and confirmation, preserve Current location label until manual relocation switches it to Dropped pin. GPS preview stays ephemeral/uncommitted and reload must not promote it or request GPS. Do not show a misleading old committed marker while GPS preview is awaiting confirmation. Place map instruction in start panel rather than behind panel at map bottom. Verify native-API emulated preview, explicit confirm, map override, reload,44px controls and phone spacing in isolated Chrome; no actual location or paid calls. Update Story1.10/context/handover/checklist to reflect new approved behaviour.

## Review Triage Log

Independent one-shot reviewer inspected actual diff and ran57 frontend tests. One verified medium issue: raw viewport centering could hide preview behind fixed panel on short/landscape screens. Patched focusPendingPin to use measured panel height and nonpersistent camera offset; on resize recenter pending pin after map resize. Browser checks demonstrate visible pin/confirmation at390x844,320x568 and844x390. No additional issue deferred. Other review lenses skipped for this focused reversible revision per one-shot workflow; actual rendered/native API checks supplement VM tests.

## Verification

57 native frontend tests, JS syntax and diff checks pass. Updated direct-flow test asserts GPS success leaves starting_point uncommitted until Confirm; retry, map relocation label, existing-start preservation, reload(no GPS/no preview promotion), deadline and stale callbacks covered. Real isolated Chrome with emulated native location/permissions checks starting-point preview, uncommitted state, explicit confirmation, unchanged later coordinate transport, forest styling,44px controls, separated choices, visible instruction, visible pin/confirmation at portrait/narrow/landscape, denial/reload/manual fallback and no horizontal overflow/runtime exceptions. Screenshot /private/tmp/jaunt-location-preview-phone.png inspected. No actual location or paid calls. Local server refreshed template; backend unchanged. Human Epic1 acceptance still pending; no Epic2 work.
