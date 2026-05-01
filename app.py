import streamlit as st
from db   import init_db, get_user, create_user
from auth import hash_password, verify_password, create_token, decode_token

st.set_page_config(page_title="LifeOS · AI Goal Engine", layout="centered", initial_sidebar_state="collapsed")

try:
    init_db()
except Exception as e:
    st.error(f"❌ Database error: {e}")
    st.stop()

if "token"    not in st.session_state: st.session_state.token    = None
if "user_id"  not in st.session_state: st.session_state.user_id  = None
if "username" not in st.session_state: st.session_state.username = None

if st.session_state.token and not st.session_state.user_id:
    uid = decode_token(st.session_state.token)
    if uid: st.session_state.user_id = uid
    else:   st.session_state.token   = None

if st.session_state.user_id:
    st.switch_page("pages/dashboard.py")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Cal+Sans&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main {
    background: #0c0c0f !important;
    font-family: 'Inter', sans-serif !important;
    color: #e4e4e7 !important;
}

.main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],
[data-testid="stSidebar"],#MainMenu,footer { display:none !important; }

/* ─ PAGE SHELL ─ */
.page {
    min-height: 100vh;
    background: #0c0c0f;
    position: relative;
    overflow-x: hidden;
}

/* ─ NOISE TEXTURE ─ */
.page::before {
    content: '';
    position: fixed; inset: 0; z-index: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E");
    background-size: 200px 200px;
    pointer-events: none;
    opacity: 0.5;
}

/* ─ GLOW BLOBS ─ */
.blob {
    position: fixed; border-radius: 50%;
    filter: blur(100px); pointer-events: none; z-index: 0;
}
.blob-1 { width:600px;height:500px;top:-200px;left:-200px;
    background:radial-gradient(circle, rgba(99,102,241,0.12) 0%, transparent 70%); }
.blob-2 { width:500px;height:500px;bottom:-100px;right:-150px;
    background:radial-gradient(circle, rgba(16,185,129,0.08) 0%, transparent 70%); }
.blob-3 { width:300px;height:300px;top:40%;left:40%;
    background:radial-gradient(circle, rgba(245,158,11,0.05) 0%, transparent 70%); }

/* ─ NAV ─ */
.nav {
    position: relative; z-index: 10;
    display: flex; align-items: center; justify-content: space-between;
    max-width: 1000px; margin: 0 auto;
    padding: 28px 40px 0;
}
.logo {
    font-family: 'Inter', sans-serif;
    font-size: 16px; font-weight: 700;
    color: #fafafa; letter-spacing: -0.3px;
    display: flex; align-items: center; gap: 8px;
}
.logo-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: linear-gradient(135deg, #6366f1, #10b981);
    display: inline-block;
}
.nav-badge {
    font-size: 11px; font-weight: 500;
    color: #71717a; padding: 4px 10px;
    border: 1px solid #27272a;
    border-radius: 20px; letter-spacing: 0.05em;
}

/* ─ HERO ─ */
.hero {
    position: relative; z-index: 10;
    max-width: 720px; margin: 0 auto;
    padding: 80px 40px 60px;
    text-align: center;
}
.hero-eyebrow {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 11px; font-weight: 600; letter-spacing: 0.12em;
    text-transform: uppercase; color: #6366f1;
    margin-bottom: 24px;
    padding: 5px 12px;
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 20px;
    background: rgba(99,102,241,0.06);
}
.live-dot {
    width: 5px; height: 5px; border-radius: 50%;
    background: #10b981;
    box-shadow: 0 0 6px #10b981;
    animation: blink 2s infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.2} }

