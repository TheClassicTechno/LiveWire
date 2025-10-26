"""
Grid Component Risk Modeling
---------------------------------
This module implements a lightweight, production‑friendly pipeline to:
  1) Compute a Component Condition Index (CCI) from vibration, temperature, and strain time‑series.
  2) Classify risk zones (green / yellow / red) based on calibrated thresholds.
  3) Estimate lead time to breach of the red threshold ("time left") by projecting CCI trends.

It is designed to work with streaming or batch data and to be easily embedded in a backend service.
It avoids uncommon dependencies; only uses numpy, pandas, scipy, scikit‑learn, and joblib.

Key ideas
---------
• CCI is a normalized, weighted composite of short‑ and long‑horizon features for vibration, temperature, and strain.
• Features include rolling stats, rate‑of‑change, and band‑power (simple FFT windows) for vibration (as a proxy for wind‑induced oscillations).
• Risk zones are determined via either fixed domain thresholds or data‑driven quantiles, then persisted for consistent inference.
• "Time Left" is estimated by fitting a simple linear model to the recent CCI trajectory and projecting when it will cross the red threshold.
  (If trend ≤ 0, time left is set to +inf.)

Data expectations
-----------------
Input dataframe must contain the following columns (case sensitive):
  - timestamp: datetime64[ns] or parseable string
  - component_id: str or categorical identifier
  - vibration: float  (unitless RMS / g, or any consistent vibration proxy)
  - temperature: float (°C)
  - strain: float (microstrain or consistent unit)
Optional but helpful:
  - age_years: float (component age)
  - wind_speed: float (m/s)  — if present, it will be included as an additional driver

Usage (training & calibration)
------------------------------
from grid_risk_model import CCIPipeline, CCIPipelineConfig
cfg = CCIPipelineConfig()
pipeline = CCIPipeline(cfg)

# 1) Fit scalers and calibrate thresholds on a historical baseline window
pipeline.fit(calib_df)  # calib_df contains the columns listed above across many components

# 2) Score new data (batch or stream)
scored = pipeline.score(new_df)  # adds columns: cci, zone, time_left_hours

# 3) Persist artifacts for deployment
pipeline.save("./artifacts")

# 4) Load later for inference
loaded = CCIPipeline.load("./artifacts")
scored = loaded.score(new_df)

Notes
-----
• If you have known failure events (labels), you can later replace/augment the simple trend projection
  with supervised models for TTF (time‑to‑failure) or survival; this module leaves a hook for that.
• If you have high‑rate vibration streams, pre‑aggregate to 1–10s RMS windows before calling score().

"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Dict, Tuple, Optional

import numpy as np
import pandas as pd
from scipy.signal import welch
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
from joblib import dump, load
import os

# -----------------------------
# Configuration
# -----------------------------

@dataclass
class CCIPipelineConfig:
    # Rolling windows (in samples). Choose based on your sampling cadence
    short_win: int = 12     # e.g., if data is 5‑min cadence, 12 ≈ 1 hour
    mid_win: int = 288      # ≈ 1 day
    long_win: int = 2016    # ≈ 1 week

    # Welch PSD settings for vibration (to capture wind‑induced oscillations)
    psd_seg_len: int = 64
    psd_overlap: int = 32
    # Frequency band indices are computed from sampling rate; we approximate by using segment length buckets

    # Feature weights for CCI (domain‑tunable)
    w_vibration: float = 0.50
    w_temperature: float = 0.30
    w_strain: float = 0.20

    # Zone definitions: either fixed values or quantiles learned during fit()
    use_quantile_zones: bool = True
    yellow_q: float = 0.80
    red_q: float = 0.95

    # If fixed thresholds are used, set them here after examining your CCI distribution
    fixed_yellow: float = 0.65
    fixed_red: float = 0.85

    # Time‑left projection params
    trend_lookback: int = 288  # number of recent points to fit trend (e.g., last day)
    max_time_left_hours: float = 24 * 365 * 10  # cap to avoid absurd values

    # Optional extra driver names
    wind_col: Optional[str] = "wind_speed"

    # Mandatory column names
    ts_col: str = "timestamp"
    id_col: str = "component_id"
    vib_col: str = "vibration"
    temp_col: str = "temperature"
    strain_col: str = "strain"


# -----------------------------
# Transformers
# -----------------------------

class SortAndCast(TransformerMixin, BaseEstimator):
    def __init__(self, cfg: CCIPipelineConfig):
        self.cfg = cfg

    def fit(self, X, y=None):
        return self

    def transform(self, X: pd.DataFrame):
        df = X.copy()
        # ensure dtypes
        if not np.issubdtype(df[self.cfg.ts_col].dtype, np.datetime64):
            df[self.cfg.ts_col] = pd.to_datetime(df[self.cfg.ts_col], errors="coerce")
        # drop rows with bad timestamps or mandatory NaNs
        df = df.dropna(subset=[self.cfg.ts_col, self.cfg.id_col, self.cfg.vib_col, self.cfg.temp_col, self.cfg.strain_col])
        df = df.sort_values([self.cfg.id_col, self.cfg.ts_col]).reset_index(drop=True)
        
        # Preserve cable_state if it exists (for validation)
        if 'cable_state' in X.columns:
            df['original_cable_state'] = X['cable_state']
        
        return df


class RollingFeatureMaker(TransformerMixin, BaseEstimator):
    """Create scale‑free rolling features per component.

    Features per signal (vibration/temperature/strain):
      - short/long EWMA
      - rolling std
      - rolling slope (via linear fit in the window)
      - delta from long EWMA ("stress")
    Vibration‑specific:
      - pseudo bandpower (Welch) using last psd_seg_len*2 samples (robust to short sequences)
    """

    def __init__(self, cfg: CCIPipelineConfig):
        self.cfg = cfg

    @staticmethod
    def _rolling_slope(x: pd.Series, win: int) -> pd.Series:
        if len(x) < win:
            return pd.Series([np.nan] * len(x), index=x.index)
        idx = np.arange(win)
        out = np.full(len(x), np.nan)
        for i in range(win - 1, len(x)):
            y = x.values[i - win + 1 : i + 1]
            # slope of least‑squares line
            A = np.vstack([idx, np.ones_like(idx)]).T
            m, _ = np.linalg.lstsq(A, y, rcond=None)[0]
            out[i] = m
        return pd.Series(out, index=x.index)

    @staticmethod
    def _welch_bandpower(x: np.ndarray) -> float:
        if len(x) < 16:
            return np.nan
        f, Pxx = welch(x, nperseg=min(len(x), 64), noverlap=32 if len(x) >= 64 else len(x)//2)
        # Emphasize mid‑high frequency bins as a proxy for oscillatory stress
        # Here we weight the upper half of the spectrum more
        if len(Pxx) == 0:
            return np.nan
        w = np.linspace(0.5, 1.0, num=len(Pxx))
        return float(np.sum(Pxx * w))

    def fit(self, X, y=None):
        return self

    def transform(self, X: pd.DataFrame):
        cfg = self.cfg
        df = X.copy()

        def per_component(group: pd.DataFrame) -> pd.DataFrame:
            g = group.copy()
            for col in [cfg.vib_col, cfg.temp_col, cfg.strain_col]:
                short = g[col].ewm(span=cfg.short_win, adjust=False).mean()
                long = g[col].ewm(span=cfg.long_win, adjust=False).mean()
                g[f"{col}_ewma_s"] = short
                g[f"{col}_ewma_l"] = long
                g[f"{col}_std_s"] = g[col].rolling(cfg.short_win, min_periods=cfg.short_win//2).std()
                g[f"{col}_slope_s"] = RollingFeatureMaker._rolling_slope(g[col], cfg.short_win)
                g[f"{col}_stress"] = (short - long)

            # Vibration bandpower over a short trailing window
            seg = max(cfg.psd_seg_len * 2, 32)
            vib_vals = g[cfg.vib_col].values
            bp = []
            for i in range(len(g)):
                start = max(0, i - seg + 1)
                bp.append(self._welch_bandpower(vib_vals[start:i+1]))
            g["vibration_bandpower"] = bp

            # Optional wind speed as additional driver
            if cfg.wind_col and cfg.wind_col in g.columns:
                g[f"{cfg.wind_col}_ewma_s"] = g[cfg.wind_col].ewm(span=cfg.short_win, adjust=False).mean()
                g[f"{cfg.wind_col}_stress"] = g[f"{cfg.wind_col}_ewma_s"] - g[cfg.wind_col].ewm(span=cfg.long_win, adjust=False).mean()

            return g

        df = df.groupby(self.cfg.id_col, group_keys=False).apply(per_component)
        return df


class ColumnScaler(TransformerMixin, BaseEstimator):
    """Standardize a selected set of numeric columns and remember which ones we used."""

    def __init__(self, cols: Optional[list] = None):
        self.cols = cols
        self.scaler = StandardScaler()

    def fit(self, X: pd.DataFrame, y=None):
        if self.cols is None:
            # Infer numeric feature columns (exclude obvious non‑features)
            self.cols = [c for c in X.columns if X[c].dtype != 'O' and not c.endswith("timestamp")]
        self.scaler.fit(X[self.cols])
        return self

    def transform(self, X: pd.DataFrame):
        Y = X.copy()
        Y[self.cols] = self.scaler.transform(Y[self.cols])
        return Y


class CCIMaker(TransformerMixin, BaseEstimator):
    """Combine standardized features into a single CCI score in [0, 1] via a smooth logistic mapping.

    The score emphasizes: vibration stress & bandpower, temperature stress, and strain stress.
    """

    def __init__(self, cfg: CCIPipelineConfig, feature_cols: Optional[list] = None):
        self.cfg = cfg
        self.feature_cols = feature_cols
        self._cols_: Optional[list] = None

    def fit(self, X: pd.DataFrame, y=None):
        # pick default columns if not provided
        if self.feature_cols is None:
            base = [
                f"{self.cfg.vib_col}_stress",
                "vibration_bandpower",
                f"{self.cfg.temp_col}_stress",
                f"{self.cfg.strain_col}_stress",
            ]
            if self.cfg.wind_col and f"{self.cfg.wind_col}_stress" in X.columns:
                base.append(f"{self.cfg.wind_col}_stress")
            self._cols_ = base
        else:
            self._cols_ = self.feature_cols
        return self

    def transform(self, X: pd.DataFrame):
        cfg = self.cfg
        df = X.copy()
        cols = self._cols_ or []
        # Ensure columns exist; if not, fill with zeros to keep shape stable
        for c in cols:
            if c not in df.columns:
                df[c] = 0.0

        # Weighted sum (standardized upstream), then logistic squashing to [0,1]
        vib = df.get(f"{cfg.vib_col}_stress", 0.0) + 0.6 * df.get("vibration_bandpower", 0.0)
        temp = df.get(f"{cfg.temp_col}_stress", 0.0)
        strain = df.get(f"{cfg.strain_col}_stress", 0.0)
        wind = df.get(f"{cfg.wind_col}_stress", 0.0) if (cfg.wind_col and f"{cfg.wind_col}_stress" in df.columns) else 0.0

        raw = cfg.w_vibration * vib + cfg.w_temperature * temp + cfg.w_strain * strain + 0.15 * wind
        # logistic: 1/(1+exp(-z)); scale raw to a reasonable range
        z = 1.5 * raw
        df["cci"] = 1.0 / (1.0 + np.exp(-z))
        return df


class ZoneCalibrator(TransformerMixin, BaseEstimator):
    """Calibrate CCI thresholds and assign zones.

    If use_quantile_zones is True, derive yellow/red from the empirical distribution on fit().
    Otherwise, use fixed thresholds from config.
    """

    def __init__(self, cfg: CCIPipelineConfig):
        self.cfg = cfg
        self.yellow_: float = cfg.fixed_yellow
        self.red_: float = cfg.fixed_red

    def fit(self, X: pd.DataFrame, y=None):
        if self.cfg.use_quantile_zones:
            cci = X["cci"].dropna()
            if len(cci) >= 100:  # need a bit of data to be meaningful
                self.yellow_ = float(np.quantile(cci, self.cfg.yellow_q))
                self.red_ = float(np.quantile(cci, self.cfg.red_q))
        return self

    def transform(self, X: pd.DataFrame):
        df = X.copy()
        yel, red = self.yellow_, self.red_
        conds = [df["cci"] < yel, (df["cci"] >= yel) & (df["cci"] < red), df["cci"] >= red]
        df["zone"] = np.select(conds, ["green", "yellow", "red"], default="green")
        df["zone_thresholds"] = list(zip([yel]*len(df), [red]*len(df)))
        return df


class TimeLeftProjector(TransformerMixin, BaseEstimator):
    """Estimate time left (in hours) until CCI crosses the red threshold, per component.

    Fit a linear regression to recent CCI vs time index and project time to red.
    If slope <= 0 or currently above red, set edge cases accordingly.
    """

    def __init__(self, cfg: CCIPipelineConfig, freq_hint_hours: Optional[float] = None):
        self.cfg = cfg
        self.freq_hint_hours = freq_hint_hours  # if timestamps are irregular, we infer cadence

    def fit(self, X, y=None):
        return self

    def transform(self, X: pd.DataFrame):
        cfg = self.cfg
        df = X.copy()

        def per_component(group: pd.DataFrame) -> pd.DataFrame:
            g = group.copy()
            if len(g) < 3:
                g["time_left_hours"] = np.inf
                return g

            # infer cadence (median delta in hours)
            ts = pd.to_datetime(g[cfg.ts_col].values)
            if len(ts) >= 2:
                dt_hours = np.median(np.diff(ts).astype('timedelta64[s]').astype(float) / 3600.0)
            else:
                dt_hours = self.freq_hint_hours or 1.0
            dt_hours = max(dt_hours, 1e-6)

            # Use last N points
            n = min(cfg.trend_lookback, len(g))
            y_cci = g["cci"].values[-n:]
            x_idx = np.arange(len(y_cci)).reshape(-1, 1)
            if np.any(~np.isfinite(y_cci)) or len(y_cci) < 3:
                g["time_left_hours"] = np.inf
                return g

            model = LinearRegression().fit(x_idx, y_cci)
            slope = float(model.coef_[0])
            intercept = float(model.intercept_)
            red = g["zone_thresholds"].iloc[-1][1] if "zone_thresholds" in g.columns else cfg.fixed_red

            # Already red
            if y_cci[-1] >= red:
                tl = 0.0
            # Not trending up
            elif slope <= 0:
                tl = np.inf
            else:
                # Solve for t: intercept + slope * t = red
                t_idx = (red - intercept) / slope
                # remaining steps from the last index
                steps_left = max(0.0, t_idx - (len(y_cci) - 1))
                tl = float(steps_left * dt_hours)
                tl = min(tl, cfg.max_time_left_hours)

            g["time_left_hours"] = np.concatenate([
                np.full(len(g) - 1, np.nan),  # only the latest value is actionable; earlier rows NaN
                [tl]
            ])
            return g

        out = df.groupby(self.cfg.id_col, group_keys=False).apply(per_component)
        return out


# -----------------------------
# End‑to‑end pipeline wrapper
# -----------------------------

class CCIPipeline:
    def __init__(self, cfg: Optional[CCIPipelineConfig] = None):
        self.cfg = cfg or CCIPipelineConfig()
        self.sorter = SortAndCast(self.cfg)
        self.feats = RollingFeatureMaker(self.cfg)
        self.scaler = ColumnScaler()
        self.cci = CCIMaker(self.cfg)
        self.zones = ZoneCalibrator(self.cfg)
        self.timeleft = TimeLeftProjector(self.cfg)
        self._fitted = False

    def fit(self, calib_df: pd.DataFrame):
        df = self.sorter.transform(calib_df)
        df = self.feats.transform(df)
        # fit scaler on engineered features
        self.scaler.fit(df)
        df = self.scaler.transform(df)
        # fit CCI combiner (no parameters beyond columns) & calibrate zones
        self.cci.fit(df)
        df = self.cci.transform(df)
        self.zones.fit(df)
        self._fitted = True
        return self

    def score(self, new_df: pd.DataFrame) -> pd.DataFrame:
        assert self._fitted, "Call fit() first or load a saved pipeline."
        df = self.sorter.transform(new_df)
        df = self.feats.transform(df)
        df = self.scaler.transform(df)
        df = self.cci.transform(df)
        df = self.zones.transform(df)
        df = self.timeleft.transform(df)
        return df

    def save(self, path: str):
        os.makedirs(path, exist_ok=True)
        dump(self.cfg, os.path.join(path, "cfg.joblib"))
        dump(self.scaler, os.path.join(path, "scaler.joblib"))
        dump(self.cci, os.path.join(path, "cci.joblib"))
        dump(self.zones, os.path.join(path, "zones.joblib"))
        # Stateless transformers need not be saved; keep versions for clarity
        meta = {
            "class": self.__class__.__name__,
            "version": 1,
            "cfg": asdict(self.cfg),
        }
        dump(meta, os.path.join(path, "meta.joblib"))

    @classmethod
    def load(cls, path: str) -> "CCIPipeline":
        cfg = load(os.path.join(path, "cfg.joblib"))
        pipe = cls(cfg)
        pipe.scaler = load(os.path.join(path, "scaler.joblib"))
        pipe.cci = load(os.path.join(path, "cci.joblib"))
        pipe.zones = load(os.path.join(path, "zones.joblib"))
        pipe._fitted = True
        return pipe


# -----------------------------
# Convenience: Backtest helper for a known window (e.g., 2018 Camp Fire)
# -----------------------------

def backtest_warning_lead_time(pipeline: CCIPipeline,
                               df_hist: pd.DataFrame,
                               fire_start_ts: str,
                               component_id: str) -> Dict[str, float]:
    """Compute the first time the component enters RED before the known event time,
    and return the lead time (hours) relative to fire_start_ts.

    Parameters
    ----------
    pipeline : CCIPipeline (already fitted on pre‑event data)
    df_hist : DataFrame with required columns covering a window before the event
    fire_start_ts : ISO timestamp string for the ignition time
    component_id : ID of the component of interest
    """
    scored = pipeline.score(df_hist[df_hist[ pipeline.cfg.id_col ] == component_id])
    scored = scored.dropna(subset=["timestamp"])  # safety
    fire_ts = pd.to_datetime(fire_start_ts)
    # when did the component first cross into RED?
    red_rows = scored[(scored["zone"] == "red") & (scored["timestamp"] < fire_ts)]
    if len(red_rows) == 0:
        return {"lead_time_hours": 0.0, "first_red_ts": None}
    first_red_ts = red_rows["timestamp"].iloc[0]
    lead = (fire_ts - first_red_ts).total_seconds() / 3600.0
    return {"lead_time_hours": float(max(0.0, lead)), "first_red_ts": str(first_red_ts)}


def validate_predictions_vs_cable_state(scored_df: pd.DataFrame) -> Dict:
    """Compare model predictions (zone) against original cable_state for validation.
    
    Returns accuracy metrics and confusion matrix.
    """
    if 'original_cable_state' not in scored_df.columns:
        return {"error": "No original_cable_state found. Ensure input data contains cable_state column."}
    
    # Clean data
    df = scored_df.dropna(subset=['zone', 'original_cable_state']).copy()
    
    if len(df) == 0:
        return {"error": "No valid data for comparison"}
    
    # Create mapping from cable_state to risk level for comparison
    def map_cable_state_to_risk(state):
        state_str = str(state).lower()
        if any(word in state_str for word in ['critical', 'fault', 'fail', 'danger']):
            return 'red'
        elif any(word in state_str for word in ['warning', 'caution', 'alert', 'moderate']):
            return 'yellow'
        else:
            return 'green'
    
    df['mapped_cable_state'] = df['original_cable_state'].apply(map_cable_state_to_risk)
    
    # Calculate metrics
    from sklearn.metrics import accuracy_score, classification_report
    import pandas as pd
    
    accuracy = accuracy_score(df['mapped_cable_state'], df['zone'])
    
    # Confusion matrix
    confusion = pd.crosstab(df['zone'], df['mapped_cable_state'], margins=True)
    
    # Classification report
    report = classification_report(df['mapped_cable_state'], df['zone'], output_dict=True)
    
    return {
        "accuracy": accuracy,
        "confusion_matrix": confusion.to_dict(),
        "classification_report": report,
        "sample_comparison": df[['component_id', 'timestamp', 'zone', 'original_cable_state', 'mapped_cable_state', 'cci']].head(10).to_dict('records')
    }


# -----------------------------
# Minimal CLI demo (optional)
# -----------------------------
if __name__ == "__main__":
    # Example synthetic usage (replace with real data)
    rng = np.random.default_rng(7)
    n = 2000
    ts = pd.date_range("2018-09-01", periods=n, freq="15min")
    comp = ["hook_97yo"] * n

    # Baseline signals
    vib = np.clip(rng.normal(0.02, 0.005, n) + 0.0001*np.arange(n), 0, None)
    temp = 25 + 5*np.sin(np.linspace(0, 20*np.pi, n)) + rng.normal(0, 0.5, n)
    strain = 100 + 0.02*np.arange(n) + rng.normal(0, 1.5, n)

    # Simulate a wind event ramping up vibration toward the end
    vib += 0.0006*np.maximum(0, np.arange(n) - int(0.7*n))

    demo = pd.DataFrame({
        "timestamp": ts,
        "component_id": comp,
        "vibration": vib,
        "temperature": temp,
        "strain": strain,
    })

    cfg = CCIPipelineConfig()
    pipe = CCIPipeline(cfg)
    # Calibrate on the first 60% as "normal"
    calib = demo.iloc[: int(0.6*n)]
    pipe.fit(calib)

    scored = pipe.score(demo)
    # Backtest lead time to a hypothetical fire at the last timestamp
    res = backtest_warning_lead_time(pipe, scored, str(ts[-1]), "hook_97yo")
    print("Backtest lead time (hours):", res)
