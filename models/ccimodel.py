"""Component Condition Index (CCI) model

This module provides:
- feature extraction utilities for short time-series of vibration, temperature, strain
- a simple trainable model wrapper (uses scikit-learn) to predict a continuous CCI/risk score
- a synthetic dataset generator to bootstrap training and smoke-tests

Design notes:
- Inputs expected for training/prediction: numpy array of shape (n_samples, seq_len, n_signals)
  where signals order is [vibration, temperature, strain]. Optionally provide an `age` array
  (in years) as additional scalar feature.
- The module exposes a heuristic CCI when no trained model is available.

This is a lightweight starting point to iterate from. Save a trained model with `save()` and
load later using `load()`.
"""

from __future__ import annotations

import os
import math
import joblib
from typing import Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error


def _aggregate_signal_features(signal: np.ndarray) -> dict:
	"""Compute simple summary features from a 1D time-series array.

	Returns mean, std, max, min, rms, and slope (linear trend).
	"""
	n = len(signal)
	if n == 0:
		return dict(mean=0.0, std=0.0, max=0.0, min=0.0, rms=0.0, slope=0.0)
	mean = float(np.mean(signal))
	std = float(np.std(signal))
	mx = float(np.max(signal))
	mn = float(np.min(signal))
	rms = float(np.sqrt(np.mean(np.square(signal))))
	# slope via linear fit
	try:
		x = np.arange(n)
		slope = float(np.polyfit(x, signal, 1)[0])
	except Exception:
		slope = 0.0
	return dict(mean=mean, std=std, max=mx, min=mn, rms=rms, slope=slope)


def timeseries_to_feature_matrix(X: np.ndarray, ages: Optional[np.ndarray] = None) -> pd.DataFrame:
	"""Convert a timeseries array into a tabular feature DataFrame.

	X shape: (n_samples, seq_len, n_signals) where signals are [vibration, temperature, strain].
	ages: optional array shape (n_samples,) in years.
	"""
	n_samples, seq_len, n_signals = X.shape
	rows = []
	for i in range(n_samples):
		sample = X[i]
		feat = {}
		# Expect signal order
		names = ["vibration", "temperature", "strain"]
		for j, name in enumerate(names[:n_signals]):
			sig = sample[:, j]
			agg = _aggregate_signal_features(sig)
			for k, v in agg.items():
				feat[f"{name}_{k}"] = v
		# age
		if ages is not None:
			feat["age_years"] = float(ages[i])
		rows.append(feat)
	return pd.DataFrame(rows)


class CCIModel:
	"""Wrapper around a regressor that predicts a continuous CCI/risk score (0..1).

	If not trained, `predict_score` will fall back to a simple heuristic.
	"""

	def __init__(self, model: Optional[RandomForestRegressor] = None):
		self.model = model if model is not None else RandomForestRegressor(n_estimators=100, random_state=42)
		self.scaler: Optional[StandardScaler] = None
		self.is_fitted = False

	def fit(self, X: pd.DataFrame, y: np.ndarray) -> None:
		self.scaler = StandardScaler()
		Xs = self.scaler.fit_transform(X.values)
		self.model.fit(Xs, y)
		self.is_fitted = True

	def predict_score(self, X: pd.DataFrame) -> np.ndarray:
		"""Return score in [0,1]. If model not fitted, use heuristic."""
		if self.is_fitted and self.scaler is not None:
			Xs = self.scaler.transform(X.values)
			out = self.model.predict(Xs)
			out = np.clip(out, 0.0, 1.0)
			return out
		# heuristic fallback (normalized weighted sum)
		# weights chosen to emphasize vibration and slope
		w = {
			"vibration_rms": 0.45,
			"vibration_slope": 0.25,
			"strain_mean": 0.15,
			"temperature_mean": 0.10,
			"age_years": 0.05,
		}
		df = X.copy()
		# fill missing columns with zeros
		for key in w.keys():
			if key not in df.columns:
				df[key] = 0.0
		# robust normalization by percentile ranges (avoid leaking)
		def norm(col):
			a = np.percentile(col, 5)
			b = np.percentile(col, 95)
			if b - a <= 0:
				return np.zeros_like(col)
			return (col - a) / (b - a)

		score = np.zeros(len(df))
		for k, weight in w.items():
			score += weight * np.clip(norm(df[k].values), 0.0, 1.0)
		# final clamp
		score = np.clip(score, 0.0, 1.0)
		return score

	def save(self, path: str) -> None:
		os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
		joblib.dump({"model": self.model, "scaler": self.scaler, "is_fitted": self.is_fitted}, path)

	@classmethod
	def load(cls, path: str) -> "CCIModel":
		data = joblib.load(path)
		inst = cls(model=data["model"]) if data.get("model") is not None else cls()
		inst.scaler = data.get("scaler")
		inst.is_fitted = bool(data.get("is_fitted", False))
		return inst


