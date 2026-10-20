---
title: 'Catalogue topic coverage for History and Architecture'
type: 'feature'
created: '2026-10-20'
status: 'review'
route: 'dispatch'
review_loop_iteration: 0
context: []
baseline_commit: 'a3b571439103658362b71cd3e25fe077cb70b8e3'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `import_heritage.py`'s `build_record()` unconditionally tags every one of the 29 approved heritage records `["heritage"]`, and "heritage" is never a user-facing Topic (FR-3). Today exactly 0 heritage records carry `history` or `architecture`, leaving those two Must-tier Topics with only 1 ready stop each (from one unrelated OSM record) against the Planner's 2-stop minimum - selectable but non-functional.

**Approach:** A human-reviewed table assigns `history`/`architecture` to each of the 29 records based on its own Statement of Significance text (never a blanket "tag everything" shortcut), stored in a new maintained override file `import_heritage.py` reads - the same pattern `data/heritage_source_text.json` already establishes - so a routine rerun never silently discards the fix. The override replaces each record's `heritage` tag; it is never added alongside it.

**Approved assignments (reviewed and confirmed by the user, 2026-10-20):**

| Heritage ID | Topics |
|---|---|
| 5012123 | history, architecture |
| 5045004 | history, architecture |
| 5068106 | history |
| 5045003 | history, architecture |
| 5012222 | history, architecture |
| 5045479 | architecture |
| 5063046 | history |
| 2030465 | history, architecture |
| 6002413 | history, architecture |
| 2423037 | history, architecture |
| 2420715 | architecture |
| 2420858 | history, architecture |
| 2030116 | history |
| 2420318 | history, architecture |
| 2030085 | history |
| 2420855 | history, architecture |
| 2420716 | history, architecture |
| 2030126 | history |
| 2030281 | history |
| 2030110 | history |
| 2420005 | history, architecture |
| 2420851 | history, architecture |
| 2030114 | history |
| 2030147 | history |
| 2421330 | history |
| 2030138 | history |
| 2030102 | architecture |
| 2030377 | history, architecture |
| 2030108 | history, architecture |

26 of 29 get `history`, 18 get `architecture` - all 29 lose `heritage`. Net: both Topics clear the 2-ready-stop minimum by a wide margin.

## Boundaries & Constraints

**Always:** Every one of the 29 ids above gets exactly the topics table entry - no silent re-derivation. `heritage` never appears in any heritage-sourced record's `topics` after this story (not even for the 3 records that keep only one of history/architecture). A record's `source_excerpt` (the verbatim Statement of Significance) is never rewritten - only `topics` changes. The override file is read by `import_heritage.py` itself, not applied as a one-off edit to `data/sydney_places.json` - a rerun must reproduce the same topics.

