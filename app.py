import streamlit as st
from db   import init_db, get_user, create_user
from auth import hash_password, verify_password, create_token, decode_token

st.set_page_config(page_title="LifeOS", layout="wide", initial_sidebar_state="collapsed")

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

# ── AUTO-LOGIN FROM TOKEN ────────────────────────────────
if st.session_state.token and not st.session_state.user_id:
    uid = decode_token(st.session_state.token)
    if uid:
        st.session_state.user_id = uid
    else:
        st.session_state.token = None

# ── IF LOGGED IN → GO TO DASHBOARD ──────────────────────
if st.session_state.user_id:
    st.switch_page("pages/dashboard.py")

# ── STYLES ───────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Inter:wght@300;400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main,
[data-testid="stAppViewContainer"] > .main > .block-container {
    background: #0a0d14 !important;
    font-family: 'Inter', sans-serif !important;
    color: #f1f5f9;
    padding-top: 0 !important;
    margin-top: 0 !important;
}
[data-testid="stHeader"],[data-testid="stToolbar"],
[data-testid="stDecoration"],#MainMenu,footer {
    display: none !important; height: 0 !important;
}
[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

.lo-aurora { position:fixed;border-radius:50%;filter:blur(110px);
    opacity:0.13;z-index:0;pointer-events:none;
    animation:adrift 18s ease-in-out infinite alternate; }
.lo-a1{width:700px;height:600px;top:-200px;left:-250px;background:#00ffd5;}
.lo-a2{width:600px;height:600px;top:10%;right:-250px;background:#7c3aed;animation-delay:-7s;}
.lo-a3{width:500px;height:400px;bottom:5%;left:30%;background:#0ea5e9;animation-delay:-13s;}
@keyframes adrift{from{transform:translate(0,0) scale(1);}to{transform:translate(40px,35px) scale(1.1);}}

.lo-page { position:relative;z-index:1;max-width:1100px;margin:0 auto;padding:0 48px 80px; }

.lo-nav { display:flex;align-items:center;justify-content:space-between;
    padding:14px 0;border-bottom:1px solid rgba(255,255,255,0.06); }
.lo-logo { font-family:'Syne',sans-serif;font-size:20px;font-weight:800;
    background:linear-gradient(90deg,#00ffd5,#00aaff);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent; }
.lo-navbadge { font-size:11px;font-weight:500;padding:5px 13px;border-radius:20px;
    color:#00ffd5;background:rgba(0,255,213,.08);border:1px solid rgba(0,255,213,.2); }

.lo-hero { text-align:center;padding:60px 0 40px;
    display:flex;flex-direction:column;align-items:center; }
.lo-hero-badge { display:inline-flex;align-items:center;gap:8px;padding:7px 20px;
    border-radius:30px;margin-bottom:24px;background:rgba(0,255,213,.07);
    border:1px solid rgba(0,255,213,.2);color:#00ffd5;font-size:13px;font-weight:500; }
.lo-badge-dot { width:6px;height:6px;border-radius:50%;background:#00ffd5;
    animation:blink 2.2s ease-in-out infinite; }
@keyframes blink{0%,100%{opacity:1;transform:scale(1);}50%{opacity:.25;transform:scale(.55);}}
.lo-h1 { font-family:'Syne',sans-serif;font-size:clamp(46px,6vw,80px);
    font-weight:800;line-height:1;color:#f1f5f9;text-align:center;width:100%; }
.lo-h1-g { font-family:'Syne',sans-serif;font-size:clamp(46px,6vw,80px);
    font-weight:800;line-height:1;margin-bottom:20px;
    background:linear-gradient(90deg,#00ffd5,#00aaff,#7c3aed);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    text-align:center;width:100%; }
.lo-hero-sub { font-size:16px;font-weight:300;color:#94a3b8;line-height:1.8;
    width:100%;max-width:520px;text-align:center !important;margin:0 auto !important; }
.lo-hero-sub strong { color:#cbd5e1;font-weight:500; }

.lo-metrics { display:grid;grid-template-columns:repeat(4,1fr);
    background:rgba(255,255,255,.025);border:1px solid rgba(255,255,255,.07);
    border-radius:20px;overflow:hidden;margin:40px 0 50px; }
.lo-metric { text-align:center;padding:24px 16px;border-right:1px solid rgba(255,255,255,.06); }
.lo-metric:last-child{border-right:none;}
.lo-metric-n { font-family:'Syne',sans-serif;font-size:34px;font-weight:700;
    background:linear-gradient(90deg,#00ffd5,#00aaff);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;line-height:1; }
.lo-metric-l { font-size:10px;color:#475569;margin-top:6px;
    letter-spacing:.1em;text-transform:uppercase; }

.lo-grid { display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-bottom:50px; }
.lo-feat { background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.08);
    border-radius:20px;padding:36px 24px 28px;text-align:center;
    transition:transform .3s,border-color .3s,box-shadow .3s; }
.lo-feat:hover { transform:translateY(-5px);border-color:rgba(0,255,213,.25);
    box-shadow:0 20px 50px rgba(0,0,0,.45); }
.lo-feat-icon-wrap { width:68px;height:68px;border-radius:50%;
    display:flex;align-items:center;justify-content:center;margin:0 auto 18px;font-size:24px; }
.ic-t{background:rgba(0,255,213,.07);border:1.5px solid rgba(0,255,213,.3);}
.ic-b{background:rgba(0,170,255,.07);border:1.5px solid rgba(0,170,255,.3);}
.ic-p{background:rgba(124,58,237,.07);border:1.5px solid rgba(124,58,237,.3);}
.lo-feat-title{font-size:16px;font-weight:600;color:#f1f5f9;margin-bottom:8px;}
.lo-feat-line{width:34px;height:2.5px;border-radius:2px;margin:0 auto 12px;}
.ln-t{background:linear-gradient(90deg,#00ffd5,#00aaff);}
.ln-b{background:linear-gradient(90deg,#00aaff,#0ea5e9);}
.ln-p{background:linear-gradient(90deg,#7c3aed,#a78bfa);}
.lo-feat-desc{font-size:13px;color:#64748b;line-height:1.7;}

/* Auth card */
.auth-card { background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.09);
    border-radius:24px;padding:40px 36px;max-width:440px;margin:0 auto 60px; }
.auth-card h2 { font-family:'Syne',sans-serif;font-size:26px;font-weight:800;
    color:#f1f5f9;margin-bottom:24px;text-align:center; }

div[data-testid="stTextInput"] input {
    background:rgba(255,255,255,.06) !important;
    border:1px solid rgba(255,255,255,.12) !important;
    border-radius:10px !important;color:#f1f5f9 !important;
}
div[data-testid="stButton"] > button {
    background:linear-gradient(90deg,#00ffd5,#00aaff) !important;
    color:#030712 !important;font-weight:600 !important;font-size:15px !important;
    border:none !important;border-radius:12px !important;padding:12px 0 !important;
    box-shadow:0 8px 28px rgba(0,255,213,.28) !important;
    transition:all .25s ease !important;width:100%;
}
div[data-testid="stButton"] > button:hover {
    transform:translateY(-2px) scale(1.02) !important;
    box-shadow:0 14px 38px rgba(0,255,213,.42) !important;
}
div[data-testid="stTabs"] [data-baseweb="tab"] {
    color:#64748b !important;font-weight:500;
}
div[data-testid="stTabs"] [aria-selected="true"] {
    color:#00ffd5 !important;border-bottom:2px solid #00ffd5 !important;
}

.lo-footer { display:flex;align-items:center;justify-content:space-between;
    padding-top:24px;border-top:1px solid rgba(255,255,255,.06);flex-wrap:wrap;gap:10px; }
.lo-footer-logo { font-family:'Syne',sans-serif;font-size:14px;font-weight:700;
    background:linear-gradient(90deg,#00ffd5,#00aaff);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent; }
.lo-footer-copy,.lo-footer-links a { font-size:12px;color:#1e293b;text-decoration:none; }
.lo-footer-links { display:flex;gap:16px; }
</style>
""", unsafe_allow_html=True)

# ── AURORA ───────────────────────────────────────────────
st.markdown("""
<div class="lo-aurora lo-a1"></div>
<div class="lo-aurora lo-a2"></div>
<div class="lo-aurora lo-a3"></div>
<div class="lo-page">
""", unsafe_allow_html=True)

# ── NAV ──────────────────────────────────────────────────
st.markdown("""
<div class="lo-nav">
  <span class="lo-logo">LifeOS</span>
  <span class="lo-navbadge">v1 &middot; Beta</span>
</div>
""", unsafe_allow_html=True)

# ── HERO ─────────────────────────────────────────────────
st.markdown("""
<div class="lo-hero">
  <div class="lo-hero-badge"><span class="lo-badge-dot"></span>AI-Powered Productivity System</div>
  <div class="lo-h1">Design Your</div>
  <div class="lo-h1-g">Perfect Day.</div>
  <p class="lo-hero-sub">
    Turn daily actions into <strong>predictable success</strong> using intelligent
    tracking, real&#8209;time predictions, and an insights engine built for focused people.
  </p>
</div>
""", unsafe_allow_html=True)

# ── METRICS ──────────────────────────────────────────────
st.markdown("""
<div class="lo-metrics">
  <div class="lo-metric"><div class="lo-metric-n">94%</div><div class="lo-metric-l">Prediction Accuracy</div></div>
  <div class="lo-metric"><div class="lo-metric-n">3&times;</div><div class="lo-metric-l">More Consistent</div></div>
  <div class="lo-metric"><div class="lo-metric-n">21d</div><div class="lo-metric-l">Avg Habit Lock-In</div></div>
  <div class="lo-metric"><div class="lo-metric-n">&infin;</div><div class="lo-metric-l">Goals Supported</div></div>
</div>
""", unsafe_allow_html=True)

# ── FEATURES ─────────────────────────────────────────────
st.markdown("""
<div class="lo-grid">
  <div class="lo-feat"><div class="lo-feat-icon-wrap ic-t">&#128202;</div>
    <div class="lo-feat-title">Smart Tracking</div><div class="lo-feat-line ln-t"></div>
    <div class="lo-feat-desc">Track habits, daily work, and screen time in one place.</div></div>
  <div class="lo-feat"><div class="lo-feat-icon-wrap ic-b">&#129668;</div>
    <div class="lo-feat-title">AI Prediction</div><div class="lo-feat-line ln-b"></div>
    <div class="lo-feat-desc">Know your success probability in real-time with AI.</div></div>
  <div class="lo-feat"><div class="lo-feat-icon-wrap ic-p">&#128161;</div>
    <div class="lo-feat-title">Insights Engine</div><div class="lo-feat-line ln-p"></div>
    <div class="lo-feat-desc">Personalized insights and actions to improve fast.</div></div>
  <div class="lo-feat"><div class="lo-feat-icon-wrap ic-t">&#11088;</div>
    <div class="lo-feat-title">Streak System</div><div class="lo-feat-line ln-t"></div>
    <div class="lo-feat-desc">Build consistency and track streaks visually.</div></div>
  <div class="lo-feat"><div class="lo-feat-icon-wrap ic-b">&#128197;</div>
    <div class="lo-feat-title">Planning Engine</div><div class="lo-feat-line ln-b"></div>
    <div class="lo-feat-desc">Plan ahead and see future completion predictions.</div></div>
  <div class="lo-feat"><div class="lo-feat-icon-wrap ic-p">&#9201;</div>
    <div class="lo-feat-title">Focus Timer</div><div class="lo-feat-line ln-p"></div>
    <div class="lo-feat-desc">Stay focused with Pomodoro and deep work sessions.</div></div>
</div>
""", unsafe_allow_html=True)

# ── AUTH CARD ────────────────────────────────────────────
st.markdown('<div class="auth-card">', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

with tab1:
    username_l = st.text_input("Username", key="login_u")
    password_l = st.text_input("Password", type="password", key="login_p")
    if st.button("Login →", key="login_btn"):
        if not username_l or not password_l:
            st.error("Fill all fields")
        else:
            user = get_user(username_l)
            if user and verify_password(password_l, user["password"]):
                st.session_state.token    = create_token(user["id"])
                st.session_state.user_id  = user["id"]
                st.session_state.username = username_l
                st.success("✅ Logged in!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

with tab2:
    username_r = st.text_input("Username (min 3 chars)", key="reg_u")
    password_r = st.text_input("Password (min 6 chars)", type="password", key="reg_p")
    if st.button("Create Account →", key="reg_btn"):
        if len(username_r.strip()) < 3:
            st.error("Username too short")
        elif len(password_r) < 6:
            st.error("Password too short")
        else:
            ok, msg = create_user(username_r.strip(), hash_password(password_r))
            if ok:
                st.success("✅ Account created — now login!")
            else:
                st.error(f"❌ {msg}")

st.markdown('</div>', unsafe_allow_html=True)

# ── FOOTER ───────────────────────────────────────────────
st.markdown("""
<div class="lo-footer">
  <span class="lo-footer-logo">LifeOS</span>
  <span class="lo-footer-copy">&copy; 2025 LifeOS &middot; Built with AI</span>
  <div class="lo-footer-links"><a href="#">Privacy</a><a href="#">Terms</a></div>
</div>
</div>
""", unsafe_allow_html=True)
