---
title: Reviewer Gate — rubric walk
target: ARCHITECTURE-SPINE.md (architecture-IBE160-2026-10-07, "Jaunt frontend-wiring slice")
reviewer: Claude (subagent, read-only review)
date: 2026-10-07
scope: Rubric-driven review per the 7-point checklist supplied by the caller. Does NOT re-find the six issues the prior reconciliation pass already fixed (binds overclaim, AD-1 sub-rules, DESIGN.md contradiction, misattributed citation, Deferred bullets for OQ-7/20/2, PRD §0 callout) — those were spot-checked for correct landing, not re-litigated.
---

# Verdict

**Conditional pass.** The spine is well-grounded in its sources, its named tech is verified-current (not asserted from training-data memory), it ratifies rather than contradicts the real brownfield code on every point checked but one, and all six fixes from the prior reconciliation pass landed correctly and remain internally consistent. One finding (AD-4's factual claim about what the AI prompt already carries) is a genuine architecture-level risk that should be corrected before `bmad-create-epics-and-stories` builds on it; the rest are smaller clarity/consistency gaps, not forks.

---

# Prior-pass fixes: verified landed correctly

Checked each of the six fixes the earlier reconciliation pass made, against the current file and its sources — all landed correctly and are internally consistent, no regressions found:

1. **Frontmatter `binds` trim** (`[FR-4, FR-6, FR-10, FR-11, FR-17, FR-18, FR-19, FR-23]`) — every one of these 8 FRs is traceable to a specific AD or Capability-map row in the body (FR-4→AD-4, FR-6→AD-1 sub-rule+Capability map+Deferred, FR-10/11→AD-5, FR-17/18→AD-6, FR-19→AD-3+Deferred+Capability map, FR-23→AD-1 sub-rule+Capability map). No orphaned binds, no orphaned FR coverage without a binds entry.
2. **AD-1 sub-rules** (GeoJSON layers for many-of-a-kind data; DOM `Marker({element})` for one-off image content) — verified against `static/app.js`: the start-point marker already uses `new maplibregl.Marker({ element: buildStartMarkerElement() })` (line 57), confirming the "pattern already established" claim is literally true, not aspirational.
3. **Misattributed citation** (NSW Heritage + Inner West Council from `prd.md` FR-20, not `architecture-plan.md`'s narrower list) — confirmed: `architecture-plan.md`'s "Still-open decisions" list only names OSM/routing-provider/Wikipedia; `prd.md` FR-20 is the one that adds NSW Heritage and Inner West Council. Citation is now correct.
4. **DESIGN.md Map-paragraph contradiction fix** — confirmed resolved in the current `DESIGN.md`: the paragraph now reads "PRD Open Question 19 ... is resolved: the running app now renders vector tiles ... What remains open is narrower," with no leftover "not yet resolved" sentence sitting next to it.
5. **Deferred bullets for OQ-7/OQ-20/OQ-2** — present and each accurately mirrors its PRD/EXPERIENCE.md source (checked against `prd.md` §9 and `EXPERIENCE.md`'s State Patterns table).
6. **PRD §0 "Known planning gaps" callout bullet** — present as the spine's final Deferred bullet, correctly framed as "fixes the invariants ... doesn't size the build itself."

---

# Checklist walk

## 1. Fixes the real divergence points for epics/stories, misses none

Mostly yes. AD-1 (map rendering), AD-2 (state ownership), AD-3 (content-generation timing), AD-5 (exclusion mechanism), AD-6 (visit history) each name a concrete, real fork and a concrete rule that closes it, and each is checked against the actual code below (§5). **AD-4 is the exception** — see Finding 1: its Rule asserts something about the *current* AI prompt payload that isn't true, which could itself cause the two-builder divergence AD-4 exists to prevent. See Finding 1.

Must-tier FRs not explicitly bound (FR-1, 2, 3, 5, 7, 8, 9, 12, 20) are reasonably left unbound: they're either pure UI/copy details with no fork risk (FR-1, 8), already structurally resolved by AD-2/AD-3 (FR-7, FR-12 — content is already in the localStorage payload by the time any screen needs it), inherited/unchanged backend behavior (FR-5), or explicitly named in Deferred with reasoning for why they're not architecture forks (FR-9's fallback-shape note, FR-20's attribution bullet). This is appropriate scoping for a feature-altitude spine, not a silent gap.

## 2. Every AD's Rule is enforceable and actually prevents its divergence

AD-1, 2, 3, 5, 6: yes — each Rule is a concrete, checkable constraint (e.g., AD-5's "takes an `excluded_ids` parameter," AD-2's "one POST returns the complete payload"). AD-4: **not fully enforceable as written** — see Finding 1.

Secondary issue: AD-1 through AD-4 carry an explicit `[ADOPTED]` status tag in their heading; AD-5 and AD-6 do not, with no stated reason for the inconsistency. See Finding 4.

## 3. Nothing under Deferred could let two units diverge if left unresolved

Reviewed all 10 Deferred bullets. Nine are safely non-forking (either inherit an already-ratified module boundary, are pure content/UI/copy questions, or are explicitly flagged as genuinely open rather than silently assumed). One has a factual accuracy problem rather than a forking problem — see Finding 3 (the FR-13/16/22 bullet mischaracterizes an already-resolved PRD/UX question as open).

One adjacent observation, not strictly a Deferred-list problem but the same family of risk the Deferred list elsewhere accepts and names explicitly: the exact *shape* of the localStorage trip-state object AD-2/AD-6 mandate is never pinned down or flagged, unlike the analogous (and explicitly reasoned) choice to defer exact API payload field names. See Finding 5.

## 4. Named tech is verified-current, not asserted from training data

Checked independently (web search + local environment), not taken on the spine's or memlog's word alone:

- **MapLibre GL JS 5.6.1, pinned, because v6 drops the UMD bundle**: confirmed via web search — MapLibre v6.0.0 shipped 2026-07-22, is ESM-only, and the v6 migration guide confirms the UMD/CSP bundle from v5 is gone. The spine's stated reason for pinning is accurate and current, not a training-data guess.
- **OpenFreeMap, free, no API key**: confirmed via web search — the public instance remains free, no registration/API key/cookies, as of current sources.
- **Flask 3.1.3**: confirmed against the actual local environment (`pip show flask` → `Version: 3.1.3`), matching the spine's Stack table exactly.
- **OpenRouteService / OpenAI**: no version number is claimed for either (ORS is described by profile/key-handling only; OpenAI by "model configurable via env var" only), so there's nothing stale to assert — appropriately unpinned rather than falsely precise.

No currency issues found here.

## 5. Ratifies rather than contradicts the brownfield code

Spot-checked `app.py`, `planner.py`, `ai.py`, `services.py` directly against specific spine claims:

- `app.py`: exactly two routes (`/`, `/api/places`), no Planner/AI calls, `CatalogueError`→503 pattern exists exactly as the Consistency Conventions table describes. Confirmed.
- `planner.py`: `shortlist_candidates`, `plan_route`, `_build_ai_options`, `check_feasibility` all exist and match the described pipeline; no `excluded_ids` parameter exists yet anywhere in the current signature — consistent with AD-5 being a forward-looking rule for not-yet-built work, not a false "already built" claim.
- `ai.py`: `select_stops()` exists; no content-generation function exists yet — matches the spine's "ai.py has select_stops() [built]; generate_content() [FR-19, not yet built]" claim exactly.
- `services.py`: only `fetch_duration_matrix()` exists; no route-geometry fetch — matches the spine's claim exactly.
- `static/app.js`: confirms the `Marker({element})` precedent cited by AD-1 (see prior-pass-fix #2 above).

**One mismatch found** — AD-4's Rule claims the preference value will pass "alongside each candidate's real `source_type`/`source_title`/content" into the *existing* selection prompt. `planner.py`'s `_build_ai_options()` (the function that actually builds that payload, lines ~245–263) only includes `id`, `name`, `topics`, and `source_excerpt` per stop — **not** `source_type` or `source_title`. See Finding 1.

## 6. Covers the driving PRD's capabilities adequately for a feature-altitude spine

Adequate. The spine explicitly scopes itself to the frontend-wiring gap and the Should-tier backend capabilities the PRD flagged as newly-discovered-but-unbuilt (FR-4, 10, 11, 17, 18, 19, 23 — plus FR-6's geometry dependency). It correctly declines to re-architect already-built Sprint 1–6 work and correctly pushes pure UI/copy/content questions to UX or epics-and-stories rather than inventing architecture for them. This matches the PRD's own framing in §0 and the "Pending UX/architecture input" list in §6.1.

## 7. Every dimension this altitude owns is decided, deferred, or an open question

Deployment/environment: **explicitly addressed**, not silent — the Structural Seed's "Deployment & environment" line states local-only V1, `python3 app.py`, no hosting/infra, citing `README.md`. Good.

Secrets/auth, statelessness, naming/id conventions, error-envelope shape: all explicitly addressed in Consistency Conventions.

**One dimension claimed-but-not-actually-covered**: the Consistency Conventions table's "State & cross-cutting" row lists **logging** in its own concern header, but the convention text in that row never mentions logging at all — only secrets handling and statelessness are actually addressed. This is the same self-overclaim pattern the prior pass fixed elsewhere (frontmatter `binds`, AD-1's "all map UI"), just not caught here. See Finding 2.

---

# Findings

### Finding 1 — AD-4's Rule misstates the current AI payload (Medium-High)
**Where:** `ARCHITECTURE-SPINE.md` AD-4 Rule, vs. `planner.py::_build_ai_options()` (~lines 245–263).

AD-4 says the landmark/hidden-gem preference should pass "into AI's existing selection prompt alongside each candidate's real `source_type`/`source_title`/content." In the actual code, the per-stop dict `_build_ai_options()` sends to AI only carries `id`, `name`, `topics`, `source_excerpt` — `source_type` and `source_title` are not in that payload today, even though they exist on the catalogue record and are already exposed to the *browser* via `app.py`'s `PUBLIC_FIELDS`.

This matters precisely because of what AD-4 exists to prevent: a story-writer or builder who takes AD-4's Rule at face value could reasonably conclude no change to `_build_ai_options()` is needed — the fields are already there, says the spine — and wire the preference value into a payload that's missing exactly the fields AD-4 says AI should be judging it against. A different builder, cross-checking against the actual code or the PRD's catalogue schema (which does include `source_type`), would expect those fields added. That's a real two-way divergence in the feature AD-4 is supposed to make unambiguous.

**Suggested fix:** amend the Rule to say the preference value is added to `_build_ai_options()`'s per-stop payload *alongside the existing fields*, and name `source_type`/`source_title` as fields that also need to be added there (not already present) — don't just assert they're already sent.

### Finding 2 — "Logging" claimed but never addressed in Consistency Conventions (Medium)
**Where:** `ARCHITECTURE-SPINE.md`, Consistency Conventions table, "State & cross-cutting" row.

The row's own concern header is `(mutation, errors, logging, config, auth)`, but the convention text only covers statelessness and secrets/config handling. Logging (e.g., whether AI/ORS failures get logged server-side, what if anything should never be logged given the privacy stance in `prd.md` §7) is a real cross-cutting dimension this altitude plausibly owns, and it's left completely silent while the table claims to cover it. This is the same category of issue the prior pass already fixed twice elsewhere (overclaimed `binds`, overclaimed "all map UI") — worth the same treatment: either add a line, or narrow the header.

### Finding 3 — Deferred bullet mischaracterizes an already-resolved PRD/UX decision as open (Low-Medium)
**Where:** `ARCHITECTURE-SPINE.md` Deferred, the FR-13/FR-16/FR-22 bullet: "`EXPERIENCE.md` already flags FR-13's own UI mechanism as open (PRD Open Question 8)."

`prd.md` §9 Open Question 8 is struck through and explicitly marked **"Resolved during UX discovery (2026-10-03): an explicit 'visited' checkbox in the top-right corner of the stop's info page/overlay."** `EXPERIENCE.md`'s own Component Patterns ("Visited checkbox badge") and State Patterns tables present this as a settled behavioral rule, not an open question. The spine's own two cited sources both say this is resolved; the Deferred bullet says the opposite. Low practical risk (the underlying mechanism really is settled and unambiguous elsewhere in the doc set), but it's a factual error against the spine's own sources and should be corrected so a future reader doesn't go looking for a decision that was already made.

### Finding 4 — Inconsistent `[ADOPTED]` status tagging across ADs (Low)
**Where:** `ARCHITECTURE-SPINE.md` headings — AD-1 through AD-4 carry `[ADOPTED]`; AD-5 ("Replace / Re-Jaunt exclusion") and AD-6 ("Visit history") do not.

Both AD-5 and AD-6 read as settled, non-tentative rules in their own body text (and the memlog records AD-5 as "stated directly rather than elicited" and AD-6 as "a natural consequence of AD-2," i.e., both are intended as decided). The missing tag is likely an oversight, but since the tag is used meaningfully elsewhere (AD-1 separately distinguishes "[ADOPTED]" for the general decision from "Status: base layer implemented..." for sub-parts), its absence on two ADs could be misread as "not yet ratified."

### Finding 5 — localStorage trip-state shape is never pinned down or flagged (Low)
**Where:** AD-2, AD-6 — both say *where* trip state lives (browser `localStorage`) but neither, nor the Deferred section, says anything about its *shape* (field/key names for the persisted trip object, visited/favourite lists, etc.).

The spine explicitly reasons through and accepts an analogous gap for API payload field names ("straightforward to derive... not a genuine two-builder divergence risk... left to epic/story-level detail"). The localStorage schema is arguably more divergence-prone than that, since multiple independently-built screens (setup, review, walking, end-of-walk) all need to read and write the same object across different build sessions/people. This isn't necessarily wrong to leave at story-level detail, but unlike the API-naming case, it isn't named or reasoned about anywhere — it's just silent. Worth either an explicit one-line Deferred bullet (parallel to the API-naming one) or folding it into AD-2/AD-6's own text.

---

# Not re-litigated (per instructions)

Confirmed-landed-correctly only, not re-examined for new problems: the `binds` trim, AD-1's two sub-rules, the attribution citation fix, the DESIGN.md contradiction fix, the three new Deferred bullets (OQ-7/20/2), and the PRD §0 callout bullet.
