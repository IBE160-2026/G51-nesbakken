# Epic 1 Context: Plan and Review a Trustworthy Walk

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

A user sets a starting point, available time, and topic (or "surprise me," or a landmark/hidden-gem preference), and gets back a real, source-grounded, time-feasible proposed walk with inspectable per-stop content and visible attribution. They can adjust it (remove/replace a stop, ask for a different one) before explicitly approving, and if nothing suitable exists they get an honest, non-dead-end explanation instead of a weak result. This is V1's Must-tier core plus its directly-attached Should-tier refinements: the whole Trip-Setup/Route-Review frontend plus the AI content-generation and grounding pipeline review depends on. It matters because the product's stated differentiator is choosing an honest alternative over a fabricated-looking answer - this epic is where that promise is either real or isn't, and every later epic assumes this planning/review loop already works.

## Stories

- Story 1.1: Trip Setup inputs - starting point, time, and topic (Must)
- Story 1.2: Catalogue topic coverage for History and Architecture (Must)
- Story 1.3: AI content generation, grounded and checked (Must)
- Story 1.4: Generate a proposed Route via a new planning endpoint (Must, backend-only)
- Story 1.5: Review and approve the proposed Route (Must)
- Story 1.6: Honest fallback when no suitable Route exists (Must)
- Story 1.7: Re-Jaunt (Should)
- Story 1.8: Manually remove or replace a stop (Should)
- Story 1.9: Landmark <-> hidden-gem preference (Should)
- Story 1.10: Use current location for starting point (Should)
- Story 1.11: Stop photo, shown only when rights-cleared (Should)

## Requirements & Constraints

- Starting point: any map tap (no boundary rejection) or a named-start chip; "use current location" is a one-shot, permissioned alternative falling back cleanly on denial/failure. A start far from any real stop is handled by the honest fallback, not a separate error.
- Time: 30-120 min, 5-min increments; walking + dwell time must never exceed it.
- Topic: history, architecture, public art, or "surprise me" (all topics stay eligible); heritage is never user-facing. History/architecture each need >=2 ready stops. An optional landmark<->hidden-gem preference shapes ranking only, never excludes a stop.
- A route has a minimum of 2 stops, a dynamic per-request maximum (never fixed/padded), every stop `ready` status.
- Before approving: inspect each stop's content/source, see total time, see attribution for every source used, plus a sitewide credit naming OSM, the routing provider, Wikipedia, NSW Heritage, and Inner West Council. Approval is one explicit action.
- No suitable route -> honest, plain-language explanation with a way back, never a weak result/dead end/user's-fault framing; a time suggestion only ever offers more. A technical/service failure must read visibly differently from this.
- Re-Jaunt and remove/replace both re-validate time feasibility before re-approval.
- Generated content must be grounded in a stop's source excerpt and/or an approved contextual source, backed by both an automated check and ongoing manual spot-checking.
- A stop photo appears only when rights-cleared; otherwise no photo, no placeholder.
- No account/login; nothing persists server-side beyond the single request/response. Mobile-first; existing automated test suite must keep passing.
- Success is judged by: real-input suitability, phone-viewable/followable routes, finishing near the requested time, genuinely real/relevant stops, source-consistent content, users understanding why each stop was included, and an honest response when nothing suitable exists.

## Technical Decisions

- Backend is fully stateless: one planning request returns the complete route+stops+content; Re-Jaunt/replace/mark-visited are separate stateless requests. State lives in two frontend `localStorage` keys: the active trip (`phase` + `schema_version` tags so refresh recovers correctly and bad payloads safely reset; also holds session-local `excluded_ids`) and a separate visit-history key (out of scope here).
- Feasibility/ordering: brute-force permutation over a shortlist; max stops = `min(7, requested_minutes // dwell_minutes_per_stop)`, never fixed. Every stop in any feasible combination is guaranteed a slot in at least one offered option.
- AI judges relevance/taste only over the pre-vetted feasible menu - never routing arithmetic, never overridden by Python. Three outcomes stay distinct: zero feasible combinations (`{"feasible": false}`, 200), AI's `none_suitable` (also 200, different reason), and a genuine AI/service failure (re-raised, mapped to non-2xx).
- Story 1.3 (next up) - content generation: one batched AI call per route (not per stop), synchronous at plan time, avoiding N sequential ~2s calls. Grounding is a rule-based (non-LLM) check by default, escalating to a model call only if a prototype proves it insufficient; must also be reusable for Epic 3's walk summaries later. A per-stop grounding failure or failed/timed-out generation call both fall back to that stop's raw source excerpt - never passed through, never failing the whole route. Attribution is a list of `{source_type, source_title, source_url}` entries, one per source actually used (never a flat string/single triple). Contextual sources come from a small curated seed file (`data/contextual_sources.json`) reached only through one function with a fixed contract - a swappable seam for future real retrieval. The prototype grounding check must be validated against both thin and richer real catalogue excerpts, checking factual support and whether thin-excerpt content is worth reading.
- The preference slider sends its exact continuous value into AI's existing prompt (no new Python "prominence" score); `source_type`/`source_title` are added to AI's candidate payload as real signal.
- Replace-a-stop passes kept stops as `retained_ids` (constrained search for one replacement); Re-Jaunt excludes every stop of the whole rejected route via a cumulative, frontend-resent `excluded_ids` list - deliberate, not a bug.
- Malformed input is rejected immediately, before any routing/AI call. End-to-end target: ~30-45s typical.
- Map rendering: data-driven features (route line, stop circles, amenity points) are GeoJSON + MapLibre paint layers, never one DOM marker per feature; a rights-cleared photo pin uses a real `maplibregl.Marker`.
- The History/Architecture catalogue fix lives in a maintained override file the importer itself reads (survives re-import), replacing each record's heritage tag, every AI assignment human-reviewed first.

## UX & Interaction Patterns

- The compact pill button and full-width primary button are genuinely separate, never interchangeable - the project's most-repeated bug; verify short-label buttons never inherit full-width styling. Re-Jaunt/"Start my jaunt" and Choose-Topic/Wild-Jaunt are equal-weight pairs.
- Chips/pills signal selection via fill inversion, never a border/checkmark; every tappable control meets a ~44x44pt touch target. The preference slider defaults to "Balanced," shown beneath buttons on topic-at-rest/Choose-Topic, absent from the Wild Jaunt confirmation sheet.
- The stop list and stop-info overlay reuse one bottom-sheet pattern (swipe-down plus a real visible close control); a stop row's "X" remove affordance appears only where remove/replace is in scope.
- Every Jarrod appearance is a real cropped/composited region of the two source PNGs, never hand-drawn/AI-regenerated; failures use his sad pose plus plain language, never color alone.
- First-time accessibility checks land in this epic: full keyboard operability + real `aria-label`s, alt text on stop photos, a WCAG contrast check on body-length ink-on-cream text, and dynamic-type checks on tightly-sized labels.

## Cross-Story Dependencies

- Backend before frontend: 1.2 and 1.3 must exist before 1.4 (endpoint); 1.4 is a hard prerequisite for 1.5 and 1.6. 1.1 feeds 1.5 but doesn't block 1.4.
- Should-tier sits on Must-tier: 1.7/1.8 need 1.4+1.5; 1.9 needs 1.1's control + 1.4's backend fields; 1.10 only needs 1.1 (independent of Epic 2's continuous tracking); 1.11 needs 1.5's stop-row component.
- Epic 1 is standalone: no dependency on Epic 2, 3, or 4.
