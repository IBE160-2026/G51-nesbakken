---
id: SPEC-1-9-landmark-hidden-gem-preference
companions:
  - implementation-and-verification.md
  - candidate-discovery-amendment.md
  - ../../planning-artifacts/architecture/architecture-IBE160-2026-10-07/ARCHITECTURE-SPINE.md
  - ../../planning-artifacts/ux-designs/ux-IBE160-2026-10-02/EXPERIENCE.md
  - ../../planning-artifacts/ux-designs/ux-IBE160-2026-10-02/DESIGN.md
sources: []
---

# Story 1.9 — Landmark / hidden-gem preference

Initial wiring approved and implemented on2026-10-23; preference-aware shortlisting direction approved later that day. Amended implementation completed and independently reviewed; live quality acceptance pending. See build contract in ../../implementation-artifacts/spec-1-9-preference-aware-discovery.md. Derived from this folder's decision log, Story1.9 in epics.md, AD-4 and the approved UX.

## Why

The slider reaches final AI selection, but nearest-place truncation can discard landmarks before selection and source excerpts do not reliably describe recognisability. Let AI use the preference when choosing routing candidates as well as the final feasible route.

## Capabilities

- **CAP-1**
  - **intent:** Users express their preference during setup without an extra confirmation step.
  - **success:** Existing sliders stay synchronized; untouched means Balanced0.5; endpoints mean0 well-known and1 hidden gems; Wild Jaunt and chosen topics use the selected value. Confirmation has no slider.
- **CAP-2**
  - **intent:** Selection considers the preference alongside actual source evidence while respecting route constraints.
  - **success:** Exact numeric value reaches AI on initial requests, retries, Re-Jaunt and Replace; each option's candidates include source_type/source_title and existing content. Preference is guidance, not a filter; existing feasibility, rejection, retention and honest-fallback behaviour passes regression checks.

- **CAP-3**
  - **intent:** Users’ preference influences which eligible nearby places reach route planning.
  - **success:** AI chooses only offered catalogue IDs from the topic-matching nearby pool before the routing cap; Python enforces exclusions, retained stops and route feasibility. Relevant landmarks can enter even when outside the nearest12. Unknown prominence is not automatically a hidden gem.

## Constraints

- Follow AD-4: no Python prominence score, source-type proxy or production landmark/hidden-gem labels. Preserve continuous values rather than a three-value enum.
- Reuse current UI, stateless endpoint and prevalidated option menu. Preserve geometry/time arithmetic, exclusion accumulation, retained stops and technical-versus-honest failure distinction.
- General knowledge may inform qualitative recognisability during selection; uncertainty must remain explicit. Generated stop stories and factual claims remain grounded in approved sources. Catalogue changes and duplicate-source enrichment require separate review.
- Automated checks make no paid calls. Fixture tests prove wiring and instructions, not live model judgement.

## Non-goals

- Profiles, Local Legends contributions, city-centre imports, provider changes, retrieval redesign, new dependencies or guarantees of different routes at each slider position.

## Success signal

Automated frontend/API/planner/prompt checks establish exact end-to-end propagation and unchanged route constraints. A separately authorised live comparison can assess whether the offered real candidates support a useful preference distinction; weak contrast is reported honestly.

## Approved defaults

- API callers omitting preference receive Balanced0.5; invalid explicit values receive400 before provider calls.
- Wild Jaunt honours an explicitly moved slider, as EXPERIENCE.md says it applies to both paths; the epic's Balanced wording describes the untouched default.

## Implementation status

- Technical bounds and recovery policy are settled in the build contract: at most200 compact alternatives,100000-character candidate input, at most2 discovery attempts and one nearest shortlist recovery after honest failure. Preference never blocks an otherwise suitable walk.
- Live quality evaluation remains separate from mocked transport/constraint tests.
