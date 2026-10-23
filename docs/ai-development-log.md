# AI Development Log

This document records significant uses of AI during the development of Jaunt, including suggestions made by AI tools, decisions I made, issues identified through review and testing, and changes made as a result.

It is not intended to record every prompt or interaction. It focuses on decisions that affected the product, architecture, implementation, or testing.

---

## Initial planning and architecture

### AI contribution

Claude reviewed the product brief and assignment documentation before
implementation and proposed an incremental architecture for Jaunt.

One early suggestion was to use a small manually curated dataset of places for the first version. Claude also helped define a Python-based architecture with a simple web frontend.

### My decisions

I rejected manual curation as the main data approach. Geographic scalability is part of the product concept, and manually entering individual places would not
test whether Jaunt could work beyond a predefined list.

I decided that the first version could be geographically limited to one area,
but the places themselves should be obtained automatically from external data.

I also decided on an important division of responsibility between deterministic
code and AI:

- Real places must come from external, verifiable data sources.
- AI must not invent places or determine whether a place exists.
- AI may later evaluate and select between real candidate places and generate
  content grounded in retrieved source material.
- Python remains responsible for deterministic validation and route-related
  calculations.

Python was selected for the backend, with a simple web frontend, keeping the
implementation aligned with the course material and understandable enough for
me to explain.

### Independent review

Codex was used as an independent reviewer of the proposed architecture rather
than as a second simultaneous developer.

One important discussion concerned whether AI or Python should make the final
stop selection. I decided that AI should make the final selection because
relevance and interestingness are central to the product concept, while Python
should validate the selection against deterministic constraints such as
available places and time.

### Reflection

The architecture phase showed that AI suggestions should not automatically be
accepted even when they simplify implementation. Manual curation would have
made the first prototype easier, but it would have avoided testing an important
assumption behind the product.

The separation between sourced facts, AI judgement, and deterministic
validation became an important architectural principle for the project.

---

## Sprint 1 – Real place data and routing feasibility

### Goal

The purpose of Sprint 1 was to test two major external dependencies before
building the application around them:

1. Whether real place data could be automatically retrieved and transformed
   into a usable catalogue.
2. Whether the routing provider could return realistic pedestrian routing
   information.

The pilot was deliberately limited to Newtown rather than the intended wider
Inner Sydney area.

### AI contribution

Claude implemented an import pipeline using OpenStreetMap/Overpass and initially
used Wikipedia-linked content as the main criterion for producing usable
records.

It also implemented a routing check using OpenRouteService.

### Testing revealed a problem

The first real import produced:

- 24 candidate places
- 1 ready
- 17 limited
- 6 rejected

Only one of the 24 candidates had a Wikipedia link.

This was not primarily an implementation failure. It exposed a weakness in the
original enrichment assumption: requiring Wikipedia effectively excluded many
local places, particularly street art, even when OpenStreetMap contained useful
factual metadata about them.

Further investigation showed that the 24 candidates included:

- 13 public-art records
- 7 churches
- 4 historic records

Many public-art records already contained fields such as artist name and
creation date in OpenStreetMap.

### My decision

Rather than manually adding places or simply increasing the geographic area, I
decided to broaden what could count as legitimate sourced information.

The enrichment priority became:

1. Wikipedia
2. Wikidata
3. descriptive OpenStreetMap tags

AI-generated facts were not introduced as a replacement for missing source
material.

### Result

After the change:

- 11 records were ready
- 7 were limited
- 6 were rejected

The 11 ready records consisted of:

- 8 using OpenStreetMap descriptive tags
- 2 using Wikidata
- 1 using Wikipedia

This produced a workable pilot catalogue without manually curating individual
places.

Live testing also confirmed that OpenRouteService returned realistic pedestrian
routing information.

### Issue discovered during testing

A previous ready record was reused by the importer's resume logic after the
catalogue schema had changed. Because the old record did not contain the new
`source_type` field, this produced an error.

For the pilot catalogue I chose a clean rebuild rather than adding migration
logic for old catalogue schemas.

### Reflection

This sprint demonstrated why testing against real external data was important.
The initial approach worked technically but produced an unusable catalogue.

The solution was not to ask AI to fill the missing information. Instead, I
changed the sourcing strategy based on evidence from the real data while
preserving the requirement that factual information remained attributable to
external sources.

---

## Sprint 2 – End-to-end mobile map foundation

### Goal

Sprint 2 was intended to prove that the basic application plumbing worked:

external catalogue → Python/Flask backend → JSON API → browser → Leaflet map.

No AI selection, routing logic, or time-budget planning was intended yet.

### AI contribution

Claude implemented:

- a Flask backend
- an API exposing ready catalogue records
- a Leaflet map
- map markers for real places
- selection of a visual starting point

Only `ready` catalogue records were exposed to the frontend.

### Issue I identified

When I first viewed the application, it had effectively been built with a
desktop-sized screen in mind.

This conflicted with the intended use of Jaunt: the application is supposed to
be used while somebody is walking.

The product brief mentioned that the route should be viewable from a phone, but
the architecture did not explicitly establish mobile-first design as a
requirement.

### My decision

I made mobile-first design an explicit product and architectural requirement
rather than treating mobile responsiveness as later visual polish.

The Sprint 2 interface was then adjusted for mobile viewport behaviour while
remaining deliberately visually simple.

### Independent review

Codex reviewed Sprint 2 and identified several issues worth fixing before
closure:

