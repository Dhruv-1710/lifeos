import streamlit as st
import pandas as pd
from datetime import date, timedelta
from db   import get_goals, create_goal, update_goal, delete_goal, get_user, get_user_by_id, create_user, update_username
from auth import decode_token, hash_password, verify_password, validate_password

st.set_page_config(page_title="LifeOS · Profile & Goals", layout="wide", initial_sidebar_state="expanded")

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
.topbar-right{display:flex;align-items:center;gap:16px;}
.topbar-name{font-size:13px;font-weight:600;color:var(--muted);}
.topbar-dot{width:8px;height:8px;border-radius:50%;background:var(--accent);box-shadow:0 0 10px var(--accent);}
.page-header{padding:32px 32px 0;position:relative;z-index:10;}
.page-title{font-size:28px;font-weight:800;color:var(--text);letter-spacing:-0.5px;margin-bottom:4px;}
.page-sub{font-size:14px;color:var(--muted);}
.content{padding:24px 32px 56px;position:relative;z-index:10;}
.slabel{font-size:11px;color:var(--subtle);letter-spacing:0.08em;text-transform:uppercase;font-weight:600;
  padding-bottom:12px;border-bottom:1px solid var(--bd);margin-bottom:18px;
  display:flex;align-items:center;justify-content:space-between;}
.icard{border:1px solid var(--bd);border-radius:14px;padding:20px;margin-bottom:12px;background:var(--s1);}
.icard-label{font-size:11px;color:var(--accent);letter-spacing:0.06em;text-transform:uppercase;font-weight:600;margin-bottom:10px;}
.icard-text{font-size:13px;color:var(--muted);font-weight:400;line-height:1.65;}
.goal-row{background:var(--s1);border:1px solid var(--bd);border-radius:14px;padding:18px 20px;
  margin-bottom:10px;display:flex;align-items:center;gap:16px;transition:border-color 0.2s;}
