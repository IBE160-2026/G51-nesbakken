---
name: Jaunt
description: Mobile-first walking companion that turns available time into a purposeful walk. Playful, spontaneous, a little quirky, led visually by Jarrod — a character built from the "JA" of the wordmark itself.
status: final
sources:
  - _bmad-output/planning-artifacts/prds/prd-IBE160-2026-09-29/prd.md
  - _bmad-output/planning-artifacts/prds/prd-IBE160-2026-09-29/addendum.md
created: 2026-10-02
updated: 2026-10-07
colors:
  forest: '#1E4A3A'
  sage: '#AFC29A'
  sage-light: '#CBDAB9'
  cream: '#F6F4EC'
  paper: '#FAFAF8'
  ink: '#16302A'
  ink-soft: '#5C6D64'
  ink-faint: '#8C9284'
  surface: '#FFFFFF'
  surface-muted: '#EDEAE2'
  sheet-handle: '#DDD8C8'
  road: '#EDEAE2'
  road-main: '#E3DED0'
  building-light: '#C7C4B6'
  building-dark: '#BDBAAC'
  tree-dark: '#5C7A52'
  tree-light: '#93AE80'
  water: '#A6C2C6'
  house-wall: '#DCE6D0'
  logo-field: '#FDFEFA'
typography:
  display-time:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    fontSize: 27px
    fontWeight: '800'
    note: 'the one large numeral moment in the system — the selected value in the time wheel-picker'
  heading:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    fontSize: 15px
    fontWeight: '700'
  bubble:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    fontSize: 13.5px
    fontWeight: '700'
  stop-name:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    fontSize: 12.5px
    fontWeight: '700'
  stop-name-detail:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    fontSize: 17px
    fontWeight: '700'
  body:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    fontSize: 12.5px
    fontWeight: '400'
    lineHeight: '1.6'
  label-caps:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    fontSize: 10.5px
    fontWeight: '700'
    letterSpacing: 0.04em
    note: 'always uppercase — section labels like "Or pick a spot", "Swipe to pick one"'
  button:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    fontSize: 13px
    fontWeight: '700'
  caption:
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif'
    fontSize: 11px
    fontWeight: '600'
rounded:
  xs: 9px
  sm: 11px
  DEFAULT: 14px
  md: 16px
  lg: 18px
  xl: 22px
  '2xl': 24px
  full: 28px
spacing:
  xs: 6px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 20px
  '2xl': 24px
components:
  button-primary:
    background: '{colors.forest}'
    foreground: '{colors.cream}'
    radius: '{rounded.lg}'
    width: '100%'
    padding: '13-14px vertical, 8px horizontal'
  button-pill:
    background: '{colors.forest}'
    foreground: '{colors.cream}'
    radius: '{rounded.full}'
    width: 'auto'
    padding: '12px 24px'
  button-secondary-fill:
    background: '{colors.sage}'
    foreground: '{colors.ink}'
    radius: '{rounded.lg}'
  button-outline:
    background: 'transparent'
    foreground: '{colors.forest}'
    border: '2px solid {colors.forest}'
    radius: '{rounded.lg}'
  chip:
    background: '{colors.surface-muted}'
    foreground: '{colors.ink}'
    radius: '{rounded.md}'
    selectedBackground: '{colors.forest}'
    selectedForeground: '{colors.cream}'
  badge:
    background: '{colors.surface-muted}'
    foreground: '{colors.ink-soft}'
    radius: '{rounded.DEFAULT}'
  bubble:
    background: '{colors.surface}'
    foreground: '{colors.ink}'
    radius: '{rounded.DEFAULT}'
    shadow: '0 6px 16px -8px rgba(22,48,42,0.18)'
  bottom-sheet:
    background: '{colors.surface}'
    radius: '{rounded.xl} {rounded.xl} 0 0'
    shadow: '0 -10px 30px rgba(22,48,42,0.18)'
    handle: '{colors.sheet-handle}'
  map-route:
    stroke: '{colors.forest}'
    strokeWidth: '6.5-7px'
  map-stop-marker:
    fill: '{colors.forest}'
    ring: '{colors.sage}'
    radius: '11px'
  map-amenity-point:
    fill: '{colors.building-light}'
    opacity: '0.7'
    radius: '5px'
  map-building:
    fillAlternateA: '{colors.building-light}'
    fillAlternateB: '{colors.building-dark}'
  map-park:
    fill: '{colors.sage}'
    treeClusterDark: '{colors.tree-dark}'
    treeClusterLight: '{colors.tree-light}'
    clip: 'real park/cemetery polygon only — clusters never exceed the true boundary'
  character-jarrod:
    bodyColor: '{colors.forest}'
    sourceAsset: 'imports/jaunty-mascot-sheet-v2-eyes-transparent.png'
    sadAsset: 'imports/jaunty-sad-transparent.png'
    rule: 'always a cropped region of real source art; never hand-drawn or regenerated from a text description'
