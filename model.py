import joblib
import os
import streamlit as st
import pandas as pd

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")

FEATURE_NAMES = ["avg","consistency","missed","trend","screen","streak","variance","momentum","screen_ratio"]
FEATURE_LABELS = {
    "avg":          "Daily average output",
    "consistency":  "Consistency (active days)",
    "missed":       "Missed days",
    "trend":        "Recent trend",
    "screen":       "Screen time",
    "streak":       "Current streak",
    "variance":     "Day-to-day variance",
    "momentum":     "Momentum",
    "screen_ratio": "Screen time vs output ratio",
}


@st.cache_resource
def load_model():
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None


def _build_features(window_done, window_screen):
    n = min(len(window_done), len(window_screen), 7)
    window = pd.DataFrame({"done": window_done[-n:], "screen_time": window_screen[-n:]})
    avg         = window["done"].mean()
    consistency = (window["done"] > 0).mean()
    missed      = int((window["done"] == 0).sum())
    screen      = window["screen_time"].mean()
    last3_mean  = window["done"].iloc[-3:].mean()
    trend       = (last3_mean - avg) / max(avg, 1)
    streak = 0
    for val in reversed(window["done"].tolist()):
        if val > 0: streak += 1
        else: break
    variance     = window["done"].std()
    variance     = 0 if pd.isna(variance) else variance
    momentum     = last3_mean / max(avg, 0.001)
    screen_ratio = screen / max(avg, 0.001)
    return {"avg": avg, "consistency": consistency, "missed": missed, "trend": trend,
            "screen": screen, "streak": streak, "variance": variance, "momentum": momentum, "screen_ratio": screen_ratio}


def _run_model(feats, required):
    model = load_model()
    if model is None:
        pace_ratio = feats["avg"] / max(required, 0.001)
        return round(max(0.05, min(pace_ratio / 2, 0.95)), 2)
    X          = pd.DataFrame([feats])[FEATURE_NAMES]
    prob       = model.predict_proba(X)[0][1]
    pace_ratio = feats["avg"] / max(required, 0.001)
    return round(max(0.05, min(0.9*prob + 0.1*(pace_ratio/2), 0.95)), 2)


def predict_success(window_done, window_screen, required):
    if len(window_done) < 7:
        return 0.5
    return _run_model(_build_features(window_done, window_screen), required)


def simulate_success(window_done, window_screen, required, overrides=None):
    if len(window_done) < 7:
        return None
    feats = _build_features(window_done, window_screen)
    if overrides:
        feats.update(overrides)
    return _run_model(feats, required)


def get_feature_importances():
    model = load_model()
    if model is None or not hasattr(model, "feature_importances_"):
        return None
    pairs = sorted(zip(FEATURE_NAMES, model.feature_importances_), key=lambda x: x[1], reverse=True)
    return [(name, FEATURE_LABELS.get(name, name), round(float(imp),3)) for name, imp in pairs]


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
