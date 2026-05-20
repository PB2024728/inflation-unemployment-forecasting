"""
Day 2 — Data collection from FRED.
Pulls all macro series, aligns to monthly frequency, and saves to data/processed/.
"""

import os
import pandas as pd
from fredapi import Fred
from dotenv import load_dotenv

load_dotenv()
FRED_KEY = os.environ["FRED_API_KEY"]
fred = Fred(api_key=FRED_KEY)

START = "1990-01-01"
END   = "2026-03-01"

# Series to pull: (fred_id, friendly_name)
SERIES = [
    ("CPIAUCSL",   "cpi"),
    ("CPILFESL",   "core_cpi"),
    ("UNRATE",     "unrate"),
    ("FEDFUNDS",   "fedfunds"),
    ("GS10",       "gs10"),
    ("TB3MS",      "tb3ms"),
    ("INDPRO",     "indpro"),
    ("PAYEMS",     "payems"),
    ("DCOILWTICO", "oil"),
    ("UMCSENT",    "sentiment"),
    ("M2SL",       "m2"),
]

def fetch_series(fred_id, name):
    print(f"  fetching {fred_id} ({name}) …")
    s = fred.get_series(fred_id, observation_start=START, observation_end=END)
    s = s.resample("MS").last()   # align to month-start
    s.name = name
    return s

def build_raw():
    frames = []
    for fid, nm in SERIES:
        frames.append(fetch_series(fid, nm))
    df = pd.concat(frames, axis=1)
    df.index.name = "date"
    raw_path = os.path.join("data", "raw", "raw_macro.csv")
    df.to_csv(raw_path)
    print(f"Raw data saved: {raw_path}  shape={df.shape}")
    return df

def build_features(df):
    out = pd.DataFrame(index=df.index)

    # --- Target: CPI inflation (YoY %) ---
    out["infl_yoy"]      = df["cpi"].pct_change(12) * 100
    out["core_infl_yoy"] = df["core_cpi"].pct_change(12) * 100

    # --- Target: unemployment level ---
    out["unrate"] = df["unrate"]

    # --- Macro predictors ---
    out["fedfunds"]  = df["fedfunds"]
    out["gs10"]      = df["gs10"]
    out["tb3ms"]     = df["tb3ms"]
    out["spread"]    = df["gs10"] - df["tb3ms"]          # yield curve
    out["d_indpro"]  = df["indpro"].pct_change() * 100   # MoM %
    out["d_payems"]  = df["payems"].pct_change() * 100
    out["d_oil"]     = df["oil"].pct_change() * 100
    out["sentiment"] = df["sentiment"]
    out["d_m2"]      = df["m2"].pct_change() * 100

    out.dropna(inplace=True)
    proc_path = os.path.join("data", "processed", "macro_monthly.csv")
    out.to_csv(proc_path)
    print(f"Processed data saved: {proc_path}  shape={out.shape}")
    return out

if __name__ == "__main__":
    raw = build_raw()
    feat = build_features(raw)
    print(feat.tail())