---

## Brand & Style

Jaunt turns a person's available time into a purposeful walk. The product's own words for its voice, from the person building it: **playful, spontaneous, curious, a little quirky, but still really easy to understand.** Not corporate, not a cold utilitarian maps-app feel — the opposite of what a destination-first navigation tool usually looks like, because Jaunt starts from the walk itself, not a place you've already decided to go.

That posture shows up visually in three deliberate choices. First, the first screen is not a map-heavy control panel — Trip Setup is a short, guided sequence (starting point → time → topic) with a character asking plain questions, not a form to fill out. Second, the character — **Jarrod** — is literally built from the product's own wordmark: he's the "JA" of "JAUNT," given a walking pose (round head, J-shaped torso, A-shaped legs mid-stride). He isn't a separate mascot bolted onto the brand; he *is* the brand's own lettering, animated. Third, the map itself (the "Quiet Streets" direction) is deliberately muted and flat-filled rather than either a default slick maps-app look or an overly illustrated storybook scene — real street geometry and real park boundaries, styled quietly enough that the route and stops stay the obvious focus.

A small naming note, since it appears in a few historical files and discussions: the character was named "Jaunty" through most of this project's design history and renamed to **Jarrod** on 2026-10-03 — a deliberate choice, not a typo. Internal asset filenames and CSS class names (`jaunty-*`) were intentionally left unchanged when this happened; they're implementation detail, not user-facing copy.

Jaunt is mobile-first by platform constraint (phone browser primary, desktop secondary) and by product logic — it's used while actually walking.

## Colors

The palette comes directly from the real wordmark artwork (`imports/jaunt-logo.png`) and has been held consistently across every rendered mock since.

- **Forest (`#1E4A3A`)** is the primary brand color — the dark forest green of the "JAUNT" lettering and of Jarrod's body. It carries every primary action (full-width buttons, the confirm/start CTA, the compact pill actions), the route line on the map, selected states (selected topic pill, selected time value), and Jarrod's own silhouette. This is a deliberate, settled choice: when two candidate route-line greens were compared during map-direction exploration, the user explicitly preferred this darker, more muted brand green over a brighter, more saturated alternative (`#1E8A52`, since discarded) — Jaunt's green should read as the brand's own color, not a generic "map route" green.
- **Sage (`#AFC29A`)** is the secondary brand green, pulled from the logo's rolling-hill scenery. Used for: the ring around stop markers and the current-position marker, secondary-filled buttons (paired beside a primary action, e.g. the landmark/hidden-gem track), and real park/green-space polygons on the map (it is literally the park fill color, not just a UI accent).
- **Cream (`#F6F4EC`)** is the primary screen/canvas background — warm, not stark white, and it's also the map's base canvas color. **Paper (`#FAFAF8`)** is a very slightly cooler near-white used behind the phone-frame mockups themselves; it has not yet been used as an actual in-app surface, so treat it as a close cousin of Cream rather than a second confirmed app background.
- **Warm Ink (`#16302A`)** is the primary text color — not pure black, kept warm to match the paper/cream surfaces. **Ink-soft (`#5C6D64`)** is secondary text (captions, meta lines, recap pills). **Ink-faint (`#8C9284`)** is tertiary text (street labels, "walk time" sublines, the smallest supporting captions).
- **Surface White (`#FFFFFF`)** is used for elevated/floating UI — bottom sheets, cards, speech bubbles, the stop-info overlay — distinguishing them from the cream map/background plane beneath. **Surface-muted (`#EDEAE2`)** is the fill for unselected chips, pills, recap badges, and picker-row highlights.
- **Map-specific supporting tones**, all real and all in active use (not decorative extras): **Road (`#EDEAE2`)** for minor streets, **Road-main (`#E3DED0`)** for arterials/diagonals, two alternating **muted greys for building texture** (`#C7C4B6` / `#BDBAAC`) so real urban density reads clearly without competing with the route, two **tree-cluster greens** (`#5C7A52` dark, `#93AE80` light) clipped to real park polygons, **Water (`#A6C2C6`)** for canals, and **House-wall (`#DCE6D0`)** used in the logo's own hillside-house illustration and reused in the loading-screen scenery.

