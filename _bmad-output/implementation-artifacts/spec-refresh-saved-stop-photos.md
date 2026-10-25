---
title: 'Show current photos on saved Jaunts'
type: 'bugfix'
created: '2026-10-25'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
baseline_commit: 'e530c55d4b3a9cd56bbb66b561b4196243465bea'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

User reports no Enmore Theatre photo. Server/phone-origin checks confirm current metadata and JPEG are served; actual route API includes photo. Browser reproduces older saved trip with no photo remains blank because overlay reads only saved stop.photo. Use the already-fetched current catalogue to resolve optional photos by stable stop ID when displaying details, including when catalogue finishes loading after details open. Keep existing route, order, settings, content/attribution, scroll/focus and persistence unchanged. No route regeneration, paid call, new endpoint or photo thumbnails/list redesign. Catalogue failure must preserve text and valid embedded-photo fallback. Current valid catalogue entry with no qualifying photo must not revive stale saved metadata.

</frozen-after-approval>

## Implementation Notes

Reuse loadPlaces existing/api/places request and photo validation/generation guards in static/app.js. Keep current photo lookup in memory; extract existing photo-only renderer for initial open and late catalogue completion, never re-open whole overlay or rewrite saved trip. Discard late work after close/change via existing photo generation and currently-open-stop reference. Add meaningful frontend regressions for old saved route, before/after catalogue timing, image removal, catalogue error and overlay switch/close. Verify ordinary Enmore list-to-details open after saved-photo removal and reload in actual Chrome. Current source-image response through phone origin is HTTP200 JPEG1288795bytes; no live provider requests. User's separate question about expected photo placement is pending; existing approved details-only presentation is preserved. User deletion of permission draft untouched.

## Review Triage Log

Picked up by a different agent (Claude) with Codex's app.js diff already written but uncommitted, no regression tests yet added despite this spec's own Implementation Notes calling for them. Independent read of the diff found it structurally sound (openPhotoStop/stopOverlayPhotoGeneration correctly reused to discard late catalogue work on close/switch; cataloguePhotosById.has() check correctly distinguishes "catalogue has this place with no current photo" from "catalogue hasn't loaded/doesn't have this id", satisfying the no-revival requirement). No findings against the diff itself - the gap was test coverage, not implementation, so it was closed directly rather than logged as a defect.

## Verification

Added 7 new node:test cases to tests/frontend-recovery.test.cjs covering every scenario named in the Implementation Notes: old saved route with no photo gets the catalogue's current one by id; a current catalogue photo overrides a different stale saved one; a catalogue entry that exists but currently has no qualifying photo does not revive a stale saved photo; a catalogue fetch failure preserves stop text and falls back to a valid saved photo; a catalogue that finishes loading after its overlay is already open fills the photo in without rebuilding the overlay; a catalogue that arrives after switching stops renders onto the stop now open, not the one first opened; a catalogue that arrives after the overlay was closed renders nothing and does not reopen it. All 7 new plus the 69 pre-existing frontend tests pass (76/76); the full Python suite is unaffected and unchanged (311/311).

Also live-verified directly against a running server (restarted fresh, since the previously-running dev server predated these edits - a recurring hazard in this project): seeded a simulated old saved trip whose Enmore Theatre stop had no `photo` field at all, reloaded the page, opened its details, and confirmed the real `/static/place-photos/enmore-theatre.jpg` image loaded in full (naturalWidth 2816, complete: true) via the catalogue lookup rather than the missing saved field.

Scope check against the frozen intent: no route regeneration, no new endpoint, no paid calls, no thumbnail/list redesign - confirmed by diff (only static/app.js changed) and by the fact `/api/plan` is never touched by this path. The unrelated `docs/photo-permission-request.md` deletion (made by the user, not this change) is preserved untouched.
