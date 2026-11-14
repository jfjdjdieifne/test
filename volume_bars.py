"""
Dynamic Volume Bar Builder
إلغاء الشموع الزمنية — الزمن غش

كل بار = حجم متساوي (مثلاً 5 BTC)
- في الأسواق الهادية: البار يأخذ وقت أطول
- في الأسواق الصاخبة: البار يتشكل بسرعة

Reference: López de Prado (2018) — Advantages of Volume Bars
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import List


@dataclass
class VolumeBar:
    bar_id: int
    timestamp_start_us: int
    timestamp_end_us: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    trade_count: int
    buy_volume: float
    sell_volume: float
    vwap: float
    notional: float


class DynamicVolumeBarBuilder:
    """
    تحويل الصفقات إلى volume bars ديناميكية
    
    المبدأ: كل بار = target_volume من التداول
    target_volume يتكيف مع نشاط السوق (percentile)
    """
    
    def __init__(
        self,
        min_volume: float = 2.0,      # BTC minimum per bar
        max_volume: float = 100.0,     # BTC maximum per bar
        percentile: float = 50.0,      # P50 = median
    ):
        self.min_vol = min_volume
        self.max_vol = max_volume
        self.percentile = percentile
        self.target_volume = (min_volume + max_volume) / 2  # initial
    
    def process_ticks(self, trades_df: pd.DataFrame, progress_every: int = 0) -> List[VolumeBar]:
        """
        تحويل aggTrades إلى VolumeBars
        
        Args:
            trades_df: DataFrame with columns [timestamp_us, price, quantity, is_buyer_maker]
            progress_every: Print progress every N trades (0 = no progress)
        
        Returns:
            List of VolumeBar objects
        """
        if trades_df.empty:
            return []
        
        timestamps = trades_df["timestamp_us"].values
        prices = trades_df["price"].values
        quantities = trades_df["quantity"].values
        is_maker = trades_df["is_buyer_maker"].values
        n = len(trades_df)
        
        bars = []
        bar_counter = 0
        current_trades = []
        current_volume = 0.0
        
        # For adaptation
        recent_ts = []
        recent_vol = []
        adapt_window_us = 300 * 1_000_000  # 5 minutes
        
        for i in range(n):
            ts = int(timestamps[i])
            price = float(prices[i])
            qty = float(quantities[i])
            maker = bool(is_maker[i])
            
            current_trades.append({
                "timestamp_us": ts,
                "price": price,
                "quantity": qty,
                "is_buyer_maker": maker,
            })
            current_volume += qty
            
            # Track for adaptation
            recent_ts.append(ts)
            recent_vol.append(qty)
            
            # Clean old entries
            cutoff = ts - adapt_window_us
            while recent_ts and recent_ts[0] < cutoff:
                recent_ts.pop(0)
                recent_vol.pop(0)
            
            # Adapt target volume every 100 trades
            if len(current_trades) % 100 == 0:
                if len(recent_vol) > 10:
                    window_vols = {}
                    for rts, rvol in zip(recent_ts, recent_vol):
                        bucket = rts // 60_000_000  # 1-minute buckets
                        window_vols[bucket] = window_vols.get(bucket, 0.0) + rvol
                    if len(window_vols) >= 2:
                        vols_arr = np.array(list(window_vols.values()))
                        self.target_volume = float(np.clip(
                            np.percentile(vols_arr, self.percentile),
                            self.min_vol,
                            self.max_vol,
                        ))
            
            # Finalize bar if volume target reached
            if current_volume >= self.target_volume:
                bar_counter += 1
                
                bar_prices = [t["price"] for t in current_trades]
                bar_qtys = [t["quantity"] for t in current_trades]
                bar_ts = [t["timestamp_us"] for t in current_trades]
                bar_buys = [t["quantity"] for t in current_trades if not t["is_buyer_maker"]]
                bar_sells = [t["quantity"] for t in current_trades if t["is_buyer_maker"]]
                
                total_v = sum(bar_qtys)
                total_n = sum(p * q for p, q in zip(bar_prices, bar_qtys))
                
                bar = VolumeBar(
                    bar_id=bar_counter,
                    timestamp_start_us=bar_ts[0],
                    timestamp_end_us=bar_ts[-1],
                    open=bar_prices[0],
                    high=max(bar_prices),
                    low=min(bar_prices),
                    close=bar_prices[-1],
                    volume=total_v,
                    trade_count=len(current_trades),
                    buy_volume=sum(bar_buys),
                    sell_volume=sum(bar_sells),
                    vwap=total_n / total_v if total_v > 0 else bar_prices[0],
                    notional=total_n,
                )
                bars.append(bar)
                
                # Reset
                current_trades = []
                current_volume = 0.0
            
            # Progress
            if progress_every > 0 and i > 0 and i % progress_every == 0:
                print(f"    {i:,}/{n:,} trades → {len(bars)} bars")
        
        # Handle remaining trades
        if current_trades and len(current_trades) > 5:
            bar_counter += 1
            bar_prices = [t["price"] for t in current_trades]
            bar_qtys = [t["quantity"] for t in current_trades]
            bar_ts = [t["timestamp_us"] for t in current_trades]
            bar_buys = [t["quantity"] for t in current_trades if not t["is_buyer_maker"]]
            bar_sells = [t["quantity"] for t in current_trades if t["is_buyer_maker"]]
            
            total_v = sum(bar_qtys)
            total_n = sum(p * q for p, q in zip(bar_prices, bar_qtys))
            
            bar = VolumeBar(
                bar_id=bar_counter,
                timestamp_start_us=bar_ts[0],
                timestamp_end_us=bar_ts[-1],
                open=bar_prices[0],
                high=max(bar_prices),
                low=min(bar_prices),
                close=bar_prices[-1],
                volume=total_v,
                trade_count=len(current_trades),
                buy_volume=sum(bar_buys),
                sell_volume=sum(bar_sells),
                vwap=total_n / total_v if total_v > 0 else bar_prices[0],
                notional=total_n,
            )
            bars.append(bar)
        
        if progress_every >= 0:
            print(f"    Done: {len(bars)} volume bars from {n:,} trades")
        
        return bars
    
    def to_dataframe(self, bars: List[VolumeBar]) -> pd.DataFrame:
        """تحويل VolumeBars إلى DataFrame"""
        if not bars:
            return pd.DataFrame()
        
        records = []
        for b in bars:
            records.append({
                "bar_id": b.bar_id,
                "timestamp_start_us": b.timestamp_start_us,
                "timestamp_end_us": b.timestamp_end_us,
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
                "volume": b.volume,
                "trade_count": b.trade_count,
                "buy_volume": b.buy_volume,
                "sell_volume": b.sell_volume,
                "vwap": b.vwap,
                "notional": b.notional,
            })
        
        df = pd.DataFrame(records)
        df["timestamp"] = pd.to_datetime(df["timestamp_end_us"] // 1000, unit="ms")
        df["delta"] = df["buy_volume"] - df["sell_volume"]
        df["range"] = df["high"] - df["low"]
        
        return df
