import streamlit as st
import pandas as pd
import time
from db   import (get_goals, create_goal, add_log, get_logs,
                  compute_status, compute_wellbeing, compute_insight,
                  compute_patterns, compute_weekly_report)
from auth import decode_token

st.set_page_config(page_title="LifeOS · Dashboard", layout="wide", initial_sidebar_state="expanded")

# ── AUTH GUARD ───────────────────────────────────────────
if not st.session_state.get("user_id"):
    if st.session_state.get("token"):
        uid = decode_token(st.session_state.token)
        if uid: st.session_state.user_id = uid
        else:   st.switch_page("app.py")
    else:
        st.switch_page("app.py")

user_id  = st.session_state.user_id
username = st.session_state.get("username", "User")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400;1,700&family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400;500&display=swap');

:root {
  --bg:      #09090b;
  --s1:      #111114;
  --s2:      #18181d;
  --bd:      #1e1e24;
  --bd2:     #2a2a35;
  --text:    #fafafa;
  --muted:   #71717a;
  --subtle:  #3f3f46;
  --accent:  #e8d5b0;
  --accent2: #c4a882;
  --green:   #4ade80;
  --amber:   #fbbf24;
  --red:     #f87171;
  --indigo:  #818cf8;
}

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main {
  background: var(--bg) !important;
  font-family: 'DM Sans', sans-serif !important;
  color: var(--text) !important;
}
.main .block-container { padding: 0 !important; max-width: 100% !important; }
[data-testid="stHeader"],[data-testid="stToolbar"],
[data-testid="stDecoration"],#MainMenu,footer { display: none !important; }

/* grain */
[data-testid="stAppViewContainer"]::before {
  content: '';
  position: fixed; inset: 0; z-index: 0; pointer-events: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='300' height='300' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");
  background-size: 200px; opacity: 0.6;
}

/* ── SIDEBAR ── */
[data-testid="stSidebar"] {
  background: var(--s1) !important;
  border-right: 1px solid var(--bd) !important;
}
[data-testid="stSidebar"] .block-container {
  padding: 32px 24px !important;
}

/* sidebar logo */
.sb-logo {
  font-family: 'Playfair Display', serif;
  font-size: 18px; font-weight: 700;
  color: var(--text); margin-bottom: 32px;
  letter-spacing: -0.3px;
}
.sb-logo em { font-style: italic; color: var(--accent); }

.sb-section {
  font-family: 'DM Mono', monospace;
  font-size: 9px; color: var(--subtle);
  letter-spacing: 0.18em; text-transform: uppercase;
  margin-bottom: 14px; margin-top: 28px;
}

/* ── TOP BAR ── */
.topbar {
  position: relative; z-index: 10;
  background: var(--s1);
  border-bottom: 1px solid var(--bd);
  padding: 18px 36px;
  display: flex; align-items: center; justify-content: space-between;
}
.topbar-logo {
  font-family: 'Playfair Display', serif;
  font-size: 16px; font-weight: 700; color: var(--text);
}
.topbar-logo em { font-style: italic; color: var(--accent); }
.topbar-user {
  display: flex; align-items: center; gap: 10px;
}
.topbar-name {
  font-family: 'DM Mono', monospace;
  font-size: 10px; color: var(--subtle);
  letter-spacing: 0.1em; text-transform: uppercase;
}
.topbar-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--green); box-shadow: 0 0 8px var(--green);
}

/* ── CONTENT ── */
.content { padding: 36px 36px 60px; position: relative; z-index: 10; }

/* ── SECTION LABEL ── */
.slabel {
  font-family: 'DM Mono', monospace;
  font-size: 9px; color: var(--subtle);
  letter-spacing: 0.18em; text-transform: uppercase;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--bd);
  margin-bottom: 20px;
  display: flex; align-items: center; justify-content: space-between;
}

