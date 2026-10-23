# Preference-aware candidate discovery amendment —2026-10-23

## Approved direction

AI should favour landmark or hidden-gem choices before the nearest-place cap, within the selected topic; Wild spans topics. General knowledge may inform recognisability, while generated stories stay grounded. No manual production landmark list or Python popularity score. This supersedes the original companion's restriction against changing shortlisting/evidence-only prominence judgement. Earlier implementation remains a historical account of the initial wiring, not the complete amended design.

## Proposed implementation boundary

1. Python collects ready, coordinate-bearing, nonexcluded places within the existing2km area and selected topic. Retained replacement stops remain mandatory even if outside this alternative pool, as today.
2. AI receives bounded candidate descriptions, location context, exact preference and budget, and chooses IDs for available shortlist slots. Python validates membership, uniqueness and cardinality; it supplies all coordinates from the catalogue. AI neither creates places nor certifies walking time.
3. Python fetches the existing bounded duration matrix and enumerates feasible options. Final AI selection uses the same preference, with general-knowledge prominence judgement allowed. Existing exclusions/retention/content/fallback contracts remain.

## Cost and feasibility findings

Actual offline counts:159 ready records overall. Within2km, the named-start Wild pools contain99(Newtown Camperdown Park),105(Newtown station) and108(King St); architecture19, history27, public_art69–78. No paid calls made. Wider discovery can transmit roughly100 descriptions rather than12 and adds an AI round trip; it can increase latency and cost. Current30–45s target is not established for this revision. Token and wall-clock measurements must be recorded before presenting a new estimate.

The cap of12 routed places remains useful to bound matrix/search cost. A selected12-place shortlist is not proof that no route exists among the rest. Simply inserting one AI call then retaining the current global-looking honest fallback would create a misleading failure case.

## Technical design to settle before coding

- Bound input size without recreating nearest-only blindness; for the pilot, assess compact records for the whole eligible pool and measure actual serialized/token sizes. Define explicit limits before future catalogue expansion, not an unbounded prompt.
- Specify candidate response schema, retry cap and technical-failure handling. Do not silently ignore the slider on provider failure or accept hallucinated IDs.
- Define limited feasibility recovery if preferred candidates cannot form a route. Consider a deterministic nearby alternative pool/second routing attempt with accurate outcome copy; avoid claiming area-wide impossibility or silently discarding preference. This needs investigation before choosing an implementation policy.
- Replacement reserves retained stops first and selects only alternatives into remaining slots. Final-stop replacement remains exactly one new stop; Re-Jaunt exclusions apply before discovery.
- Inspect whether final option coverage offers meaningful alternatives rather than only high-stop-count mixtures; do not promise all-landmark routes based only on candidate inclusion.

## Verification and acceptance

Mocked tests must show a relevant offered landmark outside nearest12 can reach routing at strong landmark preference; mixed/hidden choices stay eligible at Balanced/opposite preferences; source category alone does not imply popularity; unknown names do not imply obscurity. Test invalid IDs, retry exhaustion, input bounds, no extra calls for empty/insufficient pools, retained/excluded invariants and limited-feasibility recovery. These prove mechanics only.

A controlled live comparison should use matched start/topic/time/exclusions and record pool, shortlisted IDs, feasible offered options and chosen result. Include Bank Hotel, mural and Enmore Theatre as user-expected landmark candidates, St Peters station and Cragos Flour Mills as discovery candidates when actually eligible. No forced labels or IDs. Live calls need user-authorised budget; no claim of meaningful endpoint contrast until evaluated.

## Implementation policy resolved after user clarification

User confirmed preference is not mandatory and requested implementation. The build contract spec-1-9-preference-aware-discovery.md now settles the earlier technical checklist: bounded200-alternative compact input/100000 characters, two discovery attempts at most, unchanged12-place routing cap, and one nearest-candidate recovery after honest lack of a suitable preferred walk. No nearest fallback on technical failure. Empty/small pools skip discovery. General knowledge is permitted for recognisability only, and unknown is not automatically hidden. Earlier checklist is retained as design history.