**Not yet decided / not evidenced anywhere in the sources:** a dark-mode palette (no dark variant of any color exists in any mock or decision record), and any dedicated error/destructive color. FR-1's "tap outside pilot area is rejected with a clear message" and FR-9's honest-fallback state are both specified behaviorally but have no red/warning color anywhere in the actual mock CSS — the honest-fallback state uses Jarrod's dedicated sad pose plus plain ink-colored text, not a red/alert treatment. If an explicit error color is ever needed, it should be decided deliberately rather than assumed to be a standard red.

## Typography

Every rendered mock, without exception, uses the same native system-font stack (`-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif`) — no custom typeface has been loaded anywhere in this project's history. Given how consistently this appears across every independently-rendered file, it reads as a real, settled choice (a native, lightweight, non-precious feel that matches the "easy to understand" tone) rather than an oversight — but it has not been explicitly discussed/confirmed as a typography decision in its own right, so treat it as the de facto default rather than a locked brand typeface commitment.

The roles actually distinguished by size/weight in practice:

- **`display-time`** (27px/800) — the one large-numeral moment in the whole system: the selected value in the available-time wheel-picker ("60 min"). Nothing else in the product uses a number this large.
- **`heading`** (15px/700) — screen/page titles ("Pick a topic").
- **`bubble`** (13.5px/700) — Jarrod's speech-bubble text and other short, friendly prompts. Always bold; bubbles never carry regular-weight body text.
- **`stop-name`** (12.5px/700) in list/row contexts, scaling up to **`stop-name-detail`** (17px/700) on the full stop-info overlay.
- **`body`** (12.5px/400, line-height 1.6) — the only regular-weight, non-bold text role, reserved for actual stop content/story paragraphs. Everything else in the interface is bold.
- **`label-caps`** (10.5px/700, uppercase, 0.04em tracking) — small section labels ("Or pick a spot", "Swipe to pick one", "Landmarks or hidden gems?").
- **`button`** (13px/700) — all button/CTA labels.
- **`caption`** (11px/600) — meta lines, walk-time sublines, source attribution.

A notable, consistent pattern: almost nothing in the UI is regular-weight. Bold (700, occasionally 800) is the default for nearly every text role; only stop-content body paragraphs drop to regular weight. This reinforces the "friendly and direct, not quiet/editorial" register — the opposite instinct from a hushed, serif-driven editorial system.

## Layout & Spacing

Jaunt is single-column, mobile-first, phone-viewport-first in every sense — there is no evidence anywhere in the sources of a desktop or tablet layout being designed; desktop is explicitly secondary per the PRD, and no mock addresses it. Screen content generally sits within roughly 16–26px of horizontal padding from the device edge, tightening to ~16–18px for map-overlay content and opening up to ~20–26px for centered, sparse screens (e.g. the time picker).

Two structural patterns recur throughout and should be treated as the system's real layout grammar:

1. **Map-dominant, sheet-secondary.** On both Route Review and the active-walking screen, the map fills the full available vertical space behind the header, and content (the stop list, the catch-up list) lives in a bottom sheet that slides up over it — never a second map-sized panel competing for space.
2. **Jarrod's prominence scales inversely with screen content density.** On sparse screens (the opening starting-point/time/topic screens), Jarrod appears large and central (150–168px). As a screen's own content grows denser (deeper into Trip Setup, during the walk), he shrinks to a small supporting presence (64–110px) or, during active walking, to just his head as a 30px live-position marker. This is a real, repeatedly-applied visual rule, not a one-off — worth preserving as new screens are designed.

**Not yet decided:** no formal, named spacing scale (e.g. a 4px/8px base-unit system with token names like `spacing.2`) has actually been established. The spacing values above are the real, recurring increments pulled directly from the mock CSS (padding and gaps cluster strongly around 6/8/12/16/20/24px), but no one has deliberately named or ratified this as "the" scale — treat the frontmatter `spacing` tokens as an accurate *description* of current practice, not a pre-existing locked system.

## Elevation & Depth