/* ── GOAL CARD ── */
.gcard {
  background: var(--s1);
  border: 1px solid var(--bd);
  padding: 24px;
  transition: border-color 0.2s;
  position: relative; overflow: hidden;
}
.gcard::before {
  content: '';
  position: absolute; top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, var(--accent), transparent);
  opacity: 0;
  transition: opacity 0.2s;
}
.gcard:hover { border-color: var(--bd2); }
.gcard:hover::before { opacity: 1; }

.gcard-label {
  font-family: 'DM Mono', monospace;
  font-size: 9px; color: var(--subtle);
  letter-spacing: 0.15em; text-transform: uppercase;
  margin-bottom: 10px;
}
.gcard-val {
  font-family: 'Playfair Display', serif;
  font-size: 40px; font-weight: 700;
  color: var(--text); line-height: 1;
  letter-spacing: -1.5px;
}
.gcard-val em { font-style: italic; color: var(--accent); }
.gcard-sub {
  font-size: 12px; color: var(--muted);
  margin-top: 8px; font-weight: 300;
}

/* prob bar */
.pbar-wrap { margin-top: 16px; }
.pbar-top {
  display: flex; justify-content: space-between;
  font-family: 'DM Mono', monospace;
  font-size: 9px; color: var(--subtle);
  letter-spacing: 0.1em; text-transform: uppercase;
  margin-bottom: 6px;
}
.pbar-track {
  height: 2px; background: var(--bd2);
  position: relative;
}
.pbar-fill {
  position: absolute; top: 0; left: 0; height: 100%;
  transition: width 0.8s ease;
}

/* pill */
.pill {
  display: inline-flex; align-items: center;
  padding: 3px 8px;
  font-family: 'DM Mono', monospace;
  font-size: 9px; font-weight: 500;
  letter-spacing: 0.1em; text-transform: uppercase;
  border: 1px solid;
}
.pill-g { color: var(--green);  border-color: rgba(74,222,128,0.2); background: rgba(74,222,128,0.05); }
.pill-r { color: var(--red);    border-color: rgba(248,113,113,0.2); background: rgba(248,113,113,0.05); }
.pill-a { color: var(--amber);  border-color: rgba(251,191,36,0.2);  background: rgba(251,191,36,0.05); }
.pill-i { color: var(--indigo); border-color: rgba(129,140,248,0.2); background: rgba(129,140,248,0.05); }
.pill-ac{ color: var(--accent); border-color: rgba(232,213,176,0.2); background: rgba(232,213,176,0.05); }

/* ── PRIORITY BANNER ── */
.priority {
  border: 1px solid rgba(248,113,113,0.15);
  background: rgba(248,113,113,0.03);
  padding: 20px 24px;
  display: flex; align-items: center; gap: 16px;
  margin-bottom: 24px;
}
.priority-left {
  font-family: 'DM Mono', monospace;
  font-size: 9px; color: var(--red);
  letter-spacing: 0.15em; text-transform: uppercase;
  white-space: nowrap;
}
.priority-divider {
  width: 1px; height: 36px;
  background: rgba(248,113,113,0.15);
}
.priority-name {
  font-family: 'Playfair Display', serif;
  font-size: 18px; font-weight: 700;
  color: var(--text); font-style: italic;
}
.priority-stat {
  margin-left: auto;
  font-family: 'DM Mono', monospace;
  font-size: 9px; color: var(--muted);
  letter-spacing: 0.1em; text-transform: uppercase;
  text-align: right;
}

/* ── KEY NUMBERS ── */
.knums {
  display: grid; grid-template-columns: repeat(4,1fr);
  border: 1px solid var(--bd);
  border-right: none;
}
.knum {
  padding: 24px 20px;
  border-right: 1px solid var(--bd);
}
.knum-label {
  font-family: 'DM Mono', monospace;
  font-size: 9px; color: var(--subtle);
  letter-spacing: 0.15em; text-transform: uppercase;
  margin-bottom: 8px;
}
.knum-val {
  font-family: 'Playfair Display', serif;
  font-size: 32px; font-weight: 700;
  color: var(--text); line-height: 1;
  letter-spacing: -1px;
}
.knum-val em { font-style: italic; color: var(--accent); font-size: 28px; }

