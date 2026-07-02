"""PawPal+ — core implementation.

Four classes derived from diagrams/uml.mmd:
  Task       — a single activity (description, duration, frequency, done state)
  Pet        — pet details plus its list of tasks
  Owner      — manages multiple pets and exposes all their tasks
  Scheduler  — the "brain": retrieves, orders, and time-boxes tasks into a plan

Times are stored as minutes-since-midnight ints (e.g. 8:00 -> 480) to keep the
scheduling math simple and avoid datetime edge cases for now.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date, timedelta

# Higher weight = more important. Used by Task.score() for ordering.
PRIORITY_WEIGHTS = {"low": 1, "medium": 2, "high": 3}

# How far ahead each recurring frequency schedules its next occurrence.
FREQUENCY_STEP = {
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),
}


def _format_time(minute: int) -> str:
    """Render minutes-since-midnight as HH:MM (e.g. 480 -> '08:00')."""
    hours, mins = divmod(minute, 60)
    return f"{hours:02d}:{mins:02d}"


@dataclass
class Task:
    """A single unit of pet care work (walk, feeding, meds, grooming)."""

    title: str
    duration_minutes: int
    priority: str = "medium"  # "low" | "medium" | "high"
    frequency: str = "once"  # "once" | "daily" | "weekly"
    done: bool = False
    due_date: date = field(default_factory=date.today)
    # Back-reference to the owning pet, set by Pet.add_task. Excluded from repr
    # and equality to avoid recursion (Pet holds Tasks) and keep Tasks comparable
    # by their care details.
    pet: "Pet | None" = field(default=None, repr=False, compare=False)

    def score(self) -> float:
        """Rank value for ordering: priority dominates, shorter tasks break ties."""
        weight = PRIORITY_WEIGHTS.get(self.priority, PRIORITY_WEIGHTS["medium"])
        return weight * 1000 - self.duration_minutes

    def is_recurring(self) -> bool:
        """Whether this task repeats (frequency != 'once')."""
        return self.frequency != "once"

    def next_occurrence(self) -> "Task | None":
        """Build the next instance of a recurring task.

        Copies this task with done reset to False and the due_date advanced by
        one interval (FREQUENCY_STEP maps daily -> +1 day, weekly -> +1 week).
        timedelta handles month/year rollover, so month-end dates stay valid.

        Returns:
            A new, not-done Task for the next occurrence, or None if this task
            is one-off (frequency == 'once') and therefore does not repeat.
        """
        if not self.is_recurring():
            return None
        return replace(self, done=False, due_date=self.due_date + FREQUENCY_STEP[self.frequency])

    def mark_done(self) -> None:
        """Mark done; if recurring, queue the next occurrence on the same pet."""
        self.done = True
        if self.is_recurring() and self.pet is not None:
            self.pet.add_task(self.next_occurrence())


@dataclass
class Pet:
    """The animal being cared for; owns the tasks that need doing."""

    name: str
    species: str = "dog"  # "dog" | "cat" | "other"
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet (ignores duplicates)."""
        if task not in self.tasks:
            task.pet = self  # back-reference so the task can requeue itself
            self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Detach a care task from this pet (no-op if absent)."""
        if task in self.tasks:
            self.tasks.remove(task)
            task.pet = None

    def get_tasks(self) -> list[Task]:
        """Return a copy of this pet's tasks (callers can't mutate our list)."""
        return list(self.tasks)


@dataclass
class Owner:
    """The human user; holds preferences and owns one or more pets."""

    name: str
    day_start: int = 480  # 08:00, minutes since midnight
    day_end: int = 1320  # 22:00, minutes since midnight
    pets: list[Pet] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner (ignores duplicates)."""
        if pet not in self.pets:
            self.pets.append(pet)

    def set_availability(self, start: int, end: int) -> None:
        """Set the daily care window (minutes since midnight)."""
        if end < start:
            raise ValueError("end must be >= start")
        self.day_start = start
        self.day_end = end

    def available_minutes(self) -> int:
        """Total minutes in the care window (never negative)."""
        return max(0, self.day_end - self.day_start)

    def list_pets(self) -> list[Pet]:
        """Return a copy of this owner's pets."""
        return list(self.pets)

    def all_tasks(self) -> list[ScheduledTask]:
        """Gather every pet's tasks as unscheduled candidates (start_minute unset)."""
        return [
            ScheduledTask(pet=pet, task=task)
            for pet in self.pets
            for task in pet.tasks
        ]


@dataclass
class ScheduledTask:
    """A task placed in the plan, tied to its pet and a start time.

    start_minute is None until the scheduler assigns a slot, so the same type
    doubles as an unscheduled candidate.
    """

    pet: Pet
    task: Task
    start_minute: int | None = None

    @property
    def end_minute(self) -> int | None:
        """When this task finishes, or None if it isn't scheduled yet."""
        if self.start_minute is None:
            return None
        return self.start_minute + self.task.duration_minutes


@dataclass
class PlanDecision:
    """Why a candidate task was kept or dropped — feeds explain()."""

    pet: Pet
    task: Task
    included: bool
    reason: str


