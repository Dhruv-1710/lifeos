import streamlit as st
from db   import init_db, get_user, create_user, get_user_by_id
from auth import (hash_password, verify_password, create_token, decode_token,
                  validate_password, check_rate_limit, record_failed_attempt, reset_attempts)

st.set_page_config(page_title="LifeOS — Own Your Day", layout="centered", initial_sidebar_state="collapsed")

try:
    init_db()
except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()

for k in ["token","user_id","username"]:
    if k not in st.session_state: st.session_state[k] = None

if st.session_state.token and not st.session_state.user_id:
    uid = decode_token(st.session_state.token)
    if uid:
        st.session_state.user_id = uid
        if not st.session_state.username:
            u = get_user_by_id(uid)
            if u: st.session_state.username = u["username"]
    else:
        st.session_state.token = None

if st.session_state.user_id:
    st.switch_page("pages/dashboard.py")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&display=swap');
:root {
  --bg:#0A0E1A; --s1:rgba(255,255,255,0.035); --bd:rgba(255,255,255,0.09);
  --bd2:rgba(255,255,255,0.16); --text:#F4F6FA; --muted:#9AA4B8; --subtle:#687089;
  --accent:#2DD9A8; --accent2:#14B8A0; --blue:#3B82F6; --green:#22C55E;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0;}
html,body,[data-testid="stAppViewContainer"],[data-testid="stAppViewContainer"]>.main{
  background:var(--bg)!important;font-family:'Inter',sans-serif!important;color:var(--text)!important;}
[data-testid="stAppViewContainer"]>.main>div,.main .block-container,
.stMainBlockContainer,[data-testid="stMainBlockContainer"],
[data-testid="stAppViewBlockContainer"]{padding:0!important;margin:0!important;max-width:100%!important;}
[data-testid="stAppViewContainer"] .main{padding-top:0!important;}
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stSidebar"],#MainMenu,footer{display:none!important;}
.canvas{min-height:100vh;background:var(--bg);position:relative;overflow:hidden;}
.canvas::before{content:'';position:absolute;inset:-10%;z-index:0;pointer-events:none;
  background:radial-gradient(ellipse 900px 500px at 15% 0%,rgba(45,217,168,0.11) 0%,transparent 60%),
  radial-gradient(ellipse 700px 500px at 100% 30%,rgba(59,130,246,0.09) 0%,transparent 60%);
  animation:bgDrift 18s ease-in-out infinite;}
.nav{position:relative;z-index:10;display:flex;align-items:center;justify-content:space-between;
  max-width:1360px;margin:0 auto;padding:22px 48px 0;}
.nav-logo{font-size:21px;font-weight:800;color:var(--text);letter-spacing:-0.5px;}
.nav-logo span{background:linear-gradient(90deg,var(--accent),var(--blue));
  -webkit-background-clip:text;background-clip:text;color:transparent;}
.nav-status{display:flex;align-items:center;gap:8px;background:var(--s1);
  border:1px solid var(--bd);border-radius:100px;padding:7px 14px;
  font-size:11px;font-weight:500;color:var(--muted);letter-spacing:0.06em;text-transform:uppercase;}
.status-dot{width:6px;height:6px;border-radius:50%;background:var(--accent);
  box-shadow:0 0 10px var(--accent);animation:pulse 2.4s ease-in-out infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.35}}
@keyframes fadeUp{from{opacity:0;transform:translateY(22px);}to{opacity:1;transform:translateY(0);}}
@keyframes floatY{0%,100%{transform:translateY(0);}50%{transform:translateY(-10px);}}
@keyframes barGrow{from{width:0;}}
@keyframes gradShift{0%{background-position:0% 50%;}50%{background-position:100% 50%;}100%{background-position:0% 50%;}}
@keyframes bgDrift{0%,100%{transform:translate(0,0);}50%{transform:translate(-3%,2%);}}
@media(prefers-reduced-motion:reduce){*{animation:none!important;}}
/* staggered entrance for hero column */
.hero-kicker,.hero-h1,.hero-sub,.hero-checks{opacity:0;animation:fadeUp .7s cubic-bezier(.22,.61,.36,1) forwards;}
.hero-h1{animation-delay:.08s;}
.hero-sub{animation-delay:.18s;}
.hero-checks{animation-delay:.28s;}
.hero-check{opacity:0;animation:fadeUp .6s ease forwards;}
.hero-checks .hero-check:nth-child(1){animation-delay:.34s;}
.hero-checks .hero-check:nth-child(2){animation-delay:.42s;}
.hero-checks .hero-check:nth-child(3){animation-delay:.50s;}
.stat-panel{opacity:0;animation:fadeUp .7s ease forwards;animation-delay:.4s;}
.hero-h1 .grad{background-size:220% auto;animation:gradShift 6s ease-in-out infinite;}
.hero-wrap{position:relative;z-index:10;max-width:1360px;margin:0 auto;padding:40px 48px 0;}
.hero-kicker{display:inline-flex;align-items:center;gap:10px;font-size:11px;font-weight:600;
  color:var(--accent);letter-spacing:0.14em;text-transform:uppercase;margin-bottom:22px;}
