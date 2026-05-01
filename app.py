import streamlit as st
from db   import init_db, get_user, create_user
from auth import hash_password, verify_password, create_token, decode_token

st.set_page_config(
    page_title="LifeOS",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── ONE-TIME DB INIT ─────────────────────────────────────
try:
    init_db()
except Exception as e:
    st.error(f"❌ Database connection failed: {e}")
    st.stop()

# ── SESSION STATE ────────────────────────────────────────
if "token"    not in st.session_state: st.session_state.token    = None
if "user_id"  not in st.session_state: st.session_state.user_id  = None
if "username" not in st.session_state: st.session_state.username = None

if st.session_state.token and not st.session_state.user_id:
    uid = decode_token(st.session_state.token)
    if uid:
        st.session_state.user_id = uid
    else:
        st.session_state.token = None

if st.session_state.user_id:
    st.switch_page("pages/dashboard.py")

# ── STYLES ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=Unbounded:wght@700;900&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: #060810 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    color: #e2e8f0 !important;
}

[data-testid="stAppViewContainer"] > .main {
    background: #060810 !important;
}

.main .block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

[data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stDecoration"], #MainMenu, footer,
[data-testid="stSidebar"] {
    display: none !important;
}

/* ── HERO ── */
.hero-wrap {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    padding: 0 24px 60px;
    position: relative;
    overflow: hidden;
}

/* animated grid bg */
.hero-wrap::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image:
        linear-gradient(rgba(0,255,180,0.03) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,255,180,0.03) 1px, transparent 1px);
    background-size: 60px 60px;
    z-index: 0;
}

/* glow orbs */
.orb {
    position: fixed;
    border-radius: 50%;
    filter: blur(120px);
    pointer-events: none;
    z-index: 0;
    animation: float 12s ease-in-out infinite alternate;
}
.orb1 { width:500px;height:500px;top:-150px;left:-150px;background:rgba(0,255,180,0.07); }
.orb2 { width:400px;height:400px;top:30%;right:-150px;background:rgba(99,102,241,0.08);animation-delay:-5s; }
.orb3 { width:300px;height:300px;bottom:10%;left:20%;background:rgba(0,180,255,0.06);animation-delay:-9s; }

@keyframes float {
    from { transform: translate(0,0) scale(1); }
    to   { transform: translate(30px,25px) scale(1.08); }
}

/* ── NAV ── */
.nav {
    position: relative; z-index: 10;
    width: 100%; max-width: 900px;
    display: flex; align-items: center; justify-content: space-between;
    padding: 24px 0 0;
    margin: 0 auto;
}
.nav-logo {
    font-family: 'Unbounded', sans-serif;
    font-size: 18px; font-weight: 900;
    color: #00ffb4;
    letter-spacing: -0.5px;
}
.nav-pill {
    font-size: 11px; font-weight: 600;
    padding: 6px 14px; border-radius: 20px;
    background: rgba(0,255,180,0.08);
    border: 1px solid rgba(0,255,180,0.2);
    color: #00ffb4; letter-spacing: 0.08em;
    text-transform: uppercase;
}

/* ── HERO TEXT ── */
.hero-content {
    position: relative; z-index: 10;
    text-align: center;
    max-width: 780px;
    margin: 64px auto 0;
}

.hero-tag {
    display: inline-flex; align-items: center; gap: 8px;
    font-size: 12px; font-weight: 600; letter-spacing: 0.1em;
    text-transform: uppercase; color: #00ffb4;
    margin-bottom: 28px;
}
.hero-tag-dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #00ffb4;
    box-shadow: 0 0 10px #00ffb4;
    animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
    0%,100%{transform:scale(1);opacity:1;}
    50%{transform:scale(1.4);opacity:0.5;}
}

