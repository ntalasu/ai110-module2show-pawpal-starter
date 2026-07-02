"""PawPal+ — command-line demo.

Adds tasks out of order, then exercises the Scheduler's sorting and filtering
methods so you can confirm they behave in the terminal.
Run with:  python main.py
"""

from pawpal_system import Owner, Pet, Scheduler, ScheduledTask, Task


def show(items) -> None:
    """Print a list of ScheduledTask candidates, one per line."""
    for it in items:
        flag = "✓" if it.task.done else " "
        print(
            f"  [{flag}] {it.task.title:<14} {it.task.duration_minutes:>3} min "
            f"| {it.task.priority:<6} | {it.pet.name}"
        )


def main() -> None:
    owner = Owner("Jordan")
    owner.set_availability(8 * 60, 10 * 60)  # 120 min window

    mochi = Pet("Mochi", species="cat")
    biscuit = Pet("Biscuit", species="dog")
    owner.add_pet(mochi)
    owner.add_pet(biscuit)

    # Add tasks deliberately OUT OF ORDER (mixed priorities and durations).
    mochi.add_task(Task("Litter change", 15, "low"))
    biscuit.add_task(Task("Grooming", 45, "low", frequency="weekly"))
    mochi.add_task(Task("Feeding", 10, "high", frequency="daily"))
    biscuit.add_task(Task("Enrichment", 20, "medium"))
    biscuit.add_task(Task("Morning walk", 30, "high", frequency="daily"))

    # Mark one task done so the completion filter has something to show.
    mochi.get_tasks()[0].mark_done()  # Litter change

    scheduler = Scheduler(owner)

    print("===== All tasks (insertion order) =====")
    show(scheduler.filter_tasks())

    print("\n===== Sorted by priority (sort_tasks) =====")
    show(scheduler.sort_tasks(scheduler.filter_tasks()))

    print("\n===== Filter: not done =====")
    show(scheduler.filter_tasks(done=False))

    print("\n===== Filter: done =====")
    show(scheduler.filter_tasks(done=True))

    print("\n===== Filter: Biscuit only =====")
    show(scheduler.filter_tasks(pet_name="Biscuit"))

    print("\n===== Today's Schedule =====")
    scheduler.build_plan()
    print(scheduler.explain())

    # --- Conflict detection demo ----------------------------------------
    # build_plan packs tasks back-to-back, so it never overlaps. To exercise
    # the detector we place two tasks at the SAME start time (08:00) as if they
    # had fixed times, then let the scheduler warn about it.
    print("\n===== Conflict Check =====")
    clash = [
        ScheduledTask(mochi, Task("Feeding", 10, "high"), start_minute=8 * 60),
        ScheduledTask(biscuit, Task("Morning walk", 30, "high"), start_minute=8 * 60),
    ]
    warning = scheduler.conflict_warning(clash)
    print(warning if warning else "No conflicts detected.")


if __name__ == "__main__":
    main()