.hero-kicker::before{content:'';width:7px;height:7px;border-radius:50%;background:var(--accent);box-shadow:0 0 10px var(--accent);}
.hero-h1{font-size:clamp(38px,5.2vw,60px);font-weight:800;line-height:1.05;letter-spacing:-1.5px;color:var(--text);max-width:540px;}
.hero-h1 .grad{background:linear-gradient(90deg,var(--blue),var(--accent));-webkit-background-clip:text;background-clip:text;color:transparent;}
.hero-sub{font-size:15px;font-weight:400;color:var(--muted);line-height:1.65;max-width:480px;margin:18px 0 0;}
.hero-grid{display:grid;grid-template-columns:1.1fr 0.95fr;gap:64px;align-items:center;}
@media(max-width:860px){.hero-grid{grid-template-columns:1fr;}}
.hero-checks{margin-top:22px;display:flex;flex-direction:column;gap:9px;}
.hero-check{display:flex;align-items:center;gap:10px;font-size:13px;color:var(--muted);}
.hero-check::before{content:'✓';color:var(--accent);font-weight:800;font-size:13px;}
.mock{opacity:0;animation:fadeUp .8s ease forwards,floatY 6s ease-in-out 1s infinite;animation-delay:.25s;border:1px solid var(--bd2);border-radius:18px;padding:22px;
  background:linear-gradient(160deg,rgba(255,255,255,0.055),rgba(255,255,255,0.015));
  box-shadow:0 30px 80px rgba(0,0,0,0.5);}
