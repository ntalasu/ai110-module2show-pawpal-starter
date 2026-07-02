# PawPal+ Project Reflection

## 1. System Design
A user should be able to track pet care tasks, consider constraints, and create a daily plan. 
**a. Initial design**

- Briefly describe your initial UML design.
There are the four classes with each one having it's own attributes. 
- What classes did you include, and what responsibilities did you assign to each? I included all 4 classes: Owner, Pet, Task, and Scheduler. 
The Owner class describes the human using the app. It also holds preferences and owns one or more pets. The Pet class describes the animal being cared for. It owns the tasks that need doing. The Task class describes all the single unit of care work. The Scheduler class is the engine of the project that turns tasks and constraints into an ordered daily plan. 

**b. Design changes**

- Did your design change during implementation?

Yes. My first design had only the four classes (Owner, Pet, Task, Scheduler), and the Scheduler's plan was just a `list[Task]`. When I reviewed the design before writing logic, I found several gaps:

1. **No way to store *when* a task happens.** A Task only had `duration_minutes`, so a plan couldn't say "08:00 — Morning walk." I added a `ScheduledTask` class (pet + task + `start_minute`) so the plan can hold timing, and switched `plan` to `list[ScheduledTask]`.
2. **The Scheduler couldn't reach the tasks.** It held an Owner, and tasks live on each Pet, but there was no path from owner to task list — and flattening to `list[Task]` lost which pet each task belonged to. I added `Owner.all_tasks()`, which returns `ScheduledTask` candidates that keep the pet reference.
3. **A duplicated time budget.** Both `Owner.available_minutes` and `Scheduler.time_budget` tracked the same thing, so they could drift. I removed the Scheduler's copy and had it read from the owner instead (one source of truth).
4. **`explain()` needed data the filter threw away.** To explain why a task was skipped, I needed the reason at filter time. I added a `PlanDecision` class (included + reason) so `filter_by_time` records decisions that `explain()` reads later.

I also changed `Task.recurring` (a bool) to `frequency` ("once" / "daily" / "weekly") so it can distinguish daily vs. weekly tasks.

**Why:** these changes came from noticing the original model couldn't produce the output the scenario asked for (a timed, explained daily plan across multiple pets). Catching this at the design stage — before writing logic — was cheaper than refactoring working code later.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?

My scheduler considers three constraints: **time available** (the owner's daily care window, stored as `day_start`/`day_end` in minutes-since-midnight), **task priority** (low/medium/high), and **task duration**. The available window is a hard limit — the plan can never exceed it — while priority and duration decide *ordering* within that budget. Frequency (once/daily/weekly) is also tracked, but it drives recurrence rather than a single day's plan.

- How did you decide which constraints mattered most?

Time is the non-negotiable constraint: a plan that overruns the day is useless, so `filter_by_time` enforces it absolutely. Within that budget, I ranked **priority above duration** because the scenario is about a busy owner staying consistent with important care — a high-priority med should be scheduled before a low-priority grooming even if the grooming is shorter. Duration only acts as a tie-breaker (shorter tasks first among equal priorities) so the plan fits as many important tasks as possible.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.

My scheduler uses a **greedy algorithm**: it sorts tasks by priority (then by shorter duration to break ties) and packs them into the day back-to-back until the time budget runs out. This means it does *not* guarantee the "best" possible plan. Because it commits to high-priority tasks first, a single long high-priority task can crowd out several shorter tasks that together would have been more valuable. For example, in an hour a 45-minute high-priority grooming will block a 20-minute and a 30-minute task that could otherwise both fit. A true optimal solution would be a knapsack-style search that tries combinations to maximize total value.

- Why is that tradeoff reasonable for this scenario?

For a personal pet-care planner, "do the most important things first" is exactly the behavior a user expects and can understand — if grooming is high priority, they *want* it scheduled even if it displaces smaller tasks. The greedy approach is also O(n log n) (dominated by the sort), simple to implement, and easy to explain, which matters because the app's job includes explaining *why* each task was chosen. An optimal knapsack solver would be slower, much harder to reason about, and its "smarter" choices could feel arbitrary to the user (skipping a high-priority task to fit two low-priority ones). Predictable and explainable beats mathematically optimal for this use case.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

I used my AI coding assistant across every phase: brainstorming the UML in design, generating class stubs, implementing the scheduling logic incrementally, writing the pytest suite, wiring the Streamlit UI, and drafting the README and this reflection.

- What kinds of prompts or questions were most helpful?

**Which AI features were most effective for building the scheduler:**

1. **Codebase-aware editing** — the assistant could read `pawpal_system.py` directly and make targeted edits that matched my existing style (docstrings, dataclasses, minutes-since-midnight convention) instead of dumping generic code I'd have to rewrite.
2. **Running tests and the CLI in-loop** — it ran `python -m pytest` and `python main.py` after changes and used the real output to fix issues, so I got verified code rather than plausible-looking code.
3. **"Explain the edge cases" prompts** — asking *what to test* before *writing tests* surfaced non-obvious cases (the half-open conflict boundary, recurrence-vs-deduplication) that I wouldn't have thought to check.
4. **UML-to-code diffing** — attaching the final implementation and asking "what no longer matches my diagram?" caught several methods (`filter_tasks`, `detect_conflicts`, `next_occurrence`) that I'd added during the build but never reflected in the design.

The most helpful prompts were **specific and grounded in my files** — "based on my final implementation, what should change?" beat open-ended "write me a scheduler."

**How separate chat sessions per phase kept me organized:**

I ran design, implementation, testing, and documentation as separate sessions. This kept each conversation focused on one artifact, so context didn't bleed (a testing session wasn't distracted by UI details), and it mirrored the real workflow — finish and verify one phase before starting the next. It also made it easy to revisit a phase (e.g. reopening the design session to update the UML) without scrolling through unrelated build chatter, and each session's history became a clean record of the decisions made in that phase.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

