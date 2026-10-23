# Jaunt — Proposed Architecture and Incremental Development Plan

This document reflects the decisions made while reviewing `product-brief.md`, including two rounds of review from Codex. It describes a proposed technical architecture and a sprint-by-sprint build plan. No code has been implemented yet.

## Key design decision: bulk import, not live-per-request, not hand-curated

Data still comes from live Overpass (OpenStreetMap) and Wikipedia/Wikidata — nothing is hand-typed. But it is fetched **once, in a rerunnable offline import script**, and stored locally as a catalogue that the running application reads from. Live calls happen at import time, not inside every user request.

This resolves a real reliability problem: the public Overpass and Wikimedia APIs have rate limits and can be slow or unavailable, which would make user-facing requests and automated tests dependent on several external services all being up at once. A local, inspectable catalogue removes that dependency from the runtime path, keeps tests repeatable, and still lets the catalogue be regenerated any time by rerunning the import.

Routing is the one exception: it stays live at request time, since the start point and available time genuinely vary per user and can't be pre-computed.

## Stack

- **Backend**: Python (Flask). No database — a local JSON catalogue plus request-time state is enough for V1.
- **Frontend**: minimal vanilla JS page with a Leaflet map (OpenStreetMap tiles — free, no API key). Starting point is chosen by **map click** (plus a few predefined named starts), not typed-address geocoding — keeps V1 from needing a second live geocoding service. **Mobile-first from the foundation, not retrofitted later**: Jaunt is used while walking, so the phone browser is the primary target and desktop is secondary — every sprint's UI work (viewport, layout, touch interaction, control placement) should be built and tested mobile-first from the start, not adapted afterward.
- **Place data**: OpenStreetMap **Overpass API** + **Wikipedia/Wikidata**, fetched by the import pipeline, not at runtime.
- **Routing**: a routing provider with a **confirmed, documented pedestrian/walking profile** — this must be verified directly (see Sprint 1) rather than assumed. If the public OSRM demo server's foot profile doesn't hold up, fall back to a keyed provider such as OpenRouteService, with the key handled server-side in Flask, never exposed to the browser.
- **AI**: two bounded roles only — ranking/selecting among real, already-collected candidates (constrained to IDs Python supplies; Python rejects anything else), and summarizing each selected stop's stored source excerpt into short content. AI is never the source of truth for whether a place exists, and never invents a candidate.

## Catalogue record status

Each imported place gets an explicit status rather than a blanket "verified" label:

- `ready` — usable coordinates, name, topic-relevant tags, and real source text
- `limited` — a real place, but with weak or incomplete source information
- `rejected` — missing essential information, or a duplicate

V1 uses `ready` records at runtime. Manual review is a light spot-check (a sample per topic, plus anything an AI-generated blurb makes look suspicious), not a full manual audit of every imported place.

## Import-time topic assignment

Topics are assigned at import time using simple, documented OSM tag rules — not AI. AI's relevance judgment is reserved for runtime, where it ranks the *already broadly-classified* candidates against a specific user request (including "surprise me"). This keeps import-time classification deterministic and cheap, and keeps AI's role limited to genuine judgment calls rather than bulk labelling.

| OSM tag pattern | Assigned topic |
|---|---|
| `historic=*` | history |
| `heritage=*` | history |
| `building=church`, `building=cathedral` | architecture, history |
| `architect=*` present | architecture |
| `tourism=artwork` | public art |
| `artwork_type=*` | public art |

Source text (Wikipedia/Wikidata) is used to confirm or expand a tag-based topic where available. Import-time AI classification is only worth adding later if these rules prove insufficient in practice.

## Catalogue schema

Documented before Sprint 1 starts, so the importer and the runtime code agree on a fixed shape:

```
id
name
latitude
longitude
osm_type
osm_tags
topics
source_title
source_url
source_excerpt
status              (ready / limited / rejected)
imported_at
rejection_reason    (optional — for limited/rejected records)
```

Store a short source excerpt, not the full Wikipedia article — enough for grounded content generation without bloating the catalogue.

