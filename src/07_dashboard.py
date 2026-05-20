"""
Day 9 — Interactive Plotly dashboard (revised).
"""

import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

RES = "results"
OUT = "dashboard.html"

ALL_MODELS  = ["naive", "arima", "var", "ridge", "lasso", "rf", "xgb"]
MODEL_NAMES = {
    "naive": "Naive", "arima": "ARIMA", "var": "VAR",
    "ridge": "Ridge", "lasso": "Lasso", "rf": "Random Forest", "xgb": "XGBoost",
}
MODEL_COLORS = {
    "naive": "#aaaaaa", "arima": "#4878CF", "var":   "#2ca02c",
    "ridge": "#D65F5F", "lasso": "#9467bd", "rf":    "#e07b00", "xgb":  "#17becf",
}
TARGET_NAMES  = {"infl_yoy": "CPI Inflation (YoY %)", "unrate": "Unemployment Rate (%)"}
TARGETS       = ["infl_yoy", "unrate"]
HORIZONS      = [1, 3, 6]
PERIOD_COLORS = {"pre-2008": "#4878CF", "2008-2019": "#e07b00", "2020+": "#D65F5F"}
PERIOD_ORDER  = ["pre-2008", "2008-2019", "2020+"]

# Human-readable feature names for charts
FEATURE_LABELS = {
    "infl_yoy":       "CPI Inflation (current)",
    "core_infl_yoy":  "Core CPI Inflation (current)",
    "unrate":         "Unemployment Rate (current)",
    "fedfunds":       "Federal Funds Rate (current)",
    "gs10":           "10-Year Treasury Rate (current)",
    "tb3ms":          "3-Month T-Bill Rate (current)",
    "spread":         "Yield Spread 10Y-3M (current)",
    "d_indpro":       "Industrial Production MoM% (current)",
    "d_payems":       "Nonfarm Payrolls MoM% (current)",
    "d_oil":          "Oil Price MoM% (current)",
    "sentiment":      "Consumer Sentiment (current)",
    "d_m2":           "M2 Money Supply MoM% (current)",
}
for lag in range(1, 7):
    FEATURE_LABELS[f"infl_yoy_lag{lag}"]      = f"CPI Inflation ({lag}mo ago)"
    FEATURE_LABELS[f"core_infl_yoy_lag{lag}"] = f"Core CPI Inflation ({lag}mo ago)"
    FEATURE_LABELS[f"unrate_lag{lag}"]         = f"Unemployment Rate ({lag}mo ago)"
    FEATURE_LABELS[f"fedfunds_lag{lag}"]       = f"Federal Funds Rate ({lag}mo ago)"
    FEATURE_LABELS[f"gs10_lag{lag}"]           = f"10-Year Treasury Rate ({lag}mo ago)"
    FEATURE_LABELS[f"tb3ms_lag{lag}"]          = f"3-Month T-Bill Rate ({lag}mo ago)"
    FEATURE_LABELS[f"spread_lag{lag}"]         = f"Yield Spread 10Y-3M ({lag}mo ago)"
    FEATURE_LABELS[f"d_indpro_lag{lag}"]       = f"Industrial Production MoM% ({lag}mo ago)"
    FEATURE_LABELS[f"d_payems_lag{lag}"]       = f"Nonfarm Payrolls MoM% ({lag}mo ago)"
    FEATURE_LABELS[f"d_oil_lag{lag}"]          = f"Oil Price MoM% ({lag}mo ago)"
    FEATURE_LABELS[f"sentiment_lag{lag}"]      = f"Consumer Sentiment ({lag}mo ago)"
    FEATURE_LABELS[f"d_m2_lag{lag}"]           = f"M2 Money Supply MoM% ({lag}mo ago)"

# ── Helpers ────────────────────────────────────────────────────────────────────

def load():
    fc  = pd.read_csv(os.path.join(RES, "master_forecasts.csv"), parse_dates=["date"])
    err = pd.read_csv(os.path.join(RES, "master_errors.csv"))
    sp  = pd.read_csv(os.path.join(RES, "subperiod_errors.csv"))
    fi_frames = []
    for target in TARGETS:
        for h in HORIZONS:
            path = os.path.join(RES, f"feature_importance_{target}_h{h}.csv")
            if os.path.exists(path):
                fi_frames.append(pd.read_csv(path))
    fi = pd.concat(fi_frames) if fi_frames else pd.DataFrame()
    return fc, err, sp, fi

def _hex_to_rgba(hex_color, alpha=0.18):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

def dropdown_menu(buttons):
    """Standard dropdown style used across all panels."""
    return dict(
        buttons=buttons,
        direction="down",
        showactive=True,
        x=0.0, xanchor="left",
        y=1.0, yanchor="bottom",   # sits just above the plot, no title to clash with
        bgcolor="#e8f0fe",
        bordercolor="#2E75B6",
        borderwidth=1,
        font=dict(size=12, family="Calibri"),
        pad={"t": 4, "b": 4, "l": 8, "r": 8},
    )

