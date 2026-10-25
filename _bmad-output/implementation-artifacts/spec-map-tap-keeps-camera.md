---
title: 'Keep map still when dropping a starting pin'
type: 'bugfix'
created: '2026-10-25'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
baseline_commit: '1b4286a32daf58071a74551e55559731edef5de5'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

User reports that tapping to drop/move a pin moves the whole map instead. Restore manual map placement: a map tap changes the pending pin to the exact tapped location without changing map centre/zoom, saving it or advancing. Preserve compact menu, explicit confirmation, GPS/named-place focus and stale-GPS guards. Camera adjustment for an explicit named/GPS choice or disclosure/resize stays available; no new map interaction or layout redesign.

</frozen-after-approval>

## Implementation Notes

Regression root cause: showPendingPin calls setStartSpotsExpanded(false), whose new unconditional focusPendingPin also re-centres every map tap. Move disclosure-specific camera adjustment to the actual disclosure button handler so programmatically closing choices has no camera side effect. GPS/named/restore callers already explicitly focus their pending choice. Only static/app.js and existing tests/frontend-recovery.test.cjs require changes; docs/log/handover updated. Add regression coverage for repeated taps, taps overriding GPS/named choices and taps closing disclosure. Verify real browser click positions and unchanged camera at phone widths. No backend/provider or photo changes; unrelated permission-draft deletion remains untouched.


## Review Triage Log

Independent blind reviewer inspected the actual app/test diff and reported no findings. Other lenses skipped for this focused one-shot bug fix. No deferred issue or new public API.

## Verification

Four new regression cases failed against the old code (65 pass/4 fail) and pass with the fix (69 frontend tests pass). Cases cover repeated map taps from fresh, named, GPS and expanded-choice states, marker coordinates, unchanged camera command history, no persistence/advance until Confirm. JS syntax and diff checks pass. Backend/photo code unchanged, Python suite not rerun for this UI-only patch.

Actual isolated Chrome pointer clicks at390×844,320×568,844×390 verified two placements per fresh/named/expanded state (18 real clicks): pending coordinates equal the clicked map point, map centre/zoom remain unchanged, choices collapse and starting point remains uncommitted. No runtime exceptions or paid calls/GPS. Integer screen pixels used to match Chrome event quantisation. Human phone acceptance pending.
