---
title: 'Compact starting-point map panel'
type: 'bugfix'
created: '2026-10-25'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

The first-page menu takes too much map space. User approved a compact panel: fixed “Tap to drop a pin” heading; current-location and “Or pick a spot” controls side by side; named chips revealed only by Pick a spot; selected location beside a persistent bottom Confirm button. All named/map/GPS choices still require explicit confirmation. Keep44px targets, keyboard access, saved-start reconfirmation, GPS error/race/deadline protections and map camera clearance. No draggable sheet, no route-selection or provider changes. Collapse choices after selection or returning to the screen. Photo coverage is a separate catalogue update/research activity.

</frozen-after-approval>

## Implementation Notes

Reuse templates/index.html IDs and pendingPin path in static/app.js. Add accessible disclosure button with aria-expanded and aria-controls plus initially hidden named-start group. Use scoped static/style.css row rules, normal-size side-by-side Confirm footer, retain bounded overflow/sticky confirmation. Recalculate pending-pin camera offset after disclosure changes. Verify reduced panel height, no clipped text/controls, keyboard disclosure/selection, preserved uncommitted start and stale GPS protections in tests/frontend-recovery.test.cjs and isolated Chrome. No backend code changes.


## Review Triage Log

Independent blind reviewer inspected actual four-file diff, examined disclosure/storage/GPS/camera/focus/CSS and ran65 tests. No actionable findings; no new deferred issue. Other lenses skipped under one-shot route. Layout uncertainty was settled with isolated Chrome, including actual Enter activation after explicitly emulating tab focus.

## Verification

65 native frontend tests pass, JS syntax/diff checks pass. Real isolated Chrome checks390×844,320×568,844×390: collapsed panel161.7–163.7px (previous291.6px), expanded223.7–225.7px, all controls>=44px, no horizontal overflow, Confirm onscreen. Named choices initially hidden; Enter toggles disclosure/aria-expanded; choosing a named spot collapses choices, focuses Confirm and stays on starting page; explicit Confirm advances; Back restores saved start with collapsed choices. Pin visible above panel after choice. Screenshot/private/tmp/jaunt-compact-start-phone.png visually inspected. Basemap tiles blank in isolated environment, so remote tile rendering not verified. No provider calls/actual GPS. Human phone acceptance still pending; no Epic2 work.