/* ── ANALYSIS ROW ── */
.analysis-row {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 12px; margin-top: 4px;
}
.analysis-card {
  border: 1px solid var(--bd);
  padding: 20px;
}
.analysis-card-label {
  font-family: 'DM Mono', monospace;
  font-size: 9px; color: var(--subtle);
  letter-spacing: 0.15em; text-transform: uppercase;
  margin-bottom: 14px;
}
.aitem {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 8px 0;
  border-bottom: 1px solid var(--bd);
}
.aitem:last-child { border-bottom: none; }
.aitem-dot {
  width: 4px; height: 4px; border-radius: 50%;
  margin-top: 7px; flex-shrink: 0;
}
.aitem-text {
  font-size: 13px; color: var(--muted);
  font-weight: 300; line-height: 1.5;
}

/* ── INSIGHT CARD ── */
.icard {
  border: 1px solid var(--bd);
  padding: 24px;
  margin-bottom: 12px;
}
.icard-label {
  font-family: 'DM Mono', monospace;
  font-size: 9px; color: var(--accent);
  letter-spacing: 0.15em; text-transform: uppercase;
  margin-bottom: 10px;
}
.icard-text {
  font-size: 14px; color: var(--muted);
  font-weight: 300; line-height: 1.7;
}
.icard-text strong { color: #a1a1aa; font-weight: 400; }

/* ── WB CARD ── */
.wb-big {
  font-family: 'Playfair Display', serif;
  font-size: 72px; font-weight: 700;
  line-height: 1; letter-spacing: -3px;
}

/* ── LOG FORM ── */
.log-wrap {
  border: 1px solid var(--bd);
  padding: 28px;
}

/* ── TIMER ── */
.timer-card {
  border: 1px solid var(--bd);
  padding: 28px; text-align: center;
}
.timer-time {
  font-family: 'Playfair Display', serif;
  font-size: 64px; font-weight: 900;
  letter-spacing: -3px; color: var(--text);
  line-height: 1;
}
.timer-mode {
  font-family: 'DM Mono', monospace;
  font-size: 9px; color: var(--subtle);
  letter-spacing: 0.2em; text-transform: uppercase;
  margin-top: 8px;
}

/* ── INPUTS (dashboard) ── */
div[data-testid="stTextInput"] > label,
div[data-testid="stNumberInput"] > label,
div[data-testid="stDateInput"] > label,
div[data-testid="stSelectbox"] > label,
div[data-testid="stMultiSelect"] > label,
div[data-testid="stSlider"] > label,
div[data-testid="stCheckbox"] > label {
  font-family: 'DM Mono', monospace !important;
  font-size: 9px !important; font-weight: 500 !important;
  color: var(--subtle) !important;
  letter-spacing: 0.15em !important;
  text-transform: uppercase !important;
}
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input {
  background: transparent !important;
  border: none !important;
  border-bottom: 1px solid var(--bd2) !important;
  border-radius: 0 !important;
  color: var(--text) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 14px !important; font-weight: 300 !important;
  padding: 8px 0 !important;
  box-shadow: none !important;
}
div[data-testid="stTextInput"] input:focus,
div[data-testid="stNumberInput"] input:focus {
  border-bottom-color: var(--accent) !important;
  box-shadow: none !important;
}

div[data-testid="stButton"] > button {
  background: transparent !important;
  color: var(--accent) !important;
  font-family: 'DM Mono', monospace !important;
  font-weight: 500 !important; font-size: 10px !important;
  border: 1px solid var(--bd2) !important;
  border-radius: 0 !important;
  padding: 10px 20px !important;
  letter-spacing: 0.15em !important;
  text-transform: uppercase !important;
  transition: all 0.2s !important;
  box-shadow: none !important;
}
div[data-testid="stButton"] > button:hover {
  background: var(--accent) !important;
  color: var(--bg) !important;
  border-color: var(--accent) !important;
  transform: none !important;
  box-shadow: none !important;
}

div[data-baseweb="select"] > div {
  background: transparent !important;
  border: none !important;
  border-bottom: 1px solid var(--bd2) !important;
  border-radius: 0 !important;
  color: var(--text) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 14px !important;
}

div[data-testid="stMetric"] {
  background: var(--s1) !important;
  border: 1px solid var(--bd) !important;
  border-radius: 0 !important;
  padding: 18px 20px !important;
}
div[data-testid="stMetricLabel"] {
  font-family: 'DM Mono', monospace !important;
  font-size: 9px !important; color: var(--subtle) !important;
  font-weight: 500 !important; text-transform: uppercase !important;
  letter-spacing: 0.12em !important;
}
div[data-testid="stMetricValue"] {
  font-family: 'Playfair Display', serif !important;
  font-size: 28px !important; font-weight: 700 !important;
  color: var(--text) !important; letter-spacing: -1px !important;
}

div[data-testid="stAlert"] {
  border-radius: 0 !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 13px !important; font-weight: 300 !important;
  background: transparent !important;
  border-left: 1px solid !important;
  padding: 10px 14px !important;
}

hr { border-color: var(--bd) !important; margin: 28px 0 !important; }

div[data-testid="stExpander"] {
  background: transparent !important;
  border: 1px solid var(--bd) !important;
  border-radius: 0 !important;
}
div[data-testid="stExpander"] summary {
  font-family: 'DM Mono', monospace !important;
  font-size: 10px !important; font-weight: 500 !important;
  color: var(--muted) !important;
  letter-spacing: 0.12em !important; text-transform: uppercase !important;
}

button[data-baseweb="tab"] {
  font-family: 'DM Mono', monospace !important;
  font-size: 9px !important; color: var(--subtle) !important;
  letter-spacing: 0.15em !important; text-transform: uppercase !important;
}
button[data-baseweb="tab"][aria-selected="true"] { color: var(--accent) !important; }
div[data-baseweb="tab-highlight"] { background: var(--accent) !important; height: 1px !important; }
div[data-baseweb="tab-border"] { background: var(--bd) !important; }

div[data-testid="stDataFrame"] {
  border: 1px solid var(--bd) !important;
  border-radius: 0 !important;
}
</style>
""", unsafe_allow_html=True)

# ── TOP BAR ──────────────────────────────────────────────
st.markdown(f"""
<div class="topbar">
  <div class="topbar-logo">Life<em>OS</em></div>
  <div class="topbar-user">
    <span class="topbar-name">{username}</span>
    <span class="topbar-dot"></span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR ──────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sb-logo">Life<em>OS</em></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-section">New Goal</div>', unsafe_allow_html=True)

    g_name     = st.text_input("Goal name", placeholder="e.g. Write 50,000 words")
    g_target   = st.number_input("Target units", min_value=1, value=100)
    g_deadline = st.date_input("Deadline")

    if st.button("Create Goal →", use_container_width=True):
        if not g_name.strip():
            st.warning("Enter a goal name")
        else:
            create_goal(user_id, g_name.strip(), g_target, g_deadline)
            st.success("Goal created.")
            st.rerun()

    st.divider()
    if st.button("Sign out →", use_container_width=True):
        for k in ["token","user_id","username"]: st.session_state[k] = None
        st.switch_page("app.py")

# ── CONTENT AREA ─────────────────────────────────────────
st.markdown('<div class="content">', unsafe_allow_html=True)

# ── LOAD GOALS ───────────────────────────────────────────
goals = get_goals(user_id)

if not goals:
    st.markdown("""
    <div style="padding:80px 0;text-align:center;">
      <div style="font-family:'Playfair Display',serif;font-size:48px;font-weight:700;
           font-style:italic;color:#1e1e24;margin-bottom:16px;">"Begin."</div>
      <div style="font-family:'DM Mono',monospace;font-size:10px;color:#3f3f46;
           letter-spacing:0.15em;text-transform:uppercase;">
        Create your first goal in the sidebar
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

goal_map   = {g["name"]: g for g in goals}
selected   = st.multiselect("Select goals", list(goal_map.keys()),
                             placeholder="Choose goals to track...")

if not selected:
    st.markdown("""
    <div style="padding:48px 0;">
      <div style="font-family:'DM Mono',monospace;font-size:10px;color:#3f3f46;
           letter-spacing:0.15em;text-transform:uppercase;">
        ↑ Select one or more goals to view your dashboard
      </div>
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

# ── OVERVIEW CARDS ───────────────────────────────────────
st.markdown('<div class="slabel"><span>Overview</span></div>', unsafe_allow_html=True)

cols = st.columns(len(selected_goals))
for i, g in enumerate(selected_goals):
    s = cached_status(g["id"], user_id)
    if not s: continue
    prob  = s["success_probability"]
    color = "var(--green)" if prob > 70 else ("var(--amber)" if prob > 40 else "var(--red)")
    pstat = "pill-g" if prob > 70 else ("pill-a" if prob > 40 else "pill-r")
    with cols[i]:
        st.markdown(f"""
        <div class="gcard">
          <div class="gcard-label">{g['name']}</div>
          <div class="gcard-val">{s['progress']}<em>%</em></div>
          <div class="gcard-sub">complete · {round(s['required_per_day'],1)} units/day needed</div>
          <div class="pbar-wrap">
            <div class="pbar-top">
              <span>Success probability</span>
              <span style="color:{color};">{prob}%</span>
            </div>
            <div class="pbar-track">
              <div class="pbar-fill" style="width:{prob}%;background:{color};"></div>
            </div>
          </div>
          <div style="margin-top:14px;display:flex;gap:8px;flex-wrap:wrap;">
            <span class="{pstat} pill">{s['status']}</span>
            <span class="pill-ac pill">avg {round(s['current_avg'],1)}/day</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ── PRIORITY ─────────────────────────────────────────────
priority_data = []
for g in selected_goals:
    s    = cached_status(g["id"], user_id)
    logs = cached_logs(g["id"], user_id)
    if not s: continue
    done_v = [l["done"] for l in logs[-7:]]
    cons   = sum(1 for x in done_v if x>0) / max(len(done_v),1)
    score  = s["required_per_day"]*2 - s["current_avg"] + (1-cons)*5
    priority_data.append({"goal":g,"score":score,"status":s})

if priority_data:
    worst = max(priority_data, key=lambda x: x["score"])
    st.markdown(f"""
    <div style="margin-top:16px;">
    <div class="priority">
      <span class="priority-left">⚠ Priority</span>
      <div class="priority-divider"></div>
      <div>
        <div class="priority-name">{worst['goal']['name']}</div>
        <div style="font-family:'DM Mono',monospace;font-size:9px;
             color:var(--muted);letter-spacing:0.1em;text-transform:uppercase;margin-top:3px;">
          Needs immediate attention
        </div>
      </div>
      <div class="priority-stat">
        <div style="color:var(--red);">{worst['status']['success_probability']}%</div>
        <div>success probability</div>
      </div>
    </div>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# ── DETAILED VIEW ────────────────────────────────────────
st.markdown('<div class="slabel"><span>Detailed Analysis</span></div>', unsafe_allow_html=True)

goal_labels  = {g["id"]: g["name"] for g in selected_goals}
selected_gid = st.selectbox("Goal", selected_ids,
                             format_func=lambda gid: goal_labels.get(gid, str(gid)),
                             label_visibility="collapsed")

goal   = next(g for g in selected_goals if g["id"] == selected_gid)
logs   = cached_logs(selected_gid, user_id)
status = cached_status(selected_gid, user_id)
if not status: st.error("Failed to compute status"); st.stop()

# ── KEY NUMBERS ──────────────────────────────────────────
prob  = status["success_probability"]
color = "var(--green)" if prob>70 else ("var(--amber)" if prob>40 else "var(--red)")
st.markdown(f"""
<div class="knums">
  <div class="knum">
    <div class="knum-label">Progress</div>
    <div class="knum-val">{status['progress']}<em>%</em></div>
  </div>
  <div class="knum">
    <div class="knum-label">Success Probability</div>
    <div class="knum-val" style="color:{color};">{prob}<em>%</em></div>
  </div>
  <div class="knum">
    <div class="knum-label">Required / Day</div>
    <div class="knum-val">{round(status['required_per_day'],1)}</div>
  </div>
  <div class="knum">
    <div class="knum-label">Current Average</div>
    <div class="knum-val">{round(status['current_avg'],1)}</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ── AI ANALYSIS ──────────────────────────────────────────
if status.get("reasons") or status.get("positives"):
    st.markdown('<div class="slabel"><span>AI Analysis</span></div>', unsafe_allow_html=True)
    col_r, col_p = st.columns(2)
    with col_r:
        if status.get("reasons"):
            items = "".join([f'<div class="aitem"><div class="aitem-dot" style="background:var(--red);"></div><div class="aitem-text">{r.capitalize()}</div></div>' for r in status["reasons"]])
            st.markdown(f'<div class="analysis-card"><div class="analysis-card-label">Risk factors</div>{items}</div>', unsafe_allow_html=True)
    with col_p:
        if status.get("positives"):
            items = "".join([f'<div class="aitem"><div class="aitem-dot" style="background:var(--green);"></div><div class="aitem-text">{p.capitalize()}</div></div>' for p in status["positives"]])
            st.markdown(f'<div class="analysis-card"><div class="analysis-card-label">Strengths</div>{items}</div>', unsafe_allow_html=True)

st.divider()

# ── LOG FORM ─────────────────────────────────────────────
st.markdown('<div class="slabel"><span>Log Update</span></div>', unsafe_allow_html=True)

with st.expander("Log this hour"):
    ca, cb, cc = st.columns(3)
    with ca:
        done        = st.number_input("Work done (units)", min_value=0, value=0)
        screen_time = st.number_input("Screen time (min)",  min_value=0, value=0)
        sleep       = st.number_input("Sleep (hrs)", 0.0, 24.0, 7.0, 0.5)
    with cb:
        mood   = st.slider("Mood",   1, 5, 3)
        energy = st.slider("Energy", 1, 5, 3)
    with cc:
        stress = st.slider("Stress", 1, 5, 3)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Save log →", use_container_width=True):
            add_log(selected_gid, user_id, done, mood, energy, screen_time, stress, sleep)
            st.success("Saved.")
            st.cache_data.clear()
            st.rerun()

# ── WELLBEING ────────────────────────────────────────────
wb    = compute_wellbeing(logs)
score = wb["score"]
wc    = "var(--green)" if score>70 else ("var(--amber)" if score>40 else "var(--red)")

st.markdown('<div class="slabel" style="margin-top:28px;"><span>Wellbeing</span></div>', unsafe_allow_html=True)
col_w1, col_w2 = st.columns([1, 2])
with col_w1:
    st.markdown(f"""
    <div class="gcard" style="text-align:center;">
      <div class="gcard-label">Score</div>
      <div class="wb-big" style="color:{wc};">{score}</div>
      <div class="gcard-sub">/100</div>
    </div>
    """, unsafe_allow_html=True)
with col_w2:
    for s in wb.get("suggestions", ["Wellbeing looks good — maintain your rhythm."]):
        st.markdown(f'<div class="aitem" style="padding:12px 0;"><div class="aitem-dot" style="background:var(--accent);margin-top:8px;"></div><div class="aitem-text">{s}</div></div>', unsafe_allow_html=True)

st.divider()

# ── CHARTS ───────────────────────────────────────────────
if logs:
    st.markdown('<div class="slabel"><span>Performance</span></div>', unsafe_allow_html=True)
    df = pd.DataFrame(logs)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    view = st.selectbox("View", ["Daily", "Cumulative", "Weekly"], label_visibility="collapsed")
    req  = status["required_per_day"]
    tgt  = goal.get("target")
    dl   = goal.get("deadline")

    if view == "Daily":
        df["required"] = req
        st.line_chart(df[["date","done","required"]].set_index("date"), height=260, color=["#e8d5b0","#2a2a35"])

    elif view == "Cumulative":
        df["cumulative"]   = df["done"].cumsum()
        df["pace"]         = [(i+1)*req for i in range(len(df))]
        avg = status["current_avg"]
        ld  = df["date"].max(); td = df["cumulative"].iloc[-1]
        fd, fv, c = [], [], td
        for i in range(1,91):
            nd = ld + pd.Timedelta(days=i); c += avg
            fd.append(nd); fv.append(c)
            if tgt and c >= tgt: break
        pdf = pd.DataFrame({"date":fd,"forecast":fv})
        cdf = pd.concat([df[["date","cumulative","pace"]], pdf]).sort_values("date").set_index("date")
        st.line_chart(cdf, height=260)
        st.markdown('<div style="font-family:DM Mono,monospace;font-size:9px;color:#3f3f46;letter-spacing:0.1em;text-transform:uppercase;margin-top:6px;">cumulative · pace · forecast</div>', unsafe_allow_html=True)

        if tgt:
            reached = pdf[pdf["forecast"] >= tgt]
            if len(reached):
                comp = reached.iloc[0]["date"].date()
                st.markdown(f'<div class="icard" style="margin-top:16px;"><div class="icard-label">Forecast</div><div class="icard-text">Predicted completion: <strong>{comp}</strong></div></div>', unsafe_allow_html=True)
                if dl:
                    deadline = pd.to_datetime(dl).date()
                    diff = (deadline - comp).days
                    if diff > 0:    st.success(f"{diff} days ahead of deadline")
                    elif diff == 0: st.warning("On deadline — no buffer")
                    else:           st.error(f"{abs(diff)} days behind deadline")

        if tgt and dl:
            dl_dt     = pd.to_datetime(dl)
            days_left = (dl_dt - df["date"].max()).days
            if days_left > 0:
                done_sf  = df["cumulative"].iloc[-1]
                rem      = tgt - done_sf
                if rem > 0:
                    req_now = rem / days_left
                    gap     = req_now - status["current_avg"]
                    today_t = req_now * (0.8 if (logs and logs[-1].get("screen_time",0)>60) else 1.0)
                    st.markdown('<div class="slabel" style="margin-top:28px;"><span>Planning Engine</span></div>', unsafe_allow_html=True)
                    p1, p2 = st.columns(2)
                    p1.metric("Required / day now", round(req_now,1))
                    p2.metric("Today's target",     round(today_t,1))
                    if gap > 0: st.warning(f"Increase by {round(gap,1)} units/day to stay on track")
                    else:       st.success("Ahead of pace — keep going")
    else:
        dfw = df.resample("W", on="date")["done"].sum()
        st.bar_chart(dfw, height=260, color="#e8d5b0")

st.divider()

# ── POMODORO ─────────────────────────────────────────────
st.markdown('<div class="slabel"><span>Focus Timer</span></div>', unsafe_allow_html=True)

if "timers" not in st.session_state: st.session_state.timers = []

with st.expander("New timer"):
    tc1, tc2, tc3 = st.columns(3)
    with tc1: t_label = st.text_input("Name", value="Deep Work", key="tl")
    with tc2: t_focus = st.number_input("Focus (min)", value=25, min_value=1, key="tf")
    with tc3: t_break = st.number_input("Break (min)", value=5,  min_value=1, key="tb")
    t_loop = st.checkbox("Loop mode")
    if st.button("Add timer →"):
        st.session_state.timers.append({
            "label":t_label,"focus":t_focus,"break":t_break,
            "mode":"focus","duration":t_focus*60,
            "start_time":None,"running":False,"loop":t_loop,"switched":False
        })
        st.rerun()

for i, t in enumerate(st.session_state.timers):
    elapsed   = int(time.time()-t["start_time"]) if t.get("running") and t.get("start_time") else 0
    time_left = max(t.get("duration",0)-elapsed, 0)
    mins, secs = time_left//60, time_left%60
    mode_color = "var(--accent)" if t["mode"]=="focus" else "var(--green)"

    st.markdown(f"""
    <div class="timer-card">
      <div style="font-family:'DM Mono',monospace;font-size:9px;color:var(--subtle);
           letter-spacing:0.18em;text-transform:uppercase;margin-bottom:4px;">{t['label']}</div>
      <div class="timer-time">{mins:02d}<span style="color:var(--subtle);">:</span>{secs:02d}</div>
      <div class="timer-mode" style="color:{mode_color};">{t['mode']}</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    if col1.button("Start →",  key=f"s_{i}"): t["running"]=True; t["start_time"]=time.time()
    if col2.button("Pause",    key=f"p_{i}"):
        if t.get("running") and t.get("start_time"):
            t["duration"] = max(t["duration"]-int(time.time()-t["start_time"]),0)
        t["running"]=False; t["start_time"]=None
    if col3.button("Reset",    key=f"r_{i}"):
        t.update({"running":False,"switched":False,"mode":"focus","duration":t["focus"]*60,"start_time":None})

    if time_left==0 and t.get("running") and not t.get("switched"):
        t["switched"]=True
        if t["mode"]=="focus":
            t["mode"]="break"; t["duration"]=t["break"]*60; st.success("Break time.")
        else:
            if t["loop"]: t["mode"]="focus"; t["duration"]=t["focus"]*60
            else: t["running"]=False
        t["start_time"]=time.time()

st.divider()

# ── STREAK ───────────────────────────────────────────────
if logs:
    st.markdown('<div class="slabel"><span>Consistency</span></div>', unsafe_allow_html=True)
    done_vals = [l["done"] for l in logs]
    streak = 0
    for v in reversed(done_vals):
        if v > 0: streak += 1
        else: break
    c1, c2, c3 = st.columns(3)
    c1.metric("Streak",      f"{streak} days")
    c2.metric("Total logs",  len(logs))
    c3.metric("Active days", sum(1 for v in done_vals if v>0))

    df3 = pd.DataFrame(logs)
    df3["date"] = pd.to_datetime(df3["date"])
    last30 = df3.tail(30)[["date","done"]].set_index("date")
    st.dataframe(last30, use_container_width=True)

st.divider()

# ── INSIGHT ──────────────────────────────────────────────
ins = compute_insight(goal, logs)
pat = compute_patterns(logs)

st.markdown('<div class="slabel"><span>Insights</span></div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="icard">
  <div class="icard-label">Analysis</div>
  <div class="icard-text">{ins['explanation']}</div>
</div>
<div class="icard">
  <div class="icard-label">Recommendation</div>
  <div class="icard-text">{ins['suggestion']}</div>
</div>
""", unsafe_allow_html=True)

if pat:
    for p in pat:
        st.markdown(f'<div class="icard" style="margin-top:8px;"><div class="icard-label">Pattern</div><div class="icard-text">{p}</div></div>', unsafe_allow_html=True)

st.divider()

# ── WEEKLY REPORT ────────────────────────────────────────
rep = compute_weekly_report(logs)
if rep:
    st.markdown('<div class="slabel"><span>Weekly Report</span></div>', unsafe_allow_html=True)
    rc = "var(--green)" if rep["risk"]=="Low" else ("var(--amber)" if rep["risk"]=="Medium" else "var(--red)")
    r1,r2,r3,r4 = st.columns(4)
    r1.metric("Total done",    rep["total_done"])
    r2.metric("Daily average", rep["avg_per_day"])
    r3.metric("Streak",        f"{rep['streak']}d")
    r4.metric("Missed days",   rep["missed_days"])
    st.markdown(f"""
    <div style="margin-top:12px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
      <span class="pill" style="color:{rc};border-color:{rc}33;background:transparent;">
        {rep['risk']} risk
      </span>
      <span style="font-family:'DM Mono',monospace;font-size:9px;color:var(--subtle);
           letter-spacing:0.1em;text-transform:uppercase;">
        Best day: {rep['best_day']}
      </span>
    </div>
    """, unsafe_allow_html=True)
    for s in rep.get("summary",[]):
        st.markdown(f'<div class="aitem" style="margin-top:8px;"><div class="aitem-dot" style="background:var(--accent);"></div><div class="aitem-text">{s}</div></div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
