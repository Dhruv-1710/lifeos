"""
dataset.py — Run locally to generate dataset.csv from your Supabase DB
Then run train_model.py to create model.pkl
Commit model.pkl to your repo.
"""
import os
import psycopg2
import pandas as pd
import numpy as np

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("Set DATABASE_URL env variable first")

conn = psycopg2.connect(DATABASE_URL)
df   = pd.read_sql_query(
    "SELECT goal_id, date, done, screen_time FROM logs ORDER BY date", conn
)
conn.close()

if df.empty:
    print("❌ No logs found")
    exit()

df["date"] = pd.to_datetime(df["date"])
df["day"]  = df["date"].dt.date
dataset    = []

for gid in df["goal_id"].unique():
    gdf   = df[df["goal_id"] == gid].copy()
    daily = gdf.groupby("day").agg({"done": "sum", "screen_time": "mean"}).reset_index()
    daily["screen_time"] = daily["screen_time"].fillna(0)
    if len(daily) < 10:
        continue
    for i in range(7, len(daily) - 3):
        w           = daily.iloc[i-7:i]
        avg         = w["done"].mean()
        consistency = (w["done"] > 0).mean()
        missed      = int((w["done"] == 0).sum())
        screen      = w["screen_time"].mean()
        last3_mean  = w["done"].iloc[-3:].mean()
        avg7        = w["done"].mean()
        trend       = (last3_mean - avg7) / max(avg7, 1)
        streak = 0
        for val in reversed(w["done"].tolist()):
            if val > 0: streak += 1
            else: break
        variance     = w["done"].std()
        variance     = 0 if pd.isna(variance) else variance
        momentum     = last3_mean / max(avg7, 0.001)
        screen_ratio = screen / max(avg, 0.001)
        future_avg   = daily.iloc[i:i+3]["done"].sum() / 3
        label        = 1 if future_avg > avg * 1.1 else 0
        dataset.append([avg, consistency, missed, trend, screen,
                        streak, variance, momentum, screen_ratio, label])

if not dataset:
    print("❌ Not enough data sequences")
    exit()

out = pd.DataFrame(dataset, columns=[
    "avg","consistency","missed","trend","screen",
    "streak","variance","momentum","screen_ratio","label"
])
out = out.replace([float("inf"), float("-inf")], float("nan")).dropna()
out.to_csv("dataset.csv", index=False)
print(f"✅ dataset.csv saved — {out.shape[0]} rows")
print("👉 Now run: python train_model.py")
