"""Tests for PawPal+ core behaviors."""

import os
import sys

# Make pawpal_system (at the repo root) importable when pytest collects from tests/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pawpal_system import Pet, Task


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
