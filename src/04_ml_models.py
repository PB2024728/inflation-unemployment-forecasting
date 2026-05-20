"""
Day 5 — Machine learning forecasting models.
Builds a lagged feature matrix and runs Ridge, Lasso, Random Forest, XGBoost
under the same rolling-window backtest as the classical models.
"""

import os
import warnings
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import xgboost as xgb

warnings.filterwarnings("ignore")

PROC       = os.path.join("data", "processed", "macro_monthly.csv")
RES        = "results"
EVAL_START = "2000-01-01"
HORIZONS   = [1, 3, 6]
TARGETS    = ["infl_yoy", "unrate"]
N_LAGS     = 6   # lags of each predictor to include as features

PREDICTOR_COLS = [
    "infl_yoy", "core_infl_yoy", "unrate",
    "fedfunds", "gs10", "tb3ms", "spread",
    "d_indpro", "d_payems", "d_oil", "sentiment", "d_m2",
]

def load():
    return pd.read_csv(PROC, index_col="date", parse_dates=True)

def make_lag_features(df, n_lags=N_LAGS):
    """Create a DataFrame of lagged values for all predictor columns."""
    frames = [df[PREDICTOR_COLS]]
    for lag in range(1, n_lags + 1):
        lagged = df[PREDICTOR_COLS].shift(lag)
        lagged.columns = [f"{c}_lag{lag}" for c in PREDICTOR_COLS]
        frames.append(lagged)
    return pd.concat(frames, axis=1).dropna()

def get_models():
    return {
        "ridge": Pipeline([
            ("scaler", StandardScaler()),
            ("model",  Ridge(alpha=0.5)),     # lowered from 1.0 based on diagnostics
        ]),
        "lasso": Pipeline([
            ("scaler", StandardScaler()),
            ("model",  Lasso(alpha=0.005, max_iter=5000)),  # tightened from 0.01
        ]),
        "rf": RandomForestRegressor(
            n_estimators=100, max_depth=5, min_samples_leaf=5,
            n_jobs=-1, random_state=42
        ),
        "xgb": xgb.XGBRegressor(
            n_estimators=150, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            random_state=42, verbosity=0,
        ),
    }

def rolling_backtest_ml(df, min_train=60):
    feat_df = make_lag_features(df)
    eval_idx = feat_df.index[feat_df.index >= EVAL_START]
    records = []

    for t_idx, t in enumerate(eval_idx):
        X_train_full = feat_df[feat_df.index < t]
        if len(X_train_full) < min_train:
            continue

        actual_window = df[df.index >= t]

        for h in HORIZONS:
            if len(actual_window) < h:
                continue
            actual_h = actual_window.iloc[h - 1]

            # For h-step ahead: target is the value h months out,
            # features are the values available at time t (lag matrix already handles this).
            X_train = feat_df[feat_df.index < t]

            for target in TARGETS:
                # Build aligned (X, y) pairs: y at time s+h, X at time s
                y_index = df.index[df.index >= df.index[0]]
                target_series = df[target]

                # align: X rows up to t, y is the h-step-ahead value
                X_rows = feat_df[feat_df.index < t]
                # y for each row in X is the target value h months later
                y_dates = X_rows.index.shift(h, freq="MS")
                valid_mask = y_dates.isin(target_series.index)
                X_fit = X_rows[valid_mask]
                y_fit = target_series[y_dates[valid_mask]].values

                if len(X_fit) < 30:
                    continue

                # Features for prediction: use the most recent row (= time t)
                if t not in feat_df.index:
                    continue
                X_pred = feat_df.loc[[t]]
                act = actual_h[target]

                row = {"date": t, "horizon": h, "target": target, "actual": act}

                for name, mdl in get_models().items():
                    try:
                        mdl.fit(X_fit, y_fit)
                        row[name] = float(mdl.predict(X_pred)[0])
                    except Exception:
                        row[name] = np.nan

                records.append(row)

        if t_idx % 12 == 0:
            print(f"  ML backtest at {t.date()} …")

    return pd.DataFrame(records)

def compute_errors(fc_df):
    model_cols = ["ridge", "lasso", "rf", "xgb"]
    rows = []
    for (target, h), g in fc_df.groupby(["target", "horizon"]):
        for m in model_cols:
            if m not in g.columns:
                continue
            err = g["actual"] - g[m]
            rows.append({
                "target":  target,
                "horizon": h,
                "model":   m,
                "RMSE":    np.sqrt((err**2).mean()),
                "MAE":     err.abs().mean(),
            })
    return pd.DataFrame(rows)

if __name__ == "__main__":
    print("Loading data …")
    df = load()
    print(f"Data: {df.index[0].date()} – {df.index[-1].date()}, n={len(df)}")
    print(f"Feature matrix will have {len(PREDICTOR_COLS) * (N_LAGS + 1)} columns")

    print("Running ML rolling backtest …")
    fc = rolling_backtest_ml(df)
    fc_path = os.path.join(RES, "forecasts_ml.csv")
    fc.to_csv(fc_path, index=False)
    print(f"Forecasts saved: {fc_path}")

    err = compute_errors(fc)
    err_path = os.path.join(RES, "errors_ml.csv")
    err.to_csv(err_path, index=False)
    print("\n=== ML Errors ===")
    print(err.to_string(index=False))