.mock-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;}
.mock-title{font-size:13px;font-weight:700;color:var(--text);}
.mock-pill{font-size:10px;font-weight:700;color:var(--amber, #FBBF24);color:#FBBF24;
  border:1px solid rgba(251,191,36,0.3);background:rgba(251,191,36,0.1);border-radius:100px;padding:3px 10px;}
.mock-big{font-size:42px;font-weight:800;letter-spacing:-1.5px;color:var(--text);}
.mock-big em{font-style:normal;color:var(--accent);font-size:22px;}
.mock-row{display:flex;justify-content:space-between;font-size:11px;color:var(--muted);margin:12px 0 5px;font-weight:500;}
.mock-track{height:6px;border-radius:4px;background:rgba(255,255,255,0.08);}
.mock-fill{height:100%;border-radius:4px;animation:barGrow 1.3s cubic-bezier(.22,.61,.36,1);}
.mock-stats{display:flex;gap:8px;margin-top:16px;flex-wrap:wrap;}
.mock-chip{font-size:10px;color:var(--muted);border:1px solid var(--bd);border-radius:100px;padding:4px 10px;font-weight:600;}
.mock-note{margin-top:14px;font-size:11px;line-height:1.5;color:#F87171;background:rgba(248,113,113,0.08);
  border:1px solid rgba(248,113,113,0.22);border-radius:10px;padding:9px 12px;}
.mock-caption{margin-top:10px;font-size:10px;color:var(--subtle);letter-spacing:0.08em;text-transform:uppercase;text-align:center;}
.stat-panel{margin-top:36px;border:1px solid var(--bd);border-radius:16px;background:var(--s1);
  display:grid;grid-template-columns:repeat(4,1fr);overflow:hidden;}
.stat-cell{padding:22px 20px;border-right:1px solid var(--bd);}
.stat-cell:last-child{border-right:none;}
.stat-val{font-size:26px;font-weight:800;color:var(--text);line-height:1;letter-spacing:-0.5px;margin-bottom:3px;}
.stat-key{font-size:10px;color:var(--muted);letter-spacing:0.08em;text-transform:uppercase;font-weight:500;}
.features-grid{margin-top:16px;display:grid;grid-template-columns:repeat(3,1fr);gap:12px;}
.feat-card{border:1px solid var(--bd);border-radius:14px;background:var(--s1);padding:20px;transition:border-color 0.2s,transform 0.2s;}
.feat-card:hover{border-color:var(--bd2);transform:translateY(-2px);}
.feat-icon{width:34px;height:34px;border-radius:9px;display:flex;align-items:center;justify-content:center;
  background:rgba(45,217,168,0.12);color:var(--accent);margin-bottom:12px;}
.feat-name{font-size:14px;font-weight:700;color:var(--text);margin-bottom:6px;}
.feat-desc{font-size:12px;color:var(--muted);line-height:1.6;}
.auth-panel{margin:40px auto 56px;max-width:1360px;padding:0 48px;}
.auth-card{border:1px solid var(--bd);border-radius:20px;
  background:linear-gradient(135deg,rgba(45,217,168,0.06),rgba(59,130,246,0.05));
  padding:36px;display:grid;grid-template-columns:1fr 1.1fr;gap:32px;}
.auth-left-title{font-size:24px;font-weight:800;color:var(--text);letter-spacing:-0.5px;line-height:1.2;margin-bottom:10px;}
.auth-left-title .grad{background:linear-gradient(90deg,var(--accent),var(--blue));-webkit-background-clip:text;background-clip:text;color:transparent;}
.auth-left-sub{font-size:13px;color:var(--muted);line-height:1.65;max-width:280px;}
.auth-head{text-align:center;margin:0 auto 24px;opacity:0;animation:fadeUp .7s ease forwards;animation-delay:.15s;}
.auth-head .auth-left-title{font-size:26px;}
.auth-head .auth-left-sub{max-width:none;margin:0 auto;}
.auth-form-card{border:1px solid var(--bd);border-radius:20px;padding:30px 30px 34px;
  background:linear-gradient(135deg,rgba(45,217,168,0.06),rgba(59,130,246,0.05));
  box-shadow:0 24px 70px rgba(0,0,0,0.45);opacity:0;animation:fadeUp .7s ease forwards;animation-delay:.28s;}
.auth-hint{text-align:center;font-size:11px;color:var(--subtle);margin-top:16px;font-family:'JetBrains Mono',monospace;letter-spacing:0.02em;}
.pw-rules{font-size:11px;color:var(--subtle);margin-top:6px;line-height:1.7;font-family:'JetBrains Mono',monospace;}
div[data-testid="stTabs"]{border:1px solid var(--bd)!important;border-radius:20px!important;
  padding:28px 30px 32px!important;
  background:linear-gradient(135deg,rgba(45,217,168,0.06),rgba(59,130,246,0.05))!important;
  box-shadow:0 24px 70px rgba(0,0,0,0.42)!important;
  opacity:0;animation:fadeUp .7s ease forwards;animation-delay:.28s;}
button[data-baseweb="tab"]{margin-right:24px!important;}
div[data-baseweb="tab-list"]{justify-content:center!important;gap:10px;margin-bottom:8px;}
button[data-baseweb="tab"]{font-size:13px!important;font-weight:600!important;color:var(--subtle)!important;padding:8px 4px!important;margin-right:22px!important;}
button[data-baseweb="tab"][aria-selected="true"]{color:var(--accent)!important;}
div[data-baseweb="tab-highlight"]{background:var(--accent)!important;height:2px!important;border-radius:2px;}
div[data-baseweb="tab-border"]{background:var(--bd)!important;}
div[data-testid="stTextInput"]>label{font-size:11px!important;font-weight:600!important;color:var(--muted)!important;letter-spacing:0.08em!important;text-transform:uppercase!important;}
div[data-testid="stTextInput"] input{background:rgba(255,255,255,0.04)!important;border:1px solid var(--bd)!important;border-radius:10px!important;color:var(--text)!important;font-family:'Inter',sans-serif!important;font-size:14px!important;padding:11px 14px!important;box-shadow:none!important;transition:border-color 0.2s!important;}
div[data-testid="stTextInput"] input:focus{border-color:var(--accent)!important;box-shadow:0 0 0 3px rgba(45,217,168,0.12)!important;}
div[data-testid="stTextInput"] input::placeholder{color:var(--subtle)!important;}
div[data-testid="stButton"]>button{width:100%!important;background:linear-gradient(90deg,var(--accent2),var(--accent))!important;color:#06231C!important;font-weight:700!important;font-size:14px!important;border:none!important;border-radius:10px!important;padding:12px 0!important;transition:all 0.2s ease!important;box-shadow:0 4px 20px rgba(45,217,168,0.22)!important;}
div[data-testid="stButton"]>button:hover{filter:brightness(1.08);transform:translateY(-1px);}
div[data-testid="stAlert"]{border-radius:10px!important;font-size:13px!important;border:1px solid var(--bd)!important;background:var(--s1)!important;padding:10px 14px!important;margin-top:10px!important;}
.foot{position:relative;z-index:10;max-width:1360px;margin:0 auto;padding:20px 48px 40px;
  display:flex;align-items:center;justify-content:space-between;border-top:1px solid var(--bd);}
.foot-l,.foot-r{font-size:11px;color:var(--subtle);letter-spacing:0.06em;text-transform:uppercase;}
</style>
""", unsafe_allow_html=True)

I = lambda path, size=20: f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">{path}</svg>'
ICONS = {
    "target":  I('<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.2" fill="currentColor"/>'),
    "trend":   I('<polyline points="3,17 9,11 13,15 21,6"/><polyline points="15,6 21,6 21,12"/>'),
    "cal":     I('<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 9h18M8 3v4M16 3v4"/>'),
    "inf":     I('<circle cx="7.5" cy="12" r="4.5"/><circle cx="16.5" cy="12" r="4.5"/>'),
    "layers":  I('<path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 13l9 5 9-5"/>'),
    "brain":   I('<path d="M9 3a3 3 0 0 0-3 3 3 3 0 0 0-2 5 3 3 0 0 0 2 5 3 3 0 0 0 3 3"/><path d="M15 3a3 3 0 0 1 3 3 3 3 0 0 1 2 5 3 3 0 0 1-2 5 3 3 0 0 1-3 3"/>'),
    "bolt":    I('<polygon points="13,2 4,14 11,14 10,22 20,9 13,9 13,2"/>'),
    "heatmap": I('<rect x="3" y="3" width="4" height="4" rx="1"/><rect x="10" y="3" width="4" height="4" rx="1"/><rect x="17" y="3" width="4" height="4" rx="1"/><rect x="3" y="10" width="4" height="4" rx="1"/><rect x="10" y="10" width="4" height="4" rx="1"/><rect x="17" y="10" width="4" height="4" rx="1"/><rect x="3" y="17" width="4" height="4" rx="1"/>'),
    "heart":   I('<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21l7.8-7.8 1-1a5.5 5.5 0 0 0 0-7.6z"/>'),
}

st.markdown(f"""
<div class="canvas">
<div class="nav">
  <div class="nav-logo">Life<span>OS</span></div>
  <div class="nav-status"><span class="status-dot"></span>System Operational</div>
</div>
<div class="hero-wrap">
  <div class="hero-grid">
    <div>
      <div class="hero-kicker">AI Goal Intelligence</div>
      <div class="hero-h1">Own every <span class="grad">single day.</span></div>
      <p class="hero-sub">The only goal engine that predicts setbacks before they happen — and tells you exactly what to do about it.</p>
      <div class="hero-checks">
        <div class="hero-check">Success probability from your real 7-day pattern</div>
        <div class="hero-check">Daily targets that adapt to your energy and sleep</div>
        <div class="hero-check">Wellbeing tracking connected to your output</div>
      </div>
    </div>
    <div>
      <div class="mock">
        <div class="mock-head">
          <span class="mock-title">Solve 150 DSA problems</span>
          <span class="mock-pill">AT RISK</span>
        </div>
        <div class="mock-big">55.3<em>%</em></div>
        <div class="mock-row"><span>Progress</span><span>83 / 150</span></div>
        <div class="mock-track"><div class="mock-fill" style="width:55%;background:linear-gradient(90deg,var(--accent2),var(--accent));"></div></div>
        <div class="mock-row"><span>Success probability</span><span style="color:#FBBF24;">42%</span></div>
        <div class="mock-track"><div class="mock-fill" style="width:42%;background:#FBBF24;"></div></div>
        <div class="mock-stats">
          <span class="mock-chip">🔥 6-day streak</span>
          <span class="mock-chip">avg 1.7/day</span>
          <span class="mock-chip">needs 2.4/day</span>
        </div>
        <div class="mock-note">⚠ 3 missed days this week — consistency is your biggest risk factor. Log 2+ today to recover.</div>
      </div>
      <div class="mock-caption">Live prediction · computed from your own logs</div>
    </div>
  </div>
  <div class="stat-panel">
    <div class="stat-cell"><div class="stat-val">9+</div><div class="stat-key">Signals per prediction</div></div>
    <div class="stat-cell"><div class="stat-val">7d</div><div class="stat-key">Rolling analysis</div></div>
    <div class="stat-cell"><div class="stat-val">ML</div><div class="stat-key">RandomForest engine</div></div>
    <div class="stat-cell"><div class="stat-val">∞</div><div class="stat-key">Goals supported</div></div>
  </div>
  <div class="features-grid">
    <div class="feat-card"><div class="feat-icon">{ICONS['layers']}</div><div class="feat-name">Smart Tracking</div><div class="feat-desc">Log work, mood, energy & screen time — one clear picture of your day.</div></div>
    <div class="feat-card"><div class="feat-icon">{ICONS['brain']}</div><div class="feat-name">AI Prediction</div><div class="feat-desc">Trained ML model scores your success probability in real time.</div></div>
    <div class="feat-card"><div class="feat-icon">{ICONS['cal']}</div><div class="feat-name">Planning Engine</div><div class="feat-desc">Daily targets that adapt to your pace, deadline, and momentum.</div></div>
    <div class="feat-card"><div class="feat-icon">{ICONS['bolt']}</div><div class="feat-name">Streak System</div><div class="feat-desc">Consistency compounds — track your streak and protect it.</div></div>
    <div class="feat-card"><div class="feat-icon">{ICONS['heatmap']}</div><div class="feat-name">Calendar Heatmap</div><div class="feat-desc">See your activity at a glance, GitHub-contributions style.</div></div>
    <div class="feat-card"><div class="feat-icon">{ICONS['heart']}</div><div class="feat-name">Wellbeing Score</div><div class="feat-desc">Sleep, stress, energy — connected to your output.</div></div>
  </div>
</div>
<div class="auth-panel">
  <div class="auth-head">
    <div class="auth-left-title">Start <span class="grad">tracking today.</span></div>
    <p class="auth-left-sub">Free · No credit card · Your data stays yours · Works on any device</p>
  </div>
</div>
""", unsafe_allow_html=True)

# Centered, narrow auth card (widgets live in the middle column)
_al, _ac, _ar = st.columns([1, 1.5, 1])
with _ac:
    tab1, tab2 = st.tabs(["Sign in", "Register"])

with tab1:
    u = st.text_input("Username", key="lu", placeholder="your_username")
    p = st.text_input("Password", type="password", key="lp", placeholder="••••••••")
    if st.button("Sign in →", key="lbtn"):
        if not u or not p:
            st.error("Please fill all fields")
        else:
            allowed, msg = check_rate_limit(u.strip())
            if not allowed:
                st.error(msg)
            else:
                user = get_user(u.strip())
                if user and verify_password(p, user["password"]):
                    reset_attempts(u.strip())
                    st.session_state.token    = create_token(user["id"])
                    st.session_state.user_id  = user["id"]
                    st.session_state.username = u.strip()
                    st.rerun()
                else:
                    record_failed_attempt(u.strip())
                    st.error("Invalid credentials")

with tab2:
    u2 = st.text_input("Username", key="ru", placeholder="choose_username")
    p2 = st.text_input("Password", type="password", key="rp", placeholder="Min 8 chars, 1 uppercase, 1 number")
    p3 = st.text_input("Confirm password", type="password", key="rp2", placeholder="Re-enter password")
    if st.button("Create account →", key="rbtn"):
        if len(u2.strip()) < 3:
            st.error("Username must be at least 3 characters")
        elif p2 != p3:
            st.error("Passwords don't match")
        else:
            valid, pw_msg = validate_password(p2)
            if not valid:
                st.error(pw_msg)
            else:
                ok, msg = create_user(u2.strip(), hash_password(p2))
                if ok:
                    # signed in immediately — no second login step
                    user = get_user(u2.strip())
                    st.session_state.token    = create_token(user["id"])
                    st.session_state.user_id  = user["id"]
                    st.session_state.username = u2.strip()
                    st.rerun()
                else:
                    st.error(msg)

st.markdown("""
<div class="auth-hint">🔒 Passwords are hashed with bcrypt · min 8 chars, 1 uppercase, 1 number</div>
<div class="foot">
  <span class="foot-l">LifeOS © 2026</span>
  <span class="foot-r">Built with AI · v2.2</span>
</div>
</div>
""", unsafe_allow_html=True)