.hero-h1 {
    font-family: 'Unbounded', sans-serif;
    font-size: clamp(42px, 7vw, 88px);
    font-weight: 900;
    line-height: 1.0;
    color: #f8fafc;
    margin: 0 0 8px;
    letter-spacing: -2px;
}
.hero-h1-accent {
    font-family: 'Unbounded', sans-serif;
    font-size: clamp(42px, 7vw, 88px);
    font-weight: 900;
    line-height: 1.0;
    letter-spacing: -2px;
    background: linear-gradient(135deg, #00ffb4 0%, #00c8ff 50%, #a78bfa 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 32px;
}
.hero-sub {
    font-size: 17px;
    font-weight: 400;
    color: #64748b;
    line-height: 1.75;
    max-width: 520px;
    margin: 0 auto 48px;
}
.hero-sub strong { color: #94a3b8; font-weight: 600; }

/* ── STATS ROW ── */
.stats-row {
    display: flex; justify-content: center; gap: 0;
    max-width: 600px; margin: 0 auto 56px;
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 20px; overflow: hidden;
}
.stat {
    flex: 1; text-align: center;
    padding: 22px 16px;
    border-right: 1px solid rgba(255,255,255,0.05);
}
.stat:last-child { border-right: none; }
.stat-n {
    font-family: 'Unbounded', sans-serif;
    font-size: 28px; font-weight: 700;
    background: linear-gradient(135deg, #00ffb4, #00c8ff);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    line-height: 1;
}
.stat-l {
    font-size: 10px; color: #334155;
    margin-top: 6px; letter-spacing: 0.1em;
    text-transform: uppercase; font-weight: 600;
}

/* ── FEATURE CARDS ── */
.features {
    display: grid; grid-template-columns: repeat(3, 1fr);
    gap: 14px; max-width: 900px;
    margin: 0 auto 56px; width: 100%;
    position: relative; z-index: 10;
}
.feat-card {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 16px; padding: 28px 22px;
    transition: all 0.3s ease;
}
.feat-card:hover {
    border-color: rgba(0,255,180,0.2);
    background: rgba(0,255,180,0.03);
    transform: translateY(-3px);
}
.feat-icon { font-size: 22px; margin-bottom: 12px; }
.feat-name {
    font-size: 14px; font-weight: 600;
    color: #e2e8f0; margin-bottom: 6px;
}
.feat-desc { font-size: 12.5px; color: #475569; line-height: 1.6; }

/* ── AUTH CARD ── */
.auth-section {
    position: relative; z-index: 10;
    width: 100%; max-width: 420px;
    margin: 0 auto;
}
.auth-label {
    font-size: 11px; font-weight: 700;
    letter-spacing: 0.12em; text-transform: uppercase;
    color: #334155; text-align: center; margin-bottom: 20px;
}

/* Streamlit tab overrides */
div[data-testid="stTabs"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.07) !important;
    border-radius: 20px !important;
    padding: 28px !important;
}
button[data-baseweb="tab"] {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 13px !important; font-weight: 600 !important;
    color: #475569 !important; padding: 8px 20px !important;
    border-radius: 8px !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #00ffb4 !important;
    background: rgba(0,255,180,0.08) !important;
}
div[data-baseweb="tab-highlight"] { background: transparent !important; }
div[data-baseweb="tab-border"]    { background: rgba(255,255,255,0.06) !important; }

/* inputs */
div[data-testid="stTextInput"] input {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    color: #f1f5f9 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 14px !important;
    padding: 10px 14px !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: rgba(0,255,180,0.4) !important;
    box-shadow: 0 0 0 3px rgba(0,255,180,0.08) !important;
}
div[data-testid="stTextInput"] label {
    color: #64748b !important;
    font-size: 12px !important; font-weight: 600 !important;
    letter-spacing: 0.05em !important;
}

/* buttons */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #00ffb4, #00c8ff) !important;
    color: #020617 !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 700 !important; font-size: 14px !important;
    border: none !important; border-radius: 10px !important;
    padding: 12px 0 !important; width: 100% !important;
    box-shadow: 0 4px 24px rgba(0,255,180,0.2) !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.02em !important;
}
div[data-testid="stButton"] > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 32px rgba(0,255,180,0.35) !important;
}

/* alerts */
div[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 13px !important;
}

/* ── FOOTER ── */
.footer {
    position: relative; z-index: 10;
    text-align: center; margin-top: 40px;
    font-size: 12px; color: #1e293b;
    font-weight: 500;
}
</style>
""", unsafe_allow_html=True)

# ── LAYOUT ───────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap">
<div class="orb orb1"></div>
<div class="orb orb2"></div>
<div class="orb orb3"></div>

<div class="nav">
  <span class="nav-logo">LifeOS</span>
  <span class="nav-pill">Beta v1</span>
</div>

<div class="hero-content">
  <div class="hero-tag">
    <span class="hero-tag-dot"></span>
    AI-Powered Goal Engine
  </div>
  <div class="hero-h1">Build habits that</div>
  <div class="hero-h1-accent">actually stick.</div>
  <p class="hero-sub">
    Track your daily work, predict success with <strong>ML-powered insights</strong>,
    and crush every goal you set — all in one place.
  </p>
</div>

<div class="stats-row">
  <div class="stat"><div class="stat-n">94%</div><div class="stat-l">Accuracy</div></div>
  <div class="stat"><div class="stat-n">3×</div><div class="stat-l">Consistency</div></div>
  <div class="stat"><div class="stat-n">21d</div><div class="stat-l">Habit Lock-in</div></div>
  <div class="stat"><div class="stat-n">∞</div><div class="stat-l">Goals</div></div>
</div>

<div class="features">
  <div class="feat-card">
    <div class="feat-icon">📊</div>
    <div class="feat-name">Smart Tracking</div>
    <div class="feat-desc">Log work, mood, energy & screen time every hour</div>
  </div>
  <div class="feat-card">
    <div class="feat-icon">🔮</div>
    <div class="feat-name">AI Prediction</div>
    <div class="feat-desc">Know your success probability before it's too late</div>
  </div>
  <div class="feat-card">
    <div class="feat-icon">⚡</div>
    <div class="feat-name">Planning Engine</div>
    <div class="feat-desc">Daily targets calculated automatically from your pace</div>
  </div>
  <div class="feat-card">
    <div class="feat-icon">🔥</div>
    <div class="feat-name">Streak System</div>
    <div class="feat-desc">Build consistency with visual streak tracking</div>
  </div>
  <div class="feat-card">
    <div class="feat-icon">🍅</div>
    <div class="feat-name">Focus Timer</div>
    <div class="feat-desc">Pomodoro sessions to keep you in deep work mode</div>
  </div>
  <div class="feat-card">
    <div class="feat-icon">🧠</div>
    <div class="feat-name">Well-being Score</div>
    <div class="feat-desc">Track mood, stress & energy impact on performance</div>
  </div>
</div>

<div class="auth-section">
  <div class="auth-label">— Get Started —</div>
</div>
""", unsafe_allow_html=True)

