---
title: 'Use current location for starting point'
type: 'feature'
created: '2026-10-23'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '61d83c25f1e0279a08f50797d4fbda6ca7c803d5'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** A user cannot select their current location as the walk start.

**Approach:** Add a user-triggered one-shot browser location action on Starting Point, following Story1.10. User authorised completing remaining Epic1 stories, with combined human testing after1.11 and a hard stop before Epic2. This is implementation authority for this scope; no redundant approval needed.

## Boundaries & Constraints

**Always:** use native browser permission, only after an explicit click. Persist the resulting lat/lng as ordinary trip.starting_point and send only on later planning submission. Map/named starts remain available if location denied/unavailable/timed out/unsupported/insecure. Reuse approved controls/styles and existing setup/localStorage validation. No pilot-area rejection: outside starts follow existing planning fallback. Browser may reuse existing permission rather than prompt each time; no custom grant/revoke UI or false promise a new prompt always appears.

**Never:** watchPosition/continuous tracking, server geolocation, provider key exposure, new dependencies, automatic location request on load/reload, Epic2 features or changes to planning semantics.

## I/O & Edge-Case Matrix

| Scenario | Expected behaviour |
|---|---|
| Click location | One getCurrentPosition request, visible accessible pending status, button prevents duplicate pending requests |
| Valid success | Finite/ranged lat/lng becomes Current location start; marker and saved setup match; advance to Available Time like named start |
| Denied/unavailable/timeout/unsupported/insecure | Plain inline nonalarm explanation, no dead end or existing start destruction; map/named controls usable, retry where appropriate |
| User chooses map/named start or leaves setup while pending | Invalidate request result; late success/error cannot overwrite later choice, state or screen |
| Invalid coordinates or synchronous API exception | Same usable failure recovery; never persist invalid start |
| Reload | Stored start resumes normally; no automatic new location request; pending state is not persisted |

</frozen-after-approval>

## Code Map

- templates/index.html: Starting Point .start-panel currently has pin confirmation and named chips. Add Use my current location button and visible role=status aria-live region with current tokens/labels.
- static/app.js: showPendingPin, clearPendingPin, confirmStartBtn, startChipEls, showStep and defaultTrip. Reuse named-start immediate advance and marker/state persistence, label Current location. Add one ephemeral request token/generation guard; invalidate on manual selection and leaving start screen. No polling/watch. Access navigator/window safely for Node harness. Existing backend accepts resulting coordinate unchanged.
- static/style.css: minimal existing-token layout if needed;>=44px target, phone containment. No restyling approved screens.
- tests/frontend-recovery.test.cjs: extend browser boundary stub to inject geolocation callbacks and dispatch native input/button events. Exercise real application handlers and race cases, not helper-only tests.

## Tasks & Acceptance

- [x] templates/index.html/static/style.css — add accessible location action and calm status without displacing existing starts.
- [x] static/app.js — one-shot request plus stale-result cancellation and saved-start transition.
- [x] tests/frontend-recovery.test.cjs — matrix success/failure/race/reload and planning coordinate transport.

**Acceptance:**
- Given only keyboard interaction, when selecting current location, then the action is reachable and native permission is requested only on activation.
- Given denial/error, when recovering, then named/map selection still works without changing other trip inputs.
- Given location success, when later planning, then the acquired coordinate goes through the ordinary request and no continuous stream is created.

## Implementation Notes

Use getCurrentPosition with timeout10000ms, maximumAge0, enableHighAccuracy:false as a one-shot starting point, not navigation tracking. Do not wait forever for failure status. A browser permission prompt may remain open independently of API timeout; manual choice must invalidate eventual callbacks. Read window.isSecureContext when available and native API presence;localhost is a development secure context, plain LAN HTTP is not. Technical reference: https://developer.mozilla.org/en-US/docs/Web/API/Geolocation/getCurrentPosition . Parent handles process docs/browser verification; implementer production/tests only. Preserve all current Epic1 features; no server changes expected.

## Verification

Run native Node frontend tests, node --check and git diff --check; Python suite only if backend touched. Parent uses isolated real Chrome at phone dimensions for actual control layout/tab order, native permission state and geolocation emulation, no paid route calls. Real phone/native OS accessibility remains for the combined Epic1 human test; emulator checks must not be represented as that verification.

## Review Triage Log

Three independent layers completed; edge hunter returned none. Individual findings:
1. Blind — medium/patch: native timeout excludes permission wait. Added an app-level10s timer that invalidates callbacks and releases button; completion/manual/navigation clear it. Injected timer regression passes.
2. Blind — medium/patch: successful marker may remain outside Newtown camera. Center on returned position with map.jumpTo; assert camera coordinates.
3. Blind — low/acceptance pending: native permission accessibility cannot be established by VM tests. Isolated Chrome checked native API/permission states and keyboard reachability; real OS prompt/screen-reader check remains explicitly required at combined human acceptance, per user's chosen sequence. No false claim of phone accessibility completion.
4. Blind — low/acceptance pending: physical-phone HTTPS verification not yet available/reliable. User deferred remote setup; plain LAN HTTP correctly falls back. Localhost native API was tested; establish HTTPS for final phone acceptance before marking story done in tracker.
5. Blind — low/patch: failure tests omitted map recovery. Added denial→map→confirm test with valid state and preserved other inputs.
6. Verification — medium/patch: map cancellation before confirmation was untested. Added late success/error between dropping and confirming pin; pending pin/screen/start/status remain unchanged.

## Completion Verification

52 native frontend tests pass; JS syntax and diff checks pass. Real isolated Chrome390x844/320x568 checked44px keyboard-focusable control, no horizontal overflow, native geolocation API using emulated coordinates and browser-granted permission, denied-state fallback, named-start recovery and reload; no paid calls or actual location read. Screenshot /private/tmp/jaunt-location-phone.png inspected. Automation controls permission state; it does not prove real native-dialog screen-reader accessibility or outdoor accuracy. Native OS permission/phone HTTPS acceptance remains for the combined Epic1 user test. Backend unchanged; local server restarted to refresh cached template. Tracker remains review, not done. No Epic2 tracking added.


**User-requested revision,2026-10-23:** GPS success now previews a centred pending pin on Starting Point and requires Confirm this spot before persisting/advancing, superseding earlier immediate-advance wording. Map relocation switches label to Dropped pin. Preview is ephemeral, named starts retain direct selection, deadline/race guards remain. Panel includes visible map guidance, forest location pill and separated choices; camera offset keeps pin above panel on short/landscape screens. See spec-location-preview-confirmation.md;57 frontend tests and real browser checks pass.