## Keeping AI and routing inputs bounded

Both the AI selection step and the routing distance matrix need a small input, not the whole catalogue. `planner.py` narrows candidates in stages before either is called:

1. Catalogue records within the import boundary
2. Filtered by straight-line distance from the start point
3. Filtered to `status == ready`
4. Filtered to the requested (or, for "surprise me," best-represented) broad topic
5. Capped to a shortlist of roughly **10–15 candidates**

Before AI is called, `planner.py` requests one real distance/duration matrix covering the start point plus the full shortlist (up to 16 nodes, ~120 pairs at the cap) from the routing provider. That matrix is what Python uses to deterministically enumerate every feasible 2–5 stop combination and compute each one's best order and exact total time — AI never receives the raw matrix or does any routing arithmetic itself (an earlier design gave AI the matrix directly and asked it to compute feasibility; live testing across two models showed that arithmetic was unreliable — see docs/ai-development-log.md). AI is instead given a small, ranked menu of already-feasible options — each with its stops, content, topics, and computed totals — and picks the one that best matches the requested topic. This matters because a distance matrix grows quadratically — 15 candidates is 105 pairs, 50 candidates is already 1,225 — so capping the shortlist keeps both the matrix fetch and the combination enumeration cheap regardless.

## V1 time-budget and stop-count defaults

Concrete starting values, so `planner.py` has fixed rules to implement and test against rather than an open-ended judgment call:

- User-entered time: 30–120 minutes
- Dwell time: a fixed 5 minutes per stop for V1
- Route length: 2–5 stops
- The final estimate must not exceed the requested time; prefer using most of the available time rather than requiring an exact match

These are starting defaults, not permanent — expect to adjust them after the real-world test in Sprint 6.

## Route ordering

For every 2–5 stop combination Python considers (see "Deriving a feasible option menu" below), the final order is determined by **brute-force permutation** — trying every possible order (starting and ending at the start point) and keeping the shortest, using the matrix already fetched for the shortlist. At this size (at most 5! = 120 orderings) brute force is cheap to run, simpler to justify ("every option was checked") than a greedy heuristic, and already optimal, so there's no accuracy trade-off to make by keeping it simple.

This same computation doubles as the feasibility check: if the *shortest* possible ordering of a combination, plus fixed dwell time per stop, still exceeds the requested time, that combination is infeasible and is never offered to AI.

## Deriving a feasible option menu, and validating AI's choice

An earlier version of this design asked AI to propose a combination of stops and then validated it after the fact (real IDs, stop count, time-feasibility). Live testing across two models showed AI could not reliably do the underlying routing arithmetic itself, so Python now determines feasibility *before* AI is ever called — see docs/ai-development-log.md for the live evidence and the redesign.

1. Every 2–5 stop combination from the shortlist is checked for feasibility (see Route ordering, above) — cheap enough to run exhaustively at the shortlist's capped size (at most 1,573 combinations at a 12-candidate shortlist).
2. Feasible combinations are ranked by how fully they use the requested time and capped to a bounded menu (15 options in V1), so AI's input stays small regardless of how many combinations exist. Ranking never excludes the only feasible option(s), even when their usage is low.
3. AI is given this menu — each option's stops, content, topics, and computed total/usage — and picks the `option_key` of the one that best matches the requested topic. AI is responsible for the actual judgment of relevance and interest; Python does not second-guess it on taste, and AI does no routing arithmetic of its own.
4. Python validates only that AI's returned `option_key` is one it actually offered. Since every offered option is already proven feasible, no further arithmetic validation is needed.

If AI returns an unlisted key, or the request itself fails for a retryable reason, Python re-prompts with the specific reason and tries again. After a small fixed number of attempts — two retries is a reasonable V1 default — Jaunt falls back to the brief's honest "no suitable route" response rather than retrying indefinitely. A request with zero feasible combinations is detected immediately and never reaches AI at all. A non-retryable failure (invalid credentials, exhausted quota, permission errors) stops immediately rather than repeating a request that cannot succeed.