Jaunt uses shadow for exactly one purpose: to lift floating UI (sheets, cards, bubbles, floating pills) visually off the flat map/background plane beneath it. The map itself, and anything drawn flat on the cream canvas, never has a shadow — elevation is reserved entirely for chrome that visually floats above content, not for decoration.

Every shadow in the system is tinted with the ink color (`rgba(22,48,42, …)`), never pure black — a small, consistent detail that keeps shadows feeling warm rather than clinical, matching the cream/ink palette rather than a neutral grey-black system.

Observed shadow treatments, by how far a thing floats:
- **Bubbles / small floating badges**: `0 6px 16px -8px rgba(22,48,42,0.18–0.25)` — a soft, close lift.
- **Bottom sheets** (stop list, confirmation sheet, catch-up): `0 -10px 30px rgba(22,48,42,0.18)` — a stronger upward-cast shadow, since sheets visually detach further from the map plane below them.
- **Floating pill actions** (e.g. "View list" sitting directly over the map): `0 10px 24px -8px rgba(22,48,42,0.45)` — the strongest, most prominent shadow in the system, appropriate to an element that's a standalone floating control rather than a sheet edge.

## Shapes

Corner radius increases with how much an element "floats" off the map/background plane — small, grounded elements (thumbnails, badges, numbered stop markers) stay tight and small-radius; elevated, detached surfaces (cards, sheets) get the largest radii; and fully-detached pill actions go fully rounded.