**Never:** No change to `planner.py` (AC explicitly requires it already supports multi-topic stops unchanged - verify, don't assume). No change to `CROSS_SOURCE_DUPLICATES`/`apply_manual_duplicate_overrides()` - that mechanism is unrelated (OSM-vs-heritage duplicate resolution, not topic tagging). No new topics beyond `history`/`architecture` invented for any record (no `public_art` - that stays street-art-only).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Record with an override entry | e.g. id `5045479` -> `["architecture"]` | `build_record()` sets `topics` to exactly that list, never `["heritage"]` | N/A |
| Record with no override entry (hypothetical future id) | No entry for that id in the override file | `topics` is `[]`, never defaults to `["heritage"]` | N/A |
| Override file missing entirely | `load_topic_overrides()` finds no file | Treated as `{}` (every record gets `[]`) - mirrors `load_seed()`'s existing missing-file handling, never crashes | N/A |
| Full rerun end-to-end | `python3 import_heritage.py` run for real against live ArcGIS | `data/sydney_places.json` has the exact approved topics for all 29 ids afterward - this is the AC's explicit rerun-survives check | A genuinely missing approved id still aborts without saving (existing behavior, unchanged) |
| `planner.py` topic query, unchanged code | Query `ready` catalogue for `history` and for `architecture` | Both return >=2 stops | N/A |

</frozen-after-approval>

## Code Map

- `import_heritage.py` -- `build_record()` (line ~102) currently hardcodes `"topics": [TOPIC]` where `TOPIC = "heritage"` (line 41) before any seed logic runs; needs a new `topic_override` parameter (list or `None`) that replaces this entirely - `[]` when no override, never a fallback to `["heritage"]`. `load_seed()` (line ~95) is the exact pattern to mirror for a new `load_topic_overrides()`. `build_state_records()`/`build_local_records()`/`main()` (lines ~191-262) need to load the overrides once and pass each record's entry through to `build_record()` by id.
- `data/heritage_topic_overrides.json` (new) -- same shape convention as `data/heritage_source_text.json`: an `_instructions` string plus an `overrides` object keyed by the same string heritage ids already used in `heritage_source_text.json`'s `items`, each `{"topics": [...]}`. Content is the approved table above, verbatim.
- `data/sydney_places.json` -- regenerated by actually running `import_heritage.py` end-to-end (not hand-edited) once the override file and code change exist, per the AC's explicit rerun-survives requirement.
- `tests/test_import_heritage.py` -- `TestBuildRecord.test_ready_when_coordinates_and_statement_present` (line 21) currently asserts `topics == ["heritage"]`; this is the exact bug being fixed and must be updated to the new contract. Existing calls to `build_record(...)` with 6 positional args (no override) must keep working - add `topic_override` as a new trailing optional parameter, not inserted earlier in the signature, so every existing call site except the new tests keeps working unchanged.
- `planner.py` -- not touched. Confirm by running the existing full suite (`python3 -m unittest discover -s tests`, 179 tests passing before this change) after the change, unmodified.

## Tasks & Acceptance

**Execution:**
- [x] `data/heritage_topic_overrides.json` -- create with the approved table above, in the `heritage_source_text.json`-style shape
- [x] `import_heritage.py` -- add `TOPIC_OVERRIDES_PATH` + `load_topic_overrides()` (mirrors `load_seed()`); add `topic_override` as a new trailing optional parameter to `build_record()`, defaulting `topics` to `[]` when absent/empty, to the override list verbatim when present - delete the `"topics": [TOPIC]` hardcode
- [x] `import_heritage.py` -- thread the loaded overrides through `build_state_records()`/`build_local_records()`/`main()` so each record gets its own id's entry
- [x] `tests/test_import_heritage.py` -- update `test_ready_when_coordinates_and_statement_present` for the new default (`topics == []` with no override passed); add new tests: override applied verbatim, missing-override defaults to `[]` (never `["heritage"]`), override file missing entirely defaults every record to `[]`
- [x] Run `import_heritage.py` for real (live ArcGIS) once the above lands; verify `data/sydney_places.json`'s 29 heritage ids carry exactly the approved topics and `heritage` appears on none of them
- [x] Run the full suite (`python3 -m unittest discover -s tests`) - must stay green, `planner.py` untouched

**Acceptance Criteria:**
- Given the regenerated catalogue, when queried for `ready` records with `history` in `topics`, then at least 2 are returned (26 expected)
- Given the regenerated catalogue, when queried for `ready` records with `architecture` in `topics`, then at least 2 are returned (18 expected)
- Given any of the 29 heritage records, when its `topics` is inspected after this story, then `"heritage"` is never present
- Given `import_heritage.py` is rerun a second time with no further changes, when `data/sydney_places.json` is inspected again, then the same topics are still present (rerun-survives)

## Implementation Notes

**Files changed:** `data/heritage_topic_overrides.json` (new, the approved 29-entry table); `import_heritage.py` (`load_topic_overrides()` added mirroring `load_seed()`; `build_record()` gains a trailing `topic_override` parameter and no longer hardcodes `"topics": [TOPIC]` - the now-unused `TOPIC = "heritage"` constant was deleted; `build_state_records()`/`build_local_records()`/`main()` thread the loaded overrides through by id; the module docstring's stale "for a new `heritage` topic" framing was corrected since this story retires that topic); `tests/test_import_heritage.py` (updated the one test that asserted the old `["heritage"]` default; added 5 new tests - override applied verbatim, missing override defaults to `[]`, missing override *file* defaults to `[]`, and a regression guard that the real shipped override file covers every seed id with no `heritage` tag and clears the 2-stop minimum for both topics); `data/sydney_places.json` (regenerated by actually running the importer, not hand-edited).

**Verified:** Full suite green at 184 tests (179 baseline + 5 new), `planner.py` untouched (`git diff --stat planner.py` empty). Ran `import_heritage.py` for real against live ArcGIS: all 29 heritage ids returned `ready` (no new `limited`/`rejected`), regenerated catalogue has exactly 26 `history` / 18 `architecture` / 0 `heritage` among heritage records - matching the approved table exactly. Reran a second time with no further changes: identical counts, confirming the rerun-survives requirement. Diffed `data/sydney_places.json` directly: only `topics` and the expected refreshed `imported_at` timestamps changed - no `status`/`rejection_reason` changes, confirming `CROSS_SOURCE_DUPLICATES` handling was genuinely untouched by this change.

**Design calls made where the spec left room:** `topic_override` is typed as the raw override-file entry (`{"topics": [...]}` or `None`), not a pre-unwrapped list, since `build_state_records()`/`build_local_records()` naturally get exactly that shape back from `topic_overrides.get(str(heritage_id))` - avoids an extra unwrapping step at each call site for no benefit.

**Left incomplete / out of scope:** none - this story's scope was fully contained (one data file, one import script, its tests) and is now complete end to end, including the live rerun the AC explicitly required.

## Spec Change Log

## Review Triage Log

## Design Notes

The human-review step this story's own AC requires happened directly in conversation, not as a separate artifact: all 29 Statements of Significance were read in full and a proposed table presented with per-record rationale (architecture = named style/architect/design features; history = genuine historical narrative - events, named people, social movements, or an industry-wide historical pattern - not a bare construction date). The user confirmed: "That looks largely correct from my quick read through." The table above is that approved result, not a fresh proposal.

## Verification

**Commands:**
- `python3 -m unittest discover -s tests` -- expected: all tests pass (179 baseline + new ones), including unchanged `planner.py` tests
- `python3 import_heritage.py` -- expected: real run against live ArcGIS completes, reports `ready: 29` (no new rejections/limited), saves `data/sydney_places.json`
- `python3 -c "import json; d=json.load(open('data/sydney_places.json')); print(sum(1 for p in d if p.get('status')=='ready' and 'history' in p.get('topics',[])), sum(1 for p in d if p.get('status')=='ready' and 'architecture' in p.get('topics',[])), sum(1 for p in d if 'heritage' in p.get('topics',[])))"` -- expected: `26 18 0`

**Manual checks (if no CLI):**
- Spot-check a few ids in `data/sydney_places.json` directly against the approved table above
