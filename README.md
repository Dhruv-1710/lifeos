# LifeOS — Streamlit Cloud Deploy Guide

## 📁 File Structure

```
lifeos/
├── app.py                    ← Main entry point (landing + login)
├── pages/
│   └── dashboard.py          ← Full dashboard
├── db.py                     ← All DB functions (no FastAPI needed)
├── auth.py                   ← Login / JWT (no FastAPI needed)
├── model.py                  ← ML prediction logic
├── model.pkl                 ← Trained model (commit this after training)
├── dataset.py                ← Run locally once to generate dataset.csv
├── train_model.py            ← Run locally once to generate model.pkl
├── requirements.txt
└── .streamlit/
    └── secrets.toml          ← Local only — DO NOT commit
```

---

## 🚀 Deploy on Streamlit Cloud (free)

### Step 1 — Push to GitHub
Push this entire folder to a **public or private** GitHub repo.

> ⚠️ Do NOT commit `.streamlit/secrets.toml`  
> Add it to `.gitignore`:
> ```
> .streamlit/secrets.toml
> model.pkl     ← optional: commit only after training
> dataset.csv   ← do not commit
> ```

### Step 2 — Go to share.streamlit.io
1. Login with GitHub
2. Click **New app**
3. Select your repo
4. **Main file path:** `app.py`
5. Click **Advanced settings → Secrets** and paste:

```toml
DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@db.xxx.supabase.co:5432/postgres"
SECRET_KEY   = "any-long-random-string-here"
```

6. Click **Deploy** ✅

---

## 🤖 Train the ML model (one time, locally)

Do this after you have some data in your Supabase DB (at least 10+ days of logs):

```bash
# 1. Set env variable
export DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@db.xxx.supabase.co:5432/postgres"

# 2. Generate dataset
python dataset.py

# 3. Train model
python train_model.py

# 4. Commit model.pkl
git add model.pkl
git commit -m "Add trained model"
git push
```

Streamlit Cloud will auto-redeploy.

> 💡 Without model.pkl the app still works — it uses a pace-based fallback for predictions.

---

## 🔄 How it works

```
User visits app.py (Streamlit Cloud URL)
        ↓
Login / Register → stored in Supabase
        ↓
Dashboard → reads/writes directly to Supabase
        ↓
ML prediction → model.pkl (committed to repo)
```

No separate backend. No Render. One URL. ✅