- external catalogue strings were being inserted into popup HTML unsafely;
- missing/broken catalogue data could result in a silent empty map;
- the selected start marker looked the same as normal place markers;
- file-path handling depended on the directory from which the application was
  launched.

### Changes made

Claude implemented the accepted review findings:

- popup content is rendered safely using DOM elements and `textContent`;
- loading, empty, and error states are visible;
- the start location uses a visually distinct marker;
- a mobile instruction tells the user to tap the map to choose a start point;
- catalogue paths are resolved relative to the application rather than the
  terminal's current directory.

The popup was intentionally kept simple rather than designing the final content
experience prematurely.

### Manual testing

I tested the application using Chrome's mobile device emulation, including a
phone-sized viewport.

I also manually tested failure behaviour by temporarily renaming
`sydney_places.json`. The application displayed the expected error state rather
than silently showing an empty map. Restoring the filename restored the places.

### Reflection

This sprint exposed an important limitation of relying only on written
requirements: a statement that something "can be viewed from a phone" is weaker
than explicitly designing the application mobile-first.

I identified this through direct inspection of the working application rather
than through an AI review. It was corrected before more frontend functionality
was built on top of the desktop-oriented assumption.

---

## Sprint 3 – Deterministic planning and feasibility

### Goal

Sprint 3 introduced the deterministic part of route planning before adding AI.

The system needed to:

- shortlist real candidate places;
- obtain real walking durations;
- evaluate possible orders for selected stops;
- determine whether a selection fits the requested time.

### AI contribution

Claude implemented:

- `shortlist_candidates()`
- OpenRouteService duration-matrix retrieval
- brute-force route ordering for 2–5 stops
- deterministic feasibility calculations
- automated tests
- a runnable manual demonstration

The shortlist uses:

- `ready` records only
- a 2 km straight-line pre-filter
- explicit topic filtering when a topic is selected
- no topic filtering for `surprise_me`
- closest-first ordering
- a maximum of 12 candidates

### My decisions

Claude originally suggested that `surprise_me` should select whichever topic
had the most nearby candidates.

I rejected this because it would make the feature biased toward the most common
category before AI had an opportunity to make an interesting selection. For
`surprise_me`, candidates across topics therefore remain available.

The 2 km radius was accepted as a configurable V1 pre-filter rather than as a
claim about how far the final route should travel.

### Testing

A deterministic test revealed that `shortlist_candidates()` relied on its
caller to supply only `ready` places rather than enforcing the rule itself.

The function was changed so that the invariant is enforced internally.

The live OpenRouteService matrix endpoint was also tested successfully.

### Manual testing and a new product issue

I manually ran:

`python3 planner.py`

against real Newtown data.

For a 60-minute request using two example public-art stops, the planner returned
approximately:

- Walking time: 5.4 minutes
- Dwell time: 10.0 minutes
- Total: 15.4 minutes
- Unused time: 44.6 minutes
- Budget usage: 26%
- Feasible: Yes

The calculation was correct: a 15-minute route does fit inside a 60-minute
maximum.

However, I identified that such a route would be a poor final recommendation.
A route should not merely fit within the user's available time; it should make
reasonable use of it.

### Independent review

Codex agreed that this was not a feasibility bug, but identified several
deterministic safeguards that should exist before AI is introduced:

- measure unused time and budget-use ratio;
- reject duplicate stop selections;
- test the routing-service wrapper;
- clearly assign responsibility for validating the documented 30–120 minute
  request range.

### Changes made

Claude implemented:

- `unused_minutes`
- `budget_usage_ratio`
- duplicate-stop rejection
- 30–120 minute validation in the planner
- mocked routing-matrix service tests
- clearer human-readable manual demo output

`feasible` deliberately retains its narrow meaning: the route fits within the
maximum available time.

No minimum budget-use threshold has yet been chosen.

The final Sprint 3 test suite passed 68/68 tests.

### Reflection

The 15.4-minute result was useful precisely because the code was technically correct. It exposed the difference between **technical feasibility** and **product quality**.

Rather than changing the meaning of feasibility or asking AI alone to judge whether a route is long enough, the system now calculates objective budget-use information. Later AI selection can make subjective judgements about which places are interesting while Python can validate measurable constraints.

This reinforced the project's division of responsibility:

- AI: relevance, interest, and selection among real candidates.
- Python: validity, routing calculations, time constraints, and measurable validation.

---

## Sprint 4 – AI-assisted final selection

### Goal

Sprint 4 introduced the first AI decision in the pipeline: choosing which 2-5
stops from Sprint 3's shortlist actually form the walk, using the real
duration matrix Sprint 3 already fetches. Content generation (turning a stop
into a story or fact) was deliberately left for Sprint 5.

### Provider decision

I chose OpenAI for this sprint's stop-selection call rather than Anthropic,
specifically for this bounded structured-selection task, and asked Claude to
keep the integration isolated behind a small `select_stops()` function in
`ai.py` rather than letting OpenAI-specific request/response details leak
into `planner.py`. This was framed explicitly as a replaceable
implementation decision, not a permanent architectural dependency - the rest
of the application only calls `select_stops()` and does not know or care
which provider answers it. This leaves room to compare providers or models
later without rewriting route or planning logic.

The model itself is read from an `OPENAI_MODEL` environment variable rather
than hardcoded, so I can set it to `gpt-5.6-luna` now and compare against
`gpt-5.6-terra` later purely by editing `.env`.

