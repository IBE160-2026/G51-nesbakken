# Jaunt — Proposed Architecture and Incremental Development Plan

This document reflects the decisions made while reviewing `product-brief.md`, including two rounds of review from Codex. It describes a proposed technical architecture and a sprint-by-sprint build plan. No code has been implemented yet.

## Key design decision: bulk import, not live-per-request, not hand-curated

Data still comes from live Overpass (OpenStreetMap) and Wikipedia/Wikidata — nothing is hand-typed. But it is fetched **once, in a rerunnable offline import script**, and stored locally as a catalogue that the running application reads from. Live calls happen at import time, not inside every user request.

This resolves a real reliability problem: the public Overpass and Wikimedia APIs have rate limits and can be slow or unavailable, which would make user-facing requests and automated tests dependent on several external services all being up at once. A local, inspectable catalogue removes that dependency from the runtime path, keeps tests repeatable, and still lets the catalogue be regenerated any time by rerunning the import.

Routing is the one exception: it stays live at request time, since the start point and available time genuinely vary per user and can't be pre-computed.

## Stack

- **Backend**: Python (Flask). No database — a local JSON catalogue plus request-time state is enough for V1.
- **Frontend**: minimal vanilla JS page with a Leaflet map (OpenStreetMap tiles — free, no API key). Starting point is chosen by **map click** (plus a few predefined named starts), not typed-address geocoding — keeps V1 from needing a second live geocoding service.
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

Before AI is called, `planner.py` requests one real distance/duration matrix covering the start point plus the full shortlist (up to 16 nodes, ~120 pairs at the cap) from the routing provider. That matrix — not an estimate — is what makes AI's selection judgment meaningful: AI is given the shortlisted stops, their content and topics, and the real walking times between them, so it can weigh relevance and feasibility together rather than guessing at distance. This matters because a distance matrix grows quadratically — 15 candidates is 105 pairs, 50 candidates is already 1,225 — so capping the shortlist keeps the call cheap regardless. The same matrix is fetched once and reused, unchanged, both by AI to inform its choice and by Python to validate AI's answer and compute the final ordering.

## V1 time-budget and stop-count defaults

Concrete starting values, so `planner.py` has fixed rules to implement and test against rather than an open-ended judgment call:

- User-entered time: 30–120 minutes
- Dwell time: a fixed 5 minutes per stop for V1
- Route length: 2–5 stops
- The final estimate must not exceed the requested time; prefer using most of the available time rather than requiring an exact match

These are starting defaults, not permanent — expect to adjust them after the real-world test in Sprint 6.

## Route ordering

Once AI has selected a combination of 2–5 stops, `planner.py` determines the final order by **brute-force permutation** — trying every possible order (starting and ending at the start point) and keeping the shortest, using the matrix already fetched for the shortlist. At this size (at most 5! = 120 orderings) brute force is cheap to run, simpler to justify ("every option was checked") than a greedy heuristic, and already optimal, so there's no accuracy trade-off to make by keeping it simple.

This same computation doubles as the feasibility check: if the *shortest* possible ordering of AI's selection, plus fixed dwell time per stop, still exceeds the requested time, the selection is infeasible regardless of order and is rejected — see below.

## Validating AI's stop selection

AI is responsible for the actual judgment of which combination of stops makes the most relevant and interesting walk — that is the core product decision, and Python should not second-guess it on taste. But Python is the safety net around that judgment, using the same real matrix data:

1. **ID check** — every stop AI selected must be one of the IDs in the shortlist Python supplied. Anything else is rejected outright.
2. **Count check** — the selection must fall within the 2–5 stop range.
3. **Time-feasibility check** — using the fetched matrix, Python computes the shortest possible ordering of the selected stops (see Route ordering, above) and checks that walking time plus fixed dwell time fits within the requested time.

