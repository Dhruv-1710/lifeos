"""
db.py — Shared database connection & all data functions
Streamlit secrets se DATABASE_URL leta hai
"""
import streamlit as st
import psycopg2
import psycopg2.extras
import pandas as pd
from datetime import datetime, date


def get_conn():
    url = st.secrets["DATABASE_URL"]
    return psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            target INTEGER NOT NULL,
            deadline TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id SERIAL PRIMARY KEY,
            goal_id INTEGER REFERENCES goals(id) ON DELETE CASCADE,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            date TEXT NOT NULL,
            done INTEGER DEFAULT 0,
            mood INTEGER DEFAULT 3,
            energy INTEGER DEFAULT 3,
            screen_time INTEGER DEFAULT 0,
            stress INTEGER DEFAULT 3,
            sleep FLOAT DEFAULT 7
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


# ── USER AUTH ────────────────────────────────────────────
def get_user(username):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, password FROM users WHERE username=%s", (username,))
    row = cur.fetchone()
    cur.close(); conn.close()
    return dict(row) if row else None


def create_user(username, hashed_password):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username=%s", (username,))
    if cur.fetchone():
        cur.close(); conn.close()
        return False, "Username already taken"
    cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, hashed_password))
    conn.commit()
    cur.close(); conn.close()
    return True, "Account created"


