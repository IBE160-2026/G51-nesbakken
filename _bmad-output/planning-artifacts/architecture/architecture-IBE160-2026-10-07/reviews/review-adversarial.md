---
review-type: adversarial (BMAD architecture-spine Reviewer Gate)
target: ARCHITECTURE-SPINE.md (Jaunt frontend-wiring slice)
reviewed-against: ARCHITECTURE-SPINE.md + .memlog.md (same folder), 2026-10-07
method: for each AD, construct two independently-built units that each obey every written rule to the letter, yet build incompatibly with each other
---

# Adversarial Review — Jaunt frontend-wiring slice architecture spine

## Verdict

The spine is well-reasoned on the decisions it explicitly elicited (AD-1 tile stack, AD-3 content timing, AD-4 preference signal), but it has at least two **critical**, genuinely integration-breaking holes — one a flat self-contradiction between AD-2 and AD-6 over what "end trip" clears, the other an underspecified relationship between AD-5's `excluded_ids` and AD-6's visit history that two compliant builders would resolve in opposite, incompatible ways — plus several lower-severity payload-shape and rendering-boundary gaps that the spine's own "Deferred" section incorrectly dismisses as low-risk. None of these are violations of anything written; they are gaps the written rules leave open. Recommend: do not close this gate until AD-5/AD-6 and AD-2/AD-6 are reconciled with one new or tightened AD, and the stop/content payload shape (AD-3) gets at least a minimal field inventory.

---

## Finding 1 — CRITICAL: AD-2's "end trip" clear vs. AD-6's "same trip-state" storage location

**The clash.** AD-2's Rule: "the frontend persists the active trip to `localStorage` so an accidental refresh doesn't lose progress; an explicit 'end trip' action clears it." AD-6's Rule: "previously-visited/favourited place ids live in **the same client-side `localStorage` trip-state**" (emphasis on the spine's own wording). Read literally, AD-6 puts visit history *inside* the exact object AD-2 says "end trip" clears.

