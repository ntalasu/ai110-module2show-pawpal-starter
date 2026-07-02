import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task


def _fmt(minute):
    """Render minutes-since-midnight as HH:MM (e.g. 480 -> '08:00')."""
    return f"{minute // 60:02d}:{minute % 60:02d}"


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# --- Persistent state ("the vault") -------------------------------------
# Streamlit reruns this whole script on every interaction, so build our
# Owner + Pet once and keep them in session_state. Guard with `not in` so we
# only create them on the first load and reuse them (with their tasks) after.
if "owner" not in st.session_state:
    owner = Owner("Jordan")
    owner.add_pet(Pet("Mochi", species="cat"))  # start with one pet
    st.session_state.owner = owner

owner = st.session_state.owner

st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)

available = st.slider(
    "Minutes available today", min_value=15, max_value=480, value=120, step=15
)
owner.set_availability(8 * 60, 8 * 60 + int(available))  # care window starts at 08:00

# --- Add a Pet ----------------------------------------------------------
# The form data is handled by Owner.add_pet(). Because `owner` lives in
# session_state, the new Pet persists; Streamlit reruns the script and the
# selectbox/plan below re-read owner.list_pets(), so the change shows up.
st.subheader("Add a Pet")
with st.form("add_pet", clear_on_submit=True):
    new_pet_name = st.text_input("Pet name", value="")
    new_pet_species = st.selectbox("Species", ["dog", "cat", "other"])
    if st.form_submit_button("Add pet") and new_pet_name.strip():
        owner.add_pet(Pet(new_pet_name.strip(), species=new_pet_species))

pets = owner.list_pets()

st.markdown("### Tasks")
st.caption("Pick a pet, then add tasks — each becomes a Task object attached to it.")

pet = st.selectbox("Pet", pets, format_func=lambda p: f"{p.name} ({p.species})")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

if st.button("Add task"):
    pet.add_task(Task(task_title, duration_minutes=int(duration), priority=priority))

tasks = pet.get_tasks()
scheduler = Scheduler(owner)

st.markdown("#### Current tasks")
if tasks:
    # Let the owner filter by status, then show tasks in the scheduler's own
    # priority order so the table previews how they'll be scheduled.
    status_choice = st.radio(
        "Show", ["All", "To do", "Done"], horizontal=True, index=0
    )
    done_filter = {"All": None, "To do": False, "Done": True}[status_choice]
    ordered = scheduler.sort_tasks(
        scheduler.filter_tasks(done=done_filter, pet_name=pet.name)
    )

    if ordered:
        st.table(
            [
                {
                    "Priority": it.task.priority,
                    "Task": it.task.title,
                    "Duration (min)": it.task.duration_minutes,
                    "Status": "✅ done" if it.task.done else "⏳ to do",
                }
                for it in ordered
            ]
        )
        st.caption(
            "Sorted by the scheduler: priority first, shorter tasks break ties."
        )
    else:
        st.info(f"No {status_choice.lower()} tasks for {pet.name}.")
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Runs the Scheduler over your pet's tasks within the available time.")

if st.button("Generate schedule"):
    if not tasks:
        st.warning("Add at least one task first.")
    else:
        plan = scheduler.build_plan()

        # --- Conflicts first: the most actionable thing an owner needs to see.
        # Presented up top as a warning (not an error) with the clashing tasks,
        # their times, and a concrete next step — so the owner knows what to fix.
        conflicts = scheduler.detect_conflicts()
        if conflicts:
            lines = ["**⚠️ Two care tasks overlap in time:**", ""]
            for earlier, later in conflicts:
                scope = (
                    "same pet"
                    if earlier.pet is later.pet
                    else f"{earlier.pet.name} & {later.pet.name}"
                )
                lines.append(
                    f"- **{earlier.task.title}** "
                    f"({_fmt(earlier.start_minute)}–{_fmt(earlier.end_minute)}) "
                    f"overlaps **{later.task.title}** "
                    f"({_fmt(later.start_minute)}–{_fmt(later.end_minute)}) — {scope}"
                )
            lines += ["", "_Shorten or move one task, or add more time to your day._"]
            st.warning("\n".join(lines))
        elif plan:
            st.success("No scheduling conflicts — every task has its own time slot.")

        st.markdown("#### Today's Schedule")
        if plan:
            total = sum(item.task.duration_minutes for item in plan)
            st.success(
                f"Scheduled {len(plan)} of {len(tasks)} task(s) — "
                f"{total} of {owner.available_minutes()} min used."
            )
            st.table(
                [
                    {
                        "Time": f"{_fmt(item.start_minute)}–{_fmt(item.end_minute)}",
                        "Task": item.task.title,
                        "Duration (min)": item.task.duration_minutes,
                        "Priority": item.task.priority,
                        "Pet": item.pet.name,
                    }
                    for item in plan
                ]
            )
        else:
            st.info("Nothing fit in the available time.")

        skipped = [d for d in scheduler.decisions if not d.included]
        if skipped:
            st.markdown("#### Didn't fit today")
            st.warning(
                "These tasks were skipped because the day filled up:\n\n"
                + "\n".join(f"- **{d.task.title}** — {d.reason}" for d in skipped)
            )

        with st.expander("Plain-text explanation"):
            st.code(scheduler.explain())
