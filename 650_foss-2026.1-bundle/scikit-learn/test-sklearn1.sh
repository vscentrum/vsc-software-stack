#!/usr/bin/env bash
set -euo pipefail

PYTHON=${PYTHON:-python}
EXPECTED_SKLEARN=${EXPECTED_SKLEARN:-1.8.0}

export OMP_NUM_THREADS=${OMP_NUM_THREADS:-2}
export OPENBLAS_NUM_THREADS=${OPENBLAS_NUM_THREADS:-2}
export MKL_NUM_THREADS=${MKL_NUM_THREADS:-2}
export NUMEXPR_NUM_THREADS=${NUMEXPR_NUM_THREADS:-2}

"$PYTHON" - <<'PY'
import os
import sys
import tempfile
import importlib
import numpy as np

expected = os.environ.get("EXPECTED_SKLEARN", "1.8.0")

mods = [
    "sklearn",
    "numpy",
    "scipy",
    "joblib",
    "threadpoolctl",
]

print(f"Python: {sys.version}")
for mod in mods:
    m = importlib.import_module(mod)
    print(f"{mod}: {getattr(m, '__version__', 'unknown')}")

import sklearn
if sklearn.__version__ != expected:
    raise RuntimeError(f"Expected scikit-learn {expected}, got {sklearn.__version__}")

try:
    import matplotlib
    print(f"matplotlib: {matplotlib.__version__}")
except ImportError:
    print("matplotlib: not available, skipping optional plotting check")

from scipy import sparse
from joblib import dump, load
from sklearn.datasets import make_classification, make_regression
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingRegressor
from sklearn.svm import SVC
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA, TruncatedSVD
from sklearn.neighbors import NearestNeighbors
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, r2_score

X, y = make_classification(
    n_samples=160,
    n_features=12,
    n_informative=7,
    n_redundant=2,
    class_sep=1.5,
    random_state=42,
)

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, stratify=y, random_state=42
)

clf = Pipeline([
    ("scale", StandardScaler()),
    ("logreg", LogisticRegression(max_iter=1000)),
])
clf.fit(X_train, y_train)
pred = clf.predict(X_test)
acc = accuracy_score(y_test, pred)
print(f"logistic regression accuracy: {acc:.3f}")
assert acc > 0.80

svc = Pipeline([
    ("scale", StandardScaler()),
    ("svc", SVC(kernel="rbf", gamma="scale")),
])
svc.fit(X_train, y_train)
svc_acc = accuracy_score(y_test, svc.predict(X_test))
print(f"SVC accuracy: {svc_acc:.3f}")
assert svc_acc > 0.80

rf = RandomForestClassifier(n_estimators=24, n_jobs=2, random_state=42)
scores = cross_val_score(rf, X, y, cv=3, n_jobs=2)
print(f"random forest CV accuracy: {scores.mean():.3f}")
assert scores.mean() > 0.75

grid = GridSearchCV(
    Pipeline([
        ("scale", StandardScaler()),
        ("logreg", LogisticRegression(max_iter=1000)),
    ]),
    {"logreg__C": [0.1, 1.0]},
    cv=3,
    n_jobs=2,
)
grid.fit(X, y)
print(f"grid-search best score: {grid.best_score_:.3f}")
assert grid.best_score_ > 0.75

X_reg, y_reg = make_regression(
    n_samples=140,
    n_features=10,
    n_informative=6,
    noise=5.0,
    random_state=42,
)

ridge = Pipeline([
    ("scale", StandardScaler()),
    ("ridge", Ridge(alpha=1.0)),
])
ridge.fit(X_reg, y_reg)
r2 = r2_score(y_reg, ridge.predict(X_reg))
print(f"ridge R2: {r2:.3f}")
assert r2 > 0.90

hgb = HistGradientBoostingRegressor(max_iter=20, random_state=42)
hgb.fit(X_reg, y_reg)
hgb_pred = hgb.predict(X_reg[:5])
print(f"hist-gradient-boosting predictions: {np.round(hgb_pred, 3)}")
assert np.isfinite(hgb_pred).all()

pca = PCA(n_components=4, svd_solver="full")
Xp = pca.fit_transform(StandardScaler().fit_transform(X))
print(f"PCA shape: {Xp.shape}")
assert Xp.shape == (160, 4)

km = KMeans(n_clusters=3, n_init=5, random_state=42)
labels = km.fit_predict(Xp)
print(f"KMeans clusters: {sorted(set(labels.tolist()))}")
assert len(set(labels.tolist())) == 3

Xs = sparse.random(80, 30, density=0.12, format="csr", random_state=42)
svd = TruncatedSVD(n_components=5, random_state=42)
Xs_red = svd.fit_transform(Xs)
print(f"sparse TruncatedSVD shape: {Xs_red.shape}")
assert Xs_red.shape == (80, 5)

nn = NearestNeighbors(n_neighbors=3, metric="cosine")
nn.fit(Xs)
dist, ind = nn.kneighbors(Xs[:4])
print(f"nearest-neighbors shapes: distances={dist.shape}, indices={ind.shape}")
assert dist.shape == (4, 3)
assert ind.shape == (4, 3)

X_mixed = np.array([
    [1.0, 10.0, "red"],
    [2.0, 20.0, "blue"],
    [np.nan, 30.0, "red"],
    [4.0, 40.0, "green"],
    [5.0, np.nan, "blue"],
], dtype=object)

pre = ColumnTransformer([
    ("num", Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ]), [0, 1]),
    ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), [2]),
])
Xt = pre.fit_transform(X_mixed)
print(f"ColumnTransformer shape: {Xt.shape}")
assert Xt.shape[0] == X_mixed.shape[0]
assert np.isfinite(Xt).all()

texts = [
    "excellent fast accurate model",
    "excellent robust prediction",
    "bad slow broken model",
    "poor inaccurate result",
    "fast reliable classifier",
    "broken unreliable classifier",
]
text_y = np.array([1, 1, 0, 0, 1, 0])

text_clf = Pipeline([
    ("tfidf", TfidfVectorizer()),
    ("logreg", LogisticRegression(max_iter=1000)),
])
text_clf.fit(texts, text_y)
text_pred = text_clf.predict(texts)
text_acc = accuracy_score(text_y, text_pred)
print(f"text pipeline training accuracy: {text_acc:.3f}")
assert text_acc >= 0.80

with tempfile.TemporaryDirectory() as tmpdir:
    path = os.path.join(tmpdir, "sklearn_model.joblib")
    dump(clf, path)
    restored = load(path)
    restored_pred = restored.predict(X_test)
    assert np.array_equal(pred, restored_pred)
    print(f"joblib model round-trip: {path}")

print("OK: scikit-learn smoke test passed")
PY