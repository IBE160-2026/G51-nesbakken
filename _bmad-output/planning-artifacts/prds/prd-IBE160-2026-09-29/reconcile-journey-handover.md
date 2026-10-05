---
title: Journey Handover → PRD Reconciliation
status: findings
created: 2026-10-01
scope: Checks prd.md + addendum.md against journey-handover-source.md, excluding items already resolved by the confirmed PM/user follow-up conversation (identity-toggle resolution, un-bundling of arrival-notification/AI-summary/GPS, destination-routing/circular-finish merge, and Must/Should/Could/Future tiering in general).
---

# Reconciliation: Journey/Vision Handover vs. PRD + Addendum

## Method

Read the handover source section by section (§1 Overall vision, §2 Journey 1, §3 Journey 2, §4 Geographic expansion, §5 Additional features, §6 Important requirements/open decisions) and checked every concrete claim, caveat, and tonal note against `prd.md` and `addendum.md`. Confirmed absences with `grep -in` for key phrases across both files rather than relying on memory.

## Material gaps found

### 1. "Hybrid approach combining verified catalogue with automated discovery and enrichment" — the specific assessment asked for is missing, not just deferred

The handover makes this request twice, explicitly:

> "Please evaluate a hybrid approach combining the existing verified Newtown catalogue with automated discovery and enrichment for additional locations."

> "I'd particularly like BMAD to assess whether we can demonstrate this in at least one additional location during V1, rather than automatically postponing geographic expansion... please assess the feasibility and sequencing of automatic geographic expansion, rather than assuming that every feature beyond the existing Newtown implementation must wait until a later version."

`grep -in "automat|discovery"` across `prd.md` and `addendum.md` returns zero hits for "automated discovery" or "automatic discovery" in the sense the user meant (AI/pipeline discovering and enriching places in a *new* location without a hand-built catalogue). The only "automatic" hits are FR-15 ("automatic arrival notification") and an "automated grounding check" open question — unrelated.

What the PRD actually delivers instead (FR-21, §4.6) is: extend the *existing deterministic, same-language, Sydney-only* OSM/Wikipedia import pipeline to a second bounding box (Surry Hills). That demonstrates a second pilot area, but it is not the hybrid automated-discovery-and-enrichment architecture the user asked to have evaluated — it reuses the same catalogue-building approach, just pointed at new coordinates. True automated discovery (for non-Sydney, non-English locations like Oslo, Molde, Nice, using AI to find/validate places rather than running the same import scripts) is pushed to Non-Goals/addendum with no documented feasibility assessment, no sequencing discussion, and no stated reason why it wasn't viable for V1. The user's explicit "assess ... rather than assuming" framing suggests they wanted to see that reasoning, even if the conclusion was still "defer it" — that reasoning doesn't appear anywhere.

**Recommendation:** Either add a short explicit note (PRD §4.6 or addendum) stating that automated AI-based place discovery was considered and why it was judged infeasible/out of scope for V1 (e.g., reliability of AI-sourced facts without a verified catalogue, conflicting with FR-19's grounding guarantees), or flag this as a genuinely open question rather than silently substituting a narrower FR-21.

### 2. "The two audiences probably don't require separate interfaces" — architectural/UX framing note dropped

Handover §3: "The two audiences probably don't require separate interfaces. Their preferences should influence the selection of stops and **potentially the contextual information presented**."

This has two parts. The first (single shared interface, not two separate UIs/flows for locals vs. visitors) is never stated anywhere in `prd.md` or `addendum.md` — confirmed via grep, zero hits for "separate interface." The PRD's UJ-1/UJ-2 journeys read as parallel/identical flows, which is *consistent* with a single interface, but the explicit design principle ("don't build two interfaces") is never written down anywhere a future implementer (or `bmad-ux`) would see it.

The second part — that the landmark/hidden-gem preference should potentially affect not just *which* stops are chosen but **how they're presented** (the tone/framing of the content itself, not just stop selection) — is also absent. FR-4's consequences only describe the preference as influencing "which Stops the Option Menu favours." The idea that content/description style itself might vary by preference is lost.

**Recommendation:** Add a short note to FR-4 or §8 Open Questions capturing both: (a) single interface serving both personas is the working assumption, and (b) whether the preference should also affect content framing/tone, not only stop selection, is open.

### 3. "Playful and spontaneous" tone — lost entirely

Handover §1: "The experience should feel **playful and spontaneous**, with a Jaunt character guiding users through simple choices."

Confirmed via grep: neither "playful" nor "spontaneous" appears anywhere in `prd.md` or `addendum.md`. The Jaunt character itself is captured (addendum's "Jaunt character / guide concept" section, including the first-draft/eyes-on-mobile question), but the specific tonal direction for the *overall product feel* — which is a vision-level product decision, not merely a UX-detail — isn't recorded anywhere. Since the PRD explicitly routes "the Jaunt character concept" to `bmad-ux` (§0), there's a real risk this tonal intent never reaches that downstream document if it isn't written down somewhere first.

**Recommendation:** Add one line to PRD §1 Vision or the addendum's Jaunt character section preserving "playful and spontaneous" as the intended product feel, so it survives into UX work.

## Items checked and confirmed NOT gaps (verified present, not just assumed)

- Landmark vs. hidden-gem preference + "not merely obscure" caveat — present in FR-4 consequences almost verbatim.
- Arrival notification tied to the Jaunt character delivering it — captured verbatim in addendum's Jaunt character section.
- Nature/photography topic uncertainty ("unsure if this is limited") — captured faithfully in addendum + Non-Goals + Open Question 4, including the uncertainty itself (not resolved either way).
- Geographic candidate locations (Sydney/Nice/Oslo/Molde) and authoritative-source list (Wikipedia, Store norske leksikon, Visit Norway, heritage registers, explicit Reddit exclusion) — all present in addendum, verbatim level of detail preserved.
- Weather-rerouting, mid-walk changes, community contribution, local-legends persona, audio narration, free-text topic input, full accounts/V2-V3 — all present in Non-Goals and/or addendum with their nuances (e.g. local-legends clarification, weather trigger not needing a live API).
- Destination-based routing / circular-vs-chosen-finish merge, identity-toggle resolution, GPS/notification/AI-summary un-bundling, Must/Should/Could tiering — these are the confirmed follow-up revisions per task context; checked and consistent with the PRD, not flagged.

## Minor phrasing note (not a gap, informational only)

The handover's §6 line "however if we hit the requirements we can pause, push it and then continue developing it outside of the course" is paraphrased rather than quoted (PRD §0: "the student intends to continue developing Jaunt after the course"). The substance is preserved; flagging only because the task asked to watch for phrasing drift — this one is a faithful paraphrase, not a drift in meaning.
