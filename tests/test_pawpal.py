"""Tests for PawPal+ core behaviors."""

import os
import sys
from datetime import date, timedelta

# Make pawpal_system (at the repo root) importable when pytest collects from tests/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Owner, Pet, ScheduledTask, Scheduler, Task


def test_mark_done_changes_status():
    """Calling mark_done() flips a task from not-done to done."""
    task = Task("Feeding", duration_minutes=10, priority="high")
    assert task.done is False  # starts incomplete

    task.mark_done()

    assert task.done is True


def test_adding_task_increases_pet_task_count():
    """Adding a task to a Pet increases that pet's task count by one."""
    pet = Pet("Mochi", species="cat")
    assert len(pet.get_tasks()) == 0  # starts with no tasks

    pet.add_task(Task("Litter change", duration_minutes=15, priority="medium"))

    assert len(pet.get_tasks()) == 1


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #

def _owner_with_tasks(*tasks: Task, day_start: int = 480, day_end: int = 1320) -> Owner:
    """Build an Owner with one pet that holds the given tasks."""
    owner = Owner("Alex", day_start=day_start, day_end=day_end)
    pet = Pet("Mochi", species="cat")
    for task in tasks:
        pet.add_task(task)
    owner.add_pet(pet)
    return owner


# --------------------------------------------------------------------------- #
# Sorting correctness
# --------------------------------------------------------------------------- #

def test_build_plan_returns_tasks_in_chronological_order():
    """The built plan lays tasks out in ascending, non-overlapping start times."""
    owner = _owner_with_tasks(
        Task("Walk", duration_minutes=30, priority="low"),
        Task("Meds", duration_minutes=5, priority="high"),
        Task("Feed", duration_minutes=10, priority="medium"),
    )
    plan = Scheduler(owner).build_plan()

    starts = [item.start_minute for item in plan]
    assert starts == sorted(starts)  # chronological
    # back-to-back with no gaps or overlaps: each task starts where the last ended
    for earlier, later in zip(plan, plan[1:]):
        assert later.start_minute == earlier.end_minute


def test_sort_orders_by_priority_then_shorter_duration():
    """High priority comes first; equal priority breaks ties toward the shorter task."""
    high_long = Task("Grooming", duration_minutes=60, priority="high")
    high_short = Task("Meds", duration_minutes=5, priority="high")
    low = Task("Nap check", duration_minutes=5, priority="low")
    owner = _owner_with_tasks(low, high_long, high_short)

    ordered = Scheduler(owner).build_plan()
    titles = [item.task.title for item in ordered]

    assert titles == ["Meds", "Grooming", "Nap check"]


# --------------------------------------------------------------------------- #
# Recurrence logic
# --------------------------------------------------------------------------- #

def test_marking_daily_task_done_creates_next_day_occurrence():
    """Completing a daily task queues a fresh, not-done copy due the next day."""
    pet = Pet("Mochi", species="cat")
    today = date.today()
    daily = Task("Feeding", duration_minutes=10, priority="high",
                 frequency="daily", due_date=today)
    pet.add_task(daily)

    daily.mark_done()

    tasks = pet.get_tasks()
    assert len(tasks) == 2  # original (done) + next occurrence
    followups = [t for t in tasks if not t.done]
    assert len(followups) == 1
    nxt = followups[0]
    assert nxt.title == "Feeding"
    assert nxt.due_date == today + timedelta(days=1)
    assert nxt.frequency == "daily"  # keeps recurring


def test_marking_once_task_done_does_not_recur():
    """A one-off task does not spawn a follow-up when completed."""
    pet = Pet("Mochi", species="cat")
    once = Task("Vet visit", duration_minutes=45, priority="high", frequency="once")
    pet.add_task(once)

    once.mark_done()

    assert len(pet.get_tasks()) == 1
    assert once.next_occurrence() is None


# --------------------------------------------------------------------------- #
# Conflict detection
# --------------------------------------------------------------------------- #

def test_detect_conflicts_flags_tasks_at_the_same_time():
    """Two tasks sharing a start time are reported as a conflict."""
    pet = Pet("Mochi", species="cat")
    a = ScheduledTask(pet=pet, task=Task("Walk", duration_minutes=30), start_minute=480)
    b = ScheduledTask(pet=pet, task=Task("Feed", duration_minutes=10), start_minute=480)

    conflicts = Scheduler(_owner_with_tasks()).detect_conflicts([a, b])

    assert len(conflicts) == 1
    assert {id(x) for x in conflicts[0]} == {id(a), id(b)}


def test_conflict_warning_is_nonempty_when_times_overlap():
    """conflict_warning() surfaces a message for overlapping (not just identical) slots."""
    pet = Pet("Mochi", species="cat")
    a = ScheduledTask(pet=pet, task=Task("Walk", duration_minutes=30), start_minute=480)
    b = ScheduledTask(pet=pet, task=Task("Feed", duration_minutes=10), start_minute=500)

    warning = Scheduler(_owner_with_tasks()).conflict_warning([a, b])

    assert warning  # truthy, human-readable warning
    assert "conflict" in warning.lower()


def test_back_to_back_tasks_do_not_conflict():
    """Half-open intervals: a task starting exactly when another ends is not a conflict."""
    pet = Pet("Mochi", species="cat")
    a = ScheduledTask(pet=pet, task=Task("Walk", duration_minutes=30), start_minute=480)
    b = ScheduledTask(pet=pet, task=Task("Feed", duration_minutes=10), start_minute=510)

    conflicts = Scheduler(_owner_with_tasks()).detect_conflicts([a, b])

    assert conflicts == []


# --------------------------------------------------------------------------- #
# Edge cases
# --------------------------------------------------------------------------- #

def test_pet_with_no_tasks_produces_empty_plan():
    """An owner whose pet has no tasks yields an empty plan and no conflicts."""
    scheduler = Scheduler(_owner_with_tasks())

    assert scheduler.build_plan() == []
    assert scheduler.conflict_warning() == ""


def test_task_needing_more_than_remaining_time_is_skipped():
    """A task that doesn't fit the day window is dropped, not scheduled past day_end."""
    # Window is 60 min; the 90-min task cannot fit.
    owner = _owner_with_tasks(
        Task("Long groom", duration_minutes=90, priority="high"),
        day_start=480, day_end=540,
    )
    scheduler = Scheduler(owner)
    plan = scheduler.build_plan()

    assert plan == []
    assert any(not d.included for d in scheduler.decisions)
