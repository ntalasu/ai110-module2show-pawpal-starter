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

from dataclasses import dataclass, field

# Higher weight = more important. Used by Task.score() for ordering.
PRIORITY_WEIGHTS = {"low": 1, "medium": 2, "high": 3}


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

    def score(self) -> float:
        """Rank value for ordering: priority dominates, shorter tasks break ties."""
        weight = PRIORITY_WEIGHTS.get(self.priority, PRIORITY_WEIGHTS["medium"])
        return weight * 1000 - self.duration_minutes

    def is_recurring(self) -> bool:
        """Whether this task repeats (frequency != 'once')."""
        return self.frequency != "once"

    def mark_done(self) -> None:
        """Mark this task as completed."""
        self.done = True


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
            self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Detach a care task from this pet (no-op if absent)."""
        if task in self.tasks:
            self.tasks.remove(task)

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

    def sort_tasks(self, items: list[ScheduledTask]) -> list[ScheduledTask]:
        """Order candidates by task.score() (priority first, then shorter)."""
        return sorted(items, key=lambda item: item.task.score(), reverse=True)

    def filter_by_time(self, items: list[ScheduledTask]) -> list[PlanDecision]:
        """Greedily fit items into the budget; record a keep/drop reason for each."""
        decisions: list[PlanDecision] = []
        budget = self.owner.available_minutes()
        used = 0
        cursor = self.owner.day_start

        for item in items:
            duration = item.task.duration_minutes
            if used + duration <= budget:
                item.start_minute = cursor
                cursor += duration
                used += duration
                reason = (
                    f"scheduled at {_format_time(item.start_minute)} "
                    f"({duration} min, {item.task.priority} priority)"
                )
                decisions.append(PlanDecision(item.pet, item.task, True, reason))
            else:
                reason = (
                    f"skipped — {budget - used} min left, needs {duration}"
                )
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
