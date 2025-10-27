# app.py — Smart Goals Tracker (goal-agnostic, tabbed UI, cohesive progress controls)

import os, json
from pathlib import Path
from datetime import date, timedelta
import streamlit as st
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px

#  Load environment early and verify
dotenv_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path)
print("DEBUG: .env loaded from", dotenv_path)
print("DEBUG: API key starts with:", str(os.getenv("OPENAI_API_KEY"))[:10])

from db import (
    init_db, create_goal, list_goals, delete_goal,
    add_steps, get_steps, update_step,
    checkin, delete_checkin, get_checkins,
    compute_streak_strict, compute_streak_friendly
)
from gpt import generate_plan, weekly_summary, short_quote
from utils import parse_date, today_ymd, upcoming_days
from report import build_pdf

# ---------- App bootstrap ----------
st.set_page_config(page_title="Smart Goals Tracker", page_icon="🎯", layout="wide")
load_dotenv()
init_db()

if "selected_goal_id" not in st.session_state:
    st.session_state.selected_goal_id = None
if "summary_text" not in st.session_state:
    st.session_state.summary_text = None
if "streak_mode" not in st.session_state:
    st.session_state.streak_mode = "Friendly"  # "Friendly" | "Strict"

# ---------- Header ----------
st.title("🎯 Smart Goals Tracker")
st.caption("Turn any goal into a clear, trackable plan with streaks, insights, and PDF exports.")

# ---------- Top bar: goal select/create ----------
left, mid, right = st.columns([3, 4, 2], vertical_alignment="center")

with left:
    goals = list_goals()
    goal_labels = [f"{g['id']} • {g['title']}" for g in goals]
    selected_label = st.selectbox("Select a goal", goal_labels, index=0 if goals else None, key="goal_select")
    goal_id = None
    if selected_label:
        goal_id = int(selected_label.split(" • ", 1)[0])
        st.session_state.selected_goal_id = goal_id

with mid:
    with st.expander("➕ Create a new goal", expanded=not bool(goals)):
        new_title = st.text_input("Goal title", placeholder="e.g., Launch my portfolio website", key="new_goal_title")
        deadline = st.date_input("Optional deadline", value=None, format="YYYY-MM-DD", key="new_goal_deadline")
        colA, colB = st.columns([1,1])
        with colA:
            if st.button("Create goal", use_container_width=True):
                if new_title.strip():
                    new_id = create_goal(new_title.strip(), deadline.isoformat() if deadline else None)
                    st.success("Goal created.")
                    st.session_state.selected_goal_id = new_id
                    st.rerun()
                else:
                    st.error("Please enter a goal title.")
        with colB:
            if st.button("Generate plan with AI 🤖", help="Creates 6–8 actionable steps", use_container_width=True):
                if new_title.strip():
                    steps = generate_plan(new_title.strip(), deadline.isoformat() if deadline else None)
                    new_id = create_goal(new_title.strip(), deadline.isoformat() if deadline else None)
                    add_steps(new_id, steps)
                    st.success("Goal and steps created via AI.")
                    st.session_state.selected_goal_id = new_id
                    st.rerun()
                else:
                    st.error("Please enter a goal title first.")

with right:
    if goal_id:
        if st.button("🗑️ Delete selected goal", type="secondary"):
            delete_goal(goal_id)
            st.warning("Goal deleted.")
            st.session_state.selected_goal_id = None
            st.rerun()

# No goals yet
if not st.session_state.selected_goal_id:
    st.stop()

goal_id = st.session_state.selected_goal_id

# ---------- Sidebar: Plan Overview (sticky) ----------
with st.sidebar:
    st.header("📋 Plan Overview")
    steps_df = pd.DataFrame(get_steps(goal_id))
    if not steps_df.empty:
        next_steps = steps_df[steps_df["done"] == 0].sort_values(["due_date", "order_index"]).head(3)
        for _, row in next_steps.iterrows():
            st.markdown(f"**• {row['title']}** — {row['detail'] or '—'}")
            if row.get("due_date"):
                st.caption(f"Due: {row['due_date']}")
        st.divider()
        st.subheader("📆 Next 14 days")
        road = upcoming_days(14)
        # Simple text schedule
        for d in road:
            due = steps_df[(steps_df["due_date"] == d) & (steps_df["done"] == 0)]
            if not due.empty:
                st.write(f"**{d}**")
                for _, r in due.iterrows():
                    st.caption(f"• {r['title']} ({r['metric'] or 'metric N/A'})")
    else:
        st.info("No steps yet. Add steps on the **Plan** tab or regenerate with AI.")

    st.divider()
    st.caption("Tip: Keep steps small and measurable. Try a daily 20–40 minute cadence.")

# ---------- Tabs ----------
tab_plan, tab_progress, tab_insights = st.tabs(["🛠️ Plan", "📈 Progress", "🧠 Insights"])

