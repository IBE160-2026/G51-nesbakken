---
title: 'Preserve a valid trip when Re-Jaunt fails or reloads'
type: 'bugfix'
created: '2026-10-22'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
baseline_commit: '20a141f1cf374e9b7a89841c120d82d46136a47c'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Re-Jaunt stores rejected stops as the active reviewing route. Reload restores that rejected route, and fallback navigation can persist a reviewing trip with setup-only fields that the validator rejects, losing the user's inputs and exclusions.

**Approach:** Before requesting a replacement, retain inputs and accumulated exclusions while clearing the rejected route and persisting a valid existing setup phase/step. Failure-screen navigation also explicitly prepares valid setup state. Reload resumes setup without automatically requesting a paid route; normal success still reaches review. Add focused regression checks using Node's built-in testing tools, no framework, package.json or build step. Preserve all approved design, hard-exclusion and retry semantics.

**Approval:** User approved this bounded fix on 2026-10-22 following the independently reproduced findings in AI-discussions.md.

</frozen-after-approval>

## Implementation Notes

Planning gate: no unresolved intent gaps, irreversible operations or provider side effects. Small footprint: static/app.js, a focused Node regression test, and BMAD/process documentation. Reuse existing setting_up phase, topic-origin routing, storage validator and startRoutePlanning; do not add a persistent recovery phase or weaken validation. This is a follow-up bug fix, not a new epic story; 1.6/1.7 remain review pending verification.

Implemented a small prepareSetupState() helper in static/app.js: select the existing topic-origin setup step, set phase to setting_up, clear only active route fields, retain input fields/excluded_ids. Re-Jaunt calls it after accumulating rejected IDs and before persisting/starting the request. Honest/technical Back and different-topic navigation also prepare setup before showStep persists it. No backend, provider, schema, design or response changes.

Added tests/frontend-recovery.test.cjs using node:test and vm to execute the entire shipped app.js with minimal DOM/map/storage/network boundaries. After completing the boundary stubs, the baseline produced six failing recovery/reload tests and three passing success/retry tests. The fix passed those tests; a tenth case now additionally covers named/Wild topic and initial-setup/review-origin recovery combinations. Tests check actual serialized storage, reload without a request, full accumulated exclusions, time-cap behaviour, technical retry equality and successful review restoration. Stubbed DOM is not a rendered-browser test.

README's test commands and Python test count now document how to run both suites; the broader stale README/keyless-demo work remains deferred. Verification: 10 Node tests and 268 Python tests pass; JavaScript syntax and git diff --check pass. No paid calls, server restarts or live browser manipulation.

Final regression suite: 12 Node tests pass, including explicit submission through the actual confirmation controls after reload and success-side review restoration. No new runtime dependencies or schema version. The native test fixture reads actual topic controls from the template; it does not substitute an alternate state-machine implementation.

## Review Triage Log

BMAD one-shot independent blind review, 2026-10-22 (other review layers skipped per small-change route). All four findings were verified against the test code and patched:

1. Low: pending-reload test omitted explicit topic preservation assertions. Added before/after reload assertions for History and Wild Jaunt.
2. Medium: restored setup was not exercised through a new explicit submission. Added actual Start/Confirm control flow after reload and exact request equality including exclusions.
3. Low: successful replacement storage was validated but not booted again. Added reload-to-review, replacement-stop and no-automatic-request assertions.
4. Low: time-chip retry had no pending-reload case. Added a pending adjusted-time retry followed by reload, asserting 120 minutes, topic, exclusions and no request.

All findings addressed; no new issue deferred. Known browser layout, broader JS coverage, shared request deadline and keyless demonstration work remain outside this bounded fix. Python suite: 268 pass; frontend recovery: 12 pass; node --check and git diff --check pass. No fresh live browser/phone or paid API verification claimed.
