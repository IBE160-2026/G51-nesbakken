---
title: 'Add verified catalogue photo matches'
type: 'feature'
created: '2026-10-25'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
baseline_commit: '6e1746288c8bda0228921746cd431a420250a7b3'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

User approves adding all photographs we can match to current Jaunt stops, including Wikipedia/Commons sources. Expand the existing curated manifest with individually verified subjects, creators, licences and real local assets. Search beyond the original examples, retry previously blocked downloads when permitted, preserve correct per-image credits and proportional presentation. Confirm exact catalogue identity/address; do not substitute similarly named locations elsewhere. Do not treat public website access or a photographer licence as blanket permission for a depicted mural. No app/provider/importer refactor or new paid service. Preserve unrelated user changes, including deletion of docs/photo-permission-request.md. User explicitly says continue after interrupted agent research.

</frozen-after-approval>

## Implementation Notes

Reuse data/place_photos.json, static/place-photos and existing API/UI photo pipeline. New local originals must be visually checked and matched to ready IDs. Store primary source, creator, selected licence/link, descriptive alt and true changes statement; document asset hashes/dimensions/bytes and coverage in docs/stop-photo-coverage.md. Unavailable/uncleared matches remain documented candidates. Research agents all failed with usage-limit responses before producing artifacts; root resumes serial research/downloads to avoid shared host rate limits. Respect429 Retry-After and avoid unbounded retries. Existing311 Python/65 frontend tests plus actual API/assets/browser smoke checks; no new tests merely mirroring data. Keep human acceptance/Epic1 preference issue open, stop before Epic2. Update handover before ending. Independent review remains required by workflow; if agent budget stays blocked, persist review prompt/evidence for Claude rather than claiming it ran.


## Implementation Results

Added13 local images, increasing coverage4→17 of159 ready stops: Bank Hotel, St Peters Station, I Have a Dream, Newtown Station, Newtown Mission, Imperial Hotel, St Stephen's Church, Newtown Baptist Church, Erskineville Hotel, Stead House, Erskineville Town Hall, Sydney Park brickworks and Union Hotel. All visually checked against stable IDs/source descriptions. Seven new published originals and six published1280px Commons renditions; truthful changes text, complete credits and per-file licence links. Baptist original13MB replaced with743KB rendition before integration. No app code, API, importer or provider changes.

Exact source/download URLs, creators/licences, byte sizes/dimensions and hashes: docs/photo-match-audit-2026-10-25.json. Current coverage and rights rationale in stop-photo-coverage.md. Dream relies on exact file's public CC BY-SA4.0 plus VRT permission notice; no private-ticket claims or general mural grant. Photographer and named mural artists credited. Hippo/Brighton-Le-Sands and UK Newington false matches rejected. Unknown-provenance Stanmore historical lead not added. Public-art sources without verified reusable matching images remain text-only. Search not represented as exhaustive. Unrelated user deletion of permission draft preserved.

## Review Triage Log

Research delegates initially hit usage limits and produced no artifacts; parent resumed serial metadata research/downloads. Later independent blind review succeeded. Reviewer checked all13 hashes/bytes/dimensions/subjects/ready IDs/loader and static responses, six backend photo tests and primary live sources where available. One low documentation issue: earlier4/159 and pending Bank/StPeters/Dream notes were not clearly historical. Patched prominent latest17/159 summary and latest-batch table, with exact audit evidence and supersession statements. Follow-up reviewer reports no remaining findings. Four individual live Commons pages were independently inaccessible via web cache; parent verified API extmetadata and preserved source links/evidence. No speculative bug fixes or further deferrals introduced by review. Other review lenses skipped under one-shot route.

## Verification

311 Python and65 frontend tests pass; git diff --check passes. Actual isolated Chrome loaded all17 API-provided photo records in stop detail overlays, matching original/rendition proportions, required creator/artist/licence/source credit text and links, no horizontal overflow at390×844/320×568, close control accessible and no-photo transition clears image/credit. No runtime exceptions. Screenshot/private/tmp/jaunt-dream-photo-phone.png inspected. Fixture route text used for rendering only; no paid providers, real GPS or fabricated production stories. Saved older route objects may retain previous photo metadata; test a fresh Jaunt for new photos. Human Epic1 acceptance/preference1.9 remain open; no Epic2 work.
