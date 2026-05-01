import streamlit as st
import pandas as pd
import time
from db   import (get_goals, create_goal, add_log, get_logs,
                  compute_status, compute_wellbeing, compute_insight,
                  compute_patterns, compute_weekly_report)
from auth import decode_token

st.set_page_config(page_title="LifeOS · Dashboard", layout="wide", initial_sidebar_state="expanded")

# ── AUTH GUARD ───────────────────────────────────────────
if "user_id" not in st.session_state or not st.session_state.user_id:
    if st.session_state.get("token"):
        uid = decode_token(st.session_state.token)
        if uid: st.session_state.user_id = uid
        else:   st.switch_page("app.py")
    else:
        st.switch_page("app.py")

user_id  = st.session_state.user_id
username = st.session_state.get("username", "User")

# ── GLOBAL STYLES ────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Instrument+Serif:ital@1&display=swap');

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main {
    background: #0c0c0f !important;
    font-family: 'Inter', sans-serif !important;
    color: #e4e4e7 !important;
}

[data-testid="stHeader"],[data-testid="stToolbar"],
[data-testid="stDecoration"],#MainMenu,footer { display:none !important; }

.block-container { padding: 0 !important; max-width: 100% !important; }

/* ─ SIDEBAR ─ */
[data-testid="stSidebar"] {
    background: #111113 !important;
    border-right: 1px solid #1c1c1f !important;
}
[data-testid="stSidebar"] .block-container {
    padding: 28px 20px !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #fafafa !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    letter-spacing: -0.2px !important;
}

/* ─ INPUTS ─ */
div[data-testid="stTextInput"] > label,
div[data-testid="stNumberInput"] > label,
div[data-testid="stDateInput"] > label,
div[data-testid="stSelectbox"] > label,
div[data-testid="stMultiSelect"] > label,
div[data-testid="stSlider"] > label {
    font-size: 12px !important; font-weight: 500 !important;
    color: #52525b !important; letter-spacing: 0.03em !important;
}
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input {
    background: #0c0c0f !important;
    border: 1px solid #27272a !important;
    border-radius: 8px !important;
    color: #fafafa !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stNumberInput"] input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.1) !important;
}

/* ─ BUTTONS ─ */
div[data-testid="stButton"] > button {
    background: #6366f1 !important;
    color: #fff !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important; font-size: 13px !important;
    border: none !important; border-radius: 8px !important;
    padding: 9px 18px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.5) !important;
    transition: all 0.15s !important;
}
div[data-testid="stButton"] > button:hover {
    background: #5558e3 !important;
    box-shadow: 0 4px 12px rgba(99,102,241,0.3) !important;
    transform: translateY(-1px) !important;
}

/* ─ SELECTBOX / MULTISELECT ─ */
div[data-baseweb="select"] > div,
div[data-baseweb="select"] input {
    background: #111113 !important;
    border-color: #27272a !important;
    color: #e4e4e7 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    border-radius: 8px !important;
}

/* ─ METRICS ─ */
div[data-testid="stMetric"] {
    background: #111113 !important;
    border: 1px solid #1c1c1f !important;
    border-radius: 12px !important;
    padding: 16px 20px !important;
}
div[data-testid="stMetricLabel"] {
    font-size: 11px !important; color: #52525b !important;
    font-weight: 600 !important; text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}
div[data-testid="stMetricValue"] {
    font-size: 26px !important; font-weight: 700 !important;
    color: #fafafa !important; letter-spacing: -1px !important;
}

/* ─ ALERTS ─ */
div[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
    border: 1px solid !important;
}
div[data-testid="stAlert"][data-baseweb="notification"] {
    background: #111113 !important;
}

