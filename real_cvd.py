"""
Real CVD Engine — Cumulative Volume Delta من كل صفقة حقيقية

is_buyer_maker=True  → seller hit bid → MARKET SELL → delta = -quantity
is_buyer_maker=False → buyer hit ask  → MARKET BUY  → delta = +quantity

يكشف:
- Absorption: جهد عالي + نتيجة صغيرة (حدود سلبية تمتص الأوامر)
- Divergence: سعر يصعد + CVD يهبط = توزيع خفي
- Aggression: CVD وصعر يتحركان بنفس القوة
- Effort vs Result: الجهد مقابل النتيجة
"""

import numpy as np
import pandas as pd
from typing import Dict


class RealCVDAnalyzer:
    """محلل CVD الحقيقي — كل القيم نسبية (z-score / percentile)"""
    
    def __init__(self, vbars_df: pd.DataFrame):
        self.df = vbars_df
        self.n = len(vbars_df)
        
        # Delta and CVD
        self.delta = (vbars_df["buy_volume"] - vbars_df["sell_volume"]).values
        self.cvd = np.cumsum(self.delta)
        
        # Price
        self.close = vbars_df["close"].values
        self.high = vbars_df["high"].values
        self.low = vbars_df["low"].values
        self.volume = vbars_df["volume"].values
        
        self._compute_all()
    
    def _compute_all(self):
        """حساب كل المؤشرات"""
        # CVD slopes (z-scored)
        self.cvd_slope_fast = self._rolling_zscore_slope(self.cvd, 5)
        self.cvd_slope_med = self._rolling_zscore_slope(self.cvd, 15)
        self.cvd_slope_slow = self._rolling_zscore_slope(self.cvd, 40)
        
        # Delta z-score
        self.delta_zscore = self._rolling_zscore(self.delta, 50)
        
        # Price slopes
        self.price_slope_fast = self._rolling_zscore_slope(self.close, 5)
        self.price_slope_med = self._rolling_zscore_slope(self.close, 15)
        
        # Divergence
        self.divergence = self._compute_divergence()
        
        # Absorption
        self.absorption = self._compute_absorption()
        
        # Aggression
        self.aggression = self._compute_aggression()
        
        # Effort vs Result
        self.effort_result_ratio = self._compute_effort_result()
    
    def _rolling_zscore_slope(self, values: np.ndarray, window: int) -> np.ndarray:
        """حساب slope ثم z-score ضد تاريخه"""
        if len(values) < window + 1:
            return np.zeros(len(values))
        
        slopes = np.full(len(values), np.nan)
        for i in range(window, len(values)):
            segment = values[i-window:i]
            x = np.arange(window)
            xm = x - x.mean()
            ym = segment - segment.mean()
            denom = (xm * xm).sum()
            if denom > 1e-12:
                slopes[i] = (ym @ xm) / denom
        
        # Z-score
        s = pd.Series(slopes)
        m = s.rolling(100, min_periods=20).mean()
        std = s.rolling(100, min_periods=20).std()
        z = ((s - m) / std.clip(lower=1e-12)).values
        
        return np.nan_to_num(z, nan=0.0)
    
    def _rolling_zscore(self, values: np.ndarray, window: int) -> np.ndarray:
        """Z-score ضد تاريخه الخاص"""
        s = pd.Series(values)
        m = s.rolling(window, min_periods=max(5, window//4)).mean()
        std = s.rolling(window, min_periods=max(5, window//4)).std()
        z = ((s - m) / std.clip(lower=1e-12)).values
        return np.nan_to_num(z, nan=0.0)
    
    def _compute_divergence(self) -> np.ndarray:
        """
        Divergence بين السعر و CVD
        +1 = bullish divergence (تراكم)
        -1 = bearish divergence (توزيع)
        """
        n = self.n
        divergence = np.zeros(n)
        window = 20
        
        for i in range(window, n):
            price_seg = self.close[i-window:i+1]
            cvd_seg = self.cvd[i-window:i+1]
            
            # Bearish: price near high but CVD below earlier high
            price_near_high = price_seg[-1] >= 0.98 * np.max(price_seg[:window//2+1])
            if price_near_high:
                cvd_earlier = np.max(cvd_seg[:window//2+1])
                if cvd_seg[-1] < cvd_earlier * 0.99:
                    strength = min(1.0, (cvd_earlier - cvd_seg[-1]) / max(abs(cvd_earlier), 1e-12))
                    divergence[i] = -strength
            
            # Bullish: price near low but CVD above earlier low
            price_near_low = price_seg[-1] <= 1.02 * np.min(price_seg[:window//2+1])
            if price_near_low:
                cvd_earlier = np.min(cvd_seg[:window//2+1])
                if cvd_seg[-1] > cvd_earlier:
                    strength = min(1.0, abs(cvd_seg[-1] - cvd_earlier) / max(abs(cvd_earlier), 1e-12))
                    divergence[i] = strength
        
        return divergence
    
    def _compute_absorption(self) -> np.ndarray:
        """
        Absorption: جهد عالي + نتيجة صغيرة = حدود سلبية تمتص
        """
        effort = np.abs(self.delta_zscore)
        
        price_range = self.df["range"].values
        price_z = self._rolling_zscore(price_range, 50)
        result = np.abs(price_z)
        
        absorption = np.where(
            effort > 0.5,
            np.clip(effort / (result + 0.5), 0, 3) / 3.0,
            0.0,
        )
        
        return np.clip(absorption, 0, 1)
    
    def _compute_aggression(self) -> np.ndarray:
        """
        Aggression: delta والسعر يتحركان بنفس الاتجاه بقوة
        """
        delta_dir = np.clip(self.delta_zscore, -3, 3) / 3.0
        price_dir = np.clip(self.price_slope_fast, -3, 3) / 3.0
        
        agreement = np.sign(delta_dir) * np.sign(price_dir)
        strength = np.abs(delta_dir) * np.abs(price_dir)
        
        return np.clip(agreement * strength, -1, 1)
    
    def _compute_effort_result(self) -> np.ndarray:
        """Effort vs Result ratio"""
        effort = np.abs(self.delta)
        result = np.abs(np.diff(self.close, prepend=self.close[0]))
        
        effort_norm = self._rolling_percentile(effort, 50)
        result_norm = self._rolling_percentile(result, 50)
        
        ratio = effort_norm / np.maximum(result_norm, 0.01)
        return np.clip(ratio, 0, 5)
    
    def _rolling_percentile(self, values: np.ndarray, window: int) -> np.ndarray:
        """Percentile rank داخل rolling window"""
        s = pd.Series(values)
        rank = s.rolling(window, min_periods=max(5, window//2)).apply(
            lambda x: pd.Series(x).rank(pct=True).iloc[-1], raw=False
        )
        return rank.fillna(0.5).values
    
    def get_snapshot(self, i: int) -> Dict:
        """لقطة كاملة عند البار i"""
        return {
            "cvd": float(self.cvd[i]),
            "delta": float(self.delta[i]),
            "delta_z": float(self.delta_zscore[i]),
            "cvd_slope_fast": float(self.cvd_slope_fast[i]),
            "cvd_slope_med": float(self.cvd_slope_med[i]),
            "cvd_slope_slow": float(self.cvd_slope_slow[i]),
            "price_slope_fast": float(self.price_slope_fast[i]),
            "price_slope_med": float(self.price_slope_med[i]),
            "divergence": float(self.divergence[i]),
            "absorption": float(self.absorption[i]),
            "aggression": float(self.aggression[i]),
            "effort_result_ratio": float(self.effort_result_ratio[i]),
        }
