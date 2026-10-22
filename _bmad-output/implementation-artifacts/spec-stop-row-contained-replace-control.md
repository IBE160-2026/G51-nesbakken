---
title: 'Keep Replace inside full-width stop cards'
type: 'bugfix'
created: '2026-10-22'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
baseline_commit: '062e7b7d8547ecc477116194183326fd9c92a783'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Separate Remove/Replace buttons squeeze the beige stop area sideways. The user no longer wants a Remove control.

**Approach:** Show each stop as a full-width beige card containing separately keyboard-accessible details and Replace buttons. Remove the Remove control entirely. Keep Replace available at the final stop and preserve the approved rejection/replacement/shorter-Jaunt/final-fallback behaviour. Reuse current design tokens, maintain 44px hit targets and avoid nested buttons. User explicitly requested this UI revision on 2026-10-22; no further feature change is authorized.

</frozen-after-approval>

## Implementation Notes

Small UI-only change, no open intent questions or irreversible actions. Modify static/app.js, static/style.css, the affected frontend control regression and decision/handover notes. Backend untouched. Use existing two sibling buttons inside the li card, not a button inside a button. Review with native frontend tests and a phone-width rendered check.


Implemented: removed Remove construction/handler, kept details and Replace as sibling buttons, moved beige background/radius to the full-width li, kept the details area flexible and Replace within the card. Long names wrap rather than widening the sheet. Updated the affected control regression; no backend or replacement outcome changes.

## Review Triage Log

Independent BMAD one-shot blind reviewer found no verified defects. The remaining observation was that simulated DOM tests cannot prove CSS containment/hit targets; addressed with real isolated headless Chrome at 390x844 and 320x568. Other review layers skipped for the small UI-only route.

## Verification

27 native frontend tests pass; node --check and git diff --check pass. Real-browser check measured card and list both 342px at 390px viewport, beige background on the entire card, Replace fully inside it, details height45px and Replace44px. Tab order: close, details, Replace, next details. Narrow list scrolls without horizontal overflow. Replacement/shorter notice/reload/final-stop/sad fallback/technical retry scenarios still pass with fixture responses and no runtime exceptions. Screenshot /private/tmp/jaunt-contained-replace-phone.png visually inspected. No paid API calls or normal browser-profile changes; backend unchanged so Python suite not rerun for this UI-only revision.
