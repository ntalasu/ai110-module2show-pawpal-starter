import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

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
if tasks:
    st.write("Current tasks:")
    st.table(
        [
            {"title": t.title, "duration_minutes": t.duration_minutes, "priority": t.priority}
            for t in tasks
        ]
    )
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Runs the Scheduler over your pet's tasks within the available time.")

if st.button("Generate schedule"):
    if not tasks:
        st.warning("Add at least one task first.")
    else:
        scheduler = Scheduler(owner)
        plan = scheduler.build_plan()

        st.markdown("#### Today's Schedule")
        if plan:
            def _fmt(minute):
                return f"{minute // 60:02d}:{minute % 60:02d}"

            for item in plan:
                st.markdown(
                    f"- **{_fmt(item.start_minute)}** — {item.task.title} "
                    f"({item.task.duration_minutes} min) "
                    f"·  priority: {item.task.priority}  ·  for {item.pet.name}"
                )
        else:
            st.info("Nothing fit in the available time.")

        skipped = [d for d in scheduler.decisions if not d.included]
        if skipped:
            st.markdown("#### Skipped")
            for d in skipped:
                st.markdown(f"- {d.task.title} — {d.reason}")

        with st.expander("Plain-text explanation"):
            st.code(scheduler.explain())
