# Epic 1 Context: Plan and Review a Trustworthy Walk

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

A user sets a starting point, available time, and topic (or "surprise me," or a landmark/hidden-gem preference) and gets back a real, source-grounded, time-feasible proposed walk with inspectable per-stop content and visible attribution. They can adjust it (remove/replace a stop, ask for a different one) before explicitly approving, and if nothing suitable or relevant enough exists they get an honest, non-dead-end explanation instead of a weak result. This is V1's Must-tier core plus its attached Should-tier refinements: the whole Trip-Setup/Route-Review flow plus the AI content-generation and grounding pipeline it depends on. It matters because an honest alternative over a fabricated-looking answer is the product's stated differentiator, and every later epic assumes this planning/review loop already works.

## Stories

- Story 1.1: Trip Setup inputs - starting point, time, and topic (Must) - done
- Story 1.2: Catalogue topic coverage for History and Architecture (Must) - done
- Story 1.3: AI content generation, grounded and checked (Must) - done
- Story 1.4: Generate a proposed Route via a new planning endpoint (Must, backend-only) - done
- Story 1.5: Review and approve the proposed Route (Must) - done
- Story 1.6: Honest fallback when no suitable Route exists (Must) - in review
- Story 1.7: Re-Jaunt (Should) - backlog
- Story 1.8: Manually remove or replace a stop (Should) - backlog
- Story 1.9: Landmark <-> hidden-gem preference (Should) - backlog
- Story 1.10: Use current location for starting point (Should) - backlog
- Story 1.11: Stop photo, shown only when rights-cleared (Should) - backlog

## Requirements & Constraints

- Starting point: any map tap is accepted (no boundary rejection), or a named-start chip, or a one-shot "current location" read that falls back cleanly on denial/failure. A start far from any real stop is handled by the honest fallback, not a rejection.
- Time: 30-120 min, 5-min increments; walking plus dwell time must never exceed it. Max stop count is computed per request (`min(7, minutes // dwell_minutes_per_stop)`), never fixed, and no stop is added just to use up time.
- Topic: history, architecture, public art, or "surprise me" (all topics stay eligible when surprised); heritage is never user-facing. An optional landmark<->hidden-gem preference shapes ranking only, sent as one continuous value, never an enum, and never excludes a stop.
- A route needs >=2 `ready`-status stops whose shortest feasible ordering plus dwell time fits the requested time. Malformed/invalid input is rejected immediately, before any routing/AI call.
- Three planning outcomes stay distinct: zero feasible combinations; feasible-but-irrelevant (AI judged); a genuine AI/service failure. The first two are honest `200`s with different reasons; the third is a real non-2xx and never shares their shape. A time-adjustment suggestion always offers more, never less; a different-topic suggestion is valid regardless of time.
- Before approving: inspect each stop's content and source, see total estimated time, see attribution for every source actually used (a list - content may blend sources), plus a sitewide credit naming OSM, the routing provider, Wikipedia, NSW Heritage, and Inner West Council.
- Re-Jaunt and remove/replace both re-validate time feasibility before re-approval. No account; nothing persists server-side beyond one request/response; end-to-end target ~30-45s.
- A photo shows only with a confirmed rights-cleared source image (checkable license/source/attribution); otherwise no photo, no placeholder.

## Technical Decisions