def base_layout(**kwargs):
    """Common layout settings applied to every figure."""
    defaults = dict(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="Calibri", size=12),
        margin=dict(t=56, b=44, l=64, r=24),
    )
    defaults.update(kwargs)
    return defaults

# ── Panel 1: Winner scorecard ──────────────────────────────────────────────────

def make_scorecard(err):
    col_headers = [f"h = {h}" for h in HORIZONS]
    row_labels  = [TARGET_NAMES[t] for t in TARGETS]
    cell_vals, cell_colors = [], []

    for target in TARGETS:
        row_vals, row_cols = [], []
        for h in HORIZONS:
            sub = err[(err["target"] == target) & (err["horizon"] == h)]
            if sub.empty:
                row_vals.append("—"); row_cols.append("#f9f9f9"); continue
            best = sub.loc[sub["RMSE"].idxmin()]
            name = MODEL_NAMES.get(best["model"], best["model"])
            row_vals.append(f"<b>{name}</b><br><span style='font-size:11px'>RMSE {best['RMSE']:.4f}</span>")
            row_cols.append(_hex_to_rgba(MODEL_COLORS.get(best["model"], "#cccccc")))
        cell_vals.append(row_vals)
        cell_colors.append(row_cols)

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=["<b>What we are forecasting</b>"] + [f"<b>{c} ahead</b>" for c in col_headers],
            fill_color="#1F3964", font=dict(color="white", size=12),
            align="center", height=38,
        ),
        cells=dict(
            values=[
                [f"<b>{r}</b>" for r in row_labels],
                *[[cell_vals[ri][ci] for ri in range(len(TARGETS))] for ci in range(len(HORIZONS))],
            ],
            fill_color=[
                ["#f0f4fa"] * len(TARGETS),
                *[[cell_colors[ri][ci] for ri in range(len(TARGETS))] for ci in range(len(HORIZONS))],
            ],
            font=dict(size=12), align="center", height=56,
        ),
    )])
    fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=210)
    return fig

# ── Panel 2: RMSE horse race ───────────────────────────────────────────────────

def make_rmse_barchart(err):
    buttons, all_traces, trace_idx, combo_vis = [], [], 0, {}

    for target in TARGETS:
        for h in HORIZONS:
            sub = err[(err["target"] == target) & (err["horizon"] == h)].copy()
            sub = sub[sub["model"].isin(ALL_MODELS)].set_index("model").reindex(ALL_MODELS).dropna()
            vis_idx = []
            is_first = (target == TARGETS[0] and h == HORIZONS[0])
            for model in sub.index:
                rmse = sub.loc[model, "RMSE"]
                all_traces.append(go.Bar(
                    name=MODEL_NAMES.get(model, model),
                    x=[MODEL_NAMES.get(model, model)],
                    y=[rmse],
                    marker_color=MODEL_COLORS.get(model, "#888"),
                    text=[f"{rmse:.4f}"], textposition="outside",
                    visible=is_first, showlegend=False,
                ))
                vis_idx.append(trace_idx); trace_idx += 1
            combo_vis[(target, h)] = vis_idx

    total = trace_idx
    for target in TARGETS:
        for h in HORIZONS:
            vis = [False] * total
            for i in combo_vis[(target, h)]: vis[i] = True
            label = "1 month" if h == 1 else f"{h} months"
            buttons.append(dict(
                label=f"{TARGET_NAMES[target]}  |  {label} ahead",
                method="update",
                args=[{"visible": vis}, {"yaxis.title.text": "Forecast Error (RMSE)"}],
            ))

    fig = go.Figure(data=all_traces)
    fig.update_layout(
        **base_layout(height=400, margin=dict(t=56, b=44, l=64, r=24)),
        updatemenus=[dropdown_menu(buttons)],
        yaxis_title="Forecast Error (RMSE)",
        showlegend=False,
    )
    fig.update_yaxes(gridcolor="#eeeeee")
    return fig

# ── Panel 3: Actual vs Predicted ──────────────────────────────────────────────