# ====== PLAN TAB ======
with tab_plan:
    st.subheader("Edit plan")
    steps_raw = get_steps(goal_id)
    steps_df = pd.DataFrame(steps_raw)

    # Ensure stable columns
    cols = ["id","order_index","title","detail","metric","duration_min","why","due_date","done"]
    for c in cols:
        if c not in steps_df.columns:
            steps_df[c] = None
    steps_df = steps_df[cols].sort_values(["order_index","due_date"]).reset_index(drop=True)

    edited = st.data_editor(
        steps_df,
        key=f"editor-{goal_id}",
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "order_index": st.column_config.NumberColumn("Order", help="Drag or edit for sequencing", width="small"),
            "title": st.column_config.TextColumn("Step (actionable)"),
            "detail": st.column_config.TextColumn("How to (detail)"),
            "metric": st.column_config.TextColumn("Metric"),
            "duration_min": st.column_config.NumberColumn("Duration (min)"),
            "why": st.column_config.TextColumn("Why it matters"),
            "due_date": st.column_config.DateColumn("Due date", format="YYYY-MM-DD"),
            "done": st.column_config.CheckboxColumn("Done")
        }
    )

    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("💾 Save changes", key=f"save-{goal_id}"):
            # upsert rows
            for _, row in edited.iterrows():
                update_step(
                    step_id=row["id"],
                    goal_id=goal_id,
                    order_index=int(row["order_index"]) if pd.notna(row["order_index"]) else 0,
                    title=(row["title"] or "").strip(),
                    detail=(row["detail"] or "").strip(),
                    metric=(row["metric"] or "").strip(),
                    duration_min=int(row["duration_min"]) if pd.notna(row["duration_min"]) else None,
                    why=(row["why"] or "").strip(),
                    due_date=row["due_date"].isoformat() if pd.notna(row["due_date"]) else None,
                    done=int(row["done"] or 0)
                )
            st.success("Plan saved.")
    with col2:
        if st.button("🔁 Regenerate detailed plan (keep dates & done)"):
            # get title/deadline
            title = [g["title"] for g in list_goals() if g["id"] == goal_id][0]
            deadline = [g.get("deadline") for g in list_goals() if g["id"] == goal_id][0]
            new_steps = generate_plan(title, deadline)
            # keep user-set dates and done statuses if titles match (best effort)
            existing = { (s["title"] or "").strip().lower(): s for s in get_steps(goal_id) }
            merged = []
            for i, s in enumerate(new_steps, start=1):
                tkey = (s["title"] or "").strip().lower()
                keep = existing.get(tkey, {})
                merged.append({
                    **s,
                    "due_date": keep.get("due_date"),
                    "done": keep.get("done", 0),
                    "order_index": keep.get("order_index", i)
                })
            add_steps(goal_id, merged, replace=True)
            st.success("Plan regenerated.")
            st.rerun()

# ====== PROGRESS TAB ======
with tab_progress:
    st.subheader("Daily streak")

    # Controls + streak together
    c1, c2, c3 = st.columns([1,1,2])
    with c1:
        if st.button("I worked on this today ✅", key=f"checkin-{goal_id}", use_container_width=True):
            checkin(goal_id, today_ymd())
            st.rerun()
        if st.button("Undo today ❌", key=f"undo-{goal_id}", use_container_width=True):
            delete_checkin(goal_id, today_ymd())
            st.rerun()
    with c2:
        st.selectbox("Streak mode", ["Friendly","Strict"], key="streak_mode", help="Friendly allows yesterday as anchor if you missed today.")
        if st.session_state.streak_mode == "Friendly":
            streak = compute_streak_friendly(goal_id)
        else:
            streak = compute_streak_strict(goal_id)
        st.metric("Current streak (days)", streak)

    with c3:
        # Chart right next to controls
        checks = get_checkins(goal_id)  # list of {"day": "YYYY-MM-DD"}
        df = pd.DataFrame(checks)
        if df.empty:
            st.info("No check-ins yet. Log your first day above.")
        else:
            df["day"] = pd.to_datetime(df["day"])
            df["value"] = 1
            fig = px.bar(df.sort_values("day"), x="day", y="value", title="Check-ins over time")
            fig.update_yaxes(showticklabels=False)
            fig.update_layout(margin=dict(l=0,r=0,t=40,b=0), height=260)
            st.plotly_chart(fig, use_container_width=True, key=f"chart-{goal_id}")

# ====== INSIGHTS TAB ======
with tab_insights:
    st.subheader("AI insights & export")
    colA, colB = st.columns([1,1])
    with colA:
        if st.button("Generate weekly summary 🧠", key=f"summary-{goal_id}", use_container_width=True):
            steps = get_steps(goal_id)
            st.session_state.summary_text = weekly_summary(steps, get_checkins(goal_id))
        if st.session_state.summary_text:
            st.write(st.session_state.summary_text)
        else:
            st.caption("Click **Generate weekly summary** to get an AI recap of progress.")
        st.write(short_quote())

    with colB:
        steps = get_steps(goal_id)
        # choose current streak based on mode
        s_val = compute_streak_friendly(goal_id) if st.session_state.streak_mode == "Friendly" else compute_streak_strict(goal_id)
        if st.button("Export progress PDF 📄", key=f"pdf-{goal_id}", use_container_width=True):
            title = [g["title"] for g in list_goals() if g["id"] == goal_id][0]
            pdf = build_pdf(title, s_val, steps, st.session_state.summary_text)
            st.download_button(
                "Download report",
                data=pdf,
                file_name="progress_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

st.divider()
st.caption("Built with Streamlit, SQLite, and OpenAI. © 2025")
