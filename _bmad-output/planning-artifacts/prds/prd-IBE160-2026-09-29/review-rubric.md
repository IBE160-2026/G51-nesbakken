# PRD Quality Review — Jaunt V1 PRD (prd-IBE160-2026-09-29)

## Overall verdict

This PRD holds up well: it has a genuine thesis (time-budget-as-first-class-input, honest fallback over fabricated routes), features and success metrics that trace back to it, and unusually disciplined brownfield bookkeeping — the existing-vs-missing claims per Feature (§4.1–4.6) check out against the actual codebase and `architecture-plan.md`. The main risk is concentrated in a cluster of Should-tier FRs (FR-4, FR-11, FR-13, FR-17, FR-18) whose core mechanism is explicitly left open, which is honest but means `bmad-create-epics-and-stories` cannot fully story those out yet, and one unflagged scope narrowing relative to `product-brief.md`'s original multi-suburb V1 area. Nothing here is a blocker; the PRD's own Open Questions list already tracks most of the gaps.

## Decision-readiness — strong

Real decisions are stated as decisions, not softened into "considerations." The strongest example is the geographic-expansion call in `addendum.md` ("Geographic expansion" section): it names the rejected options (Nice/Oslo/Molde demonstration, live/runtime POI discovery via Google Places/Foursquare/Overpass), gives the specific reasons each was rejected (thin/paywalled source text, Store norske leksikon's lookup-only API, Overpass reliability limits, non-English ingestion risk against "the remaining course timeline"), and states the resulting decision plainly: "V1's FR-21 stretch goal targets a second *Sydney* area only... rather than attempting a Nice/Oslo/Molde demonstration." That is a trade-off with what was given up named explicitly, not smoothed over.

§9's 12 Open Questions are genuinely open, not rhetorical-with-answer-attached — e.g. OQ-11 ("Are terse OSM-tag-sourced excerpts... actually sufficient input... to produce something worth reading") states context (flagged in `architecture-plan.md` as "expected-but-not-yet-tested") without pretending to answer it. Counter-metrics SM-C1/SM-C2 (§8) are a real decision-readiness signal too: SM-C1 explicitly warns against optimizing time-budget usage alone, citing a documented failure mode ("technically feasible but only 15-minute-used," Sprint 3) and a measured 20–30% optimism gap in the routing provider's estimates (`ai-development-log.md`, Sprint 4).

### Findings
- **low** No `[NOTE FOR PM]` callouts anywhere in the document — the rubric expects these at real tensions. The PRD substitutes inline `**Open:**` markers inside FRs plus the consolidated §9 list, which functionally covers much of the same ground, so this is a convention gap rather than a missing-information gap. *Fix:* none required; note for consistency if this PRD template is reused.

## Substance over theater — strong

Personas: two (Jarrod, Steve), each tagged against the FRs they drive ("Realizes UJ-1" / "Realizes UJ-2" on every FR) — not persona theater. NFRs in §7 are specific, not boilerplate: "no server-side location storage" (not "secure"), a named test count ("167/167... newer than `architecture-plan.md`'s documented 155/155"), and a concretely scoped extensibility constraint ("keep language and Pilot Area boundary as configuration, not inline literals"). The Vision (§1) is specific to this product's mechanics (time budget as a first-class input covering "walking and stopping both," preferring an honest "that doesn't quite work" over a manufactured route) rather than a swappable generic statement. No findings — this dimension doesn't need them.

## Strategic coherence — strong

The thesis is explicit in §1 and the features follow from it rather than from "what's easy first": FR-9 (honest fallback) and FR-19 (grounded-or-decline content generation) are both direct expressions of "it would rather say 'that doesn't quite work' than manufacture a route." Success Metrics validate the thesis rather than measuring raw activity — SM-1 ("worth taking," "would consider using again") and SM-5 ("can articulate why each Stop was included, without prompting") test experience quality and trust, not DAU/MAU-style proxies. Counter-metrics are present and well-targeted (see Decision-readiness above). MVP scope reads as an "experience" shape (quality of one complete journey) consistently across Must/Should/Could tiers in §6.1. No findings.

## Done-ness clarity — adequate

Most Must-tier FRs are genuinely testable: FR-1 ("A tap outside the Pilot Area is rejected with a clear message, not silently accepted"), FR-8 ("No walk begins without an explicit approval action"), FR-9 (fallback "suggests a concrete alternative... not just a bare failure") all give an engineer a clear pass/fail condition. No instances of unqualified vague language like "handles gracefully" or "user-friendly" were found — where the PRD is soft (e.g. FR-19's "sufficiently grounded"), it explicitly owns the softness rather than hiding it ("not a claim that an LLM can be guaranteed never to produce unsupported content").

The dimension drops to adequate because a real cluster of FRs leaves the actual mechanism undecided, not just a UI-polish detail: FR-4's ranking signal for "well-known vs. lesser-known" is undecided (Open Question 3), FR-11's replacement-selection logic is undecided (Open Question 2), FR-13's and FR-17's UI mechanism/retention behavior are undecided (Open Questions 7, 8), and FR-18's engagement-state weighting is undecided (Open Question 9). Each is honestly flagged, but an engineer — or `bmad-create-epics-and-stories` — cannot yet write a acceptance-testable story for any of these five FRs as currently stated; they need another pass after UX/architecture resolve the open items. Separately, SM-2's "within a reasonable margin" (§8) has no number — it's explicitly TBD, which is honest, but it means this success metric can't drive a go/no-go decision yet.

### Findings
- **medium** FR-4's done-ness is incomplete on both axes that matter (ranking signal, UI form) — both pushed to Open Questions 1 and 3 (§4.1, §9). Acceptable for a Should-tier item deferred to `bmad-ux`, but downstream story creation cannot act on FR-4 until these resolve. *Fix:* no PRD change needed now; flag as a blocking dependency for `bmad-ux`/`bmad-architecture` before FR-4 is storied.
- **low** FR-11, FR-13, FR-17, FR-18 each carry an unresolved mechanism/weighting element (Open Questions 2, 8, 7, 9 respectively) — individually minor and honestly labeled, but as a cluster they mean roughly a third of the Should-tier feature set isn't story-ready. *Fix:* consider grouping these as an explicit "pending UX/architecture input" list in §6 so the gap is visible at a glance rather than only discoverable by cross-referencing §9.
- **low** SM-2 (§8) has no numeric threshold ("exact threshold TBD after real-world testing") — honestly flagged but currently unusable as an acceptance gate. *Fix:* set a provisional number now (even a wide one) so SM-2 can be tested before "real-world testing" produces the real threshold.

## Scope honesty — strong

§5 Non-Goals does real work — each item has reasoning, not just a label (e.g. destination-based routing is deferred because it needs "an endpoint constraint to the combination search," not because it's low-value — "The user considers this an important long-term Jaunt use case," preserved in Vision/addendum). `[ASSUMPTION: ...]` tags round-trip cleanly: both inline assumptions (FR-2's time-range/dwell-time carryover, FR-3's heritage-as-first-class-Topic) are indexed verbatim in §10, and no extra index entries exist without an inline source. FR-21 is honestly tiered as "stretch goal... never allowed to delay the Newtown end-to-end flow" rather than smuggled in as a Must.

One narrowing is not flagged anywhere in the PRD or its Assumptions Index: `docs/product-brief.md` (§"V1 Scope", confirmed by direct read) names the V1 test area as "a defined inner-Sydney test area covering the CBD and nearby neighbourhoods... including Chippendale, Redfern, Surry Hills, Glebe, Erskineville, and Newtown" — six suburbs. The PRD's §1 Vision instead states "V1 is proven in one pilot area — Newtown," and treats Surry Hills (one of the brief's original six) as a not-guaranteed §4.6/FR-21 *stretch goal* for a "second" pilot area. This divergence was already settled by the time the PRD was written (`architecture-plan.md` confirms Sprint 1 ran only against Newtown), so it isn't a live decision the PRD is ducking — but the PRD cites `product-brief.md` in §0 as "the approved product story" it builds on, and nowhere notes that the single-pilot-area framing is narrower than what that approved story actually scoped.

### Findings
- **medium** Unflagged scope narrowing from `product-brief.md`'s six-suburb V1 test area to Newtown-only, with one of the original six (Surry Hills) downgraded to a stretch goal (§1 Vision; §4.6/FR-21). Not a build risk (already implemented this way since Sprint 1), but it's a traceability gap against the PRD's own cited source of truth. *Fix:* add a one-line `[ASSUMPTION]` or note in §1/§10 acknowledging that Newtown-only is a narrowing from `product-brief.md`'s original multi-suburb scope, settled during early implementation rather than decided in this PRD round.

Open-items density (12 Open Questions + 2 Assumptions = 14 callouts) is high in absolute terms but appropriately calibrated: this is a chain-top PRD explicitly handing UI-level decisions to `bmad-ux` (§0, §9 OQ-1), not a green-light-to-build document, so a high count here is the right shape rather than a red flag.

## Downstream usability — strong

Glossary (§3) is present and its 11 terms are used consistently in the FRs that depend on them (Record Status's `ready`/`limited`/`rejected` in FR-5/FR-9/FR-19; Shortlist/Option Menu/Route used identically throughout §4.2). FR IDs (FR-1–FR-21) and UJ IDs (UJ-1, UJ-2) are contiguous with no gaps or duplicates; cross-references (e.g. FR-16 → FR-19, FR-19 → FR-20, OQ references → §9 entries) all resolve to real targets I could locate. UJs each carry a named protagonist with inline context (Jarrod/Steve), no floating UJs.

### Findings
- **low** Glossary drift: §3 defines `Opened/Engaged` and `Visited/Completed` with a slash, but FR-17's consequences list uses `Proposed / Opened-Engaged / Visited-Completed` with a hyphen, while FR-18 reverts to the slash form. *Fix:* standardize on one separator (slash, matching the Glossary) throughout §4.4.
- **low** Success Metric IDs are presented out of ascending order: §8's Primary group lists SM-1, SM-2, SM-3, SM-7 (skipping to 7), then Secondary lists SM-4, SM-5, SM-6. The full set (SM-1–SM-7, plus SM-C1/C2) is contiguous and unique overall, but a reader scanning top-to-bottom may think SM-4–6 are missing until reaching the Secondary group. *Fix:* either renumber so Primary/Secondary groups are each internally ascending, or add a one-line note that IDs are grouped by priority, not sequence.

## Shape fit — strong

This is a reasonable journey-led shape for a solo-developer, launch-lite course project: two named-protagonist UJs (not four-plus persona theater) feeding a capability-grouped Features section, with UI-level specifics correctly deferred to `bmad-ux` rather than decided here (§0: "the 'Jaunt character' concept and the open UI-form questions in §8 belong there").

Brownfield accuracy — spot-checked directly against the codebase and `architecture-plan.md`, not just taken on faith: the NSW Heritage MapServer WAF claim (FR-21, Non-Goals) matches `architecture-plan.md`'s Sprint 6 account verbatim ("returns HTTP 403 to any client identifying itself honestly as a script"); the English-only Wikipedia hardcode claim (§4.6, §7) matches `import_places.py`'s actual `WIKIPEDIA_SUMMARY_URL = "https://en.wikipedia.org/..."` and its `# Wikipedia (English only)` comment; the heritage-Topic-as-assumption claim (FR-3, §10) matches `product-brief.md`, which indeed names only "History, architecture, public art, and 'surprise me'" and not heritage; and the test-suite count (§7: "167/167... newer than `architecture-plan.md`'s documented 155/155") is corroborated — `architecture-plan.md` itself confirms 155/155 at Sprint 6, and a direct count of `def test_` across `tests/*.py` in the repo returns 168, consistent with the PRD's claimed 167 (off by one, immaterial). Existing-vs-missing framing per Feature (§4.1–4.6, e.g. "Existing (Sprint 2/3): starting-point selection... Missing: the actual time/topic input UI") is a disciplined, accurate pattern throughout. The one scope-narrowing gap noted under Scope Honesty is the only brownfield-accuracy blemish found.

No findings beyond the cross-reference already logged under Scope Honesty.

## Mechanical notes

- Glossary drift: `Opened/Engaged`/`Visited/Completed` (slash, §3) vs. `Opened-Engaged`/`Visited-Completed` (hyphen, FR-17) — see Downstream usability.
- SM IDs not presented in ascending order within §8 (Primary: 1, 2, 3, 7; Secondary: 4, 5, 6) — contiguous and unique overall, just non-sequential on the page — see Downstream usability.
- Assumptions Index (§10) round-trips cleanly: both inline `[ASSUMPTION]` tags (FR-2, FR-3) are indexed, and no index entries lack an inline source.
- FR IDs (1–21) and UJ IDs (1–2) are contiguous with no gaps or duplicates found.
- §5 Non-Goals achieves the rubric's intended function (explicit, reasoned omissions) without using the literal `[NON-GOAL for MVP]` bracket-tag convention — a style difference, not a defect.
- No `[NOTE FOR PM]` tags appear anywhere in the document — see Decision-readiness finding.
