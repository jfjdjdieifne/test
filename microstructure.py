"""
Microstructure Analyzer
تحليل بنية السوق الحقيقية من tick-level

1. Tick Velocity — سرعة الصفقات (trades/sec)
2. Trade Size Segmentation — retail vs institutional
3. Order Flow Imbalance — buy/sell ratio per bar
4. Volume Clustering (POC) — وين تركز الحجم داخل كل بار
5. Institutional Footprint — أثر المؤسسات
"""

import numpy as np
import pandas as pd
from typing import Dict


class MicrostructureAnalyzer:
    """محلل البنية الميكروية — كل القيم نسبية"""
    
    def __init__(self, trades_df: pd.DataFrame, vbars_df: pd.DataFrame):
        self.trades = trades_df
        self.vbars = vbars_df
        self.n_bars = len(vbars_df)
        
        # Map trades to bars
        self._map_trades_to_bars()
        
        # Compute all metrics
        self._compute_tick_velocity()
        self._compute_trade_size_dist()
        self._compute_ofi()
        self._compute_volume_clusters()
        self._compute_institutional()
    
    def _map_trades_to_bars(self):
        """تعيين كل صفقة للبار الخاص فيها"""
        bar_starts = self.vbars["timestamp_start_us"].values
        trade_ts = self.trades["timestamp_us"].values
        bar_indices = np.searchsorted(bar_starts, trade_ts, side="right") - 1
        self.trades["bar_idx"] = np.clip(bar_indices, 0, self.n_bars - 1)
    
    def _compute_tick_velocity(self):
        """Tick velocity — trades per second per bar"""
        velocities = []
        
        for bar_id in range(self.n_bars):
            mask = self.trades["bar_idx"] == bar_id
            bar_trades = self.trades[mask]
            
            if len(bar_trades) < 2:
                velocities.append(0.0)
                continue
            
            dur_us = bar_trades["timestamp_us"].iloc[-1] - bar_trades["timestamp_us"].iloc[0]
            dur_s = max(dur_us / 1_000_000, 0.001)
            velocities.append(len(bar_trades) / dur_s)
        
        self.tick_velocity = np.array(velocities)
        
        # Z-score
        s = pd.Series(self.tick_velocity)
        m = s.rolling(50, min_periods=10).mean()
        std = s.rolling(50, min_periods=10).std()
        self.tick_velocity_z = ((s - m) / std.clip(lower=1e-12)).values
        self.tick_velocity_z = np.nan_to_num(self.tick_velocity_z, nan=0.0)
        
        # Percentile
        self.tick_velocity_pct = self._rolling_pct(self.tick_velocity, 100)
    
    def _compute_trade_size_dist(self):
        """حجم الصفقات — تجزئة retail vs institutional"""
        all_sizes = self.trades["quantity"].values
        
        self.size_p25 = np.percentile(all_sizes, 25)
        self.size_p90 = np.percentile(all_sizes, 90)
        self.size_p95 = np.percentile(all_sizes, 95)
        
        # Institutional ratio per bar
        inst_ratios = []
        retail_ratios = []
        
        for bar_id in range(self.n_bars):
            mask = self.trades["bar_idx"] == bar_id
            bar_sizes = self.trades.loc[mask, "quantity"].values
            
            if len(bar_sizes) == 0:
                inst_ratios.append(0.0)
                retail_ratios.append(0.0)
                continue
            
            total = bar_sizes.sum()
            inst_vol = bar_sizes[bar_sizes >= self.size_p90].sum()
            retail_vol = bar_sizes[bar_sizes <= self.size_p25].sum()
            
            inst_ratios.append(inst_vol / max(total, 1e-12))
            retail_ratios.append(retail_vol / max(total, 1e-12))
        
        self.institutional_ratio = np.array(inst_ratios)
        self.retail_ratio = np.array(retail_ratios)
        self.institutional_ratio_z = self._rolling_zscore(self.institutional_ratio, 50)
    
    def _compute_ofi(self):
        """Order Flow Imbalance"""
        total_vol = self.vbars["volume"].values
        delta = self.vbars["buy_volume"].values - self.vbars["sell_volume"].values
        
        self.ofi = delta / np.maximum(total_vol, 1e-12)  # [-1, +1]
        
        # Cumulative
        ofi_cum = pd.Series(self.ofi).rolling(20, min_periods=5).sum().values
        self.ofi_cumulative_z = self._rolling_zscore(ofi_cum, 100)
        
        # Acceleration
        self.ofi_acceleration = np.diff(self.ofi, prepend=self.ofi[0])
        self.ofi_acceleration_z = self._rolling_zscore(self.ofi_acceleration, 50)
    
    def _compute_volume_clusters(self):
        """POC — Point of Control (وين تركز الحجم داخل البار)"""
        poc_prices = []
        
        for bar_id in range(self.n_bars):
            mask = self.trades["bar_idx"] == bar_id
            bar_trades = self.trades[mask]
            
            if len(bar_trades) == 0:
                poc_prices.append(self.vbars["close"].iloc[bar_id])
                continue
            
            prices = bar_trades["price"].values
            qtys = bar_trades["quantity"].values
            
            bar_low = self.vbars["low"].iloc[bar_id]
            bar_high = self.vbars["high"].iloc[bar_id]
            bar_range = bar_high - bar_low
            
            if bar_range < 1e-12:
                poc_prices.append(prices[0])
                continue
            
            n_bins = min(20, max(5, int(len(bar_trades) / 10)))
            bin_edges = np.linspace(bar_low, bar_high, n_bins + 1)
            bin_volumes = np.zeros(n_bins)
            
            for price, qty in zip(prices, qtys):
                bin_idx = int((price - bar_low) / bar_range * n_bins)
                bin_idx = max(0, min(bin_idx, n_bins - 1))  # FIX: clip properly
                bin_volumes[bin_idx] += qty
            
            poc_idx = np.argmax(bin_volumes)
            poc_prices.append((bin_edges[poc_idx] + bin_edges[poc_idx + 1]) / 2)
        
        self.poc_prices = np.array(poc_prices)
        
        # POC position [0, 1]
        bar_low = self.vbars["low"].values
        bar_high = self.vbars["high"].values
        bar_range = np.maximum(bar_high - bar_low, 1e-12)
        self.poc_position = np.clip((self.poc_prices - bar_low) / bar_range, 0, 1)
        self.poc_vs_close = (self.poc_prices - self.vbars["close"].values) / bar_range
    
    def _compute_institutional(self):
        """Institutional footprint — أثر المؤسسات"""
        inst_footprint = []
        
        for bar_id in range(self.n_bars):
            mask = self.trades["bar_idx"] == bar_id
            bar_trades = self.trades[mask]
            
            if len(bar_trades) == 0:
                inst_footprint.append(0.0)
                continue
            
            sizes = bar_trades["quantity"].values
            is_maker = bar_trades["is_buyer_maker"].values
            
            large_mask = sizes >= self.size_p95
            if not large_mask.any():
                inst_footprint.append(0.0)
                continue
            
            large_sizes = sizes[large_mask]
            large_maker = is_maker[large_mask]
            
            inst_buy = large_sizes[~large_maker].sum()
            inst_sell = large_sizes[large_maker].sum()
            inst_total = large_sizes.sum()
            
            inst_footprint.append((inst_buy - inst_sell) / max(inst_total, 1e-12))
        
        self.institutional_footprint = np.array(inst_footprint)
    
    def _rolling_zscore(self, values, window):
        s = pd.Series(values)
        m = s.rolling(window, min_periods=max(5, window//4)).mean()
        std = s.rolling(window, min_periods=max(5, window//4)).std()
        z = ((s - m) / std.clip(lower=1e-12)).values
        return np.nan_to_num(z, nan=0.0)
    
    def _rolling_pct(self, values, window):
        s = pd.Series(values)
        rank = s.rolling(window, min_periods=max(5, window//4)).apply(
            lambda x: pd.Series(x).rank(pct=True).iloc[-1], raw=False
        )
        return rank.fillna(0.5).values
    
    def get_snapshot(self, i: int) -> Dict:
        """لقطة كاملة عند البار i"""
        return {
            "tick_velocity_z": float(self.tick_velocity_z[i]),
            "tick_velocity_pct": float(self.tick_velocity_pct[i]),
            "institutional_ratio": float(self.institutional_ratio[i]),
            "institutional_ratio_z": float(self.institutional_ratio_z[i]),
            "retail_ratio": float(self.retail_ratio[i]),
            "ofi": float(self.ofi[i]),
            "ofi_cumulative_z": float(self.ofi_cumulative_z[i]),
            "ofi_acceleration_z": float(self.ofi_acceleration_z[i]),
            "poc_position": float(self.poc_position[i]),
            "poc_vs_close": float(self.poc_vs_close[i]),
            "institutional_footprint": float(self.institutional_footprint[i]),
        }
