---
title: 'Show a stop photo only when rights-cleared'
type: 'feature'
created: '2026-10-23'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '14238b0e11f3a33ad7871d6d2343bf207fffd779'
context:
  - docs/stop-photo-coverage.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Stop details have an unused bare-photo hook but no rights-cleared photo pipeline or visible licence credit.

**Approach:** Use a small independently maintained curated photo manifest, with a verified local Newtown Post Office photo, to populate optional stop-detail photography with creator/source/licence credit. User authorised finishing Epic1 before combined acceptance; stop before Epic2.

## Boundaries & Constraints

**Always:** photos are optional; no eligible image means text-only without placeholder. Display only complete reviewed metadata plus a local existing asset; visible licence type/link, creator, primary source link and change statement. Preserve aspect ratio, useful alt text, keyboard links and sheet scrolling. No photo thumbnails/map-pin replacement; approved numbered markers and full-width beige list unchanged. Keep attribution for prose sources separately intact. Catalogue imports must not overwrite photo curation.

**Never:** infer reuse rights from image presence, use AI-generated photos, fetch photos in route requests, expose arbitrary image URLs, or weaken stop-story grounding. Keep source copyright/licence evidence in docs. Do not claim all159 stops were externally researched.

## I/O & Edge-Case Matrix

| Scenario | Expected result |
|---|---|
| Complete reviewed manifest + existing local asset | Optional photo object in public place and planned stop responses; image in detail overlay with complete credit only after successful load |
| No/unreviewed/incomplete/invalid manifest entry or missing asset | Omit photo from response; valid route/text unaffected |
| Manifest missing/malformed | All photo-less results still work; no core planning failure |
| No photo or old bare photo_url | No image/credit/blank box; prose full width |
| Image load fails or overlay switches stops | Hide/reset image and credit without hiding text or leaking old photo/attribution |
| Save/reload and replacement | Valid optional metadata survives normal recovery; backend remains canonical; retained stories and rejection rules unchanged |

</frozen-after-approval>

## Code Map

- data/place_photos.json: parent created one audited metadata entry, reviewed:true, fields url/source_url/creator/license/license_url/alt/changes. static/place-photos/newtown-post-office.jpg is the downloaded unmodified original. docs/stop-photo-coverage.md gives primary evidence and byte hash. Do not edit image or add unverified entries.
- app.py: add fail-soft manifest loader and metadata validation/join for to_public_place/load_ready_places and api_plan's stops_response. Resolve local file safely inside static/place-photos; no traversal or external image sources. Require complete reviewed metadata and HTTPS source/licence links. Expose optional photo object, without internal reviewed flag. Do not let catalogue's unreviewed photo fields bypass manifest. No planner/AI change.
- static/app.js: isValidStop optional structured photo validation, openStopOverlay image load/error/reset and complete credit rendering via textContent/createElement. Stop bare photo_url from triggering display; older photo-less saved trips stay valid. Preserve content and source attribution. Avoid stale image callback showing another stop's credit.
- templates/index.html/static/style.css: wrap existing image with initially hidden figure and credit caption; proportional image rather than cropping; text-only when unavailable. Use existing tokens; no restyling other screens.
- tests/test_app.py and tests/frontend-recovery.test.cjs: manifest completeness/failure/local-path and API joining; actual frontend load/error/next-stop/reset, credit links, reload and optional metadata. Existing Node element stub may need load/error callback support, do not introduce a framework.

## Tasks & Acceptance

- [x] app.py — optional curated metadata join with fail-soft loading and safe local assets.
- [x] static/app.js/templates/index.html/static/style.css — image lifecycle, caption/source/licence, accessible no-placeholder fallback.
- [x] tests — matrix and existing route/location regressions.

**Acceptance:**
- Given Newtown Post Office, when viewing its details after image loads, then verified actual photo and creator/source/licence/change credit appear.
- Given any other stop or bad image, when viewing, then only its existing text/attribution appears with no photo box.
- Given an importer rerun, when photo metadata is read, then sidecar manifest/asset remain independent of imported records.

## Implementation Notes

One verified photograph demonstrates the feature without claiming broad coverage. Initial stored coverage0/159, audited manifest1/159; more photos can be curated later. Parent already downloaded/inspected original JPEG and will handle logs, browser test and server restart. Implementation agent edits production/tests only. No paid API/live route calls. Preserve Story1.10 changes. Batch authorisation covers this feature; final Epic1 user acceptance remains outstanding.

## Verification

Full Python unittest and Node frontend suites, syntax/diff checks. Parent real Chrome loads actual local image and caption at390x844/320x568 using seeded or intercepted routes, verifies no-photo and broken-image cases plus scrolling and links. Existing source attribution remains visible. No live provider calls or actual photo licence inference in tests. Stop before Epic2 after Epic1 status reconciliation and user test checklist.

## Review Triage Log

All three independent BMAD layers completed. Each finding checked against production code and tests:
1. Blind — medium/patch: invalid optional photo rejected an otherwise valid stop/saved trip. Core trip validation now ignores malformed optional photo metadata; display still requires complete safe isValidPhoto. Added saved-review and planning-response null/incomplete/unsafe-photo cases preserving text and route.
2. Verification — medium/patch: lifecycle test manually fired load without proving a URL was assigned. Assert image.src equals curated URL before onload; real Chrome independently loaded original2816px image.
3. Edge — low/patch: asset-root resolve error could break optional photo loading. Catch OSError/RuntimeError and return empty photos; API regression verifies text-only200.
4. Parent — low/patch: new photo test class followed unittest.main, so direct module execution omitted it. Moved guard to end and ran python3 -B -m tests.test_app -q:47 tests pass including photo class. Discovery had already run all photo tests.

## Completion Verification

Final combined verification:311 Python tests and56 native Node tests pass, JS syntax/diff checks pass. Optional metadata join tested at both public endpoints, manifest malformed/missing/unreviewed/incomplete/unsafe/missing/symlink assets, image lifecycle/load/error/reset/credit links, canonical replacement metadata and malformed-photo recovery. Parent's real Chrome390x844/320x568 loaded actual local JPEG(naturalWidth2816), proportional342x256.5 display, creator/source/licence links, no horizontal overflow, text-only and broken-image fallback, and reload. No uncaught runtime exceptions; screenshot /private/tmp/jaunt-photo-phone.png inspected. Post Office licence verified from specific primary Commons description, selecting CC BY3.0 with credit; source asset unmodified. Curated coverage1/159 is a lower bound, not full availability research. No paid calls.

Local5056 server restarted with final backend/template. Remote gateway/tunnel stopped per user deferral. All remaining Epic1 feature implementation is complete;1.6/1.7/1.9/1.10/1.11 remain tracker review for combined user acceptance, Epic1 remains in-progress and all Epic2 stories remain backlog. Real phone HTTPS/native permission accessibility is explicitly pending in docs/epic-1-acceptance-checklist.md. Existing cross-cutting deferred tasks remain separate; no next-epic work started.