### AI contribution

Claude implemented:

- `ai.py`: prompt construction, the OpenAI request/response handling, and
  parsing/validating that the response is the expected JSON shape
  (`{"selected_ids": [...]}`), forced via OpenAI's structured-output JSON
  schema rather than parsed from free text;
- `planner.py`'s new `plan_route()`: the orchestration function that
  shortlists candidates, fetches the real matrix, calls AI, validates the
  result, and retries or falls back;
- automated tests for both, with the OpenAI HTTP call mocked rather than
  making real requests.

### My decisions

Python continues to validate everything AI returns, unchanged from the
Sprint 3 design: selected ids must exist in the shortlist, must be unique,
the count must be 2-5, and the selection must be feasible within the
requested time using `check_feasibility()` from Sprint 3. AI cannot bypass
any of this - it only supplies candidate ids.

Sprint 3's manual test had already shown that a feasible selection can still
badly under-use the requested time. Since no permanent minimum-usage rule
has been agreed, I decided against baking a hard threshold into
`check_feasibility()`'s meaning of "feasible". Instead, Sprint 4 uses
`budget_usage_ratio` (already computed in Sprint 3) only to trigger one
extra retry, asking AI for a fuller selection, out of a shared two-retry
budget also used for invalid selections (unknown id, duplicate, wrong
count, infeasible). If retries run out, the best valid, feasible selection
seen is kept rather than discarded - a modest but working route is a better
outcome than an unnecessary "no suitable route" fallback.

**The 50% budget-usage retry threshold is explicitly provisional**, not a
final product requirement. It exists only to decide when to spend a retry
asking AI to do better; it does not reject anything on its own, and it may
be adjusted or replaced once there is real test data on what usage levels
actually feel acceptable to a walker.

### Testing

All OpenAI calls are mocked in `tests/test_ai.py` and `tests/test_planner.py`
- no automated test spends real API credits. Manual testing against a real
OpenAI call (using a real `OPENAI_API_KEY` and `OPENAI_MODEL` in `.env`) is
a separate, deliberate step I run myself via `python3 planner.py`, not part
of the automated suite.

### Reflection

This sprint's main decision was about where to draw the line between "AI's
judgment" and "Python's safety net" now that AI is actually in the loop.
Keeping the provider swappable and keeping the budget-usage rule a soft,
clearly-labelled retry trigger rather than a hard rule are both examples of
deferring a decision I'm not ready to make permanently, without blocking
progress on the sprint that needed *something* working now.

### Live testing exposed the retry-based design's real weakness

The first live run against `gpt-5.6-luna` failed on every attempt with an
OpenAI 429 error, and a second run timed out on the third attempt - both
infrastructure problems, not selection problems. I asked Claude to bump the
request timeout (30s to 60s) without changing anything else.

Once the API calls themselves were reaching OpenAI, a deeper problem showed
up. Two live requests for a 60-minute `public_art` walk both failed after
using all 3 attempts:

- `gpt-5.6-luna`: two different 5-stop selections, both reported as exactly
  75 minutes - no sign of the model correctly recomputing a different total
  for a different selection.
- `gpt-5.6-terra`: 5 stops (75 min) -> 4 stops (75 min) -> 3 stops (61 min) -
  visibly converging, but one retry short of success.

I asked Claude to add a per-attempt log (what AI proposed, and why Python
accepted or rejected it) before doing anything else, since the existing code
only reported the final failure reason and threw away what happened on
earlier attempts. That log is what made the pattern above visible at all.

My first response was to ask Claude to tighten the prompt: state the time
formula explicitly, tell the model to self-check its arithmetic before
answering, and include the previous selection in retry feedback (since each
`select_stops()` call is stateless and has no memory of its own prior
answer). This measurably helped - `terra`'s convergence above is a result of
it - but did not fully fix the problem.

### Independent diagnosis from Codex

I gave Codex the live evidence and asked for an independent diagnosis before
trying more prompt engineering. Codex's assessment: this was primarily an
**orchestration and input-design problem**, not (only) a model-capability
gap. The design was asking AI to interpret an indexed duration matrix,
choose a subset, find a good visiting order, sum legs, convert units, add
dwell time, and judge relevance - all at once, in a single structured-output
call with no room to show its work. Python was then independently
re-solving the same routing problem to validate the answer. Codex's
proposed fix: have Python enumerate every feasible 2-5 stop combination up
front (reusing `check_feasibility()` unchanged) and let AI choose only from
that pre-validated menu - AI keeps the relevance/interest judgement, Python
owns all the arithmetic, not just the validation of it.

I asked Claude to independently evaluate Codex's proposal rather than
implement it as-is, per the project's rule that neither AI's suggestions are
accepted without review. Claude agreed with the core diagnosis, and added
two refinements: (1) the offered menu had to stay bounded and ranked (all
1,573 possible combinations at the shortlist cap would blow up the prompt),
with an explicit rule that ranking must never *exclude* the only feasible
option(s) just because their usage is low - the 15-minute route from
Sprint 3's original manual test is exactly this case; (2) AI's response
changed from reproducing a raw id list to picking a short `option_key`
(`"option_1"`, ...), removing even a typo/mismatch risk, since Python
already knows each option's exact stops and order.

### Result