def make_avp(fc):
    buttons, all_traces, trace_idx, combo_vis = [], [], 0, {}

    for target in TARGETS:
        for h in HORIZONS:
            sub = fc[(fc["target"] == target) & (fc["horizon"] == h)].sort_values("date")
            vis_idx = []
            is_first = (target == TARGETS[0] and h == HORIZONS[0])
            all_traces.append(go.Scatter(
                x=sub["date"], y=sub["actual"], name="Actual",
                line=dict(color="black", width=2.2), visible=is_first,
            ))
            vis_idx.append(trace_idx); trace_idx += 1
            for model in ALL_MODELS:
                if model not in sub.columns: continue
                all_traces.append(go.Scatter(
                    x=sub["date"], y=sub[model],
                    name=MODEL_NAMES.get(model, model),
                    line=dict(color=MODEL_COLORS.get(model, "#888"), width=1.2, dash="dot"),
                    opacity=0.85, visible=is_first,
                ))
                vis_idx.append(trace_idx); trace_idx += 1
            combo_vis[(target, h)] = vis_idx

    total = trace_idx
    for target in TARGETS:
        for h in HORIZONS:
            vis = [False] * total
            for i in combo_vis[(target, h)]: vis[i] = True
            label = "1 month" if h == 1 else f"{h} months"
            buttons.append(dict(
                label=f"{TARGET_NAMES[target]}  |  {label} ahead",
                method="update",
                args=[{"visible": vis}, {"yaxis.title.text": TARGET_NAMES[target]}],
            ))

    fig = go.Figure(data=all_traces)
    fig.update_layout(
        **base_layout(height=460, margin=dict(t=56, b=44, l=64, r=24)),
        updatemenus=[dropdown_menu(buttons)],
        yaxis_title=TARGET_NAMES[TARGETS[0]],
        xaxis_title="Date",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(gridcolor="#eeeeee")
    fig.update_yaxes(gridcolor="#eeeeee")
    return fig

# ── Panel 4: Sub-period RMSE ──────────────────────────────────────────────────

def make_subperiod(sp):
    buttons, all_traces, trace_idx, combo_vis = [], [], 0, {}

    for target in TARGETS:
        for h in HORIZONS:
            sub = sp[(sp["target"] == target) & (sp["horizon"] == h) & sp["model"].isin(ALL_MODELS)].copy()
            is_first = (target == TARGETS[0] and h == HORIZONS[0])
            vis_idx = []
            for period in PERIOD_ORDER:
                p_sub = sub[sub["period"] == period].set_index("model").reindex(ALL_MODELS).dropna()
                all_traces.append(go.Bar(
                    name=period,
                    x=[MODEL_NAMES.get(m, m) for m in p_sub.index],
                    y=p_sub["RMSE"].values,
                    marker_color=PERIOD_COLORS[period],
                    visible=is_first, legendgroup=period, showlegend=is_first,
                    text=[f"{v:.3f}" for v in p_sub["RMSE"].values],
                    textposition="outside",
                ))
                vis_idx.append(trace_idx); trace_idx += 1
            combo_vis[(target, h)] = vis_idx

    total = trace_idx
    for target in TARGETS:
        for h in HORIZONS:
            vis = [False] * total
            for i in combo_vis[(target, h)]: vis[i] = True
            label = "1 month" if h == 1 else f"{h} months"
            buttons.append(dict(
                label=f"{TARGET_NAMES[target]}  |  {label} ahead",
                method="update",
                args=[{"visible": vis}, {"yaxis.title.text": "Forecast Error (RMSE)"}],
            ))

    fig = go.Figure(data=all_traces)
    fig.update_layout(
        **base_layout(height=420, margin=dict(t=56, b=44, l=64, r=24)),
        updatemenus=[dropdown_menu(buttons)],
        barmode="group",
        yaxis_title="Forecast Error (RMSE)",
        legend=dict(title="<b>Time Period</b>", orientation="v"),
    )
    fig.update_yaxes(gridcolor="#eeeeee")
    return fig

# ── Panel 5: Feature importance ────────────────────────────────────────────────

def make_feature_importance(fi):
    if fi.empty:
        return go.Figure().add_annotation(text="Feature importance data not found.", showarrow=False)

    buttons, all_traces, trace_idx, combo_vis = [], [], 0, {}

    for model in ["rf", "xgb"]:
        for target in TARGETS:
            for h in HORIZONS:
                sub = fi[(fi["model"] == model) & (fi["target"] == target) & (fi["horizon"] == h)].copy()
                sub = sub.nlargest(15, "importance").sort_values("importance")
                sub["label"] = sub["feature"].map(lambda x: FEATURE_LABELS.get(x, x))
                is_first = (model == "rf" and target == TARGETS[0] and h == HORIZONS[0])
                vis_idx = []
                all_traces.append(go.Bar(
                    x=sub["importance"], y=sub["label"],
                    orientation="h",
                    marker_color=MODEL_COLORS.get(model, "#888"),
                    visible=is_first, showlegend=False,
                    hovertemplate="%{y}<br>Importance: %{x:.4f}<extra></extra>",
                ))
                vis_idx.append(trace_idx); trace_idx += 1
                combo_vis[(model, target, h)] = vis_idx

    total = trace_idx
    for model in ["rf", "xgb"]:
        for target in TARGETS:
            for h in HORIZONS:
                vis = [False] * total
                for i in combo_vis[(model, target, h)]: vis[i] = True
                label = "1 month" if h == 1 else f"{h} months"
                buttons.append(dict(
                    label=f"{MODEL_NAMES[model]}  |  {TARGET_NAMES[target]}  |  {label} ahead",
                    method="update",
                    args=[{"visible": vis}, {"xaxis.title.text": "Importance Score"}],
                ))

    fig = go.Figure(data=all_traces)
    fig.update_layout(
        **base_layout(height=460, margin=dict(t=56, b=44, l=260, r=24)),
        updatemenus=[dropdown_menu(buttons)],
        xaxis_title="Importance Score",
    )
    fig.update_xaxes(gridcolor="#eeeeee")
    return fig

# ── HTML assembly ──────────────────────────────────────────────────────────────

def fig_to_html(fig):
    return fig.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})

