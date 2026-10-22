---
name: Jaunt
description: How Jaunt behaves — the Trip Setup → Route Review → Active Walking → End of Walk flow, Jarrod's behavioral role, and the Must-tier baseline a Should/Could feature is allowed to degrade to.
status: final
sources:
  - _bmad-output/planning-artifacts/prds/prd-IBE160-2026-09-29/prd.md
  - _bmad-output/planning-artifacts/prds/prd-IBE160-2026-09-29/addendum.md
created: 2026-10-02
updated: 2026-10-18
---

> Distilled from `.memlog.md` (the canonical decision record for this UX pass) and the promoted `mockups/` (`flow-01-setup.html`, `flow-02-generate.html`, `flow-03-walk.html`, `key-must-tier-skeleton.html`, plus `key-route-review-quiet-streets-v2.html` — a map-styling direction reference, not a flow, cited mainly by `DESIGN.md`). `DESIGN.md` is the visual-identity sibling — this file cross-references its tokens by name (`{path.to.token}`) rather than restating colors, type sizes, or component styling. Both spines win on conflict with any mock. Several items below are flagged **Open** rather than resolved — they are genuinely undecided in the sources, not guessed at.

## Foundation

Mobile-first web app, phone browser primary, desktop secondary (per `prd.md` §7 Platform — built and tested mobile-first from the start, not retrofitted). No tablet or desktop layout exists in any source; this spine, like `DESIGN.md`, describes the phone-viewport experience only.

No named UI system — every component (buttons, chips, sheets, the map) is bespoke, built from the tokens in `DESIGN.md`'s frontmatter. No dark mode exists (not designed, not requested). No account, login, or profile anywhere in V1 — Favourites and Visit History are local-device state only (`prd.md` §7 Privacy). The product is proven in one bounded Pilot Area, Newtown (inner Sydney); nothing in this spine assumes a second area, though the IA and components are written so one could be swapped in without new screens.

The experience is a single forward-moving funnel, not a hub-and-spoke app: Trip Setup → Route Review → Active Walking → End of Walk, once per Jaunt. There is no persistent tab bar or bottom nav — the only "home" a user returns to is a fresh Trip Setup, reached either by finishing a walk or by the honest fallback's way back.

A cross-cutting behavioral rule, not scoped to one screen: **Jarrod's on-screen prominence scales inversely with how populated the screen already is.** Sparse screens (an empty map, a single wheel-picker, the topic-at-rest screen) give him a large, central role (150–168px, per `DESIGN.md` Layout & Spacing); content-dense screens (the stop list sheet, the walking map with markers and a drawer) shrink him to a small supporting presence or drop him to just a 30px head-marker. This rule recurs enough times in the decision record (memlog #62, #91, Layout & Spacing in `DESIGN.md`) to treat as load-bearing, not a one-off — see Component Patterns below.

## Information Architecture

| Surface | Reached from | Purpose |
|---|---|---|
| Launch splash | Cold app open (once per session) | Full wordmark reveal → looping idle animation; establishes brand, no input yet |
| Starting point | Splash ends / app relaunch | Choose where the walk begins |
| Available time | Starting point → Continue | 5-min-increment wheel, 30–120 min |
| Topic — at rest | Time → Continue | Two co-equal entry paths: Choose Topic or Wild Jaunt, plus the optional preference control |
| Choose Topic page | "Choose Topic" tap | Topic scroller + repeated preference control; Wild Jaunt is not offered here |
| Confirmation sheet | Wild Jaunt tap (straight from "at rest"), or the topic page's "Start my [Topic] Jaunt" pill | Last chance to back out before generation starts |
| Loading | Confirmation sheet confirmed | "Concocting your jaunt…", Jarrod walking through generic scenery |
| Route Review | Loading succeeds | Map + stop-list sheet; approve, Re-Jaunt, or remove a stop |
| Honest fallback | Loading fails to find a feasible Route | Replaces Route Review entirely for this request; always offers a way back |
| Active walking | Route Review → "Start my jaunt" | Map, stop markers, live position (if granted), hamburger access |
| Off-canvas drawer | Hamburger tap, during walking | Currently holds only "End Jaunt"; reserved for unbuilt Post-V1 rows |
| Stop info overlay | Tap a stop (map marker or list row), pre-walk or during | Story/fact/content + explicit Visited checkbox |
| End-of-walk catch-up | "End Jaunt" | Retroactively mark any stop Visited before summarizing |
| Summary | Catch-up → "Create summary of visited stops" | AI recap + photos + per-stop favourite, grounded only in Visited stops |
| Jaunt complete (no-summary) | Catch-up → "or end without a summary", or a zero-Visited walk | Honest, deliberately calm ending with no AI content |
| Visited-stops recap (no AI) | A failed AI summary generation, with at least one Visited stop | Revised 2026-10-18: not the same screen as the no-summary ending — a plain list of the actually-Visited stops, each still carrying its own favourite-heart target, so favouriting never depends on AI succeeding |

