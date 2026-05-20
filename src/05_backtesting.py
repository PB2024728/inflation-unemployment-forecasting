"""
Day 6 — Master bake-off: merge ARIMA/VAR and ML results into one table.
Outputs results/master_errors.csv and results/master_forecasts.csv.
"""

import os
import numpy as np
import pandas as pd

RES = "results"

def load_forecasts():
    fc_ts = pd.read_csv(os.path.join(RES, "forecasts_arima_var.csv"), parse_dates=["date"])
    fc_ml = pd.read_csv(os.path.join(RES, "forecasts_ml.csv"), parse_dates=["date"])

    # Merge on date / horizon / target / actual
    key = ["date", "horizon", "target", "actual"]
    fc = pd.merge(fc_ts, fc_ml, on=key, how="outer")
    fc.to_csv(os.path.join(RES, "master_forecasts.csv"), index=False)
    print(f"Master forecasts: {fc.shape}")
    return fc

def compute_master_errors(fc):
    all_models = ["naive", "arima", "var", "ridge", "lasso", "rf", "xgb"]
    rows = []
    for (target, h), g in fc.groupby(["target", "horizon"]):
        for m in all_models:
            if m not in g.columns:
                continue
            err = g["actual"] - g[m]
            n = err.dropna().shape[0]
            rows.append({
                "target":  target,
                "horizon": h,
                "model":   m,
                "n_obs":   n,
                "RMSE":    round(np.sqrt((err**2).mean()), 4),
                "MAE":     round(err.abs().mean(), 4),
            })
    return pd.DataFrame(rows)

def print_table(err):
    for target in err["target"].unique():
        print(f"\n{'='*60}")
        print(f"Target: {target}")
        print(f"{'='*60}")
        sub = err[err["target"] == target].copy()
        pivot = sub.pivot_table(index="model", columns="horizon", values="RMSE")
        pivot.columns = [f"h={c}" for c in pivot.columns]
        print(pivot.round(4).to_string())

if __name__ == "__main__":
    fc = load_forecasts()
    err = compute_master_errors(fc)
    err.to_csv(os.path.join(RES, "master_errors.csv"), index=False)
    print_table(err)
    print(f"\nMaster errors saved to {os.path.join(RES, 'master_errors.csv')}")
