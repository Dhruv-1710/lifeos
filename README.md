# LifeOS — Own Your Day

AI-powered goal tracking and prediction app built with Streamlit + Supabase.

## Quick Start

### 1. Setup secrets
```
mkdir .streamlit
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your Supabase DATABASE_URL and a SECRET_KEY
```

### 2. Install dependencies
```
pip install -r requirements.txt
```

### 3. Run
```
streamlit run app.py
```

## File Structure
```
lifeos/
├── app.py                  ← Landing + login page
├── pages/
│   ├── dashboard.py        ← Main dashboard
│   └── profile.py          ← Profile, Goals CRUD, Account settings
├── db.py                   ← Database layer (Supabase/Postgres)
├── auth.py                 ← JWT + bcrypt + rate limiting
├── model.py                ← ML prediction + what-if simulator
├── dataset.py              ← Run locally to generate training data
├── train_model.py          ← Run locally to train model.pkl
├── requirements.txt
├── .gitignore
└── .streamlit/
    └── secrets.toml        ← Local only — DO NOT commit
```

## Deploy on Streamlit Cloud
1. Push to GitHub (ensure secrets.toml is in .gitignore)
2. Go to share.streamlit.io → New app
3. Set main file: `app.py`
4. Add secrets in Advanced settings:
```toml
DATABASE_URL = "postgresql://..."
SECRET_KEY   = "your-random-secret"
```

## Demo Data
New account? Click **"✨ Try with demo data"** on the dashboard — it creates a
sample goal with 6 weeks of realistic logs (weekday rhythm, an improving trend,
a missed patch, sleep-correlated energy) so every feature has something to show.
Delete it anytime from Profile → My Goals.

## Accuracy Notes (v2.1)
- All 7-day statistics use **calendar days ending today** (zero-filled), so
  missed days lower your stats instead of silently vanishing
- New goals show **"Collecting Data — day N/7"** instead of a fake 50% score
- Streaks count **consecutive calendar days** (an unlogged 'today' doesn't
  break the streak until tomorrow)
- Adjusted daily target only uses a mood/energy check-in from the **last 24h**
- The ideal-pace line runs from your start to the target at the deadline
- `dataset.py` builds training features the same calendar-aware way — if you
  trained a model before v2.1, re-run it so the model matches the app

## Train the ML Model (optional — app works without it)

**Not enough real logs yet?** Bootstrap with synthetic data (no DB needed):
```bash
python synthetic_data.py   # generates dataset.csv from 400 simulated users
python train_model.py      # generates model.pkl  (~0.81 accuracy)
```

**Once you have a few weeks of real logs**, retrain on your own data:
```bash
export DATABASE_URL="postgresql://..."   # Windows: $env:DATABASE_URL="..."
python dataset.py          # generates dataset.csv from your real logs
python train_model.py      # regenerates model.pkl
```
`model.pkl` sits in the project root; the app loads it automatically on next
run (the "What drives this prediction" chart appears, and predictions come from
the model instead of the pace-based fallback). Commit model.pkl to deploy it.

The success label = *"will keep showing up and not collapse"* (based on future
activity, not level — a level-based label makes steady high performers look
risky due to mean-reversion). synthetic_data.py and dataset.py use the exact
same 9 features, so a synthetic-trained model transfers cleanly to real data.

## Authentication
- bcrypt password hashing (rounds=12)
- JWT tokens (7-day expiry)
- Password policy: min 8 chars, 1 uppercase, 1 number
- Rate limiting: 5 failed attempts → 5 min lockout
- Password change + account delete from Profile page

## Tech Stack
Python · Streamlit · PostgreSQL (Supabase) · scikit-learn · statsmodels · bcrypt · JWT
