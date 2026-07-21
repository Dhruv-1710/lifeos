"""
dataset.py — Run locally to generate dataset.csv from your Supabase DB
Then run train_model.py to create model.pkl
"""
import os
import psycopg2
import pandas as pd
import numpy as np

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise Exception("Set DATABASE_URL env variable first:\nexport DATABASE_URL='postgresql://...'")

conn = psycopg2.connect(DATABASE_URL)
df   = pd.read_sql_query("SELECT goal_id, date, done, screen_time FROM logs ORDER BY date", conn)
conn.close()

if df.empty:
    print("No logs found"); exit()

df["date"] = pd.to_datetime(df["date"])
df["day"]  = df["date"].dt.date
dataset    = []

for gid in df["goal_id"].unique():
    gdf   = df[df["goal_id"]==gid].copy()
    daily = gdf.groupby("day").agg({"done":"sum","screen_time":"mean"})
    daily.index = pd.to_datetime(daily.index)
    # zero-fill calendar gaps so missed days count as 0 — MUST match how the
    # app builds its live 7-day window, otherwise train/serve features differ
    daily = daily.asfreq("D")
    daily["done"]        = daily["done"].fillna(0)
    daily["screen_time"] = daily["screen_time"].fillna(0)
    daily = daily.reset_index().rename(columns={"index": "day"})
    if len(daily) < 10:
        continue
    for i in range(7, len(daily)-3):
        w            = daily.iloc[i-7:i]
        avg          = w["done"].mean()
        consistency  = (w["done"]>0).mean()
        missed       = int((w["done"]==0).sum())
        screen       = w["screen_time"].mean()
        last3_mean   = w["done"].iloc[-3:].mean()
        trend        = (last3_mean-avg)/max(avg,1)
        streak = 0
        for val in reversed(w["done"].tolist()):
            if val>0: streak+=1
            else: break
        variance     = w["done"].std() or 0
        momentum     = last3_mean/max(avg,0.001)
        screen_ratio = screen/max(avg,0.001)
        fut          = daily.iloc[i:i+4]["done"]
        # success = keeps showing up AND doesn't collapse. Based on future
        # ACTIVITY, not level — level-based labels suffer mean-reversion.
        fut_active   = (fut > 0).mean()
        fut_avg      = fut.mean()
        label        = 1 if (fut_active >= 0.5 and fut_avg >= avg * 0.6) else 0
        dataset.append([avg,consistency,missed,trend,screen,streak,variance,momentum,screen_ratio,label])

if not dataset:
    print("Not enough data sequences"); exit()

out = pd.DataFrame(dataset, columns=["avg","consistency","missed","trend","screen","streak","variance","momentum","screen_ratio","label"])
out = out.replace([float("inf"),float("-inf")],float("nan")).dropna()
out.to_csv("dataset.csv",index=False)
print(f"dataset.csv saved — {out.shape[0]} rows")
print("Now run: python train_model.py")