def generate_synthetic_dataset(n_samples: int = 2000, seq_len: int = 128, seed: int = 0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
	"""Create a synthetic dataset (X, ages, risk_score).

	X returned shape: (n_samples, seq_len, 3) with signals [vibration, temperature, strain].
	risk_score is continuous in [0,1] (higher means closer to failure).
	"""
	rng = np.random.default_rng(seed)
	X = np.zeros((n_samples, seq_len, 3), dtype=float)
	ages = rng.uniform(0, 120, size=(n_samples,))  # component age in years
	risk = np.zeros(n_samples)
	for i in range(n_samples):
		age = ages[i]
		# temperature: daily-ish variation + ambient
		base_temp = rng.uniform(5, 40)
		temp = base_temp + 2 * np.sin(np.linspace(0, 6 * np.pi, seq_len)) + rng.normal(0, 0.5, seq_len)
		# vibration: base low plus occasional high-wind spikes; correlate with age weakly
		wind_factor = rng.uniform(0, 1.5)
		vibration = 0.1 * (1 + age / 100.0) + wind_factor * (rng.normal(0, 1, seq_len) ** 2)
		# strain: follows vibration but with slower dynamics
		strain = 0.01 * (1 + age / 100.0) + 0.5 * np.convolve(vibration, np.ones(5) / 5, mode='same')
		X[i, :, 0] = vibration
		X[i, :, 1] = temp
		X[i, :, 2] = strain
		# compute summary statistics to craft a risk score
		vib_rms = np.sqrt(np.mean(vibration ** 2))
		temp_mean = float(np.mean(temp))
		strain_mean = float(np.mean(strain))
		# base linear combination then pass through sigmoid-like mapping
		raw = 0.03 * age + 6.0 * vib_rms + 0.02 * (temp_mean - 20.0) + 4.0 * strain_mean + rng.normal(0, 0.5)
		score = 1.0 / (1.0 + math.exp(-raw / 10.0))  # softer scale
		risk[i] = float(np.clip(score, 0.0, 1.0))
	return X, ages, risk


def train_on_synthetic(save_path: Optional[str] = None, verbose: bool = True) -> Tuple[CCIModel, pd.DataFrame, np.ndarray]:
	"""Train a CCIModel on synthetic data and optionally save it.

	Returns (model, feature_df, y).
	"""
	X_ts, ages, y = generate_synthetic_dataset(n_samples=1500, seq_len=128, seed=42)
	df = timeseries_to_feature_matrix(X_ts, ages=ages)
	X_train, X_val, y_train, y_val = train_test_split(df, y, test_size=0.2, random_state=42)
	model = CCIModel()
	model.fit(X_train, y_train)
	preds = model.predict_score(X_val)
	rmse = math.sqrt(mean_squared_error(y_val, preds))
	if verbose:
		print(f"Trained model RMSE on val set: {rmse:.4f}")
		# show thresholds
		print("Threshold suggestion: green <0.33, yellow 0.33-0.66, red >0.66")
	if save_path:
		model.save(save_path)
		if verbose:
			print(f"Saved model to {save_path}")
	return model, df, y


if __name__ == "__main__":
	# quick smoke run when module executed directly
	m, df, y = train_on_synthetic(save_path="cci_model.joblib", verbose=True)
	# demonstrate prediction on a few synthetic samples
	X_ts, ages, y_true = generate_synthetic_dataset(n_samples=5, seq_len=128, seed=123)
	feats = timeseries_to_feature_matrix(X_ts, ages=ages)
	scores = m.predict_score(feats)
	for i, (s, gt, age) in enumerate(zip(scores, y_true, ages)):
		zone = "GREEN" if s < 0.33 else ("YELLOW" if s < 0.66 else "RED")
		print(f"Sample {i}: score={s:.3f} zone={zone} age={age:.1f} years true_score={gt:.3f}")

