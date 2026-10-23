---
title: 'Preference-aware candidate discovery'
type: 'feature'
created: '2026-10-23'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '3372b87c5443bc10e740201130f61abc4b59d8df'
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The slider reaches selection, but nearest12 truncation hides relevant landmarks and evidence-only fame instructions impede recognition. User found maximum well-known returned only discovery-type places despite nearby landmarks.

**Approach:** AI chooses routing candidates from the wider eligible nearby pool using the continuous preference and general knowledge of recognisability. Python still owns all eligibility and walking feasibility. Preference is not a must: if preferred places cannot form a suitable walk, try ordinary nearby alternatives. User approved this direction and explicitly requested implementation; no repeated approval needed.

## Boundaries & Constraints

**Always:** keep existing2km area, ready/topic/coordinate/exclusion filters, mandatory retained replacement stops,12-place routing cap, exact preference0=well-known/1=hidden, and source-grounded stop stories. General knowledge can inform prominence only; unknown does not mean hidden. Strong preference should noticeably favour matching candidates/options where available, before filling time. Keep balanced/mixed choices possible, honest relevance rejection, technical503 errors and current single-stop replacement semantics.

**Never:** invent places/IDs, add permanent prominence labels/manual landmark lists, compute popularity in Python, require preference match to return a walk, expand expensive route search unboundedly, change frontend visuals or use paid calls for automated verification.

## I/O & Edge-Case Matrix

| Scenario | Expected result |
|---|---|
| Eligible pool larger than12 | AI sees pool before nearest cap; selects exactly available alternative slots; Python validates unique offered IDs and routes at most12 including mandatory retention |
| Pool fits available slots | Use all eligible records without a needless discovery call; final selection still uses preference |
| Strong preference with fitting landmarks outside nearest12 | Mocked AI-selected landmarks reach feasible route options; final guidance prioritises preference without forced test IDs |
| Preferred shortlist infeasible or AI judges none suitable | Try nearest eligible shortlist once when its membership differs; keep same preference; no recursion/unbounded recovery |
| Discovery unknown/duplicate/missing/extra IDs or provider failure | Bounded retry then technical error; fatal credential/quota errors propagate immediately, never honest no-match |
| Recovery still cannot return suitable walk | Existing honest fallback or retained-only/final-stop outcome, with reason limited to searched candidates, never a claim every place was checked |
| Too large candidate input | Explicit controlled service error, not silent nearest-only truncation |

</frozen-after-approval>

## Code Map

- planner.py: split collection of eligible nearby pool from nearest12 shortlist; preserve shortlist_candidates existing default contract for current callers/tests. plan_route orchestrates preference discovery, then existing bounded matrix/combination/AI-selection helper, then at most one nearest recovery. Keep replacement retained order/content rules and provider exceptions. Reuse code rather than duplicate the route-selection body.
- ai.py: add candidate-ID selection using existing provider helper/auth/model, a separate structured schema/system instruction and validation. Allow internal helper optional schema/system arguments without breaking existing callers/mocks. Update final selection prompts to permit general knowledge for recognisability only and favour preference fit over budget use. Content grounding prompts remain unchanged.
- tests/test_planner.py, tests/test_ai.py, tests/test_app.py: cover pool/ID validation, recovery, hard constraints, API technical outcomes and full real orchestrator with mocked providers. Existing tests that exercise large pools must mock discovery explicitly to prevent network. No framework/dependency.

## Tasks & Acceptance

- [x] planner.py — collect wider eligible pool; reserve retained slots; orchestrate discovery and bounded feasibility recovery.
- [x] ai.py — separate candidate schema/instructions/provider call, ID validation and bounded retry; revise final prominence guidance without weakening content grounding.
- [x] tests — cover all matrix rows, exact preference, unknown != hidden, absent landmarks still yield feasible nonpreferred walk, and rejection/retention invariants.
- [x] Process docs — reconcile AD-4/epic/context/spec with approved wider discovery, record cost bounds and test limitations; restart test server(s) for new backend.

**Acceptance:**
- Given a topic, when discovering candidates, then nonmatching/rejected places never reach AI alternatives; Wild spans topics.
- Given a landmark outside nearest12 but in eligible pool, when AI selects it, then it reaches final feasible options without increasing matrix cap.
- Given no suitable preferred walk, when nearest recovery is feasible, then the app returns that walk instead of rejecting solely for preference mismatch.
- Given replacement, when either attempt runs, then every retained stop survives, exclusions remain hard and final-stop behaviour is unchanged.

## Implementation Notes

No unresolved product question; user approved flexible preference and implementation. Technical policy: maximum200 eligible alternatives; compact descriptions(max320 excerpt characters,120 name,160 title), JSON prompt bounded100000 characters. Exceeding limits is a service limitation, not geographic infeasibility. These explicit pilot limits replace silent truncation and require later batching for larger areas. Keep real IDs intact. Discovery gets at most2 attempts (one retry); existing final-selection retry bound unchanged. Use all records if the pool fits12 minus retention. Skip discovery when alternatives fit and ordinary pool size<=4 (all2..4 subsets fit the15-option menu), or replacement alternatives fit (each retained+one option fits). For ordinary pools of5..12, ask AI to order all IDs, preserving every eligible record but enabling preference prefixes; otherwise the15-option menu can still crowd out a two-landmark walk. This necessary ordering call supersedes the earlier blanket small-pool skip policy. Nearest fallback runs only after honest no-combo/none_suitable/retained-only, never on technical errors; skip identical membership. Recovery still reserves retained slots. Report failure scoped to candidates checked, not exhaustive whole-area search. Existing candidate-radius and route computation unchanged. AI discovery IDs must be ordered best preference match first, not just an unordered set. Preserve that AI order in routing shortlist. The feasible option menu must include feasible leading-prefix combinations (sizes2 through existing max7) from that AI-ranked shortlist before coverage/budget fill, so a short landmark-focused walk is actually offered rather than only long mixed options. Keep AD-7 per-stop coverage and total menu cap15; prefix coverage reduces the remaining coverage burden. Enable prefix diversity for discovery-selected lists without altering ordinary legacy menu callers. No Python prominence/category calculation. Candidate prompt must provide Sydney pilot/location context (start coordinates or place coordinates) so generic names are not mistaken for places elsewhere. Additional AI call and occasional second matrix increase cost/latency; do not assert measured timings without live evidence. Current pilot has99–108 Wild alternatives; no paid calls needed to validate orchestration.

