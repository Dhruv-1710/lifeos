import streamlit as st
import pandas as pd
from datetime import date, timedelta
from db   import (get_goals, create_goal, add_log, get_logs, update_log, delete_log,
                  compute_status, compute_wellbeing, compute_wellbeing_correlations,
                  compute_insight, compute_patterns, compute_weekly_report,
                  compute_forecast, compute_adaptive_target, compute_heatmap_data,
                  compute_cross_goal_competition, compute_streak, seed_demo_data,
                  get_user_by_id)
from auth import decode_token
from model import get_feature_importances, simulate_success

st.set_page_config(page_title="LifeOS · Dashboard", layout="wide", initial_sidebar_state="expanded")

# ── AUTH GUARD ───────────────────────────────────────────
if not st.session_state.get("user_id"):
    if st.session_state.get("token"):
        uid = decode_token(st.session_state.token)
        if uid: st.session_state.user_id = uid
        else:   st.switch_page("app.py")
    else:
        st.switch_page("app.py")

user_id = st.session_state.user_id
if not st.session_state.get("username"):
    _u = get_user_by_id(user_id)
    if _u: st.session_state.username = _u["username"]
username = st.session_state.get("username") or "User"

GOAL_CATEGORIES = ["General", "Health", "Study", "Career", "Personal", "Finance"]
GOAL_STATUSES   = ["Active", "Paused", "Completed", "Archived"]
GOAL_NAME_EXAMPLES = {
    "General": "e.g. Solve 100 DSA problems", "Health": "e.g. Run 200 km",
    "Study": "e.g. Finish 10 course modules",  "Career": "e.g. Apply to 50 companies",
    "Personal": "e.g. Read 20 books",          "Finance": "e.g. Save ₹50,000",
}
GOAL_TEMPLATES = {
    "Read 20 books this year":      {"target": 20,    "days": 365, "category": "Personal", "notes": "Each book = 1 unit."},
    "Build a workout habit":        {"target": 100,   "days": 180, "category": "Health",   "notes": "Each session = 1 unit."},
    "Write my book":                {"target": 50000, "days": 180, "category": "Personal", "notes": "Log words written."},
    "Learn a new skill":            {"target": 200,   "days": 200, "category": "Career",   "notes": "Log deliberate practice hours."},
    "Save toward a goal":           {"target": 50000, "days": 365, "category": "Finance",  "notes": "Log amount saved."},
    "Land a job or internship":     {"target": 100,   "days": 90,  "category": "Career",   "notes": "Each application = 1 unit."},
    "Build a mindfulness practice": {"target": 100,   "days": 120, "category": "Health",   "notes": "Each session = 1 unit."},
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');
:root{--bg:#0A0E1A;--s1:rgba(255,255,255,0.035);--s2:rgba(255,255,255,0.06);
  --bd:rgba(255,255,255,0.09);--bd2:rgba(255,255,255,0.16);--text:#F4F6FA;
  --muted:#9AA4B8;--subtle:#687089;--accent:#2DD9A8;--accent2:#14B8A0;
  --blue:#3B82F6;--green:#22C55E;--amber:#FBBF24;--red:#F87171;--indigo:#818CF8;}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html,body,[data-testid="stAppViewContainer"],[data-testid="stAppViewContainer"]>.main{
  background:var(--bg)!important;font-family:'Inter',sans-serif!important;color:var(--text)!important;}
.main .block-container{padding:0!important;max-width:100%!important;}
[data-testid="stToolbar"],[data-testid="stDecoration"],#MainMenu,footer{display:none!important;}
/* keep the header shell so the sidebar reopen chevron stays clickable */
[data-testid="stHeader"]{background:transparent!important;box-shadow:none!important;}
[data-testid="stSidebarNav"]{display:none!important;}
[data-testid="stSidebarCollapsedControl"],[data-testid="collapsedControl"]{
  z-index:999999!important;color:var(--muted)!important;}
[data-testid="stSidebarCollapsedControl"] button,[data-testid="collapsedControl"] button{
  background:var(--s2)!important;border:1px solid var(--bd)!important;border-radius:10px!important;}
[data-testid="stAppViewContainer"]::before{content:'';position:fixed;inset:0;z-index:0;pointer-events:none;
  background:radial-gradient(ellipse 900px 500px at 10% 0%,rgba(45,217,168,0.07) 0%,transparent 60%),
  radial-gradient(ellipse 700px 500px at 100% 20%,rgba(59,130,246,0.06) 0%,transparent 60%);}
[data-testid="stSidebar"]{background:#0D1526!important;border-right:1px solid var(--bd)!important;}
[data-testid="stSidebar"] .block-container{padding:28px 22px!important;}
.sb-logo{font-size:18px;font-weight:800;color:var(--text);margin-bottom:28px;letter-spacing:-0.3px;}
.sb-logo em{font-style:normal;background:linear-gradient(90deg,var(--accent),var(--blue));-webkit-background-clip:text;background-clip:text;color:transparent;}
.sb-section{font-size:11px;color:var(--subtle);letter-spacing:0.08em;text-transform:uppercase;font-weight:600;margin-bottom:12px;margin-top:24px;}
.topbar{position:relative;z-index:10;background:#0D1526;border-bottom:1px solid var(--bd);
  padding:16px 32px;display:flex;align-items:center;justify-content:space-between;}
.topbar-logo{font-size:17px;font-weight:800;color:var(--text);}
.topbar-logo em{font-style:normal;background:linear-gradient(90deg,var(--accent),var(--blue));-webkit-background-clip:text;background-clip:text;color:transparent;}
.topbar-user{display:flex;align-items:center;gap:10px;}
.topbar-name{font-size:13px;font-weight:600;color:var(--muted);}
.topbar-dot{width:8px;height:8px;border-radius:50%;background:var(--accent);box-shadow:0 0 10px var(--accent);}
.content{padding:28px 28px 56px;position:relative;z-index:10;}
.slabel{font-size:11px;color:var(--subtle);letter-spacing:0.08em;text-transform:uppercase;font-weight:600;
  padding-bottom:12px;border-bottom:1px solid var(--bd);margin-bottom:18px;
  display:flex;align-items:center;justify-content:space-between;}
.gcard{background:var(--s1);border:1px solid var(--bd);border-radius:14px;padding:20px;
  transition:border-color 0.2s,transform 0.2s;position:relative;overflow:hidden;}
.gcard:hover{border-color:var(--bd2);transform:translateY(-1px);}
.gcard-label{font-size:11px;color:var(--subtle);letter-spacing:0.06em;text-transform:uppercase;font-weight:600;margin-bottom:10px;}
.gcard-val{font-size:32px;font-weight:800;color:var(--text);line-height:1;letter-spacing:-1px;}
.gcard-val em{font-style:normal;color:var(--accent);}
.gcard-sub{font-size:12px;color:var(--muted);margin-top:7px;font-weight:400;}
.pbar-wrap{margin-top:14px;}
.pbar-top{display:flex;justify-content:space-between;font-size:11px;color:var(--subtle);font-weight:500;margin-bottom:5px;}
.pbar-track{height:5px;background:var(--bd);border-radius:4px;position:relative;}
.pbar-fill{position:absolute;top:0;left:0;height:100%;border-radius:4px;transition:width 0.8s ease;}
.pill{display:inline-flex;align-items:center;padding:4px 10px;border-radius:100px;font-size:11px;font-weight:600;border:1px solid;}
.pill-g{color:var(--green);border-color:rgba(34,197,94,0.25);background:rgba(34,197,94,0.10);}
.pill-r{color:var(--red);border-color:rgba(248,113,113,0.25);background:rgba(248,113,113,0.10);}
.pill-a{color:var(--amber);border-color:rgba(251,191,36,0.25);background:rgba(251,191,36,0.10);}
.pill-i{color:var(--indigo);border-color:rgba(129,140,248,0.25);background:rgba(129,140,248,0.10);}
.pill-ac{color:var(--accent);border-color:rgba(45,217,168,0.25);background:rgba(45,217,168,0.10);}
.priority{border:1px solid rgba(248,113,113,0.25);background:rgba(248,113,113,0.06);border-radius:14px;
  padding:18px 22px;display:flex;align-items:center;gap:16px;margin-bottom:20px;}
.priority-left{font-size:11px;color:var(--red);letter-spacing:0.06em;text-transform:uppercase;font-weight:700;white-space:nowrap;}
.priority-divider{width:1px;height:32px;background:rgba(248,113,113,0.25);}
.priority-name{font-size:17px;font-weight:700;color:var(--text);}
.priority-stat{margin-left:auto;font-size:11px;color:var(--muted);text-align:right;font-weight:500;}
.knums{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.knum{background:var(--s1);border:1px solid var(--bd);border-radius:14px;padding:18px;}
.knum-label{font-size:11px;color:var(--subtle);letter-spacing:0.06em;text-transform:uppercase;font-weight:600;margin-bottom:7px;}
.knum-val{font-size:26px;font-weight:800;color:var(--text);line-height:1;letter-spacing:-0.5px;}
.knum-val em{font-style:normal;color:var(--accent);font-size:22px;}
.analysis-card{border:1px solid var(--bd);border-radius:14px;padding:16px;background:var(--s1);}
.analysis-card-label{font-size:11px;color:var(--subtle);letter-spacing:0.06em;text-transform:uppercase;font-weight:600;margin-bottom:12px;}
.aitem{display:flex;align-items:flex-start;gap:10px;padding:7px 0;border-bottom:1px solid var(--bd);}
.aitem:last-child{border-bottom:none;}
.aitem-dot{width:5px;height:5px;border-radius:50%;margin-top:7px;flex-shrink:0;}
.aitem-text{font-size:13px;color:var(--muted);font-weight:400;line-height:1.5;}
.icard{border:1px solid var(--bd);border-radius:14px;padding:18px;margin-bottom:12px;background:var(--s1);}
.icard-label{font-size:11px;color:var(--accent);letter-spacing:0.06em;text-transform:uppercase;font-weight:600;margin-bottom:9px;}
.icard-text{font-size:13px;color:var(--muted);font-weight:400;line-height:1.65;}
.icard-text strong{color:var(--text);font-weight:600;}
.wb-big{font-size:52px;font-weight:800;line-height:1;letter-spacing:-1.5px;}
.heatmap-scroll{overflow-x:auto;padding-bottom:6px;}
.heatmap-months{display:flex;align-items:flex-end;margin-bottom:4px;height:14px;}
.heatmap-month-label{font-family:'JetBrains Mono',monospace;font-size:10px;color:var(--subtle);white-space:nowrap;overflow:hidden;}
.heatmap-grid{display:grid;grid-auto-flow:column;grid-template-rows:repeat(7,13px);grid-auto-columns:13px;gap:3px;}
.heatmap-cell{width:13px;height:13px;border-radius:3px;}
.hm-b0{background:var(--bd);}.hm-b1{background:rgba(45,217,168,0.22);}
.hm-b2{background:rgba(45,217,168,0.42);}.hm-b3{background:rgba(45,217,168,0.68);}.hm-b4{background:var(--accent);}
.heatmap-legend{display:flex;align-items:center;gap:5px;margin-top:10px;font-size:10px;color:var(--subtle);font-weight:500;text-transform:uppercase;letter-spacing:0.04em;}
.goal-row{background:var(--s1);border:1px solid var(--bd);border-radius:14px;padding:16px 20px;
  margin-bottom:10px;display:flex;align-items:center;gap:14px;transition:border-color 0.2s;}
.goal-row:hover{border-color:var(--bd2);}
.goal-row-name{font-size:14px;font-weight:700;color:var(--text);}
.goal-row-meta{font-size:11px;color:var(--subtle);font-weight:500;margin-top:3px;}
.wb-tile{background:var(--s1);border:1px solid var(--bd);border-radius:14px;padding:14px 16px;}
.wb-tile-name{font-size:10px;color:var(--subtle);letter-spacing:0.07em;text-transform:uppercase;font-weight:600;}
.wb-tile-val{font-size:22px;font-weight:800;color:var(--text);margin-top:4px;letter-spacing:-0.5px;}
.wb-tile-bar{height:5px;border-radius:4px;background:var(--bd);margin-top:9px;}
.wb-tile-fill{height:100%;border-radius:4px;}
.wb-tile-status{font-size:10px;font-weight:600;margin-top:7px;letter-spacing:0.04em;text-transform:uppercase;}
.goal-meta-tag{display:inline-flex;align-items:center;font-size:10px;color:var(--muted);font-weight:600;
  letter-spacing:0.04em;text-transform:uppercase;border:1px solid var(--bd2);border-radius:100px;padding:3px 9px;margin-right:6px;}
div[data-testid="stTextInput"]>label,div[data-testid="stTextArea"]>label,
div[data-testid="stNumberInput"]>label,div[data-testid="stDateInput"]>label,
div[data-testid="stSelectbox"]>label,div[data-testid="stMultiSelect"]>label,
div[data-testid="stSlider"]>label,div[data-testid="stCheckbox"]>label{
  font-size:11px!important;font-weight:600!important;color:var(--muted)!important;letter-spacing:0.06em!important;text-transform:uppercase!important;}
div[data-testid="stTextInput"] input,div[data-testid="stNumberInput"] input,div[data-testid="stTextArea"] textarea{
  background:rgba(255,255,255,0.04)!important;border:1px solid var(--bd)!important;border-radius:10px!important;
  color:var(--text)!important;font-family:'Inter',sans-serif!important;font-size:14px!important;padding:9px 12px!important;box-shadow:none!important;}
div[data-testid="stTextInput"] input:focus,div[data-testid="stNumberInput"] input:focus,div[data-testid="stTextArea"] textarea:focus{
  border-color:var(--accent)!important;box-shadow:0 0 0 3px rgba(45,217,168,0.12)!important;}
div[data-testid="stButton"]>button{background:linear-gradient(90deg,var(--accent2),var(--accent))!important;
  color:#06231C!important;font-weight:700!important;font-size:12px!important;border:none!important;
  border-radius:10px!important;padding:9px 18px!important;transition:all 0.2s!important;
  box-shadow:0 2px 14px rgba(45,217,168,0.18)!important;}
div[data-testid="stButton"]>button:hover{filter:brightness(1.08);transform:translateY(-1px);}
div[data-baseweb="select"]>div{background:rgba(255,255,255,0.04)!important;border:1px solid var(--bd)!important;
  border-radius:10px!important;color:var(--text)!important;font-family:'Inter',sans-serif!important;}
div[data-testid="stMetric"]{background:var(--s1)!important;border:1px solid var(--bd)!important;border-radius:14px!important;padding:16px 18px!important;}
div[data-testid="stMetricLabel"]{font-size:11px!important;color:var(--subtle)!important;font-weight:600!important;text-transform:uppercase!important;letter-spacing:0.06em!important;}
div[data-testid="stMetricValue"]{font-size:24px!important;font-weight:800!important;color:var(--text)!important;letter-spacing:-0.5px!important;}
div[data-testid="stAlert"]{border-radius:10px!important;font-size:13px!important;background:var(--s1)!important;border:1px solid var(--bd)!important;padding:10px 14px!important;}
hr{border-color:var(--bd)!important;margin:22px 0!important;}
div[data-testid="stExpander"]{background:var(--s1)!important;border:1px solid var(--bd)!important;border-radius:14px!important;}
div[data-testid="stExpander"] summary{font-size:12px!important;font-weight:600!important;color:var(--muted)!important;}
button[data-baseweb="tab"]{font-size:12px!important;color:var(--subtle)!important;font-weight:600!important;}
button[data-baseweb="tab"][aria-selected="true"]{color:var(--accent)!important;}
div[data-baseweb="tab-highlight"]{background:var(--accent)!important;height:2px!important;border-radius:2px;}
div[data-baseweb="tab-border"]{background:var(--bd)!important;}
div[data-testid="stDataFrame"]{border:1px solid var(--bd)!important;border-radius:12px!important;overflow:hidden;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

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
    st.markdown('<div class="sb-section">Navigation</div>', unsafe_allow_html=True)
    if st.button("👤  Profile & Goals", use_container_width=True, key="goto_profile"):
        st.switch_page("pages/profile.py")
    st.divider()
    st.markdown('<div class="sb-section">Quick Log</div>', unsafe_allow_html=True)
    st.caption("Select a goal below to log progress from the dashboard.")
    st.divider()
    if st.button("Sign out", use_container_width=True, key="signout"):
        for k in ["token","user_id","username"]: st.session_state[k] = None
        st.switch_page("app.py")

# ── CONTENT ──────────────────────────────────────────────
st.markdown('<div class="content">', unsafe_allow_html=True)

# ── LOAD GOALS ───────────────────────────────────────────
goals = get_goals(user_id, include_archived=False)

if not goals:
    # Onboarding wizard
    if "onb_step" not in st.session_state:
        st.session_state.onb_step = 1
    step = st.session_state.onb_step
    st.markdown('<div class="slabel"><span>Welcome — set up your first goal</span></div>', unsafe_allow_html=True)
    dcol1, dcol2 = st.columns([3, 1])
    with dcol1:
        st.caption(f"Step {step} of 3")
    with dcol2:
        if st.button("✨ Try with demo data", key="seed_demo", use_container_width=True,
                     help="Creates two sample goals (one on track, one at risk) with 6 weeks of realistic logs — comparison, priority and interaction features included. Delete them anytime."):
            ok, msg = seed_demo_data(user_id)
            if ok: st.success(msg); st.rerun()
            else:  st.info(msg)

    if step == 1:
        st.markdown("##### What are you working toward?")
        st.selectbox("Pick a category", GOAL_CATEGORIES, key="onb_category")
        if st.button("Next →", key="onb_next1"):
            st.session_state.onb_step = 2; st.rerun()

    elif step == 2:
        st.markdown("##### Goal details")
        _cat = st.session_state.get("onb_category","General")
        st.text_input("Goal name", placeholder=GOAL_NAME_EXAMPLES.get(_cat,""), key="onb_name")
        st.number_input("Target units", min_value=1, value=100, key="onb_target")
        st.date_input("Deadline", value=date.today()+timedelta(days=90), key="onb_deadline")
        b1,b2 = st.columns(2)
        if b1.button("← Back", key="onb_b2", use_container_width=True): st.session_state.onb_step=1; st.rerun()
        if b2.button("Review →", key="onb_n2", use_container_width=True):
            if not st.session_state.get("onb_name","").strip(): st.warning("Enter a goal name")
            else: st.session_state.onb_step=3; st.rerun()

    elif step == 3:
        st.markdown("##### Review")
        st.markdown(f"""<div class="icard"><div class="icard-label">{st.session_state.get('onb_category','General')}</div>
          <div class="icard-text"><strong>{st.session_state.get('onb_name','')}</strong><br>
          Target: {st.session_state.get('onb_target',100)} units · Due: {st.session_state.get('onb_deadline')}</div></div>""", unsafe_allow_html=True)
        b1,b2 = st.columns(2)
        if b1.button("← Back", key="onb_b3", use_container_width=True): st.session_state.onb_step=2; st.rerun()
        if b2.button("Create goal →", key="onb_create", use_container_width=True):
            ok, msg = create_goal(user_id, st.session_state["onb_name"], st.session_state["onb_target"],
                                   st.session_state["onb_deadline"], category=st.session_state.get("onb_category","General"))
            if ok:
                for k in ["onb_step","onb_category","onb_name","onb_target","onb_deadline"]: st.session_state.pop(k,None)
                st.success(msg); st.balloons(); st.rerun()
            else: st.error(msg)
    st.stop()

# ── HEADER ───────────────────────────────────────────────
_active_ct = sum(1 for g in goals if g.get("status", "Active") == "Active")
_plural = "s" if _active_ct != 1 else ""
st.markdown(
    f'<div style="font-size:24px;font-weight:800;letter-spacing:-0.5px;color:var(--text);">Welcome back, {username}</div>'
    f'<div style="font-size:13px;color:var(--muted);margin:4px 0 20px;">{date.today().strftime("%A, %d %B %Y")} · {_active_ct} active goal{_plural}</div>',
    unsafe_allow_html=True)

# ── GOAL SELECTOR (active goals pre-selected — no empty first screen) ──
goal_map = {g["name"]: g for g in goals}
_default = [g["name"] for g in goals if g.get("status", "Active") == "Active"][:4] or [goals[0]["name"]]
selected = st.multiselect("Select goals to track", list(goal_map.keys()), default=_default, placeholder="Choose goals…")

if not selected:
    st.markdown('<div style="padding:40px 0;font-family:JetBrains Mono,monospace;font-size:10px;color:var(--subtle);letter-spacing:0.15em;text-transform:uppercase;">↑ Select one or more goals above to view your dashboard</div>', unsafe_allow_html=True)
    st.stop()

selected_goals = [goal_map[s] for s in selected]
selected_ids   = [g["id"] for g in selected_goals]

# ── CACHE ────────────────────────────────────────────────
@st.cache_data(ttl=30)
def cached_logs(gid, uid): return get_logs(gid, uid)

@st.cache_data(ttl=30)
def cached_status(gid, uid, _goal):
    # gid+uid form the cache key; _goal (underscore = unhashed) is only the
    # payload. The old version had ONLY an underscore param, so every goal
    # shared one cache entry and showed identical stats.
    logs = get_logs(gid, uid)
    return compute_status(_goal, logs)

def status_for(g):
    return cached_status(g["id"], user_id, dict(g))

# ── OVERVIEW CARDS ───────────────────────────────────────
st.markdown('<div class="slabel"><span>Overview</span></div>', unsafe_allow_html=True)
cols = st.columns(len(selected_goals))
for i, g in enumerate(selected_goals):
    s = status_for(g)
    if not s: continue
    is_active = g.get("status","Active") == "Active"
    lc    = s.get("low_confidence")
    prob  = s["success_probability"]
    if lc:
        color = "var(--indigo)"; prob_html = f"day {s.get('days_of_history',0)}/7"; bar_w = 0; pstat = "pill-i"
    else:
        color = "var(--green)" if prob>70 else ("var(--amber)" if prob>40 else "var(--red)")
        pstat = "pill-g" if prob>70 else ("pill-a" if prob>40 else "pill-r")
        prob_html = f"{prob}%"; bar_w = prob
    sp    = f'<span class="{pstat} pill">{s["status"]}</span>' if is_active else '<span class="pill-i pill">Paused</span>'
    op    = "" if is_active else "opacity:0.6;filter:grayscale(0.35);"
    with cols[i]:
        st.markdown(f"""
        <div class="gcard" style="{op}">
          <div class="gcard-label">{g['name']}</div>
          <span class="goal-meta-tag">{g.get('category','General')}</span>
          <span class="goal-meta-tag">{g.get('status','Active')}</span>
          <div class="gcard-val" style="margin-top:12px;">{s['progress']}<em>%</em></div>
          <div class="gcard-sub">complete · {round(s['required_per_day'],1)} units/day needed</div>
          <div class="pbar-wrap">
            <div class="pbar-top"><span>Success probability</span><span style="color:{color};">{prob_html}</span></div>
            <div class="pbar-track"><div class="pbar-fill" style="width:{bar_w}%;background:{color};"></div></div>
          </div>
          <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap;">
            {sp}<span class="pill-ac pill">avg {round(s['current_avg'],1)}/day</span>
          </div>
        </div>""", unsafe_allow_html=True)

# ── PRIORITY ─────────────────────────────────────────────
pd_list = []
for g in selected_goals:
    if g.get("status","Active") != "Active": continue
    s    = status_for(g)
    logs = cached_logs(g["id"], user_id)
    if not s or s.get("low_confidence"): continue
    done_v = [l["done"] for l in logs[-7:]]
    cons   = sum(1 for x in done_v if x>0) / max(len(done_v),1)
    score  = s["required_per_day"]*2 - s["current_avg"] + (1-cons)*5
    pd_list.append({"goal":g,"score":score,"status":s})

if pd_list:
    worst = max(pd_list, key=lambda x: x["score"])
    st.markdown(f"""
    <div style="margin-top:16px;">
    <div class="priority">
      <span class="priority-left">⚠ Priority</span>
      <div class="priority-divider"></div>
      <div>
        <div class="priority-name">{worst['goal']['name']}</div>
        <div style="font-family:'JetBrains Mono',monospace;font-size:9px;color:var(--muted);letter-spacing:0.1em;text-transform:uppercase;margin-top:3px;">Needs immediate attention</div>
      </div>
      <div class="priority-stat">
        <div style="color:var(--red);">{worst['status']['success_probability']}%</div>
        <div>success probability</div>
      </div>
    </div></div>""", unsafe_allow_html=True)

st.divider()

# ── GOAL COMPARISON — which goal is fine, which needs attention ──
if len(selected_goals) >= 2:
    _comp = [(g, status_for(g)) for g in selected_goals]
    _comp = [(g, s) for g, s in _comp if s]
    ranked  = [(g, s) for g, s in _comp if not s.get("low_confidence") and s.get("status") != "No Data"]
    warming = [(g, s) for g, s in _comp if s.get("low_confidence")]
    if ranked:
        ranked.sort(key=lambda c: c[1]["success_probability"], reverse=True)
        st.markdown('<div class="slabel"><span>Goal Comparison — where to focus</span></div>', unsafe_allow_html=True)
        rows_html = ""
        for i, (g, s) in enumerate(ranked):
            prob  = s["success_probability"]
            pace  = s["current_avg"] / max(s["required_per_day"], 0.001)
            color = "var(--green)" if prob > 70 else ("var(--amber)" if prob > 40 else "var(--red)")
            if i == 0 and prob > 60:
                tag = '<span style="color:var(--green);">✅ Doing well — keep momentum</span>'
            elif i == len(ranked) - 1 and prob <= 60:
                tag = '<span style="color:var(--red);">🎯 Focus here first</span>'
            elif prob <= 40:
                tag = '<span style="color:var(--amber);">⚠ Needs attention</span>'
            else:
                tag = '<span style="color:var(--muted);">On watch</span>'
            rows_html += f'''<div class="goal-row">
              <div style="flex:1;min-width:0;">
                <div class="goal-row-name">{g["name"]}</div>
                <div class="goal-row-meta">pace {round(pace*100)}% of required · avg {round(s["current_avg"],1)}/day vs {round(s["required_per_day"],1)} needed</div>
              </div>
              <div style="width:110px;flex-shrink:0;"><div class="pbar-track"><div class="pbar-fill" style="width:{min(prob,100)}%;background:{color};"></div></div></div>
              <div style="width:48px;text-align:right;font-weight:800;color:{color};flex-shrink:0;">{round(prob)}%</div>
              <div style="width:200px;font-size:11px;text-align:right;flex-shrink:0;">{tag}</div>
            </div>'''
        st.markdown(rows_html, unsafe_allow_html=True)
        if warming:
            st.caption("Still collecting data: " + ", ".join(g["name"] for g, _ in warming))
        st.divider()

# ── GOAL INTERACTIONS ────────────────────────────────────
if len(selected_goals) >= 2:
    glm = {g["name"]: cached_logs(g["id"], user_id) for g in selected_goals}
    notable = [it for it in compute_cross_goal_competition(glm) if it["relationship"] != "independent"]
    if notable:
        st.markdown('<div class="slabel"><span>Goal Interactions</span></div>', unsafe_allow_html=True)
        for it in notable[:4]:
            c   = "var(--red)" if it["relationship"]=="competing" else "var(--green)"
            vrb = "tend to trade off — more on one usually means less on the other" if it["relationship"]=="competing" \
                  else "tend to move together — busy days lift both"
            st.markdown(f"""<div class="icard" style="margin-bottom:8px;">
              <div class="icard-label" style="display:flex;justify-content:space-between;">
                <span>{it['goal_a']} ↔ {it['goal_b']}</span><span style="color:{c};">r = {it['r']}</span></div>
              <div class="icard-text">These goals {vrb} ({it['n_days']} overlapping days).</div></div>""", unsafe_allow_html=True)
        st.caption("Correlation, not causation — goals may simply react to the same busy or quiet stretches.")
        st.divider()

# ── DETAILED VIEW ────────────────────────────────────────
st.markdown('<div class="slabel"><span>Detailed Analysis</span></div>', unsafe_allow_html=True)
goal_labels  = {g["id"]: g["name"] for g in selected_goals}
selected_gid = st.selectbox("Goal", selected_ids, format_func=lambda gid: goal_labels.get(gid,str(gid)), label_visibility="collapsed")
goal    = next(g for g in selected_goals if g["id"]==selected_gid)
logs    = cached_logs(selected_gid, user_id)
status  = status_for(goal)
if not status: st.error("Failed to compute status"); st.stop()

if goal.get("notes"):
    st.markdown(f'<div class="icard"><div class="icard-label">Why this matters</div><div class="icard-text">{goal["notes"]}</div></div>', unsafe_allow_html=True)

# ── QUICK LOG ────────────────────────────────────────────
qc1, qc2, qc3 = st.columns([3,1,1])
with qc1:
    quick_done = st.number_input(f"Quick log — units done today", min_value=0, value=0, key="ql_done")
with qc2:
    st.markdown("<div style='height:27px'></div>", unsafe_allow_html=True)
    if st.button("Log →", key="ql_btn", use_container_width=True):
        add_log(selected_gid, user_id, quick_done, 3, 3, 0, 3, 7.0)
        st.success("Logged (neutral defaults — use 'Detailed Log' below for mood/energy/sleep).")
        cached_logs.clear(); cached_status.clear(); st.rerun()

# ── KEY NUMBERS ──────────────────────────────────────────
prob  = status["success_probability"]
if status.get("low_confidence"):
    color = "var(--indigo)"; prob_cell = "—"
else:
    color = "var(--green)" if prob>70 else ("var(--amber)" if prob>40 else "var(--red)")
    prob_cell = f"{prob}<em>%</em>"
st.markdown(f"""
<div class="knums" style="margin-top:16px;">
  <div class="knum"><div class="knum-label">Progress</div><div class="knum-val">{status['progress']}<em>%</em></div></div>
  <div class="knum"><div class="knum-label">Success Probability</div><div class="knum-val" style="color:{color};">{prob_cell}</div></div>
  <div class="knum"><div class="knum-label">Required / Day</div><div class="knum-val">{round(status['required_per_day'],1)}</div></div>
  <div class="knum"><div class="knum-label">Current Average</div><div class="knum-val">{round(status['current_avg'],1)}</div></div>
</div>""", unsafe_allow_html=True)
if status.get("low_confidence"):
    st.caption(f"📊 Collecting data — day {status.get('days_of_history',0)} of 7. Predictions unlock after a full week of history.")

# ── MILESTONES ───────────────────────────────────────────
MARKS = [25, 50, 75, 100]
pp    = status["progress"]
mk    = f"ms_{selected_gid}"
last  = st.session_state.get(mk, 0)
reached_ms = [m for m in MARKS if pp >= m]
if reached_ms and max(reached_ms) > last:
    st.session_state[mk] = max(reached_ms)
    st.balloons(); st.success(f"🎉 {max(reached_ms)}% milestone reached!")

segs   = "".join([f'<div style="flex:1;height:6px;border-radius:2px;background:{"var(--accent)" if pp>=m else "var(--bd2)"};"></div>' for m in MARKS])
labels = "".join([f'<span style="flex:1;text-align:center;">{m}%{" ✓" if pp>=m else ""}</span>' for m in MARKS])
st.markdown(f"""<div style="margin-top:14px;">
  <div style="display:flex;gap:4px;">{segs}</div>
  <div style="display:flex;margin-top:4px;font-family:JetBrains Mono,monospace;font-size:9px;color:var(--subtle);">{labels}</div>
</div>""", unsafe_allow_html=True)

st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# ── AI ANALYSIS ──────────────────────────────────────────
if status.get("reasons") or status.get("positives"):
    st.markdown('<div class="slabel"><span>AI Analysis</span></div>', unsafe_allow_html=True)
    cr, cp = st.columns(2)
    with cr:
        if status.get("reasons"):
            items = "".join([f'<div class="aitem"><div class="aitem-dot" style="background:var(--red);"></div><div class="aitem-text">{r.capitalize()}</div></div>' for r in status["reasons"]])
            st.markdown(f'<div class="analysis-card"><div class="analysis-card-label">Risk factors</div>{items}</div>', unsafe_allow_html=True)
    with cp:
        if status.get("positives"):
            items = "".join([f'<div class="aitem"><div class="aitem-dot" style="background:var(--green);"></div><div class="aitem-text">{p.capitalize()}</div></div>' for p in status["positives"]])
            st.markdown(f'<div class="analysis-card"><div class="analysis-card-label">Strengths</div>{items}</div>', unsafe_allow_html=True)

st.divider()

# ── MODEL INSIGHTS ───────────────────────────────────────
st.markdown('<div class="slabel"><span>Model Insights</span></div>', unsafe_allow_html=True)
fi_col, sim_col = st.columns(2)
with fi_col:
    st.markdown('<div class="analysis-card-label" style="margin-bottom:10px;">What drives this prediction</div>', unsafe_allow_html=True)
    imp = get_feature_importances()
    if imp is None:
        st.caption("No trained model.pkl found — using pace-based fallback. Train and commit model.pkl to enable this.")
    else:
        top   = imp[:5]
        fi_df = pd.DataFrame({"Importance":[i for _,_,i in top]}, index=[l for _,l,_ in top])
        st.bar_chart(fi_df, height=200, color="#2DD9A8")
        st.caption("Relative importance from the trained RandomForest model.")
with sim_col:
    st.markdown('<div class="analysis-card-label" style="margin-bottom:10px;">What-if simulator</div>', unsafe_allow_html=True)
    wd = status.get("window_done",[])
    ws = status.get("window_screen",[])
    if len(wd) < 7:
        st.caption("Need 7 days of logs to enable the simulator.")
    else:
        cur_cons   = sum(1 for x in wd if x>0)/len(wd)
        cur_screen = sum(ws)/max(len(ws),1)
        cur_missed = sum(1 for x in wd if x==0)
        sc = st.slider("Consistency (%)", 0, 100, int(cur_cons*100), key="sc")
        ss = st.slider("Screen time (min/day)", 0, 240, int(cur_screen), key="ss")
        sm = st.slider("Missed days", 0, 7, cur_missed, key="sm")
        sp = simulate_success(wd, ws, status["required_per_day"], overrides={"consistency":sc/100,"screen":ss,"missed":sm})
        bl = status["success_probability"]/100
        c1,c2 = st.columns(2)
        c1.metric("Current", f"{bl*100:.0f}%")
        if sp is not None:
            c2.metric("Simulated", f"{sp*100:.0f}%", delta=f"{(sp-bl)*100:+.0f}%")
        st.caption("Adjusting sliders doesn't change your real data.")

st.divider()

# ── DETAILED LOG ─────────────────────────────────────────
st.markdown('<div class="slabel"><span>Detailed Log</span></div>', unsafe_allow_html=True)
with st.expander("Log this session — mood, energy, screen time, sleep"):
    ca, cb, cc = st.columns(3)
    with ca:
        done        = st.number_input("Work done (units)", min_value=0, value=0, key="dl_done")
        screen_time = st.number_input("Screen time (min)", min_value=0, value=0, key="dl_screen")
    with cb:
        mood   = st.slider("Mood",   1, 5, 3, key="dl_mood")
        energy = st.slider("Energy", 1, 5, 3, key="dl_energy")
        stress = st.slider("Stress", 1, 5, 3, key="dl_stress")
    with cc:
        # Sleep is a daily snapshot — shown here since this is the full-detail log
        sleep = st.number_input("Sleep last night (hrs)", 0.0, 24.0, 7.0, 0.5, key="dl_sleep",
                                help="How many hours did you sleep? This is a daily value — logged once per day.")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Save log →", use_container_width=True, key="dl_save"):
            add_log(selected_gid, user_id, done, mood, energy, screen_time, stress, sleep)
            st.success("Saved.")
            cached_logs.clear(); cached_status.clear(); st.rerun()

# ── WELLBEING ────────────────────────────────────────────
wb    = compute_wellbeing(logs)
score = wb["score"]
wc    = "var(--green)" if score>70 else ("var(--amber)" if score>40 else "var(--red)")
st.markdown('<div class="slabel" style="margin-top:24px;"><span>Wellbeing &amp; Mental Health</span></div>', unsafe_allow_html=True)
cw1, cw2 = st.columns([1, 3])
with cw1:
    st.markdown(f'<div class="gcard" style="text-align:center;"><div class="gcard-label">Score</div><div class="wb-big" style="color:{wc};">{score}</div><div class="gcard-sub">/100 · last {wb.get("n_days",0)} logged days</div></div>', unsafe_allow_html=True)
with cw2:
    factors = wb.get("factors", [])
    if factors:
        BAND = {"good": ("var(--green)", "Good"), "ok": ("var(--amber)", "Okay"), "low": ("var(--red)", "Needs attention")}
        tiles = ""
        for f in factors:
            fcol, flab = BAND.get(f["band"], ("var(--muted)", ""))
            note = " · lower is better" if f["name"] == "Stress" else ""
            tiles += f'''<div class="wb-tile">
              <div class="wb-tile-name">{f["name"]}{note}</div>
              <div class="wb-tile-val">{f["display"]}</div>
              <div class="wb-tile-bar"><div class="wb-tile-fill" style="width:{f["score"]}%;background:{fcol};"></div></div>
              <div class="wb-tile-status" style="color:{fcol};">{flab}</div>
            </div>'''
        st.markdown(f'<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;">{tiles}</div>', unsafe_allow_html=True)
    else:
        st.caption("Log mood, energy, stress and sleep in the Detailed Log to see your breakdown.")

st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)
st.markdown('<div class="analysis-card"><div class="analysis-card-label">What to do for your mental health</div>' +
    "".join(f'<div class="aitem"><div class="aitem-dot" style="background:var(--accent);"></div><div class="aitem-text">{sg}</div></div>' for sg in wb.get("suggestions", [])) +
    '</div>', unsafe_allow_html=True)
st.caption("General lifestyle suggestions based on your logs — not medical advice. If low mood or stress persists, please talk to someone you trust or a professional.")

st.divider()

# ── CORRELATION ANALYSIS ─────────────────────────────────
st.markdown('<div class="slabel"><span>Correlation Analysis</span></div>', unsafe_allow_html=True)
corr = compute_wellbeing_correlations(logs)
if not corr["available"]:
    st.caption(corr["reason"])
else:
    results = corr["results"]
    if not results:
        st.caption("Not enough variation in logs yet to compute correlations.")
    else:
        cc1, cc2 = st.columns(2)
        with cc1:
            for r in results:
                rc  = "var(--green)" if r["direction"]=="positive" else "var(--red)"
                sgn = "+" if r["r"]>=0 else "−"
                dw  = "higher" if r["direction"]=="positive" else "lower"
                st.markdown(f"""<div class="icard" style="margin-bottom:8px;">
                  <div class="icard-label" style="display:flex;justify-content:space-between;">
                    <span>{r['factor']}</span><span style="color:{rc};">r = {sgn}{abs(r['r'])}</span></div>
                  <div class="icard-text"><strong>{r['strength'].capitalize()} {r['direction']}</strong> — higher {r['factor'].lower()} tends to coincide with {dw} output.</div>
                </div>""", unsafe_allow_html=True)
        with cc2:
            top = results[0]
            sdf = corr["scatter_df"][[top["column"],"done"]].rename(columns={top["column"]:top["factor"],"done":"Output"})
            st.caption(f"Strongest: {top['factor']} vs Output")
            st.scatter_chart(sdf, x=top["factor"], y="Output", height=240, color="#2DD9A8")
        st.caption(f"Based on {corr['n']} days · Correlation ≠ causation.")

st.divider()

# ── PERFORMANCE CHARTS ───────────────────────────────────
if logs:
    st.markdown('<div class="slabel"><span>Performance</span></div>', unsafe_allow_html=True)
    df   = pd.DataFrame(logs)
    df["date"] = pd.to_datetime(df["date"])
    df   = df.sort_values("date")
    view = st.selectbox("View", ["Daily","Cumulative","Weekly"], label_visibility="collapsed")
    req  = status["required_per_day"]
    tgt  = goal.get("target")
    dl   = goal.get("deadline")

    if view == "Daily":
        ds  = df.groupby(df["date"].dt.normalize())["done"].sum().asfreq("D", fill_value=0)
        ddf = pd.DataFrame({"done": ds, "required": req})
        st.line_chart(ddf, height=240, color=["#2DD9A8","#5A6379"])

    elif view == "Cumulative":
        sp0 = goal.get("starting_point") or 0
        df["cumulative"] = df["done"].cumsum() + sp0
        # Ideal pace = straight line from start to the target at the
        # deadline (the old per-log-entry pace line was meaningless)
        pace_df = None
        if tgt and dl:
            first_day = df["date"].min().normalize()
            dl_dt     = pd.to_datetime(dl)
            if dl_dt > first_day:
                span    = max((dl_dt - first_day).days, 1)
                pidx    = pd.date_range(first_day, dl_dt, freq="D")
                pace_df = pd.DataFrame({"date": pidx,
                                        "target pace": [sp0 + (tgt - sp0) * ((d - first_day).days / span) for d in pidx]})
        fc = compute_forecast(goal, logs)
        if not fc["available"]:
            st.caption(fc["reason"])
        else:
            fdf = pd.DataFrame({"date":fc["forecast_dates"],"forecast":fc["forecast_cumulative"]})
            frames = [df[["date","cumulative"]], fdf] + ([pace_df] if pace_df is not None else [])
            cdf = pd.concat(frames).sort_values("date").set_index("date")
            st.line_chart(cdf, height=240)
            ml  = "Trend-aware (Holt's)" if fc["method"]=="trend_aware" else "Simple average (need 14+ days for trend)"
            st.caption(f"Forecast method: {ml}")
            if tgt:
                if fc["completion_date"]:
                    comp = fc["completion_date"].date()
                    st.markdown(f'<div class="icard" style="margin-top:12px;"><div class="icard-label">Forecast</div><div class="icard-text">Predicted completion: <strong>{comp}</strong></div></div>', unsafe_allow_html=True)
                    if dl:
                        diff = (pd.to_datetime(dl).date()-comp).days
                        if diff>0: st.success(f"{diff} days ahead of deadline")
                        elif diff==0: st.warning("On deadline — no buffer")
                        else: st.error(f"{abs(diff)} days behind deadline")
                elif fc["capped"]:
                    st.warning("At current pace, goal won't be reached within 90 days.")

        if tgt and dl:
            dl_dt = pd.to_datetime(dl)
            days_left = (dl_dt-df["date"].max()).days
            if days_left>0:
                done_sf = df["cumulative"].iloc[-1]
                rem     = tgt-done_sf
                if rem>0:
                    req_now = rem/days_left
                    gap     = req_now-status["current_avg"]
                    st.markdown('<div class="slabel" style="margin-top:24px;"><span>Planning Engine</span></div>', unsafe_allow_html=True)
                    adt = compute_adaptive_target(req_now, logs)
                    p1,p2 = st.columns(2)
                    p1.metric("Required / day now", round(req_now,1))
                    if adt["available"]:
                        p2.metric("Today's adjusted target", adt["adjusted_target"],
                                  delta=f"{adt['adjustment_pct']:+.0f}%" if adt["adjustment_pct"]!=0 else None)
                    else:
                        p2.metric("Today's target", round(req_now,1))
                    if gap>0: st.warning(f"Increase by {round(gap,1)} units/day to stay on track")
                    else: st.success("Ahead of pace — keep going")
                    if adt.get("available") and adt.get("factors"):
                        tag = ", ".join(adt["factors"])
                        if adt["is_reduced"]:
                            st.markdown(f'<div class="icard" style="margin-top:10px;"><div class="icard-label">Target eased — {tag}</div><div class="icard-text">Today only — the shortfall appears as a slightly higher required pace on remaining days.</div></div>', unsafe_allow_html=True)
                        elif adt["is_boosted"]:
                            st.markdown(f'<div class="icard" style="margin-top:10px;"><div class="icard-label">Target nudged up — {tag}</div><div class="icard-text">Checking in well today — good window to push ahead of pace.</div></div>', unsafe_allow_html=True)
    else:
        dfw = df.resample("W", on="date")["done"].sum()
        st.bar_chart(dfw, height=240, color="#2DD9A8")

st.divider()

# ── CONSISTENCY & HEATMAP ────────────────────────────────
if logs:
    st.markdown('<div class="slabel"><span>Consistency</span></div>', unsafe_allow_html=True)
    streak = compute_streak(logs)
    _ad = pd.DataFrame(logs)
    _ad["day"] = pd.to_datetime(_ad["date"]).dt.date
    active_days = int(_ad.groupby("day")["done"].sum().gt(0).sum())
    _sday = "s" if streak != 1 else ""
    c1,c2,c3 = st.columns(3)
    c1.metric("Streak",      f"{streak} day{_sday}")
    c2.metric("Total logs",  len(logs))
    c3.metric("Active days", active_days)

    hm = compute_heatmap_data(logs, weeks=18)
    if hm["available"]:
        CELL=16
        lh=""
        for idx,(wi,lb) in enumerate(hm["month_labels"]):
            nw = hm["month_labels"][idx+1][0] if idx+1<len(hm["month_labels"]) else len(hm["weeks"])
            lh += f'<div class="heatmap-month-label" style="width:{(nw-wi)*CELL}px;">{lb}</div>'
        ch=""
        for week in hm["weeks"]:
            for d in week:
                tt = f'{d["date"].strftime("%d %b %Y")} · {d["value"]:g} units'
                ch += f'<div class="heatmap-cell hm-b{d["bucket"]}" title="{tt}"></div>'
        st.markdown(f"""<div class="heatmap-scroll"><div class="heatmap-months">{lh}</div>
          <div class="heatmap-grid">{ch}</div>
          <div class="heatmap-legend"><span>Less</span>
          <div class="heatmap-cell hm-b0"></div><div class="heatmap-cell hm-b1"></div>
          <div class="heatmap-cell hm-b2"></div><div class="heatmap-cell hm-b3"></div>
          <div class="heatmap-cell hm-b4"></div><span>More</span>
          <span style="margin-left:12px;">{hm['active_days']} active days of last {hm['total_days']}</span>
          </div></div>""", unsafe_allow_html=True)

    df3 = pd.DataFrame(logs)
    df3["date"] = pd.to_datetime(df3["date"])
    st.dataframe(df3.tail(30)[["date","done","mood","energy","stress","sleep"]].set_index("date"), use_container_width=True)

    with st.expander("⚙ Manage Logs — edit or delete individual entries"):
        recent = sorted(logs, key=lambda l: l["date"], reverse=True)[:50]
        if recent:
            lopts = {f'{pd.to_datetime(l["date"]).strftime("%d %b %Y, %I:%M %p")} — done {l["done"]}': l for l in recent}
            lk    = st.selectbox("Choose entry", list(lopts.keys()), key="ml_sel")
            ml    = lopts[lk]
            day_str = pd.to_datetime(ml["date"]).strftime("%Y-%m-%d")
            sdc = sum(1 for l in logs if pd.to_datetime(l["date"]).strftime("%Y-%m-%d")==day_str)
            if sdc>1: st.caption(f"⚠ {sdc} entries on {day_str} — review for duplicates.")
            lc1,lc2,lc3 = st.columns(3)
            with lc1:
                eld = st.number_input("Done", min_value=0, value=int(ml["done"]),  key=f"eld_{ml['id']}")
                els = st.number_input("Screen (min)", min_value=0, value=int(ml["screen_time"]), key=f"els_{ml['id']}")
                elsl= st.number_input("Sleep (hrs)", 0.0, 24.0, float(ml["sleep"]), 0.5, key=f"elsl_{ml['id']}")
            with lc2:
                elm = st.slider("Mood",   1,5,int(ml["mood"]),  key=f"elm_{ml['id']}")
                ele = st.slider("Energy", 1,5,int(ml["energy"]),key=f"ele_{ml['id']}")
            with lc3:
                elst= st.slider("Stress", 1,5,int(ml["stress"]),key=f"elst_{ml['id']}")
            b1,b2 = st.columns(2)
            with b1:
                if st.button("Save changes →", key=f"slg_{ml['id']}", use_container_width=True):
                    ok,msg = update_log(ml["id"],user_id,eld,elm,ele,els,elst,elsl)
                    if ok: st.success(msg); cached_logs.clear(); cached_status.clear(); st.rerun()
                    else:  st.error(msg)
            with b2:
                dc = st.checkbox("Confirm delete", key=f"dclg_{ml['id']}")
                if st.button("Delete entry", key=f"dlg_{ml['id']}", use_container_width=True):
                    if dc: delete_log(ml["id"],user_id); st.success("Deleted"); cached_logs.clear(); cached_status.clear(); st.rerun()
                    else: st.warning("Tick 'Confirm delete' first")

st.divider()

# ── INSIGHTS ─────────────────────────────────────────────
ins = compute_insight(goal, logs)
pat = compute_patterns(logs)
st.markdown('<div class="slabel"><span>Insights</span></div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="icard"><div class="icard-label">Analysis</div><div class="icard-text">{ins['explanation']}</div></div>
<div class="icard"><div class="icard-label">Recommendation</div><div class="icard-text">{ins['suggestion']}</div></div>
""", unsafe_allow_html=True)
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
    st.markdown(f"""<div style="margin-top:12px;display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
      <span class="pill" style="color:{rc};border-color:{rc}33;background:{rc}11;">{rep['risk']} risk</span>
      <span style="font-family:'JetBrains Mono',monospace;font-size:9px;color:var(--subtle);">Best day: {rep['best_day']}</span>
    </div>""", unsafe_allow_html=True)
    for sg in rep.get("summary",[]):
        st.markdown(f'<div class="aitem" style="margin-top:8px;"><div class="aitem-dot" style="background:var(--accent);"></div><div class="aitem-text">{sg}</div></div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
