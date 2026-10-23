# Jaunt

A mobile-first web app that turns a person's available time into a purposeful walk. Enter a starting point, how much time you have, and optionally a topic (history, architecture, public art, heritage, or "surprise me"), and Jaunt proposes a short walking loop with real, nearby stops — each with a short AI-generated story or fact grounded in real source material, never invented.

This is a student project for **IBE160 – Programmering med KI** (NMBU), developed with Claude Code and Codex as AI development partners. See [Project status](#project-status) below for exactly what's working today versus still planned, and [Planning & process documentation](#planning--process-documentation) for the full requirements/design trail.

## Prerequisites

- **Python 3.13** (or a recent Python 3.x — no version-specific syntax is used, but this is what the project was built and tested against)
- `pip`
- Two free API keys (see [Configuration](#configuration)):
  - [OpenRouteService](https://openrouteservice.org/dev/#/signup) — walking-route distance/duration
  - [OpenAI](https://platform.openai.com/api-keys) — AI stop selection and content generation

## Setup & run

```bash
git clone <this-repo-url>
cd IBE160

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt

cp .env.example .env
# then edit .env and fill in your real API keys

python3 app.py
```

Open **http://127.0.0.1:5000** in a browser.

## Configuration

Copy `.env.example` to `.env` and fill in:

| Variable | What it's for |
|---|---|
| `OPENROUTESERVICE_API_KEY` | Walking-route distance/duration matrix (`services.py`) |
| `OPENAI_API_KEY` | AI stop selection (`ai.py`) |
| `OPENAI_MODEL` | Which OpenAI model to use, e.g. `gpt-4o-mini` |

`.env` is gitignored and never committed. The catalogue of verified places (`data/sydney_places.json`) is already included in the repo, so you do **not** need to run the import scripts or hold any API keys just to start the app and see the map.

## Project status

The product requirements (see the PRD, linked below) describe the complete intended V1 flow: choose a starting point/time/topic → Jaunt generates and you review a route → you walk it, with AI-generated content per stop → an optional end-of-walk summary.

**What's actually running in this codebase right now:** the backend pieces are built and tested independently — the place catalogue and import pipeline, the route planner (shortlisting, feasibility, brute-force ordering), and AI-assisted stop selection from a pre-validated option menu. The frontend currently serves the catalogue on an interactive map (Leaflet) but is **not yet wired** to the planner/AI pipeline — there is no time/topic input UI and no route-generation flow in the browser yet. This is the single largest known gap, tracked explicitly in the PRD (`§0` and `Open Question 14`) rather than hidden.

If something in the running app looks incomplete compared to the PRD, that's this gap, not a surprise — check the PRD's Must/Should/Could tiering (`§6.1`) for what's actually committed for the course submission.

## Running tests

```bash
python3 -m unittest discover -s tests -v
node --test tests/frontend-recovery.test.cjs
```

The Python suite contains 305 tests covering the planner, preference-aware discovery/recovery, API, AI response handling and import pipelines. The 37 JavaScript recovery tests require Node.js but no npm install or build step. They execute the actual frontend script with browser/map/network boundaries stubbed, covering continuous preference transport/slider synchronization, Re-Jaunt and individual-stop replacement, malformed replacement responses, repeated edits, inline notice placement, card-local progress/modal cleanup, reload and retry; they do not verify rendered layout. Both suites use fixed/mocked data, so no API keys are needed.

## Regenerating the catalogue (optional)

The repo already includes a built catalogue (`data/sydney_places.json`) for the Newtown, Sydney pilot area, so this step is **not required** to run the app. If you want to rerun the import pipeline from scratch (e.g. after a code change to an importer):

```bash
python3 import_places.py      # OpenStreetMap + Wikipedia/Wikidata
python3 import_street_art.py  # Inner West Council street-art dataset
python3 import_heritage.py    # NSW Heritage MapServer (hand-curated seed list)
```

These make live network calls to external services (Overpass, Nominatim, NSW ArcGIS) and are resumable/rerunnable — see `docs/architecture-plan.md` for the design rationale.

## Project structure

```
app.py                  Flask app (current: serves the catalogue to the map)
planner.py               Route shortlisting, feasibility, ordering
ai.py                     AI stop-selection and content generation
services.py                Routing distance/duration matrix (OpenRouteService)
import_places.py        }  Offline, rerunnable catalogue-building scripts
import_street_art.py    }  (see docs/architecture-plan.md)
import_heritage.py      }
data/sydney_places.json  The built catalogue (committed, no regeneration needed)
static/, templates/     Frontend (Leaflet map)
tests/                   Unit tests (python3 -m unittest)
docs/                     Product brief, architecture plan, dev log, reflection report
_bmad-output/            PRD, UX design (DESIGN.md/EXPERIENCE.md), full decision trail
ai-prompts.md            Verbatim log of substantive AI prompts (course requirement)
AI-discussions.md        Async handoff notes between Claude and Codex
```

## Planning & process documentation

This project follows the BMAD method (Problem → Product Brief → PRD → UX → Architecture → Implementation). Each stage's artifacts are kept and updated, not just generated once:

- [`docs/product-brief.md`](docs/product-brief.md) — the original product brief
- [`_bmad-output/planning-artifacts/prds/prd-IBE160-2026-09-29/prd.md`](_bmad-output/planning-artifacts/prds/prd-IBE160-2026-09-29/prd.md) — the finalized PRD (requirements, Must/Should/Could tiering, open questions), plus [`addendum.md`](_bmad-output/planning-artifacts/prds/prd-IBE160-2026-09-29/addendum.md) and the [`.memlog.md`](_bmad-output/planning-artifacts/prds/prd-IBE160-2026-09-29/.memlog.md) decision trail
- [`_bmad-output/planning-artifacts/ux-designs/ux-IBE160-2026-10-02/DESIGN.md`](_bmad-output/planning-artifacts/ux-designs/ux-IBE160-2026-10-02/DESIGN.md) and [`EXPERIENCE.md`](_bmad-output/planning-artifacts/ux-designs/ux-IBE160-2026-10-02/EXPERIENCE.md) — visual identity and behavior/flow spec, plus the UX [`.memlog.md`](_bmad-output/planning-artifacts/ux-designs/ux-IBE160-2026-10-02/.memlog.md) and rendered mocks in `.working/`
- [`docs/architecture-plan.md`](docs/architecture-plan.md) — technical architecture and the sprint-by-sprint build log, including known limitations per sprint
- [`docs/ai-development-log.md`](docs/ai-development-log.md) — narrative log of how AI was used during development, including mistakes caught and corrected
- [`ai-prompts.md`](ai-prompts.md) — verbatim log of substantive prompts given to Claude Code and Codex
- [`AI-discussions.md`](AI-discussions.md) — async notes Claude and Codex leave each other on open problems
- [`docs/reflection-report.md`](docs/reflection-report.md) — the reflection report (in progress)

---

# Working with AI on this project

The sections below are the standing working agreement between the student and the AI development partners (Claude Code and Codex) for this project — read by both tools at the start of every session via `AGENTS.md`.

## Project purpose

This repository contains my project for **IBE160 – Programmering med KI**.

The goal is to develop a working software product while using AI tools such as **Claude and GPT/Codex as development partners**.

This is also an academic assignment. The development process, decisions, use of AI, testing, limitations, and reflection are therefore important parts of the project.

The goal is **not to build the most technically advanced product possible**.

The goal is to build a product that:

- satisfies the assignment requirements
- works reliably
- has a clear purpose and user experience
- uses appropriate programming concepts
- is understandable to the student
- can be explained and defended by the student

---

# Source of truth

Before making significant changes, read the relevant project documentation.

Important files may include:

- the IBE160 assignment/project description
- `product-brief.md`
- reflection report/template
- README files
- existing source code
- configuration files
- documentation in the repository

The **IBE160 assignment specification is the highest-priority source of truth**.

Do not invent assignment requirements.

If documentation and implementation conflict, identify the conflict before making assumptions.

If a requirement is ambiguous, flag it instead of silently deciding what it means.

---

# Product development approach

Follow this general process:

**Problem → Product Brief → Requirements → Design → Implementation → Testing → Reflection**

Do not jump directly into implementation when the intended behaviour is unclear.

The product brief should primarily define:

- the problem
- intended users
- desired outcome
- core product concept
- important features
- success criteria
- MVP scope
- what is deliberately out of scope

Keep **product requirements** separate from **technical implementation decisions**.

---

# Development priorities

Use the following order of priorities:

1. Meet the IBE160 assessment requirements.
2. Preserve existing working functionality.
3. Build the agreed core product.
4. Keep the implementation understandable.
5. Prefer simple and maintainable solutions.
6. Test important functionality.
7. Improve UI/UX where it meaningfully improves the product.
8. Add technical sophistication only when it solves a real problem.

A smaller product that works well is preferable to a larger unfinished product.

Do not add features merely because they are technically possible.

---

# Working method

## Before changing code

1. Inspect the existing repository.
2. Read relevant documentation.
3. Understand what already works.
4. Identify the requirement or problem being addressed.
5. Consider the smallest reasonable change that solves it.

Do not start rewriting code before understanding the existing implementation.

## When implementing

- Make small, reviewable changes.
- Preserve working functionality.
- Follow existing project conventions where reasonable.
- Keep functions and components focused.
- Use descriptive names.
- Avoid unnecessary complexity.
- Add comments when reasoning would otherwise be difficult to understand.
- Do not rewrite large working sections without a clear reason.

## After implementing

- Run relevant tests or checks.
- Check for regressions.
- Check important user flows manually when appropriate.
- Explain what changed.
- Mention remaining limitations or uncertainties.

---

# AI collaboration

Claude and GPT/Codex are **development partners**, not autonomous owners of the project.

Do not make major product or architectural decisions silently.

For significant changes, first explain:

1. What problem was identified?
2. What should change?
3. Why is the change necessary?
4. What files/components will be affected?
5. Are there important trade-offs?

Small and obvious fixes can be implemented directly.

---

# Claude's role

Claude is primarily responsible for:

- implementation
- feature development
- UI/UX
- product thinking
- debugging
- explaining implementation choices

Claude should keep implementation aligned with the product brief and assignment requirements.

Claude should avoid expanding the project scope unnecessarily.

---

# GPT / Codex role

GPT/Codex is primarily responsible for:

- code review
- debugging difficult problems
- checking implementation against requirements
- testing
- identifying edge cases
- identifying unnecessary complexity
- suggesting targeted improvements
- providing a second opinion on architecture

GPT/Codex should not refactor working code simply because another implementation style is possible.

---

# Working across AI agents

Claude and GPT/Codex should review each other's work independently.

If Claude implemented something, GPT/Codex may review it.

If GPT/Codex implemented something, Claude may review it.

Do not assume another AI's implementation is correct.

However, do not change code simply to make it stylistically different.

Focus reviews on:

- bugs
- assignment requirements
- usability
- maintainability
- unnecessary complexity
- missing functionality
- edge cases
- testing

---

# Code quality

Write code that the student can reasonably understand and explain.

Prefer:

- straightforward control flow
- small functions
- clear naming
- explicit behaviour
- established libraries
- minimal dependencies

Avoid:

- premature optimisation
- unnecessary design patterns
- excessive abstraction
- deeply nested logic
- unexplained generated code
- unnecessary dependencies
- enterprise-style architecture for a student project

If a sophisticated solution is genuinely necessary, explain why a simpler solution is insufficient.

---

# Debugging

When something breaks:

1. Reproduce the problem.
2. Inspect the relevant code.
3. Identify the likely root cause.
4. Fix the root cause rather than hiding the symptom.
5. Test the affected behaviour.
6. Check that related functionality still works.

Do not repeatedly rewrite unrelated parts of the application while debugging one problem.

---

# Testing

Testing should focus on meaningful behaviour.

Prioritise:

- core product functionality
- important user flows
- calculations or business logic
- data handling
- input validation
- likely edge cases
- previously fixed bugs

Do not create excessive tests simply to increase the number of tests.

Run the existing test suite after meaningful changes when one exists.

---

# Scope control

Before adding a feature, ask:

> Is this required by the assignment, necessary for the core product, or clearly valuable to the user?

If not, treat it as optional.

Use these categories when useful:

### Must have

Required for the product or assignment.

### Should have

Important but not essential for the first working version.

### Could have

Useful enhancement if there is enough time.

### Out of scope

Not part of the current project.

Do not allow **Could have** features to interfere with completing **Must have** functionality.

---

# Academic context

This is an academic project involving AI-assisted development.

Important development decisions should remain understandable enough to reflect on later.

When relevant, preserve information about:

- why a technical approach was chosen
- where AI contributed
- problems encountered
- incorrect AI suggestions
- changes made after testing
- trade-offs
- limitations
- what required human judgement
- differences between Claude and GPT/Codex suggestions

Do not fabricate reflections or claim something happened during development if it did not.

---

# Communication with the student

When explaining things:

- Use clear and practical language.
- Assume the student is learning programming.
- Do not hide simple concepts behind technical jargon.
- Explain technical terminology when necessary.
- Explain the actual code in this repository rather than giving generic programming lectures.
- Recommend one sensible approach when possible instead of presenting many unnecessary alternatives.
- Warn before making risky or large changes.

If something appears wrong, explain **why** rather than simply replacing it.

---

# Important restrictions

Do not:

- invent assignment requirements
- silently change the product scope
- remove working functionality without justification
- add unnecessary features
- overengineer the application
- introduce dependencies without a reason
- rewrite working code solely for stylistic preference
- pretend tests passed if they were not run
- claim to have inspected a file that was not actually inspected
- fabricate results for the reflection report
- hide uncertainty

---

# Final principle

Do not ask:

> "What is the most impressive system an AI can build?"

Instead ask:

> "What is the simplest good solution that fulfils the IBE160 requirements, produces a useful working product, and leaves the student able to understand and explain what was built?"
## Academic project constraints
- This is a university student project, not a production commercial product.
- The student must be able to understand and explain the implementation.
- Prefer solutions appropriate to the scope of IBE160.
- Do not introduce frameworks, infrastructure or abstractions unless they solve a real project requirement.
- When generating substantial code, explain how it works.
- Keep the implementation consistent with the student's demonstrated project decisions.
