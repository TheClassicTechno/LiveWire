"""
RUL (Remaining Useful Life) Backend API
========================================

Flask endpoints for real-time RUL prediction.

Endpoints:
  POST /api/rul/predict - Predict RUL for a single component
  POST /api/rul/batch-predict - Predict RUL for multiple components
  GET /api/rul/model-info - Get model metadata and performance metrics
"""

import os
import json
import numpy as np
import pandas as pd
from flask import Blueprint, jsonify, request
from datetime import datetime
import joblib
import logging

bp = Blueprint('rul', __name__)
logger = logging.getLogger(__name__)

# Global model cache
rul_model = None
rul_scaler = None
rul_feature_names = None
rul_samples_per_lifecycle = None


def load_rul_artifacts():
    """Load pre-trained RUL model and scaler from disk"""
    global rul_model, rul_scaler, rul_feature_names, rul_samples_per_lifecycle

    artifacts_dir = os.path.join(os.path.dirname(__file__), '..', 'models', 'artifacts')

    try:
        rul_model = joblib.load(os.path.join(artifacts_dir, 'rul_model.pkl'))
        rul_scaler = joblib.load(os.path.join(artifacts_dir, 'rul_scaler.pkl'))
        rul_feature_names = joblib.load(os.path.join(artifacts_dir, 'rul_feature_names.pkl'))
        rul_samples_per_lifecycle = joblib.load(os.path.join(artifacts_dir, 'rul_samples_per_lifecycle.pkl'))

        logger.info("✅ RUL model artifacts loaded successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to load RUL artifacts: {e}")
        return False


def engineer_features(sensor_readings: dict, previous_readings: list = None) -> np.ndarray:
    """
    Engineer features from sensor readings for RUL prediction.

    Args:
        sensor_readings: Dict with keys like 'sensor_1', 'sensor_2', ..., 'sensor_20'
                        Also expects 'op_setting_1', 'op_setting_2', 'op_setting_3'
                        And 'time_cycles' (operational cycles so far)
        previous_readings: List of previous sensor readings (for trend calculation)

    Returns:
        Feature vector (numpy array) ready for model prediction
    """

    # Extract sensor values (filter out sensors 21-26 which are all NaN)
    sensor_cols = [f'sensor_{i}' for i in range(1, 21)]  # sensors 1-20 only
    sensor_values = np.array([sensor_readings.get(col, 0) for col in sensor_cols])

    # Operational settings
    op_settings = np.array([
        sensor_readings.get('op_setting_1', 0),
        sensor_readings.get('op_setting_2', 0),
        sensor_readings.get('op_setting_3', 0)
    ])

    # Time in operation
    time_in_op = sensor_readings.get('time_cycles', 0)
    max_cycles = sensor_readings.get('max_cycles', 361)  # Default to CMaps max
    time_normalized = time_in_op / max_cycles if max_cycles > 0 else 0

    # Calculate degradation trends (slope from first to current)
    trends = []
    if previous_readings and len(previous_readings) > 1:
        # We have history - calculate actual trends
        history_df = pd.DataFrame(previous_readings)
        for col in sensor_cols:
            if col in history_df.columns:
                x = history_df.index.values
                y = history_df[col].values
                if len(y) > 1 and np.max(x) > np.min(x):
                    slope = (y[-1] - y[0]) / (x[-1] - x[0])
                    trends.append(slope)
                else:
                    trends.append(0)
            else:
                trends.append(0)
    else:
        # No history - use zeros (will be updated when historical data arrives)
        trends = [0] * len(sensor_cols)
    trends = np.array(trends)

    # Sensor volatility (std from history)
    volatility = np.zeros(len(sensor_cols))
    if previous_readings and len(previous_readings) > 1:
        history_df = pd.DataFrame(previous_readings)
        for i, col in enumerate(sensor_cols):
            if col in history_df.columns:
                volatility[i] = history_df[col].std() if not history_df[col].isna().all() else 0

    # Combine all features in the same order as training
    features = np.concatenate([
        sensor_values,      # Current sensor values (20)
        trends,             # Degradation trends (20)
        volatility,         # Sensor volatility (20)
        op_settings,        # Operational settings (3)
        [time_in_op, time_normalized]  # Time metrics (2)
    ])

    return features


