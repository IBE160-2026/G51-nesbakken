---
title: 'Load a stop replacement inside its card'
type: 'feature'
created: '2026-10-22'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
baseline_commit: '581d9d0e8318aae86268d02f630c72514add404d'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Replacing a single stop currently hides the entire route behind Concocting your Jaunt, obscuring that other stops remain unchanged.

**Approach:** Keep the map and stop sheet visible, replace only the selected card's content with Finding a replacement…, and temporarily disable Start and further edits until its request completes. Keep other stops' names/content visible. Initial generation and whole-route Re-Jaunt still use the full loading screen. Keep approved replacement success, shorter-Jaunt inline explanation, final-stop sad fallback and distinct technical failure/retry behaviour; retries also show card-local loading. Reload must still resume valid setup without restoring rejected stops or automatically sending a request. User approved this change on 2026-10-22.

</frozen-after-approval>

## Implementation Notes

Small frontend-only change: static/app.js, static/style.css, focused native Node tests and decision notes. Use an in-memory display snapshot while the existing persisted trip remains in valid recovery state; do not make the old rejected route approvable or persist it as reviewing. Clear busy controls on every outcome. Close/restore modal inert state when navigating to failure screens. No backend, API contract, timeout, schema or provider changes.


Implemented a display-only replacementPreviewStops snapshot and local busy state. The persisted trip still uses the existing safe setup recovery shape; only the selected list card shows progress while neighbours and the map remain visible. Start/Re-Jaunt/change-input controls and row editing are disabled during the request. Success/retained-only return to the list, final honest failure uses sad Jarrod, and technical retry restores local progress with the same constraints. Completion releases controls and modal inert state. Initial generation/Re-Jaunt retain full-screen loading.

## Review Triage Log

Independent BMAD one-shot blind review found one real interaction: closing progress and opening credits during a request left credits over the result and could corrupt modal inert state. Medium, patched: completion dismisses review overlays before presenting success/failure. Four regression cases cover replacement-found, retained-only, technical failure and final-stop failure with credits open. Other review layers skipped for the small frontend-only route. No issue deferred.

## Verification

35 native Node tests, node --check and git diff --check pass. Added controlled pending-response tests for selected-card-only progress, unchanged neighbour names, disabled/guarded controls, no duplicate requests, close/reopen progress, success cleanup, technical retry, final fallback and ordinary full-screen loading. Real isolated Chrome at 390x844 and 320x568 confirms the map/list stay visible, no Concocting screen, correct status text, disabled controls, modal cleanup, keyboard ordering and last-card progress visible within the scrolling sheet. Existing replacement/shorter notice/reload/final-stop scenarios still pass. Screenshot /private/tmp/jaunt-inline-loading-phone.png visually inspected; fixture responses intercepted, no paid calls or normal browser-profile changes. Backend untouched; Python suite not rerun for this frontend-only change.