- `{rounded.xs}` (9px) and `{rounded.sm}` (11px) — small image crops: stop-list thumbnails and summary-screen thumbnails.
- `{rounded.DEFAULT}` (14px) — bubbles, small badges/recap pills, the stop-info photo banner.
- `{rounded.md}` (16px) — chips: topic pills, named-start chips.
- `{rounded.lg}` (18px) — primary full-width action buttons.
- `{rounded.xl}` (22px) — bottom-sheet top corners (paired with `0 0` on the bottom corners, since sheets dock flush to the screen edge).
- `{rounded['2xl']}` (24px) — the most elevated single card in the system (the time wheel-picker's card).
- `{rounded.full}` (28px) — compact auto-width pill buttons and floating pill actions; at these components' actual heights this radius reads as a true pill/stadium shape, not a rounded rectangle.

Deliberately **not** used anywhere: sharp/unrounded corners. Every UI surface in every mock has some degree of rounding — there's no "sharp tool" register anywhere in this system, consistent with the warm, approachable brand posture.

The map itself is the one place this logic inverts on purpose: building blocks, roads, and the route line are drawn with true/flat geometry (plain rectangles for buildings, no corner-rounding), and park/cemetery shapes use their real surveyed polygon boundary with zero artistic liberty taken on the boundary itself. Rounded, friendly UI chrome sits *on top of* an honestly-flat, geometrically-real map — the softness belongs to the interface, not to the geography.

## Components

→ Composition reference: `mockups/key-route-review-quiet-streets-v2.html` (the Map component's "Quiet Streets" treatment, rendered in full), `mockups/flow-01-setup.html` (preference control, chips, pill buttons in situ), `mockups/flow-02-generate.html`, `mockups/flow-03-walk.html`, `mockups/key-must-tier-skeleton.html`. These are rendered examples of the components below, not a separate spec — this file's prose wins on conflict.

**Primary button (full-width).** `{colors.forest}` fill, `{colors.cream}` text, `{rounded.lg}` corners, ~13–14px vertical padding, `width: 100%`. Used whenever there's exactly one dominant action on a screen (e.g. "Continue" after picking time, the confirmation sheet's "Start my [Topic] Jaunt").

**Compact pill button (auto-width).** Same fill/text colors as the primary button, but `{rounded.full}` (28px) corners, `display: inline-flex`, `width: auto`, ~12px/24px padding. Used for short-label single actions that shouldn't stretch edge-to-edge (e.g. "Start my History Jaunt" on the Choose-Topic page, "Back to start" on the no-summary ending).

> **This distinction has been the single most-repeated real bug in this project.** A short-text button inheriting the full-width-primary treatment (meant for a different context — typically a two-button flex row) has happened at least twice independently: "Start my History Jaunt" was once stretched into an oversized box after inheriting `flex:1` from a paired-button style, and "Back to start" on the walk-complete screen made the identical mistake inheriting `.cta-btn.primary`'s `width:100%`. Both were caught and fixed, but only after the fact. Treat full-width-primary and compact-pill as genuinely distinct components, never variants selected by habit.

**Equal-weight button pair.** Two buttons of equal visual weight sitting side by side, each `flex: 1`, ~10px gap between them, sharing one row. Used only when two actions are genuinely co-equal choices, never for a single short-label action: "Choose Topic" (forest fill) beside "Wild Jaunt" (sage fill) on the topic-selection opening screen; "Re-Jaunt" (forest outline) beside "Start my jaunt" (forest fill) on Route Review.

**Chip / pill.** `{colors.surface-muted}` fill, `{colors.ink}` text, `{rounded.md}` corners, ~9–10px/14–16px padding, horizontally scrollable in a row with hidden scrollbar. Selected state inverts to `{colors.forest}` fill / `{colors.cream}` text. Used for named starting-point chips and topic pills.

**Preference control (landmark ↔ hidden-gem slider).** A horizontal track, `{colors.sage}` fill, 5px tall, `{rounded.md}` corners, with a circular `{colors.forest}`-filled handle (18px) and a soft drop shadow. An uppercase caption ("Landmarks or hidden gems? *optional*" — the "optional" in `{colors.ink-faint}`, the rest in `{colors.ink-soft}`, 10.5px/700) sits above the track; a small floating "Balanced" tag (`{colors.surface}` fill, `{colors.forest}` text, pill-shaped) centers itself above the handle at its default position; "Well-known" / "Hidden gems" labels (`{colors.ink-faint}`, 10px/600) sit below the track at each end. Default position is dead-center (Balanced) when untouched. Behavior (where it appears, what it does, FR-4) lives in `{EXPERIENCE.md}`'s Component Patterns — this is the visual spec only. Visual reference: `mockups/flow-01-setup.html`.

**Small badge / recap pill.** `{colors.surface-muted}` fill (or `{colors.forest}` fill for the in-walk time-remaining pill), small text (10.5–11.5px/700), `{rounded.DEFAULT}` corners, `inline-flex`, `width: auto`, `white-space: nowrap` — sized to its own content, never stretched. Used for the header recap ("Newtown · 60 min"), the route-review time total, and the in-walk "~18 min left" pill.

**Speech bubble.** `{colors.surface}` fill, `{colors.ink}` text, `{rounded.DEFAULT}` corners, soft close-lift shadow. Always paired with a Jarrod pose rather than standing alone — the bubble is specifically how Jarrod talks, not a generic tooltip/toast component.

**Bottom sheet.** `{colors.surface}` fill, `{rounded.xl}` top corners / square bottom corners, strong upward shadow, a small `{colors.sheet-handle}` drag-handle bar centered at the top. The single recurring structural pattern used for: the Route Review stop list, the pre-generation "Ready for your Jaunt?" confirmation, and the end-of-walk catch-up list. A near-full-screen variant (same visual language, taller) is used for the stop-info overlay.

**Card.** `{colors.surface}` fill, `{rounded['2xl']}` corners, soft shadow. Currently only one real instance exists — the time wheel-picker card — so treat "card" as a pattern with a single confirmed application rather than a fully generalized component yet.

**Stop row (list item).** A numbered circle marker (forest-filled, white number) or, for the route's own start/end point, a sage-filled marker. An optional 40–52px rounded-square photo thumbnail sits beside the text when a rights-cleared photo exists (FR-22); when it doesn't, the text simply takes the full row width — there is never a placeholder/blank-image box standing in for a missing photo. A small circular "remove" affordance (✕, muted fill) sits at the row's trailing edge where stop removal applies (FR-11).

**Map.** Rendered in full in `mockups/key-route-review-quiet-streets-v2.html` — this paragraph describes that mock, not an independent spec. **Implementation note (2026-10-07):** the running app renders on MapLibre GL JS over OpenFreeMap's free "positron" vector style as a starting base layer (architecture decision AD-1) — this approximates the muted palette below but does not yet reproduce it exactly; a custom style forked from OpenFreeMap and matched to this section's exact colors is follow-up work, not yet done. The "Quiet Streets" treatment: flat cream canvas; minor roads as thin neutral strokes, the one arterial street as a slightly heavier/darker stroke; buildings as alternating light/dark muted-grey rectangles (real texture, never blanked-out); parks/green space filled sage with a tree-cluster icon device clipped strictly to the park's real polygon boundary; the route itself a thick (6.5–7px) forest-green line following real street geometry, turning only at genuine intersections, never a freeform curve cutting through blocks; stop markers as forest-filled circles with a sage ring and a white number, or — where a rights-cleared photo exists — a rounded-square photo-thumbnail pin instead; the live position marker is Jarrod's head alone (a real ~30px crop, isolated at the actual alpha-channel gap between his head and torso in the source sheet — not a redrawn dot); background amenity points (FR-23) render as small (5px), low-opacity (0.7), muted-grey dots with simple generic glyphs, always visually subordinate to the route and stops. **Important open item:** this whole treatment is hand-drawn SVG in every mock; the running app currently serves standard raster map tiles, and whether this exact custom styling is achievable on top of that (vs. requiring vector tiles or a different rendering approach) is an open architecture question, not yet resolved (PRD Open Question 19). This section states the *intended visual target*, not a confirmed-achievable implementation.

**Off-canvas drawer.** A full-height white panel sliding in from the left (established at 78% of screen width) over a dimmed scrim, triggered by a hamburger icon. Currently holds only "End Jaunt"; explicitly reserved as the future home for two Post-V1 items (weather-rerouting, mid-walk re-route) once those exist — do not add rows for unbuilt features.

**Visited checkbox badge.** A small bordered square (forest 1.5px border) paired with a "Visited" label, floating top-right on the stop-info overlay, visually separate from the content below it — opening/reading the story never toggles this on its own.

**Jarrod (the character).** Body always rendered in solid `{colors.forest}` — this is the one non-negotiable identity anchor across every pose. Two simple dot eyes (white oval, dark pupil), no mouth, no eyebrows, no other facial features — a deliberate, hard-capped scope decision made explicitly for mobile-scaling reasons. The real source sheet (`imports/jaunty-mascot-sheet-v2-eyes-transparent.png`) contains nine poses in a 3×3 grid: a plain walk, a wave/greeting (raised arm + spark lines), an alert/buzz pose (motion lines), a fist-up/excited pose, a carefree pose, and accessorized variants (olive/orange caps; olive/yellow/blue backpacks) that demonstrate the one place color variety is allowed — **accessories may carry other colors; the body itself never does.** A separate, dedicated sad pose exists (`imports/jaunty-sad-transparent.png`) — properly hunched, head tilted down, droopy eyes, used specifically for the honest no-suitable-route state (FR-9). Sizing in observed use ranges from a small 84px overlay figure down to a 30px head-only live-position marker, up to a 168px central greeting figure, following the prominence-scales-with-content-density rule in Layout & Spacing above.

## Do's and Don'ts

| Do | Don't |
|---|---|
| Treat every Jarrod appearance as a cropped/composited region of the real source PNGs (`jaunty-mascot-sheet-v2-eyes-transparent.png`, `jaunty-sad-transparent.png`) | Hand-draw, redraw, or regenerate Jarrod as new vector/SVG shapes from a text description — this produced an unrecognizable, distorted result twice in this project before the real-asset-crop rule was adopted |
| Keep Jarrod's body solid `{colors.forest}`; let accessories (cap, backpack) carry other colors | Recolor Jarrod's body itself, or invent a new pose by transforming an existing one (e.g. the discarded `rotate(18deg)` "sad" hack) once a real dedicated asset exists for that state |
| Use full-width-primary for a single dominant action; compact auto-width pill for a short-label action; equal-weight flex pairs only for two genuinely co-equal actions | Let a short-label button inherit full-width or `flex:1` styling meant for a different button context — this exact bug has recurred more than once |
| Keep map geometry (parks, the route line, street grid) true to real-world shape and boundary, with styling applied on top | Take artistic liberty with a real boundary — e.g. drawing a park as a freeform illustrated blob instead of its true polygon |
| Keep background amenity points (FR-23) small, muted, and clearly subordinate to the route and stop markers | Let the amenities layer approach default-maps-app pin density/contrast and start competing visually with the route or stops |
| Tint shadows with the ink color (`rgba(22,48,42,…)`), reserved for floating UI only | Use neutral grey/black shadows, or add shadow to flat map content |
| Show a stop's real photo when a rights-cleared source image exists; otherwise let the text fill the row | Show a placeholder/blank-image box standing in for a missing photo |

**Open items not covered above** (reasoning and detail live at each point of use, not repeated here): dark-mode palette and error/destructive color — see Colors; spacing-scale ratification — see Layout & Spacing; Quiet Streets rendering achievability — see Components → Map.