@bp.route('/api/rul/predict', methods=['POST'])
def predict_rul():
    """
    Predict RUL for a single component.

    Request JSON:
    {
        "component_id": "CABLE_A1_MAIN",
        "sensors": {
            "sensor_1": 123.45,
            "sensor_2": 456.78,
            ...
            "sensor_20": 789.12,
            "op_setting_1": 42.0,
            "op_setting_2": 0.84,
            "op_setting_3": 100.0,
            "time_cycles": 150
        },
        "previous_readings": [
            {"sensor_1": 120.0, "sensor_2": 450.0, ...},
            {"sensor_1": 121.5, "sensor_2": 452.0, ...}
        ],
        "max_cycles": 361
    }

    Returns:
    {
        "component_id": "CABLE_A1_MAIN",
        "rul_cycles": 48.5,
        "rul_hours": 48.5,
        "rul_days": 2.02,
        "confidence": 0.087,
        "risk_zone": "yellow",
        "risk_score": 0.72,
        "timestamp": "2025-10-26T11:00:00Z"
    }
    """

    if not rul_model:
        return jsonify({"error": "RUL model not loaded"}), 500

    try:
        data = request.get_json()

        # Validate required fields
        if 'component_id' not in data or 'sensors' not in data:
            return jsonify({"error": "Missing 'component_id' or 'sensors'"}), 400

        component_id = data['component_id']
        sensor_readings = data['sensors']
        previous_readings = data.get('previous_readings', [])

        # Engineer features
        X = engineer_features(sensor_readings, previous_readings)

        # Scale features
        X_scaled = rul_scaler.transform(X.reshape(1, -1))

        # Make prediction
        rul_cycles = float(rul_model.predict(X_scaled)[0])

        # Ensure non-negative RUL
        rul_cycles = max(0, rul_cycles)

        # Convert cycles to hours/days (assuming 1 cycle = 1 hour for power grid)
        rul_hours = rul_cycles
        rul_days = rul_cycles / 24.0

        # Calculate confidence (ensemble uncertainty)
        predictions_all = np.array([tree.predict(X_scaled) for tree in rul_model.estimators_[:, 0]])
        confidence = float(np.std(predictions_all))

        # Determine risk zone
        if rul_hours < 24:
            risk_zone = "red"
            risk_score = 0.8 + (1 - min(rul_hours / 24, 1)) * 0.2
        elif rul_hours < 72:
            risk_zone = "yellow"
            risk_score = 0.4 + (1 - min((rul_hours - 24) / 48, 1)) * 0.4
        else:
            risk_zone = "green"
            risk_score = max(0, 0.4 - (rul_hours - 72) / 360 * 0.4)

        risk_score = min(1.0, max(0.0, risk_score))

        response = {
            "component_id": component_id,
            "rul_cycles": round(rul_cycles, 2),
            "rul_hours": round(rul_hours, 2),
            "rul_days": round(rul_days, 2),
            "confidence": round(confidence, 3),
            "risk_zone": risk_zone,
            "risk_score": round(risk_score, 2),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        logger.info(f"✅ RUL prediction for {component_id}: {rul_hours:.2f}h ({risk_zone})")
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"❌ RUL prediction failed: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route('/api/rul/batch-predict', methods=['POST'])
def batch_predict_rul():
    """
    Predict RUL for multiple components in one request.

    Request JSON:
    {
        "predictions": [
            {
                "component_id": "CABLE_A1_MAIN",
                "sensors": { ... },
                "previous_readings": [ ... ]
            },
            {
                "component_id": "CABLE_A2_BACKUP",
                "sensors": { ... },
                "previous_readings": [ ... ]
            }
        ]
    }

    Returns:
    {
        "predictions": [
            { component_id, rul_cycles, rul_hours, rul_days, confidence, risk_zone, risk_score, timestamp },
            ...
        ],
        "critical_count": 2,
        "warning_count": 5,
        "safe_count": 18
    }
    """

    if not rul_model:
        return jsonify({"error": "RUL model not loaded"}), 500

    try:
        data = request.get_json()

        if 'predictions' not in data:
            return jsonify({"error": "Missing 'predictions' array"}), 400

        predictions_list = data['predictions']
        results = []
        risk_counts = {"red": 0, "yellow": 0, "green": 0}

        for pred_req in predictions_list:
            component_id = pred_req.get('component_id')
            sensor_readings = pred_req.get('sensors', {})
            previous_readings = pred_req.get('previous_readings', [])

            # Engineer and predict
            X = engineer_features(sensor_readings, previous_readings)
            X_scaled = rul_scaler.transform(X.reshape(1, -1))

            rul_cycles = float(rul_model.predict(X_scaled)[0])
            rul_cycles = max(0, rul_cycles)
            rul_hours = rul_cycles
            rul_days = rul_cycles / 24.0

            # Confidence
            predictions_all = np.array([tree.predict(X_scaled) for tree in rul_model.estimators_[:, 0]])
            confidence = float(np.std(predictions_all))

            # Risk zone
            if rul_hours < 24:
                risk_zone = "red"
                risk_score = 0.8 + (1 - min(rul_hours / 24, 1)) * 0.2
            elif rul_hours < 72:
                risk_zone = "yellow"
                risk_score = 0.4 + (1 - min((rul_hours - 24) / 48, 1)) * 0.4
            else:
                risk_zone = "green"
                risk_score = max(0, 0.4 - (rul_hours - 72) / 360 * 0.4)

            risk_score = min(1.0, max(0.0, risk_score))
            risk_counts[risk_zone] += 1

            results.append({
                "component_id": component_id,
                "rul_cycles": round(rul_cycles, 2),
                "rul_hours": round(rul_hours, 2),
                "rul_days": round(rul_days, 2),
                "confidence": round(confidence, 3),
                "risk_zone": risk_zone,
                "risk_score": round(risk_score, 2),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })

        response = {
            "predictions": results,
            "critical_count": risk_counts["red"],
            "warning_count": risk_counts["yellow"],
            "safe_count": risk_counts["green"]
        }

        logger.info(f"✅ Batch RUL prediction: {len(results)} components")
        return jsonify(response), 200

    except Exception as e:
        logger.error(f"❌ Batch RUL prediction failed: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route('/api/rul/model-info', methods=['GET'])
def model_info():
    """
    Get RUL model metadata and performance information.

    Returns:
    {
        "model_type": "GradientBoosting",
        "training_data": "NASA CMaps FD001",
        "test_mae": 68.76,
        "test_rmse": 80.28,
        "test_r2": -2.73,
        "feature_count": 68,
        "model_loaded": true,
        "timestamp": "2025-10-26T11:00:00Z"
    }
    """

    return jsonify({
        "model_type": "GradientBoosting",
        "training_data": "NASA CMaps FD001",
        "test_mae": 68.76,
        "test_rmse": 80.28,
        "test_r2": -2.73,
        "feature_count": 68,
        "n_estimators": 100,
        "max_depth": 6,
        "stratified_sampling": True,
        "samples_per_lifecycle": 20,
        "model_loaded": rul_model is not None,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }), 200


@bp.before_app_serving
def initialize_rul_model():
    """Load RUL model when Flask app starts"""
    logger.info("🚀 Initializing RUL model...")
    if load_rul_artifacts():
        logger.info("✅ RUL API ready")
    else:
        logger.warning("⚠️ RUL model failed to load - predictions will fail")