`ai.py` no longer sends a duration matrix or asks AI to compute anything;
its system prompt explicitly says every offered option is already checked
and AI should not try to recompute or second-guess that. `planner.py` gained
`_enumerate_feasible_combinations()` (reuses `check_feasibility()`, unchanged
arithmetic) and `_build_ai_options()` (ranks by budget usage, caps at 15
options). `plan_route()`'s retry loop is now a safety net for a failed
request or an unlisted `option_key`, not the mechanism for correcting bad
arithmetic - because AI can no longer produce bad arithmetic. A request with
zero feasible combinations is now detected immediately, before any AI call.
The 50% budget-usage threshold's retry role from earlier in this sprint is
gone entirely - usage is now a ranking signal Python computes once, not
something a retry loop coaxes AI toward.

### Reflection

The retry loop and prompt tightening earlier in this sprint treated the
symptom (bad answers) with more pressure on the model to be more careful.
The real fix was to stop asking the model to do arithmetic it isn't suited
for, and let Python do the part it's actually good at. The live per-attempt
log was what turned "it's not working" into evidence precise enough for
Codex to diagnose and for me to evaluate the fix against - a case for
building in that kind of visibility earlier, not just when something breaks.
### ORS estimates vs. other routing providers

Two manual comparisons against external map apps, both for real Jaunt-generated routes:

- A 60-minute `public_art` route: OpenRouteService estimated 38.4 minutes walking. Recreating approximately the same route externally produced 41 minutes in Maps.me and approximately 53 minutes in Google Maps, although the Google route required substituting a neighbouring building for two sculptures.
- A 45-minute `architecture` route (three churches): ORS estimated a 15.3-minute round trip. Using the same start point Jaunt actually used (an earlier comparison used the wrong start point and was discarded), Maps.me gave 20 minutes and Google Maps gave 18 minutes for the same full loop.

Both comparisons point the same direction: **ORS trends faster/more optimistic than Google Maps and Maps.me for this area**, by roughly 20-30%. This is not evidence of a bug - a follow-up check pulled ORS's own turn-by-turn directions for the church route and confirmed its duration-matrix numbers and its real routed path agree exactly, so Jaunt is reporting what ORS actually computes. It does mean the estimate itself runs optimistic relative to other providers.

This reinforces, with two independent data points now, that very high calculated budget utilisation should not automatically be treated as ideal: users may need a time buffer for routing-provider variation, walking speed, and time spent at stops, on top of whatever ORS reports.

### Route backtracking - deferred to Sprint 6

A separate manual test (a 45-minute `architecture` request) produced a 15.3-minute round trip through three churches that felt, on inspection of the real ORS turn-by-turn directions, like it wound through several short laneways rather than a clean loop. This raised the question of whether Jaunt should avoid ordering stops so the route backtracks along the same street.

Claude's assessment: this can't be solved well in Sprint 4. `plan_route()`'s ordering (`compute_best_order()`) only has point-to-point *durations* from the ORS matrix - not actual street geometry - so there is no way to detect that two legs reuse the same block without real route polylines, which Sprint 6 already adds. Attempting a geometry-free heuristic now would be guessing, not measuring.

Decision: noted in `docs/architecture-plan.md`'s Sprint 6 description as something to consider once real route geometry exists, rather than adding an unreliable approximation to Sprint 4.

### Sprint 4 closure: validation and outcome

The path to a working Sprint 4 was not linear, and the sequence matters more than the final result on its own:

1. **Automated tests passed first.** The original design - AI given the candidate stops and the raw ORS duration matrix, asked to select a feasible 2-5 stop combination itself - passed its full mocked test suite, because mocked AI responses can't exercise real arithmetic ability.
2. **Live testing failed.** Real OpenAI calls exposed repeated feasibility failures the mocks couldn't catch. For one 60-minute request, three consecutive attempts came back estimated at 75, 75, and 61 minutes - all over budget, with no reliable sign of the model correcting its own arithmetic between attempts.
3. **The failure was investigated, not patched over.** Rather than simply raising the retry count or hoping a more powerful model would compute better, a per-attempt log was added to see exactly what AI proposed at each try, which made the pattern (and, separately, a genuine 429/timeout infrastructure issue) visible enough to diagnose.
4. **The architecture was redesigned.** Python now derives every feasible 2-5 stop combination deterministically from the matrix (reusing Sprint 3's `check_feasibility()` unchanged) and offers AI a small, ranked menu of already-feasible options. AI no longer touches routing arithmetic at all - it returns an `option_key`, which Python validates against the menu it actually offered and maps back to the stored, pre-computed ordered stops.
5. **Independent review.** Codex reviewed the redesigned architecture and found it sound, with two small must-fix issues: non-retryable OpenAI/account errors (invalid credentials, exhausted quota) were being retried identically to ordinary transient failures instead of failing fast, and `docs/architecture-plan.md` still described the original matrix-to-AI design rather than the implemented one.
6. **Both issues were fixed** - `ai.py` now distinguishes a non-retryable `AiFatalError` from the ordinary retryable case, and the architecture document was brought back in line with the implementation.
7. **Automated tests passed again**, now covering the actual failure modes rather than ones mocking could paper over: 112/112 tests, clean compilation, no whitespace issues.
8. **A final live test succeeded on the first attempt.** For a 40-minute request, AI selected `option_2` on try 1 (no retries needed): 14.8 minutes walking, 25.0 minutes dwell, 39.8 minutes total, feasible within budget. The displayed 100% budget usage is rounding - the underlying ratio is approximately 99.5%.

### Two things to carry into Sprint 6, not resolve now

**Near-100% budget usage is not automatically the ideal result.** Routing estimates and real walking/dwell time both vary - see "ORS estimates vs. other routing providers" above - so a route using nearly the entire requested time leaves no margin for that variation. An appropriate comfort margin (e.g. an upper usage target below 100%) should be evaluated against real-world test data in Sprint 6, not introduced as an unsupported guess now.

**Routing-provider accuracy is a separate, already-tracked question.** The ORS-vs-Google/Maps.me differences observed during manual testing were checked and found to be internally consistent on Jaunt's side (the duration matrix and ORS's own turn-by-turn directions agree exactly) - there is no evidence of a Jaunt calculation bug. Whether ORS's estimates track real walking time closely enough is a routing-provider-accuracy question for the Sprint 6 real-world test, not a Sprint 4 defect.

