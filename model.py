import joblib
import os
import pandas as pd

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")


def load_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None


def predict_success(window_done, window_screen, required):
    if len(window_done) < 7:
        return 0.5

    n = min(len(window_done), len(window_screen), 7)
    window = pd.DataFrame({
        "done":        window_done[-n:],
        "screen_time": window_screen[-n:]
    })

    avg         = window["done"].mean()
    consistency = (window["done"] > 0).mean()
    missed      = int((window["done"] == 0).sum())
    screen      = window["screen_time"].mean()
    last3_mean  = window["done"].iloc[-3:].mean()
    avg7        = window["done"].mean()
    trend       = (last3_mean - avg7) / max(avg7, 1)

    streak = 0
    for val in reversed(window["done"].tolist()):
        if val > 0: streak += 1
        else: break

    variance    = window["done"].std()
    variance    = 0 if pd.isna(variance) else variance
    momentum    = last3_mean / max(avg7, 0.001)
    screen_ratio = screen / max(avg, 0.001)

    X = pd.DataFrame([{
        "avg": avg, "consistency": consistency, "missed": missed,
        "trend": trend, "screen": screen, "streak": streak,
        "variance": variance, "momentum": momentum, "screen_ratio": screen_ratio
    }])

    model = load_model()
    if model is None:
        # fallback: pace-based estimate
        pace_ratio = avg / max(required, 0.001)
        return round(max(0.05, min(pace_ratio / 2, 0.95)), 2)

    prob       = model.predict_proba(X)[0][1]
    pace_ratio = avg / max(required, 0.001)
    prob       = 0.9 * prob + 0.1 * (pace_ratio / 2)
    return round(max(0.05, min(prob, 0.95)), 2)


def explain_prediction(avg, required, consistency, missed, trend, screen):
    reasons, positives = [], []
    pace_ratio = avg / max(required, 0.001)
    if pace_ratio < 1:    reasons.append("your current pace is lower than required")
    if consistency < 0.6: reasons.append("your consistency is low")
    if trend < 0:         reasons.append("your recent performance is declining")
    if screen > 60:       reasons.append("your screen time is high")
    if missed >= 3:       reasons.append("you missed several days recently")
    if pace_ratio >= 1:   positives.append("you are maintaining required pace")
    if consistency > 0.8: positives.append("you are consistent")
    if trend > 0:         positives.append("your performance is improving")
    if screen < 30:       positives.append("your screen time is under control")
    return reasons, positives