.hero-title {
    font-family: 'Inter', sans-serif;
    font-size: clamp(40px, 6vw, 72px);
    font-weight: 700;
    line-height: 1.05;
    letter-spacing: -2.5px;
    color: #fafafa;
    margin-bottom: 4px;
}
.hero-title-em {
    font-family: 'Instrument Serif', serif;
    font-style: italic;
    font-size: clamp(44px, 6.5vw, 78px);
    background: linear-gradient(135deg, #6366f1 0%, #a78bfa 40%, #10b981 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -1px;
    display: block;
    margin-bottom: 28px;
}
.hero-sub {
    font-size: 16px; font-weight: 400;
    color: #71717a; line-height: 1.7;
    max-width: 480px; margin: 0 auto 48px;
}
.hero-sub b { color: #a1a1aa; font-weight: 500; }

/* ─ METRICS STRIP ─ */
.metrics {
    position: relative; z-index: 10;
    display: flex; justify-content: center;
    gap: 0; max-width: 540px; margin: 0 auto 64px;
    border: 1px solid #1c1c1f; border-radius: 16px;
    overflow: hidden; background: #111113;
}
.metric {
    flex: 1; padding: 20px 12px; text-align: center;
    border-right: 1px solid #1c1c1f;
}
.metric:last-child { border-right: none; }
.metric-val {
    font-size: 26px; font-weight: 700;
    color: #fafafa; letter-spacing: -1px;
    line-height: 1;
}
.metric-val span {
    background: linear-gradient(135deg,#6366f1,#10b981);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
}
.metric-key {
    font-size: 10px; color: #3f3f46; margin-top: 5px;
    text-transform: uppercase; letter-spacing: 0.1em; font-weight: 600;
}

/* ─ FEATURES GRID ─ */
.features {
    position: relative; z-index: 10;
    max-width: 880px; margin: 0 auto 64px;
    padding: 0 40px;
    display: grid; grid-template-columns: repeat(3,1fr); gap: 12px;
}
.feat {
    background: #111113;
    border: 1px solid #1c1c1f;
    border-radius: 14px; padding: 24px 20px;
    transition: border-color 0.2s, background 0.2s;
}
.feat:hover {
    border-color: #27272a;
    background: #141416;
}
.feat-icon {
    font-size: 20px; margin-bottom: 10px;
    display: block;
}
.feat-name {
    font-size: 13px; font-weight: 600;
    color: #e4e4e7; margin-bottom: 5px;
}
.feat-desc { font-size: 12px; color: #52525b; line-height: 1.55; }

/* ─ AUTH SHELL ─ */
.auth-wrap {
    position: relative; z-index: 10;
    max-width: 400px; margin: 0 auto 32px;
    padding: 0 24px;
}
.auth-heading {
    text-align: center; font-size: 13px;
    color: #3f3f46; margin-bottom: 16px;
    letter-spacing: 0.08em; text-transform: uppercase; font-weight: 600;
}

/* Streamlit overrides */
div[data-testid="stTabs"] {
    background: #111113 !important;
    border: 1px solid #1c1c1f !important;
    border-radius: 16px !important;
    padding: 24px !important;
}
button[data-baseweb="tab"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important; font-weight: 500 !important;
    color: #52525b !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #fafafa !important;
}
div[data-baseweb="tab-highlight"] {
    background: #6366f1 !important; height: 2px !important;
}
div[data-baseweb="tab-border"] { background: #1c1c1f !important; }

div[data-testid="stTextInput"] > label {
    font-size: 12px !important; font-weight: 500 !important;
    color: #52525b !important; letter-spacing: 0.04em !important;
    font-family: 'Inter', sans-serif !important;
}
div[data-testid="stTextInput"] input {
    background: #0c0c0f !important;
    border: 1px solid #27272a !important;
    border-radius: 10px !important;
    color: #fafafa !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 14px !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.1) !important;
    outline: none !important;
}
div[data-testid="stTextInput"] input::placeholder { color: #3f3f46 !important; }

div[data-testid="stButton"] > button {
    width: 100% !important;
    background: #6366f1 !important;
    color: #fff !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important; font-size: 14px !important;
    border: none !important; border-radius: 10px !important;
    padding: 11px 0 !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.4), 0 0 0 1px rgba(99,102,241,0.3) !important;
    transition: all 0.15s ease !important;
    letter-spacing: -0.1px !important;
}
div[data-testid="stButton"] > button:hover {
    background: #5558e3 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(99,102,241,0.3) !important;
}

div[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 13px !important;
}

/* ─ FOOTER ─ */
.footer {
    position: relative; z-index: 10;
    text-align: center; padding: 0 0 40px;
    font-size: 11px; color: #27272a; font-weight: 500;
    letter-spacing: 0.05em;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page">
<div class="blob blob-1"></div>
<div class="blob blob-2"></div>
<div class="blob blob-3"></div>

<div class="nav">
  <div class="logo"><span class="logo-dot"></span>LifeOS</div>
  <span class="nav-badge">Early Access</span>
</div>

<div class="hero">
  <div class="hero-eyebrow"><span class="live-dot"></span>AI-Powered · Real-time Predictions</div>
  <div class="hero-title">The goal engine that</div>
  <span class="hero-title-em">actually works.</span>
  <p class="hero-sub">
    Track your daily progress, predict success with <b>machine learning</b>,
    and get personalized insights — before it's too late to change course.
  </p>
</div>

<div class="metrics">
  <div class="metric">
    <div class="metric-val"><span>94%</span></div>
    <div class="metric-key">ML Accuracy</div>
  </div>
  <div class="metric">
    <div class="metric-val"><span>3×</span></div>
    <div class="metric-key">Consistency</div>
  </div>
  <div class="metric">
    <div class="metric-val"><span>21d</span></div>
    <div class="metric-key">Habit Lock-in</div>
  </div>
  <div class="metric">
    <div class="metric-val"><span>∞</span></div>
    <div class="metric-key">Goals</div>
  </div>
</div>

<div class="features">
  <div class="feat">
    <span class="feat-icon">📊</span>
    <div class="feat-name">Smart Tracking</div>
    <div class="feat-desc">Log work, mood, energy & screen time. Everything in one place.</div>
  </div>
  <div class="feat">
    <span class="feat-icon">🔮</span>
    <div class="feat-name">AI Prediction</div>
    <div class="feat-desc">ML model predicts your success probability in real-time.</div>
  </div>
  <div class="feat">
    <span class="feat-icon">⚡</span>
    <div class="feat-name">Planning Engine</div>
    <div class="feat-desc">Daily targets auto-calculated from your pace and deadline.</div>
  </div>
  <div class="feat">
    <span class="feat-icon">🔥</span>
    <div class="feat-name">Streak System</div>
    <div class="feat-desc">Visual streaks and consistency tracking to keep you going.</div>
  </div>
  <div class="feat">
    <span class="feat-icon">🍅</span>
    <div class="feat-name">Focus Timer</div>
    <div class="feat-desc">Built-in Pomodoro timer for deep, distraction-free work.</div>
  </div>
  <div class="feat">
    <span class="feat-icon">🧠</span>
    <div class="feat-name">Well-being Score</div>
    <div class="feat-desc">Tracks mood, stress and sleep impact on your performance.</div>
  </div>
</div>

<div class="auth-wrap">
  <div class="auth-heading">Get started</div>
</div>
""", unsafe_allow_html=True)

# ── AUTH ─────────────────────────────────────────────────
tab1, tab2 = st.tabs(["Sign in", "Create account"])

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
                st.error("Invalid username or password")

with tab2:
    u2 = st.text_input("Username", key="ru", placeholder="choose_a_username")
    p2 = st.text_input("Password", type="password", key="rp", placeholder="min 6 characters")
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
<div class="footer">LifeOS © 2025 &nbsp;·&nbsp; Built with AI &nbsp;·&nbsp; All rights reserved</div>
</div>
""", unsafe_allow_html=True)
