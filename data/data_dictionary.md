# Data Dictionary

## Raw Series (from FRED)

| Column | FRED ID | Description | Units |
|---|---|---|---|
| cpi | CPIAUCSL | Consumer Price Index, All Urban Consumers | Index (1982-84=100) |
| core_cpi | CPILFESL | CPI ex. Food & Energy | Index (1982-84=100) |
| unrate | UNRATE | Civilian Unemployment Rate | % |
| fedfunds | FEDFUNDS | Effective Federal Funds Rate | % |
| gs10 | GS10 | 10-Year Treasury Constant Maturity Rate | % |
| tb3ms | TB3MS | 3-Month Treasury Bill Secondary Market Rate | % |
| indpro | INDPRO | Industrial Production Index | Index (2017=100) |
| payems | PAYEMS | Total Nonfarm Employees | Thousands |
| oil | DCOILWTICO | Crude Oil Prices: WTI | USD/barrel |
| sentiment | UMCSENT | U. of Michigan Consumer Sentiment | Index |
| m2 | M2SL | M2 Money Stock | Billions USD |

## Processed Features (data/processed/macro_monthly.csv)

| Column | Transformation | Role |
|---|---|---|
| infl_yoy | cpi.pct_change(12) × 100 | **Target** |
| core_infl_yoy | core_cpi.pct_change(12) × 100 | Target / predictor |
| unrate | level | **Target** / predictor |
| fedfunds | level | Predictor |
| gs10 | level | Predictor |
| tb3ms | level | Predictor |
| spread | gs10 − tb3ms | Predictor (yield curve) |
| d_indpro | indpro.pct_change() × 100 | Predictor (MoM%) |
| d_payems | payems.pct_change() × 100 | Predictor (MoM%) |
| d_oil | oil.pct_change() × 100 | Predictor (MoM%) |
| sentiment | level | Predictor |
| d_m2 | m2.pct_change() × 100 | Predictor (MoM%) |

## Sample Period

- Raw pull: 1990-01-01 – 2025-12-01
- After transformations (12-month lag for YoY): ~1991-01-01 onward
- Evaluation period: 2000-01-01 onward
- Minimum training window: 60 months
