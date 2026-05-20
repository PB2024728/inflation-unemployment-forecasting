"""
Day 9 — Final presentation-ready figures.
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

sns.set_theme(style="whitegrid", palette="muted", font_scale=1.1)

RES = "results"
FIG = "figures"
TARGETS  = ["infl_yoy", "unrate"]
HORIZONS = [1, 3, 6]
ALL_MODELS = ["naive", "arima", "var", "ridge", "lasso", "rf", "xgb"]
MODEL_COLORS = {
    "naive": "#aaaaaa",
    "arima": "#4878CF",
    "var":   "#6ACC65",
    "ridge": "#D65F5F",
    "lasso": "#B47CC7",
    "rf":    "#C4AD66",
    "xgb":   "#77BEDB",
}

def load():
    fc  = pd.read_csv(os.path.join(RES, "master_forecasts.csv"), parse_dates=["date"])
    err = pd.read_csv(os.path.join(RES, "master_errors.csv"))
    return fc, err

# ── Fig A: actual vs predicted (best model per horizon) ───────────────────────

def fig_actual_vs_predicted(fc, target="infl_yoy"):
    fig, axes = plt.subplots(len(HORIZONS), 1, figsize=(13, 10), sharex=True)
    sub = fc[fc["target"] == target].copy()
    for ax, h in zip(axes, HORIZONS):
        g = sub[sub["horizon"] == h].sort_values("date")
        ax.plot(g["date"], g["actual"], label="Actual", color="black", linewidth=1.2)
        for m in ALL_MODELS:
            if m in g.columns:
                ax.plot(g["date"], g[m], label=m.upper(),
                        color=MODEL_COLORS.get(m, None), alpha=0.7, linewidth=0.8)
        ax.set_title(f"h={h} month ahead")
        ax.set_ylabel(target)
        if h == HORIZONS[0]:
            ax.legend(ncol=4, fontsize=8, loc="upper left")
    fig.suptitle(f"Actual vs Predicted — {target}", fontsize=13, fontweight="bold")
    fig.tight_layout()
    fname = os.path.join(FIG, f"actual_vs_predicted_{target}.png")
    fig.savefig(fname, dpi=150)
    plt.close()
    print(f"Saved {fname}")

# ── Fig B: RMSE heatmap (model × horizon) ─────────────────────────────────────

def fig_rmse_heatmap(err, target="infl_yoy"):
    sub = err[err["target"] == target].copy()
    pivot = sub.pivot_table(index="model", columns="horizon", values="RMSE")
    pivot.columns = [f"h={c}" for c in pivot.columns]
    pivot = pivot.reindex([m for m in ALL_MODELS if m in pivot.index])

    fig, ax = plt.subplots(figsize=(7, 5))
    sns.heatmap(pivot, annot=True, fmt=".4f", cmap="YlOrRd", ax=ax,
                linewidths=0.5, cbar_kws={"label": "RMSE"})
    ax.set_title(f"RMSE by Model & Horizon — {target}")
    fig.tight_layout()
    fname = os.path.join(FIG, f"rmse_heatmap_{target}.png")
    fig.savefig(fname, dpi=150)
    plt.close()
    print(f"Saved {fname}")

# ── Fig C: bar chart — RMSE by model for each horizon ─────────────────────────

def fig_rmse_bars(err):
    fig, axes = plt.subplots(len(TARGETS), len(HORIZONS), figsize=(14, 8))
    for i, target in enumerate(TARGETS):
        for j, h in enumerate(HORIZONS):
            ax = axes[i][j]
            sub = err[(err["target"] == target) & (err["horizon"] == h)].copy()
            sub = sub[sub["model"].isin(ALL_MODELS)]
            sub["model"] = pd.Categorical(sub["model"], categories=ALL_MODELS, ordered=True)
            sub = sub.sort_values("model")
            colors = [MODEL_COLORS.get(m, "#888") for m in sub["model"]]
            ax.bar(sub["model"], sub["RMSE"], color=colors, edgecolor="white")
            ax.set_title(f"{target}\nh={h}", fontsize=9)
            ax.set_xlabel("")
            ax.tick_params(axis="x", labelsize=7, rotation=30)
            ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.3f"))
    fig.suptitle("RMSE Comparison — All Models, Targets, Horizons", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fname = os.path.join(FIG, "rmse_bar_all.png")
    fig.savefig(fname, dpi=150)
    plt.close()
    print(f"Saved {fname}")

# ── Fig D: winner grid ────────────────────────────────────────────────────────

def fig_winner_grid(err):
    rows = []
    for target in TARGETS:
        for h in HORIZONS:
            sub = err[(err["target"] == target) & (err["horizon"] == h)]
            if sub.empty:
                continue
            winner = sub.loc[sub["RMSE"].idxmin(), "model"]
            rows.append({"target": target, "horizon": h, "winner": winner})
    w = pd.DataFrame(rows)
    pivot = w.pivot(index="target", columns="horizon", values="winner")

    fig, ax = plt.subplots(figsize=(7, 3))
    ax.axis("off")
    tbl = ax.table(
        cellText=pivot.values,
        rowLabels=pivot.index,
        colLabels=[f"h={c}" for c in pivot.columns],
        loc="center",
        cellLoc="center",
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(12)
    tbl.scale(1.5, 2.2)
    ax.set_title("Best Model by Target & Horizon (lowest RMSE)", pad=20, fontsize=12)
    fig.tight_layout()
    fname = os.path.join(FIG, "winner_grid.png")
    fig.savefig(fname, dpi=150)
    plt.close()
    print(f"Saved {fname}")

if __name__ == "__main__":
    fc, err = load()
    for target in TARGETS:
        fig_actual_vs_predicted(fc, target=target)
        fig_rmse_heatmap(err, target=target)
    fig_rmse_bars(err)
    fig_winner_grid(err)
    print("\nAll final figures saved to figures/")
