---
title: 'Landmark to hidden-gem preference'
type: 'feature'
created: '2026-10-23'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '697aa7c18d41c46a6330aa24b789d6f222b0a979'
context:
  - _bmad-output/specs/spec-1-9-landmark-hidden-gem-preference/SPEC.md
  - _bmad-output/specs/spec-1-9-landmark-hidden-gem-preference/implementation-and-verification.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The existing preference slider saves state but never reaches AI selection. Users cannot actually favour landmarks or lesser-known discoveries.

**Approach:** Connect the existing continuous slider through the stateless planning request and retry chain to AI's qualitative selection. Add real source_type/source_title alongside existing candidate evidence. User approved the linked canonical spec and implementation plan on2026-10-23; this build spec records the same scope.

## Boundaries & Constraints

**Always:** preserve0=well-known,0.5=Balanced,1=hidden gems; keep exact numeric values, existing visual inversion and synchronized sliders. Untouched Wild Jaunt defaults Balanced; explicit changes apply to both topic paths. Keep current confirmation without a slider. Preserve AD-4 qualitative judgement, AD-7 feasible menus, exclusions, retained stops, geometry, budgets, grounding and technical-versus-honest failure handling.

**Never:** compute prominence in Python, filter candidates by preference, add production popularity labels, force test IDs into routes, enrich catalogue duplicates silently, add dependencies/providers/profiles/retrieval machinery, make paid calls during automated verification, or promise different routes when evidence/feasible choices cannot support them.

## I/O & Edge-Case Matrix

| Scenario | Input/state | Expected result |
|---|---|---|
| Explicit preference |0,0.5,1 and0.37| Exact value reaches AI prompt and all attempt retries; unchanged valid route constraints |
| Compatibility | Missing API preference | Balanced0.5 |
| Malformed input | bool/null/string/nonfinite/out-of-range |400 before planning/provider calls |
| Whole-trip actions | initial plan/Re-Jaunt/technical retry/time adjustment/reload | Same saved preference, no enum rounding or automatic request on reload |
| Individual replacement | retained/excluded constraints | Same preference; retained stops and rejection constraints preserved |
| Sparse candidates | Only one kind of suitable stop | Guidance remains soft; a suitable offered walk may be selected |

</frozen-after-approval>

## Code Map

- static/app.js: trip.preference, prefToInputValue/inputValueToPref, startRoutePlanning. Reuse existing saved state and synchronized slider handlers; add preference to shared payload.
- app.py: _validate_plan_request and api_plan. Validate finite non-bool JSON number[0,1], default0.5 only when absent; pass to planner. No endpoint response changes.
- planner.py: plan_route retry loop and _build_ai_options. Append backward-compatible optional preference parameter, forward on each attempt, add source_type/source_title to options. No arithmetic/menu algorithm changes.
- ai.py: select_stops and build_prompt. Append optional preference preserving existing feedback positional callers. Include numeric value and plain-language guidance, never category proxy or unsupported fame claims. Preserve schema.
- tests/test_app.py, tests/test_planner.py, tests/test_ai.py, tests/frontend-recovery.test.cjs: extend existing unittest/native Node tests, no new framework. Existing exact mock assertions may need new default keyword.

## Tasks & Acceptance

- [x] static/app.js — send saved preference for every shared planning request.
- [x] app.py — validate optional value and pass to planner, preserving older callers.
- [x] planner.py and ai.py — carry value to every AI attempt and supply source metadata/guidance without hard filtering.
- [x] tests — cover matrix, exact frontend inversion/transport, backend-to-prompt integration with mocked providers, source metadata nullable title, default/invalid inputs and soft-preference case; run full Python/Node suites.

**Acceptance Criteria:**
- Given either setup slider, when adjusted and submitted by chosen topic or Wild Jaunt, then synchronized values and direction produce the intended numeric signal, with no confirmation slider.
- Given retry/Re-Jaunt/Replace, when planning again, then unchanged preference reaches AI while existing hard route constraints remain intact.
- Given source metadata, when AI receives options, then real source_type and nullable source_title accompany existing content; no prominence field or synthetic production label is added.
- Given controlled tests, when passing, then claims are limited to wiring/instructions; live four-candidate evaluation remains optional and separately authorised.