There is no tab bar, drawer-as-primary-nav, or bottom sheet that persists across surfaces — each sheet/overlay belongs to exactly one surface and is dismissed (swipe-down) before the next one appears. The one recurring exception is the stop-list bottom sheet pattern itself, which is the same component on both Route Review and (collapsed) during Active Walking.

→ Composition reference: `mockups/flow-01-setup.html` (splash → setup → topic → confirm), `mockups/flow-02-generate.html` (loading → review → fallback), `mockups/flow-03-walk.html` (walking → stop info → end of walk), `mockups/key-must-tier-skeleton.html` (Must-tier-only baseline, all Should/Could removed), `mockups/key-route-review-quiet-streets-v2.html` (map-styling direction reference — see `DESIGN.md`'s Map component for the full spec this mock renders). Spine wins on conflict.

## Voice and Tone

Microcopy only — brand posture (playful, spontaneous, curious, a little quirky, easy to understand) lives in `DESIGN.md` Brand & Style.

| Do | Don't |
|---|---|
| "Where are we jaunting from?" | "Enter your starting location" |
| "How much time have you got?" | "Select trip duration" |
| "A topic in mind, or feeling spontaneous?" | "Choose a category" |
| "Ready for your History Jaunt?" | "Confirm route parameters" |
| "Concocting your jaunt…" | "Loading…" / a progress percentage |
| "Jarrod was unable to make a 30-minute History Jaunt from here." | "No results found" / "Error: infeasible request" |
| "Here's what might work instead:" | A list framed as the user having failed/asked wrong |
| "Catch up on anything you forgot to check off." | "You have 2 incomplete tasks" |
| "What a jaunt! Here's everywhere you stopped." | "Trip Report" / "Session Summary" |
| Topic-specific copy where it's free ("Start my History Jaunt", not "Start my Jaunt") | Generic copy where a real variable (topic, time) is already known |
| Plain, honest language for failure (fallback, no-summary ending) | Red/alarm-coded error language — no error color exists in `DESIGN.md`, and none should be invented casually |

**Draft, not yet locked:** the "Jaunt complete" heading and its "Nice walk!" acknowledgment line (end-of-walk, no-summary state) are explicitly unconfirmed placeholder copy per the render notes in `flow-03-walk.html` — treat as a strong direction, not settled wording, until the user confirms it.

**Character naming note carried from `DESIGN.md`:** the character is "Jarrod" in all user-facing copy and in this document. Internal asset filenames and CSS class names still say "jaunty" — that's implementation detail, never user-facing.

## Component Patterns

Behavioral rules only — visual specs (fills, radii, shadows) live in `DESIGN.md.Components`.

| Component | Behavioral rule |
|---|---|
| Jarrod ({character-jarrod}) | Prominence scales inversely with screen content density (see Foundation). Appears at transitions (greetings, loading, confirmation, fallback, end-of-walk) — never a persistent, constantly-talking presence, and never takes over a screen that already has its own content to show. |
| Speech bubble ({components.bubble}) | Always paired with a Jarrod pose; never a standalone tooltip/toast. One short line, always bold (per `DESIGN.md` typography — bubbles never carry regular-weight text). |
| Equal-weight button pair ({components.button-secondary-fill} + {components.button-primary} variants) | Reserved for genuinely co-equal choices only: "Choose Topic" / "Wild Jaunt" on the topic-at-rest screen, "Re-Jaunt" / "Start my jaunt" on Route Review. Never used for a single dominant action. |
| Full-width primary vs. compact pill ({components.button-primary} vs. pill variant) | Full-width = exactly one dominant action on the screen (Continue, the confirmation sheet's confirm button). Compact auto-width pill = a short-label single action that must not stretch edge-to-edge ("Start my History Jaunt", "Back to start"). This exact confusion has recurred as a real, caught-twice bug (`DESIGN.md` Components) — treat the two as distinct components a developer must choose deliberately, not interchangeable variants. |
| Chip / topic pill / named-start chip ({components.chip}) | Horizontally scrollable row, hidden scrollbar. Selected state is a fill inversion, not a border or checkmark addition. |
| Bottom sheet ({components.bottom-sheet}) | One structural pattern reused for: the Route Review stop list, the pre-generation confirmation, and the end-of-walk catch-up list. Dismiss by swiping down. A taller, near-full-screen variant is the stop-info overlay. |
| Preference control (landmark ↔ hidden-gem slider) | Lives beneath both top-level buttons on the topic-at-rest screen, applies regardless of which path is taken, defaults to Balanced if untouched. Repeats on the Choose-Topic page for visibility. **Deliberately absent from the Wild Jaunt path's own confirmation** — Wild Jaunt stays a true one-tap action with no slider gate, even though the control's own default (Balanced) still applies to it. |
| Stop row (list item) | **Superseded 2026-10-21 (Codex review caught this row going stale after the live amendment) — see `epics.md` UX-DR12 for the current, live design:** a numbered circle marker alongside a small place-type icon, not a photo-thumbnail in the row; a rights-cleared photo (FR-22, Should) shows in the stop's own content overlay instead. A trailing "✕" remove affordance appears only where FR-11 (remove/replace) is in scope. |
| Map stop marker (Should-tier, photo-aware) | **Superseded 2026-10-21 (same correction) — see `epics.md` UX-DR13 for the current, live design:** a white-plate circle carrying the order number plus a small place-type icon (picked from the stop's name first, its topic otherwise); a rights-cleared photo shows in the overlay, not as the map pin. Jarrod does not appear as an individual stop marker anywhere on the map - that part is unchanged. |
| Live position marker (Should-tier, FR-14) | Jarrod's head alone (a real ~30px crop at the alpha-channel gap between head and torso) — not a generic dot, not his full figure. When this layer is absent (GPS off/denied/not attempted), the map shows no marker at all rather than a broken or placeholder one — see State Patterns. **Added 2026-10-18:** a small directional arrow appears on the head only while `GeolocationCoordinates.heading` is a real, non-null value (the browser's own GPS-course-over-ground signal, reusing FR-14's existing permission — no separate compass/`DeviceOrientationEvent` permission is requested). Heading is `null`/`NaN` whenever the device is stationary or can't determine it, which is most of the time a user pauses to read a stop's content — the arrow simply disappears and the head shows alone in that case, never a guessed or stale direction. |
| Off-canvas drawer | Hamburger-triggered, full-height white panel from the left (~78% of screen width) over a dimmed scrim. Currently holds only "End Jaunt." **Reserved but explicitly empty** for two named Post-V1 rows ("in case of rain" weather-rerouting, mid-walk re-route) — do not add rows for features that don't exist yet. Its exact placement is tentative (see Open Items below), not a locked decision. |
| Visited checkbox badge | A small bordered square + "Visited" label, floating top-right on the stop-info overlay, visually and interactionally separate from the content below it. Opening/reading a stop's story never toggles this — it requires its own explicit tap, every time. |
| Catch-up row | A checkbox-style row per stop, pre-checked if marked Visited during the walk, tappable to catch up retroactively. A retroactive catch-up tap is still an explicit Visited/Completed action (not inferred), per `prd.md` FR-13. |

## State Patterns

| State | Surface | Treatment |
|---|---|---|
| Cold launch | Splash | **Corrected 2026-10-21 (user's explicit choice, after seeing the full reveal phase render as "a square photo" popping up first):** goes straight to the looping hillside-scene + wordmark idle animation - the separate full-wordmark-reveal phase this row used to describe was removed, not just shortened. Auto-advances after ~2.6s (tap/key to skip); plays once per page load, not shown again until a fresh load. |
| Starting point outside Pilot Area | Starting point | **Corrected 2026-10-18 (Codex review caught this row was stale):** any tapped point is accepted — there is no separate rejection. A start too far from any real Stop is handled once the planning request runs, via the honest fallback (`prd.md` FR-1, revised 2026-10-18). This row previously described a rejection that was removed from the PRD and epics.md but missed here. |
| Topic — at rest vs. Choose Topic page | Topic | "At rest" shows both Choose Topic and Wild Jaunt plus the preference control. The Choose Topic page is a genuine separate screen (not an in-place expand) and **does not show Wild Jaunt** — committing to a topic removes the instant-surprise option from that screen. |
| Confirmation sheet | Over whichever screen triggered it | Dimmed background, a happy Jarrod pose, one primary confirm action, a quieter secondary "wait, let me change that" dismiss link back to the triggering screen. |
| Route Review loaded | Route Review | Map (full available height) + stop-list sheet; "Re-Jaunt" and "Start my jaunt" sit as an equal-prominence pair, never one buried beneath the other. |
| Stop removed | Route Review | **Amended by user 2026-10-22:** seek a replacement while keeping other stops. If none is suitable, keep the verified shorter Jaunt and show an inline message at the removed row position. One stop may remain; disable Remove there but keep Replace. If the final stop is rejected and cannot be replaced, show sad Jarrod. Revalidate route time/geometry before approval. |
| Re-Jaunt requested | Route Review | Returns a different feasible Route when one exists in the Option Menu; falls back to the Honest Fallback message if none exists (`prd.md` FR-10). |
| Honest fallback — with alternative | Replaces Route Review | Jarrod's dedicated sad pose + one trimmed sentence naming the request that failed + concrete alternative chips. **Alternatives must offer more time, never less** — reducing the time budget can never turn an infeasible request feasible under the current Planner model; this was a corrected logic error (`prd.md` FR-9). A different-topic suggestion is valid in either direction. |
| Honest fallback — no alternative | Replaces Route Review | Sad pose alone, honest message, still always a way back to adjust inputs — never a dead end, even with nothing specific to offer. |
| Technical/service failure | Replaces Route Review | Must read as distinct from the honest "no suitable walk" message — these are different situations and should never share copy (`prd.md` FR-9). Not yet designed as its own screen in any mock; flagged as a gap, not resolved. |
| Active walking — live position on (Should) | Active walking | Jarrod's head-only marker moves along the route in real time, subject to explicit, revocable permission. |
| Active walking — no GPS (Must-tier fallback) | Active walking | A calm, non-alarming "Location off" pill replaces the marker; the static map, route, and stop markers are otherwise identical. This is explicitly **not an error state** — it is the Must-tier baseline every walk must degrade to cleanly, whether GPS was denied, deferred, or never attempted. |
| Drawer open | Active walking | White panel + scrim over the dimmed screen; closing returns to exactly the walking state it was opened from. |
| Stop info overlay open | Over whichever screen triggered it | Near-full-screen, swipe-down to dismiss; Visited checkbox starts unchecked unless already marked. |
| End-of-walk catch-up | End of walk | Each stop shows checked/unchecked; unchecked rows carry a soft "forgot?" hint, not a demand. |
| Summary generated (Should) | End of walk | Jarrod reappears (same loading-pattern reuse as "Concocting your jaunt…") while generating. Includes only stops holding Visited/Completed state — a stop that was only Opened/Engaged or merely Proposed is never described as visited (`prd.md` FR-16). Each visited stop gets a favourite-heart tap target. |
| Jaunt complete — no summary | End of walk | Reached via the catch-up screen's quiet secondary link, or a walk with zero Visited stops. **Must look complete, not degraded** — no stripped-down summary layout, no missing-content placeholder; it is its own deliberately calm, finished-feeling screen. |
| Visited-stops recap (no AI) | End of walk | **Revised 2026-10-18:** a failed AI summary generation (with at least one Visited stop) no longer lands here — it gets its own plain, non-AI list of the Visited stops with favourite-heart targets intact, since the user's real data (what they actually visited) shouldn't be hidden by an AI-service hiccup. |
| "X min left" display during walking | Active walking | **Open, unresolved:** could mean time remaining from the original budget (simple arithmetic) or estimated time-to-finish from current position (needs real-time progress calculation the Planner doesn't yet do) — PRD Open Question 20. Do not assume either meaning is settled when building this. |
| Local Visit History retention | Background (no dedicated screen) | **Open, unresolved:** whether stored history/favourites ever expire, and whether there's any user-facing way to clear them, is undecided — PRD Open Question 7. No clear/reset control exists in any mock; don't assume history is permanent or that one isn't needed. |

## Scope Tiers & Graceful Degradation

A product-specific concern worth its own section: Jaunt has an explicit, separately-rendered **Must-tier-only skeleton** (`key-must-tier-skeleton.html`) showing the bare minimum complete product with every Should/Could feature genuinely absent — not just unstyled. Every Should/Could feature in this spine must be able to switch off cleanly back to that baseline; none of them may be load-bearing for a Must-tier flow to work end to end.

| Capability | Must (always present) | Should (real value, may be absent) | Could (not designed in detail) | Post-V1 (not in scope at all) |
|---|---|---|---|---|
| Starting point | Map-tap, named-start chips | One-shot "use my current location" (FR-24) | — | — |
| Topic | Fixed topic list + Wild Jaunt/"surprise me" | Landmark ↔ hidden-gem preference slider | — | — |
| Pre-generation step | — (goes straight to Loading) | Confirmation bottom sheet (a UX nicety, not an FR) | — | — |
| Route Review actions | Approve (one button), full stop list, total time shown | Re-Jaunt, remove/replace a stop, muted background amenities (FR-23) | — | — |
| Map styling | Plain grey-road map (close to default raster tiles, per PRD Open Question 19) | "Quiet Streets" illustrated treatment (buildings, bounded tree clusters, canal fills) | — | — |
| Walking position | Static map, stops visible, no position marker | Live GPS-following head marker (FR-14) | Automatic arrival notification (FR-15, depends on FR-14) | — |
| Stop content | Dismissible content overlay, source attribution, opening always optional | Explicit Visited checkbox, rights-cleared photos (FR-22) | — | — |
| End of walk | None required beyond the walk being walkable | Catch-up, AI summary, favourites, "Jaunt complete" honest ending | — | — |
| Repeat use | — | Local Visit History, Favourites, repeat-use route variety (FR-17/18) | — | — |
| Navigation chrome | — | Hamburger/off-canvas drawer with "End Jaunt" | — | Weather-rerouting, mid-walk re-route (reserved drawer rows only, not built) |

Character use scales down accordingly: in the Must-tier skeleton, Jarrod still appears for warmth at transitions, but more sparingly and smaller than in the fuller-vision mocks — the same prominence-scales-with-density rule, applied to a leaner set of screens.

## Interaction Primitives

- **Tap** is the primary action everywhere: map-tap to set a starting point, tap a chip/pill to select, tap a stop row or marker to open its content.
- **Horizontal swipe/scroll** on chip and pill rows (named starts, topic scroller) — hidden scrollbar, no visible paging dots.
- **Vertical swipe/scroll** on the time wheel-picker — 5-minute increments, the one large-numeral moment in the system (`{typography.display-time}`).
- **Swipe down to dismiss** is the consistent gesture for every sheet and overlay (stop-list sheet, confirmation sheet, catch-up sheet, stop-info overlay). No source mock pairs this with a visible, tappable close control except the Must-tier skeleton's stop overlay, which uses an explicit "✕" — this inconsistency is a real gap, flagged under Accessibility Floor below.
- **Two distinct, separately-scoped location permission moments:** a one-shot "use my current location" tap (FR-24, for starting point only) and continuous live tracking during the walk (FR-14). Neither is ever requested automatically or silently; both degrade cleanly to their non-GPS equivalent when denied.
- **Explicit affirmative taps, never inferred states:** marking a stop Visited (separate from opening its content), approving a Route (separate from merely reviewing it), and favouriting a stop (separate from it simply appearing in the summary).
- **Removing a stop** is a direct tap on its row's own "✕", not a swipe-to-delete gesture — distinct from the swipe-down-to-dismiss used for whole sheets.

**Never happens, by deliberate decision — not merely unbuilt:**
- Opening a stop's content never auto-marks it Visited.
- A missing photo never shows a placeholder/blank-image box — the text simply fills the row.
- A fallback or infeasible-request message never suggests less time as the fix.
- The honest fallback, and the no-summary "Jaunt complete" ending, are never dead ends — both always offer a way back or forward.
- Jarrod never appears as a hand-drawn/redrawn figure — every appearance in every mock is a real cropped region of the source character art (a hard rule in `DESIGN.md`, carried into behavior: this document assumes the same discipline applies to the shipped app's asset pipeline, not just the mocks).
- Live position tracking is never simulated from a non-GPS signal, and the continuous position stream is never sent to or stored on a server (`prd.md` §7 Privacy).

## Accessibility Floor

**Honest baseline, not a compliance claim:** no contrast check, no screen-reader (VoiceOver/TalkBack) pass, and no touch-target sizing audit has actually been run against any real screen in this project's history. Nothing below should be read as "verified" — it is the floor this product commits to meeting, stated so it can be checked later, not asserted as already true.

- **Touch targets:** every tappable control observed in the mocks (chips, pills, the Visited checkbox, the remove "✕", catch-up rows) should meet or exceed a ~44×44pt-equivalent target, consistent with the padding conventions already in `DESIGN.md.Components` — this is a commitment to hold components to, not a measurement that has been taken.
- **Contrast:** `DESIGN.md`'s ink-on-cream/surface palette (`{colors.ink}` on `{colors.cream}`/`{colors.surface}`) was chosen for a warm-but-legible register, but no WCAG contrast ratio has actually been calculated or tested for any text/background pairing in this system. This should be checked before shipping, not assumed from the palette alone.
- **State signaled by more than color:** selected chips/pills invert fill *and* carry the selected text itself (the label is still readable, not color-only); the Visited badge pairs a bordered checkbox shape with the word "Visited," not a color change alone; the honest fallback uses Jarrod's dedicated sad pose plus plain-language copy rather than a red/alert color treatment — `DESIGN.md` explicitly notes no error/destructive color has ever been established in this system, so nothing currently relies on color alone to signal a failure state.
- **Gesture-only dismissal is a real, flagged gap:** the stop-info overlay and most sheets rely on swipe-down with only a text label ("swipe down to dismiss") as a hint — no visible tap-target close control exists in the current mocks (the Must-tier skeleton's stop overlay is the one exception, using an explicit "✕"). This should be resolved toward always having a tappable alternative to the gesture, not just a visual label.
- **Permission prompts** (one-shot location, FR-24; continuous tracking, FR-14) rely on the browser's own native, presumably-accessible permission dialog — not a custom UI — but this has not been separately verified for this product.
- **Dynamic type / text scaling** has not been tested against any screen; several labels (e.g. the time-pill, compact pills) are sized to hug short text tightly, which may not gracefully accommodate a longer translated or larger-type string — worth testing before this is treated as settled.

## Key Flows

### Flow 1 — Vilde has an hour and wants a reason to leave the flat (UJ-1)

1. Vilde opens Jaunt. The splash plays once — wordmark reveal, then the looping hillside idle — and resolves straight into Trip Setup.
2. Starting point: she taps a point on the map near her flat (she could also have picked a named chip or used current-location, FR-24, but she already knows where she's starting).
3. Available time: the wheel-picker rests on 60 — she leaves it there.
4. Topic: Jarrod's bubble asks "A topic in mind, or feeling spontaneous?" She taps **Choose Topic**, lands on the separate topic page (Wild Jaunt no longer offered here by design), swipes to **History**, leaves the landmark/hidden-gem preference at Balanced, and taps "Start my History Jaunt."
5. The confirmation sheet rises: "Ready for your History Jaunt?" She confirms.
6. Loading: "Concocting your jaunt…" with Jarrod walking across the generic scenery.
7. Route Review: a 4-stop, 52-minute loop. She taps into St Stephen's Church to read its content before deciding (FR-7) — satisfied, she taps "Start my jaunt" rather than Re-Jaunt.
8. Active walking: live position is attempted and granted — Jarrod's head marker tracks her along Church St. She reaches St Stephen's Church (a photo-pin marker), taps it, reads the overlay, swipes it down without yet marking it visited — she wants to actually stand there first.
9. She walks on, taps the Visited checkbox once she's genuinely at the church, skips opening King St Terraces entirely (never required, FR-12), and detours into Mural Lane for its street art.
10. She opens the hamburger drawer and taps "End Jaunt."
11. Catch-up: St Stephen's and King St Terraces... — only St Stephen's was explicitly marked; Mural Lane and Camperdown Cemetery show as "forgot?" rows. She taps Mural Lane to catch it up retroactively (still an explicit Visited/Completed action, not inferred) but leaves Camperdown unchecked — she genuinely skipped it.
12. She taps "Create summary of visited stops." Jarrod reappears while it generates.
13. **Climax:** the summary shows St Stephen's and Mural Lane — never Camperdown, which she never confirmed — each with a short grounded recap. She taps the heart on Mural Lane, the stop that actually surprised her. That one tap is the whole payoff: next time, Jaunt favours places she hasn't seen, but lets this favourite resurface.

*Edge case, per PRD UJ-1: had her 60-minute History request been infeasible, step 6 would instead land on the honest fallback — Jarrod's sad pose, one honest sentence, and alternative chips offering more time or a different topic, never less time.*

### Flow 2 — Steve has 90 minutes before dinner with friends (UJ-2)

1. Steve opens Jaunt for the first time, in an unfamiliar neighbourhood, on a clock.
2. Starting point: rather than hunting for a landmark he doesn't know, he taps "Use my current location" (FR-24) — a one-shot position read, with its own explicit permission prompt, distinct from the continuous tracking he hasn't granted yet.
3. Available time: he dials the wheel to 90.
4. Topic: he doesn't know what's around, so he taps **Wild Jaunt** directly from the at-rest screen — one tap, no slider gate, straight to the confirmation sheet ("Ready for your Wild Jaunt?"). He confirms.
5. Loading, then Route Review: a mixed-topic loop. Being unfamiliar with the area, he'd lean toward well-known places over obscure ones (FR-4) — but since he's on Wild Jaunt's fast path, he leaves the preference at its Balanced default rather than detouring to adjust it. He opens two stops' content right there on the review screen before deciding anything.
6. He approves. This time location permission is denied (he doesn't want to burn battery before dinner) — the walking screen shows the calm "Location off" pill instead of a marker, same static route and photo-pin stops, no error framing anywhere.
7. He walks the loop, opens the two stops whose photo-pins caught his eye on the map, never opens the others, and reaches the end of the loop with time to spare.
8. He opens the hamburger drawer, taps "End Jaunt," glances at the catch-up screen — and, in a rush, taps the quiet secondary link: "or end without a summary."
9. **Climax:** he lands on "Jaunt complete" — a short, deliberately calm, deliberately complete-looking screen with no AI text, no photos, nothing pretending to be more than it is. He taps "Back to start" and closes the tab. No account was ever created; nothing persisted that he didn't want to keep.

*Edge case, per PRD UJ-2: had nothing suitable fit his 90-minute window, step 5 would instead be the honest fallback rather than a stretched, lower-quality route — Jaunt would rather say so than manufacture something weak.*
