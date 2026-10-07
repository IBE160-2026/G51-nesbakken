---
title: Jaunt V1 PRD
status: final
created: 2026-09-29
updated: 2026-10-07
---

# PRD: Jaunt V1

## 0. Document Purpose

This PRD formalizes requirements for Jaunt V1 — the version submitted for the IBE160 "Programmering med KI" course assessment. It builds on `docs/product-brief.md` (the approved product story) and `docs/architecture-plan.md` (the existing sprint-by-sprint build plan and technical decisions for Sprints 1–6, already implemented). It is written from here forward, not backdated — Sprints 1–6 (catalogue import, planner shortlisting/feasibility, AI stop-selection backend) are already built, per `architecture-plan.md`'s results sections (Sprints 1, 3, 5, 6) and `docs/ai-development-log.md`/git history (Sprints 2, 4, which `architecture-plan.md` doesn't itself carry completion evidence for). This PRD's job is to state, with the same rigor as if written first, what the complete V1 must do, including the still-missing user-facing flow (AI content generation and frontend wiring) and a small set of new capabilities surfaced during journey discovery.

Throughout this document, **V1** means the IBE160-assessed scope only. Where something is explicitly **Post-V1 / Vision**, that means it is outside what's being assessed, not decided against — the student intends to continue developing Jaunt after the course. FRs are numbered globally (FR-1 through FR-24) for stable downstream reference. `[ASSUMPTION: ...]` tags mark places this PRD infers without full confirmation; all are indexed in §9.

Downstream, this PRD is expected to feed `bmad-ux` (the "Jaunt character" concept and the open UI-form questions in §8 belong there), `bmad-architecture`, and `bmad-create-epics-and-stories`.

**Known planning gaps, flagged for the next stage:** a feasibility review of this PRD found that no existing sprint plan (`architecture-plan.md` Sprints 2, 7, 8, 9) assigns a sprint, estimate, or task to building the Trip Setup / Route Review frontend that FR-1–FR-9 depend on — the actual UI for choosing time/topic, reviewing a proposed route, and approving it. This is real, unscheduled Must-tier work, not merely under-tiered, and should be explicitly sized by `bmad-architecture`/sprint-planning given the compressed remaining timeline (see Open Question 14). Separately, FR-6's requirement to show the full walking path depends on route-geometry work that's explicitly Sprint 8, not yet built (see §4.2). An independent review (2026-10-03) also consolidated a list of backend capability the UX now assumes but that doesn't exist yet in `planner.py` (which currently only accepts start coordinates, Topic, time, and dwell allowance): real exclusion-and-revalidation logic for Re-Jaunt (FR-10) and manual replacement (FR-11) — not just re-calling the Planner, which doesn't guarantee a different result; an actual selection signal for the landmark/hidden-gem preference (FR-4); local visit-history actually feeding Route variety (FR-18); and AI content generation plus its grounding check (FR-19), still the largest unbuilt piece. These are legitimate planned features already named by their own FRs, not hidden scope — but they are backend work, not frontend wiring onto capability that already exists, and should be sized as such.

## 1. Vision

Jaunt turns a person's available time into a purposeful walk. Someone with 30–120 minutes to spend enters a starting point, how much time they have, and optionally what they're interested in — history, architecture, public art, heritage, or "surprise me." Jaunt proposes a short loop with 2–5 real stops, each carrying a short piece of AI-generated content — a story, a fact, a small task, or a prompt to notice or do something — grounded in real source material, not invented. The person reviews the proposed route, approves it, and walks it, with the option to revisit favourite places and discover new ones on future Jaunts.

What makes this worth building rather than just using an existing maps app: Jaunt starts from the walk itself, not a destination the user already picked. It treats "how much time do I have" as a first-class input covering the whole outing — walking and stopping both — and it would rather say "that doesn't quite work, try this instead" than manufacture a route out of weak or irrelevant stops. Tell Jaunt how much time you have, and it gives you something worth walking for.

The intended feel is playful and spontaneous, not utilitarian — a guiding Jaunt character (first draft in progress, see `addendum.md`) is part of that tone, not just a notification mechanism. This belongs to `bmad-ux` to realize, but the PRD states it here so the tone isn't lost downstream.