**Time-budget usage, not just time-budget compliance.** Feasibility alone only verifies that a combination *fits* within the requested time — it doesn't judge whether it makes *sensible use* of it. Sprint 3's own manual demo surfaced this directly: a 2-stop selection using only 15 minutes of a 60-minute request came back "feasible," which is technically correct but not a good final result. Python's menu ranking (step 2 above) favours fuller time usage, while AI still makes the final relevance-based pick among the ranked options — this ranking is a provisional heuristic, not a permanent minimum threshold.

## Module structure

Fewer files than earlier drafts, but each is still traceable to one of the brief's named "Important development decisions":

| Brief's decision point | Module | Job |
|---|---|---|
| How candidate places are collected, verified, and classified | `import_places.py` | Offline, rerunnable: bulk Overpass query for the import boundary, normalize and deduplicate, follow Wikidata/Wikipedia links, assign topics via the tag rules above, write `data/sydney_places.json` incrementally (skipping already-completed records on rerun, so one failed enrichment call doesn't require repeating the whole import), and print a summary of ready/limited/rejected/failed counts |
| A second `public_art` source (Sprint 5) | `import_street_art.py` | Offline, rerunnable: Inner West Council's "Perfect Match" street art dataset (.xlsx), geocoded via Nominatim, merged into the same `data/sydney_places.json` by reusing `import_places.py`'s save/dedup functions rather than duplicating them |
| A `heritage` topic (Sprint 6) | `import_heritage.py` | Offline, rerunnable: a small hand-curated list of NSW ArcGIS Heritage MapServer ids (State + local), coordinates from ArcGIS directly, source text read from a manually-maintained seed file rather than fetched automatically |
| How the route and time constraints are checked | `planner.py` | Loads the catalogue, narrows candidates to a bounded shortlist, requests a real distance/duration matrix, deterministically enumerates and ranks every feasible 2–5 stop combination into a bounded option menu (brute-force ordering per combination), and validates that AI's chosen `option_key` was actually offered, with retry/fallback |
| How AI determines relevance to a topic; how descriptions stay consistent with sources | `ai.py` | Given a bounded menu of already-feasible route options (each with its stops, content/topics, and computed totals) from `planner.py`, AI picks the option that best forms a relevant and interesting walk for the requested topic — Jaunt's core judgment call, with no routing arithmetic involved. Also handles grounded content generation from stored source excerpts |
| — | `services.py` | The routing live-at-runtime external call (the other is `ai.py`'s OpenAI call): distance matrix + final route geometry |
| — | `app.py` + `static/`/`templates/` | Flask endpoint, map-click start point, Leaflet rendering |
| — | `data/sydney_places.json` | The imported catalogue |
| — | `tests/` | Unit tests for `planner.py`'s combination-enumeration/time-budget logic and `ai.py`'s option-key handling, run against fixed/mocked responses — not live services |

## Incremental development plan

Reordered so a minimal end-to-end web flow exists early instead of only in the last sprint, and so the import pipeline is proven on a small pilot area before being pointed at the full inner-Sydney boundary.

**Sprint 1 — Prove the two biggest unknowns, on a small pilot area.**
Build `import_places.py` against a single small pilot neighbourhood first (e.g. Newtown or Redfern) rather than the full inner-Sydney boundary — faster to iterate on and far fewer records to inspect while the importer itself is still being debugged. The boundary is just a config value, so the same code later runs against the wider area unchanged. In the same sprint, directly test the chosen routing provider's endpoint to confirm it actually returns pedestrian routes and durations — do not assume this; verify it before building on top of it.

**Sprint 2 — Minimal end-to-end web flow.**
Flask + Leaflet showing the pilot-area catalogue stops near a clicked start point on a map. No AI, no time-budget logic yet — this sprint only proves the plumbing (backend, frontend, map rendering, data serialization) works before more logic is layered on.

> **2026-10-07 update:** the frontend map library was migrated from Leaflet to MapLibre GL JS (vector tiles via OpenFreeMap), before Sprint 7/8 work began — decision AD-1, recorded in `_bmad-output/planning-artifacts/architecture/architecture-IBE160-2026-10-07/.memlog.md` (to be distilled into that run's `ARCHITECTURE-SPINE.md` at Finalize). The plumbing this sprint proved (Flask serving the catalogue, map-click start point, map rendering) is unchanged in substance; only the rendering library is different. This note exists so this sentence doesn't silently misdescribe what's actually running.

**Sprint 3 — Candidate shortlisting, routing matrix, and the ordering/feasibility helper.**
`planner.py`: build the shortlisting pipeline and request the real distance/duration matrix for the start point plus shortlist, then build the brute-force ordering-and-feasibility helper described above. This helper can be fully unit-tested at this point using a hand-built fake matrix — no AI needed yet, since it's pure logic once the matrix exists.

**Sprint 4 — AI final stop selection.**
`ai.py` (part 1): Python derives a bounded, ranked menu of already-feasible 2–5 stop combinations from the shortlist and matrix built in Sprint 3 (see "Deriving a feasible option menu" above); AI picks the option that best matches the requested topic, including the "surprise me" case. Python validates only that AI's chosen `option_key` was actually offered, and retries or falls back as described above. This replaced an initial version where AI proposed raw candidate ids and computed feasibility itself — live testing across two models showed that arithmetic was unreliable; see docs/ai-development-log.md.

**Sprint 5 — Second candidate-place source: Inner West Council street art.**
Inserted after Sprint 4, not part of the original plan: the OSM-only catalogue produced very few `public_art` stops. `import_street_art.py` adds Inner West Council's "Perfect Match" street art dataset as an independent second source for the same topic, merged into the existing `data/sydney_places.json` (same schema, same `ready`/`limited`/`rejected` conventions). See docs/ai-development-log.md and "Sprint 5 results" below.

**Sprint 6 — A new topic: `heritage`, from NSW official heritage data.**
Also inserted after Sprint 4: a broader architecture/history topic (not just churches), sourced from NSW's official Heritage MapServer (State Heritage Register + locally-listed LEP items). `import_heritage.py` uses a small, hand-curated set of 29 items rather than automated bulk retrieval, since the official descriptive-text application turned out to sit behind a WAF that blocks non-browser clients — see docs/ai-development-log.md and "Sprint 6 results" below.

**Sprint 7 — AI content generation.**
`ai.py` (part 2): each selected stop's stored source excerpt becomes a short story, fact, or prompt. Testing focus includes spot-checking generated text against its source, since content consistency is a named success criterion.

**Sprint 8 — Expand the catalogue, then final routing and real-world test.**
Now that the pipeline is proven on the pilot area, rerun the importers against the full inner-Sydney boundary. Then: real route geometry for the finalized stop order, full error/timeout handling for the routing call, required attribution (OSM, routing provider, Wikipedia, NSW Heritage, Inner West Council) in the UI, and a real-world walking test comparing estimated vs. actual time.

Once real route geometry is available, consider whether the chosen stop order backtracks along the same street for a meaningful stretch (a "there and back" feel) and, if so, prefer an equally- or near-equally-fast ordering that doesn't. This isn't solvable before Sprint 8: `plan_route()` only has point-to-point *durations* from the ORS matrix, not actual polylines, so there's no way to detect path overlap without the geometry this sprint adds. Raised during Sprint 4 manual testing - see docs/ai-development-log.md.

**Sprint 9 (stretch, if time allows before November).**
Device geolocation, point-to-point routes, typed-address geocoding, read-aloud via the browser's `SpeechSynthesis`.

Estimated runway extended by two sprints from the original plan (roughly 9–10 weeks) to accommodate the two inserted data-source sprints — now closer to 11–12 weeks.

## Still-open decisions

- Routing provider choice — depends on the Sprint 1 walking-profile check
- AI provider and API key handling (needed by Sprint 4, worth deciding before then)
- Attribution requirements in the UI for OSM, the routing provider, and Wikipedia
- Exact pilot neighbourhood for Sprint 1 (Newtown vs. Redfern vs. another), and the final inner-Sydney bounding box coordinates

## Sprint 1 results and known limitations

Sprint 1 is complete, run against live data for the Newtown pilot area (24 candidate elements from Overpass). Final catalogue: 11 `ready`, 7 `limited`, 6 `rejected`. Routing confirmed via OpenRouteService's foot-walking profile (5.0 km/h implied speed on a real two-point test, sent via the `Authorization` header rather than a URL parameter). 34/34 offline unit tests passing.

Known limitations accepted for the pilot:

- **Resume cache does not detect schema changes.** `import_places.py` skips rebuilding any record already marked `ready` (or already marked a resolved duplicate), to avoid redundant network calls on rerun. This assumes the record's *shape* hasn't changed since it was last saved. If the catalogue schema changes (e.g. the `source_type` field added mid-sprint), old cached `ready` records written before that change will be missing the new field, and the resume logic will not notice or fix this — it reuses the stale dict as-is. This was hit directly during Sprint 1: rerunning after adding `source_type` produced a `KeyError` on the one `ready` record left over from the previous schema version. The fix for a schema change is to delete `data/sydney_places.json` and run a clean import, not to rely on resume. There is no automatic migration, and none is planned for V1.
- **English-only Wikipedia enrichment.** Only `wikipedia` tags with an `en:` prefix (or no prefix, assumed English) are followed; other languages are marked `limited` with an explicit reason rather than queried.
- **Approximate deduplication.** Records are only treated as duplicates if they share an identical normalized name within 75 metres of a better-sourced record. This will miss duplicates using different names for the same physical place, and could in principle merge two distinct places that happen to share both a name and close proximity — accepted as good enough for a pilot, not exact entity resolution.
- **OSM-tag-sourced content is terse.** Where enrichment falls back to OSM's own descriptive tags (`artist_name`, `start_date`, `inscription`, `subject`), the resulting excerpt is a short factual fragment (e.g. "By Jasmine Sarin, 2021"), not prose — real and sourced, but much thinner than a Wikipedia or Wikidata excerpt. Expected to be sufficient input for Sprint 5's AI content generation, but not yet tested against that.
- **Wikidata fallback is minimal.** Only the English short `description` field is used — no sitelink-following to other-language Wikipedia articles, and no broader Wikidata claims (e.g. inception date, creator) beyond the description string.

## Sprint 3 results and known limitations

Sprint 3 is complete: `planner.py` implements candidate shortlisting, and `services.py` fetches a real OpenRouteService duration matrix. `planner.py` then determines the best stop order by brute-force permutation and checks feasibility against the requested time budget. 68/68 tests pass. The live ORS matrix endpoint was also exercised directly (not just via mocked tests) by running `python3 planner.py` against real Newtown data, confirming the matrix request and response shape work end to end outside the test suite.

Known limitations accepted at the end of Sprint 3:

- **Feasibility does not imply good budget use.** A manual run against real data produced a "feasible" 2-stop, 60-minute-budget route that used only about 15 minutes (26% budget usage) — technically correct, since it fits under the maximum, but not a route a user asked for a 60-minute walk would want. `check_feasibility()` now reports `unused_minutes` and `budget_usage_ratio` alongside `feasible`, but `feasible` deliberately keeps its narrow meaning (fits within the maximum time) rather than being redefined to also mean "uses the time well."
- **No minimum budget-usage threshold has been chosen.** Budget usage is measured and returned, but nothing currently rejects or flags a low-usage-but-feasible selection — that judgment is left to Sprint 4's AI stop selection, as described above under "Time-budget usage, not just time-budget compliance."
- **Duplicate-stop selections are rejected**, and the documented 30–120 minute request range is validated in exactly one place, `check_feasibility()`, rather than being re-checked by each caller.

## Sprint 5 results and known limitations

Sprint 5 is complete: `import_street_art.py` adds Inner West Council's "Perfect Match" street art dataset as a second, independent source for `public_art`, merged into the same `data/sydney_places.json` OSM already writes to. Final catalogue after fixes from an independent Codex review: 121 `ready`, 4 `limited`, 48 `rejected` (of 173 source rows), 44 `ready` records inside the Newtown pilot bounding box. 142/142 tests passing at the time (112 pre-existing + 30 new).

Known limitations accepted at the end of Sprint 5:

- **Row-number-based ids are not stable across a reordered or edited source sheet.** The council spreadsheet's own "Number" column has duplicate values and literal `"##"` error cells, so the importer uses each artwork's row number in the sheet as its id instead. This is stable across reruns of the same file, but would silently produce a different record if the source sheet is ever re-sorted or has rows inserted above an existing entry. Not fixed - flagged for review if the source file is ever updated that way.
- **Cross-source duplicate detection is a small, manually reviewed list, not automatic.** The same physical mural can exist in both OSM and the council dataset with coordinates too far apart (up to ~200m, from address-level geocoding vs. a precise OSM pin) for the existing 75m dedup radius to catch. Two confirmed pairs are handled via an explicit `CROSS_SOURCE_DUPLICATES` mapping rather than widening the radius globally, which risked false positives elsewhere. A third pair might exist unnoticed.
- **Geocoding depends on Nominatim's address matching**, with a fallback from the sheet's "Full Address" to its "Street Address" column when the first attempt fails (venue-name prefixes often trip up the first). 21 of 173 addresses still fail both attempts and are reported, not guessed.

## Sprint 6 results and known limitations

Sprint 6 is complete: `import_heritage.py` adds a new `heritage` topic from NSW's official Heritage MapServer (ArcGIS), covering architecture/history more broadly than churches - pubs, a theatre, rail infrastructure, civic and commercial buildings, and named houses/terraces. Unlike the other two importers, this one does not fetch source text automatically: NSW's official Statement-of-Significance text lives only in an interactive web app (`hms.heritage.nsw.gov.au`) behind a WAF that returns HTTP 403 to any client identifying itself honestly as a script, confirmed directly rather than assumed. Spoofing a browser identity to get past it was explicitly rejected. Instead, 29 items were hand-selected from the official ArcGIS structured data (for geographic spread and type variety) and their Statement of Significance manually copied, verbatim, into a small seed file (`data/heritage_source_text.json`) that a person maintains directly.

Final result: all 29 approved items are `ready` (7 State Heritage Register, 22 local LEP items), all inside the Newtown pilot bounding box, all with coordinates from ArcGIS directly (no geocoding needed) and real verbatim source text. 155/155 tests passing.

Known limitations accepted at the end of Sprint 6:

- **The pipeline cannot grow itself.** Adding another heritage stop means manually picking an ArcGIS id and manually copying its Statement of Significance - there is no automated path from "more candidates exist" to "more ready records," unlike the other two importers. This was a deliberate trade-off to avoid working around an access control, not an oversight.
- **Only 29 of roughly 174 individually-listed heritage items in the pilot bbox are covered.** The 29 were chosen for variety and spread, not because the other ~145 are unsuitable - most are simply unnamed/generic entries ("Terrace group", "Commercial building") that would need their own Statement of Significance read before being worth adding.
- **HMS access is inherently fragile and outside this project's control.** If NSW ever changes or removes the public `ViewItem`/`SectionContainer` pages, the seed file's `hms_url` links (used for manual retrieval and citation) could break with no warning; there is no automated check for this.


## 2026-10-23 amendment — preference-aware candidate discovery

The earlier nearest-only shortlisting description is superseded for Story1.9: qualitative AI discovery can inspect the wider topic-eligible nearby pool before the12-place routing cap. Python still owns eligibility, exclusions/retention and all route arithmetic. General knowledge informs recognisability only; generated content stays source-grounded. One bounded nearest-candidate recovery remains available after honest lack of a suitable preferred walk. See current AD-4 amendment and spec-1-9-preference-aware-discovery.md for input/call bounds and feasible-option diversity. No permanent popularity labels or Python prominence heuristic.
