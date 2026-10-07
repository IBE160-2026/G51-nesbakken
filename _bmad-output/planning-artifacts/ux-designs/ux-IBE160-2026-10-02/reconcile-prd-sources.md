# Reconciliation: DESIGN.md / EXPERIENCE.md vs. PRD sources

Checked against `prd.md`, `addendum.md` (EXPERIENCE.md's declared `sources:`), and `docs/product-brief.md` (vision/tone cross-check, not a formal source). Pass covers every FR, UJ, NFR, and qualitative/tiering item in the PRD/addendum.

## Sources frontmatter check

- **EXPERIENCE.md**: `sources:` lists `prd.md` and `addendum.md` — correct, matches the task brief.
- **DESIGN.md**: has **no `sources:` field at all** in its frontmatter (confirmed via grep — only `name`, `description`, `status`, `created`, `updated`, `colors`, `typography`, `rounded`, `spacing`, `components`). Yet its prose cites `FR-1`, `FR-9`, `FR-22`, `FR-23` by number and clearly draws on the PRD throughout. This is an inconsistency between the sibling spine files — DESIGN.md should either declare the same `sources:` list as EXPERIENCE.md or the omission should be explained. Flag for the finalize step to fix.

## Real gaps found

1. **FR-17's retention/reset question (PRD Open Question 7) is dropped, not carried forward.** PRD §6.1 explicitly lists "FR-17 (retention/reset behaviour, OQ-7)" under "Pending UX/architecture input" — i.e., the PRD expects UX or architecture to either resolve or explicitly flag this before story-writing. EXPERIENCE.md's Foundation and Scope Tiers sections describe Visit History/Favourites as local-only (correct) but never mention whether history ever expires or can be cleared by the user — no "Open" note anywhere, unlike how FR-11's replacement logic (OQ-2) and the "X min left" ambiguity (OQ-20) were correctly carried forward as explicit Open items. This is a silent drop of a PRD-flagged open question, not a correct out-of-scope omission (retention/clear-history is a user-facing behavior question, not backend-only).

2. **Scope Tiers table's "Navigation chrome" row places two explicit Non-Goals inside the Must/Should/Could tiering table.** Weather-rerouting and mid-walk re-route are PRD §5 Non-Goals (fully out of V1, not merely low-priority V1 scope), but EXPERIENCE.md's Scope Tiers table lists them in the "Could (not designed in detail)" column alongside genuine V1 Could-tier items (e.g. FR-15). The cell text does say "(both Post-V1, reserved drawer rows only)," and the IA table and Component Patterns table elsewhere correctly call these "Post-V1" — so this is self-correcting in context, but structurally it risks a reader skimming the tiering table and concluding these are in-scope V1 Could items. Minor, worth a cleanup pass (e.g. a distinct "Post-V1 (reserved, not built)" annotation instead of reusing the Could column).

## Checked and confirmed correct (no gap)

- Must/Should/Could tiering in Scope Tiers matches PRD §6.1 exactly, including the late amendments: FR-14 correctly Should (not Could), FR-22/FR-23/FR-24 all correctly Should, FR-15 correctly Could and explicitly dependent on FR-14, FR-13 correctly Should (not Must) with the Visited checkbox.
- FR-9's corrected logic (alternative must offer more time, never less) is carried forward verbatim in State Patterns, including the technical-failure-vs-honest-fallback distinction, honestly flagged as "not yet designed as its own screen... a gap, not resolved" — matches PRD framing exactly, no overclaim.
- FR-11's replacement-logic ambiguity (OQ-2) and OQ-20 ("X min left" meaning) are both correctly carried forward as explicit "Open" items in State Patterns, not quietly resolved.
- FR-4's UI form (slider) is correctly resolved by EXPERIENCE.md (UX's job per OQ-1), while the backend ranking signal (OQ-3) and FR-18's exact weighting (OQ-9) are correctly left unaddressed — both are backend/tuning-only questions, same category as FR-19's grounding-check mechanism, appropriately out of scope for a UX spine.
- UJ-1 and UJ-2 are both fully realized as Key Flows, matching persona, climax, resolution, and edge cases (including the "never less time" and "no account/no lasting record" resolutions).
- Product brief's core differentiator — "Jaunt starts from the walk itself, not a destination already chosen" — is captured near-verbatim in DESIGN.md's Brand & Style section, not genericized. The "honest over fabricated" differentiator isn't restated as its own brand pillar in DESIGN.md, but is thoroughly covered in EXPERIENCE.md's Voice & Tone table and State Patterns (fallback behavior, no red/alarm color) — correct division of labor between the two spines, not a gap.
- Non-Goals (audio narration, community contributions, destination-based routing, accounts, full personalization) are absent from both spines with no contradiction.
- Privacy NFR (no server-side position storage, no account) and Platform NFR (mobile-first) are both explicitly and correctly reflected.
- FR-19 (grounding/automated-check mechanism) and FR-18's exact weighting are backend-only and correctly have no visual/behavioral spec — consistent with the task's own guidance on what counts as legitimately out of scope.
- Glossary's four Engagement States (Proposed / Opened-Engaged / Visited-Completed / Favourited) are used correctly and distinctly throughout EXPERIENCE.md (summary generation, catch-up rows, "never happens" list).

## Minor/soft observations (not hard gaps)

- FR-6's note that full route-polyline display depends on unbuilt Sprint-8 route-geometry work is only indirectly echoed via DESIGN.md's OQ-19 map-styling-achievability flag — adjacent but not a direct cross-reference. Not a contradiction, just slightly less precise than it could be.
