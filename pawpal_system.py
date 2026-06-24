"""PawPal+ — class skeleton.

Stubs only: names, attributes, and empty methods derived from diagrams/uml.mmd.
No scheduling logic yet — implement behavior in small increments after this.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Task:
    """A single unit of pet care work (walk, feeding, meds, grooming)."""

    title: str
    duration_minutes: int
    priority: str = "medium"  # "low" | "medium" | "high"
    recurring: bool = False
    done: bool = False

    def score(self) -> float:
        """Rank value used for ordering, derived from priority and duration."""
        raise NotImplementedError

    def is_recurring(self) -> bool:
        """Whether this task repeats (e.g. daily vs. one-off)."""
        raise NotImplementedError

    def mark_done(self) -> None:
        """Mark this task as completed."""
        raise NotImplementedError


@dataclass
class Pet:
    """The animal being cared for; owns the tasks that need doing."""

    name: str
    species: str = "dog"  # "dog" | "cat" | "other"
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a care task to this pet."""
        raise NotImplementedError

    def remove_task(self, task: Task) -> None:
        """Detach a care task from this pet."""
        raise NotImplementedError

    def get_tasks(self) -> list[Task]:
        """Return this pet's tasks."""
        raise NotImplementedError


@dataclass
class Owner:
    """The human user; holds preferences and owns one or more pets."""

    name: str
    available_minutes: int = 0
    pets: list[Pet] = field(default_factory=list)
    preferences: dict = field(default_factory=dict)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        raise NotImplementedError

    def set_availability(self, start, end) -> None:
        """Define the daily time window available for care."""
        raise NotImplementedError

    def list_pets(self) -> list[Pet]:
        """Return this owner's pets."""
        raise NotImplementedError


class Scheduler:
    """Turns an owner's tasks + constraints into an ordered daily plan."""

    def __init__(self, owner: Owner, time_budget: int = 0) -> None:
        self.owner = owner
        self.time_budget = time_budget
        self.plan: list[Task] = []

    def build_plan(self) -> list[Task]:
        """Choose and order tasks for the day within the time budget."""
        raise NotImplementedError

    def sort_tasks(self, tasks: list[Task]) -> list[Task]:
        """Order tasks by priority, then duration."""
        raise NotImplementedError

    def filter_by_time(self, tasks: list[Task]) -> list[Task]:
        """Drop tasks that would overflow the available time budget."""
        raise NotImplementedError

    def explain(self) -> str:
        """Explain why each task was chosen and when it happens."""
        raise NotImplementedError