V1 is proven in one pilot area — Newtown, inner Sydney — with a verified, source-backed catalogue built by an offline import pipeline (OpenStreetMap, Wikipedia/Wikidata, an Inner West Council street-art dataset, and a hand-curated NSW heritage list). [ASSUMPTION: this is narrower than `product-brief.md`'s original V1 scope, which named a six-suburb area (Chippendale, Redfern, Surry Hills, Glebe, Erskineville, Newtown). The narrowing to Newtown-only was already settled during Sprint 1 implementation, for faster iteration on a smaller pilot — not a new decision made in this PRD round, but not previously flagged against the brief either.] The longer-term vision, captured but explicitly not required for V1, is an app that can be pointed at a new neighbourhood or city without hand-building its catalogue from scratch.

Beyond V1, one direction stands out as a strong long-term use case in its own right, not just another item on a wishlist: **"give me an interesting walk that gets me to this destination within my time"** — routing *to* somewhere the user already needs to be (a restaurant, a meeting point), rather than only looping back to the start. It's deferred from V1 because it's a genuine planning-algorithm rework, not because it's a minor idea (see §5 Non-Goals and `addendum.md`).

## 2. Target User

### 2.1 Jobs To Be Done

- **As a local with unstructured spare time**, I want a reason to go for a walk in my own area, so that a walk becomes an experience instead of the same familiar loop.
- **As a visitor in an unfamiliar area**, I want a manageable, time-bounded walk that helps me notice or learn something, without researching attractions and building my own route.
- **As either**, I want to trust that what I'm shown is real and relevant — not a generic list of "nearby attractions," and not fabricated when nothing suitable exists.

### 2.2 Key User Journeys

- **UJ-1. Vilde has an hour and wants a reason to leave the flat.**
  - **Persona + context:** Vilde lives in Newtown. No particular destination in mind — she has about an hour free and wants to discover something about her own neighbourhood, or just get outside with a purpose.
  - **Entry state:** Opens Jaunt on her phone browser. No account.
  - **Path:** Taps her starting point on the map. Sets available time (~60 min) and picks a topic — or "surprise me." Jaunt proposes a route: a map with 2–5 stops and an expandable list. She inspects individual stop descriptions, is happy with the selection, and explicitly approves it.
  - **Climax:** Walking, she gets an optional nudge to open each stop's story as she reaches it — engaging is never required to keep going. She finishes the loop back where she started.
  - **Resolution:** The walk is remembered locally; next time, Jaunt favours places she hasn't seen, while letting a favourite resurface occasionally.
  - **Edge case:** If Vilde's requested time/topic combination has no feasible route, Jaunt says so plainly and suggests a shorter walk or different topic rather than forcing a weak result.
  - **If available in this version** *(Should-tier, not required for the core path above)*: Vilde could be lukewarm on one proposed stop and remove or replace it (FR-11), or reject the whole route and tap Re-Jaunt for a different one (FR-10), before approving. If she explicitly marks stops visited as she goes (FR-13, distinct from just opening their stories), she gets a short AI-generated summary afterward grounded only in what she actually confirmed visiting (FR-16).

- **UJ-2. Steve has 90 minutes before dinner with friends.**
  - **Persona + context:** Steve is visiting Newtown for the first time, meeting friends for dinner in 90 minutes. He doesn't know the area and doesn't want to spend his window researching it.
  - **Entry state:** Opens Jaunt on his phone. No account.
  - **Path:** Same mechanical flow as Vilde's — starting point, time, topic. He reviews the proposed route, inspects the stops, and approves it.
  - **Climax:** He walks the loop, opening a couple of stop stories that catch his eye, finishing with time to spare before dinner.
  - **Resolution:** He leaves with a short, honest sense of what he actually saw — no need for an account or any lasting record if he doesn't want one.
  - **Edge case:** If nothing suitable fits his 90-minute window and stated interest, Jaunt is honest about that rather than stretching the definition of "relevant" to fill a route.
  - **If available in this version** *(Should-tier)*: being unfamiliar with the area, Steve could indicate he'd rather see well-known places than obscure ones (FR-4) — a preference that isn't tied to being a "visitor" as such; a local might want the same thing.

## 3. Glossary

- **Jaunt (the outing)** — a single generated walk: a starting point, a time budget, an optional topic, and a proposed or approved route of stops. ("Have a Jaunt.")
- **Stop** — a real place from the catalogue, with a name, coordinates, one or more Topics, a source excerpt, and (once generated) short AI content.
- **Catalogue** — the local, offline-imported dataset of candidate Stops for a given Pilot Area, built by the import pipeline (`import_places.py`, `import_street_art.py`, `import_heritage.py`).
- **Pilot Area** — the bounded geographic area a Catalogue covers (V1: Newtown). A stretch goal (FR-21) tests a second pilot area.
- **Topic** — history, architecture, public art, heritage, or "surprise me." Each Stop carries one or more Topics assigned at import time.
- **Record Status** — a Stop's catalogue status: `ready` (usable at runtime), `limited` (weak/incomplete source), or `rejected` (not usable).
- **Shortlist** — the bounded set of nearby `ready` Stops (≈10–15) the Planner narrows candidates to before requesting a routing matrix.
- **Option Menu** — the bounded, ranked set of feasible 2–5 stop combinations the Planner derives from the Shortlist and hands to AI for final selection.
- **Route** — the ordered sequence of Stops, with computed walking + dwell time, that the Planner and AI together produce for a given request.
- **Re-Jaunt** — regenerating a new Route from the same starting point, time, and topic inputs, after rejecting a proposed Route.
- **Source Excerpt** — the real text (Wikipedia/Wikidata, OSM tags, council dataset, or NSW Heritage statement) stored against a specific Stop, which grounds its AI-generated content.
- **Contextual Source** — a reliable source of *general* information not specific to any one Stop (e.g. facts about an architectural style, period, or movement). May supplement a Stop's own thin Source Excerpt, but only to state something general — never phrased or implied as a fact specifically known about that particular Stop.
- **Dwell Time** — the fixed per-stop time allowance (5 minutes in V1) added to walking time when checking whether a Route fits the user's time budget.
- **Stop Engagement State** — one of four distinct, non-equivalent states a Stop can hold for a given user, tracked separately rather than collapsed into one "seen it" flag:
  - **Proposed** — the Stop appeared in a Route the user was shown (approved or not).
  - **Opened/Engaged** — the user viewed the Stop's content, at any time (pre-walk review via FR-7, or during the walk via FR-12). This is *not* evidence of physical presence — content can be opened before ever walking there.
  - **Visited/Completed** — the user explicitly affirmed they were physically at the Stop (FR-13), only actionable during an active walk. Distinct from and stronger than Opened/Engaged.
  - **Favourited** — the user explicitly marked the Stop to preferentially resurface in future Routes.
- **Visit History** — the locally-stored (no-account) record of each Stop's Engagement State per user, used to vary future Route generation (FR-18).

## 4. Features

### 4.1 Trip Setup
**Description:** The entry point to every Jaunt. Realises UJ-1, UJ-2. Existing (Sprint 2/3): starting-point selection and the underlying time/topic data model. Missing: the actual time/topic input UI and the preference capability below.

**Functional Requirements:**

#### FR-1: Choose a starting point
User selects a starting point by tapping the map, or choosing from a small set of predefined named starts. Realises UJ-1, UJ-2.

**Consequences (testable):**
- A tapped point within the current Pilot Area is accepted and used as the Route's start/end.
- A tap outside the Pilot Area is rejected with a clear message, not silently accepted.

#### FR-24: Use current location for starting point *(Should — added 2026-10-03 during UX discovery)*
Alongside map-tap and named starts, the user can tap a "use my current location" option that makes a one-time (not continuous) browser geolocation request to suggest/center a starting point. Realises UJ-1, UJ-2.

**Consequences (testable):**
- Location is only requested on explicit tap, with the same explicit/revocable permission prompt as FR-14 — never automatic or silent.
- A denied or failed request falls back cleanly to map-tap/named starts; it is never a dead end.
- This is a single one-shot position read, not the continuous tracking FR-14 covers during the walk — lower complexity, and not dependent on FR-14 being built first.

#### FR-2: Choose available time
User sets total available time, 30–120 minutes. Realises UJ-1, UJ-2.

**Consequences (testable):**
- The Planner never proposes a Route whose Dwell-Time-inclusive total exceeds the entered time.
- [ASSUMPTION: the 30–120 minute range and 5-minute fixed Dwell Time carry over unchanged from `architecture-plan.md`; not re-confirmed with the user in this PRD round, and `architecture-plan.md` itself already flags these as provisional defaults to revisit after real-world testing.]

#### FR-3: Choose a topic
User selects one Topic — history, architecture, public art, or heritage — or "surprise me." Realises UJ-1, UJ-2.

**Consequences (testable):**
- All four named Topics plus "surprise me" are selectable. [ASSUMPTION: heritage is included here as a first-class option alongside the three named in `product-brief.md`, since Sprint 6 added it as real, sourced catalogue data even though the original brief text predates that sprint.]
- **Corrected 2026-10-03 (independent review caught this was factually wrong against the actual code):** "Surprise me" keeps candidates across *all* Topics rather than filtering to one — `planner.py`'s `shortlist_candidates()` explicitly skips Topic filtering for `surprise_me` so AI can make the final cross-Topic selection itself, rather than this step silently narrowing to a single "most common" Topic first. The previous wording ("selects from the best-represented Topic") misstated this. "Wild Jaunt" remains an accurate UX label for this actual mixed-Topic behaviour.
- **Known gap, not yet resolved (flagged 2026-10-03):** the catalogue currently has only 1 `ready` stop each for History and Architecture (129 for Public Art, 29 for Heritage) — the Planner requires at least 2 Stops to build a Route, so **History and Architecture cannot currently produce a Route at all**, even though both are offered as Topic choices here and in the UX mocks. This is a real data/product gap, not a planner bug — see Open Question 18.

#### FR-4: Express a landmark ↔ lesser-known preference
User can indicate a preference between well-known and lesser-known stops, feeding stop selection. One interface serves both UJ-1 and UJ-2 — this preference, not a separate UI per audience, is what adapts the experience. Realises UJ-2 (and UJ-1, since either persona may want either preference).

**Consequences (testable):**
- The preference is a capability, not an identity question — there is no "are you a local or a visitor" toggle, and no separate interface per audience.
- The preference influences which Stops the Option Menu favours, without excluding "hidden gem" Stops from being genuinely interesting (not merely obscure).
- The preference may also shape the contextual framing of a Stop's content (e.g. emphasizing what a local-leaning user wouldn't already know), not only which Stops are selected — exact extent is open, see Open Question 3.
- **Open:** the literal UI control (spectrum, toggle, choice chips, or something else) is intentionally undecided here — see Open Question 1. The underlying signal that ranks a Stop as "well-known" vs "lesser-known" is also undecided — see Open Question 3.

