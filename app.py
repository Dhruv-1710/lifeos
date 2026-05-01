import streamlit as st
from db   import init_db, get_user, create_user
from auth import hash_password, verify_password, create_token, decode_token

st.set_page_config(
    page_title="LifeOS — Own Your Day",
    layout="centered",
    initial_sidebar_state="collapsed"
)

try:
    init_db()
except Exception as e:
    st.error(f"Database error: {e}")
    st.stop()

for k in ["token","user_id","username"]:
    if k not in st.session_state: st.session_state[k] = None

if st.session_state.token and not st.session_state.user_id:
    uid = decode_token(st.session_state.token)
    if uid: st.session_state.user_id = uid
    else:   st.session_state.token   = None

if st.session_state.user_id:
    st.switch_page("pages/dashboard.py")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,700;0,900;1,400;1,700&family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400;500&display=swap');

:root {
  --bg:       #09090b;
  --surface:  #111114;
  --border:   #1e1e24;
  --border2:  #2a2a35;
  --text:     #fafafa;
  --muted:    #71717a;
  --subtle:   #3f3f46;
  --accent:   #e8d5b0;
  --accent2:  #c4a882;
  --green:    #4ade80;
  --red:      #f87171;
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
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stSidebar"],#MainMenu,footer { display: none !important; }

/* ── CANVAS ── */
.canvas {
  min-height: 100vh;
  background: var(--bg);
  position: relative;
  overflow: hidden;
}

/* grain overlay */
.canvas::before {
  content: '';
  position: fixed; inset: 0; z-index: 1;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='300' height='300'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='300' height='300' filter='url(%23n)' opacity='0.035'/%3E%3C/svg%3E");
  background-repeat: repeat;
  background-size: 200px;
  pointer-events: none;
}

/* warm glow top */
.canvas::after {
  content: '';
  position: fixed;
  top: -300px; left: 50%; transform: translateX(-50%);
  width: 800px; height: 600px;
  background: radial-gradient(ellipse at center, rgba(232,213,176,0.04) 0%, transparent 65%);
  pointer-events: none; z-index: 0;
}

/* ── NAV ── */
.nav {
  position: relative; z-index: 10;
  display: flex; align-items: center; justify-content: space-between;
  max-width: 960px; margin: 0 auto;
  padding: 36px 48px 0;
}
.nav-logo {
  font-family: 'Playfair Display', serif;
  font-size: 20px; font-weight: 700;
  color: var(--text);
  letter-spacing: -0.5px;
}
.nav-logo em { color: var(--accent); font-style: italic; }
.nav-status {
  display: flex; align-items: center; gap: 7px;
  font-family: 'DM Mono', monospace;
  font-size: 10px; color: var(--subtle);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
.status-dot {
  width: 5px; height: 5px; border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 8px var(--green);
  animation: pulse 3s ease-in-out infinite;
}
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* ── HERO ── */
.hero {
  position: relative; z-index: 10;
  max-width: 880px; margin: 0 auto;
  padding: 96px 48px 72px;
}
.hero-kicker {
  font-family: 'DM Mono', monospace;
  font-size: 10px; font-weight: 500;
  color: var(--accent);
  letter-spacing: 0.2em; text-transform: uppercase;
  margin-bottom: 28px;
  display: flex; align-items: center; gap: 12px;
}
.hero-kicker::before {
  content: '';
  width: 32px; height: 1px;
  background: var(--accent);
  display: inline-block;
}

.hero-h1 {
  font-family: 'Playfair Display', serif;
  font-size: clamp(52px, 7.5vw, 96px);
  font-weight: 900;
  line-height: 0.95;
  letter-spacing: -3px;
  color: var(--text);
  margin-bottom: 0;
}
.hero-h1 em {
  font-style: italic;
  color: var(--accent);
}
.hero-h1 .ghost {
  color: transparent;
  -webkit-text-stroke: 1px var(--border2);
}

.hero-sub {
  font-size: 16px;
  font-weight: 300;
  color: var(--muted);
  line-height: 1.75;
  max-width: 440px;
  margin: 36px 0 0;
}
.hero-sub strong { color: #a1a1aa; font-weight: 400; }

/* ── HORIZONTAL RULE ── */
.rule {
  position: relative; z-index: 10;
  max-width: 960px; margin: 0 auto;
  padding: 0 48px;
  border-top: 1px solid var(--border);
}

/* ── STATS ── */
.stats {
  position: relative; z-index: 10;
  max-width: 960px; margin: 0 auto;
  padding: 0 48px;
  display: grid; grid-template-columns: repeat(4, 1fr);
  border-left: 1px solid var(--border);
}
.stat {
  padding: 32px 24px;
  border-right: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}
.stat-val {
  font-family: 'Playfair Display', serif;
  font-size: 36px; font-weight: 700;
  color: var(--text); line-height: 1;
  margin-bottom: 6px;
}
.stat-val em { font-style: italic; color: var(--accent); }
.stat-key {
  font-family: 'DM Mono', monospace;
  font-size: 9px; color: var(--subtle);
  letter-spacing: 0.15em; text-transform: uppercase;
}

/* ── FEATURES ── */
.features {
  position: relative; z-index: 10;
  max-width: 960px; margin: 0 auto;
  padding: 0 48px;
  display: grid; grid-template-columns: repeat(3,1fr);
  border-left: 1px solid var(--border);
}
.feat {
  padding: 32px 24px;
  border-right: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  transition: background 0.2s;
}
.feat:hover { background: rgba(232,213,176,0.02); }
.feat-num {
  font-family: 'DM Mono', monospace;
  font-size: 9px; color: var(--subtle);
  letter-spacing: 0.15em; margin-bottom: 20px;
}
.feat-name {
  font-family: 'Playfair Display', serif;
  font-size: 18px; font-weight: 700;
  color: var(--text); margin-bottom: 10px;
  letter-spacing: -0.3px;
}
.feat-desc {
  font-size: 13px; color: var(--muted);
  line-height: 1.65; font-weight: 300;
}

/* ── AUTH SECTION ── */
.auth-outer {
  position: relative; z-index: 10;
  max-width: 960px; margin: 0 auto;
  padding: 0 48px;
  border-left: 1px solid var(--border);
  display: grid; grid-template-columns: 1fr 1fr;
}
.auth-left {
  padding: 48px 32px 48px 24px;
  border-right: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}
.auth-left-title {
  font-family: 'Playfair Display', serif;
  font-size: 28px; font-weight: 700;
  color: var(--text); margin-bottom: 8px;
  letter-spacing: -0.5px; line-height: 1.2;
}
.auth-left-title em { font-style: italic; color: var(--accent); }
.auth-left-sub {
  font-size: 13px; color: var(--muted); line-height: 1.65;
  font-weight: 300; max-width: 260px;
}
.auth-right {
  padding: 48px 24px 48px 32px;
  border-bottom: 1px solid var(--border);
}

/* tabs */
div[data-testid="stTabs"] {
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
}
button[data-baseweb="tab"] {
  font-family: 'DM Mono', monospace !important;
  font-size: 10px !important; font-weight: 500 !important;
  color: var(--subtle) !important;
  letter-spacing: 0.12em !important;
  text-transform: uppercase !important;
  padding: 8px 0 !important;
  margin-right: 24px !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
  color: var(--accent) !important;
}
div[data-baseweb="tab-highlight"] {
  background: var(--accent) !important;
  height: 1px !important;
}
div[data-baseweb="tab-border"] { background: var(--border) !important; }

/* inputs */
div[data-testid="stTextInput"] > label {
  font-family: 'DM Mono', monospace !important;
  font-size: 9px !important; font-weight: 500 !important;
  color: var(--subtle) !important;
  letter-spacing: 0.15em !important;
  text-transform: uppercase !important;
}
div[data-testid="stTextInput"] input {
  background: transparent !important;
  border: none !important;
  border-bottom: 1px solid var(--border2) !important;
  border-radius: 0 !important;
  color: var(--text) !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 14px !important;
  font-weight: 300 !important;
  padding: 10px 0 !important;
  box-shadow: none !important;
  transition: border-color 0.2s !important;
}
div[data-testid="stTextInput"] input:focus {
  border-bottom-color: var(--accent) !important;
  box-shadow: none !important;
}
div[data-testid="stTextInput"] input::placeholder {
  color: var(--subtle) !important;
  font-weight: 300 !important;
}

/* button */
div[data-testid="stButton"] > button {
  width: 100% !important;
  background: var(--accent) !important;
  color: #09090b !important;
  font-family: 'DM Mono', monospace !important;
  font-weight: 500 !important; font-size: 11px !important;
  border: none !important; border-radius: 0 !important;
  padding: 14px 0 !important;
  letter-spacing: 0.15em !important;
  text-transform: uppercase !important;
  transition: all 0.2s ease !important;
  box-shadow: none !important;
}
div[data-testid="stButton"] > button:hover {
  background: var(--text) !important;
  transform: none !important;
}

/* alerts */
div[data-testid="stAlert"] {
  border-radius: 0 !important;
  font-family: 'DM Sans', sans-serif !important;
  font-size: 13px !important;
  font-weight: 300 !important;
  border-left: 2px solid !important;
  background: transparent !important;
  padding: 10px 14px !important;
  margin-top: 8px !important;
}

/* ── FOOTER ── */
.foot {
  position: relative; z-index: 10;
  max-width: 960px; margin: 0 auto;
  padding: 24px 48px;
  display: flex; align-items: center; justify-content: space-between;
  border-left: 1px solid var(--border);
  border-right: 1px solid var(--border);
}
.foot-l {
  font-family: 'DM Mono', monospace;
  font-size: 9px; color: var(--subtle);
  letter-spacing: 0.12em; text-transform: uppercase;
}
.foot-r {
  font-family: 'DM Mono', monospace;
  font-size: 9px; color: var(--border2);
  letter-spacing: 0.1em; text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)

# ── MARKUP ───────────────────────────────────────────────
st.markdown("""
<div class="canvas">

<div class="nav">
  <div class="nav-logo">Life<em>OS</em></div>
  <div class="nav-status"><span class="status-dot"></span>All systems operational</div>
</div>

<div class="hero">
  <div class="hero-kicker">AI Goal Intelligence</div>
  <div class="hero-h1">
    Own<br>
    every<br>
    <em>single</em><br>
    <span class="ghost">day.</span>
  </div>
  <p class="hero-sub">
    The only goal engine that predicts failure <strong>before it happens</strong> —
    and tells you exactly what to do about it.
  </p>
</div>

<div class="rule"></div>

<div class="stats">
  <div class="stat">
    <div class="stat-val">94<em>%</em></div>
    <div class="stat-key">ML Accuracy</div>
  </div>
  <div class="stat">
    <div class="stat-val">3<em>×</em></div>
    <div class="stat-key">Consistency Gain</div>
  </div>
  <div class="stat">
    <div class="stat-val">21<em>d</em></div>
    <div class="stat-key">Avg Habit Lock-in</div>
  </div>
  <div class="stat">
    <div class="stat-val"><em>∞</em></div>
    <div class="stat-key">Goals Supported</div>
  </div>
</div>

<div class="features">
  <div class="feat">
    <div class="feat-num">01</div>
    <div class="feat-name">Smart Tracking</div>
    <div class="feat-desc">Log work, mood, energy & screen time. Your data, complete picture.</div>
  </div>
  <div class="feat">
    <div class="feat-num">02</div>
    <div class="feat-name">AI Prediction</div>
    <div class="feat-desc">ML model scores your success probability in real-time. No surprises.</div>
  </div>
  <div class="feat">
    <div class="feat-num">03</div>
    <div class="feat-name">Planning Engine</div>
    <div class="feat-desc">Daily targets auto-calculated from your pace, deadline and momentum.</div>
  </div>
  <div class="feat">
    <div class="feat-num">04</div>
    <div class="feat-name">Streak System</div>
    <div class="feat-desc">Consistency compounds. Track your streak, protect it with your life.</div>
  </div>
  <div class="feat">
    <div class="feat-num">05</div>
    <div class="feat-name">Focus Timer</div>
    <div class="feat-desc">Pomodoro built in. No apps. No context switching. Just work.</div>
  </div>
  <div class="feat">
    <div class="feat-num">06</div>
    <div class="feat-name">Wellbeing Score</div>
    <div class="feat-desc">Sleep, stress, energy — all connected to your output. See the link.</div>
  </div>
</div>

<div class="auth-outer">
  <div class="auth-left">
    <div class="auth-left-title">Start<br>tracking<br><em>today.</em></div>
    <p class="auth-left-sub" style="margin-top:16px;">
      Free. No credit card. Your data stays yours. Works on any device.
    </p>
  </div>
  <div class="auth-right">
""", unsafe_allow_html=True)

# ── AUTH ─────────────────────────────────────────────────
tab1, tab2 = st.tabs(["Sign in", "Register"])

with tab1:
    u = st.text_input("Username", key="lu", placeholder="your_username")
    p = st.text_input("Password", type="password", key="lp", placeholder="••••••••")
    if st.button("Sign in →", key="lbtn"):
        if not u or not p:
            st.error("Please fill all fields")
        else:
            user = get_user(u.strip())
            if user and verify_password(p, user["password"]):
                st.session_state.token    = create_token(user["id"])
                st.session_state.user_id  = user["id"]
                st.session_state.username = u.strip()
                st.rerun()
            else:
                st.error("Invalid credentials")

with tab2:
    u2 = st.text_input("Username", key="ru", placeholder="choose_username")
    p2 = st.text_input("Password", type="password", key="rp", placeholder="min 6 chars")
    if st.button("Create account →", key="rbtn"):
        if len(u2.strip()) < 3:
            st.error("Username must be at least 3 characters")
        elif len(p2) < 6:
            st.error("Password must be at least 6 characters")
        else:
            ok, msg = create_user(u2.strip(), hash_password(p2))
            if ok: st.success("Account created — sign in now")
            else:  st.error(msg)

st.markdown("""
  </div>
</div>

<div class="foot">
  <span class="foot-l">LifeOS © 2025</span>
  <span class="foot-r">Built with AI · v1.0 Beta</span>
</div>

</div>
""", unsafe_allow_html=True)
