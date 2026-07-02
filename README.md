# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

Paste a sample of your app's CLI or Streamlit output here so a reader can see what a generated plan looks like:

```
# e.g.:
# Daily plan for Biscuit (Golden Retriever):
#   08:00 — Morning walk (30 min) [priority: high]
#   09:00 — Feeding (10 min) [priority: high]
#   ...
```
==== Today's Schedule for Jordan =====
Daily plan (120 min available):
  08:00 — Feeding (10 min) [priority: high] for Mochi
  08:10 — Morning walk (30 min) [priority: high] for Biscuit
  08:40 — Litter change (15 min) [priority: medium] for Mochi
  08:55 — Enrichment play (20 min) [priority: medium] for Biscuit
  09:15 — Grooming (45 min) [priority: low] for Biscuit
## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
# Paste your pytest output here
```

## 📐 Smarter Scheduling

All scheduling logic lives in `pawpal_system.py`. Times are stored as
minutes-since-midnight ints (e.g. `08:00` → `480`) to keep the math simple.

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Task.score()`, `Scheduler.sort_tasks()` | Each task's `score()` weights priority (low/medium/high) far above duration, so priority dominates and a shorter task breaks ties. `sort_tasks()` orders candidates by that score, highest first. |
| Filtering by pet / status | `Scheduler.filter_tasks(done, pet_name)` | Optional, combinable filters. `done=True/False` keeps completed/incomplete tasks (`None` keeps both); `pet_name` matches a pet case-insensitively. |
| Time-boxing (fit to the day) | `Scheduler.filter_by_time()`, `Scheduler.build_plan()` | Greedily packs sorted tasks back-to-back from `day_start`; tasks that overflow the window are skipped with a recorded reason. |
| Conflict detection | `Scheduler.detect_conflicts()`, `Scheduler.conflict_warning()` | `detect_conflicts()` returns pairs of tasks whose half-open `[start, end)` time slots overlap (across any pets). `conflict_warning()` wraps it in a friendly message and never raises — returns `""` when clear. |
| Recurring tasks | `Task.is_recurring()`, `Task.next_occurrence()`, `Task.mark_done()` | Completing a `daily`/`weekly` task auto-creates the next occurrence with its `due_date` advanced via `datetime.timedelta` (handles month/year rollover); one-off tasks spawn nothing. |
| Explanation | `Scheduler.explain()` | Renders the timed plan plus a "Skipped" section, so the user can see what was chosen, when, and why. |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
