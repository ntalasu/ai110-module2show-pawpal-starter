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
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
