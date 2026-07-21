"""
train_model.py — Train RandomForest on dataset.csv
Run: python train_model.py
"""
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
import joblib, os

DATA_PATH  = "dataset.csv"
MODEL_PATH = "model.pkl"
FEATURES   = ["avg","consistency","missed","trend","screen","streak","variance","momentum","screen_ratio"]

if not os.path.exists(DATA_PATH):
    print("dataset.csv not found — run dataset.py first"); exit()

df = pd.read_csv(DATA_PATH)
missing = [f for f in FEATURES if f not in df.columns]
if missing:
    print("Missing columns:", missing); exit()
if df["label"].nunique() < 2:
    print("Only one class in label — need more varied data"); exit()

df = df.replace([np.inf,-np.inf],np.nan).dropna(subset=FEATURES+["label"])
X, y = df[FEATURES], df["label"]
X_train,X_test,y_train,y_test = train_test_split(X,y,test_size=0.2,random_state=42,stratify=y)

model = RandomForestClassifier(n_estimators=250,max_depth=8,min_samples_split=4,
                               min_samples_leaf=2,random_state=42)
model.fit(X_train,y_train)

print("Accuracy:", round(accuracy_score(y_test,model.predict(X_test)),3))
print("ROC-AUC:", round(roc_auc_score(y_test,model.predict_proba(X_test)[:,1]),3))

joblib.dump(model,MODEL_PATH)
print("model.pkl saved — commit it to your repo and redeploy")