- **Statelessness:** one request returns the complete route+stops+content; replace/mark-visited/Re-Jaunt are separate stateless requests. State lives in frontend `localStorage`: the active trip (`phase` + `schema_version`, so refresh recovers and an invalid payload safely resets) and a separate visit-history key untouched by "end trip."
- **Exclusion vs. retention:** `excluded_ids` is a hard filter - Re-Jaunt adds every stop of the rejected route ("clean break"), resending the full list each call, never a delta. `retained_ids` (replace-one-stop) constrains the search to keep every retained stop plus one replacement, not an unconstrained re-search. Story 1.8 must pick and document one concrete replacement strategy.
- **AI selection honesty:** the selection schema needs an explicit "none suitable" outcome (with a reason), distinct from zero-feasible and from a service failure. Menu construction must guarantee every stop in some feasible combination appears in some offered option before filling the rest by budget-usage ratio.
- **Error shape:** "no suitable route" is always a `200` with `{"feasible": false, "reason": ...}`; non-2xx is reserved for genuine failures (mirrors `CatalogueError -> 503`); a real AI/service failure must no longer collapse into that same shape.
- **Content generation:** one batched call per route, not per stop, run synchronously before the response returns; grounding is a two-stage check - a cheap rule-based pre-filter, then a batched LLM-based semantic check that is the actual final gate (the rule-based check alone can't catch a fabricated claim/relationship that introduces no new date or name). Content is only ever shown once the semantic check has genuinely confirmed it. Any grounding/generation failure falls back to the stop's raw source excerpt rather than discarding the route. Each stop carries its own `id`, order, `content`, and an attribution **list** of `{source_type, source_title, source_url}` (one per source used, since content may blend a Contextual Source) - never a flat string or single triple. Contextual Sources come from a small curated seed file behind one fixed-contract function, swappable later for real retrieval.
- **Preference signal:** no Python-computed "prominence" field - `source_type`/`source_title` join AI's candidate payload and the slider value passes into its prompt as guidance; AI alone judges well-known-ness.
- **Secrets:** provider keys (OpenRouteService, OpenAI) stay server-side via the existing `.env`/`load_env()`/`get_api_key()` pattern, never exposed to the browser.
- **Route geometry:** a new `services.py` function fetches the real polyline for the chosen order (same ORS-auth pattern as the duration-matrix function); reused, not re-fetched, by the walking screen later.
- **Catalogue coverage:** History/Architecture tags for heritage-sourced records are AI-proposed, human-approved, and persisted in a maintained override file the importer reads - never an edit a routine rerun would discard.

## UX & Interaction Patterns

- Map stop markers: a white-plate circle with the order number plus a small place-type icon (from a name keyword, else the topic); Jarrod-at-the-stop as an individual marker is rejected. A rights-cleared photo shows inside the stop's content overlay when tapped - never as the map pin or a row thumbnail.
- The compact pill button and full-width primary button are genuinely separate, never interchangeable - the project's most-repeated bug. Chips/pills signal selection via fill inversion, never a border/checkmark. Re-Jaunt and "Start my jaunt" appear as an equal-weight pair.
- The stop list and stop-info overlay reuse one bottom-sheet pattern (swipe-down), and each needs a real visible, tappable close control too - a flagged gap this epic fixes. Jarrod is always a real cropped region of the source PNGs, never redrawn; failures use his sad pose plus plain language, never a red/alert color.
- Copy follows Voice & Tone: plain, warm, topic-specific where known, never generic form-field language or alarm-coded failure framing.
- First-time accessibility checks land here, none previously verified: full keyboard operability with real `aria-label`s (map-tap start needs its own keyboard alternative), alt text on stop photos, a WCAG contrast check on body-length ink-on-cream/surface text, a ~44x44pt touch-target check, and a dynamic-type check on tightly-sized labels.
- The one-shot location prompt must use the browser's native, accessible dialog, not a custom UI.

## Cross-Story Dependencies

- Backend before frontend: 1.2 and 1.3 are hard prerequisites for 1.4; 1.4 is a hard prerequisite for 1.5 and 1.6. 1.1 feeds 1.5's inputs but doesn't block 1.4.
- Should-tier sits on Must-tier: 1.7/1.8 need 1.4/1.5 and extend its contract with `excluded_ids`/`retained_ids`; 1.9 needs 1.1's control plus 1.4's backend fields; 1.10 only needs 1.1 (independent of Epic 2's continuous tracking); 1.11 needs 1.5's stop-row component.
- Epic 1 is standalone: no Must-tier story depends on Should/Could, and none depend on Epic 2, 3, or 4.
