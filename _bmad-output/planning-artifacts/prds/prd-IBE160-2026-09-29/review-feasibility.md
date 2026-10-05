---
title: Jaunt V1 PRD — Adversarial Feasibility Review
status: draft
created: 2026-10-01
reviewed-by: Claude (adversarial review pass)
scope: Realism of §6.1 Must-tier against remaining timeline, Sprints 7-8 not started, and "meaningful AI" course requirement
---

# PRD Feasibility Review — Findings

Reviewed: `prd.md` (2026-09-29, updated 2026-10-01), `addendum.md`, `docs/architecture-plan.md` (ground truth for what's built: Sprints 1-6 complete, Sprints 7-9 not started).

Context used throughout: today is 2026-10-01; deadline is mid-November 2026 (~6-6.5 weeks); the developer is solo, part-time on this project (concurrently writing a thesis); `architecture-plan.md`'s own schedule already grew from an estimated 9-10 weeks to 11-12 weeks for the full Sprint 1-9 plan after only two sprint insertions (Sprints 5 and 6), which is evidence that this project's actual velocity has consistently run behind its own estimates.

---

## F1 — [CRITICAL] FR-19's "checked process" is written so that doing nothing beyond existing manual practice still satisfies it

**Location:** §4.5 FR-19, consequence bullets 2 and 3; §9 Open Question 10.

FR-19's opening paragraph reads as a real commitment: "a checked process, not a claim that an LLM can be guaranteed never to produce unsupported content... have a way to check generated content against its source and fall back when a check fails, rather than relying on the model's good behavior alone." Its second consequence bullet describes concrete runtime behavior: "If generation is attempted... and the result cannot be checked against its Source Excerpt as sufficiently grounded, the system falls back... rather than presenting unchecked content to the user." Read alone, this commits to building an automated per-request grounding check integrated into the generation pipeline — a real engineering task (some form of entailment/similarity check or a second verification LLM call, plus retry/exclude/flag-for-review logic).

But the very next bullet walks this back to the status quo: "Spot-checking generated content against its Source Excerpt (existing manual practice from Sprint 5/6) continues as the V1 baseline check; a more systematic/automated grounding check is an open question (see Open Question 10), not assumed here." And Open Question 10 explicitly leaves unresolved "is a more systematic or automated check... worth building for V1, or does manual spot-checking... remain sufficient."

This is an internal contradiction, not just an open question: bullet 2 is written as a testable, systemic consequence ("the system falls back"), which is exactly the kind of sentence a Should/Could item earns its own line for, yet bullet 3 permits satisfying Must-tier FR-19 with precisely the same manual, developer-eyeballing-samples practice already used in Sprints 5-6 for catalogue QA — a different thing (reviewing imported place *records*, not AI-generated *prose*) dressed up with the same name. A student could legitimately claim "FR-19 done" having built zero new verification code. Given §4.5 bills this FR as "the most direct expression of the course's 'must actually use AI' requirement," an examiner asking "show me the check-and-fallback mechanism" could get the answer "I read through some outputs by hand," which is a materially weaker claim than the FR's own prose implies.

**Recommendation for the student:** decide now, explicitly, whether FR-19's Must-tier bar is (a) manual spot-check only, or (b) a built automated check — don't let Sprint 7 implementation pressure decide it implicitly. If (a), rewrite FR-19's second consequence bullet so it doesn't promise system-level fallback behavior that won't exist. If (b), budget real hours for it now, because it doesn't currently appear in any sprint's task list (see F2).

---

## F2 — [CRITICAL] No sprint in the ground-truth plan sizes the Trip Setup / Route Review frontend that most Must-tier FRs depend on

**Location:** `architecture-plan.md` Sprints 2, 7, 8, 9; PRD §0 ("the still-missing user-facing flow"), §4.1, §4.2.

Checking what each planned sprint actually covers:
- Sprint 2 ("Minimal end-to-end web flow"): map + click-to-start-point + showing nearby catalogue stops. Explicitly "No AI, no time-budget logic yet."
- Sprint 7: `ai.py` part 2 — backend content generation only. "Testing focus includes spot-checking generated text against its source."
- Sprint 8: rerun importers against the full boundary (not required for V1 per the PRD — Newtown alone suffices), real route geometry, routing error/timeout handling, attribution in the UI, and the real-world walking test.
- Sprint 9 (stretch): geolocation, point-to-point routing, typed-address geocoding, read-aloud.

Nowhere in this list is there a line item for building: the time/topic input UI (FR-2, FR-3 — PRD §4.1 explicitly calls this "Missing"), the Route Review screen (map + expandable stop list + total-time display + per-stop detail view with source citation — FR-6, FR-7), the approve action (FR-8), or the honest-fallback UI (FR-9). This is the majority of what a user actually interacts with, and it is new work on top of Sprint 2's bare map-click plumbing. The PRD's own document-purpose section (§0) acknowledges "frontend wiring" as still-missing work distinct from "AI content generation," but no document — not the PRD, not `architecture-plan.md` — assigns it a sprint number, a time estimate, or even a named task. It is present only as scattered consequence bullets inside FR-5 through FR-9.

This means a non-trivial, unestimated chunk of Must-tier work is currently invisible in the plan — not merely under-tiered the way the task brief hypothesized for FR-19, but absent from scheduling entirely.

---

## F3 — [HIGH] Remaining-time math doesn't obviously close, and the PRD's own tiering doesn't flag the compounding risk

**Location:** whole-document pattern; most visibly §6.1 Must list, §9 Open Question 11, and `architecture-plan.md`'s Sprint 7/8 descriptions and schedule note ("now closer to 11-12 weeks").

From 2026-10-01 to mid-November is roughly 6-6.5 weeks, part-time, alongside a concurrent thesis. In that window the Must-tier list requires, at minimum: (a) the unscoped frontend build (F2), (b) Sprint 7's content-generation prompt engineering, tested against source material the architecture plan itself flags as a real unknown ("Known limitations... OSM-tag-sourced content is terse... Expected to be sufficient... but not yet tested," repeated in PRD §9 Open Question 11), and (c) Sprint 8's route-geometry integration, attribution UI, and a real-world walking test that requires physically walking Newtown routes and comparing estimated-vs-actual time — an activity with elapsed-calendar-time cost (weather, scheduling, possibly repeat walks if estimates are off) that doesn't compress just because more hours are worked.

`architecture-plan.md`'s own estimate already grew 20-30% (9-10 weeks → 11-12 weeks) after only two sprint insertions during Sprints 5-6 — i.e., this specific project has a demonstrated track record of its own estimates being optimistic. The PRD's §6.1 Should-tier ordering note ("pursued once Musts are working, roughly in this order if time is short") acknowledges schedule pressure for the Should tier, but nothing in §6.1 or §9 names the compounding risk across F1+F2+F3 together as a single surfaced risk — each is only visible piecemeal, if at all.

---

## F4 — [MEDIUM] The strongest "meaningful AI" argument is the least proven; the weakest is already built

**Location:** §4.5 intro; §9 Open Question 11; `architecture-plan.md` "Deriving a feasible option menu" section.

AI does two jobs in this system: (1) pick one option from a Python-pre-filtered, pre-validated, already-same-topic, already-feasibility-ranked menu (built, Sprint 4), and (2) turn a stored source excerpt into short prose (not built, Sprint 7). Job (1) is architecturally honest about AI's role (no routing arithmetic, Python is the feasibility authority — a genuinely good design choice for the "AI shouldn't do what determinism can do better" argument), but by the time AI sees the menu, most of the interesting narrowing has already happened in Python; an examiner could reasonably ask whether a simple scoring heuristic could replace this step, and the answer ("judging which specific combination makes the most interesting walk, not just which is feasible") is defensible but thin unless the student is ready to argue it explicitly.

Job (2) — turning terse, sometimes fragmentary source text (the architecture plan's own example: "By Jasmine Sarin, 2021") into something "worth reading" — is the more clearly AI-dependent, harder-to-fake task, and the one most likely to persuade an examiner that AI is functionally load-bearing rather than decorative. But it is entirely unbuilt, and the PRD itself (Open Question 11) flags that whether the source material is even sufficient for this is untested. If Sprint 7 underperforms or slips, the delivered product's best "meaningful AI" evidence weakens considerably, leaving mostly the thinner, already-built selection step to carry the argument.

---

## F5 — [MEDIUM] FR-6's "full walking path" quietly depends on route-geometry work that doesn't exist yet, and isn't broken out against FR-6 in §6.1

**Location:** §4.2 FR-6 ("The map shows the full walking path..."); `architecture-plan.md` line ~154 ("`plan_route()` only has point-to-point durations from the ORS matrix, not actual polylines"); Sprint 8 description.

Per `architecture-plan.md`, the planner currently has only point-to-point durations from the ORS distance matrix, not actual route polylines — geometry is explicitly named as Sprint 8 work. FR-6 is Must-tier and plainly requires showing "the full walking path" on the map, which needs that geometry (fetching an ORS directions response and rendering it, not just placing markers at stop coordinates). This dependency is real but is folded anonymously into "Sprint 8" alongside attribution UI and the real-world test, rather than being named as its own cost against a specific Must-tier FR in §6.1.

---

## F6 — [MEDIUM] Primary success metrics presuppose testing work that no FR commits to actually doing

**Location:** §8 SM-1, SM-2, SM-7 (marked "Primary"); §4 (no corresponding FR).

SM-1 ("testers rate the completed walk as worth taking"), SM-2 (estimated vs. actual time, requiring the real-world walking test), and SM-7 (testers complete the full flow on a phone) all require actually running tester sessions and/or the real-world walking test. No FR in §4 lists "conduct a real-world test" or "run tester sessions" as a deliverable. It is therefore possible for every Must-tier FR to reach "code complete" without the validation activity the PRD's own primary success criteria depend on ever being scheduled as time. Worth an explicit line item (even a one-sentence NFR or a Should-tier FR) so it isn't assumed to happen for free at the end.

---

## F7 — [LOW, positive calibration] FR-21 is correctly and safely tiered

**Location:** §4.6, §6.1 Should item 6.

FR-21 (second pilot area) is explicitly scoped as a stretch goal, explicitly never allowed to delay the Newtown end-to-end flow, and its own feature-specific NFR is phased sensibly (config refactor first, then a second-area run). No feasibility issue here — included for contrast with the Must-tier findings above.

---

## F8 — [LOW, positive calibration] The PRD is generally honest about risk elsewhere

**Location:** §9 (12 Open Questions), §10 (Assumptions Index), §8 SM-C1/SM-C2 (acknowledging ORS's 20-30% optimistic time estimates and the still-outstanding real-world test).

The PRD's general practice of flagging assumptions and open questions is good and should be preserved — the issues above are specific gaps (particularly F1's internal contradiction and F2's unscoped frontend work), not a general critique of the document's honesty.

---

# Summary

| Severity | Count |
|---|---|
| Critical | 2 (F1, F2) |
| High | 1 (F3) |
| Medium | 3 (F4, F5, F6) |
| Low | 2 (F7, F8 — positive calibration notes) |

**Bottom line:** The Must-tier list is achievable in principle but the PRD's tiering understates two things: (1) FR-19's "checked process" language is internally inconsistent — it can be satisfied by doing nothing more than existing manual spot-checking, which undercuts the course's "meaningfully incorporate AI" claim if that's how it's built, and (2) the entire user-facing frontend (Trip Setup + Route Review) that most Must-tier FRs depend on has no assigned sprint, time estimate, or named task anywhere in the planning documents. Combined with a demonstrated history of this project's own schedule estimates running long, and an untested content-generation risk (Open Question 11) sitting on the most defensible "meaningful AI" argument, the remaining ~6.5 weeks carries materially more risk than §6.1's tiering surfaces.