### 4.2 Route Generation & Review
**Description:** The Planner (existing, Sprints 3–4) and AI stop-selection (existing, Sprint 4) already produce a Route from a Shortlist and Option Menu. What's missing is showing that Route to the user and letting them act on it before committing to walk it. Realises UJ-1, UJ-2.

**Functional Requirements:**

#### FR-5: Generate a proposed Route
System generates a feasible, time-bounded Route (2–5 stops) from the user's starting point, time, and topic, using the existing Planner + AI selection pipeline. Realises UJ-1, UJ-2.

**Consequences (testable):**
- Every proposed Route's shortest feasible ordering, plus Dwell Time, fits within the requested time (existing Planner guarantee).
- Every Stop in a proposed Route has Record Status `ready`.

#### FR-6: Display the proposed Route
The Route and its Stops are shown on the map with an expandable stop list. Realises UJ-1, UJ-2.

**Consequences (testable):**
- The map shows the full walking path and every Stop's location. **Depends on route-geometry work not yet built**: the Planner currently has only point-to-point durations from the routing matrix, not actual route polylines — per `architecture-plan.md`, fetching and rendering real route geometry is Sprint 8 work, not yet done. This FR cannot be fully complete until that lands.
- The stop list is orderable/expandable to show each Stop's name and Topic without requiring a tap into detail view.
- The estimated total time (walking + Dwell Time) is shown on the review screen, per `product-brief.md`'s "Data out: Estimated walking and stop time" — not only used internally for feasibility checks (FR-2, FR-5).

#### FR-23: Muted background amenities shown at high zoom *(Should — added 2026-10-03 during UX discovery)*
When zoomed in sufficiently, the map shows nearby general points of interest (e.g. cafes, restaurants) as a muted, secondary reference layer — present for orientation, but never visually competing with the Jaunt Route or its Stops. These points are background map information only: they carry no AI-generated content, no Topic, and are never candidates for Route selection.

**Consequences (testable):**
- Amenity points are visually subordinate to the Route line and Stop markers at every zoom level where they appear (smaller and/or lower-contrast than Route/Stop styling).
- Amenity points are display-only — never stored as Stops, never fed into the Planner or AI selection.
- **Open:** actual feasibility and data source depend on how the custom (non-default-OSM-tile) map styling chosen for Route Review is implemented — left to `bmad-architecture`, see Open Question 17.

