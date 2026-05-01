import streamlit as st
import pandas as pd
import time
from db   import (get_goals, create_goal, add_log, get_logs,
                  compute_status, compute_wellbeing, compute_insight,
                  compute_patterns, compute_weekly_report)
from auth import decode_token

st.set_page_config(page_title="LifeOS — Dashboard", layout="wide", initial_sidebar_state="expanded")

# ── AUTH GUARD ───────────────────────────────────────────
if "user_id" not in st.session_state or not st.session_state.user_id:
    if "token" in st.session_state and st.session_state.token:
        uid = decode_token(st.session_state.token)
        if uid:
            st.session_state.user_id = uid
        else:
            st.switch_page("app.py")
    else:
        st.switch_page("app.py")

user_id  = st.session_state.user_id
username = st.session_state.get("username", "User")

# ── STYLES ───────────────────────────────────────────────
st.markdown("""
<style>
body,[data-testid="stAppViewContainer"],[data-testid="stAppViewContainer"]>.main {
    background:#0e1117 !important; color:#f1f5f9;
}
[data-testid="stHeader"],[data-testid="stToolbar"],
[data-testid="stDecoration"],#MainMenu,footer { display:none !important; }
.block-container { padding-top:1.5rem !important; }
.stMetric { background:rgba(255,255,255,0.05);padding:15px;
    border-radius:15px;backdrop-filter:blur(10px);
    box-shadow:0 0 15px rgba(0,0,0,0.3); }
div[data-testid="stButton"] > button {
    border-radius:10px !important;
    background:linear-gradient(90deg,#00ffd5,#00aaff) !important;
    color:#030712 !important;font-weight:600 !important;border:none !important;
}
h1,h2,h3 { color:#00ffd5 !important; }
.priority-box { background:linear-gradient(90deg,#ff4d4d22,#ff000011);
    border:1px solid #ff4d4d55;padding:20px;border-radius:15px;
    color:#ff6b6b;font-size:18px;font-weight:600;
    box-shadow:0 0 20px rgba(255,0,0,0.15); }
</style>
""", unsafe_allow_html=True)

# ── HEADER ───────────────────────────────────────────────
col_title, col_user = st.columns([5, 1])
with col_title:
    st.title("🧠 Life OS — AI Goal Engine")
with col_user:
    st.markdown(f"**👤 {username}**")
    if st.button("Logout"):
        for key in ["token", "user_id", "username"]:
            st.session_state[key] = None
        st.switch_page("app.py")

st.divider()

# ── SIDEBAR — CREATE GOAL ────────────────────────────────
with st.sidebar:
    st.header("➕ New Goal")
    g_name     = st.text_input("Goal Name")
    g_target   = st.number_input("Target (total units)", min_value=1, value=100)
    g_deadline = st.date_input("Deadline")

    if st.button("Create Goal", use_container_width=True):
        if not g_name.strip():
            st.warning("Enter a goal name")
        else:
            create_goal(user_id, g_name.strip(), g_target, g_deadline)
            st.success("✅ Goal Created!")
            st.rerun()

    st.divider()
    st.caption("LifeOS v1 · Beta")

# ── LOAD GOALS ───────────────────────────────────────────
goals = get_goals(user_id)

if not goals:
    st.warning("No goals yet — create one in the sidebar ←")
    st.stop()

goal_map  = {f"{g['name']} (ID:{g['id']})": g for g in goals}
selected  = st.multiselect("🎯 Select Goals to View", list(goal_map.keys()))

if not selected:
    st.info("👆 Select one or more goals above to see your dashboard")
    st.stop()

selected_goals = [goal_map[s] for s in selected]
selected_ids   = [g["id"] for g in selected_goals]

# ── CACHE LOGS & STATUS ──────────────────────────────────
@st.cache_data(ttl=30)
def cached_logs(goal_id, uid):
    return get_logs(goal_id, uid)

@st.cache_data(ttl=30)
def cached_status(goal_id, uid):
    logs = get_logs(goal_id, uid)
    goal = next((g for g in get_goals(uid) if g["id"] == goal_id), None)
    if not goal:
        return None
    return compute_status(goal, logs)

# ── OVERALL SUMMARY ──────────────────────────────────────
st.subheader("📊 Overall Summary")
cols = st.columns(len(selected_goals))
for i, g in enumerate(selected_goals):
    s = cached_status(g["id"], user_id)
    if not s:
        continue
    with cols[i]:
        st.metric(g["name"],       f"{s['progress']}%",          "progress")
        st.metric("Status",         s["status"])
        st.metric("Success Prob",  f"{s['success_probability']}%")

st.divider()

