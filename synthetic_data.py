"""
synthetic_data.py — Not enough real logs yet? Generate a realistic synthetic
dataset.csv to bootstrap the model.

Simulates 400 goal histories with varied personas (steady achievers, decliners,
weekend warriors, burnouts, erratic loggers) and extracts EXACTLY the same
9 features + label that dataset.py builds from real logs.

Run:  python synthetic_data.py      → creates dataset.csv
Then: python train_model.py         → creates model.pkl
Later, once you have a few weeks of real logs, retrain with dataset.py.
"""
import random
import numpy as np
import pandas as pd

rng = random.Random(7)
np.random.seed(7)

N_GOALS = 400
rows = []

for _ in range(N_GOALS):
    days       = rng.randint(30, 90)
    base       = rng.uniform(0.8, 6.0)         # personal baseline units/day
    weekend    = rng.uniform(0.6, 1.6)         # weekend multiplier
    drift      = rng.uniform(-0.02, 0.02)      # slow improving/declining trend
    miss_p     = rng.uniform(0.05, 0.35)       # probability of a missed day
    burnout_at = rng.randint(15, days) if rng.random() < 0.35 else None
    screen_mu  = rng.uniform(40, 140)
    noise      = rng.uniform(0.5, 1.6)

    done, screen = [], []
    level = base
    for t in range(days):
        level = max(0.2, level * (1 + drift + rng.gauss(0, 0.01)))
        mult  = weekend if (t % 7) >= 5 else 1.0
        if burnout_at and burnout_at <= t < burnout_at + rng.randint(3, 8):
            v = 0.0                             # burnout patch
        elif rng.random() < miss_p:
            v = 0.0                             # ordinary missed day
        else:
            v = max(0.0, rng.gauss(level * mult, noise))
        done.append(round(v, 1))
        screen.append(max(15.0, rng.gauss(screen_mu - v * 6, 22)))

    s, sc = pd.Series(done), pd.Series(screen)
    # identical sliding-window feature extraction to dataset.py
    for i in range(7, days - 3):
        w           = s.iloc[i-7:i]
        avg         = w.mean()
        consistency = (w > 0).mean()
        missed      = int((w == 0).sum())
        scr         = sc.iloc[i-7:i].mean()
        last3       = w.iloc[-3:].mean()
        trend       = (last3 - avg) / max(avg, 1)
        streak = 0
        for val in reversed(w.tolist()):
            if val > 0: streak += 1
            else: break
        variance     = w.std() or 0
        momentum     = last3 / max(avg, 0.001)
        screen_ratio = scr / max(avg, 0.001)
        fut          = s.iloc[i:i+4]
        # success = keeps showing up AND doesn't collapse. Based on future
        # ACTIVITY, not level — level-based labels suffer mean-reversion
        # (low performers look "safe", high performers look "risky")
        fut_active   = (fut > 0).mean()
        fut_avg      = fut.mean()
        label        = 1 if (fut_active >= 0.5 and fut_avg >= avg * 0.6) else 0
        rows.append([avg, consistency, missed, trend, scr, streak,
                     variance, momentum, screen_ratio, label])

out = pd.DataFrame(rows, columns=["avg", "consistency", "missed", "trend", "screen",
                                  "streak", "variance", "momentum", "screen_ratio", "label"])
out = out.replace([np.inf, -np.inf], np.nan).dropna()
out.to_csv("dataset.csv", index=False)
print(f"dataset.csv saved — {len(out)} rows ({out['label'].mean()*100:.0f}% positive class)")
print("Now run: python train_model.py")