def build_dashboard():
    fc, err, sp, fi = load()

    f_scorecard = make_scorecard(err)
    f_rmse      = make_rmse_barchart(err)
    f_avp       = make_avp(fc)
    f_subperiod = make_subperiod(sp)
    f_fi        = make_feature_importance(fi)

    CDN = '<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Inflation &amp; Unemployment Forecasting Bake-Off</title>
{CDN}
<style>
  *, *::before, *::after {{ box-sizing: border-box; }}
  body {{
    font-family: Calibri, 'Segoe UI', Arial, sans-serif;
    background: #f0f4fa;
    margin: 0; padding: 0 0 60px 0;
    color: #333; line-height: 1.6;
  }}

  /* ── Header ── */
  .hero {{
    background: linear-gradient(135deg, #1F3964 0%, #2E75B6 100%);
    color: white;
    padding: 44px 56px 36px 56px;
  }}
  .hero h1 {{ margin: 0 0 6px 0; font-size: 28px; font-weight: bold; letter-spacing: 0.4px; }}
  .hero .subtitle {{ font-size: 15px; opacity: 0.88; margin: 0 0 14px 0; }}
  .badges {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; }}
  .badge {{
    background: rgba(255,255,255,0.18); border-radius: 20px;
    padding: 3px 14px; font-size: 12px; letter-spacing: 0.3px;
  }}

  /* ── Layout ── */
  .container {{ max-width: 1180px; margin: 0 auto; padding: 0 32px; }}

  /* ── Intro section ── */
  .intro {{
    background: white; border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.07);
    padding: 32px 36px; margin: 32px 0 24px 0;
  }}
  .intro h2 {{ color: #1F3964; font-size: 18px; margin: 0 0 12px 0; }}
  .intro p  {{ color: #444; font-size: 14px; margin: 0 0 10px 0; }}
  .intro-grid {{
    display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-top: 20px;
  }}
  .intro-card {{
    background: #f5f8ff; border-left: 4px solid #2E75B6;
    border-radius: 0 8px 8px 0; padding: 14px 18px;
  }}
  .intro-card h4 {{ color: #1F3964; font-size: 13px; margin: 0 0 6px 0; text-transform: uppercase; letter-spacing: 0.8px; }}
  .intro-card p  {{ color: #555; font-size: 13px; margin: 0; }}

  /* ── Glossary ── */
  .glossary {{
    background: white; border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.07);
    padding: 28px 36px; margin-bottom: 24px;
  }}
  .glossary h2 {{ color: #1F3964; font-size: 18px; margin: 0 0 6px 0; }}
  .glossary .note {{ color: #888; font-size: 13px; margin: 0 0 20px 0; font-style: italic; }}
  .gloss-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }}
  .gloss-group h4 {{
    color: #2E75B6; font-size: 12px; text-transform: uppercase;
    letter-spacing: 0.8px; margin: 0 0 10px 0; padding-bottom: 6px;
    border-bottom: 2px solid #e0e8f8;
  }}
  .gloss-item {{ margin-bottom: 10px; }}
  .gloss-term {{ font-weight: bold; color: #1F3964; font-size: 13px; }}
  .gloss-def  {{ color: #555; font-size: 12.5px; margin: 1px 0 0 0; }}
  .model-dot {{
    display: inline-block; width: 10px; height: 10px;
    border-radius: 50%; margin-right: 5px; vertical-align: middle;
  }}

  /* ── Panels ── */
  .panel {{
    background: white; border-radius: 10px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.07);
    padding: 24px 28px 20px 28px; margin-bottom: 28px;
  }}
  .panel-header {{
    display: flex; align-items: baseline; gap: 12px; margin-bottom: 6px;
  }}
  .panel-num {{
    background: #1F3964; color: white; font-size: 11px;
    font-weight: bold; padding: 2px 9px; border-radius: 12px; flex-shrink: 0;
  }}
  .panel-title {{ color: #1F3964; font-size: 17px; font-weight: bold; margin: 0; }}
  .panel-desc {{
    font-size: 13.5px; color: #555; margin: 0 0 4px 0; line-height: 1.65;
  }}
  .how-to {{
    background: #fffbf0; border-left: 4px solid #e07b00;
    border-radius: 0 6px 6px 0; padding: 9px 14px;
    font-size: 13px; color: #7a4800; margin: 8px 0 6px 0;
  }}
  .how-to b {{ color: #5a3300; }}
  .finding {{
    background: #f0f6ff; border-left: 4px solid #2E75B6;
    border-radius: 0 6px 6px 0; padding: 9px 14px;
    font-size: 13px; color: #1a3560; margin-top: 8px; line-height: 1.65;
  }}
  .finding b {{ color: #1F3964; }}

  /* ── Dropdown label ── */
  .dropdown-label {{
    font-size: 12px; color: #2E75B6; font-weight: bold;
    text-transform: uppercase; letter-spacing: 0.6px;
    margin: 14px 0 2px 0;
  }}

  /* ── Responsive ── */
  @media (max-width: 860px) {{
    .intro-grid, .gloss-grid {{ grid-template-columns: 1fr; }}
    .hero {{ padding: 28px 20px; }}
    .container {{ padding: 0 14px; }}
    .panel {{ padding: 18px 16px; }}
  }}
</style>
</head>
<body>

<!-- ═══════════════════════ HERO ═══════════════════════ -->
<div class="hero">
  <h1>Inflation &amp; Unemployment Forecasting Bake-Off</h1>
  <p class="subtitle">A head-to-head comparison of traditional econometric models vs modern machine learning methods</p>
  <div class="badges">
    <span class="badge">Monthly U.S. data · 1991–2026</span>
    <span class="badge">Expanding-window backtest · Jan 2000 → Feb 2026</span>
    <span class="badge">2 targets · 3 forecast horizons · 7 models · 1,864 forecasts</span>
  </div>
</div>

<div class="container">

<!-- ═══════════════════════ INTRODUCTION ═══════════════════════ -->
<div class="intro">
  <h2>What Is This Dashboard?</h2>
  <p>
    This dashboard presents the results of a rigorous forecasting competition. Seven prediction models
    were tested on their ability to forecast two critical U.S. economic indicators —
    <strong>inflation</strong> and the <strong>unemployment rate</strong> — at three different time
    horizons: 1 month, 3 months, and 6 months into the future.
  </p>
  <p>
    The competition pits <strong>traditional econometric models</strong> (tools economists have used for
    decades) against <strong>machine learning models</strong> (modern, data-driven approaches). The goal
    is not just to find the most accurate model, but to understand <em>when</em> and <em>why</em> each
    method succeeds or fails — and what that tells us about the nature of macroeconomic forecasting.
  </p>
  <p>
    Every model was tested under a strict <strong>no-cheating rule</strong>: at each point in time,
    models could only use data that would have actually been available on that date. This ensures the
    results reflect genuine predictive skill, not hindsight. The evaluation covers over 300 monthly
    forecast rounds spanning January 2000 to February 2026.
  </p>
  <div class="intro-grid">
    <div class="intro-card">
      <h4>What we are forecasting</h4>
      <p>
        <strong>CPI Inflation (YoY %)</strong> — how much prices have risen over the past 12 months,
        expressed as a percentage. This is the number the Federal Reserve targets to keep near 2%.<br><br>
        <strong>Unemployment Rate (%)</strong> — the percentage of people in the labour force who are
        actively looking for work but cannot find a job.
      </p>
    </div>
    <div class="intro-card">
      <h4>How accuracy is measured</h4>
      <p>
        We use <strong>RMSE (Root Mean Squared Error)</strong> — think of it as the average distance
        between a model's forecast and what actually happened. <strong>Lower RMSE = more accurate.</strong>
        Larger errors are penalised more heavily than small ones, so a model that is occasionally
        wildly wrong will score much worse than one that is consistently close.
      </p>
    </div>
    <div class="intro-card">
      <h4>How to use this dashboard</h4>
      <p>
        Each section below has a <strong>dropdown menu</strong> at the top of the chart — use it to
        switch between targets (inflation vs unemployment) and forecast horizons (1, 3, or 6 months
        ahead). In the time series chart, click model names in the legend to show or hide individual
        forecasts. Hover over any chart element for exact values.
      </p>
    </div>
    <div class="intro-card">
      <h4>The headline result</h4>
      <p>
        <strong>XGBoost wins 5 of 6 categories.</strong> Lasso wins the remaining one (short-horizon
        inflation). Traditional models (ARIMA, VAR) are never the outright winner. The biggest story
        is the 2020 COVID shock — tree-based models handled it far better than every other approach,
        while traditional models and linear ML methods produced catastrophically large errors.
      </p>
    </div>
  </div>
</div>

<!-- ═══════════════════════ GLOSSARY ═══════════════════════ -->
<div class="glossary">
  <h2>Glossary — What Does Everything Mean?</h2>
  <p class="note">Expand your understanding before diving into the charts. Every term used in this dashboard is explained below.</p>
  <div class="gloss-grid">

    <div class="gloss-group">
      <h4>The Models</h4>
      <div class="gloss-item">
        <p class="gloss-term"><span class="model-dot" style="background:#aaaaaa"></span>Naive</p>
        <p class="gloss-def">Predicts that next month's value will equal this month's. No maths at all — just copy the last reading. Harder to beat than it sounds.</p>
      </div>
      <div class="gloss-item">
        <p class="gloss-term"><span class="model-dot" style="background:#4878CF"></span>ARIMA</p>
        <p class="gloss-def">A classic statistical model that finds repeating patterns in a single series (e.g. inflation's own history). Used by central banks for decades.</p>
      </div>
      <div class="gloss-item">
        <p class="gloss-term"><span class="model-dot" style="background:#2ca02c"></span>VAR</p>
        <p class="gloss-def">Like ARIMA, but models inflation and unemployment jointly — because each influences the other. Captures cross-variable dynamics.</p>
      </div>
      <div class="gloss-item">
        <p class="gloss-term"><span class="model-dot" style="background:#D65F5F"></span>Ridge</p>
        <p class="gloss-def">A machine learning model that uses all 84 economic inputs at once, gently shrinking weaker ones so they do not dominate. Keeps everything.</p>
      </div>
      <div class="gloss-item">
        <p class="gloss-term"><span class="model-dot" style="background:#9467bd"></span>Lasso</p>
        <p class="gloss-def">Like Ridge, but more decisive — it completely switches off predictors it considers unhelpful, focusing on the most informative signals only.</p>
      </div>
      <div class="gloss-item">
        <p class="gloss-term"><span class="model-dot" style="background:#e07b00"></span>Random Forest</p>
        <p class="gloss-def">Runs 100 separate decision trees on different slices of the data and averages the results. Robust to extreme events like COVID.</p>
      </div>
      <div class="gloss-item">
        <p class="gloss-term"><span class="model-dot" style="background:#17becf"></span>XGBoost</p>
        <p class="gloss-def">Builds 150 decision trees in sequence, each learning from the mistakes of the last. The gold standard in modern applied forecasting competitions.</p>
      </div>
    </div>

    <div class="gloss-group">
      <h4>The Economic Variables</h4>
      <div class="gloss-item">
        <p class="gloss-term">CPI Inflation (YoY %)</p>
        <p class="gloss-def">How much more expensive a basket of everyday goods is compared to 12 months ago. The Fed's primary inflation measure, targeting ~2%.</p>
      </div>
      <div class="gloss-item">
        <p class="gloss-term">Core CPI Inflation</p>
        <p class="gloss-def">Same as CPI but with food and energy removed. Because oil and grocery prices swing wildly, core CPI better reflects underlying inflation trends.</p>
      </div>
      <div class="gloss-item">
        <p class="gloss-term">Unemployment Rate</p>
        <p class="gloss-def">Percentage of people actively looking for work who cannot find a job. Ranged from 3.4% (tight labour market) to 14.8% (COVID shock, April 2020).</p>
      </div>
      <div class="gloss-item">
        <p class="gloss-term">Federal Funds Rate</p>
        <p class="gloss-def">The interest rate the Federal Reserve sets for overnight bank lending. Raising it slows the economy and fights inflation; cutting it stimulates growth.</p>
      </div>
      <div class="gloss-item">
        <p class="gloss-term">10-Year Treasury Rate</p>
        <p class="gloss-def">The interest rate on a 10-year U.S. government bond. Reflects long-run growth and inflation expectations built into financial markets.</p>
      </div>
      <div class="gloss-item">
        <p class="gloss-term">Yield Spread (10Y – 3M)</p>
        <p class="gloss-def">The gap between long-term and short-term interest rates. When it turns negative (inverted), it has historically preceded recessions by 12–18 months.</p>
      </div>
      <div class="gloss-item">
        <p class="gloss-term">Industrial Production</p>
        <p class="gloss-def">How much the manufacturing, mining, and utility sectors are producing month-over-month. A direct measure of real economic activity.</p>
      </div>
      <div class="gloss-item">
        <p class="gloss-term">Nonfarm Payrolls</p>
        <p class="gloss-def">The number of paid workers in the U.S. economy (excluding farm workers). A key monthly jobs report watched closely by markets and policymakers.</p>
      </div>
      <div class="gloss-item">
        <p class="gloss-term">Oil Prices (WTI)</p>
        <p class="gloss-def">West Texas Intermediate crude oil price. A major driver of energy costs and, in turn, headline inflation. Can swing 50%+ in a single month during crises.</p>
      </div>
      <div class="gloss-item">
        <p class="gloss-term">Consumer Sentiment</p>
        <p class="gloss-def">University of Michigan survey measuring how confident Americans feel about the economy. A forward-looking indicator of spending and demand.</p>
      </div>
      <div class="gloss-item">
        <p class="gloss-term">M2 Money Supply</p>
        <p class="gloss-def">The total amount of money in the economy including cash, bank deposits, and money market funds. Rapid M2 growth can signal future inflation.</p>
      </div>
    </div>

    <div class="gloss-group">
      <h4>Key Terms &amp; Concepts</h4>
      <div class="gloss-item">
        <p class="gloss-term">RMSE (Root Mean Squared Error)</p>
        <p class="gloss-def">The main accuracy metric. It measures the average size of a model's forecast errors, penalising large mistakes more than small ones. Lower = better.</p>
      </div>
      <div class="gloss-item">
        <p class="gloss-term">Forecast Horizon (h)</p>
        <p class="gloss-def">How far ahead we are predicting. h=1 means 1 month ahead; h=3 means 3 months; h=6 means 6 months. Accuracy typically falls as the horizon increases.</p>
      </div>
      <div class="gloss-item">
        <p class="gloss-term">Expanding-Window Backtest</p>
        <p class="gloss-def">The testing method used throughout. Each model is retrained monthly using only past data, then asked to forecast the future. No model ever "sees" the future. 314 rounds of testing from 2000 to 2026.</p>
      </div>
      <div class="gloss-item">
        <p class="gloss-term">Feature Importance</p>
        <p class="gloss-def">A score showing which input variables the ML models weighted most heavily. Higher importance = the model relied on that variable more when making predictions.</p>
      </div>
      <div class="gloss-item">
        <p class="gloss-term">Economic Regime</p>
        <p class="gloss-def">A distinct period with different economic conditions. We split results into: Pre-2008 (stable growth), 2008–2019 (financial crisis recovery), and 2020+ (COVID shock and inflation surge).</p>
      </div>
      <div class="gloss-item">
        <p class="gloss-term">Structural Shock</p>
        <p class="gloss-def">A sudden, large, unexpected change that breaks historical patterns — like COVID pushing unemployment from 3.5% to 14.8% in a single month. The hardest events for any model to forecast.</p>
      </div>
      <div class="gloss-item">
        <p class="gloss-term">YoY (Year-over-Year)</p>
        <p class="gloss-def">Comparing this month's value to the same month 12 months ago, expressed as a percentage change. Removes seasonal patterns and shows the true trend.</p>
      </div>
      <div class="gloss-item">
        <p class="gloss-term">MoM (Month-over-Month)</p>
        <p class="gloss-def">Comparing this month's value to last month's, expressed as a percentage change. More reactive and noisier than YoY, but captures turning points faster.</p>
      </div>
    </div>

  </div>
</div>

<!-- ═══════════════════════ PANEL 1 ═══════════════════════ -->
<div class="panel">
  <div class="panel-header">
    <span class="panel-num">01</span>
    <h3 class="panel-title">Winner Scorecard</h3>
  </div>
  <p class="panel-desc">
    This table shows the single best-performing model for each combination of what is being forecast
    (inflation or unemployment) and how far ahead (1, 3, or 6 months). "Best" means the lowest RMSE —
    the smallest average forecast error — measured across all 314 monthly evaluation rounds from 2000 to 2026.
    The colour of each cell matches the winning model's colour used throughout this dashboard.
  </p>
  <div class="how-to">
    <b>How to read it:</b> Each cell names the winning model and shows its RMSE score in smaller text.
    A lower RMSE means the model's forecasts were closer to reality. The cells are colour-coded to the
    model — so you can instantly see which model family dominates.
  </div>
  {fig_to_html(f_scorecard)}
  <div class="finding">
    <b>Key result:</b> XGBoost (teal) wins 5 of 6 categories. Lasso (purple) wins short-horizon inflation,
    where its ability to focus on a tight set of signals beats more complex approaches. No traditional
    econometric model (ARIMA or VAR) is the outright winner in any category.
  </div>
</div>

<!-- ═══════════════════════ PANEL 2 ═══════════════════════ -->
<div class="panel">
  <div class="panel-header">
    <span class="panel-num">02</span>
    <h3 class="panel-title">RMSE Horse Race</h3>
  </div>
  <p class="panel-desc">
    This bar chart shows the forecast accuracy (RMSE) of all seven models side by side for any
    target and horizon you choose. Use the dropdown menu to switch between combinations.
    <strong>Shorter bars = more accurate forecasts.</strong> The Naive model (grey) is the baseline —
    it simply predicts no change from last month. Every other model needs to beat it to justify its complexity.
  </p>
  <div class="how-to">
    <b>How to use it:</b> Select a target and horizon from the dropdown, then compare the bar heights.
    Notice how the gap between models changes as you switch from h=1 (1 month ahead) to h=6 (6 months ahead).
    The Naive bar is a useful reference — any model taller than Naive is worse than doing nothing.
  </div>
  <p class="dropdown-label">&#9660; Select target &amp; horizon</p>
  {fig_to_html(f_rmse)}
  <div class="finding">
    <b>Key finding:</b> Traditional models (ARIMA, VAR) are never the shortest bar in any combination.
    However, ARIMA is still competitive at 1-month inflation — only Lasso and XGBoost clearly beat it.
    For unemployment at every horizon, ARIMA and VAR are actually much taller than the Naive bar,
    meaning they are actively worse than doing nothing. Ridge and Lasso also fail badly for unemployment.
  </div>
</div>

<!-- ═══════════════════════ PANEL 3 ═══════════════════════ -->
<div class="panel">
  <div class="panel-header">
    <span class="panel-num">03</span>
    <h3 class="panel-title">Actual vs Predicted</h3>
  </div>
  <p class="panel-desc">
    This time series chart shows the real (actual) values of inflation or unemployment as a solid black line,
    alongside each model's forecasts shown as dotted coloured lines. This allows you to see not just
    <em>how accurate</em> each model was on average, but <em>when</em> and <em>how</em> they failed —
    which is often the most informative part of any forecast comparison.
  </p>
  <div class="how-to">
    <b>How to use it:</b> Select a target and horizon from the dropdown. Click on any model name in the legend
    to hide or show that model's forecasts — useful for isolating a specific comparison.
    Use your scroll wheel or click-and-drag on the chart to zoom into specific time periods.
    Try zooming into <strong>2020</strong> (COVID shock) or <strong>2022</strong> (inflation surge) to
    see how dramatically models diverged from reality during those events.
  </div>
  <p class="dropdown-label">&#9660; Select target &amp; horizon</p>
  {fig_to_html(f_avp)}
  <div class="finding">
    <b>What to look for:</b> Around April 2020, unemployment spiked from 3.5% to 14.8% then quickly
    recovered. Zoom in on unemployment forecasts to see how ARIMA, Ridge, and Lasso diverged wildly
    from reality, while XGBoost and Random Forest tracked the shock and recovery much more closely.
    For inflation, zoom into 2021–2023 to see how all models struggled with the post-pandemic surge —
    though XGBoost recovered its accuracy faster than the others.
  </div>
</div>

<!-- ═══════════════════════ PANEL 4 ═══════════════════════ -->
<div class="panel">
  <div class="panel-header">
    <span class="panel-num">04</span>
    <h3 class="panel-title">Performance by Economic Regime</h3>
  </div>
  <p class="panel-desc">
    A model that looks accurate on average can hide the fact that it performs brilliantly in normal times
    but catastrophically during crises — or vice versa. This chart breaks RMSE into three distinct
    historical periods, each with very different economic conditions, so you can see which models are
    genuinely reliable across regimes and which ones only look good during calm periods.
  </p>
  <p class="panel-desc">
    <strong>Pre-2008</strong> — stable growth, low and steady inflation, gradual employment changes.<br>
    <strong>2008–2019</strong> — financial crisis, zero-interest-rate policy, slow recovery with low inflation.<br>
    <strong>2020+</strong> — COVID shock (unemployment spike), post-pandemic inflation surge to 9%, aggressive Fed rate hikes.
  </p>
  <div class="how-to">
    <b>How to use it:</b> Each cluster of bars represents one model. Within each cluster, the three bars
    show that model's accuracy in each of the three time periods (blue = pre-2008, orange = 2008–2019,
    red = 2020+). A model with consistent bar heights across all three periods is stable. A model with
    a very tall red bar performs well in normal times but breaks down under stress.
  </div>
  <p class="dropdown-label">&#9660; Select target &amp; horizon</p>
  {fig_to_html(f_subperiod)}
  <div class="finding">
    <b>Key finding:</b> XGBoost is the <em>only</em> model with competitive red bars (2020+) for
    unemployment. Every other model — including Lasso and Ridge — has a red bar that dwarfs the others,
    meaning they collapsed completely during the COVID shock. For inflation, Lasso (purple) has the
    smallest blue and orange bars (best pre-2020 accuracy) but its red bar grows significantly —
    showing it degrades under extreme conditions. ARIMA, interestingly, performs <em>better</em> during
    2020+ for inflation than in earlier periods.
  </div>
</div>

<!-- ═══════════════════════ PANEL 5 ═══════════════════════ -->
<div class="panel">
  <div class="panel-header">
    <span class="panel-num">05</span>
    <h3 class="panel-title">Feature Importance — What Are the Models Paying Attention To?</h3>
  </div>
  <p class="panel-desc">
    The machine learning models were each given 84 input variables to work with — the current value
    and 6 monthly lags of all 12 economic series (e.g. "Unemployment Rate 3 months ago", "Oil Price
    last month", etc.). This chart shows which of those 84 inputs each model weighted most heavily
    when making its forecasts. A higher importance score means the model relied on that input more.
  </p>
  <p class="panel-desc">
    This is important for two reasons: it tells us <em>what economic signals actually drive forecasts</em>,
    and it reveals a key difference between how Random Forest and XGBoost use their information.
  </p>
  <div class="how-to">
    <b>How to use it:</b> Select a model (Random Forest or XGBoost), a target, and a horizon from the
    dropdown. The bars show the top 15 most important inputs, with the most important at the bottom.
    Compare Random Forest vs XGBoost on the same target and horizon to see how differently they
    use the available data — this is one of the most revealing comparisons in the project.
  </div>
  <p class="dropdown-label">&#9660; Select model, target &amp; horizon</p>
  {fig_to_html(f_fi)}
  <div class="finding">
    <b>Key finding:</b> Random Forest concentrates most of its weight on the <em>current level</em>
    of the variable being forecast — it is essentially a sophisticated version of "next month will look
    like this month." XGBoost, by contrast, spreads importance across many lagged variables, genuinely
    learning that financial conditions <em>several months ago</em> predict what happens today.
    The <strong>10-Year Treasury Rate</strong> and <strong>Yield Spread</strong> appear consistently
    across both models and all horizons — confirming decades of economic research showing that financial
    market signals are leading indicators of real economic activity.
  </div>
</div>

</div><!-- end .container -->
</body>
</html>"""

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Dashboard saved: {OUT}")

if __name__ == "__main__":
    build_dashboard()