# ── PRIORITY ENGINE ──────────────────────────────────────
priority_data = []
for g in selected_goals:
    s    = cached_status(g["id"], user_id)
    logs = cached_logs(g["id"], user_id)
    if not s:
        continue
    done_vals   = [l["done"] for l in logs[-7:]]
    consistency = sum(1 for x in done_vals if x > 0) / max(len(done_vals), 1)
    last_screen = logs[-1].get("screen_time", 0) if logs else 0
    score       = (s["required_per_day"] * 2
                   - s["current_avg"]
                   + (1 - consistency) * 5
                   + last_screen / 50)
    priority_data.append({"goal": g, "score": score, "status": s})

if priority_data:
    worst = max(priority_data, key=lambda x: x["score"])
    st.subheader("🧠 Priority Focus")
    st.markdown(f"""
    <div class="priority-box">
    🚨 <b>Focus on:</b> {worst['goal']['name']}
    &nbsp;&nbsp;·&nbsp;&nbsp; Prob: {worst['status']['success_probability']}%
    &nbsp;&nbsp;·&nbsp;&nbsp; Avg: {worst['status']['current_avg']} / Need: {worst['status']['required_per_day']}
    </div>
    """, unsafe_allow_html=True)
    st.caption("This goal needs the most attention right now")
    st.divider()

# ── DETAILED VIEW ────────────────────────────────────────
goal_labels  = {g["id"]: g["name"] for g in selected_goals}
selected_gid = st.selectbox("🎯 Detailed View — Select Goal",
                             selected_ids,
                             format_func=lambda gid: goal_labels.get(gid, str(gid)))

goal      = next(g for g in selected_goals if g["id"] == selected_gid)
logs      = cached_logs(selected_gid, user_id)
status    = cached_status(selected_gid, user_id)

if not status:
    st.error("Failed to compute status")
    st.stop()

st.header(f"🎯 {goal['name']}")

# ── METRICS ROW ──────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("📈 Progress",     f"{status['progress']}%")
c2.metric("⚡ Required/Day", round(status["required_per_day"], 1))
c3.metric("🔥 Current Avg",  round(status["current_avg"], 1))
c4.metric("🎯 Status",       status["status"])

# ── PREDICTION ───────────────────────────────────────────
st.subheader("🔮 AI Prediction")
prob = status["success_probability"]
if prob > 70:
    st.success(f"🚀 Success Probability: **{prob}%** — You're on track!")
elif prob > 40:
    st.warning(f"⚠️ Success Probability: **{prob}%** — Needs improvement")
else:
    st.error(f"💀 Success Probability: **{prob}%** — High risk, act now!")

# ── PREDICTION EXPLANATION ───────────────────────────────
if status.get("reasons"):
    st.markdown("**❌ Issues:**")
    for r in status["reasons"]:
        st.error(r)
if status.get("positives"):
    st.markdown("**✅ Strengths:**")
    for p in status["positives"]:
        st.success(p)

st.divider()

# ── WELLBEING ────────────────────────────────────────────
wb = compute_wellbeing(logs)
st.subheader("🧠 Well-being Score")
col_wb1, col_wb2 = st.columns([1, 2])
with col_wb1:
    score = wb["score"]
    st.metric("Score", f"{score}/100")
    if score > 70:   st.success("🟢 Good condition")
    elif score > 40: st.warning("🟡 Moderate condition")
    else:            st.error("🔴 Needs attention")
with col_wb2:
    for s in wb.get("suggestions", []):
        st.info(f"👉 {s}")

st.divider()

# ── LOG FORM ─────────────────────────────────────────────
st.subheader("⏱️ Log This Hour")
st.caption("Log every hour — accuracy improves with more data")

col_a, col_b = st.columns(2)
with col_a:
    mood        = st.slider("Mood (1-5)",   1, 5, 3)
    energy      = st.slider("Energy (1-5)", 1, 5, 3)
    stress      = st.slider("Stress (1-5)", 1, 5, 3)
with col_b:
    sleep       = st.number_input("Sleep today (hrs)", 0.0, 24.0, 7.0, 0.5)
    done        = st.number_input("Work done (units)", min_value=0, value=0)
    screen_time = st.number_input("Screen time (min)",  min_value=0, value=0)

if st.button("✅ Save Log", use_container_width=True):
    add_log(selected_gid, user_id, done, mood, energy, screen_time, stress, sleep)
    st.success("✅ Saved!")
    st.cache_data.clear()
    st.rerun()

st.divider()

# ── ACTION PLAN ──────────────────────────────────────────
st.subheader("🎯 What to do right now")
actions = []
if status["current_avg"] < status["required_per_day"]:
    actions.append(f"Increase effort to {round(status['required_per_day'], 1)} units/day")
