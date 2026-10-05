# Input Reconciliation: architecture-plan.md vs prd.md

**Input document:** `docs/architecture-plan.md`
**PRD checked:** `_bmad-output/planning-artifacts/prds/prd-IBE160-2026-09-29/prd.md`
**Purpose:** Verify the PRD accurately and completely reflects architecture-plan.md's statements about current build state, technical constraints, and known limitations.

---

## Claims checked and confirmed accurate

| Claim | Verdict |
|---|---|
| 30–120 min time range, 5-minute fixed dwell time carried over | **Accurate.** Matches architecture-plan.md lines 84–86 exactly; PRD correctly flags it as an unconfirmed carried-over assumption (FR-2, Assumptions Index). |
| "15-minute route, technically feasible but low budget-usage" used as counter-metric | **Accurate** for this half of the claim. Matches Sprint 3 known limitations (architecture-plan.md lines 184–187: "a 'feasible' 2-stop, 60-minute-budget route that used only about 15 minutes (26% budget usage)"). See inaccuracy #1 below for the other half of the same PRD sentence. |
| `import_places.py` hard-codes English-only Wikipedia parsing | **Accurate.** Matches architecture-plan.md line 175 ("English-only Wikipedia enrichment..."). Correctly carried into PRD §4.6 FR-21 and its NFR. |
| Existing test suite should keep passing as features are added | **Accurate**, and PRD correctly notes its cited count (167/167) is newer than and supersedes architecture-plan.md's documented 155/155 at end of Sprint 6 (line 204). |
| Minimum budget-usage threshold is an open question since Sprint 3/4 | **Accurate.** Matches lines 187–188 almost verbatim; carried into PRD Open Question 6. |
| Attribution requirements (OSM, routing provider, Wikipedia, NSW Heritage, Inner West Council) | **Accurate.** Matches the Sprint 8 task (line 152) and the "Still-open decisions" list; carried into PRD FR-20. |
| Heritage included as a first-class Topic | Reasonable inference, correctly flagged as an assumption since Sprint 6 (lines 200–210) post-dates the original brief. |

---

## Gaps / inaccuracies found

### 1. Fabricated/unsourced statistic attributed to architecture-plan.md (SM-C1)

PRD §8, SM-C1 states:

> "`architecture-plan.md` already documents both a 'technically feasible but only 15-minute-used' failure mode and **routing-provider estimates running 20–30% optimistic versus real walking**."

The first half (the 15-minute/26%-budget-usage failure mode) is real and correctly sourced to Sprint 3's known limitations. **The second half — a claim that ORS/routing estimates run "20–30% optimistic versus real walking" — does not appear anywhere in architecture-plan.md.** The document's only concrete walking-speed data point is Sprint 1's confirmation of "5.0 km/h implied speed on a real two-point test" (line 170); it never compares this against real-world walking results, and no real-world walking test has occurred yet in the plan (that's explicitly a Sprint 8 task, "a real-world walking test comparing estimated vs. actual time," line 152, not yet run per the document). This is a specific, quantified claim presented as if sourced from the architecture document, but it is not — it should either be removed, re-attributed to wherever it actually came from (if anywhere), or marked as the PRD author's own projection/assumption rather than something "architecture-plan.md already documents."

### 2. FR-21's "config-only" claim contradicts the heritage importer's documented limitation

PRD §4.6, FR-21 consequence states:

> "After phase (1), running the importers against a new bounding box (set via configuration) produces `ready` Stops **without modifying `planner.py`, `ai.py`, or the frontend**."

This is true for `import_places.py` (OSM/Wikipedia) and `import_street_art.py` (Inner West Council dataset), which are genuinely rerunnable against a new boundary. It is **not** true for `import_heritage.py`. Architecture-plan.md's Sprint 6 known limitations are explicit on this point (lines 206–209):

