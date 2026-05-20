# Inflation & Unemployment Forecasting Bake-Off

## Project Goal

Compare traditional time-series models (ARIMA, VAR) against machine learning models (Ridge, Lasso, Random Forest, XGBoost) for forecasting inflation and unemployment. The goal is not just to minimize error, but to understand *which model class performs better, under what conditions, and why*.

## Research Question

> Do traditional time-series models outperform machine learning methods in forecasting inflation and unemployment, or do ML methods gain an edge once richer predictor sets and nonlinear patterns are included?

## Targets

| Variable | Transformation |
|---|---|
| CPI inflation (headline) | YoY % change (12-month) |
| Core CPI inflation | YoY % change |
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

- Expanding-window backtesting (all data up to time t, no look-ahead)
- Metrics: RMSE, MAE, directional accuracy
- Separate tables per target variable and per forecast horizon

## Repository Structure

```
data/
  raw/          # Downloaded source files (FRED CSVs, etc.)
  processed/    # Clean merged monthly dataset

src/
  01_collect_data.py
  02_eda.py
  03_arima_var.py
  04_ml_models.py
  05_backtesting.py
  06_diagnostics.py
  07_visualizations.py

notebooks/      # Exploratory notebooks
figures/        # All output plots
results/        # Forecast outputs and error tables
```

## Data Sources

All data pulled from FRED (Federal Reserve Economic Data):

| Series | FRED ID | Transformation |
|---|---|---|
| CPI All Items | CPIAUCSL | YoY % or monthly annualized |
| Core CPI | CPILFESL | YoY % |
| Unemployment Rate | UNRATE | Level |
| Fed Funds Rate | FEDFUNDS | Level |
| 10Y Treasury | GS10 | Level |
| 3M Treasury Bill | TB3MS | Level |
| Industrial Production | INDPRO | Log difference |
| Nonfarm Payrolls | PAYEMS | Log difference |
| Oil Prices (WTI) | DCOILWTICO | Log difference |
| Consumer Sentiment | UMCSENT | Level |
| M2 Money Supply | M2SL | Log difference |
| Yield Spread (10Y-3M) | Derived | Level |

## Training / Evaluation Split

- Training start: 1990-01-01 (or earliest available)
- Evaluation window: rolling or expanding from 2000-01-01 onward
- Minimum training window: 5 years (60 months)

## Findings (to be filled in)

_TBD after backtesting is complete._

## Requirements

See `requirements.txt`.
