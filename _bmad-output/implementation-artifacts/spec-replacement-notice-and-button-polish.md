---
title: 'Contain the no-replacement message and slim the Replace button'
type: 'chore'
created: '2026-10-23'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
baseline_commit: 'c71194e53356c1127d18880147d15d817d32fb85'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The no-replacement explanation sits outside the beige stop-card treatment, and Replace looks too bulky.

**Approach:** Give the inline explanation the same full-width beige card background/radius. Make Replace's visible outline/text slimmer while keeping its interactive target at least 44px high and preserving accessible names, keyboard focus and all replacement/loading behaviour. CSS-only visual revision requested by the user on 2026-10-23; reuse existing colours.

</frozen-after-approval>

## Implementation Notes

Small, reversible CSS-only change plus BMAD/process notes. Use an inset noninteractive outline pseudo-element inside the unchanged >=44px button target rather than shrinking its touch area. Verify rendered card background, button hit/paint dimensions and narrow-screen containment in isolated Chrome with mocked planning responses. No backend/JS/API/schema changes.

## Verification and Review

Implemented in static/style.css only: full-width beige notice with the existing 14px card radius; Replace uses 12px text and an inset outline, retaining a 44px interactive height (28px painted outline).

Independent blind review found no actionable defects; keyboard focus and pointer behaviour remain intact. Real isolated Chrome checks at 390x844 and 320x568 passed: notice/card width342px at390px, beige background rgb(237,234,226), Replace target44px, keyboard order, scrolling/no horizontal overflow, replacement success, retained-only notice, final-stop fallback and technical retry. Screenshot /private/tmp/jaunt-notice-polish-phone.png visually inspected. All planning requests used fixtures; no paid API calls. No backend or JavaScript changes. git diff --check passed.