if logs and logs[-1].get("screen_time", 0) > 60:
    actions.append("Reduce screen time by at least 30 minutes")
actions += wb.get("suggestions", [])
actions = list(dict.fromkeys(actions))

if not actions:
    st.success("🚀 You're on track — keep going!")
else:
    for a in actions:
        st.info(f"👉 {a}")

st.divider()

# ── CHARTS ───────────────────────────────────────────────
if logs:
    df = pd.DataFrame(logs)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    st.subheader("📈 Charts")
    view_type = st.selectbox("View", ["Daily", "Cumulative", "Weekly"])

    required  = status["required_per_day"]
    target_v  = goal.get("target")
    deadline_v = goal.get("deadline")

    if view_type == "Daily":
        df["required"] = required
        st.line_chart(df[["date", "done", "required"]].set_index("date"), height=300)

    elif view_type == "Cumulative":
        df["cumulative"]   = df["done"].cumsum()
        df["required_cum"] = [(i + 1) * required for i in range(len(df))]

        avg       = status["current_avg"]
        last_date = df["date"].max()
        total_done = df["cumulative"].iloc[-1]
        future_dates, predicted = [], []
        current_total = total_done

        for i in range(1, 91):
            nd = last_date + pd.Timedelta(days=i)
            current_total += avg
            future_dates.append(nd)
            predicted.append(current_total)
            if target_v and current_total >= target_v:
                break

        pred_df   = pd.DataFrame({"date": future_dates, "predicted": predicted})
        chart_df  = pd.concat([
            df[["date", "cumulative", "required_cum"]],
            pred_df
        ]).sort_values("date").set_index("date")

        st.line_chart(chart_df, height=300)
        st.caption("cumulative = actual · required_cum = pace line · predicted = forecast")

        if target_v:
            reached = pred_df[pred_df["predicted"] >= target_v]
            if len(reached) > 0:
                comp_date = reached.iloc[0]["date"].date()
                st.success(f"📅 Predicted completion: **{comp_date}**")
                if deadline_v:
                    dl = pd.to_datetime(deadline_v).date()
                    diff = (dl - comp_date).days
                    if diff > 0:    st.success(f"🚀 {diff} days ahead of deadline!")
                    elif diff == 0: st.warning("⚖️ Exactly on deadline")
                    else:           st.error(f"⚠️ {abs(diff)} days behind deadline")
            else:
                st.error("❌ At current pace, goal won't be completed in time")

        # ── PLANNING ENGINE ──────────────────────────────
        if target_v and deadline_v:
            dl_date   = pd.to_datetime(deadline_v)
            today_dt  = df["date"].max()
            days_left = (dl_date - today_dt).days
            if days_left > 0:
                done_so_far = df["cumulative"].iloc[-1]
                remaining   = target_v - done_so_far
                if remaining > 0:
                    req_now      = remaining / days_left
                    cur_avg      = status["current_avg"]
                    gap          = req_now - cur_avg
                    last_screen  = logs[-1].get("screen_time", 0) if logs else 0
                    focus_factor = 0.8 if last_screen > 60 else 1.0
                    last_done    = logs[-1]["done"] if logs else cur_avg
                    momentum     = 1.1 if last_done >= cur_avg else 0.9
                    today_target = req_now * focus_factor * momentum
                    session_size = round(today_target / 4, 1)

                    st.subheader("⚡ Planning Engine")
                    p1, p2 = st.columns(2)
                    with p1:
                        st.markdown("### 📊 Catch-up Plan")
                        st.metric("Needed/day",   round(req_now, 1))
                        st.metric("Current avg",  round(cur_avg, 1))
                        if gap > 0: st.warning(f"Increase by {round(gap,1)}/day")
                        else:       st.success("Ahead of pace!")
                    with p2:
                        st.markdown("### 🤖 Today's Target")
                        st.metric("Today Target", round(today_target, 1))
                        st.caption(f"4 sessions × {session_size} units each")
                        if last_screen > 60: st.warning("Reduce screen time first")
                        else:                st.success("Deep focus mode — go!")
                else:
                    st.success("🎉 Goal already completed!")

    else:  # Weekly
        df_w = df.resample("W", on="date")["done"].sum()
        st.bar_chart(df_w, height=300)

else:
    st.info("No logs yet — start logging above")

st.divider()

# ── POMODORO TIMER ───────────────────────────────────────
st.subheader("🍅 Focus Timer")

if "timers" not in st.session_state:
    st.session_state.timers = []

