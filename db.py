"""
db.py — Shared database connection & all data functions
"""
import streamlit as st
import psycopg2
import psycopg2.extras
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from contextlib import contextmanager


def get_conn():
    url = st.secrets["DATABASE_URL"]
    return psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)


@contextmanager
def get_cursor(commit=False):
    conn = get_conn()
    cur  = conn.cursor()
    try:
        yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


def init_db():
    with get_cursor(commit=True) as cur:
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
                category TEXT DEFAULT 'General',
                notes TEXT DEFAULT '',
                status TEXT DEFAULT 'Active',
                starting_point INTEGER DEFAULT 0,
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
        for ddl in [
            "ALTER TABLE goals ADD COLUMN IF NOT EXISTS category TEXT DEFAULT 'General'",
            "ALTER TABLE goals ADD COLUMN IF NOT EXISTS notes TEXT DEFAULT ''",
            "ALTER TABLE goals ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'Active'",
            "ALTER TABLE goals ADD COLUMN IF NOT EXISTS starting_point INTEGER DEFAULT 0",
            "ALTER TABLE logs ADD COLUMN IF NOT EXISTS sleep FLOAT DEFAULT 7",
        ]:
            cur.execute(ddl)
        cur.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'uniq_user_goal_name') THEN
                    BEGIN
                        ALTER TABLE goals ADD CONSTRAINT uniq_user_goal_name UNIQUE (user_id, name);
                    EXCEPTION WHEN others THEN NULL;
                    END;
                END IF;
            END $$;
        """)


# ── USER AUTH ────────────────────────────────────────────
def get_user(username):
    with get_cursor() as cur:
        cur.execute("SELECT id, password FROM users WHERE username=%s", (username,))
        row = cur.fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id):
    with get_cursor() as cur:
        cur.execute("SELECT id, username, password FROM users WHERE id=%s", (user_id,))
        row = cur.fetchone()
    return dict(row) if row else None


def update_username(user_id, new_username):
    new_username = (new_username or "").strip()
    if len(new_username) < 3:
        return False, "Username must be at least 3 characters"
    with get_cursor(commit=True) as cur:
        cur.execute("SELECT id FROM users WHERE username=%s AND id!=%s", (new_username, user_id))
        if cur.fetchone():
            return False, "Username already taken"
        cur.execute("UPDATE users SET username=%s WHERE id=%s", (new_username, user_id))
    return True, "Username updated"


def create_user(username, hashed_password):
    with get_cursor(commit=True) as cur:
        cur.execute("SELECT id FROM users WHERE username=%s", (username,))
        if cur.fetchone():
            return False, "Username already taken"
        cur.execute("INSERT INTO users (username, password) VALUES (%s,%s)", (username, hashed_password))
    return True, "Account created"


# ── GOALS ────────────────────────────────────────────────
def get_goals(user_id, include_archived=False):
    with get_cursor() as cur:
        if include_archived:
            cur.execute(
                "SELECT id,name,target,deadline,category,notes,status,starting_point FROM goals WHERE user_id=%s ORDER BY id",
                (user_id,))
        else:
            cur.execute(
                "SELECT id,name,target,deadline,category,notes,status,starting_point FROM goals WHERE user_id=%s AND status != 'Archived' ORDER BY id",
                (user_id,))
        rows = cur.fetchall()
    return [dict(r) for r in rows]


def goal_name_exists(user_id, name, exclude_id=None):
    with get_cursor() as cur:
        if exclude_id:
            cur.execute("SELECT id FROM goals WHERE user_id=%s AND LOWER(name)=LOWER(%s) AND id!=%s", (user_id, name, exclude_id))
        else:
            cur.execute("SELECT id FROM goals WHERE user_id=%s AND LOWER(name)=LOWER(%s)", (user_id, name))
        return cur.fetchone() is not None


def create_goal(user_id, name, target, deadline, category="General", notes="", starting_point=0):
    name = name.strip()
    if goal_name_exists(user_id, name):
        return False, "A goal with this name already exists"
    if not target or target <= 0:
        return False, "Target must be greater than 0"
    if isinstance(deadline, str):
        deadline = date.fromisoformat(deadline)
    if deadline < date.today():
        return False, "Deadline cannot be in the past"
    if starting_point and starting_point >= target:
        return False, "Starting point must be less than the target"
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                "INSERT INTO goals (user_id,name,target,deadline,category,notes,starting_point) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (user_id, name, target, str(deadline), category, notes.strip(), starting_point or 0)
            )
        return True, "Goal created"
    except psycopg2.errors.UniqueViolation:
        return False, "A goal with this name already exists"


def update_goal(goal_id, user_id, name, target, deadline, category, notes, status):
    name = name.strip()
    if goal_name_exists(user_id, name, exclude_id=goal_id):
        return False, "A goal with this name already exists"
    if not target or target <= 0:
        return False, "Target must be greater than 0"
    try:
        with get_cursor(commit=True) as cur:
            cur.execute(
                "UPDATE goals SET name=%s,target=%s,deadline=%s,category=%s,notes=%s,status=%s WHERE id=%s AND user_id=%s",
                (name, target, str(deadline), category, notes.strip(), status, goal_id, user_id)
            )
        return True, "Goal updated"
    except psycopg2.errors.UniqueViolation:
        return False, "A goal with this name already exists"


def delete_goal(goal_id, user_id):
    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM goals WHERE id=%s AND user_id=%s", (goal_id, user_id))
    return True, "Goal deleted"


def set_goal_status(goal_id, user_id, status):
    with get_cursor(commit=True) as cur:
        cur.execute("UPDATE goals SET status=%s WHERE id=%s AND user_id=%s", (status, goal_id, user_id))
    return True


# ── LOGS ─────────────────────────────────────────────────
def add_log(goal_id, user_id, done, mood, energy, screen_time, stress, sleep=7.0):
    now = datetime.now().isoformat()
    with get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO logs (goal_id,user_id,date,done,mood,energy,screen_time,stress,sleep) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (goal_id, user_id, now, done, mood, energy, screen_time, stress, sleep)
        )


def get_logs(goal_id, user_id):
    with get_cursor() as cur:
        cur.execute(
            "SELECT id,date,done,mood,energy,screen_time,stress,sleep FROM logs WHERE goal_id=%s AND user_id=%s ORDER BY date",
            (goal_id, user_id)
        )
        rows = cur.fetchall()
    return [dict(r) for r in rows]


def update_log(log_id, user_id, done, mood, energy, screen_time, stress, sleep):
    if done < 0 or screen_time < 0 or sleep < 0:
        return False, "Values can't be negative"
    with get_cursor(commit=True) as cur:
        cur.execute(
            "UPDATE logs SET done=%s,mood=%s,energy=%s,screen_time=%s,stress=%s,sleep=%s WHERE id=%s AND user_id=%s",
            (done, mood, energy, screen_time, stress, sleep, log_id, user_id)
        )
    return True, "Log updated"


def delete_log(log_id, user_id):
    with get_cursor(commit=True) as cur:
        cur.execute("DELETE FROM logs WHERE id=%s AND user_id=%s", (log_id, user_id))
    return True, "Log deleted"


# ── DAILY AGGREGATION (one row per calendar day) ─────────
def _daily_aggregate(logs_raw):
    """
    Collapses raw logs into ONE ROW PER DAY:
    - done, screen_time: summed
    - mood, energy, stress: averaged (snapshot values)
    - sleep: averaged per day (you sleep once per day, not per log entry)
    """
    if not logs_raw:
        return pd.DataFrame()
    df = pd.DataFrame(logs_raw)
    df["day"] = pd.to_datetime(df["date"]).dt.date
    agg = df.groupby("day").agg(
        done=("done", "sum"),
        screen_time=("screen_time", "sum"),
        mood=("mood", "mean"),
        energy=("energy", "mean"),
        stress=("stress", "mean"),
        sleep=("sleep", "mean"),
    ).reset_index()
    agg["day"] = pd.to_datetime(agg["day"])
    return agg.sort_values("day").reset_index(drop=True)


def _daily_series(logs_raw):
    """Aggregate raw logs into a regular daily series (done sum), zero-filled on gaps."""
    if not logs_raw:
        return pd.Series(dtype=float)
    df = pd.DataFrame(logs_raw)
    df["day"] = pd.to_datetime(df["date"]).dt.date
    daily = df.groupby("day")["done"].sum()
    daily.index = pd.to_datetime(daily.index)
    return daily.sort_index().asfreq("D", fill_value=0)


# ── COMPUTED STATUS ───────────────────────────────────────
def compute_status(goal, logs_raw):
    target         = goal["target"]
    deadline       = goal["deadline"]
    starting_point = goal.get("starting_point", 0) or 0
    total_done     = starting_point + sum(r["done"] for r in logs_raw)
    progress       = min((total_done / target) * 100, 100) if target else 0
    days_left      = max((datetime.fromisoformat(str(deadline)).date() - date.today()).days, 0)
    remaining      = max(target - total_done, 0)
    required       = remaining / max(days_left, 1)

    daily = _daily_series(logs_raw)
    if daily.empty:
        return {
            "progress": round(progress, 2), "required_per_day": round(required, 2),
            "current_avg": 0, "success_probability": 0, "status": "No Data",
            "reasons": ["No logs yet"], "positives": [], "window_done": [], "window_screen": [],
            "days_of_history": 0, "low_confidence": True,
        }

    # Calendar-continuous last-7-days window ENDING TODAY, zero-filled.
    # The old version looked at the last 7 *logged* days, so skipping days
    # made every stat look better instead of worse — missed days must count.
    today       = pd.Timestamp(date.today())
    win_idx     = pd.date_range(end=today, periods=7, freq="D")
    window_done = [float(v) for v in daily.reindex(win_idx, fill_value=0).values]

    sdf = pd.DataFrame(logs_raw)
    sdf["day"] = pd.to_datetime(sdf["date"]).dt.normalize()
    screen_by_day = sdf.groupby("day")["screen_time"].mean()
    window_screen = [float(screen_by_day.get(d, 0.0)) for d in win_idx]

    days_of_history = int(min((today - daily.index.min()).days + 1, 7))
    days_of_history = max(days_of_history, 1)
    low_confidence  = days_of_history < 7

    # During warm-up, average only over days that could have had logs, so a
    # 3-day-old goal isn't punished for the 4 days before it existed
    denom       = days_of_history if low_confidence else 7
    obs         = window_done[-denom:]
    obs_screen  = window_screen[-denom:]
    avg7        = sum(obs) / denom
    avg3        = sum(obs[-3:]) / min(3, denom)
    trend       = (avg3 - avg7) / max(avg7, 1)
    screen_avg  = sum(obs_screen) / denom
    consistency = sum(1 for x in obs if x > 0) / denom
    missed      = sum(1 for x in obs if x == 0)

    from model import predict_success, explain_prediction
    if low_confidence:
        prob = 0.5
        reasons   = []
        positives = [f"Collecting data — day {days_of_history} of 7"]
    else:
        prob = predict_success(window_done, window_screen, required)
        reasons, positives = explain_prediction(avg7, required, consistency, missed, trend, screen_avg)
    prob = max(0.0, min(prob, 1.0))

    if total_done >= target:
        status = "Completed"
    elif low_confidence:
        status = "Collecting Data"
    else:
        status = "Achievable" if prob > 0.6 else "At Risk"

    return {
        "progress": round(progress, 2), "required_per_day": round(required, 2),
        "current_avg": round(avg7, 2), "success_probability": round(prob * 100, 2),
        "status": status, "reasons": reasons, "positives": positives,
        "window_done": window_done, "window_screen": window_screen,
        "days_of_history": days_of_history, "low_confidence": low_confidence,
    }


def compute_streak(logs_raw):
    """Consecutive calendar days with output, ending today (an unlogged
    'today' doesn't break the streak until tomorrow)."""
    daily = _daily_series(logs_raw)
    if daily.empty:
        return 0
    today = pd.Timestamp(date.today())
    s = daily.reindex(pd.date_range(daily.index.min(), today, freq="D"), fill_value=0)
    vals = list(s.values)
    if vals and vals[-1] == 0:
        vals = vals[:-1]
    streak = 0
    for v in reversed(vals):
        if v > 0: streak += 1
        else: break
    return streak


def compute_wellbeing(logs_raw):
    """Wellbeing score + per-factor breakdown + targeted mental-health advice.
    Factors are averaged over the last 5 logged days."""
    daily = _daily_aggregate(logs_raw)
    if daily.empty:
        return {"score": 0, "suggestions": ["No data yet"], "factors": [], "n_days": 0}
    recent = daily.tail(5)
    mood   = float(recent["mood"].mean())
    energy = float(recent["energy"].mean())
    stress = float(recent["stress"].mean())
    sleep  = float(recent["sleep"].mean())

    mood_s   = (mood - 1) / 4 * 100
    energy_s = (energy - 1) / 4 * 100
    stress_s = (5 - stress) / 4 * 100          # lower stress = higher score
    # 4h → 0, 8h → 100 (linear): 5h sleep should read "needs attention",
    # not the 62% the old min(sleep,8)/8 scale gave it
    sleep_s  = max(0.0, min(100.0, (sleep - 4) / 4 * 100))
    score    = max(0, min(100, int(round((mood_s + energy_s + stress_s + sleep_s) / 4))))

    def band(v):
        return "good" if v >= 70 else ("ok" if v >= 45 else "low")

    factors = [
        {"name": "Mood",   "display": f"{mood:.1f}/5",   "score": int(mood_s),   "band": band(mood_s)},
        {"name": "Energy", "display": f"{energy:.1f}/5", "score": int(energy_s), "band": band(energy_s)},
        {"name": "Stress", "display": f"{stress:.1f}/5", "score": int(stress_s), "band": band(stress_s)},
        {"name": "Sleep",  "display": f"{sleep:.1f}h",   "score": int(sleep_s),  "band": band(sleep_s)},
    ]

    ADVICE = {
        "Sleep":  "aim for 7–8 hours on a fixed schedule — sleep is the single biggest lever for energy and focus. No screens for 30 min before bed.",
        "Stress": "try a 10-minute walk or slow 4-7-8 breathing before work blocks, and split big targets into 25-minute sprints with real breaks.",
        "Energy": "low energy responds fastest to sleep, daylight and movement — a short morning walk and regular meals beat late-day caffeine.",
        "Mood":   "schedule one thing you enjoy every day, get sunlight, and talk to someone you trust. Logging one small win daily measurably lifts mood.",
    }
    weakest = sorted(factors, key=lambda f: f["score"])[:2]
    suggestions = [f"{f['name']} needs attention — {ADVICE[f['name']]}" for f in weakest if f["score"] < 70]
    if not suggestions:
        suggestions = ["All four factors look healthy — protect your sleep routine and keep the current rhythm going."]
    return {"score": score, "suggestions": suggestions, "factors": factors, "n_days": int(len(recent))}


MIN_DAYS_FOR_CORRELATION = 8

def _correlation_strength(r):
    a = abs(r)
    if a < 0.10: return "negligible"
    if a < 0.30: return "weak"
    if a < 0.50: return "moderate"
    if a < 0.70: return "strong"
    return "very strong"


def compute_wellbeing_correlations(logs_raw):
    daily = _daily_aggregate(logs_raw)
    if len(daily) < MIN_DAYS_FOR_CORRELATION:
        return {"available": False, "reason": f"Need at least {MIN_DAYS_FOR_CORRELATION} distinct days of data (have {len(daily)})."}
    factors = {"sleep": "Sleep (hrs)", "mood": "Mood", "energy": "Energy", "stress": "Stress", "screen_time": "Screen time (min)"}
    results = []
    for col, label in factors.items():
        if daily[col].nunique() < 2 or daily["done"].nunique() < 2:
            continue
        r = daily["done"].corr(daily[col])
        if pd.isna(r):
            continue
        results.append({"factor": label, "column": col, "r": round(float(r), 2),
                         "strength": _correlation_strength(r), "direction": "positive" if r > 0 else "negative"})
    results.sort(key=lambda x: abs(x["r"]), reverse=True)
    return {"available": True, "n": len(daily), "results": results, "scatter_df": daily}


def compute_insight(goal, logs_raw):
    target, deadline = goal["target"], goal["deadline"]
    daily = _daily_aggregate(logs_raw)
    if daily.empty:
        return {"explanation": "No data yet", "suggestion": "Start logging regularly"}
    total_done  = (goal.get("starting_point", 0) or 0) + daily["done"].sum()
    days_left   = max((datetime.fromisoformat(str(deadline)).date() - date.today()).days, 0)
    remaining   = max(target - total_done, 0)
    required    = remaining / max(days_left, 1)
    avg         = total_done / max(len(daily), 1)
    avg_screen  = daily["screen_time"].mean()
    missed      = int((daily["done"].tail(7) == 0).sum())
    reasons, actions = [], []
    if avg < required:
        reasons.append("your current pace is lower than required")
        actions.append(f"increase effort to {round(required,1)} per day")
    if avg_screen > 60:
        reasons.append("your screen time is high")
        actions.append("reduce screen time by 30 minutes")
    if missed >= 3:
        reasons.append("your consistency dropped recently")
        actions.append("maintain streak and avoid missed days")
    explanation = ("You are behind because " + ", and ".join(reasons) + "." if reasons else "You are on track. Keep maintaining your pace.")
    suggestion  = ("To improve: " + ", and ".join(actions) + "." if actions else "Continue your current strategy.")
    return {"explanation": explanation, "suggestion": suggestion}


def compute_patterns(logs_raw):
    daily = _daily_aggregate(logs_raw)
    if len(daily) < 5:
        return []
    daily["day_name"] = daily["day"].dt.day_name()
    insights    = []
    weekday_avg = daily[daily["day"].dt.weekday < 5]["done"].mean()
    weekend_avg = daily[daily["day"].dt.weekday >= 5]["done"].mean()
    if pd.notna(weekday_avg) and pd.notna(weekend_avg):
        insights.append("You perform better on weekends" if weekend_avg > weekday_avg else "Your weekday performance is stronger")
    if daily["done"].sum() > 0:
        insights.append(f"Your best performing day is {daily.groupby('day_name')['done'].mean().idxmax()}")
    high_screen = daily[daily["screen_time"] > 60]["done"].mean()
    low_screen  = daily[daily["screen_time"] <= 60]["done"].mean()
    if pd.notna(high_screen) and pd.notna(low_screen) and high_screen < low_screen:
        insights.append("High screen time days reduce your productivity")
    return insights


def compute_weekly_report(logs_raw):
    daily = _daily_series(logs_raw)
    if daily.empty:
        return None
    today = pd.Timestamp(date.today())
    idx   = pd.date_range(end=today, periods=7, freq="D")
    week  = daily.reindex(idx, fill_value=0)

    total  = int(week.sum())
    avg    = round(float(week.mean()), 2)
    missed = int((week == 0).sum())
    streak = compute_streak(logs_raw)

    agg = _daily_aggregate(logs_raw)
    if not agg.empty:
        sw = agg.set_index("day")["screen_time"].reindex(idx, fill_value=0)
        avg_screen = round(float(sw.mean()), 2)
    else:
        avg_screen = 0.0

    best_day = week.idxmax().day_name() if total > 0 else "No activity"
    # risk from consistency, not raw units — works whether a unit is
    # 1 book or 1000 words
    risk = "High" if missed >= 4 else ("Medium" if missed >= 2 else "Low")
    summary = []
    if missed == 0:     summary.append("Perfect week — you showed up every single day")
    elif missed > 2:    summary.append(f"You missed {missed} days this week")
    if avg_screen > 60: summary.append("Your screen time was high")
    return {"total_done": total, "avg_per_day": avg, "missed_days": missed, "streak": streak,
            "avg_screen_time": avg_screen, "best_day": best_day, "risk": risk, "summary": summary}


MIN_DAYS_FOR_TREND_FORECAST = 14

def compute_forecast(goal, logs_raw, horizon_days=90):
    target         = goal["target"]
    starting_point = goal.get("starting_point", 0) or 0
    daily          = _daily_series(logs_raw)
    if daily.empty:
        return {"available": False, "reason": "No logs yet."}
    cumulative_so_far = starting_point + float(daily.sum())
    last_date         = daily.index.max()
    method = "simple_average"
    forecast_values = None
    if len(daily) >= MIN_DAYS_FOR_TREND_FORECAST and daily.std() > 0:
        try:
            from statsmodels.tsa.holtwinters import Holt
            model = Holt(daily.values, initialization_method="estimated").fit(optimized=True)
            forecast_values = np.clip(model.forecast(horizon_days), 0, None)
            method = "trend_aware"
        except Exception:
            forecast_values = None
    if forecast_values is None:
        forecast_values = [float(daily.mean())] * horizon_days
    forecast_dates = [last_date + pd.Timedelta(days=i+1) for i in range(horizon_days)]
    cum = cumulative_so_far
    cum_values, completion_date, capped = [], None, True
    for d, v in zip(forecast_dates, forecast_values):
        cum += float(v)
        cum_values.append(cum)
        if target and cum >= target:
            completion_date = d; capped = False; break
    return {
        "available": True, "method": method, "cumulative_so_far": round(cumulative_so_far, 2),
        "completion_date": completion_date, "capped": capped,
        "history_dates": list(daily.index), "history_cumulative": list(starting_point + daily.cumsum()),
        "forecast_dates": forecast_dates[:len(cum_values)], "forecast_cumulative": cum_values,
    }


MAX_DOWNWARD_ADJUSTMENT = 0.30
MAX_UPWARD_ADJUSTMENT   = 0.15

def compute_adaptive_target(base_required, logs_raw):
    if not logs_raw or base_required <= 0:
        return {"available": False}
    daily = _daily_aggregate(logs_raw)
    if daily.empty:
        return {"available": False}
    recent = daily.iloc[-1]
    # A days-old check-in says nothing about today — require freshness
    last_day = pd.to_datetime(recent["day"]).date()
    if (date.today() - last_day).days > 1:
        return {"available": False, "reason": "no recent check-in"}
    energy, mood, stress, sleep = recent["energy"], recent["mood"], recent["stress"], recent["sleep"]
    raw_adj = (0.35*(energy-3)/2 + 0.25*(mood-3)/2 + 0.25*(-(stress-3)/2) + 0.15*max(-1.0, min(1.0, (sleep-7)/3)))
    adjustment = max(-MAX_DOWNWARD_ADJUSTMENT, min(MAX_UPWARD_ADJUSTMENT, raw_adj))
    adjusted_target = round(base_required * (1 + adjustment), 1)
    factors = []
    if energy <= 2: factors.append("low energy")
    if mood   <= 2: factors.append("low mood")
    if stress >= 4: factors.append("high stress")
    if sleep  <  6: factors.append("short sleep")
    if energy >= 4 and stress <= 2: factors.append("good energy and low stress")
    return {
        "available": True, "base_required": round(base_required,1),
        "adjustment_pct": round(adjustment*100,1),
        "adjusted_target": max(adjusted_target, 0),
        "factors": factors, "is_reduced": adjustment < -0.01, "is_boosted": adjustment > 0.01,
    }


def compute_heatmap_data(logs_raw, weeks=18):
    daily = _daily_series(logs_raw)
    if daily.empty:
        return {"available": False}
    today = pd.Timestamp(date.today())
    end   = max(today, daily.index.max())
    start = end - pd.Timedelta(days=weeks*7-1)
    start -= pd.Timedelta(days=(start.weekday()+1) % 7)
    end   += pd.Timedelta(days=6-((end.weekday()+1) % 7))
    full_range = pd.date_range(start, end, freq="D")
    series = daily.reindex(full_range, fill_value=0)
    positive = series[series > 0]
    if len(positive) >= 4:
        q25, q50, q75 = positive.quantile([0.25, 0.5, 0.75])
    else:
        mx = positive.max() if len(positive) else 1
        q25, q50, q75 = mx*0.33, mx*0.66, mx*0.99
    def bucket(v):
        if v <= 0: return 0
        if v <= q25: return 1
        if v <= q50: return 2
        if v <= q75: return 3
        return 4
    weeks_grid, month_labels, last_month = [], [], None
    n_weeks = len(full_range) // 7
    for w in range(n_weeks):
        week_days = []
        for d in range(7):
            ts = full_range[w*7+d]
            val = float(series.loc[ts])
            week_days.append({"date": ts, "value": val, "bucket": bucket(val)})
        weeks_grid.append(week_days)
        m = week_days[0]["date"].strftime("%b")
        if m != last_month:
            month_labels.append((w, m)); last_month = m
    return {
        "available": True, "weeks": weeks_grid, "month_labels": month_labels,
        "active_days": int((series > 0).sum()), "total_days": len(series),
    }


def compute_cross_goal_competition(goal_logs_map):
    daily_map = {name: _daily_series(logs) for name, logs in goal_logs_map.items()}
    daily_map = {name: s for name, s in daily_map.items() if not s.empty}
    names, results = list(daily_map.keys()), []
    for i in range(len(names)):
        for j in range(i+1, len(names)):
            a_name, b_name = names[i], names[j]
            a, b = daily_map[a_name], daily_map[b_name]
            start, end = max(a.index.min(), b.index.min()), min(a.index.max(), b.index.max())
            if start > end: continue
            idx = pd.date_range(start, end, freq="D")
            if len(idx) < 10: continue
            a_al = a.reindex(idx, fill_value=0); b_al = b.reindex(idx, fill_value=0)
            if a_al.std() == 0 or b_al.std() == 0: continue
            r = a_al.corr(b_al)
            if pd.isna(r): continue
            relationship = "competing" if r <= -0.2 else ("complementary" if r >= 0.2 else "independent")
            results.append({"goal_a": a_name, "goal_b": b_name, "r": round(float(r),2),
                             "n_days": len(idx), "relationship": relationship})
    results.sort(key=lambda x: abs(x["r"]), reverse=True)
    return results


# ── DEMO DATA ─────────────────────────────────────────────
def _generate_demo_history(days=45):
    """Two goal histories that share the same person (same daily wellness)
    but COMPETE for time: heavy DSA days squeeze workouts out, and workouts
    have been declining lately — so Comparison, Priority and Interactions
    all have something real to show."""
    import random
    rng = random.Random(42)
    dsa_rows, gym_rows = [], []
    for i in range(days, 0, -1):
        d = datetime.now() - timedelta(days=i)
        sleep  = round(min(9.5, max(4.5, rng.gauss(7.1, 0.9))), 1)
        energy = max(1, min(5, int(round((sleep - 4.5) / 1.2 + rng.gauss(0.4, 0.7)))))
        mood   = max(1, min(5, energy + rng.choice([-1, 0, 0, 1])))
        stress = max(1, min(5, 6 - energy + rng.choice([-1, 0, 0])))

        # Goal 1 — DSA: weekday rhythm, improving trend, one rough patch
        base  = 3.4 if d.weekday() >= 5 else 2.2
        phase = 1.25 if i < 15 else (0.8 if i > 35 else 1.0)
        dsa   = 0
        if not ((20 <= i <= 22) or rng.random() < 0.08):
            dsa = max(0, int(rng.gauss(base * phase, 1.1)))
            if dsa == 0 and rng.random() < 0.6:
                dsa = 1
            if dsa > 0:
                screen = max(20, int(rng.gauss(95 - dsa * 8, 25)))
                dsa_rows.append((d, dsa, mood, energy, screen, stress, sleep))

        # Goal 2 — workouts: started strong, declining lately, and inversely
        # tied to DSA load (the "competing goals" signal)
        w_phase = 0.6 if i < 15 else (1.35 if i > 30 else 1.0)
        gym = max(0, int(round(rng.gauss(2.4 * w_phase - 0.5 * dsa, 0.7))))
        if gym > 0:
            gym_rows.append((d, gym, mood, energy, max(20, int(rng.gauss(80, 20))), stress, sleep))
    return dsa_rows, gym_rows


def seed_demo_data(user_id):
    """Creates TWO demo goals — one on track, one at risk — with ~6 weeks of
    realistic logs, so every feature (comparison, priority, interactions,
    correlations, forecast) lights up. Delete them from Profile → My Goals."""
    specs = [
        ("Demo — Solve 150 DSA problems", 150, 45, "Study",
         "Sample goal (doing well). Explore the dashboard, then delete both demo goals anytime from Profile → My Goals."),
        ("Demo — 100 workout sessions", 100, 40, "Health",
         "Sample goal (at risk — declining lately, competes with DSA time). Delete anytime from Profile → My Goals."),
    ]
    for name, *_ in specs:
        if goal_name_exists(user_id, name):
            return False, "Demo goals already exist — delete them first to reseed"

    ids = []
    for name, target, dl_days, cat, notes in specs:
        ok, msg = create_goal(user_id, name, target, date.today() + timedelta(days=dl_days),
                              category=cat, notes=notes)
        if not ok:
            return False, msg
        with get_cursor() as cur:
            cur.execute("SELECT id FROM goals WHERE user_id=%s AND name=%s", (user_id, name))
            ids.append(cur.fetchone()["id"])

    dsa_rows, gym_rows = _generate_demo_history()

    def pack(gid, rows):
        return [(gid, user_id, d.isoformat(), done, mood, energy, screen, stress, sleep)
                for (d, done, mood, energy, screen, stress, sleep) in rows]

    with get_cursor(commit=True) as cur:
        cur.executemany(
            "INSERT INTO logs (goal_id,user_id,date,done,mood,energy,screen_time,stress,sleep) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            pack(ids[0], dsa_rows) + pack(ids[1], gym_rows))
    return True, f"2 demo goals created — {len(dsa_rows)} + {len(gym_rows)} days of sample data"
