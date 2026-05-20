"""
Day 4 — ARIMA and VAR benchmark models.
Generates rolling-window forecasts for h=1,3,6 and saves to results/.
"""

import os
import warnings
import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.api import VAR

warnings.filterwarnings("ignore")

PROC       = os.path.join("data", "processed", "macro_monthly.csv")
RES        = "results"
TRAIN_START = "1990-01-01"
EVAL_START  = "2000-01-01"
HORIZONS    = [1, 3, 6]
TARGETS     = ["infl_yoy", "unrate"]

def load():
    df = pd.read_csv(PROC, index_col="date", parse_dates=True)
    df = df[TARGETS]
    return df

# ─── Naive forecast ───────────────────────────────────────────────────────────

def naive_forecast(series, h):
    """Last observed value repeated h steps."""
    return pd.Series([series.iloc[-1]] * h)

# ─── ARIMA ────────────────────────────────────────────────────────────────────

def _auto_arima_order(series):
    """Select ARIMA(p,d,q) by AIC over a small grid. Called once per (t, target)."""
    best_aic, best_order = np.inf, (1, 1, 1)
    for p in range(3):
        for d in range(2):
            for q in range(3):
                try:
                    m = SARIMAX(series, order=(p, d, q), trend="c",
                                enforce_stationarity=False, enforce_invertibility=False)
                    r = m.fit(disp=False)
                    if r.aic < best_aic:
                        best_aic, best_order = r.aic, (p, d, q)
                except Exception:
                    continue
    return best_order

def fit_arima(series, order):
    model = SARIMAX(series, order=order, trend="c",
                    enforce_stationarity=False, enforce_invertibility=False)
    return model.fit(disp=False)

def arima_forecast(series, h, order):
    res = fit_arima(series, order)
    return res.forecast(steps=h)

# ─── VAR ──────────────────────────────────────────────────────────────────────

def var_forecast(df_var, h, maxlags=6):
    model = VAR(df_var)
    fitted = model.fit(maxlags=maxlags, ic="aic")
    fc = fitted.forecast(df_var.values[-fitted.k_ar:], steps=h)
    return pd.DataFrame(fc, columns=df_var.columns)

# ─── Rolling-window backtester ────────────────────────────────────────────────

def rolling_backtest(df, min_train=60):
    eval_idx = df.index[df.index >= EVAL_START]
    records = []

    for t_idx, t in enumerate(eval_idx):
        train = df[df.index < t]
        if len(train) < min_train:
            continue

        actual_window = df[df.index >= t]

        # Select ARIMA order once per (t, target) — shared across all horizons
        arima_orders = {}
        for target in TARGETS:
            try:
                arima_orders[target] = _auto_arima_order(train[target])
            except Exception:
                arima_orders[target] = (1, 1, 1)

        for h in HORIZONS:
            if len(actual_window) < h:
                continue
            actual_h = actual_window.iloc[h - 1]   # value h steps ahead

            for target in TARGETS:
                s = train[target]
                act = actual_h[target]

                # Naive
                nf = naive_forecast(s, h).iloc[-1]

                # ARIMA — uses pre-selected order for this training window
                try:
                    af = arima_forecast(s, h, arima_orders[target]).iloc[-1]
                except Exception:
                    af = np.nan

                # VAR
                try:
                    vf = var_forecast(train[TARGETS], h)
                    vf_val = vf[target].iloc[-1]
                except Exception:
                    vf_val = np.nan

                records.append({
                    "date":    t,
                    "horizon": h,
                    "target":  target,
                    "actual":  act,
                    "naive":   nf,
                    "arima":   af,
                    "var":     vf_val,
                })

        if t_idx % 12 == 0:
            print(f"  backtesting at {t.date()} …")

    return pd.DataFrame(records)

def compute_errors(fc_df):
    model_cols = ["naive", "arima", "var"]
    rows = []
    for (target, h), g in fc_df.groupby(["target", "horizon"]):
        for m in model_cols:
            err = g["actual"] - g[m]
            rows.append({
                "target":  target,
                "horizon": h,
                "model":   m,
                "RMSE":    np.sqrt((err**2).mean()),
                "MAE":     err.abs().mean(),
                "dir_acc": ((np.sign(err) == 0).mean()),   # placeholder
            })
    return pd.DataFrame(rows)

if __name__ == "__main__":
    print("Loading data …")
    df = load()
    print(f"Data: {df.index[0].date()} – {df.index[-1].date()}, n={len(df)}")

    print("Running rolling backtest (ARIMA + VAR) …")
    fc = rolling_backtest(df)
    fc_path = os.path.join(RES, "forecasts_arima_var.csv")
    fc.to_csv(fc_path, index=False)
    print(f"Forecasts saved: {fc_path}")

    err = compute_errors(fc)
    err_path = os.path.join(RES, "errors_arima_var.csv")
    err.to_csv(err_path, index=False)
    print("\n=== ARIMA / VAR Errors ===")
    print(err.to_string(index=False))