with st.expander("➕ New Timer"):
    t_label  = st.text_input("Name",         value="Focus Session", key="t_label")
    t_focus  = st.number_input("Focus (min)", value=25, min_value=1, key="t_focus")
    t_break  = st.number_input("Break (min)", value=5,  min_value=1, key="t_break")
    t_loop   = st.checkbox("🔁 Loop mode",   key="t_loop")
    if st.button("Add Timer"):
        st.session_state.timers.append({
            "label": t_label, "focus": t_focus, "break": t_break,
            "mode": "focus", "duration": t_focus * 60,
            "start_time": None, "running": False,
            "loop": t_loop, "switched": False
        })
        st.success("Timer added!")

for i, t in enumerate(st.session_state.timers):
    st.divider()
    st.subheader(f"⏱️ {t['label']}")
    if t.get("running") and t.get("start_time"):
        elapsed   = int(time.time() - t["start_time"])
        time_left = max(t["duration"] - elapsed, 0)
    else:
        time_left = t.get("duration", 0)

    mins, secs = time_left // 60, time_left % 60
    st.markdown(f"### {mins:02d}:{secs:02d}")
    st.caption(f"Mode: **{t.get('mode','focus').upper()}**")

    col1, col2, col3 = st.columns(3)
    if col1.button("▶️ Start",  key=f"st_{i}"):
        t["running"] = True; t["start_time"] = time.time()
    if col2.button("⏸️ Pause",  key=f"pa_{i}"):
        if t.get("running") and t.get("start_time"):
            t["duration"] = max(t["duration"] - int(time.time() - t["start_time"]), 0)
        t["running"] = False; t["start_time"] = None
    if col3.button("🔄 Reset",  key=f"re_{i}"):
        t.update({"running": False, "switched": False, "mode": "focus",
                  "duration": t["focus"] * 60, "start_time": None})

    if time_left == 0 and t.get("running") and not t.get("switched"):
        t["switched"] = True
        if t["mode"] == "focus":
            st.success("🎉 Focus done → Break time!")
            t["mode"] = "break"; t["duration"] = t["break"] * 60
        else:
            st.success("🔥 Break done → Back to focus!")
            if t["loop"]:
                t["mode"] = "focus"; t["duration"] = t["focus"] * 60
            else:
                t["running"] = False
        t["start_time"] = time.time()

st.divider()

# ── SCREEN TIME ──────────────────────────────────────────
st.subheader("📱 Screen Time")
last_sc = logs[-1].get("screen_time", 0) if logs else 0
st.metric("Last Logged", f"{last_sc} min")
if last_sc > 60:   st.error("🚫 High distraction — reduce screen time now")
elif last_sc > 30: st.warning("⚠️ Moderate distraction")
else:              st.success("✅ Good focus level")

st.divider()

# ── STREAK & HEATMAP ─────────────────────────────────────
if logs:
    st.subheader("🔥 Consistency")
    done_vals = [l["done"] for l in logs]
    streak = 0
    for val in reversed(done_vals):
        if val > 0: streak += 1
        else: break
    st.metric("Current Streak (days)", streak)

    df2 = pd.DataFrame(logs)
    df2["date"] = pd.to_datetime(df2["date"])
    last30 = df2.tail(30)[["date", "done"]].set_index("date")
    st.caption("Last 30 days activity — darker = more work done")
    st.dataframe(last30.style.background_gradient(cmap="viridis"))

st.divider()

# ── PATTERNS ─────────────────────────────────────────────
st.subheader("📊 Behavior Patterns")
patterns = compute_patterns(logs)
if patterns:
    for p in patterns:
        st.info(f"📌 {p}")
else:
    st.info("Log for at least 5 days to see patterns")

st.divider()

# ── AI INSIGHT ───────────────────────────────────────────
st.subheader("🧠 AI Insight")
ins = compute_insight(goal, logs)
st.warning(f"📌 {ins['explanation']}")
st.success(f"✅ {ins['suggestion']}")

st.divider()

# ── WEEKLY REPORT ────────────────────────────────────────
st.subheader("📊 Weekly Report")
rep = compute_weekly_report(logs)
if rep:
    r1, r2, r3 = st.columns(3)
    r1.metric("Total Done",      rep["total_done"])
    r2.metric("Avg/Day",         rep["avg_per_day"])
    r3.metric("Current Streak",  rep["streak"])
    r1.metric("Missed Days",     rep["missed_days"])
    r2.metric("Avg Screen Time", rep["avg_screen_time"])
    r3.metric("Best Day",        rep["best_day"])

    if   rep["risk"] == "Low":    st.success("🟢 Low Risk Week")
    elif rep["risk"] == "Medium": st.warning("🟡 Medium Risk Week")
    else:                         st.error("🔴 High Risk Week")

    for s in rep.get("summary", []):
        st.info(f"📌 {s}")
else:
    st.info("Not enough data yet")
