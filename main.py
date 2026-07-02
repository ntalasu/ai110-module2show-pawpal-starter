"""PawPal+ — command-line demo.

Builds a small owner/pets/tasks setup and prints today's schedule.
Run with:  python main.py
"""

from pawpal_system import Owner, Pet, Scheduler, Task


def main() -> None:
    # 1. Create the owner and their daily care window (08:00–10:00 = 120 min).
    owner = Owner("Jordan")
    owner.set_availability(8 * 60, 10 * 60)

    # 2. Create at least two pets.
    mochi = Pet("Mochi", species="cat", notes="shy, needs meds after food")
    biscuit = Pet("Biscuit", species="dog", notes="high energy")

    # 3. Add at least three tasks with different durations and priorities.
    mochi.add_task(Task("Feeding", duration_minutes=10, priority="high", frequency="daily"))
    mochi.add_task(Task("Litter change", duration_minutes=15, priority="medium"))

    biscuit.add_task(Task("Morning walk", duration_minutes=30, priority="high", frequency="daily"))
    biscuit.add_task(Task("Enrichment play", duration_minutes=20, priority="medium"))
    biscuit.add_task(Task("Grooming", duration_minutes=45, priority="low", frequency="weekly"))

    owner.add_pet(mochi)
    owner.add_pet(biscuit)

    # 4. Build and print today's schedule.
    scheduler = Scheduler(owner)
    scheduler.build_plan()

    print(f"===== Today's Schedule for {owner.name} =====")
    print(scheduler.explain())


if __name__ == "__main__":
    main()
