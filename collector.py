"""
Binance AggTrades Collector
تحميل بيانات الصفقات الحقيقية من Binance Data Center

aggTrades = كل صفقة فردية مع:
- price: السعر
- quantity: الكمية
- is_buyer_maker: True = seller hit bid (market sell)
                  False = buyer hit ask (market buy)
"""

import os
import io
import zipfile
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional


# Binance Data Center
BASE_URL = "https://data.binance.vision/data"
DAILY_URL = f"{BASE_URL}/spot/daily/aggTrades"

# CSV columns
COLUMNS = [
    "agg_trade_id", "price", "quantity", "first_trade_id",
    "last_trade_id", "transact_time", "is_buyer_maker", "_ignore"
]

CACHE_DIR = Path.home() / ".engine_v6" / "data"


def ensure_cache():
    """Ensure cache directory exists"""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def download_daily(symbol: str, year: int, month: int, day: int, force: bool = False) -> pd.DataFrame:
    """
    تحميل aggTrades ليوم واحد من Binance
    
    Returns:
        DataFrame with columns: timestamp_us, price, quantity, is_buyer_maker
    """
    ensure_cache()
    
    filename = f"{symbol}-aggTrades-{year}-{month:02d}-{day:02d}"
    cache_path = CACHE_DIR / f"{filename}.csv"
    
    # Check cache
    if cache_path.exists() and not force:
        return pd.read_csv(cache_path)
    
    url = f"{DAILY_URL}/{symbol}/{filename}.zip"
    print(f"  Downloading: {url}")
    
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
    except Exception as e:
        print(f"  ERROR: {e}")
        return pd.DataFrame()
    
    # Extract from ZIP
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        csv_name = zf.namelist()[0]
        with zf.open(csv_name) as f:
            df = pd.read_csv(f, header=None, names=COLUMNS)
    
    if df.empty:
        return df
    
    # Keep only needed columns
    df = df[["transact_time", "price", "quantity", "is_buyer_maker"]].copy()
    df.rename(columns={"transact_time": "timestamp_us"}, inplace=True)
    df["price"] = df["price"].astype(np.float64)
    df["quantity"] = df["quantity"].astype(np.float64)
    df["is_buyer_maker"] = df["is_buyer_maker"].astype(bool)
    
    # Convert timestamp to microseconds
    median_ts = df["timestamp_us"].median()
    if median_ts < 1e14:  # milliseconds → microseconds
        df["timestamp_us"] = df["timestamp_us"] * 1000
    
    df = df.sort_values("timestamp_us").reset_index(drop=True)
    
    # Cache as CSV
    df.to_csv(cache_path, index=False)
    
    return df


def get_summary(df: pd.DataFrame) -> dict:
    """ملخص سريع للبيانات"""
    if df.empty:
        return {}
    
    ts = pd.to_datetime(df["timestamp_us"] // 1000, unit="ms")
    
    buy_mask = ~df["is_buyer_maker"]
    buy_vol = df.loc[buy_mask, "quantity"].sum()
    sell_vol = df.loc[~buy_mask, "quantity"].sum()
    total = buy_vol + sell_vol
    
    return {
        "trades": len(df),
        "start": str(ts.iloc[0]),
        "end": str(ts.iloc[-1]),
        "price_min": float(df["price"].min()),
        "price_max": float(df["price"].max()),
        "volume": float(total),
        "buy_pct": float(buy_vol / total * 100) if total > 0 else 0,
        "trades_per_sec": float(len(df) / max(1, (ts.iloc[-1] - ts.iloc[0]).total_seconds())),
    }
