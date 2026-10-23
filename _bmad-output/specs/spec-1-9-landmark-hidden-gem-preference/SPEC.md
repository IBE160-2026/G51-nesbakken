---
id: SPEC-1-9-landmark-hidden-gem-preference
companions:
  - implementation-and-verification.md
  - ../../planning-artifacts/architecture/architecture-IBE160-2026-10-07/ARCHITECTURE-SPINE.md
  - ../../planning-artifacts/ux-designs/ux-IBE160-2026-10-02/EXPERIENCE.md
  - ../../planning-artifacts/ux-designs/ux-IBE160-2026-10-02/DESIGN.md
sources: []
---

# Story 1.9 — Landmark / hidden-gem preference

Approved for implementation on2026-10-23. Derived from this folder's decision log, Story1.9 in epics.md, AD-4 and the approved UX.

## Why

The existing setup slider saves a preference but has no effect on selection. Connect it to qualitative AI selection so users can favour familiar landmarks or lesser-known discoveries as the catalogue expands.

## Capabilities

- **CAP-1**
  - **intent:** Users express their preference during setup without an extra confirmation step.
  - **success:** Existing sliders stay synchronized; untouched means Balanced0.5; endpoints mean0 well-known and1 hidden gems; Wild Jaunt and chosen topics use the selected value. Confirmation has no slider.
- **CAP-2**
  - **intent:** Selection considers the preference alongside actual source evidence while respecting route constraints.
  - **success:** Exact numeric value reaches AI on initial requests, retries, Re-Jaunt and Replace; each option's candidates include source_type/source_title and existing content. Preference is guidance, not a filter; existing feasibility, rejection, retention and honest-fallback behaviour passes regression checks.

## Constraints

- Follow AD-4: no Python prominence score, source-type proxy or production landmark/hidden-gem labels. Preserve continuous values rather than a three-value enum.
- Reuse current UI, stateless endpoint and prevalidated option menu. Preserve geometry/time arithmetic, exclusion accumulation, retained stops and technical-versus-honest failure distinction.
- Source evidence supports selection; do not invent prominence or stories from thin content. Catalogue changes and duplicate-source enrichment require separate review.
- Automated checks make no paid calls. Fixture tests prove wiring and instructions, not live model judgement.

## Non-goals

- Profiles, Local Legends contributions, city-centre imports, provider changes, retrieval redesign, new dependencies or guarantees of different routes at each slider position.

## Success signal

Automated frontend/API/planner/prompt checks establish exact end-to-end propagation and unchanged route constraints. A separately authorised live comparison can assess whether the offered real candidates support a useful preference distinction; weak contrast is reported honestly.

## Approved defaults

- API callers omitting preference receive Balanced0.5; invalid explicit values receive400 before provider calls.
- Wild Jaunt honours an explicitly moved slider, as EXPERIENCE.md says it applies to both paths; the epic's Balanced wording describes the untouched default.

## Open Questions

- No unresolved implementation questions. Optional live AI evaluation remains a separate step.
