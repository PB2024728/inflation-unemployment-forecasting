# Inflation & Unemployment Forecasting Bake-Off

## Project Goal

Compare traditional time-series models (ARIMA, VAR) against machine learning models (Ridge, Lasso, Random Forest, XGBoost) for forecasting inflation and unemployment. The goal is not just to minimize error, but to understand *which model class performs better, under what conditions, and why*.

## Research Question

> Do traditional time-series models outperform machine learning methods in forecasting inflation and unemployment, or do ML methods gain an edge once richer predictor sets and nonlinear patterns are included?

## Targets

| Variable | Transformation |
|---|---|
| CPI inflation (headline) | YoY % change (12-month) |
| Unemployment rate | Level |

## Forecast Horizons

- h=1 (1 month ahead)
- h=3 (3 months ahead)
- h=6 (6 months ahead)

## Models

| Class | Model |
|---|---|
| Baseline | Naive (random walk) |
| Classical | ARIMA |
| Classical | VAR |
| ML | Ridge Regression |
| ML | Lasso Regression |
| ML | Random Forest |
| ML | XGBoost |

## Evaluation

- Expanding-window backtesting — all data up to time t used for training (no look-ahead bias)
- 313 evaluation rounds from 2000-01-01 onward
- Metrics: RMSE and MAE
- Sub-period analysis: pre-2008, 2008–2019, 2020+

## Repository Structure

```
data/
  processed/        # Clean merged monthly dataset (421 rows, 12 features)
  data_dictionary.md

src/
  01_collect_data.py       # FRED API pull and feature engineering
  02_eda.py                # Exploratory analysis and plots
  03_arima_var.py          # ARIMA and VAR expanding-window backtest
  04_ml_models.py          # Ridge, Lasso, RF, XGBoost backtest
  05_backtesting.py        # Merge all forecasts into master files
  06_diagnostics.py        # Residuals, feature importance, sub-period analysis
  07_dashboard.py          # Interactive Plotly HTML dashboard
  generate_*.py            # Word document report generators

figures/            # All output plots (EDA, residuals, feature importance)
results/            # Forecast CSVs and error tables
Debriefs/           # Project reports and final documents
dashboard.html      # Interactive results dashboard (open in any browser)
```

## Data Sources

All data pulled from FRED (Federal Reserve Economic Data), January 1990 – early 2026:

| Series | FRED ID | Transformation |
|---|---|---|
| CPI All Items | CPIAUCSL | YoY % change |
| Core CPI | CPILFESL | YoY % change |
| Unemployment Rate | UNRATE | Level |
| Fed Funds Rate | FEDFUNDS | Level |
| 10Y Treasury | GS10 | Level |
| 3M Treasury Bill | TB3MS | Level |
| Industrial Production | INDPRO | Monthly log difference |
| Nonfarm Payrolls | PAYEMS | Monthly log difference |
| Oil Prices (WTI) | DCOILWTICO | Monthly log difference |
| Consumer Sentiment | UMCSENT | Level |
| M2 Money Supply | M2SL | Monthly log difference |
| Yield Spread (10Y–3M) | Derived | Level |

The ML models used a lagged feature matrix: 6 lags of all 12 variables = 84 features total.

## Training / Evaluation Split

- Training start: 1990-01-01
- Evaluation window: expanding from 2000-01-01 onward
- Minimum training window: 60 months

## Findings

### Inflation (CPI Year-over-Year %) — RMSE by Model and Horizon

| Model | h=1 | h=3 | h=6 |
|---|---|---|---|
| Naive | 0.449 | 0.977 | 1.436 |
| ARIMA | 0.402 | 0.957 | 1.448 |
| VAR | 0.431 | 1.127 | 1.974 |
| Ridge | 0.533 | 1.424 | 1.597 |
| **Lasso** | **0.278** | 0.934 | 1.242 |
| Random Forest | 0.421 | 0.795 | 1.060 |
| **XGBoost** | 0.335 | **0.746** | **0.831** |

**Lasso won at h=1**; XGBoost dominated at h=3 and h=6 — beating ARIMA by ~42% at 6 months.

### Unemployment Rate (%) — RMSE by Model and Horizon

| Model | h=1 | h=3 | h=6 |
|---|---|---|---|
| Naive | 0.642 | 1.087 | 1.400 |
| ARIMA | 0.996 | 2.741 | 5.756 |
| VAR | 0.989 | 2.729 | 5.937 |
| Ridge | 2.211 | 2.338 | 2.665 |
| Lasso | 2.099 | 2.073 | 2.506 |
| Random Forest | 0.448 | 0.903 | 1.168 |
| **XGBoost** | **0.259** | **0.903** | **0.956** |

ARIMA's 6-month RMSE of 5.76 reflects catastrophic failure during the COVID-19 unemployment spike (3.5% → 14.7% in two months). XGBoost's error over the same period was ~0.96 — roughly 6× more accurate.

### Sub-Period Analysis (Unemployment, h=1 RMSE)

| Model | Pre-2008 | 2008–2019 | 2020+ |
|---|---|---|---|
| Naive | 0.126 | 0.178 | 1.299 |
| ARIMA | 0.129 | 0.160 | 2.135 |
| Lasso | 0.079 | **0.066** | 3.937 |
| Random Forest | 0.142 | 0.319 | 0.795 |
| **XGBoost** | **0.113** | 0.243 | **0.492** |

In calm periods (2008–2019), Lasso was actually the most accurate for unemployment. The ML tree-model advantage emerged specifically during high-volatility regimes.

### Key Findings

1. **Machine learning wins overall, but not uniformly.** The advantage is clearest at longer horizons (h=3, h=6) and during economic shocks.
2. **XGBoost was the most consistent top performer** across nearly every target and horizon combination.
3. **Lasso was the surprise winner for 1-month inflation** — automatic variable selection from 84 features paid off at close range.
4. **Classical models failed catastrophically on unemployment during COVID.** ARIMA's 6-month error reached 5.76 percentage points; XGBoost held at 0.96.
5. **The Naive benchmark is competitive for near-term unemployment** in stable regimes — unemployment moves slowly, so "no change" is genuinely hard to beat.
6. **Alpha tuning did not improve results.** Original regularization values (Ridge α=1.0, Lasso α=0.01) were already near-optimal — itself a finding about default robustness.

## Requirements

See `requirements.txt`. Key dependencies: `pandas`, `numpy`, `scikit-learn`, `xgboost`, `statsmodels`, `plotly`, `fredapi`, `python-docx`.

To reproduce: add your FRED API key to a `.env` file as `FRED_API_KEY=your_key_here`, then run scripts 01 through 07 in order.
