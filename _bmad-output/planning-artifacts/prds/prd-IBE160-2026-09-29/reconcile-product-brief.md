# Input Reconciliation: product-brief.md → prd.md / addendum.md

**Input checked:** `docs/product-brief.md`
**Checked against:** `prd.md` (primary) and `addendum.md` (deferred/Post-V1 content, counts as captured)
**Date:** 2026-10-01

## Method

Went through `product-brief.md` section by section (Executive Summary, Problem, Proposed Solution,
Intended Users, What Makes Jaunt Different, V1 Scope, Data and Important Decisions, Success Criteria,
Vision) and checked whether each distinct idea appears in substance in `prd.md` or `addendum.md`.
Only material gaps — dropped, flattened, or contradicted ideas — are listed below. Everything else
checked out as captured; those full mappings are in the "Confirmed captured" section at the end for
traceability, in case Codex wants to spot-check this reconciliation.

## Note on the brief's actual tone language

The task brief for this reconciliation mentioned checking for phrases like "playful and spontaneous."
That exact phrase does not appear anywhere in `docs/product-brief.md` as currently written — the
brief's tone is closer to plainspoken and matter-of-fact, with its one clear affective/brand beat being
the "have a Jaunt" framing in the Vision section and the honesty-over-fabrication stance running through
Proposed Solution / What Makes Jaunt Different / Success Criteria. This reconciliation checks against
what the brief actually contains, not the phrase as quoted in the task instructions.

## Gaps Found

### 1. Vision section: aspirational "have a Jaunt" framing narrowed to roadmap items

The brief's Vision section is built around a single emotional/brand payoff: "have a Jaunt" becoming
"an easy answer when someone has spare time, needs a break, wants to go outside, or wants to explore
somewhere unfamiliar. Tell Jaunt how much time you have, and it gives you something worth walking for."
That's the brief's entire long-term pitch — a cultural catchphrase, not a feature list.

PRD §1 Vision keeps the mechanics (a person enters time/topic, gets a loop with 2-5 stops) and names a
genuine long-term direction (destination-based routing, multi-area catalogue growth), but the "have a
Jaunt" aspirational framing itself does not appear in the Vision section's prose. It survives only as a
Glossary entry ("Jaunt (the outing) ... ('Have a Jaunt.')" — PRD line 58), which is a definitional
footnote, not the forward-looking brand statement the brief gave it. The PRD's Vision reads as a scope
roadmap; the brief's Vision reads as a brand ambition. Not contradicted, but narrowed in spirit — worth
deciding whether that catchphrase belongs back in PRD §1 or is intentionally left for `bmad-ux` /
marketing-adjacent work.

### 2. Success Metrics (§8) missing an explicit "viewable and followable from a phone" metric

The brief's Success Criteria list includes, as its own bullet: "The route can be viewed and followed
from a phone." This is listed at the same level as completion-time accuracy, stop relevance, and content
groundedness — i.e., the brief treats mobile usability as something to be tested and verified, not just
assumed.

PRD §8 Success Metrics (SM-1 through SM-6) has no corresponding metric. Mobile-first is present as a
platform constraint (§7: "Mobile-first web app... Built and tested mobile-first from the start"), but a
constraint is not the same as a tested success criterion. Every other brief Success Criteria bullet maps
cleanly to an SM; this one does not. Recommend either folding it into SM-1 explicitly or adding a short
SM-7.

### 3. "Estimated walking time plus an allowance for time at stops" — internal check only, not a user-facing FR