#### FR-7: Inspect stop content before approving
User can open each Stop's AI-generated content and its source before deciding whether to approve the Route. Realises UJ-1, UJ-2.

**Consequences (testable):**
- Every Stop's content is visible from the review screen, not only during the walk.
- A visible reference to the Source Excerpt (or its origin) accompanies each Stop's content (see FR-20).

#### FR-8: Explicitly approve the Route
User must take an explicit approval action before a Route becomes an active walk. Realises UJ-1, UJ-2.

**Consequences (testable):**
- No walk begins without an explicit approval action from the review screen.

#### FR-9: Honest fallback when no suitable Route exists
When no feasible or sufficiently relevant Route can be built for the request, the system says so, explains why in plain terms, and always gives a way back to change inputs — rather than returning a weak/irrelevant Route or a dead-end failure screen. Realises UJ-1, UJ-2 (edge cases).

**Consequences (testable):**
- A request with zero feasible Stop combinations never reaches AI selection and produces the fallback message (existing Planner behaviour).
- **Corrected 2026-10-03 (independent review caught a logical error):** when a suggested time adjustment is offered, it must suggest *more* time, never less — reducing the time budget strictly shrinks the feasible search space in the current Planner model, so it can never turn an infeasible request into a feasible one. (The previous wording's own example, "try 45 minutes," was ambiguous about direction; the UX mock's actual example — offering 45 minutes after a failed *30*-minute request — has this right.) A different-Topic suggestion is valid regardless of direction, since it changes the candidate pool.
- The fallback distinguishes a technical/service failure (e.g. the routing provider is unreachable) from an honest "no suitable walk" result — these are different situations and should not share the same message.
- A concrete alternative is suggested when one is known to help; the message is still honest and still offers a way back to adjust inputs even when no specific alternative can be computed.

#### FR-10: Re-Jaunt
User can request a new proposed Route using the same starting point, time, and topic. Realises UJ-1.

**Consequences (testable):**
- Re-Jaunt returns a different Route than the one just rejected when a feasible alternative exists in the Option Menu.
- Falls back to FR-9's honest message if no alternative exists.

#### FR-11: Manually remove or replace a stop
Before approving, user can remove or replace an individual Stop in the proposed Route. Realises UJ-1.

**Consequences (testable):**
- Removing or replacing a Stop re-validates the Route's time feasibility before it can be approved.
- **Open:** how a replacement candidate is chosen (fresh AI/Planner suggestion vs. next-best from the existing Shortlist) is undecided — see Open Question 2.

### 4.3 Walking Experience
**Description:** What happens between approval and finishing. Realises UJ-1, UJ-2. FR-12 is Must; the rest of this feature is Should/Could, deliberately kept separable so a simpler V1 doesn't silently depend on GPS.

**Functional Requirements:**

#### FR-12: Access stop content during the walk
Each approved Stop's content remains available during the walk; opening it is always optional. Realises UJ-1, UJ-2.

**Consequences (testable):**
- A user can complete a Route without opening any Stop's content, and the app does not block or nag them for skipping it.

#### FR-13: Mark a stop Visited/Completed
User can explicitly affirm they were physically at a Stop, during an active walk — distinct from, and not satisfied merely by, opening the Stop's content (Opened/Engaged, see Glossary). Realises UJ-1 — feeds FR-16.