If any check fails, Python re-prompts AI with the specific reason (unknown ID, wrong count, or doesn't fit even at the best ordering) and asks for a different combination from the same shortlist. After a small fixed number of attempts — two retries is a reasonable V1 default — Jaunt falls back to the brief's honest "no suitable route" response rather than retrying indefinitely.

## Module structure

Fewer files than earlier drafts, but each is still traceable to one of the brief's named "Important development decisions":

| Brief's decision point | Module | Job |
|---|---|---|
| How candidate places are collected, verified, and classified | `import_places.py` | Offline, rerunnable: bulk Overpass query for the import boundary, normalize and deduplicate, follow Wikidata/Wikipedia links, assign topics via the tag rules above, write `data/sydney_places.json` incrementally (skipping already-completed records on rerun, so one failed enrichment call doesn't require repeating the whole import), and print a summary of ready/limited/rejected/failed counts |
| How the route and time constraints are checked | `planner.py` | Loads the catalogue, narrows candidates to a bounded shortlist, requests a real distance/duration matrix covering the start point and shortlist, validates AI's selection (real IDs, stop count, time-feasibility) with retry/fallback, and computes the final stop ordering by brute-force permutation over AI's selection |
| How AI determines relevance to a topic; how descriptions stay consistent with sources | `ai.py` | Given the shortlist, their content/topics, and the real distance/duration matrix, AI makes the final selection of 2–5 stops that best forms a relevant, interesting, and time-feasible walk — Jaunt's core judgment call. Also handles grounded content generation from stored source excerpts |
| — | `services.py` | The one live-at-runtime external call: routing (distance matrix + final route geometry) |
| — | `app.py` + `static/`/`templates/` | Flask endpoint, map-click start point, Leaflet rendering |
| — | `data/sydney_places.json` | The imported catalogue |
| — | `tests/` | Unit tests for `planner.py`'s time-budget logic and `ai.py`'s ID-allowlist enforcement, run against fixed/mocked responses — not live services |

## Incremental development plan

Reordered so a minimal end-to-end web flow exists early instead of only in the last sprint, and so the import pipeline is proven on a small pilot area before being pointed at the full inner-Sydney boundary.

**Sprint 1 — Prove the two biggest unknowns, on a small pilot area.**
Build `import_places.py` against a single small pilot neighbourhood first (e.g. Newtown or Redfern) rather than the full inner-Sydney boundary — faster to iterate on and far fewer records to inspect while the importer itself is still being debugged. The boundary is just a config value, so the same code later runs against the wider area unchanged. In the same sprint, directly test the chosen routing provider's endpoint to confirm it actually returns pedestrian routes and durations — do not assume this; verify it before building on top of it.

**Sprint 2 — Minimal end-to-end web flow.**
Flask + Leaflet showing the pilot-area catalogue stops near a clicked start point on a map. No AI, no time-budget logic yet — this sprint only proves the plumbing (backend, frontend, map rendering, data serialization) works before more logic is layered on.

**Sprint 3 — Candidate shortlisting, routing matrix, and the ordering/feasibility helper.**
`planner.py`: build the shortlisting pipeline and request the real distance/duration matrix for the start point plus shortlist, then build the brute-force ordering-and-feasibility helper described above. This helper can be fully unit-tested at this point using a hand-built fake matrix — no AI needed yet, since it's pure logic once the matrix exists.

**Sprint 4 — AI final stop selection.**
`ai.py` (part 1): Python supplies AI with the shortlist, their content/topics, and the real matrix built in Sprint 3; AI selects the final 2–5 stops, including the "surprise me" case. Python validates the selection using Sprint 3's helper (real IDs, stop count, time-feasibility) and retries or falls back as described above.

**Sprint 5 — AI content generation.**
`ai.py` (part 2): each selected stop's stored source excerpt becomes a short story, fact, or prompt. Testing focus includes spot-checking generated text against its source, since content consistency is a named success criterion.

**Sprint 6 — Expand the catalogue, then final routing and real-world test.**
Now that the pipeline is proven on the pilot area, rerun `import_places.py` against the full inner-Sydney boundary. Then: real route geometry for the finalized stop order, full error/timeout handling for the routing call, required attribution (OSM, routing provider, Wikipedia) in the UI, and a real-world walking test comparing estimated vs. actual time.

**Sprint 7 (stretch, if time allows before November).**
Device geolocation, point-to-point routes, typed-address geocoding, read-aloud via the browser's `SpeechSynthesis`.

Estimated runway unchanged: roughly 9–10 weeks (early September through November).

## Still-open decisions

- Routing provider choice — depends on the Sprint 1 walking-profile check
- AI provider and API key handling (needed by Sprint 4, worth deciding before then)
- Attribution requirements in the UI for OSM, the routing provider, and Wikipedia
- Exact pilot neighbourhood for Sprint 1 (Newtown vs. Redfern vs. another), and the final inner-Sydney bounding box coordinates