## Verification

Run full Python unittest and native Node suites, JS syntax/diff checks. Mock routing and AI boundaries; inspect actual prompt IDs/menu and recovery outcomes, not only mocked final responses. Prove every matrix row executes. Inspect real catalogue eligibility of user examples(Bank Hotel, I Have A Dream, Enmore Theatre; St Peters station, Cragos Flour Mills) without forced labels. Record real pool/prompt sizes and call bounds; live model judgement remains unverified until user testing. Main and baseline branches remain untouched; no push/deploy. Parent handles logging/docs/server restart; implementation agent changes production/tests only and reports checks.

## Implementation evidence before independent review

Production discovery and bounded recovery implemented;301 Python and37 native Node tests pass per implementation run. Parent independently exercised real Newtown catalogue through real discovery→planner→final prompt with mocked AI/routing:105 eligible candidates,45620-character discovery input, Enmore Theatre outside nearest12 entered routing, and a two-stop Bank+Enmore option was offered and selected within a simulated budget. This is an orchestration check with simulated walking times/AI, not live prominence judgement or outdoor route validation. All provider calls mocked.

## Spec Change Log

2026-10-23 direct verification found that ordinary pools of5..12 can still have more than15 feasible combinations, crowding out short landmark-focused walks if discovery is skipped. Clarified nonfrozen technical policy: rank all IDs in these pools (drop none), skip only pools<=4 or fitting replacement alternatives, and preserve preference prefixes. KEEP wider-pool eligibility, bounded provider/matrix calls, soft fallback, strict IDs and all retention/exclusion rules. No product decision or frozen intent changed; this is a necessary ordering call, not needless discovery.

## Review Triage Log

All three independent layers completed. Edge hunter returned no findings. Each finding triaged separately:

1. Blind — **low, patch:** nearest recovery dropped first shortlist final-selection attempts/log, hiding work in developer diagnostics. Aggregate both attempts and label shortlist source when recovery occurs.
2. Blind — **false:** replacement prefix allegedly omits shorter valid retained+alternative combinations. Replacement requires every retained stop plus exactlyONE new stop, so with six retained stops only a seven-stop candidate is valid; its prefix includes strongest first alternative. No multi-alternative replacement introduced.
3. Blind — **low, patch:** city-only context lacks candidate coordinates requested in technical contract. Include existing catalogue coordinates in compact discovery records; no client coordinates trusted.
4. Blind — **low, patch:** malformed-ID retry lacks error feedback. Add concise feedback for the one retry while respecting input bounds and response contract.
5. Blind — **low, patch:** discovery/recovery scenarios lack exact endpoint/Balanced/intermediate coverage and explicit ordinary alternatives acceptance. Parameterize real mocked-boundary orchestration over0/.5/1/.37; tests do not claim model quality.
6. Blind — **low, patch:** exclusion propagation untested through both discovery and recovery. Add inspected input/matrix/menu/final-result regression preserving retained IDs.
7. Blind — **false as completion defect:** tasks intentionally remain unchecked until parent's acceptance/matrix audit and server restart, not on implementation-agent report alone. Finalization checks them after evidence passes; live evaluation remains separate.
8. Verification reviewer — **medium, patch:** candidate schema/system override unverified at real HTTP request construction. Add real discover_candidates→_call_openai test with requests.post mocked; assert discovery schema/system body and valid returned IDs while existing selection default remains tested.

Parent found an additional five-place menu omission; nonfrozen policy clarification is in Spec Change Log. Rank all IDs where necessary to preserve preference prefixes rather than add production labels or grow menu/matrix caps.

## Completion verification

After review fixes, parent ran305 Python tests and37 Node tests; all pass, along with node --check and git diff --check. Matrix audit: discovery ID validation/limits/provider transport tests; ordinary and replacement recovery/no-combo/rejection tests; real orchestrator preference0/.5/1/.37; inspected exclusion/retention through both attempts; identical-membership skip and technical nonrecovery; five-place ranked-all/menu coverage test; final-stop/missing-retained regressions in existing suite. Input location coordinates and bounded feedback verified. Prefix option coverage remains within15 and routing within12.

Parent's real-catalogue mocked-boundary check confirmed105 eligible Newtown-station Wild candidates and Enmore outside nearest12 entering a feasible short Bank+Enmore option with simulated walking times. Final compact candidate input including coordinates measured51269 characters, below100000; this is character size, not a token/cost benchmark. No paid calls. One discovery stage(two attempts maximum), at most two matrices and final selection chains; small ordinary<=4 and fitting replacement pools skip discovery. No claim of live qualitative success before user testing. No new issue deferred; existing global request-budget/latency work remains separate, and the new stage can increase latency.

Both own test processes restarted to load backend changes: local5056 and password-protected gateway5057. Gateway credentials/original expiry preserved. Old tunnel timed out and is being reconnected; current URL/session recorded in AI-discussions.md. No app UI changes or catalogue labels. Story1.9 remains review awaiting user's live quality check, not accepted on mocked evidence alone.