.goal-row:hover{border-color:var(--bd2);}
.goal-row-name{font-size:15px;font-weight:700;color:var(--text);flex:1;}
.goal-row-meta{font-size:11px;color:var(--subtle);font-weight:500;margin-top:3px;}
.pill{display:inline-flex;align-items:center;padding:3px 9px;border-radius:100px;font-size:11px;font-weight:600;border:1px solid;}
.pill-g{color:var(--green);border-color:rgba(34,197,94,0.25);background:rgba(34,197,94,0.10);}
.pill-r{color:var(--red);border-color:rgba(248,113,113,0.25);background:rgba(248,113,113,0.10);}
.pill-a{color:var(--amber);border-color:rgba(251,191,36,0.25);background:rgba(251,191,36,0.10);}
.pill-i{color:var(--indigo);border-color:rgba(129,140,248,0.25);background:rgba(129,140,248,0.10);}
.pill-ac{color:var(--accent);border-color:rgba(45,217,168,0.25);background:rgba(45,217,168,0.10);}
.danger-zone{border:1px solid rgba(248,113,113,0.25);border-radius:14px;padding:20px;background:rgba(248,113,113,0.04);}
.danger-title{font-size:13px;font-weight:700;color:var(--red);margin-bottom:6px;letter-spacing:0.02em;}
.danger-sub{font-size:12px;color:var(--muted);margin-bottom:16px;line-height:1.55;}
div[data-testid="stTextInput"]>label,div[data-testid="stTextArea"]>label,
div[data-testid="stNumberInput"]>label,div[data-testid="stDateInput"]>label,
div[data-testid="stSelectbox"]>label,div[data-testid="stMultiSelect"]>label{
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
div[data-testid="stAlert"]{border-radius:10px!important;font-size:13px!important;background:var(--s1)!important;border:1px solid var(--bd)!important;padding:10px 14px!important;}
hr{border-color:var(--bd)!important;margin:22px 0!important;}
div[data-testid="stExpander"]{background:var(--s1)!important;border:1px solid var(--bd)!important;border-radius:14px!important;}
div[data-testid="stExpander"] summary{font-size:12px!important;font-weight:600!important;color:var(--muted)!important;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ── TOP BAR ──────────────────────────────────────────────
st.markdown(f"""
<div class="topbar">
  <div class="topbar-logo">Life<em>OS</em></div>
  <div class="topbar-right">
    <span class="topbar-name">{username}</span>
    <span class="topbar-dot"></span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR ──────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sb-logo">Life<em>OS</em></div>', unsafe_allow_html=True)
    st.markdown('<div class="sb-section">Navigation</div>', unsafe_allow_html=True)
    if st.button("📊  Dashboard", use_container_width=True, key="goto_dash"):
        st.switch_page("pages/dashboard.py")
    st.divider()
    if st.button("Sign out", use_container_width=True, key="signout"):
        for k in ["token","user_id","username"]: st.session_state[k] = None
        st.switch_page("app.py")

# ── PAGE HEADER ──────────────────────────────────────────
st.markdown("""
<div class="page-header">
  <div class="page-title">Profile &amp; Goals</div>
  <div class="page-sub">Manage your goals, track changes, and keep your account secure.</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="content">', unsafe_allow_html=True)

# ── TABS ─────────────────────────────────────────────────
tab_goals, tab_new, tab_account = st.tabs(["My Goals", "New Goal", "Account"])

# ════════════════════════════════════════════════════════
# TAB 1 — MY GOALS (edit / status / delete)
# ════════════════════════════════════════════════════════
with tab_goals:
    show_arch = st.toggle("Show archived goals", value=False, key="show_arch")
    goals     = get_goals(user_id, include_archived=show_arch)

    if not goals:
        st.markdown('<div class="icard"><div class="icard-text">No goals yet. Go to the <b>New Goal</b> tab to create one.</div></div>', unsafe_allow_html=True)
    else:
        STATUS_COLORS = {"Active":"pill-ac","Paused":"pill-i","Completed":"pill-g","Archived":"pill-r"}
        for g in goals:
            sc = STATUS_COLORS.get(g.get("status","Active"),"pill-ac")
            days_left = (pd.to_datetime(g["deadline"]).date()-date.today()).days
            dl_txt    = f"{days_left}d left" if days_left>=0 else f"{abs(days_left)}d overdue"
            st.markdown(f"""
            <div class="goal-row">
              <div>
                <div class="goal-row-name">{g['name']}</div>
                <div class="goal-row-meta">{g['category']} · Target {g['target']} · {dl_txt}</div>
              </div>
              <span class="{sc} pill">{g.get('status','Active')}</span>
            </div>""", unsafe_allow_html=True)

            with st.expander(f"Edit — {g['name']}"):
                e1, e2 = st.columns(2)
                with e1:
                    e_name = st.text_input("Goal name", value=g["name"], key=f"en_{g['id']}")
                    e_tgt  = st.number_input("Target units", min_value=1, value=int(g["target"]), key=f"et_{g['id']}")
                    e_dl   = st.date_input("Deadline", value=pd.to_datetime(g["deadline"]).date(), key=f"ed_{g['id']}")
                with e2:
                    e_cat  = st.selectbox("Category", GOAL_CATEGORIES,
                                          index=GOAL_CATEGORIES.index(g["category"]) if g["category"] in GOAL_CATEGORIES else 0,
                                          key=f"ec_{g['id']}")
                    e_stat = st.selectbox("Status", GOAL_STATUSES,
                                          index=GOAL_STATUSES.index(g["status"]) if g["status"] in GOAL_STATUSES else 0,
                                          key=f"es_{g['id']}")
                    e_notes= st.text_area("Notes", value=g.get("notes",""), key=f"eno_{g['id']}", height=80)

                sb1, sb2 = st.columns(2)
                with sb1:
                    if st.button("Save changes →", key=f"sv_{g['id']}", use_container_width=True):
                        if not e_name.strip():
                            st.warning("Goal name can't be empty")
                        else:
                            ok, msg = update_goal(g["id"], user_id, e_name, e_tgt, e_dl, e_cat, e_notes, e_stat)
                            if ok: st.success(msg); st.rerun()
                            else:  st.error(msg)
                with sb2:
                    conf = st.checkbox("Confirm delete", key=f"cd_{g['id']}")
                    if st.button("Delete goal", key=f"dg_{g['id']}", use_container_width=True):
                        if conf:
                            delete_goal(g["id"], user_id)
                            st.success("Goal deleted"); st.rerun()
                        else:
                            st.warning("Tick 'Confirm delete' first")

# ════════════════════════════════════════════════════════
# TAB 2 — NEW GOAL
# ════════════════════════════════════════════════════════
with tab_new:
    # Quick-start template
    st.markdown('<div class="slabel"><span>Quick Start from a Template</span></div>', unsafe_allow_html=True)
    tchoice = st.selectbox("Template", ["— custom goal —"] + list(GOAL_TEMPLATES.keys()), key="tmpl")
    if st.button("Pre-fill from template →", key="tmpl_btn"):
        if tchoice != "— custom goal —":
            t = GOAL_TEMPLATES[tchoice]
            st.session_state["ng_name"]     = tchoice
            st.session_state["ng_target"]   = t["target"]
            st.session_state["ng_start"]    = 0
            st.session_state["ng_deadline"] = date.today()+timedelta(days=t["days"])
            st.session_state["ng_category"] = t["category"]
            st.session_state["ng_notes"]    = t["notes"]
            st.rerun()

    st.divider()
    st.markdown('<div class="slabel"><span>Goal Details</span></div>', unsafe_allow_html=True)

    _cat = st.session_state.get("ng_category","General")
    f1, f2 = st.columns(2)
    with f1:
        g_name     = st.text_input("Goal name *", placeholder=GOAL_NAME_EXAMPLES.get(_cat,""), key="ng_name")
        g_target   = st.number_input("Target units *", min_value=1, value=st.session_state.get("ng_target",100), key="ng_target")
        g_start    = st.number_input("Already done (optional)", min_value=0, value=0, key="ng_start",
                                      help="If migrating a goal already in progress.")
    with f2:
        g_deadline = st.date_input("Deadline *", value=st.session_state.get("ng_deadline", date.today()+timedelta(days=90)), key="ng_deadline")
        g_category = st.selectbox("Category", GOAL_CATEGORIES, key="ng_category")
        g_notes    = st.text_area("Notes (optional)", placeholder="Why this goal matters…", key="ng_notes", height=100)

    if st.button("Create Goal →", key="create_goal_btn", use_container_width=True):
        if not g_name.strip():
            st.error("Goal name is required")
        elif g_start >= g_target:
            st.error("Already-done amount must be less than the target")
        else:
            ok, msg = create_goal(user_id, g_name, g_target, g_deadline,
                                   category=g_category, notes=g_notes, starting_point=g_start)
            if ok:
                for k in ["ng_name","ng_target","ng_start","ng_deadline","ng_category","ng_notes","tmpl"]:
                    st.session_state.pop(k, None)
                st.success(f"✅ {msg}")
                st.rerun()
            else:
                st.error(msg)

# ════════════════════════════════════════════════════════
# TAB 3 — ACCOUNT
# ════════════════════════════════════════════════════════
with tab_account:
    st.markdown('<div class="slabel"><span>Account Info</span></div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="icard">
      <div class="icard-label">Signed in as</div>
      <div class="icard-text" style="font-size:20px;font-weight:800;color:var(--text);">{username}</div>
    </div>""", unsafe_allow_html=True)

    st.divider()

    # ── CHANGE USERNAME ──────────────────────────────────
    st.markdown('<div class="slabel"><span>Change Username</span></div>', unsafe_allow_html=True)
    with st.expander("Update your username"):
        nu = st.text_input("New username", value=username, key="nu_name")
        if st.button("Change username →", key="nu_btn", use_container_width=True):
            if nu.strip() == username:
                st.info("That is already your username")
            else:
                ok, msg = update_username(user_id, nu)
                if ok:
                    st.session_state.username = nu.strip()
                    st.success(msg); st.rerun()
                else:
                    st.error(msg)

    st.divider()

    # ── CHANGE PASSWORD ──────────────────────────────────
    st.markdown('<div class="slabel"><span>Change Password</span></div>', unsafe_allow_html=True)
    with st.expander("Update your password"):
        cp1 = st.text_input("Current password", type="password", key="cp_cur")
        cp2 = st.text_input("New password", type="password", key="cp_new",
                             placeholder="Min 8 chars, 1 uppercase, 1 number")
        cp3 = st.text_input("Confirm new password", type="password", key="cp_con")
        if st.button("Change password →", key="cp_btn", use_container_width=True):
            if not cp1 or not cp2 or not cp3:
                st.error("Fill all fields")
            elif cp2 != cp3:
                st.error("New passwords don't match")
            else:
                valid, pw_msg = validate_password(cp2)
                if not valid:
                    st.error(pw_msg)
                else:
                    user = get_user_by_id(user_id)
                    if not user or not verify_password(cp1, user["password"]):
                        st.error("Current password is incorrect")
                    else:
                        from db import get_cursor
                        with get_cursor(commit=True) as cur:
                            cur.execute(
                                "UPDATE users SET password=%s WHERE id=%s",
                                (hash_password(cp2), user_id)
                            )
                        st.success("Password updated successfully")

    st.divider()

    # ── DANGER ZONE ──────────────────────────────────────
    st.markdown('<div class="slabel"><span>Danger Zone</span></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="danger-zone">
      <div class="danger-title">Delete Account</div>
      <div class="danger-sub">This will permanently delete your account and all associated goals and logs. This action cannot be undone.</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    with st.expander("⚠ Delete my account"):
        da_pw   = st.text_input("Enter your password to confirm", type="password", key="da_pw")
        da_conf = st.checkbox("I understand this is permanent and irreversible", key="da_conf")
        if st.button("Delete account permanently", key="da_btn", use_container_width=True):
            if not da_pw or not da_conf:
                st.error("Enter password and check the confirmation box")
            else:
                user = get_user_by_id(user_id)
                if not user or not verify_password(da_pw, user["password"]):
                    st.error("Incorrect password")
                else:
                    from db import get_cursor
                    with get_cursor(commit=True) as cur:
                        cur.execute("DELETE FROM users WHERE id=%s", (user_id,))
                    for k in ["token","user_id","username"]: st.session_state[k] = None
                    st.switch_page("app.py")

st.markdown('</div>', unsafe_allow_html=True)
