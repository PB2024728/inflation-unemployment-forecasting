"""
Day 7 — Model diagnostics and interpretation.
- Residual analysis per model
- Feature importance for Random Forest and XGBoost
- Sub-period stability check (pre/post 2008, pre/post 2020)
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import xgboost as xgb

sns.set_theme(style="whitegrid")

PROC   = os.path.join("data", "processed", "macro_monthly.csv")
RES    = "results"
FIG    = "figures"
N_LAGS = 6

PREDICTOR_COLS = [
    "infl_yoy", "core_infl_yoy", "unrate",
    "fedfunds", "gs10", "tb3ms", "spread",
    "d_indpro", "d_payems", "d_oil", "sentiment", "d_m2",
]

def load_master():
    fc = pd.read_csv(os.path.join(RES, "master_forecasts.csv"), parse_dates=["date"])
    err = pd.read_csv(os.path.join(RES, "master_errors.csv"))
    return fc, err

def plot_residuals(fc, target="infl_yoy", h=1):
    sub = fc[(fc["target"] == target) & (fc["horizon"] == h)].copy()
    models = ["naive", "arima", "var", "ridge", "lasso", "rf", "xgb"]
    models = [m for m in models if m in sub.columns]

    fig, axes = plt.subplots(len(models), 1, figsize=(12, 2.5 * len(models)), sharex=True)
    for ax, m in zip(axes, models):
        res = sub["actual"] - sub[m]
        ax.plot(sub["date"], res, linewidth=0.8, label=f"{m} residuals")
        ax.axhline(0, color="red", linewidth=0.6, linestyle="--")
        ax.set_title(f"{m.upper()}  (RMSE={np.sqrt((res**2).mean()):.4f})")
        ax.set_ylabel("Error")
    fig.suptitle(f"Residuals — {target}, h={h}", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fname = os.path.join(FIG, f"residuals_{target}_h{h}.png")
    fig.savefig(fname, dpi=150)
    plt.close()
    print(f"Saved {fname}")

def plot_feature_importance(df, target="infl_yoy", h=1):
    # Build lag features inline
    frames = [df[PREDICTOR_COLS]]
    for lag in range(1, N_LAGS + 1):
        lagged = df[PREDICTOR_COLS].shift(lag)
        lagged.columns = [f"{c}_lag{lag}" for c in PREDICTOR_COLS]
        frames.append(lagged)
    feat = pd.concat(frames, axis=1).dropna()

    target_series = df[target]
    X_rows = feat
    y_dates = X_rows.index.shift(h, freq="MS")
    valid_mask = y_dates.isin(target_series.index)
    X_fit = X_rows[valid_mask]
    y_fit = target_series[y_dates[valid_mask]].values

    rf = RandomForestRegressor(n_estimators=300, max_depth=6, random_state=42, n_jobs=-1)
    rf.fit(X_fit, y_fit)
    xg = xgb.XGBRegressor(n_estimators=300, max_depth=4, learning_rate=0.05,
                           subsample=0.8, colsample_bytree=0.8, random_state=42, verbosity=0)
    xg.fit(X_fit, y_fit)

    fi_rf  = pd.Series(rf.feature_importances_,  index=X_fit.columns).nlargest(20)
    fi_xgb = pd.Series(xg.feature_importances_, index=X_fit.columns).nlargest(20)

    # Save CSVs for dashboard consumption
    fi_rf_df = fi_rf.reset_index()
    fi_rf_df.columns = ["feature", "importance"]
    fi_rf_df["model"] = "rf"
    fi_rf_df["target"] = target
    fi_rf_df["horizon"] = h

    fi_xgb_df = fi_xgb.reset_index()
    fi_xgb_df.columns = ["feature", "importance"]
    fi_xgb_df["model"] = "xgb"
    fi_xgb_df["target"] = target
    fi_xgb_df["horizon"] = h

    combined = pd.concat([fi_rf_df, fi_xgb_df])
    csv_fname = os.path.join(RES, f"feature_importance_{target}_h{h}.csv")
    combined.to_csv(csv_fname, index=False)

    fig, axes = plt.subplots(1, 2, figsize=(14, 7))
    fi_rf.sort_values().plot(kind="barh", ax=axes[0], color="steelblue")
    axes[0].set_title(f"RF Feature Importance — {target} h={h}")
    fi_xgb.sort_values().plot(kind="barh", ax=axes[1], color="coral")
    axes[1].set_title(f"XGB Feature Importance — {target} h={h}")
    fig.tight_layout()
    fname = os.path.join(FIG, f"feature_importance_{target}_h{h}.png")
    fig.savefig(fname, dpi=150)
    plt.close()
    print(f"Saved {fname} + {csv_fname}")

def sub_period_rmse(fc):
    """RMSE split by period: pre-2008, 2008-2019, 2020+."""
    def period(d):
        if d < pd.Timestamp("2008-01-01"):
            return "pre-2008"
        elif d < pd.Timestamp("2020-01-01"):
            return "2008-2019"
        else:
            return "2020+"
    fc = fc.copy()
    fc["period"] = fc["date"].apply(period)

    models = ["naive", "arima", "var", "ridge", "lasso", "rf", "xgb"]
    rows = []
    for (target, h, per), g in fc.groupby(["target", "horizon", "period"]):
        for m in models:
            if m not in g.columns:
                continue
            err = g["actual"] - g[m]
            rows.append({
                "target": target, "horizon": h, "period": per, "model": m,
                "RMSE": round(np.sqrt((err**2).mean()), 4),
                "n": len(err.dropna()),
            })
    out = pd.DataFrame(rows)
    out.to_csv(os.path.join(RES, "subperiod_errors.csv"), index=False)
    print("Sub-period RMSE table saved.")
    return out

if __name__ == "__main__":
    fc, err = load_master()
    df = pd.read_csv(PROC, index_col="date", parse_dates=True)

    print("--- Residual plots ---")
    for target in ["infl_yoy", "unrate"]:
        for h in [1, 3, 6]:
            plot_residuals(fc, target=target, h=h)

    print("\n--- Feature importance ---")
    for target in ["infl_yoy", "unrate"]:
        for h in [1, 3, 6]:
            print(f"  fitting RF + XGB for {target} h={h} …")
            plot_feature_importance(df, target=target, h=h)

    print("\n--- Sub-period RMSE ---")
    sp = sub_period_rmse(fc)
    print(sp[sp["horizon"] == 1].pivot_table(
        index="model", columns=["target", "period"], values="RMSE"
    ).round(4))
