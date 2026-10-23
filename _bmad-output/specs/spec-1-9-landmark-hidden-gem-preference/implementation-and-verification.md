# Implementation and verification plan

## Existing implementation

static/app.js stores trip.preference, validates it on recovery, synchronizes both sliders and converts the visual left-hidden/right-well-known direction into0=well-known,1=hidden. startRoutePlanning omits it from its request. app.py validates the other planning fields; planner.plan_route and ai.select_stops/build_prompt have no preference parameter. _build_ai_options includes id/name/topics/source_excerpt but lacks source_type/source_title. Reuse all these seams without a planner rewrite.

## Proposed changes

1. Add preference to the common frontend request so initial planning, retry, Re-Jaunt and replacement share the same value. Preserve existing saved-state recovery and current slider precision; do not quantize into categories.
2. Validate optional preference in app.py: absent defaults0.5; explicit JSON integer/float must be finite and within[0,1]; reject booleans, strings, null and out-of-range values before provider calls. Pass through planner to each AI attempt using backward-compatible optional arguments; preserve existing positional callers.
3. Add source_type and nullable source_title to each candidate in the option menu. Add the exact numeric preference and plain-language endpoint/balanced guidance to selection prompts. Explain that lesser-known does not mean low quality, source category is not popularity, weak evidence warrants caution, and preference never requires rejecting an otherwise suitable walk. Preserve existing selection schema and response validation.
4. Run existing Python and native Node suites plus targeted regressions. Verify keyboard/phone slider behaviour without redesigning it. Update status/logs after implementation, independent review and user walkthrough.

## Acceptance checks

- Both slider endpoints, Balanced and a noncentral value such as0.37 survive the actual request and prompt without category rounding; existing visual inversion remains correct.
- Omitted preference remains compatible; invalid explicit values produce400 with no AI/routing call.
- Every selection retry receives the same value and candidate metadata; ordinary and replacement feasible menus remain constrained exactly as before.
- Frontend retry, time adjustment, reload, Re-Jaunt and individual replacement preserve preference. Fresh trip retains the existing Balanced default.
- Prompt inspection verifies guidance and real candidate fields. Mocked selection tests verify integration only and are never presented as proof of model preference quality.
- Phone/keyboard check confirms synchronized sliders and no slider added to confirmation.

## Real candidate evaluation

| Intended comparison | Ready catalogue ID | Evidence caveat |
| --- | --- | --- |
| Landmark candidate: Bank Hotel | heritage/2420858 | Source supports prominent location and longstanding local association; no measured popularity. |
| Landmark candidate: I Have A Dream | node/6836072185 | Active excerpt only gives artists/year. Richer rejected duplicate perfect_match/16 is not reactivated or silently merged. |
| Lesser-known candidate: St Peters station | heritage/5012222 | Surviving early building/awning details provide discovery interest, not proof of obscurity. |
| Lesser-known candidate: Cragos Flour Mills | heritage/2030114 | Industrial/railway history provides discovery interest; public access is not established by this description. |

User accepted these four provisional candidates. No test labels enter the real catalogue or become AI input masquerading as sourced facts. Mixed comparison uses surprise_me because the mural is public_art while the other three are heritage topics. Choose start/time that offers relevant candidates; inspect actual shortlist/options before interpreting results. A candidate outside the nearest shortlist or feasible route cannot demonstrate preference. Do not enlarge the shortlist or force these IDs to obtain a desired result.

Controlled fixtures may supply clearly documented contrasting descriptions and feasible choices to test transport/prompt construction, including only-one-kind-feasible cases. Live evaluation, if authorised, compares endpoint and Balanced requests under the same feasible conditions, records offered/selected IDs and evidence, and reports variability. No required two-and-two quota or guarantee of endpoint-specific IDs. Newtown's limited variety and thin mural evidence can limit contrast; future approved sources can improve it without changing the selection boundary.