/* ─ TABS ─ */
button[data-baseweb="tab"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important; font-weight: 500 !important;
    color: #52525b !important;
}
button[data-baseweb="tab"][aria-selected="true"] { color: #fafafa !important; }
div[data-baseweb="tab-highlight"] { background: #6366f1 !important; height: 2px !important; }
div[data-baseweb="tab-border"] { background: #1c1c1f !important; }

/* ─ DIVIDER ─ */
hr { border-color: #1c1c1f !important; }

/* ─ EXPANDER ─ */
div[data-testid="stExpander"] {
    background: #111113 !important;
    border: 1px solid #1c1c1f !important;
    border-radius: 10px !important;
}
div[data-testid="stExpander"] summary {
    font-size: 13px !important; font-weight: 500 !important;
    color: #a1a1aa !important;
}

/* ─ DATAFRAME ─ */
div[data-testid="stDataFrame"] {
    border: 1px solid #1c1c1f !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* ─ CHARTS ─ */
div[data-testid="stArrowVegaLiteChart"],
div[data-testid="stVegaLiteChart"] {
    background: #111113 !important;
    border: 1px solid #1c1c1f !important;
    border-radius: 12px !important;
    padding: 12px !important;
}

/* ─ CUSTOM CARDS ─ */
.card {
    background: #111113;
    border: 1px solid #1c1c1f;
    border-radius: 14px;
    padding: 20px 22px;
    margin-bottom: 12px;
}
.card-title {
    font-size: 11px; font-weight: 600;
    color: #52525b; text-transform: uppercase;
    letter-spacing: 0.1em; margin-bottom: 8px;
}
.card-value {
    font-size: 28px; font-weight: 700;
    color: #fafafa; letter-spacing: -1px;
}

/* ─ SECTION HEADERS ─ */
.section-head {
    font-size: 13px; font-weight: 600;
    color: #71717a; text-transform: uppercase;
    letter-spacing: 0.08em; margin: 28px 0 16px;
    display: flex; align-items: center; gap: 8px;
}
.section-head::after {
    content: ''; flex: 1; height: 1px;
    background: #1c1c1f;
}

/* ─ STATUS PILL ─ */
.pill {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 4px 10px; border-radius: 20px;
    font-size: 11px; font-weight: 600; letter-spacing: 0.05em;
}
.pill-green { background: rgba(16,185,129,0.1); color: #10b981; border: 1px solid rgba(16,185,129,0.2); }
.pill-red   { background: rgba(239,68,68,0.1);  color: #ef4444; border: 1px solid rgba(239,68,68,0.2); }
.pill-amber { background: rgba(245,158,11,0.1); color: #f59e0b; border: 1px solid rgba(245,158,11,0.2); }
.pill-indigo{ background: rgba(99,102,241,0.1); color: #6366f1; border: 1px solid rgba(99,102,241,0.2); }

/* ─ PROB BAR ─ */
.prob-bar-wrap {
    background: #1c1c1f; border-radius: 100px;
    height: 6px; width: 100%; overflow: hidden; margin-top: 8px;
}
.prob-bar-fill {
    height: 100%; border-radius: 100px;
    transition: width 0.6s ease;
}

/* ─ TOP NAV ─ */
.top-nav {
    background: #111113;
    border-bottom: 1px solid #1c1c1f;
    padding: 16px 32px;
    display: flex; align-items: center; justify-content: space-between;
}
.top-nav-logo {
    font-size: 15px; font-weight: 700; color: #fafafa;
    display: flex; align-items: center; gap: 7px;
}
.top-nav-logo-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: linear-gradient(135deg,#6366f1,#10b981);
}
.top-nav-user {
    font-size: 12px; color: #52525b; font-weight: 500;
}
.content-area { padding: 28px 32px; }

/* ─ PRIORITY ALERT ─ */
.priority-alert {
    background: linear-gradient(135deg, rgba(239,68,68,0.06), rgba(239,68,68,0.02));
    border: 1px solid rgba(239,68,68,0.15);
    border-radius: 12px; padding: 16px 20px;
    display: flex; align-items: center; gap: 12px;
}
.priority-icon { font-size: 20px; }
.priority-text { flex: 1; }
.priority-label { font-size: 11px; font-weight: 600; color: #ef4444;
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 2px; }
.priority-name { font-size: 15px; font-weight: 600; color: #fafafa; }

/* ─ INSIGHT CARD ─ */
.insight-card {
    background: linear-gradient(135deg, rgba(99,102,241,0.05), rgba(99,102,241,0.02));
    border: 1px solid rgba(99,102,241,0.15);
    border-radius: 12px; padding: 18px 20px;
}
.insight-label { font-size: 10px; font-weight: 600; color: #6366f1;
    text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px; }
.insight-text { font-size: 14px; color: #a1a1aa; line-height: 1.6; }
.insight-text b { color: #e4e4e7; font-weight: 500; }

/* ─ ACTION ITEM ─ */
.action-item {
    display: flex; align-items: flex-start; gap: 10px;
    padding: 12px 16px;
    background: #111113; border: 1px solid #1c1c1f;
    border-radius: 10px; margin-bottom: 8px;
}
.action-bullet {
    width: 6px; height: 6px; border-radius: 50%;
    background: #6366f1; margin-top: 6px; flex-shrink: 0;
}
.action-text { font-size: 13px; color: #a1a1aa; line-height: 1.5; }

/* ─ TIMER CARD ─ */
.timer-display {
    font-size: 52px; font-weight: 700; color: #fafafa;
    letter-spacing: -2px; text-align: center;
    font-variant-numeric: tabular-nums;
    margin: 12px 0;
}
.timer-mode {
    text-align: center; font-size: 11px; font-weight: 600;
    color: #52525b; text-transform: uppercase; letter-spacing: 0.1em;
}
</style>
""", unsafe_allow_html=True)

# ── TOP NAV ──────────────────────────────────────────────
st.markdown(f"""
<div class="top-nav">
  <div class="top-nav-logo">
    <span class="top-nav-logo-dot"></span>LifeOS
  </div>
  <span class="top-nav-user">👤 {username}</span>
</div>
<div class="content-area">
""", unsafe_allow_html=True)

# ── SIDEBAR ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("### New Goal")
    g_name     = st.text_input("Goal name", placeholder="e.g. Read 12 books")
    g_target   = st.number_input("Target (units)", min_value=1, value=100)
    g_deadline = st.date_input("Deadline")
    if st.button("Create goal", use_container_width=True):
        if not g_name.strip():
            st.warning("Enter a goal name")
        else:
            create_goal(user_id, g_name.strip(), g_target, g_deadline)
            st.success("Goal created!")
            st.rerun()

    st.divider()
    if st.button("Sign out", use_container_width=True):
        for k in ["token","user_id","username"]: st.session_state[k] = None
        st.switch_page("app.py")

    st.markdown('<div style="margin-top:auto;padding-top:20px;font-size:11px;color:#27272a;font-weight:500;">LifeOS v1 · Beta</div>', unsafe_allow_html=True)

# ── LOAD GOALS ───────────────────────────────────────────
goals = get_goals(user_id)

if not goals:
    st.markdown("""
    <div style="text-align:center;padding:80px 0;">
      <div style="font-size:40px;margin-bottom:16px;">🎯</div>
      <div style="font-size:16px;font-weight:600;color:#fafafa;margin-bottom:8px;">No goals yet</div>
      <div style="font-size:13px;color:#52525b;">Create your first goal in the sidebar</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

goal_map     = {f"{g['name']}": g for g in goals}
selected     = st.multiselect("Select goals", list(goal_map.keys()),
                               placeholder="Choose goals to track...")

if not selected:
    st.markdown("""
    <div style="text-align:center;padding:60px 0;">
      <div style="font-size:13px;color:#3f3f46;">Select one or more goals above to view your dashboard</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

selected_goals = [goal_map[s] for s in selected]
selected_ids   = [g["id"] for g in selected_goals]

# ── CACHE ────────────────────────────────────────────────
@st.cache_data(ttl=30)
def cached_logs(gid, uid):    return get_logs(gid, uid)

@st.cache_data(ttl=30)
def cached_status(gid, uid):
    logs = get_logs(gid, uid)
    goal = next((g for g in get_goals(uid) if g["id"] == gid), None)
    return compute_status(goal, logs) if goal else None

# ── OVERVIEW ─────────────────────────────────────────────
st.markdown('<div class="section-head">Overview</div>', unsafe_allow_html=True)
cols = st.columns(len(selected_goals))
for i, g in enumerate(selected_goals):
    s = cached_status(g["id"], user_id)
    if not s: continue
    with cols[i]:
        prob  = s["success_probability"]
        color = "#10b981" if prob > 70 else ("#f59e0b" if prob > 40 else "#ef4444")
        st.markdown(f"""
        <div class="card">
          <div class="card-title">{g['name']}</div>
          <div class="card-value">{s['progress']}%</div>
          <div style="margin-top:10px;">
            <div style="display:flex;justify-content:space-between;margin-bottom:4px;">
              <span style="font-size:11px;color:#52525b;">Success probability</span>
              <span style="font-size:11px;font-weight:600;color:{color};">{prob}%</span>
            </div>
            <div class="prob-bar-wrap">
              <div class="prob-bar-fill" style="width:{prob}%;background:{color};"></div>
            </div>
          </div>
          <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap;">
            <span class="pill {'pill-green' if s['status']=='Achievable' else 'pill-red' if s['status']=='At Risk' else 'pill-indigo'}">{s['status']}</span>
            <span class="pill pill-amber">⚡ {round(s['required_per_day'],1)}/day needed</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ── PRIORITY FOCUS ───────────────────────────────────────
priority_data = []
for g in selected_goals:
    s    = cached_status(g["id"], user_id)
    logs = cached_logs(g["id"], user_id)
    if not s: continue
    done_vals   = [l["done"] for l in logs[-7:]]
    consistency = sum(1 for x in done_vals if x > 0) / max(len(done_vals), 1)
    score       = s["required_per_day"] * 2 - s["current_avg"] + (1-consistency)*5
    priority_data.append({"goal": g, "score": score, "status": s})

if priority_data and len(priority_data) > 0:
    worst = max(priority_data, key=lambda x: x["score"])
    st.markdown('<div class="section-head">Focus</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="priority-alert">
      <span class="priority-icon">🚨</span>
      <div class="priority-text">
        <div class="priority-label">Needs attention now</div>
        <div class="priority-name">{worst['goal']['name']} — {worst['status']['success_probability']}% success probability</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── DETAILED VIEW ────────────────────────────────────────
st.markdown('<div class="section-head">Detailed View</div>', unsafe_allow_html=True)

goal_labels  = {g["id"]: g["name"] for g in selected_goals}
selected_gid = st.selectbox("Goal", selected_ids,
                             format_func=lambda gid: goal_labels.get(gid, str(gid)),
                             label_visibility="collapsed")

goal   = next(g for g in selected_goals if g["id"] == selected_gid)
logs   = cached_logs(selected_gid, user_id)
status = cached_status(selected_gid, user_id)

if not status:
    st.error("Failed to compute status")
    st.stop()

# ── KEY METRICS ──────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric("Progress",         f"{status['progress']}%")
c2.metric("Required / day",   round(status["required_per_day"], 1))
c3.metric("Current avg",      round(status["current_avg"], 1))
c4.metric("Success prob",     f"{status['success_probability']}%")

# ── AI PREDICTION REASONS ────────────────────────────────
if status.get("reasons") or status.get("positives"):
    st.markdown('<div class="section-head">AI Analysis</div>', unsafe_allow_html=True)
    col_r, col_p = st.columns(2)
    with col_r:
        if status.get("reasons"):
            for r in status["reasons"]:
                st.markdown(f"""
                <div class="action-item">
                  <div style="width:6px;height:6px;border-radius:50%;background:#ef4444;margin-top:6px;flex-shrink:0;"></div>
                  <div class="action-text">{r.capitalize()}</div>
                </div>""", unsafe_allow_html=True)
    with col_p:
        if status.get("positives"):
            for p in status["positives"]:
                st.markdown(f"""
                <div class="action-item">
                  <div style="width:6px;height:6px;border-radius:50%;background:#10b981;margin-top:6px;flex-shrink:0;"></div>
                  <div class="action-text">{p.capitalize()}</div>
                </div>""", unsafe_allow_html=True)

st.divider()

# ── LOG FORM ─────────────────────────────────────────────
st.markdown('<div class="section-head">Log Update</div>', unsafe_allow_html=True)

with st.expander("📝 Log this hour", expanded=False):
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        done        = st.number_input("Work done (units)", min_value=0, value=0)
        screen_time = st.number_input("Screen time (min)",  min_value=0, value=0)
        sleep       = st.number_input("Sleep (hrs)", 0.0, 24.0, 7.0, 0.5)
    with col_b:
        mood   = st.slider("Mood",   1, 5, 3)
        energy = st.slider("Energy", 1, 5, 3)
    with col_c:
        stress = st.slider("Stress", 1, 5, 3)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Save log", use_container_width=True):
            add_log(selected_gid, user_id, done, mood, energy, screen_time, stress, sleep)
            st.success("Saved!")
            st.cache_data.clear()
            st.rerun()

# ── WELLBEING ────────────────────────────────────────────
wb    = compute_wellbeing(logs)
score = wb["score"]
wb_color = "#10b981" if score > 70 else ("#f59e0b" if score > 40 else "#ef4444")

st.markdown('<div class="section-head">Well-being</div>', unsafe_allow_html=True)
col_wb1, col_wb2 = st.columns([1, 2])
with col_wb1:
    st.markdown(f"""
    <div class="card" style="text-align:center;">
      <div class="card-title">Score</div>
      <div style="font-size:48px;font-weight:700;color:{wb_color};letter-spacing:-2px;">{score}</div>
      <div style="font-size:11px;color:#52525b;">out of 100</div>
    </div>
    """, unsafe_allow_html=True)
with col_wb2:
    if wb.get("suggestions"):
        for s in wb["suggestions"]:
            st.markdown(f"""
            <div class="action-item">
              <div class="action-bullet"></div>
              <div class="action-text">{s}</div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown('<div class="action-item"><div class="action-bullet" style="background:#10b981;"></div><div class="action-text">Well-being looks good — keep it up!</div></div>', unsafe_allow_html=True)

# ── ACTION PLAN ──────────────────────────────────────────
st.markdown('<div class="section-head">Action Plan</div>', unsafe_allow_html=True)
actions = []
if status["current_avg"] < status["required_per_day"]:
    actions.append(f"Increase daily effort to {round(status['required_per_day'], 1)} units")
if logs and logs[-1].get("screen_time", 0) > 60:
    actions.append("Reduce screen time by at least 30 minutes")
for s in wb.get("suggestions", []):
    actions.append(s)
actions = list(dict.fromkeys(actions))

if not actions:
    st.markdown('<div class="insight-card"><div class="insight-label">Status</div><div class="insight-text">You\'re on track — <b>keep the momentum going.</b></div></div>', unsafe_allow_html=True)
else:
    for a in actions:
        st.markdown(f"""
        <div class="action-item">
          <div class="action-bullet"></div>
          <div class="action-text">{a}</div>
        </div>""", unsafe_allow_html=True)

st.divider()

# ── CHARTS ───────────────────────────────────────────────
if logs:
    st.markdown('<div class="section-head">Charts</div>', unsafe_allow_html=True)
    df = pd.DataFrame(logs)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    view = st.selectbox("View", ["Daily performance", "Cumulative progress", "Weekly summary"], label_visibility="collapsed")
    required_v = status["required_per_day"]
    target_v   = goal.get("target")
    deadline_v = goal.get("deadline")

    if view == "Daily performance":
        df["required"] = required_v
        chart_df = df[["date", "done", "required"]].set_index("date")
        st.line_chart(chart_df, height=280, color=["#6366f1","#27272a"])

    elif view == "Cumulative progress":
        df["cumulative"]   = df["done"].cumsum()
        df["required_cum"] = [(i+1)*required_v for i in range(len(df))]
        avg = status["current_avg"]
        last_date = df["date"].max()
        total_done = df["cumulative"].iloc[-1]
        future_dates, predicted, cur = [], [], total_done
        for i in range(1, 91):
            nd = last_date + pd.Timedelta(days=i)
            cur += avg; future_dates.append(nd); predicted.append(cur)
            if target_v and cur >= target_v: break
        pred_df  = pd.DataFrame({"date": future_dates, "forecast": predicted})
        chart_df = pd.concat([
            df[["date","cumulative","required_cum"]],
            pred_df
        ]).sort_values("date").set_index("date")
        st.line_chart(chart_df, height=280)
        st.caption("cumulative = actual · required_cum = pace target · forecast = AI projection")

        if target_v:
            reached = pred_df[pred_df["forecast"] >= target_v]
            if len(reached):
                comp = reached.iloc[0]["date"].date()
                st.markdown(f'<div class="insight-card"><div class="insight-label">Forecast</div><div class="insight-text">Predicted completion: <b>{comp}</b></div></div>', unsafe_allow_html=True)
                if deadline_v:
                    dl   = pd.to_datetime(deadline_v).date()
                    diff = (dl - comp).days
                    if diff > 0:    st.success(f"🚀 {diff} days ahead of deadline")
                    elif diff == 0: st.warning("Exactly on deadline")
                    else:           st.error(f"⚠️ {abs(diff)} days behind deadline")
            else:
                st.error("At current pace, goal won't complete in time")

        # Planning engine
        if target_v and deadline_v:
            dl_date   = pd.to_datetime(deadline_v)
            today_dt  = df["date"].max()
            days_left = (dl_date - today_dt).days
            if days_left > 0:
                done_so_far = df["cumulative"].iloc[-1]
                remaining   = target_v - done_so_far
                if remaining > 0:
                    req_now = remaining / days_left
                    gap     = req_now - status["current_avg"]
                    today_t = req_now * (0.8 if (logs and logs[-1].get("screen_time",0)>60) else 1.0)
                    st.markdown('<div class="section-head">Planning Engine</div>', unsafe_allow_html=True)
                    p1, p2 = st.columns(2)
                    with p1:
                        st.metric("Required / day now", round(req_now, 1))
                        if gap > 0: st.warning(f"Increase by {round(gap,1)} units/day")
                        else:       st.success("Ahead of pace!")
                    with p2:
                        st.metric("Today's target", round(today_t, 1))
                        st.caption(f"4 sessions × {round(today_t/4,1)} units each")

    else:
        df_w = df.resample("W", on="date")["done"].sum()
        st.bar_chart(df_w, height=280, color="#6366f1")

st.divider()

# ── POMODORO ─────────────────────────────────────────────
st.markdown('<div class="section-head">Focus Timer</div>', unsafe_allow_html=True)

if "timers" not in st.session_state: st.session_state.timers = []

with st.expander("➕ New timer"):
    tc1, tc2, tc3 = st.columns(3)
    with tc1: t_label = st.text_input("Name", value="Focus", key="tl")
    with tc2: t_focus = st.number_input("Focus (min)", value=25, min_value=1, key="tf")
    with tc3: t_break = st.number_input("Break (min)", value=5, min_value=1, key="tb")
    t_loop = st.checkbox("Loop mode")
    if st.button("Add timer"):
        st.session_state.timers.append({
            "label": t_label, "focus": t_focus, "break": t_break,
            "mode": "focus", "duration": t_focus*60,
            "start_time": None, "running": False,
            "loop": t_loop, "switched": False
        })
        st.rerun()

for i, t in enumerate(st.session_state.timers):
    elapsed   = int(time.time() - t["start_time"]) if t.get("running") and t.get("start_time") else 0
    time_left = max(t.get("duration", 0) - elapsed, 0)
    mins, secs = time_left // 60, time_left % 60

    with st.container():
        st.markdown(f"""
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
            <span style="font-size:13px;font-weight:600;color:#e4e4e7;">{t['label']}</span>
            <span class="pill {'pill-indigo' if t['mode']=='focus' else 'pill-green'}">{t['mode'].upper()}</span>
          </div>
          <div class="timer-display">{mins:02d}:{secs:02d}</div>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)
        if col1.button("▶ Start",  key=f"s_{i}"):
            t["running"] = True; t["start_time"] = time.time()
        if col2.button("⏸ Pause",  key=f"p_{i}"):
            if t.get("running") and t.get("start_time"):
                t["duration"] = max(t["duration"] - int(time.time()-t["start_time"]), 0)
            t["running"] = False; t["start_time"] = None
        if col3.button("↺ Reset",  key=f"r_{i}"):
            t.update({"running":False,"switched":False,"mode":"focus",
                      "duration":t["focus"]*60,"start_time":None})

        if time_left == 0 and t.get("running") and not t.get("switched"):
            t["switched"] = True
            if t["mode"] == "focus":
                t["mode"] = "break"; t["duration"] = t["break"]*60
                st.success("Break time!")
            else:
                if t["loop"]: t["mode"] = "focus"; t["duration"] = t["focus"]*60
                else: t["running"] = False
            t["start_time"] = time.time()

st.divider()

# ── STREAK ───────────────────────────────────────────────
if logs:
    st.markdown('<div class="section-head">Consistency</div>', unsafe_allow_html=True)
    done_vals = [l["done"] for l in logs]
    streak = 0
    for v in reversed(done_vals):
        if v > 0: streak += 1
        else: break

    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("Current streak", f"{streak} days")
    col_s2.metric("Total logs", len(logs))
    col_s3.metric("Days active", sum(1 for v in done_vals if v > 0))

    df3 = pd.DataFrame(logs)
    df3["date"] = pd.to_datetime(df3["date"])
    last30 = df3.tail(30)[["date", "done"]].set_index("date")
    st.dataframe(last30, use_container_width=True)

st.divider()

# ── PATTERNS ─────────────────────────────────────────────
patterns = compute_patterns(logs)
if patterns:
    st.markdown('<div class="section-head">Behavior Patterns</div>', unsafe_allow_html=True)
    for p in patterns:
        st.markdown(f"""
        <div class="insight-card" style="margin-bottom:8px;">
          <div class="insight-label">Pattern</div>
          <div class="insight-text">{p}</div>
        </div>""", unsafe_allow_html=True)

# ── AI INSIGHT ───────────────────────────────────────────
ins = compute_insight(goal, logs)
st.markdown('<div class="section-head">AI Insight</div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="insight-card" style="margin-bottom:8px;">
  <div class="insight-label">Analysis</div>
  <div class="insight-text">{ins['explanation']}</div>
</div>
<div class="insight-card">
  <div class="insight-label">Recommendation</div>
  <div class="insight-text">{ins['suggestion']}</div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── WEEKLY REPORT ────────────────────────────────────────
rep = compute_weekly_report(logs)
if rep:
    st.markdown('<div class="section-head">Weekly Report</div>', unsafe_allow_html=True)
    r1,r2,r3,r4 = st.columns(4)
    r1.metric("Total done",     rep["total_done"])
    r2.metric("Daily average",  rep["avg_per_day"])
    r3.metric("Streak",         f"{rep['streak']}d")
    r4.metric("Missed days",    rep["missed_days"])

    risk_color = "#10b981" if rep["risk"]=="Low" else ("#f59e0b" if rep["risk"]=="Medium" else "#ef4444")
    st.markdown(f"""
    <div style="margin-top:12px;display:flex;align-items:center;gap:8px;">
      <span style="font-size:11px;color:#52525b;">Weekly risk:</span>
      <span class="pill" style="background:rgba(0,0,0,0.2);color:{risk_color};border-color:{risk_color}33;">{rep['risk']}</span>
      <span style="font-size:11px;color:#52525b;margin-left:8px;">Best day: <b style="color:#a1a1aa;">{rep['best_day']}</b></span>
    </div>
    """, unsafe_allow_html=True)

    for s in rep.get("summary", []):
        st.markdown(f'<div class="action-item" style="margin-top:8px;"><div class="action-bullet"></div><div class="action-text">{s}</div></div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