**Consequences (testable):**
- The signal is a manual, explicit action separate from viewing content, not derived from GPS proximity and not inferred from an Opened/Engaged state alone.
- A Stop that was only ever Opened/Engaged (e.g. previewed during FR-7's pre-walk review, or browsed mid-walk out of curiosity without being there) is never recorded as Visited/Completed.
- **Resolved (UX, 2026-10-03):** an explicit "visited" checkbox in the top-right corner of the stop's info page/overlay — see Open Question 8.

#### FR-14: Show live position during the walk *(Should — amended 2026-10-02, see §9 Open Question 15)*
User's current position is shown on the map during an active walk, subject to explicit location permission. Realises UJ-1, UJ-2.

**Consequences (testable):**
- Position is never requested or shown without an explicit, revocable permission prompt.
- No position data is sent to or stored on a server (see §7 Privacy).

#### FR-15: Automatic arrival notification *(Could — depends on FR-14)*
When the user's live position is near an unvisited Stop, they receive a prompt inviting them to open its content. Realises UJ-1, UJ-2.

**Consequences (testable):**
- Only fires when FR-14 is active and permitted; never simulated from a non-GPS signal.
- Stays Could unless architecture finds this comes near-free once FR-14's position-tracking plumbing exists — if so, worth revisiting as a Should too (see §9 Open Question 15).

### 4.4 Wrap-Up & Repeat Use
**Description:** What happens after a walk, and what changes the next time. Realises UJ-1. All Should — real value, deliberately not required for a minimally complete V1.

**Functional Requirements:**

#### FR-16: AI-generated walk summary
After finishing, the user receives a short AI-generated summary grounded strictly in Stops marked Visited/Completed (FR-13) — never Stops that were merely Proposed or only Opened/Engaged. Realises UJ-1.

**Consequences (testable):**
- The summary never describes a Stop as having been visited unless it holds Visited/Completed state; it does not claim or imply physical presence it has no evidence for.
- A walk with zero Stops marked Visited/Completed produces no summary (or an honest "nothing confirmed" message) rather than fabricating one from Proposed/Opened stops.
- Grounded in the same Source Excerpts as the per-stop content (see FR-19) — no new invented detail.

#### FR-17: Local visit history and favourites
User's Visit History — tracking each Stop's Engagement State (Proposed / Opened/Engaged / Visited/Completed) — and Favourites are stored locally, without requiring an account. Realises UJ-1.

**Consequences (testable):**
- No account creation or login is required to use Favourites or Visit History.
- The four Engagement States (Glossary) are stored distinctly, not collapsed into a single "seen" flag.
- **Open:** retention/reset behaviour (does history ever expire, can a user clear it) is undecided — see Open Question 7.

#### FR-18: Repeat-use route variety
Future Route generation varies Stop selection based on Engagement State, weighted by how strongly each state indicates the user already experienced the Stop, while still allowing Favourites to resurface. Realises UJ-1.

**Consequences (testable):**
- A Stop marked Visited/Completed is deprioritized more strongly than one that was only Proposed (shown but never approved/walked) or Opened/Engaged (previewed but not confirmed visited) — a merely-Proposed Stop should not be penalized as if the user had actually experienced it.
- A Favourite is not excluded by the deprioritization rule, regardless of its other Engagement State.
- **Open:** the exact weighting between Engagement States is a tuning/design detail, not fixed by this PRD — see Open Question 9.

### 4.5 Trustworthy, Source-Grounded AI Content
**Description:** Cross-cutting — applies to every Stop's content (FR-7, FR-12) and the walk summary (FR-16). This is the product's core differentiator and the most direct expression of the course's "must actually use AI" requirement, and it is already the operating principle behind the existing Planner/AI split (AI never does routing arithmetic; Python is the source of truth for feasibility).

**Functional Requirements:**

#### FR-19: AI content generation is grounded, automatically checked, manually spot-checked, and falls back rather than fabricates
AI-generated Stop content and walk summaries are grounded in the Stop's own Source Excerpt, a Contextual Source (see Glossary), or both. This is a design constraint and a checked process, not a claim that an LLM can be guaranteed never to produce unsupported content. Must-tier V1 requires **both** layers, not either instead of the other: (a) an automated check of generated content against its grounding material, with retry, exclusion, or flagging for review when a check fails, and (b) continued manual spot-checking (existing Sprint 5/6 practice) as a second layer. The simplest sensible design for the automated check — a rule-based overlap/entailment check, a second verification model call, or something else — is left to architecture to work out, not fixed here.

**Consequences (testable):**
- A Stop with `limited` Record Status (its own Source Excerpt is weak/incomplete) is not automatically offered in an Option Menu on that basis — **open whether a reliable Contextual Source could make such a Stop usable instead of excluding it outright; see Open Question 13.**
- Content blending a Stop's own Source Excerpt with Contextual Source material is only acceptable if a reader could not mistake the contextual part for something specifically known about that Stop.
- An automated grounding check runs on generated content before it reaches the user; a failed check triggers a defined fallback (exclude the Stop, retry generation, or flag for review), not silent pass-through.
- Manual spot-checking against source material continues as a required second layer, not a substitute for the automated check.

#### FR-20: Source attribution shown to the user
Each Stop's content is shown alongside a reference to where it came from (Wikipedia, OSM tags, council dataset, or NSW Heritage), satisfying `product-brief.md`'s "Data out: References to the source material."

**Consequences (testable):**
- Every Stop's content view includes a visible source reference, not only available on request.
- Required attribution for OSM, the routing provider, Wikipedia, NSW Heritage, and Inner West Council (already named as a Sprint 8 task in `architecture-plan.md`) appears somewhere in the UI, not only in this content view.

#### FR-22: Stop photo, shown only when a rights-cleared source image exists *(Should — added 2026-10-02 during UX discovery)*
A Stop's content and stop-list/card display may include a photo, but only when sourced from material the user actually has the rights to use (e.g. an appropriately-licensed Wikidata/Wikimedia Commons image) — never an unverified or scraped image. A Stop without a rights-cleared image simply has no photo; this is not a reason to exclude the Stop itself.

**Consequences (testable):**
- No photo is ever shown without a confirmed, checkable usage right attached to it (license type, source, attribution) — the same rigor FR-20 already applies to text attribution extends to images.
- Stops without a qualifying image display with no photo, not a placeholder or stock image standing in for the real place.
- **Open:** which source(s) count as "rights-cleared" for V1 (Wikidata/Wikimedia Commons with an open license is the obvious candidate, per the user) and what fraction of existing `ready` Stops would actually qualify — left to `bmad-architecture` to assess; this FR's real-world value depends on that coverage.

### 4.6 Geographic Reach *(stretch goal, not a hard V1 requirement)*
**Description:** Newtown remains the minimum supported Pilot Area for V1. This feature is an explicit stretch goal — attempted only once the Must-tier features above are working — not a blocker for course submission. Scoped to a second *Sydney* area only, after assessing and rejecting a Nice/Oslo/Molde demonstration and true live/runtime POI discovery as unrealistic within the course timeline — full assessment in `addendum.md`'s "Geographic expansion" section.

**Functional Requirements:**

#### FR-21: Second pilot-area demonstration
In two phases: (1) a small refactor moving existing Newtown/English-specific hard-coded values (e.g. bounding box, Wikipedia language prefix) into configuration — an extension of the §7 extensibility NFR, done once; then (2) pointing the import pipeline at a second Sydney-area bounding box (e.g. Surry Hills, per feasibility research showing denser OSM coverage than Newtown itself, no language change required) to produce a working, demonstrable Catalogue.

**Consequences (testable):**
- After phase (1), running the OSM-based and street-art importers against a new bounding box (set via configuration) produces `ready` Stops without modifying `planner.py`, `ai.py`, or the frontend.
- **Caveat:** the manual-curation limitation belongs to `import_heritage.py`'s one source — NSW's Heritage MapServer, WAF-blocked (see `architecture-plan.md`) — not to the heritage Topic itself. A new area's heritage Stops should first be attempted via the same automated OSM+Wikidata path used for history/architecture, or another scriptable heritage register if one exists there — potentially combining a place from one source with descriptive content from another. Manual curation is a fallback, not the default; a second-area demonstration can proceed with whichever Topics the automated path actually covers.
- Phase (1) is a prerequisite, not assumed to already be true of the current codebase.
- **Open:** the exact second-area boundary is not yet confirmed — see Open Question 5.

**Feature-specific NFRs:**
- The app must not hard-code assumptions (e.g. English-only Wikipedia parsing, confirmed in `import_places.py`) in ways that would be materially more expensive to undo later than to avoid now — see §7.

## 5. Non-Goals (Explicit)

**Out of the IBE160-assessed V1** (see §6 for full tiering; items here are explicitly *not being built* for course submission, though several are captured in the addendum as intended Post-V1 work, not rejected ideas):

- **Destination-based / point-to-point routing** — routing *to* a chosen destination instead of a loop back to the start (see §1 Vision for why this is deferred, not dropped).
- **Full user accounts and cross-device sync.**
- **Multi-language ingestion and non-Sydney locations** (Nice, Oslo, Molde, etc.), and true live/runtime POI discovery as an alternative to the offline import pipeline — assessed in detail and deliberately deferred given the remaining course timeline, not silently dropped; see `addendum.md`'s "Geographic expansion" section for the full assessment and reasoning — beyond the single-language, single-region scope of the FR-21 stretch goal.
- **Weather-responsive rerouting.**
- **Mid-walk route changes** after approval (shortening, changing destination, requesting a new route while already walking) — distinct from Re-Jaunt (FR-10), which only applies before a Route is approved.
- **Audio narration (read-aloud).**
- **Community-contributed stops/stories, or a "local legends" contributor role.**
- **A nature/photography topic** — open question about whether enough grounding source text exists; not decided either way (see §9, Open Question 4).
- **Free-text/multi-topic input** — V1 keeps the fixed topic list (FR-3); writing in open-ended interests is a named future direction.

## 6. MVP Scope

### 6.1 In Scope — V1 (course-assessed)

**Must:**
- FR-1, FR-2, FR-3 (Trip Setup core)
- FR-5, FR-6, FR-7, FR-8, FR-9 (Route Generation & Review core)
- FR-12 (stop content accessible during walk)
- FR-19, FR-20 (trustworthy, source-grounded, attributed AI content)
- Newtown working end-to-end as the tested Pilot Area
- NFR: no hard-coded English-only/Newtown-only assumptions that would be materially costly to undo later (§7)
- NFR: baseline privacy stance — no server-side location storage, no account required (§7)

**Should** *(real value; pursued once Musts are working, roughly in this order if time is short)*:
1. FR-10 (Re-Jaunt) — cheapest, good candidate to promote to Must if time allows
2. FR-11 (manual stop remove/replace)
3. FR-4 (landmark ↔ lesser-known preference)
4. FR-13, FR-16 (mark-visited + AI walk summary — bundled with each other, decoupled from live tracking)
5. FR-17, FR-18 (local visit history, favourites, repeat-use variety)
6. FR-21 (second pilot-area demonstration) — explicitly a stretch goal per §4.6, never allowed to delay the Newtown end-to-end flow
7. FR-14 (live position during the walk) — amended 2026-10-02 from Could to Should during UX discovery; attempt for V1 if the engineering cost is reasonable, but it does not block course submission the way Musts do (see §9 Open Question 15)
8. FR-22 (stop photo, rights-cleared only) — added 2026-10-02 during UX discovery; value depends on actual source coverage, which architecture still needs to assess (see §9 Open Question 16)
9. FR-23 (muted background amenities at high zoom) — added 2026-10-03 during UX discovery; lowest-priority of the UX-added Shoulds since it's purely a map-display enhancement, feasibility/cost left to architecture (see §9 Open Question 17)
10. FR-24 (use current location for starting point) — added 2026-10-03 during UX discovery; a one-shot geolocation request, browser-native with no new service dependency, genuinely cheap relative to the other UX-added Shoulds

**Could:**
- FR-15 (automatic arrival notification) — no longer bundled with FR-14 now that FR-14 is a Should. Stays Could on its own, unless architecture finds it comes near-free once FR-14's position-tracking plumbing exists, in which case it's worth revisiting as a Should too.

**Pending UX/architecture input** *(not story-ready as-is — flagged at a glance so this isn't only discoverable by cross-referencing §9)*: FR-4 (ranking signal + UI form, OQ-1/3), FR-11 (replacement-selection logic, OQ-2), FR-13 (mark-visited UI mechanism, OQ-8), FR-17 (retention/reset behaviour, OQ-7), FR-18 (Engagement-State weighting, OQ-9). Each is intentionally left open per the user's preference to keep implementation decisions visible rather than silently chosen — but `bmad-ux`/`bmad-architecture` should resolve these before `bmad-create-epics-and-stories` tries to write acceptance-testable stories for them.

### 6.2 Out of Scope for V1

See §5 Non-Goals for the full list and reasoning. All Non-Goal items are preserved in `addendum.md` for Post-V1 development — none are dropped, only deferred past the course-assessed scope.

## 7. Constraints and Guardrails

**Privacy:**
- No account is required for any V1 feature, including Favourites and Visit History (FR-17).
- **Revised 2026-10-07 (architecture review caught an over-broad promise):** for V1, Visit History, Favourites, and any mark-visited state (FR-13) are stored locally on the user's device — no server-side account system exists in V1, and this data is not persisted on any server in this version. A planning request may transmit the minimal signal needed for that one computation (the same transient-use posture FR-24 already establishes for a one-shot location coordinate below); nothing from it is stored server-side in V1 regardless. **This is a V1 implementation fact, not a permanent architectural promise** — it does not foreclose a future server-side account system (synced favourites, saved walks, personalized recommendations), which `addendum.md` already names as a legitimate Post-V1 direction. The original absolute "never on a server" wording would have silently ruled that out; revised so V1's privacy posture and the project's own stated future direction don't contradict each other.
- Live position (FR-14, Should) is only ever requested with an explicit, revocable permission prompt, is not required for any Must-tier feature, and the continuous position stream itself is never transmitted to or stored on a server — it only drives the client's own map display.
- **Clarified 2026-10-03 (independent review caught an overstatement):** this does not mean *no* location data ever leaves the device. A starting point derived from FR-24's one-shot "use my current location" is, by design, sent to the routing/planning service — the same way a map-tapped or named-start coordinate already is. What stays device-only is the continuous GPS stream (FR-14) and any stored history/favourites, not a one-time selected coordinate the Route genuinely needs to be computed.

**Source integrity (cross-cutting, see FR-19/FR-20):**
- AI never originates a Stop's existence — only the import pipeline's verified catalogue does.
- AI never generates content for a Stop without grounding in its Source Excerpt, a reliable Contextual Source, or both — and never presents a Contextual Source's general information as if it were specifically known about that Stop.
- V1 requires both an automated grounding check and manual spot-checking for generated content (FR-19) — not manual checking alone.

**Language & geographic extensibility:**
- V1 ships English-only, Newtown-scoped. The codebase should keep language and Pilot Area boundary as configuration, not inline literals, so that extending to a second area (FR-21) or, later, a second language, is additive rather than a rewrite. This is an architectural posture for V1, not a commitment to build multi-language support now.

**Platform:**
- Mobile-first web app (phone browser primary); desktop is secondary. Built and tested mobile-first from the start, per existing `architecture-plan.md` decision — not retrofitted later.

**Reliability / regression:**
- The existing test suite (168/168 passing — directly re-run and verified 2026-10-07, superseding earlier 167/167 and 155/155 figures) must continue passing as V1 features are added; new Must/Should features get their own tests per `AGENTS.md`'s testing priorities (core functionality, calculations, data handling, edge cases).

## 8. Success Metrics

*Reusing and operationalizing `product-brief.md`'s Success Criteria, now cross-referenced to FRs. IDs are grouped by priority (Primary/Secondary/Counter), not sequence — SM-7 was added later and sits with Primary despite the number.*

**Primary**
- **SM-1**: Testers rate the completed walk as "worth taking" and would consider using Jaunt again — qualitative survey after developer + external testing in Newtown. Validates FR-1–FR-9, FR-16.
- **SM-2**: Actual walk completion time against the user's requested time, with an **asymmetric** tolerance — finishing up to 25% *under* the requested time is acceptable (suboptimal, not harmful); finishing more than 10% *over* is not. Overrunning is treated as the more serious failure — since staying within the user's stated available time is one of Jaunt's core promises — and underrunning isn't. Both thresholds are provisional (set now, given the ~20–30% routing-provider optimism gap already observed in `docs/ai-development-log.md`, so this metric is usable before data exists) and will be reassessed once Sprint 8's real-world test produces real data. Validates FR-2, FR-5.
- **SM-3**: Displayed Stops are rated real and relevant to the selected Topic by testers. Validates FR-5, FR-19.
- **SM-7**: Testers complete the full flow — setup through an approved, walkable route — on a phone browser, per `product-brief.md`'s "the route can be viewed and followed from a phone." Validates §7 Platform, FR-1–FR-8.

**Validation activity this depends on:** SM-1, SM-2, and SM-7 all require actually running tester sessions and/or the real-world walking test — these are not guaranteed to happen just because the Must-tier FRs reach "code complete." Scheduling tester sessions and the real-world walking test (per `architecture-plan.md`'s Sprint 8) is itself part of V1 Must-tier completion, not a free afterthought.

**Secondary**
- **SM-4**: AI-generated content is consistent with its Source Excerpt on spot-check review. Validates FR-19, FR-20.
- **SM-5**: Testers can articulate why each Stop was included, without prompting. Validates FR-7, FR-19.
- **SM-6**: When no suitable Route exists, the system responds honestly (alternative suggestion, not a fabricated or weak Route) across a set of deliberately infeasible test requests. Validates FR-9.

**Counter-metrics (do not optimize)**
- **SM-C1**: Time-budget usage percentage alone. A Route that uses ~100% of the requested time is not automatically better — `architecture-plan.md` already documents a "technically feasible but only 15-minute-used" failure mode (Sprint 3), and `docs/ai-development-log.md` records two manual comparisons finding the routing provider's estimates run roughly 20–30% optimistic against real walking apps on real Jaunt routes (Sprint 4) — a real-world walking test is still outstanding (Sprint 8). Counterbalances SM-2.
- **SM-C2**: Source-groundedness must not be pursued by making content so terse it stops being interesting — the brief's differentiator is a story/fact/prompt worth reading, not a minimal factual fragment. Counterbalances SM-3/SM-4.

## 9. Open Questions

1. What UI form best expresses the landmark ↔ lesser-known preference (FR-4) — a spectrum/slider, discrete choices, or something else? Deliberately deferred to the UX stage (`bmad-ux`), not decided here.
2. How is a manual stop replacement (FR-11) chosen — a fresh AI/Planner suggestion, or the next-best remaining Shortlist candidate? Either way, feasibility must be re-validated.
3. What signal drives "well-known" vs. "lesser-known" ranking for FR-4 (e.g. Wikidata sitelink count, OSM tag presence, something else)? Technical, unresolved. Relatedly, should the preference also shape how a Stop's content is framed (not just which Stops are chosen) — and if so, how much?
4. Is there enough grounding source text to support a future nature/photography Topic the way history/architecture/public art are grounded today? Open, not decided either way (see `addendum.md`).
5. What exact second pilot-area boundary should FR-21's stretch goal target? Surry Hills is suggested by feasibility research (denser OSM coverage than Newtown, no language change needed) but not confirmed.
6. What minimum time-budget-usage threshold, if any, should the Planner enforce? Open since Sprint 3/4 (`architecture-plan.md`), still unresolved.
7. What retention/reset behaviour should local Visit History (FR-17) have — does it ever expire, can a user clear it?
8. ~~What's the exact UI mechanism for marking a Stop Visited/Completed (FR-13)?~~ **Resolved during UX discovery (2026-10-03):** an explicit "visited" checkbox in the top-right corner of the stop's info page/overlay — separate from opening the content itself, so it stays distinct per FR-13's requirement.
9. What's the exact weighting between Engagement States (Proposed / Opened-Engaged / Visited-Completed / Favourited) in FR-18's repeat-use variety logic? Direction is set (stronger engagement → stronger deprioritization; Favourited is exempt); the precise tuning is a design/architecture detail left open.
10. Simplest sensible design for FR-19's required automated grounding check (e.g. a rule-based text-overlap/entailment check vs. a second verification model call) — left to `bmad-architecture`.
11. Are terse OSM-tag-sourced excerpts (e.g. "By Jasmine Sarin, 2021" — real but thin, per Sprint 1's known limitations) actually sufficient input for FR-19's content generation to produce something worth reading, not just technically grounded? Flagged in `architecture-plan.md` as expected-but-not-yet-tested; Sprint 7 content generation is the first point at which this can actually be checked.
12. Should Route ordering (FR-5) account for a route backtracking along the same street for a meaningful stretch (a "there and back" feel), given it bears on SM-1's "worth taking" judgment? `architecture-plan.md` defers this to Sprint 8 since it needs real route geometry, not just the duration matrix, to detect — not yet addressed by any FR here.
13. Should a reliable Contextual Source (FR-19) be able to make an otherwise-`limited`-status Stop usable — i.e. a place that's verified real but whose own Source Excerpt is thin could still be included if general contextual information fills the gap — or should Contextual Sources only ever supplement already-`ready` Stops? Left open for architecture/further product decision; also open what counts as a "reliable" Contextual Source for V1 (a small curated reference set vs. something broader).
14. Frontend build sizing — see §0's "Known planning gaps" callout.
15. FR-14 (live position) was amended from Could to Should during UX discovery (2026-10-02), on the user's own instruction to attempt it for V1 "if not too complicated." What counts as "too complicated" isn't defined — `bmad-architecture` should size the actual GPS/live-tracking work and confirm this is still realistic within the remaining timeline before it's treated as committed. If sizing shows FR-15 (automatic arrival notification) comes near-free once FR-14's plumbing exists, both should be reassessed together.
16. FR-22 (stop photos) was added during UX discovery (2026-10-02) on the condition that only rights-cleared images are ever shown. Its actual value depends on how many `ready` Stops have a qualifying image available (Wikidata/Wikimedia Commons with an open license is the obvious first source to check) — `bmad-architecture` should assess real coverage before this is treated as more than a nice-to-have for the Stops that happen to qualify.
17. FR-23 (muted background amenities) was added during UX discovery (2026-10-03) as a V1 target, on the user's explicit instruction after recalibrating an earlier "not like Google Maps" stance — the intent is a quiet, zoom-dependent reference layer that never competes visually with the Route/Stops, not full map-app density. Since Route Review uses a custom map style rather than default OSM tiles, this isn't free the way it would be on stock OSM rendering — `bmad-architecture` needs to determine the actual data source and cost (e.g. live Overpass amenity queries vs. a vector-tile styling approach) before this is treated as committed.
18. ~~History and Architecture cannot currently produce a Route~~ **Approved direction (2026-10-03), not yet built:** only 1 `ready` Stop exists for each against the Planner's 2-Stop minimum (Public Art has 129, Heritage has 29). Fix: AI reads each Heritage record's Statement of Significance and suggests additional Topics (`architecture`, `history`) *only where the source text actually supports that specific Topic* — explicitly not a blanket "tag every Heritage record as both" shortcut to inflate the counts — with a human-reviewed approval pass before storing the expanded `topics` array. No Planner changes needed (it already supports multi-Topic Stops); the original source text is never rewritten. Remaining open: exact implementation is `bmad-architecture`'s to size and build.
19. **Route Review's "Quiet Streets" custom map styling may not be achievable with the app's current rendering approach** (flagged 2026-10-03): the running application displays standard raster map tiles; the UX mocks' custom-styled buildings/parks/route (and FR-23's amenities layer) are hand-drawn SVG, which cannot simply be layered onto raster tiles. `bmad-architecture` needs to choose a practical real rendering approach (e.g. vector tiles with custom styling, a different tile source, or a scoped-down visual treatment that works with raster tiles) before the exact pixel-level look in the mocks is treated as a committed visual target rather than a direction.
20. **What does "X min left" mean during the walk** (surfaced in the key-walking-to-summary.html mock, flagged 2026-10-03)? Two materially different things: (a) time remaining from the originally requested budget (simple arithmetic, no new capability), or (b) estimated time to finish from the user's actual current position (requires real-time progress/location calculation the Planner does not currently do — a bigger hidden scope item than any of the explicitly tracked new FRs). Not yet defined; must be resolved before this is treated as a small display detail.

## 10. Assumptions Index

- §4.1 FR-2 — 30–120 minute time range and 5-minute fixed Dwell Time carried over unchanged from `architecture-plan.md`, not re-confirmed this round.
- §4.1 FR-3 — heritage included as a first-class Topic option alongside history/architecture/public art, since Sprint 6 added it as real catalogue data after the original brief text was written.
- §1 Vision — Newtown-only V1 Pilot Area is narrower than `product-brief.md`'s original six-suburb V1 scope; narrowing already settled during Sprint 1 implementation, not decided in this PRD round.