# ── AUTH TABS ────────────────────────────────────────────
tab1, tab2 = st.tabs(["🔐  Login", "📝  Register"])

with tab1:
    u = st.text_input("Username", key="lu", placeholder="Enter your username")
    p = st.text_input("Password", type="password", key="lp", placeholder="Enter your password")
    if st.button("Login →", key="lbtn"):
        if not u or not p:
            st.error("Please fill all fields")
        else:
            user = get_user(u)
            if user and verify_password(p, user["password"]):
                st.session_state.token    = create_token(user["id"])
                st.session_state.user_id  = user["id"]
                st.session_state.username = u
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

with tab2:
    u2 = st.text_input("Username", key="ru", placeholder="Choose a username (min 3 chars)")
    p2 = st.text_input("Password", type="password", key="rp", placeholder="Choose a password (min 6 chars)")
    if st.button("Create Account →", key="rbtn"):
        if len(u2.strip()) < 3:
            st.error("Username must be at least 3 characters")
        elif len(p2) < 6:
            st.error("Password must be at least 6 characters")
        else:
            ok, msg = create_user(u2.strip(), hash_password(p2))
            if ok:
                st.success("✅ Account created! Now login.")
            else:
                st.error(f"❌ {msg}")

st.markdown("""
  <div class="footer">LifeOS &copy; 2025 &nbsp;·&nbsp; Built with AI</div>
</div>
""", unsafe_allow_html=True)