---

## Sprint 5 – A second public_art source: Inner West Council's "Perfect Match" street art

### Goal

The OSM-only catalogue had very few `public_art` stops. Inner West Council
publishes its own "Perfect Match" street art dataset (council/artist fields
plus a friend's personal visit notes, as an .xlsx export) covering Newtown
and neighbouring suburbs, with a real artist statement for most artworks -
exactly the kind of quotable, attributable source material the project
requires. The goal was to bring this in as a second source for the same
`public_art` topic, alongside OSM, without inventing or rewriting any of it.

### AI contribution

Before writing any code, Claude inspected the source file directly (raw XML
inside the .xlsx, before openpyxl was even installed) rather than trusting
the file's summary description. This surfaced several real data problems
not mentioned in the original request:

- the sheet's own "Number" column - the obvious choice for a record id - has
  three duplicated values and four rows containing the literal text "##"
  (an Excel overflow artifact), so it can't be used as an id;
- 10 rows have no usable artwork title: 5 blank cells, 3 with the literal
  placeholder text "TBC", and 2 using the council's own "*Title" marker for
  "no title recorded". The first 8 were found on first inspection; the "*Title"
  pair was missed initially - it was imported as if it were a real artwork
  name - and only caught by scanning for repeated/odd titles after the first
  import run;
- two Statement cells are placeholder text ("TBC", "CARPARK"), not real
  artist statements;
- the first geocoding pass (using the "Full Address" column directly)
  failed for 42 of ~165 addresses - mostly because Full Address often
  prefixes the real street address with a venue name Nominatim's geocoder
  couldn't resolve (e.g. "IGA Wall, 259 King St, Newtown"). The sheet has a
  separate "Street Address" column that is usually the same address with
  the venue name already stripped, so Claude added it as an automatic
  fallback query when the first attempt fails - not a different or guessed
  address, the council's own alternate column for the same location. This
  cut failures from 42 to 21.

Claude then implemented `import_street_art.py`, reusing `import_places.py`'s
existing `load_existing()`, `save_records()`, and `mark_duplicates()`
directly (imported, not copied) so the two scripts share one atomic-save and
resume convention rather than two.

### My decisions

I decided the street art records should merge into the same
`data/sydney_places.json` file OSM already writes to, rather than a separate
file, since both `planner.py` and `app.py` already read a single path and
the id namespaces (`node/`, `way/`, `perfect_match/`) can't collide. The
trade-off Claude flagged: `import_places.py`'s `mark_duplicates()` now runs
across both sources whenever either script is rerun, which could catch a
genuine cross-source duplicate (the same real mural in both datasets) or
could be an unwanted coupling. I accepted this as a reasonable trade-off for
a much simpler integration, but see "known limitation" below - it doesn't
fully work.

I decided to add `openpyxl` as a real dependency rather than requiring a
manual CSV export step, since a manual export step conflicts with the
product brief's "automatically collected" V1 principle and would need
re-doing by hand if the source file is ever updated.

I decided to import all suburbs in the dataset (not just the 36 Newtown
rows), since `planner.shortlist_candidates()` already filters candidates by
distance from whatever start point is given - out-of-range records are
simply unused, not wrongly surfaced - and this needs no suburb-matching code
at all.

Records marked "No Longer Visible" by the friend's personal tracking must
not become `ready` stops. I forced these to `status: "rejected"` with an
explicit `rejection_reason`, reusing the catalogue's existing three-value
status vocabulary rather than adding a fourth status. The friend's own
tracking fields (Status, Visited Date, Photo, KM Walked) are kept in a
separate `field_notes` object with their own source label, are never used as
`source_excerpt`, and are outside `app.py`'s `PUBLIC_FIELDS` allowlist, so
they can never reach the frontend even by accident.

### Result

(Superseded by the fixes below - see "Independent review" for the numbers
actually shipped.) 123 of 173 artwork rows became `ready`, 4 `limited` (real
title, no usable statement), 46 `rejected` (10 missing/placeholder title, 14
"No Longer Visible", 21 failed geocoding after both address attempts, 1
cross-source duplicate of an existing OSM record caught by the automatic
`mark_duplicates()` pass). 46 ready records fall inside the existing Newtown
pilot bounding box. The 21 addresses that still failed geocoding (mostly
street-corner descriptions like "Corner of Pidcock and Mallet St" and bare
landmark names like "Town Square" with no street number) are listed by the
script rather than guessed at.

`shortlist_candidates(start_lat, start_lon, "public_art")` from the same
Newtown start point `planner.py`'s own manual demo uses now returns a mix of
OSM and council-sourced stops, confirming the two sources integrate without
any change to `planner.py` or `app.py`.

### Known limitation found during verification

`mark_duplicates()` did not catch a real duplicate: "I Have a Dream" (Andrew
Aiken, 1991) exists in both datasets, but the council's address-geocoded
coordinate and OSM's precisely-placed node are 201m apart - well outside the
75m dedup radius, which was tuned for OSM's own node-vs-way duplicates, not
for comparing a precise pin against a geocoded street address. This was
initially left as a known issue rather than patched with an arbitrary radius
increase - see "Independent review" below for how it was actually resolved.

### Independent review

I asked Codex to review the importer independently before treating Sprint 5
as closed. It found three real bugs by reproducing each one rather than just
reading the code, plus the documentation inconsistency above (this section's
title count was fixed to 10 as a result):

1. **A `ready` record never re-checked the spreadsheet.** `build_record()`
   returned a cached `ready` record immediately, without looking at the
   current spreadsheet row at all. If the friend later marked a
   previously-`ready` artwork "No Longer Visible", rerunning the importer
   would not pick that up - the artwork would stay a walkable stop forever.
   Codex reproduced this directly.
2. **A failed geocode was cached permanently.** `geocode_address()` cached
   every outcome, including an HTTP error or network failure, keyed by the
   query string. Codex simulated an HTTP 503 followed by a rerun and showed
   the "retry" only ever read the cached failure - no second request was
   ever made, so a purely transient failure could never recover.
3. **The same real mural could be offered twice in one walk.** The known
   limitation above is real and does affect route correctness, not just
   catalogue tidiness: `shortlist_candidates()` for a Newtown start point
   returns both records. Codex's suggested fix - a small, explicitly
   reviewed mapping of confirmed cross-source duplicates, not a wider
   automatic radius - matched what the limitation note above had already
   flagged as the right trade-off, so it was implemented rather than left
   open.

### Changes made

- `build_record()` no longer short-circuits on a cached `ready` record. Every
  street-art record is rebuilt from the spreadsheet on every run. This costs
  nothing extra over the network: geocoding was already cached separately by
  address, so a previously-successful lookup is still reused without a new
  request.
- `geocode_address()` now only writes to the cache on a successful lookup.
  An HTTP error, network exception, or a clean "no results" answer is never
  cached, so it is retried on the next run rather than frozen as permanent.
- Before finalising which artworks appear twice, I asked Claude to search
  for *all* cross-source name matches between the two "ready" sets, not just
  the one found by accident during manual testing. This turned up a second
  real duplicate ("Block Party", Sharon Billinge, 2023, 160m apart) that had
  been missed. Both pairs were confirmed by matching artist and year before
  being added to a small, explicit `CROSS_SOURCE_DUPLICATES` mapping, applied
  as a reviewed override after the automatic `mark_duplicates()` pass. The
  OSM record is kept in each pair, since it has a more precisely placed
  coordinate than this dataset's geocoded address.
- Added `tests/test_import_street_art.py`, including regression tests that
  reproduce all three bugs directly (a record built `ready` then rebuilt
  from a row later marked "No Longer Visible"; a mocked HTTP 503 followed by
  a mocked-success retry; the manual duplicate override).

After the fixes: 123 ready / 4 limited / 46 rejected became 121 ready / 4
limited / 48 rejected once the two confirmed cross-source duplicates were
also rejected. All 112 pre-existing tests plus the new importer tests pass.

### Reflection

The original "not a bug" framing for the duplicate-mural issue was wrong in
an important way: it correctly identified that a global radius increase
would be the wrong fix, but incorrectly concluded that meant no fix should
be attempted now. A small, explicitly reviewed list was available the whole
time and required no risky heuristic - the actual work was searching
properly for every cross-source match instead of only the one already
noticed. Codex's review was valuable specifically because it reproduced each
bug rather than trusting the code's own comments and docstrings, which is
what caught the stale-cache and permanent-failure-cache bugs that reading
the code alone (including my own review while writing it) had missed.

---

## Sprint 6 – A `heritage` topic: NSW official heritage data, curated rather than scraped

### Goal

Add a third topic - broader architecture/history than just churches - using
NSW's official Heritage MapServer (state and locally-listed heritage items),
covering Newtown and neighbouring suburbs.

### Research, before writing any code

I asked Claude to research the available NSW ArcGIS heritage layers before
proposing anything. It queried the live services directly rather than
assuming field names or coverage, and found real problems in the data that
weren't obvious from the layer names:

- The Local Environmental Plan layer's own `H_ID` field is not globally
  unique - the same code means a different real place under different
  councils' plans. `HeritageItemID` is the reliable identifier.
- Several genuine single items are mapped as multiple points sharing one
  `HeritageItemID` (e.g. "Brick paving", 13 points for one linear feature) -
  needs deduplication, not treated as 13 separate stops.
- The State-significance rows inside the Local Environmental Plan layer
  mostly just restate what the State Heritage Register layer already has
  more cleanly - using both without filtering would double up the same real
  building.
- Some `H_NAME` values contain mojibake from NSW's own data export pipeline
  (double-encoded smart quotes). Not something to guess a fix for.

### The key finding: official descriptive text is not scrapable without misrepresenting the client

The ArcGIS layers themselves carry no Statement of Significance, Description,
or History text - only identifying/administrative fields. That text lives
in a separate interactive application (`hms.heritage.nsw.gov.au`), and
Claude confirmed directly (not assumed) that it sits behind a WAF that
returns HTTP 403 to any request identifying itself honestly as a script -
including this project's own identifying User-Agent - and only serves
content to a request presenting a spoofed real-browser User-Agent. Claude
flagged this explicitly rather than quietly building around it, and also
checked for an official structured/bulk alternative (data.nsw.gov.au, SEED,
and the published Data Dictionary PDF for the EPI Heritage layer) before
concluding there isn't one - the descriptive text genuinely only exists
inside the WAF-protected application.

### My decision

I told Claude not to spoof a browser identity or otherwise work around the
WAF, for this project or otherwise. Automated bulk scraping of official text
behind an access control it clearly doesn't want scripts to have is a
different thing from querying the same department's open ArcGIS REST API,
which welcomes scripted access and answered every request normally.

Instead of automated retrieval, the pipeline uses a small, human-curated
seed file (`data/heritage_source_text.json`) that a person fills in by hand
from the public HMS page, one item at a time. Claude tested its own
browsing tool against two of the approved pages first and got the same 403
both times, confirming this isn't a workaround-able quirk of one automated
method - so all 29 approved items currently need manual retrieval, which is
reported clearly rather than left silently empty with no explanation.

I also decided the source-text field should mean one specific thing
(verbatim Statement of Significance) rather than silently falling back to
Description or History when significance is missing - consistency of
meaning across records matters more than maximising how many end up
`ready`.

### Result

(Superseded by "Sprint 6 completion" below.) `import_heritage.py` covers 29
hand-reviewed candidates (7 State Heritage Register, 22 local items), chosen
from the full official candidate pool (~174 individual items in the pilot
bbox after filtering out conservation areas and archaeological sites) for
geographic spread and type variety - pubs, a theatre, rail infrastructure,
churches, named houses/terraces, and commercial/industrial buildings, not
just churches. Coordinates and names come directly from ArcGIS (Layers 4 and
5); no geocoding needed. All 29 landed inside the existing Newtown pilot
bounding box on the live run, and all 29 approved ids were still present in
ArcGIS (nothing delisted or renumbered since research). At this point all 29
were `limited`, pending manual Statement of Significance retrieval into the
seed file - correct and honest given no text had been supplied yet, not a
bug.

### Reflection

This sprint's interesting decision wasn't technical - it would have been
easy to spoof a User-Agent and call it done, since the data itself really is
public and non-authenticated. The reason not to is that "the content is
public" and "the server is willing to serve it to an honest request" are
different facts, and the second one was tested and came back no. Treating an
access control as an obstacle to code around, rather than as a signal to
stop and ask, would have quietly baked a misrepresentation into the
project's own data pipeline.

### Sprint 6 completion

I manually opened each of the 29 approved items' HMS pages myself and
transcribed their Statement of Significance verbatim into
`data/heritage_source_text.json` - the manual step the WAF decision above
made necessary. Pasting real multi-paragraph text directly into JSON by hand
produced two real problems along the way, both found by checking actual
file/tool state rather than assumed:

- The first save attempt didn't reach disk (an unsaved editor buffer) -
  confirmed by inspecting the raw file content, not by trusting "I've saved
  it."
- The second attempt produced invalid JSON (literal newlines/tabs inside
  string values). Fixed by parsing with `json.loads(..., strict=False)` and
  re-serializing - which properly escapes those characters without touching
  a single character of the transcribed wording - then verified with a
  field-by-field diff against the pre-repair parse showing zero content
  drift.

All 29 Statements of Significance are now supplied, and before any
cross-source duplicate handling, all 29 heritage records were `ready`.
**The manual transcription itself has not been independently checked against
the live HMS pages** - I typed what I read, but no second pass has confirmed
character-for-character accuracy. Worth a spot-check before treating this
catalogue as fully verified.

An independent review then found two real gaps, addressed directly rather
than deferred:

1. **Two confirmed cross-source duplicates with OSM**, found by comparing
   the heritage and OSM catalogues directly: "Uniting Church and Pipe Organ"
   (`heritage/5045004`) is the same building as OSM's "Newtown Mission"
   (`way/548526874`), and "St Stephen's Anglican Church and Cemetery"
   (`heritage/5045479`) is the same building as OSM's "St Stephen's Anglican
   Church" (`way/172735168`). Neither pair is caught by the existing 75m
   name-matching dedup (the names differ), and the general threshold was
   deliberately not widened, for the same reason as Sprint 5's identical
   OSM/street-art gap: it risks false positives elsewhere. Instead, a small
   reviewed `CROSS_SOURCE_DUPLICATES` mapping in `import_heritage.py` -
   following Sprint 5's own convention - rejects the OSM side of each pair.
   Unlike Sprint 5 (where OSM was kept for its more precise coordinate), the
   **heritage record is kept here**: it carries the official NSW Statement of
   Significance, a heritage-authority assessment, rather than a
   general-purpose Wikipedia/Wikidata summary, and keeping the heritage
   record preserves the `heritage` topic itself. The two OSM records
   (`way/548526874`, `way/172735168`) are now `rejected` with reason
   `"duplicate of heritage/... (reviewed cross-source match)"`; the two
   heritage records remain `ready` under the `heritage` topic.
2. **A whitespace-only or non-string statement could have counted as
   "present."** `build_record()` now requires `statement_of_significance` to
   be a string with at least one non-whitespace character before marking a
   record `ready` - stripping is used only to check this, never to modify
   what's actually stored in `source_excerpt`.
3. **A partial ArcGIS response could have overwritten a good catalogue with
   a stale one.** If any approved id isn't returned by ArcGIS on a given run,
   `main()` now aborts with a clear list of the missing ids before
   `save_records()` is ever called, instead of silently saving whatever
   partial set came back as though the import had fully succeeded.

Also fixed: two existing street-art tests were silently making real network
calls to Nominatim (found by temporarily forcing `requests.get` to raise
inside the whole test module and seeing exactly which tests broke, rather
than guessing). Both needed a geocode result and had an incomplete cache;
both now mock the response instead, with no change to what each test
actually verifies.

Final state: 29/29 heritage records `ready`, 226 total catalogue records,
167/167 tests passing (added: source-text validation, the cross-source
duplicate override, the abort-on-missing-ids path, and direct query-string
coverage confirming State queries use `HOITEMID` against Layer 5 and Local
queries use `HeritageItemID` against Layer 4 with the researched
`LAY_CLASS`/`SIG` filters).

No upstream NSW wording was corrected or cleaned up in this pass - any typo
or unusual phrasing inside a transcribed Statement of Significance is left
exactly as the source states it, on the same "verbatim or don't use it"
principle as everywhere else in this project. Deterministic ordering for
multi-point local items (beyond "keep the first point seen") was considered
and deliberately left for a later pass, not implemented here.

## 2026-10-23 — Story1.9 preference signal (Codex temporary developer)

Connected the approved existing slider/state through the stateless API and planner retries to AI selection. Added candidate source type/title; preference remains qualitative, evidence-based guidance rather than Python prominence scoring or filtering. Defaults to Balanced only when omitted; explicit invalid values are rejected before provider calls. Re-Jaunt/replacement retain their hard constraints.

Independent BMAD review clarified preference before the budget tie-breaker and strengthened integration/recovery coverage. Final checks:288 Python tests,37 native Node tests, JS syntax/diff checks and real Chrome mobile/keyboard/request checks with intercepted planning responses. No paid calls or catalogue edits. Newtown selection contrast needs later live evaluation; accepted examples are Bank Hotel/I Have A Dream versus St Peters station/Cragos Flour Mills, subject to feasible availability and adequate source evidence. User walkthrough pending; see build spec and AI-discussions.md for handover.


## 2026-10-23 — Preference-aware candidate discovery follow-up

User testing exposed weak landmark results. Replaced nearest-only candidate discovery with AI ordering/selection over the wider eligible pool before the12-place routing cap. General knowledge can inform recognisability, while generated stories remain source-grounded. Added feasible leading-prefix options so short matching walks reach final selection; retained AD-7 coverage and15-option bound. One nearest recovery follows honest preferred-attempt failure; technical errors remain technical. Small ordinary pools5–12 rank all IDs;<=4 and fitting replacements avoid needless discovery. Hard exclusions/retention unchanged.

Independent three-layer review completed; patched recovery diagnostics, coordinate context, retry feedback and transport/constraint tests. Final305 Python and37 Node tests pass; no paid calls. Actual catalogue105-candidate prompt measured51269 characters, with mocked orchestration confirming Enmore can reach a short feasible option despite being outside old nearest12. No live quality/cost/latency claim. Both test servers restarted; user acceptance remains pending. Main/baseline untouched; local safeguard3372b87c5443bc10e740201130f61abc4b59d8df.


## 2026-10-23 — Remaining Epic1 stories1.10/1.11 (Codex temporary developer)

Implemented explicit one-shot location with native browser permission,10s application deadline covering unanswered permission, valid coordinate persistence/map centering and stale callback cancellation after manual selection/navigation. Denial/errors preserve named/map choices. No continuous GPS. Independent review strengthened timeout/camera/manual-race coverage; native API/permission states checked in isolated Chrome with emulated coordinates, not actual user location. Real OS/phone HTTPS/accessibility test remains pending.

Implemented optional rights-cleared detail photos from curated sidecar and local assets, independent of catalogue imports. One verified original Post Office image by Sardaka under CC BY3.0, with creator/source/licence/change credit and useful alt. Stored initial coverage0/159; curated audited coverage1/159, not exhaustive availability. Missing/broken/invalid metadata remains text-only, including saved-trip recovery; no thumbnails/map-photo pins. Review patched optional-data route rejection, root-resolution fallback and HTTP/image-source verification.

Combined final311 Python and56 Node tests pass, plus syntax/diff and real Chrome390/320px image/load/error/reload checks. All automated provider work mocked; no paid calls. Test server5056 current; temporary remote gateway/tunnel stopped per user deferral. Local checkpoint14238b0e11f3a33ad7871d6d2343bf207fffd779 preserves1.10 before photo changes. All Epic1 features implemented, remaining acceptance statuses stay review; stop before Epic2. Use docs/epic-1-acceptance-checklist.md. Examiner demo/shared request deadline and other prior deferred work remain outside this batch.


## 2026-10-23 — Confirm current-location pin before advancing

User feedback superseded the initial GPS immediate-advance flow. Reused pending-pin confirmation for current location; visible panel map guidance, forest action and spacing restore intended setup usability. GPS preview stays uncommitted until confirmation; manual relocation/old start/reload/race rules preserved. Review identified short-screen map occlusion, fixed with measured camera offset and resize handling.57 frontend tests and rendered native-API-emulated browser checks across portrait/narrow/landscape pass; no backend/paid-call change. See spec-location-preview-confirmation.md.