## Implementation Notes

Intent gaps:none after prior spec approval. Irreversibles:none. Footprint:four existing production files, existing tests and process docs; optional arguments are the only call-contract extension. Preserve existing positional feedback and dwell callers. Simple feature spanning layers warrants full dispatch review rather than one-shot.

## Verification

Run python3 -B -m unittest discover -s tests -q, node --test tests/frontend-recovery.test.cjs, node --check static/app.js and git diff --check. Verify actual browser slider direction/synchronization and request capture at phone dimensions with planning requests mocked. Automated mocks cannot prove live model judgement. User candidates: Bank Hotel, I Have A Dream, St Peters station and Cragos Flour Mills; use surprise_me for mixed topics and inspect feasible availability before judging preference. No catalogue edits or live evaluation in this implementation.

## Implementation and verification results

Implemented the four planned production seams with optional arguments appended to preserve positional callers. No catalogue data or feasible-menu algorithms changed. All287 Python tests and37 native Node tests passed, plus JS syntax/diff checks. API-to-real-prompt integration includes retries and metadata; replacement tests show unchanged feasible menus across preferences. Real isolated Chrome390x844/320x568 checked actual keyboard slider movement, direction, synchronization,0.37 chosen-topic and1 Wild request payloads, no confirmation slider, reload preservation without fetch and no horizontal overflow or runtime exceptions. All planning responses intercepted; no paid call. Screenshot /private/tmp/jaunt-preference-phone.png recorded.

## Review Triage Log

All three BMAD layers ran independently. Edge-case hunter returned no findings; verification-gap reviewer found no gaps. Blind review findings individually triaged:

1. **Medium, patch:** system-level budget tie-breaker omitted preference, risking budget overriding an evidenced preference difference. System guidance now includes preference before budget resolves otherwise comparable options; same soft suitability rules retained.
2. **Low, patch:** single-suitable-option planner mock cannot prove model judgement. This remains explicitly a menu regression, not a live-model claim; strengthened the existing prompt-contract test to assert no preference-only rejection.
3. **Low, patch:** real API-to-prompt integration ended only with none_suitable. Added a successful offered-option integration across0/.5/1/.37, with mocked content/geometry, verifying canonical route IDs and budget.
4. **Low, patch:** metadata tests lacked mixed/missing categories. Integration now includes differing source types, explicit null title and absent metadata keys; asserts unchanged values/nulls reach the prompt.
5. **Low, patch:** reload test asserted saved preference but not displayed sliders. Extended existing test to open both setup steps after reload and check their actual restored values; real Chrome independently checked reload.
6. **False:** temporary build spec in-review versus sprint in-progress is not a readiness defect. Workflow step04 uses in-review for build review and step05 moves sprint to review only after review passes; final states are done(build)/review(tracker).

## Completion Verification

After patches:288 Python tests and37 native Node tests pass; node --check static/app.js and git diff --check pass. All matrix cases have executed coverage: exact values/default/invalid types in API tests, API-to-real-prompt retry and successful result integration, frontend initial/Wild/Re-Jaunt/technical/time/reload/replacement requests, replacement retained/excluded invariant menus across preferences, and soft-guidance/menu checks. The only-suitable-option test proves no Python filtering, not AI qualitative compliance.

Real isolated Chrome390x844 and320x568: native keyboard arrow changes the slider, direction/synchronization correct, chosen-topic0.37 and Wild1 appear in captured planning requests, no confirmation slider, saved preference recovers without automatic request, no horizontal overflow or runtime exceptions. Screenshot /private/tmp/jaunt-preference-phone.png visually inspected. Test server5056 restarted for backend changes. No paid provider call, catalogue mutation, dependency or new API response field. No new issue deferred; live model quality remains an explicit evaluation limitation. User product walkthrough is next.