The brief lists this explicitly both as V1 scope ("Estimated walking time plus an allowance for time at
stops") and as a Data-out item ("Estimated walking and stop time"), implying the user sees this estimate,
not just that the system uses it internally to gate feasibility.

In the PRD, estimated time appears only as an internal Planner guarantee: FR-2's consequence is "The
Planner never proposes a Route whose Dwell-Time-inclusive total exceeds the entered time," and FR-5
similarly treats it as a feasibility check. FR-6 (display the route) and FR-7 (inspect stop content)
don't mention surfacing the estimated walk time / dwell allowance to the user on the review screen. It's
plausible this is assumed to be part of FR-6's map/list display, but it's not stated as a testable
consequence anywhere the way the other Data-out items are (FR-6 for stops-on-map, FR-7/FR-19 for content,
FR-20 for sourcing, FR-9 for the fallback). Worth confirming whether displaying the estimate is intended
and, if so, adding it as an explicit FR-6 consequence.

### 4. "Social features" named as out-of-scope in the brief, absent from the PRD entirely

The brief's V1 Scope section closes with: "User accounts, worldwide coverage, user-contributed places,
and social features are outside the initial scope" — four sibling exclusions named together.

PRD §5 Non-Goals explicitly addresses three of the four: full user accounts (listed), multi-language/
non-Sydney locations as "worldwide coverage" (listed), and community-contributed stops (listed, also in
addendum). "Social features" has no corresponding entry in §5 Non-Goals, §6.2 Out of Scope, or anywhere
in `addendum.md`. This isn't a contradiction — nothing in the PRD proposes social features — but it's an
explicit brief item that simply didn't get carried into the PRD's exclusion list, unlike its three
siblings. Likely fine to fold in as a one-line addition to §5 for completeness.

### 5. Minor: "notice something or do something" prompt distinction collapsed to generic "prompt"

The brief's Proposed Solution describes AI-generated content as potentially "a historical fact, an
architectural detail, information about public art, or a prompt encouraging the user to notice something
or do something in their surroundings" — i.e., two distinct prompt flavors (passive noticing vs. active
doing/task).

The PRD (Glossary "Stop" definition, FR-19, FR-7) consistently uses the flattened triad "story, fact, or
prompt" without preserving the notice-vs-do distinction. This is a small nuance loss, not a scope change
— content generation isn't restricted in a way that would prevent "do something" prompts — but the brief's
specific framing of two prompt sub-types doesn't show up anywhere, including `addendum.md`. Lowest-priority
of the five gaps; flagging for completeness rather than urgency.

## Confirmed Captured (no gap — for traceability)

- Core premise (time → purposeful walk, loop back to start by default) — PRD §1 Vision, FR-2, FR-5.
- Honesty-over-fabrication stance (brief's central differentiator) — FR-9, FR-19, §7 Source integrity,
  Non-Goals framing throughout.
- Primary user (local, unstructured time) / secondary user (visitor, unfamiliar area) — PRD §2.1 Jobs To
  Be Done, UJ-1/UJ-2.
- "What Makes Jaunt Different" (starts from the walk, not a destination; time covers whole outing, not
  just walking) — PRD §1 Vision paragraph 2.
- V1 Scope bullets (starting point, time selection, 4 topics + surprise-me, AI stop selection, loop
  route, map display, source-grounded content, source attribution, honest fallback) — FR-1, FR-2, FR-3,
  FR-5, FR-6, FR-7, FR-19, FR-20, FR-9, all tiered Must.
- Heritage topic addition beyond the brief's three — explicitly flagged as an assumption (PRD §10,
  Assumptions Index) rather than silently introduced.
- "Possible extensions, if time permits" (current location, point-to-point routes, audio read-aloud) —
  FR-14 (Could), Non-Goals + addendum (destination routing), addendum (audio narration).
- "Outside initial scope": accounts, worldwide coverage, user-contributed places — PRD §5 Non-Goals (see
  Gap 4 above for the one missing sibling, social features).
- Important development decisions (candidate collection/verification, AI relevance-matching, route/time
  checking, source-consistency of generated text) — reflected via Catalogue/Record Status concepts
  (Glossary), FR-3/FR-5, FR-2/FR-5, FR-19.
- No-account requirement — §7 Privacy, FR-17.
- Success Criteria: suitable result from inputs (SM-1, implied), completion-time accuracy (SM-2), real/
  relevant stops (SM-3), content-source consistency (SM-4), users understanding stop inclusion (SM-5),
  honest fallback (SM-6), "worth taking / would use again" (SM-1).
- Vision's longer-term ideas (more locations/topics/route types, audio, community contribution with
  verification) — PRD §1 (multi-area), addendum.md (audio, community contribution, "local legends").