# ── GOALS ────────────────────────────────────────────────
def get_goals(user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name, target, deadline FROM goals WHERE user_id=%s ORDER BY id",
                (user_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [dict(r) for r in rows]


def create_goal(user_id, name, target, deadline):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO goals (user_id, name, target, deadline) VALUES (%s,%s,%s,%s)",
                (user_id, name, target, str(deadline)))
    conn.commit()
    cur.close(); conn.close()


# ── LOGS ─────────────────────────────────────────────────
def add_log(goal_id, user_id, done, mood, energy, screen_time, stress, sleep):
    conn = get_conn()
    cur = conn.cursor()
    now = datetime.now().isoformat()
    cur.execute(
        """INSERT INTO logs (goal_id, user_id, date, done, mood, energy, screen_time, stress, sleep)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (goal_id, user_id, now, done, mood, energy, screen_time, stress, sleep)
    )
    conn.commit()
    cur.close(); conn.close()


def get_logs(goal_id, user_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """SELECT date, done, mood, energy, screen_time, stress, sleep
        FROM logs WHERE goal_id=%s AND user_id=%s ORDER BY date""",
        (goal_id, user_id)
    )
    rows = cur.fetchall()
    cur.close(); conn.close()
    return [dict(r) for r in rows]


# ── COMPUTED STATUS ───────────────────────────────────────
def compute_status(goal, logs_raw):
    """Returns status dict same as old /status API"""
    from collections import defaultdict

    target   = goal["target"]
    deadline = goal["deadline"]

    total_done = sum(r["done"] for r in logs_raw)
    progress   = (total_done / target) * 100 if target else 0

    days_left = (datetime.fromisoformat(deadline).date() - date.today()).days
    days_left  = max(days_left, 0)
    remaining  = max(target - total_done, 0)
    required   = remaining / max(days_left, 1)

    day_map = defaultdict(lambda: {"done": 0, "screen": []})
    for r in logs_raw:
        try:
            day = r["date"].split("T")[0]
        except Exception:
            continue
        day_map[day]["done"] += r["done"]
        day_map[day]["screen"].append(r["screen_time"])

    if not day_map:
        return {
            "progress": round(progress, 2),
            "required_per_day": round(required, 2),
            "current_avg": 0,
            "success_probability": 0,
            "status": "No Data",
            "reasons": ["No logs yet"],
            "positives": [],
            "window_done": [],
            "window_screen": [],
        }

    days_sorted  = sorted(day_map.keys())
    last7_days   = days_sorted[-7:]
    window_done  = [day_map[d]["done"] for d in last7_days]
    window_screen = []
    for d in last7_days:
        sc = [s for s in day_map[d]["screen"] if isinstance(s, (int, float))]
        window_screen.append(sum(sc) / max(len(sc), 1))

    avg7        = sum(window_done) / max(len(window_done), 1)
    avg3        = sum(window_done[-3:]) / max(len(window_done[-3:]), 1)
    trend       = (avg3 - avg7) / max(avg7, 1)
    screen_avg  = sum(window_screen) / max(len(window_screen), 1)
    consistency = sum(1 for x in window_done if x > 0) / max(len(window_done), 1)
    missed      = sum(1 for x in window_done if x == 0)

    from model import predict_success, explain_prediction
    prob     = predict_success(window_done, window_screen, required)
    reasons, positives = explain_prediction(avg7, required, consistency, missed, trend, screen_avg)
    prob     = max(0.0, min(prob, 1.0))

    if total_done >= target:
        status = "Completed"
    else:
        status = "Achievable" if prob > 0.6 else "At Risk"

    return {
        "progress":            round(progress, 2),
        "required_per_day":    round(required, 2),
        "current_avg":         round(avg7, 2),
        "success_probability": round(prob * 100, 2),
        "status":              status,
        "reasons":             reasons,
        "positives":           positives,
        "window_done":         window_done,
        "window_screen":       window_screen,
    }


def compute_wellbeing(logs_raw):
    recent = logs_raw[-5:] if len(logs_raw) >= 5 else logs_raw
    if not recent:
        return {"score": 0, "suggestions": ["No data yet"]}
    mood   = sum(r["mood"]   for r in recent) / len(recent)
    energy = sum(r["energy"] for r in recent) / len(recent)
    stress = sum(r["stress"] for r in recent) / len(recent)
    sleep  = sum(r["sleep"]  for r in recent) / len(recent)
    score  = int(mood * 15 + energy * 15 + (5 - stress) * 15 + sleep * 5)
    score  = max(0, min(score, 100))
    suggestions = []
    if stress > 3: suggestions.append("Reduce stress — take short breaks")
    if energy < 3: suggestions.append("Low energy — rest more")
    if sleep  < 6: suggestions.append("Need more sleep — aim for 7-8 hours")
    return {"score": score, "suggestions": suggestions}


def compute_insight(goal, logs_raw):
    from collections import defaultdict
    target   = goal["target"]
    deadline = goal["deadline"]
    if not logs_raw:
        return {"explanation": "No data yet", "suggestion": "Start logging regularly"}
    total_done  = sum(r["done"] for r in logs_raw)
    screen_list = [r["screen_time"] for r in logs_raw]
    days_left   = max((datetime.fromisoformat(deadline).date() - date.today()).days, 0)
    remaining   = max(target - total_done, 0)
    required    = remaining / max(days_left, 1)
    day_map     = defaultdict(int)
    for r in logs_raw:
        day_map[r["date"].split("T")[0]] += r["done"]
    avg        = total_done / max(len(day_map), 1)
    avg_screen = sum(screen_list) / max(len(screen_list), 1)
    missed     = sum(1 for x in [r["done"] for r in logs_raw[-7:]] if x == 0)
    reasons, actions = [], []
    if avg < required:
        reasons.append("your current pace is lower than required")
        actions.append(f"increase effort to {round(required, 1)} per day")
    if avg_screen > 60:
        reasons.append("your screen time is high")
        actions.append("reduce screen time by 30 minutes")
    if missed >= 3:
        reasons.append("your consistency dropped recently")
        actions.append("maintain streak and avoid missed days")
    explanation = ("You are behind because " + ", and ".join(reasons) + "."
                   if reasons else "You are on track. Keep maintaining your pace.")
    suggestion  = ("To improve, you should " + ", and ".join(actions) + "."
                   if actions else "Continue your current strategy.")
    return {"explanation": explanation, "suggestion": suggestion}


def compute_patterns(logs_raw):
    if len(logs_raw) < 5:
        return []
    df = pd.DataFrame(logs_raw)
    df["date"] = pd.to_datetime(df["date"])
    df["day"]  = df["date"].dt.day_name()
    insights   = []
    weekday_avg = df[df["date"].dt.weekday < 5]["done"].mean()
    weekend_avg = df[df["date"].dt.weekday >= 5]["done"].mean()
    if weekend_avg > weekday_avg:
        insights.append("You perform better on weekends")
    else:
        insights.append("Your weekday performance is stronger")
    if df["done"].sum() > 0:
        best_day = df.groupby("day")["done"].mean().idxmax()
        insights.append(f"Your best performing day is {best_day}")
    high_screen = df[df["screen_time"] > 60]["done"].mean()
    low_screen  = df[df["screen_time"] <= 60]["done"].mean()
    if pd.notna(high_screen) and pd.notna(low_screen) and high_screen < low_screen:
        insights.append("High screen time days reduce your productivity")
    return insights


def compute_weekly_report(logs_raw):
    if not logs_raw:
        return None
    df     = pd.DataFrame(logs_raw)
    df["date"] = pd.to_datetime(df["date"])
    last7  = df.tail(7)
    total  = int(last7["done"].sum())
    avg    = round(last7["done"].mean(), 2)
    missed = int((last7["done"] == 0).sum())
    streak = 0
    for val in reversed(last7["done"].tolist()):
        if val > 0: streak += 1
        else: break
    avg_screen = round(last7["screen_time"].mean(), 2)
    best_day   = (last7.loc[last7["done"].idxmax()]["date"].day_name()
                  if last7["done"].sum() > 0 else "No activity")
    risk    = "High" if avg < 3 else ("Medium" if avg < 5 else "Low")
    summary = []
    if missed > 2:      summary.append("You missed several days this week")
    if avg_screen > 60: summary.append("Your screen time was high")
    if avg >= 5:        summary.append("You had a strong performance this week")
    return {
        "total_done": total, "avg_per_day": avg,
        "missed_days": missed, "streak": streak,
        "avg_screen_time": avg_screen, "best_day": best_day,
        "risk": risk, "summary": summary
    }
