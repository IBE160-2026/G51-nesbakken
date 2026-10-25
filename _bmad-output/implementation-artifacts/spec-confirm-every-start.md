---
title: 'Confirm every starting-point choice'
type: 'bugfix'
created: '2026-10-25'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

The starting-point map must never advance on selecting a named spot, map pin or current location. Every choice previews the pin until the user presses Confirm at the bottom of the panel. Confirm stays visible and is disabled until a choice exists; a previously confirmed start is available for reconfirmation on return/reload. At the top, show “Tap to drop a pin” in the same style as “Pick a spot”, followed by the current-location action and named choices. Keep the panel tidy, preserve keyboard access, map visibility, GPS deadline/stale-callback protections and other setup settings. User requested this revision and authorised continuation; supersedes the prior named-start immediate-advance exception. Photo search is research only, separate from this UI fix; no Google integration or new photo assets in this patch.

</frozen-after-approval>

## Implementation Notes

Small reversible change in templates/index.html, static/style.css, static/app.js and tests/frontend-recovery.test.cjs. Reuse pendingPin for all choices, keep heading fixed and move dynamic instructions to the selected-location/status area. Place selection label and always-visible Confirm after chips. Restore confirmed selection into preview on return without auto-advancing. Preserve ephemeral unconfirmed previews on reload (discard, never auto-save). Confirming while GPS is pending cancels stale GPS callbacks. Update acceptance checklist, handover, AI discussions and prompt log. No backend/provider or route-selection changes.


## Review Triage Log

One-shot workflow uses the independent blind-hunter review; other lenses skipped for this focused reversible fix. Reviewer inspected actual diff and executed tests; follow-up review found no new regressions.

- Medium layout risk: panel lacked a height bound after adding a permanent footer. Reproduced offscreen panel under CSS magnification; added70dvh height bound/vertical scrolling and sticky footer. Actual reduced CSS viewports422×195 and195×422 plus ordinary390×844,320×568 and844×390 retain in-viewport panel/Confirm and no horizontal overflow. CSS zoom is not identical to native browser zoom; physical-device magnification/accessibility remains a human check.
- Low verification gap: old named stale-GPS test confirmed before delivering callback, masking chip-level cancellation. Added unconfirmed named preview test asserting unchanged saved state, preview and screen after stale success/failure.
- Low verification gap: saved A → unconfirmed B → reload missing. Added named/map/GPS cases proving A returns reconfirmable and no GPS/request occurs on reload.
- Low accessibility wording: named chips still said Set starting point. Updated labels to Preview starting point at; explicit Confirm performs commitment.

## Verification

64 frontend tests pass; node --check static/app.js and git diff --check pass. Backend unchanged, no Python rerun necessary for this UI patch. Isolated Chrome/native-API emulation verifies GPS preview/confirm, denied/manual recovery and reload; Confirm44px,18px spacing, equal heading styling, no overflow, visible marker/confirmation at390×844,320×568,844×390. Additional reduced CSS viewports422×195 and195×422 keep panel and Confirm onscreen. Screenshot/private/tmp/jaunt-confirm-start-phone.png inspected. Basemap tiles were blank in the isolated screenshot, so this evidence verifies panel/marker geometry, not remote tile rendering. No real GPS or paid provider calls. User acceptance still pending; no Epic2 implementation.
