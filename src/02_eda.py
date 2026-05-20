"""
Day 3 — Exploratory data analysis.
Produces 6 figures saved to figures/.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

PROC = os.path.join("data", "processed", "macro_monthly.csv")
FIG  = "figures"

sns.set_theme(style="whitegrid", palette="muted")

def load():
    df = pd.read_csv(PROC, index_col="date", parse_dates=True)
    return df

def fig1_targets(df):
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    axes[0].plot(df.index, df["infl_yoy"], label="CPI YoY %", color="steelblue")
    axes[0].plot(df.index, df["core_infl_yoy"], label="Core CPI YoY %", color="coral", linestyle="--")
    axes[0].axhline(0, color="black", linewidth=0.6)
    axes[0].set_ylabel("Inflation (%)")
    axes[0].legend()
    axes[0].set_title("Inflation (Year-over-Year)")

    axes[1].plot(df.index, df["unrate"], color="darkgreen")
    axes[1].set_ylabel("Unemployment Rate (%)")
    axes[1].set_title("Unemployment Rate")

    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig1_targets_over_time.png"), dpi=150)
    plt.close()

def fig2_correlation(df):
    corr = df.corr()
    fig, ax = plt.subplots(figsize=(11, 9))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0,
                linewidths=0.5, ax=ax)
    ax.set_title("Correlation Matrix — Monthly Macro Series")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig2_correlation_heatmap.png"), dpi=150)
    plt.close()

def fig3_rolling_stats(df):
    window = 24
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    for col, ax, title, color in [
        ("infl_yoy",  axes[0], "Inflation — Rolling Mean & Std (24m)", "steelblue"),
        ("unrate",    axes[1], "Unemployment — Rolling Mean & Std (24m)", "darkgreen"),
    ]:
        s = df[col]
        rm = s.rolling(window).mean()
        rs = s.rolling(window).std()
        ax.plot(df.index, s, alpha=0.4, color=color, label="Actual")
        ax.plot(df.index, rm, color=color, label="Rolling mean")
        ax.fill_between(df.index, rm - rs, rm + rs, alpha=0.15, color=color, label="±1 Std")
        ax.set_title(title)
        ax.legend(fontsize=8)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig3_rolling_stats.png"), dpi=150)
    plt.close()

def fig4_phillips(df):
    fig, ax = plt.subplots(figsize=(8, 6))
    sc = ax.scatter(df["unrate"], df["infl_yoy"], c=df.index.year,
                    cmap="plasma", alpha=0.6, edgecolors="none", s=20)
    plt.colorbar(sc, ax=ax, label="Year")
    ax.set_xlabel("Unemployment Rate (%)")
    ax.set_ylabel("CPI Inflation YoY (%)")
    ax.set_title("Phillips Curve — Inflation vs Unemployment")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig4_phillips_curve.png"), dpi=150)
    plt.close()

def fig5_rates(df):
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df.index, df["fedfunds"], label="Fed Funds")
    ax.plot(df.index, df["gs10"],     label="10Y Treasury")
    ax.plot(df.index, df["tb3ms"],    label="3M T-Bill")
    ax.plot(df.index, df["spread"],   label="Spread (10Y-3M)", linestyle="--")
    ax.axhline(0, color="black", linewidth=0.5)
    ax.set_title("Interest Rates and Yield Spread")
    ax.set_ylabel("%")
    ax.legend()
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig5_interest_rates.png"), dpi=150)
    plt.close()

def fig6_predictors(df):
    cols = ["d_indpro", "d_payems", "d_oil", "sentiment", "d_m2"]
    labels = ["Indus. Prod. MoM%", "Payrolls MoM%", "Oil MoM%", "Consumer Sentiment", "M2 MoM%"]
    fig, axes = plt.subplots(len(cols), 1, figsize=(12, 12), sharex=True)
    for ax, col, lbl in zip(axes, cols, labels):
        ax.plot(df.index, df[col], linewidth=0.8)
        ax.set_title(lbl)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig6_macro_predictors.png"), dpi=150)
    plt.close()

if __name__ == "__main__":
    df = load()
    print(df.describe().round(2))
    fig1_targets(df)
    fig2_correlation(df)
    fig3_rolling_stats(df)
    fig4_phillips(df)
    fig5_rates(df)
    fig6_predictors(df)
    print("EDA figures saved to figures/")