When wiring conflict detection into the Streamlit UI, the assistant pointed out — and I confirmed — that my `build_plan()` packs tasks back-to-back through a single cursor, so a *generated* plan is conflict-free by construction and `detect_conflicts()` would never actually fire in the app. The tempting "clean" move was to delete the conflict code as dead. I rejected that: I kept `detect_conflicts()`/`conflict_warning()` and wired them in honestly (showing a positive "no conflicts" state), because the methods are genuinely correct and tested, and they'll matter the moment I add user-pinned start times. I also declined to bolt on pinned-time scheduling just to make the demo flashier — that would have added complexity outside the phase I was in.

I made a smaller modification too: an early UI draft nested a `_fmt` helper inside a button handler; I pulled it up to module scope so both the tasks table and the schedule could share one formatter instead of redefining it.

- How did you evaluate or verify what the AI suggested?

I verified by running things, not by reading alone: the pytest suite had to stay green (11 passing), `python main.py` had to produce the schedule and conflict output I expected, and I sanity-checked generated code against my own design rules (single source of truth for the time budget, tasks comparable by care details, no dead code left behind). When a suggested test used a `set` of `ScheduledTask` dataclasses, the test crashed with `TypeError: unhashable type` — running it caught the mistake immediately, and I fixed the assertion to compare by identity instead.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?

The 11 tests in `tests/test_pawpal.py` cover:

1. **Task basics** — `mark_done()` flips a task's status, and adding a task to a pet increases its task count.
2. **Sorting correctness** — the built plan comes out in chronological, non-overlapping start times, and `sort_tasks` ranks by priority first with shorter tasks breaking ties.
3. **Recurrence logic** — completing a `daily` task auto-creates a fresh, not-done occurrence due the following day, while a one-off (`once`) task spawns nothing.
4. **Conflict detection** — tasks sharing or overlapping a time slot are flagged and `conflict_warning()` returns a readable message, but back-to-back tasks (touching but not overlapping) are correctly *not* flagged.
5. **Edge cases** — a pet with no tasks yields an empty plan and no conflicts, and a task too long to fit the day window is skipped rather than scheduled past `day_end`.

- Why were these tests important?

They target the parts of the system where the logic is genuinely non-obvious and most likely to break silently. Sorting and time-boxing are the core value of the app, so they have to be right. The **half-open conflict boundary** (does a task starting exactly when another ends count as a clash?) and the **recurrence-vs-deduplication interaction** are subtle enough that a wrong answer would look plausible — exactly the cases worth locking down with tests. The edge cases (empty pet, task that can't fit) protect against crashes and off-by-one time-budget errors on the boundaries where bugs usually hide.

**b. Confidence**

- How confident are you that your scheduler works correctly?

**Confidence level: 4 / 5.** The core behaviors — sorting by priority, time-boxing tasks into the day window, recurring-task requeueing, and conflict detection — are all covered by passing tests, so I'm confident the common paths work as intended. I held back from a 5 because a few edge cases aren't yet tested (see below).

- What edge cases would you test next if you had more time?

With more time I'd add tests for:

1. **Weekly month/year rollover** — a `weekly` task due Dec 29 should advance to Jan 5, confirming the recurrence relies on `timedelta` and not naive date math.
2. **Cross-pet conflicts** — `detect_conflicts()` should flag overlaps between tasks belonging to *different* pets and label the scope correctly, not just same-pet clashes.
3. **Duplicate-task rejection** — `Pet.add_task` ignores duplicates, and because `pet` is excluded from equality, I'd verify a genuinely new recurrence (different `due_date`) is still added while an exact duplicate is dropped.
4. **`filter_tasks` combinations** — `done` and `pet_name` applied together, case-insensitive name matching, and a name that matches no pet (empty result, not an error).
5. **Availability boundaries** — `set_availability(end < start)` raising `ValueError`, and a zero-length window (`available_minutes() == 0`) skipping every task.
6. **Unknown priority string** — a typo'd priority falling back to the medium weight in `score()` rather than sorting as zero.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

I'm most satisfied with catching the design gaps *before* writing logic — adding `ScheduledTask`, `PlanDecision`, and `Owner.all_tasks()` at the design stage meant the implementation flowed cleanly and produced the timed, explained plan the scenario asked for. I'm also happy with the test suite: it pins down the genuinely tricky behaviors (half-open conflict boundary, daily recurrence) rather than just the easy paths.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

I'd add **user-pinned start times** so tasks can have fixed times (e.g. "meds at 08:00"), which would make `detect_conflicts()` meaningful in the app rather than only in tests. I'd also test the remaining edge cases named in my confidence note (weekly month/year rollover, cross-pet conflicts, duplicate-task rejection), and consider whether the greedy scheduler should offer an optional "fit the most tasks" mode alongside "most important first."

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

**On being the "lead architect" with powerful AI tools:** the AI is fast and fluent, but it optimizes for the local request, not for the health of *my* system — so the decisions that keep the design coherent stayed mine. My job was to own the architecture (what the classes are and why), to insist on a single source of truth, to reject changes that were "clean" locally but wrong globally (like deleting the tested conflict code), and to *verify by running* rather than trusting confident-sounding output. The AI multiplied my speed dramatically, but only because I stayed the one deciding what "correct" meant and holding the whole design in view; used passively, it would have produced working-looking code that quietly drifted from the design.