> "**The pipeline cannot grow itself.** Adding another heritage stop means manually picking an ArcGIS id and manually copying its Statement of Significance - there is no automated path from 'more candidates exist' to 'more ready records,' unlike the other two importers. This was a deliberate trade-off to avoid working around an access control, not an oversight."

So for a second pilot area, heritage coverage would require hand-curating new ArcGIS ids and manually transcribing Statement-of-Significance text per item — a config change alone cannot "produce `ready` Stops" for that topic. The PRD's FR-21 doesn't carry this limitation forward anywhere (not in the FR's consequences, not in Open Question 5, not in §7's extensibility NFR). As written, FR-21 overstates what the config refactor achieves and could mislead downstream architecture/epic work into assuming a uniform, low-effort path to a second pilot area across all three importers.

### 3. Untested content-grounding risk for terse (OSM-tag-sourced) excerpts not carried into FR-19/SM-C2

Architecture-plan.md's Sprint 1 known limitations (lines 177) state:

> "**OSM-tag-sourced content is terse.** ... the resulting excerpt is a short factual fragment ... real and sourced, but much thinner than a Wikipedia or Wikidata excerpt. **Expected to be sufficient input for Sprint 5's AI content generation, but not yet tested against that.**"

This is a specific, named, *unresolved* risk about whether AI content generation (FR-19, the PRD's core differentiator) actually works well against the thinnest source excerpts in the catalogue (notably street-art entries). The PRD's FR-19 and SM-C2 address terseness only as a general principle ("source-groundedness must not be pursued by making content so terse it stops being interesting") but never acknowledge that architecture-plan.md flags this as a specific, not-yet-validated risk for a known subset of the catalogue. This would be a reasonable addition to Open Questions or the FR-19 consequences.

### 4. "There-and-back" route-ordering concern omitted entirely

Architecture-plan.md (lines 154) documents an open, deferred design concern:

> "Once real route geometry is available, consider whether the chosen stop order backtracks along the same street for a meaningful stretch (a 'there and back' feel) and, if so, prefer an equally- or near-equally-fast ordering that doesn't. ... Raised during Sprint 4 manual testing."

This is a real, named product-quality concern (a route that doubles back on itself undermines "worth taking," PRD's SM-1) explicitly deferred to Sprint 8 pending route geometry. It does not appear anywhere in the PRD — not in FR-6 (display route), not in Non-Goals, not in Open Questions — even though it's a known, documented gap between current capability and desired route quality.

### 5. Minor: "Sprints 1–6 already built" blends sprints with differing evidence in the source document

Architecture-plan.md only contains explicit "results and known limitations" sections (test counts, live-run confirmation) for Sprints 1, 3, 5, and 6 — there is no equivalent documented completion evidence for Sprint 2 or Sprint 4 within this document. The PRD's blanket framing ("Sprints 1–6 ... already implemented," §0) and FR-level claims ("Existing (Sprint 2/3)," FR-1; "existing, Sprint 4," FR-5) may well be correct based on other evidence (e.g., git history shows commits for Sprints 2 and 4), but architecture-plan.md itself is not the source for that confirmation for those two sprints. Not a contradiction, but worth noting since the PRD text implies architecture-plan.md as its basis throughout.

---

## Items checked and found to need no PRD change

- "Still-open decisions" list (routing provider, AI provider/key handling, attribution, pilot neighbourhood) — all effectively resolved by the Sprint 1/4/8 narrative and reflected correctly where relevant (FR-20, Pilot Area = Newtown).
- Sprint 1 limitations on resume-cache schema drift, approximate deduplication, and minimal Wikidata fallback — implementation-level detail correctly left out of a product-level PRD.
- Sprint 5 limitations on row-number ids, cross-source duplicate detection, and Nominatim geocoding failures — same, implementation-level.
- Sprint 6 limitation on partial heritage coverage (29 of ~174 items) — borderline, but doesn't materially change any V1 FR since V1 only needs Newtown's existing `ready` records.