class Scheduler:
    """Turns an owner's tasks + constraints into an ordered daily plan.

    Reads its time budget from the owner (owner.available_minutes()) rather
    than storing a separate copy, so there is one source of truth.
    """

    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.plan: list[ScheduledTask] = []
        self.decisions: list[PlanDecision] = []

    def build_plan(self) -> list[ScheduledTask]:
        """Gather candidates, sort, filter by time, and assign start times."""
        candidates = [c for c in self.owner.all_tasks() if not c.task.done]
        ordered = self.sort_tasks(candidates)
        self.decisions = self.filter_by_time(ordered)
        self.plan = [item for item in ordered if item.start_minute is not None]
        return self.plan

    def filter_tasks(
        self, done: bool | None = None, pet_name: str | None = None
    ) -> list[ScheduledTask]:
        """Query tasks across every pet, applying any provided filters.

        Starts from all of the owner's tasks and narrows the list. Each filter
        is optional and they combine (logical AND); None means "ignore this
        filter", which is why `done` uses None rather than defaulting to False.

        Args:
            done: Keep only completed (True) or incomplete (False) tasks;
                None keeps both.
            pet_name: Keep only tasks for the pet with this name
                (case-insensitive); None keeps all pets.

        Returns:
            Matching tasks as ScheduledTask candidates, each retaining its pet
            reference.
        """
        items = self.owner.all_tasks()
        if done is not None:
            items = [it for it in items if it.task.done == done]
        if pet_name is not None:
            items = [it for it in items if it.pet.name.lower() == pet_name.lower()]
        return items

    def sort_tasks(self, items: list[ScheduledTask]) -> list[ScheduledTask]:
        """Order candidates by task.score() (priority first, then shorter)."""
        return sorted(items, key=lambda item: item.task.score(), reverse=True)

    def filter_by_time(self, items: list[ScheduledTask]) -> list[PlanDecision]:
        """Greedily fit items into the day window; record a keep/drop reason for each.

        A single `cursor` tracks where the next task goes; it doubles as the
        running total of time used (cursor - day_start).
        """
        decisions: list[PlanDecision] = []
        cursor = self.owner.day_start

        for item in items:
            duration = item.task.duration_minutes
            if cursor + duration <= self.owner.day_end:
                item.start_minute = cursor
                cursor += duration
                reason = (
                    f"scheduled at {_format_time(item.start_minute)} "
                    f"({duration} min, {item.task.priority} priority)"
                )
                decisions.append(PlanDecision(item.pet, item.task, True, reason))
            else:
                remaining = self.owner.day_end - cursor
                reason = f"skipped — {remaining} min left, needs {duration}"
                decisions.append(PlanDecision(item.pet, item.task, False, reason))

        return decisions

    def explain(self) -> str:
        """Explain, from self.plan and self.decisions, what was chosen and when."""
        available = self.owner.available_minutes()
        lines = [f"Daily plan ({available} min available):"]

        if self.plan:
            for item in self.plan:
                lines.append(
                    f"  {_format_time(item.start_minute)} — {item.task.title} "
                    f"({item.task.duration_minutes} min) "
                    f"[priority: {item.task.priority}] for {item.pet.name}"
                )
        else:
            lines.append("  (nothing scheduled)")

        skipped = [d for d in self.decisions if not d.included]
        if skipped:
            lines.append("Skipped:")
            for decision in skipped:
                lines.append(
                    f"  {decision.task.title} ({decision.pet.name}) — {decision.reason}"
                )

        return "\n".join(lines)

    def detect_conflicts(
        self, items: list[ScheduledTask] | None = None
    ) -> list[tuple[ScheduledTask, ScheduledTask]]:
        """Return pairs of scheduled tasks whose time slots overlap.

        Two tasks overlap when one starts before the other ends (half-open
        intervals, so back-to-back tasks that merely touch do NOT conflict).
        Works across pets; check each pair's .pet to tell same-pet from cross-pet.
        Defaults to self.plan.
        """
        pool = self.plan if items is None else items
        scheduled = sorted(
            (it for it in pool if it.start_minute is not None),
            key=lambda it: it.start_minute,
        )

        conflicts: list[tuple[ScheduledTask, ScheduledTask]] = []
        for i, earlier in enumerate(scheduled):
            for later in scheduled[i + 1:]:
                if later.start_minute >= earlier.end_minute:
                    break  # sorted by start, so nothing further can overlap
                conflicts.append((earlier, later))
        return conflicts

    def conflict_warning(self, items: list[ScheduledTask] | None = None) -> str:
        """Summarize any scheduling overlaps as a warning message.

        A lightweight, non-crashing wrapper around detect_conflicts: it never
        raises, so callers can guard with a plain `if warning:` instead of
        try/except. Each line names both tasks, their time ranges, the pet(s),
        and whether the clash is same-pet or cross-pet.

        Args:
            items: Scheduled tasks to check; defaults to self.plan.

        Returns:
            A multi-line warning string when overlaps exist, or an empty string
            (falsy) when the schedule is clear.
        """
        conflicts = self.detect_conflicts(items)
        if not conflicts:
            return ""

        lines = [f"⚠️  {len(conflicts)} scheduling conflict(s) detected:"]
        for earlier, later in conflicts:
            scope = "same pet" if earlier.pet is later.pet else "different pets"
            lines.append(
                f"  {earlier.task.title} ({_format_time(earlier.start_minute)}"
                f"–{_format_time(earlier.end_minute)}, {earlier.pet.name}) overlaps "
                f"{later.task.title} ({_format_time(later.start_minute)}"
                f"–{_format_time(later.end_minute)}, {later.pet.name}) [{scope}]"
            )
        return "\n".join(lines)
