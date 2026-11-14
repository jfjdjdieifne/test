"""
Energy Field — حقل الطاقة
دمج كل الإشارات في فضاء احتمالي مستمر

NO FIXED THRESHOLDS
NO HARD VETOES
NO BINARY CONDITIONS

كل ضعف = وزن أقل (مش رفض)
فقط safety rails غير قابلة للتفاوض
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class EnergySnapshot:
    bar_idx: int
    timestamp: object
    signals: Dict[str, float]
    
    long_pressure: float      # [0, 0.85]
    sell_pressure: float      # [0, 0.85]
    net_pressure: float       # [-1, +1]
    conviction: float         # [0, 0.85]
    
    absorption_buy: float
    absorption_sell: float
    aggression_buy: float
    aggression_sell: float
    institutional_lean: float
    trap_score: float
    
    long_probability: float   # [0.10, 0.80]
    expected_payoff_r: float
    suggested_size_mult: float


class EnergyField:
    """
    حقل الطاقة التكيفي
    يدمج CVD + Microstructure + Price Structure
    """
    
    def __init__(self, vbars_df: pd.DataFrame, cvd_analyzer, micro_analyzer):
        self.df = vbars_df
        self.cvd = cvd_analyzer
        self.micro = micro_analyzer
        self.n = len(vbars_df)
        
        self._compute_price_structure()
        
        # Weights for online learning
        self.weights = self._init_weights()
        self.outcomes: List[Tuple[Dict, float]] = []
    
    def _init_weights(self) -> Dict[str, float]:
        return {
            "cvd_slope_fast": 0.10, "cvd_slope_med": 0.08, "cvd_divergence": 0.12,
            "cvd_absorption": 0.10, "cvd_aggression": 0.10, "cvd_effort_result": 0.08,
            "tick_velocity_z": 0.05, "ofi": 0.12, "ofi_cumulative_z": 0.08,
            "ofi_acceleration_z": 0.06, "institutional_footprint": 0.10,
            "institutional_ratio_z": 0.06, "poc_position": 0.05,
            "displacement": 0.10, "sweep_strength": 0.12,
            "close_position": 0.06, "momentum": 0.08,
        }
    
    def _compute_price_structure(self):
        """Price-derived metrics"""
        close = self.df["close"].values
        high = self.df["high"].values
        low = self.df["low"].values
        open_ = self.df["open"].values
        rng = np.maximum(high - low, 1e-12)
        
        # Close position
        self.close_pos = (close - low) / rng
        self.body_ratio = np.abs(close - open_) / rng
        
        # Displacement
        avg_range = pd.Series(rng).rolling(50, min_periods=10).mean().values
        expansion = rng / np.maximum(avg_range, 1e-12)
        
        s = pd.Series(expansion)
        m = s.rolling(100, min_periods=20).mean()
        std = s.rolling(100, min_periods=20).std()
        exp_z = ((s - m) / std.clip(lower=1e-12)).values
        exp_z = np.nan_to_num(exp_z, nan=0.0)
        
        direction = np.sign(close - open_)
        self.displacement = direction * np.clip(exp_z, 0, 3) / 3.0 * self.body_ratio
        
        # Momentum
        atr = pd.Series(rng).rolling(14, min_periods=5).mean().values
        slope = pd.Series(close).rolling(8, min_periods=4).apply(
            lambda x: np.polyfit(np.arange(len(x)), x, 1)[0] if len(x) >= 4 else 0, raw=True
        ).values
        momentum = slope / np.maximum(atr, 1e-12)
        
        s2 = pd.Series(momentum)
        m2 = s2.rolling(100, min_periods=max(5, 25)).mean()
        std2 = s2.rolling(100, min_periods=max(5, 25)).std()
        self.momentum_z = np.clip(np.nan_to_num(((s2 - m2) / std2.clip(lower=1e-12)).values, nan=0.0), -3, 3)
        
        # Sweeps
        self._detect_swings()
    
    def _detect_swings(self):
        """Swing detection + sweep strength"""
        n = self.n
        high = self.df["high"].values
        low = self.df["low"].values
        
        self.swing_highs = []
        self.swing_lows = []
        
        for k in range(2, n - 2):
            if high[k] > high[k-1] and high[k] > high[k-2] and high[k] > high[k+1] and high[k] > high[k+2]:
                self.swing_highs.append((k, float(high[k])))
            if low[k] < low[k-1] and low[k] < low[k-2] and low[k] < low[k+1] and low[k] < low[k+2]:
                self.swing_lows.append((k, float(low[k])))
        
        self.sweep_strength = np.zeros(n)
        range_vals = np.maximum(high - low, 1e-12)
        
        for i in range(5, n):
            recent_lows = [(idx, p) for idx, p in self.swing_lows if max(0, i-30) <= idx < i - 2]
            for sw_idx, sw_price in recent_lows:
                if self.df["low"].iloc[i] < sw_price and self.df["close"].iloc[i] > sw_price:
                    reclaim = (self.df["close"].iloc[i] - sw_price) / max(range_vals[i], 1e-12)
                    vol_z = self._bar_vol_z(i)
                    self.sweep_strength[i] = max(self.sweep_strength[i], reclaim * (1 + vol_z))
            
            recent_highs = [(idx, p) for idx, p in self.swing_highs if max(0, i-30) <= idx < i - 2]
            for sw_idx, sw_price in recent_highs:
                if self.df["high"].iloc[i] > sw_price and self.df["close"].iloc[i] < sw_price:
                    rej = (sw_price - self.df["close"].iloc[i]) / max(range_vals[i], 1e-12)
                    vol_z = self._bar_vol_z(i)
                    self.sweep_strength[i] = max(self.sweep_strength[i], -rej * (1 + vol_z))
    
    def _bar_vol_z(self, i: int) -> float:
        vol = self.df["volume"].values
        if i < 20:
            return 0.0
        window = vol[max(0, i-50):i]
        std = window.std()
        if std < 1e-12:
            return 0.0
        return float(np.clip((vol[i] - window.mean()) / std, -3, 3))
    
    def get_snapshot(self, i: int) -> EnergySnapshot:
        """لقطة حقل الطاقة عند البار i"""
        if i < 20 or i >= self.n:
            return self._empty(i)
        
        cvd_s = self.cvd.get_snapshot(i)
        micro_s = self.micro.get_snapshot(i)
        
        signals = {
            "cvd_slope_fast": np.clip(cvd_s["cvd_slope_fast"], -3, 3) / 3.0,
            "cvd_slope_med": np.clip(cvd_s["cvd_slope_med"], -3, 3) / 3.0,
            "cvd_divergence": cvd_s["divergence"],
            "cvd_absorption": cvd_s["absorption"],
            "cvd_aggression": cvd_s["aggression"],
            "cvd_effort_result": np.clip(cvd_s["effort_result_ratio"] - 1.0, -2, 2) / 2.0,
            "tick_velocity_z": np.clip(micro_s["tick_velocity_z"], -3, 3) / 3.0,
            "ofi": micro_s["ofi"],
            "ofi_cumulative_z": np.clip(micro_s["ofi_cumulative_z"], -3, 3) / 3.0,
            "ofi_acceleration_z": np.clip(micro_s["ofi_acceleration_z"], -3, 3) / 3.0,
            "institutional_footprint": micro_s["institutional_footprint"],
            "institutional_ratio_z": np.clip(micro_s["institutional_ratio_z"], -3, 3) / 3.0,
            "poc_position": micro_s["poc_position"] - 0.5,
            "displacement": self.displacement[i],
            "sweep_strength": np.clip(self.sweep_strength[i], -2, 2) / 2.0,
            "close_position": self.close_pos[i] - 0.5,
            "momentum": self.momentum_z[i] / 3.0,
        }
        
        # Long pressure
        long_w = {
            "cvd_aggression": 0.20, "ofi": 0.20, "ofi_cumulative_z": 0.12,
            "ofi_acceleration_z": 0.08, "institutional_footprint": 0.15,
            "displacement": 0.10, "sweep_strength": 0.15, "cvd_divergence": 0.10,
            "momentum": 0.10, "close_position": 0.05,
        }
        sell_w = dict(long_w)
        
        long_pressure = sum(long_w[k] * max(0, signals[k]) for k in long_w)
        sell_pressure = sum(sell_w[k] * max(0, -signals[k]) for k in sell_w)
        
        # TUNED: cap at 0.85
        long_pressure = np.clip(long_pressure * 1.5, 0, 0.85)
        sell_pressure = np.clip(sell_pressure * 1.5, 0, 0.85)
        
        net_pressure = long_pressure - sell_pressure
        
        # Absorption
        abs_buy = signals["cvd_absorption"] * max(0, signals["ofi"]) if signals["ofi"] > 0 else 0
        abs_sell = signals["cvd_absorption"] * max(0, -signals["ofi"]) if signals["ofi"] < 0 else 0
        
        # Aggression
        agg_buy = max(0, signals["cvd_aggression"])
        agg_sell = max(0, -signals["cvd_aggression"])
        
        # Institutional lean
        inst_lean = 0.5 * signals["institutional_footprint"] + 0.5 * signals["ofi"]
        inst_lean = np.clip(inst_lean, -1, 1)
        
        # Trap score
        trap_score = (
            0.30 * signals["cvd_absorption"] +
            0.25 * (1.0 - abs(signals["displacement"])) +
            0.25 * abs(signals["cvd_divergence"]) +
            0.20 * (1.0 - abs(signals["ofi"]))
        )
        trap_score = np.clip(trap_score, 0, 1)
        
        # TUNED: conviction penalized by trap score, capped at 0.85
        conviction = np.clip(abs(net_pressure) * (1.0 - trap_score * 0.5), 0, 0.85)
        
        # TUNED: probability — MORE SENSITIVE to net pressure
        # Increased multiplier from 0.3 to 0.5 for better signal detection
        long_prob = 0.5 + 0.5 * net_pressure * conviction
        long_prob = np.clip(long_prob, 0.10, 0.90)  # Extended range to 0.90
        
        expected_payoff = abs(net_pressure) * 3.0
        size_mult = np.clip(conviction * 1.5, 0, 2.0)
        
        return EnergySnapshot(
            bar_idx=i,
            timestamp=self.df["timestamp"].iloc[i] if "timestamp" in self.df.columns else None,
            signals=signals,
            long_pressure=long_pressure,
            sell_pressure=sell_pressure,
            net_pressure=net_pressure,
            conviction=conviction,
            absorption_buy=abs_buy,
            absorption_sell=abs_sell,
            aggression_buy=agg_buy,
            aggression_sell=agg_sell,
            institutional_lean=inst_lean,
            trap_score=trap_score,
            long_probability=long_prob,
            expected_payoff_r=expected_payoff,
            suggested_size_mult=size_mult,
        )
    
    def _empty(self, i: int) -> EnergySnapshot:
        return EnergySnapshot(
            bar_idx=i, timestamp=None, signals={},
            long_pressure=0.5, sell_pressure=0.5, net_pressure=0.0, conviction=0.0,
            absorption_buy=0.0, absorption_sell=0.0,
            aggression_buy=0.0, aggression_sell=0.0,
            institutional_lean=0.0, trap_score=0.0,
            long_probability=0.5, expected_payoff_r=0.0, suggested_size_mult=0.0,
        )
    
    def record_outcome(self, snapshot: EnergySnapshot, pnl_pct: float):
        """تسجيل نتيجة للتعلم"""
        self.outcomes.append((dict(snapshot.signals), pnl_pct))
        
        if len(self.outcomes) >= 25 and len(self.outcomes) % 10 == 0:
            self._adapt_weights()
    
    def _adapt_weights(self):
        """تعلم الأوزان"""
        if len(self.outcomes) < 25:
            return
        
        recent = self.outcomes[-100:]
        
        for sig_name in self.weights:
            sig_vals, out_vals = [], []
            for signals, outcome in recent:
                if sig_name in signals:
                    sig_vals.append(signals[sig_name])
                    out_vals.append(outcome)
            
            if len(sig_vals) < 10:
                continue
            
            sig_arr, out_arr = np.array(sig_vals), np.array(out_vals)
            
            if np.std(sig_arr) > 1e-12 and np.std(out_arr) > 1e-12:
                corr = np.corrcoef(sig_arr, out_arr)[0, 1]
                if not np.isnan(corr):
                    adj = 1.0 + 0.1 * corr
                    self.weights[sig_name] = np.clip(self.weights[sig_name] * adj, 0.01, 0.30)
        
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v / total for k, v in self.weights.items()}
