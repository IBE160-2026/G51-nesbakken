---
title: 'Expand curated stop-photo coverage'
type: 'feature'
created: '2026-10-25'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

User confirms the Bank Hotel and Enmore Theatre photo subjects and requests more catalogue photos, including public art from the Newtown webpage and other sources. Add individually verified reusable photographs using the existing sidecar/credit/optional-image pipeline. Verify subject, stable ready catalogue ID, creator, primary licence/permission and any underlying artwork permissions before marking reviewed. Retain local unmodified assets and exact credit/source/licence metadata. Do not scrape or assume public-webpage images are reusable; document sources lacking permission instead. No Google integration, new paid services, generated replacement photos or importer refactor. Ask for the intended Newtown webpage while researching known relevant sources independently.

</frozen-after-approval>

## Implementation Notes

Existing data/place_photos.json and static/place-photos/ assets, app.load_place_photos and UI require no new public contracts. Extend data only for individually verified subjects; record primary source URLs, chosen licence, hash/size/dimensions and truthful coverage in docs/stop-photo-coverage.md. Bank/Enmore Commons pages offer Sardaka CC BY3.0; inspect downloaded originals and map to actual catalogue IDs. Research other sources in parallel, add only eligible verified matches; no arbitrary number target. Run existing backend photo validation/API tests and frontend photo lifecycle tests; browser inspect representative actual assets/credits. No new tests mirroring the manifest.


## Implementation Results

Added inspected unmodified Enmore Theatre (Sardaka/CC BY3.0), Cragos Flour Mill (J Bar/CC BY-SA3.0) and The Trail sculpture (Paul McCarthy/CC BY2.5) originals with per-photo source/licence/alt text. Coverage now4/159 ready stops including Post Office. Asset hashes, dimensions, sizes, exact primary evidence and mural permissions research in docs/stop-photo-coverage.md. Existing pipeline/API unchanged. No new service, paid call or importer change.

Bank Hotel and St Peters asset downloads hit429; bounded retry followed Retry-After10, then stopped at Retry-After600. Those two are recorded pending, not marked reviewed/added. User identified newtowngraffitimap.com and Council2017–2022 Perfect Match gallery; actual matches found, no applicable reuse grant for photographs/artworks verified. Newtown reserves rights; Council gallery supplies artist/location but no applicable photo reuse licence. Permission draft prepared for user review; not sent. Follow-ups recorded in deferred-work.md, not hidden as completed coverage.

## Review Triage Log

Independent reviewer checked actual image subjects, stable ready IDs, alt text, primary Commons licences/creators, local hashes/sizes, valid manifest/API joins and truthful4/159 coverage; ran6 existing photo backend tests and65 frontend tests. No actionable findings. Other lenses skipped for this data-only expansion. Reviewer did not independently reproduce download429 history or every mural-source/statute check; parent has tool-output evidence and primary links. Public-art permission remains explicitly unresolved.

## Verification

Full311 Python tests and65 frontend tests pass; JS syntax/diff checks pass. Real isolated Chrome loaded all4 local assets using actual/api/places data: image ratio matches original, correct creator/licence/source links, no horizontal overflow at390×844/320×568, close remains visible and switching to no-photo stop resets image/credits. Screenshot/private/tmp/jaunt-expanded-photo-phone.png inspected (Trail). Fixture route/text used only for presentation checks, no paid providers or invented production content. User acceptance remains pending. No Epic2 work.