**Two compliant builders:**
- **Builder A** (implements the "end trip" action) reads AD-2's rule as the authority on what gets cleared, and AD-6's rule as the authority on *where* history lives ("the same... trip-state"). Puts visited/favourited ids inside `localStorage['jaunt_trip']` alongside route/stops/content. "End trip" does `localStorage.removeItem('jaunt_trip')` — fully compliant with AD-2's literal instruction, and with AD-6's literal "same... trip-state" wording.
- **Builder B** (implements the planning request's history payload, independently, perhaps a sprint later) reasons from *purpose*: FR-17/18 and the Deferred section's own note on PRD Open Question 7 ("visit-history retention/expiry... remains genuinely undecided") only make sense if history survives across trips — a history that's wiped every time a trip ends can't filter repeats or weight variety on the *next* trip. Implements a separate, persistent key `localStorage['jaunt_history']` that "end trip" does **not** touch.

**Why this breaks at integration, not just diverges in style:** if Builder A's "end trip" ships first, every "end trip" silently erases the exact data FR-17/18 depend on, and Builder B's planning-payload code (reading from `jaunt_history`, which Builder A never writes to because Builder A folded history into `jaunt_trip`) finds nothing there — visit-based filtering/weighting never fires, with no error, just quietly inert. Neither builder violated a single written rule.

**Close with:** a new sentence in AD-6 (or a split AD-2a) stating explicitly: visit history is a **separate, persistent** localStorage key from the active-trip key; "end trip" (AD-2) clears only the active-trip key; a *different*, currently-undecided mechanism governs if/when history itself is ever cleared (this is exactly where PRD OQ-7 should get its own explicit storage-key answer, not just a "remains undecided" note).

---

## Finding 2 — CRITICAL: AD-5's `excluded_ids` vs. AD-6's visit-history ids — same list or two, hard filter or soft weight?

This is the pair the Reviewer Gate specifically asked me to pressure-test, and it holds up as a real hole.

**The clash.** AD-5: the selection path "takes an `excluded_ids` parameter" — described entirely as rejected stops from a Replace/Re-Jaunt action within the current trip; a hard exclusion. AD-6: "previously-visited/favourited place ids... sent as part of the planning request payload so Python can **filter repeats** and AI can **weight variety accordingly**." That one sentence names *two different mechanisms* (a hard Python-side filter, and a soft AI-side weighting signal) without saying which ids go through which path, or whether AD-6's ids and AD-5's `excluded_ids` are the same parameter or two.

There is a second, sharper version of the same gap buried in AD-6's own wording: it bundles "visited" and "favourited" ids into one undifferentiated bucket. Visited-and-not-revisited is a "don't repeat" signal; favourited is almost certainly meant as the opposite — "resurface this, the user liked it" — yet AD-6's Rule never distinguishes them, and describes both as flowing into the same filter/weight sentence.

**Two compliant builders:**
- **Builder A** (planner.py's selection-path signature) reads AD-5 literally as defining one parameter, `excluded_ids`, and reads AD-6's "filter repeats" as instructing that visited+favourited ids get unioned straight into that same parameter before calling selection. Favouriting a place now permanently hard-excludes it from every future trip — probably the opposite of what a "favourite" should do, but nothing in AD-6 says otherwise.
- **Builder B** (the frontend payload builder, or a differently-scoped planner.py change) reads AD-6's "AI can weight variety accordingly" as requiring visited/favourited ids to reach the AI prompt as a **separate, soft** signal, never merged into the hard `excluded_ids` list — specifically so a favourited place *can* still be suggested again. Sends a second field, e.g. `visit_history: [...]`, distinct from `excluded_ids`.

**Why this breaks at integration:** if the frontend is built to Builder B's two-field model but planner.py is built to Builder A's one-field model (or vice versa), the second field is silently ignored — either previously-visited places keep reappearing when the spec clearly wants repeats filtered, or favourited places get hard-excluded exactly like an explicit reject, which a user would reasonably read as a bug ("why does favouriting a place make it never show up again?"). Both builders followed AD-5 and AD-6 to the letter; the letter just doesn't say which of these two shapes is correct.

The Consistency Conventions table's naming row ("Place/stop identity is the catalogue's existing `id` field... `excluded_ids`/history lists never mint a second id scheme") only guarantees the *id values* are consistent — it says nothing about whether exclusion and history are one list or two, so it does not close this gap, despite reading as if it might.

**Close with:** a new AD (or a tightened AD-5/AD-6) that states explicitly: (a) whether `excluded_ids` and visit-history ids are the same request field or two distinct fields; (b) whether visited ids are a hard filter, a soft AI-weighting signal, or both; (c) whether favourited ids get the *same* treatment as visited ids or the opposite (resurfaced, not suppressed); (d) whether an id used once via AD-5 (a same-trip reject) graduates into AD-6's persistent history after the trip ends, or is forgotten once that trip's `excluded_ids` list goes out of scope.

---

## Finding 3 — HIGH: AD-3's "complete payload" — stop/content schema not pinned, and the spine's own Deferred section wrongly waves this off

The Reviewer Gate brief specifically asked whether the app.py/planner.py/ai.py boundary's "complete payload" is actually pinned down field-by-field. It is not, and the spine's Deferred section explicitly (and incorrectly, on this evidence) calls this low-risk: *"Exact `/api/...` endpoint names and payload field names... not a genuine two-builder divergence risk, left to epic/story-level detail."*

**The clash.** AD-3 only says content generation for every stop "runs synchronously... One complete payload goes to the frontend and into `localStorage`." It never enumerates what a "stop" object contains. At minimum the following are genuinely undecided by anything written: whether `content` (FR-19) is a single string or a structured object with named sub-fields (the memlog's own phrasing elsewhere gestures at "fun fact"/story/task as possibly distinct pieces); and where per-stop attribution lives for FR-20 (OSM/ORS/Wikipedia/NSW Heritage/Inner West Council) — inside each stop object (so a per-stop "Source: Wikipedia" credit can render) or as a single global footer unrelated to any one stop's fields. The Deferred section separately (and correctly) flags FR-20's attribution *UI* as unresolved, but FR-20's attribution *data shape inside the payload* is a different question that AD-3 should own and currently doesn't.

**Two compliant builders:**
- **Builder A** (ai.py's `generate_content()` + the planning endpoint assembling the response) emits `stop.content` as a flat string and no attribution fields on the stop at all, since nothing in AD-3 requires them.
- **Builder B** (the frontend, built independently against DESIGN.md/EXPERIENCE.md's per-stop attribution requirement) renders `stop.attribution.source_name` / `stop.attribution.source_url` per stop, assuming the backend supplies them per FR-20.

**Why this breaks:** the frontend renders `undefined`/blank attribution for every stop, or throws on the missing nested object — a visible defect at demo time, with neither side having broken a written rule. "Left to epic/story-level detail" is a reasonable call for *endpoint names*; it is not a reasonable call for *this* field, because FR-20 and FR-19 both already exist and already collide at exactly this boundary.

**Close with:** AD-3 (or a new AD-3a) should give the stop object a minimal, named field inventory — even just `{id, name, order, content, attribution}` with `attribution` pinned as present-or-absent-by-convention — rather than leaving the entire shape to story-level discovery.

---

## Finding 4 — HIGH: Consistency Conventions' two-shape error convention has no slot for a per-stop FR-19 grounding failure

The Reviewer Gate brief specifically asked about this. The table defines exactly two shapes: ordinary infeasibility as `200 {"feasible": false, ...}`, and genuine system failure as non-2xx (mirroring `CatalogueError` → 503). FR-19's content-generation function is explicitly paired with "a grounding check" in the Structural Seed, and that check can fail for **one stop** inside an otherwise-successful 6-stop route. Neither documented shape fits: it's not "no suitable route" (the route *is* feasible), and treating it as a system failure contradicts AD-3's own explicitly-stated purpose ("keep the walk itself working if connectivity drops" — i.e., resilience, not an all-or-nothing teardown).

**Two compliant builders:**
- **Builder A** treats a grounding-check failure as a genuine system failure (it can't produce AD-3's "complete payload"), raises, and lets app.py return it as a 503 — same bucket as an AI-credentials outage. A single stop's content hiccup now fails the *entire* route.
- **Builder B** treats it as a per-stop business-level degradation, returns a normal `200 {"feasible": true, ...}`, but invents an undocumented marker inside that one stop — e.g. `content: null` or `{"content_failed": true}` — that nothing else in the spine defines, so no frontend builder reading only the Consistency Conventions table would know to check for it.

**Why this breaks:** Builder A's version makes one weak grounding-check result nuke a perfectly good route (the opposite of AD-3's stated intent); Builder B's version introduces a third, silent failure shape that only exists if a frontend builder happens to guess it. Both comply with "never raise for a business case, reserve non-2xx for system failures" — the table just never anticipated a failure that's per-item inside an otherwise-successful response.

**Close with:** extend the Consistency Conventions error-shape row (or add a dedicated sub-rule under AD-3) to name this third case explicitly: a per-stop content/grounding failure is **not** a request-level failure; it degrades that one stop in place inside a normal `200` response, with a named field for the frontend to check (e.g. `stop.content_unavailable: true` + a user-facing fallback string) — and route feasibility is never revoked because of it.

---

## Finding 5 — MEDIUM: AD-1 binds "park" styling but the Rule never addresses parks

AD-1's Binds line explicitly claims to govern "stop/**park**/live-position styling," but the Rule's two sub-bullets only ever classify: (bucket 1 — GeoJSON layers) route line, background amenity points, no-photo stop circles; (bucket 2 — DOM Marker) live-position marker, photo'd stop pins. Parks are named as governed, then never mentioned again.

**Two compliant builders:** Builder A renders parks as GeoJSON polygon/fill layers (reasoning: "background," data-driven, no custom image content needed — fits bucket 1's stated criterion). Builder B renders each park as a DOM `Marker({element})` with a custom park icon (reasoning: parks need a distinct visual treatmentDESIGN.md likely specifies, closer to "needs real image/icon content" than a plain circle). Both are defensible readings of a Rule that simply never says. If one builder's z-ordering/click-handling assumes parks are GeoJSON features (queryable via `map.queryRenderedFeatures`) and another's code elsewhere assumes parks are DOM markers (queryable via `document.querySelector`), any shared "what did the user tap" handler breaks for park taps.

**Close with:** add one line to AD-1 explicitly classifying parks into one of the two buckets (background amenity-style data almost certainly means GeoJSON fill layer, consistent with the other "background" features already in that bucket).

---

## Finding 6 — MEDIUM: AD-1's photo/no-photo split on *stops specifically* creates two rendering mechanisms for one conceptual entity, with no shared addressing scheme

AD-1 splits "numbered stop circles with no photo" (GeoJSON circle layer) from "a rights-cleared-photo stop pin" (DOM Marker) — i.e., within the single conceptual category "stop," which mechanism applies depends on a per-stop data value (does this stop have a cleared photo?), not a fixed category. A single 7-stop route can plausibly mix both.

**Two compliant builders:** Builder A, needing a "selected stop" highlight or a "jump to stop N" list to scroll/highlight the correct map feature, implements that lookup against MapLibre's GeoJSON feature-state API (`setFeatureState` by stop id) — which silently does nothing for the subset of stops actually rendered as DOM markers. Builder B implements the same lookup against `document.querySelector('[data-stop-id=...]')` — which silently does nothing for the subset rendered as GeoJSON circles. Each is "correct" for the stop-rendering rule AD-1 states; neither handles the other's half of the mixed set, and the gap is invisible until a route happens to contain both kinds of stop on the same screen.

**Close with:** AD-1 should name a single, rendering-mechanism-independent addressing scheme for "find/highlight the map feature for stop id X" (e.g., both GeoJSON features and DOM markers get the catalogue `id` attached — as a feature property and as a `data-stop-id` attribute respectively — and any code that needs to address "the stop" does both lookups, not just one).

---

## Finding 7 — LOW/MEDIUM: AD-4's preference value representation is unpinned across the Browser→API boundary

AD-4 names the preference signal only descriptively ("Balanced/landmark-leaning/hidden-gem-leaning" in the memlog) and says it "passes into AI's existing selection prompt," but never pins the wire representation. A UI slider (continuous) and a 3-way discrete choice are both plausible readings of "leaning," and DESIGN.md/EXPERIENCE.md are outside this review's scope to check, but the spine itself should pin this at the API boundary regardless of which UI shape wins, since app.py and the frontend are built by different sessions.

**Two compliant builders:** Builder A (app.py) expects `preference: "hidden_gem" | "balanced" | "landmark"` (enum). Builder B (frontend) sends `preference_bias: 0.73` (continuous slider value), reasoning that "leaning" implies a spectrum. Whichever side is "wrong" gets a value it silently can't interpret (an unrecognized enum string, or a float where a string was expected) and the preference signal is dropped or mishandled with no error surfaced (nothing in the Consistency Conventions table requires validating this field, so it likely fails open/silently).

**Close with:** AD-4 should state the exact wire type (string enum vs. numeric range) for the preference value, independent of whatever UI control produces it.

---

## Secondary note — AD-5 / AD-2 interaction: does the frontend resend the *full* accumulated `excluded_ids` every call?

AD-2 establishes the backend has no memory between requests. AD-5 says the selection path "takes an `excluded_ids` parameter" and that Replace/Re-Jaunt "re-runs with the rejected stop(s) added to that exclusion list" — but never states that the caller (the frontend) is responsible for re-sending the **full, accumulated** list on every call, as opposed to just the single newly-rejected id and trusting some accumulation that AD-2 explicitly rules out server-side. A builder who treats AD-5 as adding to "that exclusion list" without re-reading AD-2 closely enough could reasonably build app.py to expect only the delta. This is a narrower instance of Finding 2's same root cause (the exact shape of "current state as input" in AD-2 is never spelled out) and should be closed by the same new AD-5/AD-6 language proposed in Finding 2, with an explicit line that the full `excluded_ids` list is resent in full on every follow-up call, never a delta.

---

## Summary table

| # | AD(s) | Severity | One-line hole |
|---|-------|----------|----------------|
| 1 | AD-2 × AD-6 | Critical | "End trip" (AD-2) may clear the exact localStorage object AD-6 says history lives in ("the same... trip-state"), silently defeating FR-17/18 |
| 2 | AD-5 × AD-6 | Critical | No stated answer on whether `excluded_ids` and visit-history ids are one list or two, hard-filter or soft-weight, and whether "favourited" means suppress or resurface |
| 3 | AD-3 | High | Stop/content payload schema (incl. FR-19 content structure, FR-20 attribution) not pinned; spine's own Deferred section wrongly calls this low-risk |
| 4 | Consistency Conventions / AD-3 (FR-19) | High | No documented shape for a per-stop grounding-check failure inside an otherwise-feasible route; forces a choice between killing a good route (503) or inventing an undocumented per-stop error marker |
| 5 | AD-1 | Medium | "Park" styling named in Binds, never addressed by the Rule's two sub-buckets |
| 6 | AD-1 | Medium | Photo/no-photo split within "stop" produces two rendering mechanisms for one entity with no shared id-addressing scheme for highlight/selection |
| 7 | AD-4 | Low/Medium | Preference-signal wire representation (enum vs. continuous) unpinned at the Browser→API boundary |
| — | AD-5 × AD-2 | Medium (derivative of #2) | Not stated that `excluded_ids` must be resent in full (not as a delta) on every follow-up call, given backend statelessness |

None of these are violations of any AD as written — each pair of hypothetical builders fully complies with the letter of every rule that binds them. That is exactly what makes them real holes rather than implementation mistakes: closing them requires new or tightened architecture language, not better compliance.
