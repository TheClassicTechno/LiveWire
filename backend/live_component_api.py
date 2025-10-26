"""
Live Component API
==================

Serves and updates the live component that's hooked to hardware.
Handles:
1. Historical degradation data (30+ days)
2. Current hardware readings
3. RUL predictions
4. Hardware manipulation (simulate temp/vibration changes)
"""

import os
import json
import logging
from datetime import datetime
from flask import Blueprint, jsonify, request
from typing import Dict, Optional

try:
    from backend.synthetic_degradation import initialize_live_component, get_component_state
    HAS_DEGRADATION = True
except ImportError:
    HAS_DEGRADATION = False

try:
    from backend import rul_api
    HAS_RUL = True
except ImportError:
    HAS_RUL = False
    rul_api = None

try:
    from elasticsearch import Elasticsearch
    HAS_ELASTICSEARCH = True
except ImportError:
    HAS_ELASTICSEARCH = False

bp = Blueprint('live_component', __name__)
logger = logging.getLogger(__name__)

# Ensure RUL model is loaded
if HAS_RUL and rul_api:
    rul_api.load_rul_artifacts()


def get_state():
    """Get current component state"""
    if not HAS_DEGRADATION:
        return None
    return get_component_state()


def is_initialized():
    """Check if component is initialized"""
    state = get_state()
    return state and state.get("initialized", False)


def get_degradation_sim():
    """Get degradation simulator"""
    state = get_state()
    return state.get("degradation_sim") if state else None


def get_live_tracker():
    """Get live tracker"""
    state = get_state()
    return state.get("live_tracker") if state else None


def get_elasticsearch_client():
    """Initialize and return Elasticsearch client"""
    if not HAS_ELASTICSEARCH:
        return None

    endpoint = os.getenv('ELASTIC_ENDPOINT')
    api_key = os.getenv('ELASTIC_API_KEY')

    if not endpoint or not api_key:
        return None

    try:
        es = Elasticsearch(
            hosts=[endpoint],
            api_key=api_key,
            verify_certs=True,
            request_timeout=5
        )
        es.info()
        return es
    except Exception as e:
        logger.debug(f"⚠️ Elasticsearch unavailable: {e}")
        return None


def fetch_latest_sensor_data_from_elastic(component_id: str = "LIVE_COMPONENT_01") -> Optional[dict]:
    """
    Fetch the latest sensor reading from Elasticsearch.

    Returns a dict with sensor values that can be used to update current reading.
    Returns None if Elastic is unavailable or no data found.

    Expected Elastic index: metrics-livewire.sensors-default
    Expected fields: temperature, vibration, strain, power (from Raspberry Pi)
    """
    es = get_elasticsearch_client()
    if not es:
        return None

    try:
        # Query latest sensor data from last 5 minutes
        query = {
            "size": 1,
            "sort": [{"@timestamp": {"order": "desc"}}],
            "query": {
                "bool": {
                    "must": [
                        {"range": {"@timestamp": {"gte": "now-5m"}}}
                    ]
                }
            }
        }

        result = es.search(index="metrics-livewire.sensors-default", body=query)
        hits = result.get("hits", {}).get("hits", [])

        if not hits:
            return None

        latest = hits[0]["_source"]

        # Map Elastic sensor fields to our 21-sensor format
        # For now, use the available sensor values and preserve the structure
        return {
            "temperature": latest.get("temperature", 350.0),
            "vibration": latest.get("vibration", 100.0),
            "strain": latest.get("strain", 100.0),
            "power": latest.get("power", 1000.0),
            "timestamp": latest.get("@timestamp"),
            "from_elastic": True
        }

    except Exception as e:
        logger.debug(f"Failed to fetch from Elastic: {e}")
        return None


def build_sensor_reading_from_elastic(elastic_data: dict, baseline_reading: dict) -> dict:
    """
    Build a complete sensor reading by merging Elastic real-time data with baseline structure.

    Elastic provides: temperature, vibration, strain, power
    We need to map these to our 21-sensor format using the baseline structure.

    Args:
        elastic_data: Real-time sensor data from Elasticsearch (temperature, vibration, strain, power)
        baseline_reading: Template sensor reading with all 21 sensors + operational settings

    Returns:
        Complete sensor reading dict with updated sensor values from Elastic
    """
    if not elastic_data or not baseline_reading:
        return baseline_reading

    # Make a copy to avoid modifying the original
    updated = baseline_reading.copy()

    # Map Elastic fields to our sensor model
    # We'll scale the Elastic values proportionally to the baseline range

    # Temperature (typically sensor_2 in our model, range 350-500)
    if "temperature" in elastic_data:
        # Elastic temp range: 15-45°C, map to our 350-500 range
        elastic_temp = elastic_data["temperature"]
        scaled_temp = 350 + (elastic_temp - 15) * (500 - 350) / (45 - 15)
        updated["sensor_2"] = max(350, min(500, scaled_temp))

    # Vibration (typically sensor_1, range 100-150)
    if "vibration" in elastic_data:
        # Elastic vibration range: 0.05-2.0 g-force, map to 100-150
        elastic_vib = elastic_data["vibration"]
        scaled_vib = 100 + (elastic_vib - 0.05) * (150 - 100) / (2.0 - 0.05)
        updated["sensor_1"] = max(100, min(150, scaled_vib))

    # Strain (typically sensor_3, range 50-200 or similar)
    if "strain" in elastic_data:
        elastic_strain = elastic_data["strain"]
        # Assume elastic strain range is 50-500 microstrain, map to sensor scale
        updated["sensor_3"] = max(50, min(500, elastic_strain))

    # Power/Load (might map to operational setting or additional sensor)
    if "power" in elastic_data:
        # Power: 800-1500W, normalize to 0-1 range for op_setting_3
        elastic_power = elastic_data["power"]
        normalized_power = (elastic_power - 800) / (1500 - 800)
        updated["op_setting_3"] = max(0.0, min(1.0, normalized_power))

    return updated


def recalculate_rul(sensor_readings: dict, historical_readings: list = None) -> Optional[dict]:
    """
    Recalculate RUL for given sensor readings using the RUL model.

    Args:
        sensor_readings: Dict with sensor_1...21, op_setting_1-3, time_cycles, max_cycles
        historical_readings: List of previous readings for trend calculation (optional)

    Returns:
        RUL prediction dict with rul_hours, rul_cycles, risk_zone, risk_score, confidence
        Or None if RUL model not available
    """
    if not HAS_RUL or not rul_api or not rul_api.rul_model:
        logger.warning("⚠️ RUL model not loaded, cannot recalculate")
        return None

    try:
        import numpy as np

        # Get historical data for trend calculation if available
        previous_readings = None
        if historical_readings:
            # Use last 20 readings for trend calculation
            previous_readings = historical_readings[-20:] if len(historical_readings) > 20 else historical_readings

        # Engineer features from sensor readings
        X = rul_api.engineer_features(sensor_readings, previous_readings)

        # Scale features
        X_scaled = rul_api.rul_scaler.transform(X.reshape(1, -1))

        # Make prediction
        rul_cycles = float(rul_api.rul_model.predict(X_scaled)[0])
        rul_cycles = max(0, rul_cycles)  # Ensure non-negative

        # Convert to hours (1 cycle = 1 hour for power grid)
        rul_hours = rul_cycles
        rul_days = rul_cycles / 24.0

        # Calculate confidence (ensemble uncertainty)
        predictions_all = np.array([tree.predict(X_scaled) for tree in rul_api.rul_model.estimators_[:, 0]])
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

        return {
            "rul_cycles": round(rul_cycles, 2),
            "rul_hours": round(rul_hours, 2),
            "rul_days": round(rul_days, 2),
            "confidence": round(confidence, 3),
            "risk_zone": risk_zone,
            "risk_score": round(risk_score, 2),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    except Exception as e:
        logger.error(f"❌ RUL recalculation failed: {e}")
        return None


@bp.route('/api/live-component/init', methods=['POST'])
def init_live_component():
    """
    Initialize the live component system with historical data.

    Request JSON (optional):
    {
        "component_id": "LIVE_COMPONENT_01",
        "total_days": 35
    }

    Returns:
    {
        "status": "initialized",
        "component_id": "LIVE_COMPONENT_01",
        "historical_readings": 840,
        "summary": { ... }
    }
    """
    try:
        data = request.get_json() or {}
        component_id = data.get("component_id", "LIVE_COMPONENT_01")
        total_days = data.get("total_days", 35)

        logger.info(f"🔧 Initializing live component: {component_id}")

        # Initialize the system
        sim, tracker = initialize_live_component(component_id, total_days)

        # Get summary
        summary = sim.get_degradation_summary()
        df = sim.get_historical_df()

        # Initialize RUL prediction from the last historical reading
        last_reading = sim.get_latest_reading()
        if last_reading:
            historical_readings = df.to_dict('records')
            rul_prediction = recalculate_rul(last_reading, historical_readings)
            if rul_prediction:
                tracker.rul_prediction = rul_prediction
                tracker.current_reading = last_reading
                tracker.last_update = datetime.utcnow()
                logger.info(f"✅ Initial RUL calculated: {rul_prediction['rul_hours']:.1f}h ({rul_prediction['risk_zone']})")

        return jsonify({
            "status": "initialized",
            "component_id": component_id,
            "location": tracker.location,
            "historical_readings": len(df),
            "simulation_period_days": total_days,
            "initial_rul_cycles": summary["initial_rul_cycles"],
            "final_rul_cycles": summary["final_rul_cycles"],
            "current_rul_hours": tracker.rul_prediction.get("rul_hours") if tracker.rul_prediction else None,
            "current_risk_zone": tracker.rul_prediction.get("risk_zone") if tracker.rul_prediction else None,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 200

    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}")
        return jsonify({"error": str(e), "status": "failed"}), 500


@bp.route('/api/live-component/status', methods=['GET'])
def get_live_component_status():
    """
    Get current status of the live component.

    First tries to fetch latest sensor data from Elasticsearch.
    If Elastic data is available, recalculates RUL using:
      - 35-day synthetic historical baseline
      - Latest real sensor data from Elastic

    Returns:
    {
        "component_id": "LIVE_COMPONENT_01",
        "location": { "lat": 34.0522, "lon": -118.2437 },
        "current_reading": { sensor_1, sensor_2, ... },
        "rul_prediction": { rul_hours, risk_zone, ... },
        "data_source": "elastic" or "synthetic",
        "last_update": "2025-10-26T11:30:00Z"
    }
    """
    try:
        if not is_initialized():
            return jsonify({"error": "Component not initialized", "status": "uninitialized"}), 400

        tracker = get_live_tracker()
        sim = get_degradation_sim()

        # Try to fetch latest sensor data from Elasticsearch
        elastic_data = fetch_latest_sensor_data_from_elastic()
        data_source = "synthetic"

        if elastic_data:
            # We have real hardware data from Elastic
            # Merge it with our baseline structure and recalculate RUL
            baseline_reading = tracker.current_reading or sim.get_latest_reading()
            if baseline_reading:
                # Build complete sensor reading from Elastic data + baseline structure
                updated_reading = build_sensor_reading_from_elastic(elastic_data, baseline_reading)

                # Get historical data for feature engineering
                df = sim.get_historical_df()
                historical_readings = df.to_dict('records') if df is not None else None

                # Recalculate RUL with the merged data
                new_rul = recalculate_rul(updated_reading, historical_readings)
                if new_rul:
                    tracker.current_reading = updated_reading
                    tracker.rul_prediction = new_rul
                    tracker.last_update = datetime.utcnow()
                    data_source = "elastic"
                    logger.info(f"✅ RUL updated from Elastic: {new_rul['rul_hours']:.1f}h ({new_rul['risk_zone']})")

        state = tracker.get_state()
        return jsonify({
            **state,
            "data_source": data_source,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 200

    except Exception as e:
        logger.error(f"❌ Failed to get status: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route('/api/live-component/history', methods=['GET'])
def get_live_component_history():
    """
    Get historical degradation data for the live component.

    Query params:
      - days: Number of days to return (default: all)
      - interval: Every Nth reading (default: 1 = every reading)

    Returns:
    {
        "component_id": "LIVE_COMPONENT_01",
        "readings": [ { timestamp, sensor_1...21, rul_true }, ... ],
        "count": 840
    }
    """
    try:
        if not is_initialized():
            return jsonify({"error": "Component not initialized"}), 400

        sim = get_degradation_sim()
        days = int(request.args.get("days", 999))
        interval = int(request.args.get("interval", 1))

        df = sim.get_historical_df()

        # Filter by days if requested
        if days < 999:
            cutoff_idx = max(0, len(df) - (days * 12))  # Assuming 12 readings/day
            df = df.iloc[cutoff_idx:]

        # Sample by interval
        if interval > 1:
            df = df.iloc[::interval]

        # Convert to list of dicts
        readings = df.to_dict('records')

        return jsonify({
            "component_id": sim.component_id,
            "readings": readings,
            "count": len(readings),
            "total_days": sim.total_days,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 200

    except Exception as e:
        logger.error(f"❌ Failed to get history: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route('/api/live-component/update-hardware', methods=['POST'])
def update_hardware_state():
    """
    Update the live component with new hardware readings.

    This simulates what would come from the Raspberry Pi.

    Request JSON:
    {
        "sensor_readings": {
            "sensor_1": 125.5,
            ...,
            "sensor_21": 38.0,
            "op_setting_1": 42.5,
            "op_setting_2": 0.85,
            "op_setting_3": 105.0,
            "time_cycles": 8400
        },
        "rul_prediction": {
            "rul_cycles": 150,
            "rul_hours": 150,
            "rul_days": 6.25,
            "risk_zone": "yellow",
            "risk_score": 0.65,
            "confidence": 0.095
        }
    }

    Returns:
    {
        "status": "updated",
        "component_id": "LIVE_COMPONENT_01",
        "timestamp": "2025-10-26T11:30:00Z"
    }
    """
    try:
        if not is_initialized():
            return jsonify({"error": "Component not initialized"}), 400

        tracker = get_live_tracker()
        data = request.get_json()

        if "sensor_readings" not in data or "rul_prediction" not in data:
            return jsonify({"error": "Missing sensor_readings or rul_prediction"}), 400

        sensor_readings = data["sensor_readings"]
        rul_prediction = data["rul_prediction"]

        # Update the tracker
        tracker.update_from_hardware(sensor_readings, rul_prediction)

        logger.info(f"✅ Updated hardware state: RUL={rul_prediction.get('rul_hours')}h ({rul_prediction.get('risk_zone')})")

        return jsonify({
            "status": "updated",
            "component_id": tracker.component_id,
            "rul_prediction": rul_prediction,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 200

    except Exception as e:
        logger.error(f"❌ Failed to update hardware: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route('/api/live-component/simulate-stress', methods=['POST'])
def simulate_hardware_stress():
    """
    Simulate hardware stress (temperature increase, vibration spike, etc.)

    This takes the current state, modifies sensors, and recalculates RUL to show impact.

    Request JSON:
    {
        "stress_type": "temperature",  # or "vibration", "strain", "all"
        "magnitude": 10.0  # Percentage increase (0-100)
    }

    Returns:
    {
        "status": "stressed",
        "stress_type": "temperature",
        "magnitude": 10.0,
        "baseline_rul": { ... },
        "stressed_rul": { ... },
        "rul_change_hours": -5.2,
        "rul_change_percent": -3.15,
        "message": "Temperature increased by 10%"
    }
    """
    try:
        if not is_initialized():
            return jsonify({"error": "Component not initialized"}), 400

        tracker = get_live_tracker()
        sim = get_degradation_sim()
        data = request.get_json()
        stress_type = data.get("stress_type", "temperature")
        magnitude = min(100, max(0, float(data.get("magnitude", 5))))  # 0-100%

        current = tracker.current_reading
        if not current:
            return jsonify({"error": "No current reading available"}), 400

        # Get baseline RUL before stress
        baseline_rul = tracker.rul_prediction
        if not baseline_rul:
            return jsonify({"error": "No baseline RUL available"}), 400

        # Create modified sensor readings
        modified = current.copy()

        # Apply stress based on type
        if stress_type in ["temperature", "all"]:
            # Increase temperature-related sensors (2, 3)
            modified["sensor_2"] = modified.get("sensor_2", 400) * (1 + magnitude / 100)
            modified["sensor_3"] = modified.get("sensor_3", 500) * (1 + magnitude / 100)

        if stress_type in ["vibration", "all"]:
            # Increase vibration sensors (1, 4, 5)
            modified["sensor_1"] = modified.get("sensor_1", 125) * (1 + magnitude / 100)
            modified["sensor_4"] = modified.get("sensor_4", 100) * (1 + magnitude / 100)
            modified["sensor_5"] = modified.get("sensor_5", 60) * (1 + magnitude / 100)

        if stress_type in ["strain", "all"]:
            # Increase strain sensors (6-10)
            for i in range(6, 11):
                key = f"sensor_{i}"
                modified[key] = modified.get(key, 50) * (1 + magnitude / 100)

        # Get historical data for trend calculation
        historical_readings = None
        if sim:
            df = sim.get_historical_df()
            # Convert to list of dicts for trend calculation
            historical_readings = df.to_dict('records')

        # Recalculate RUL with stressed sensors
        stressed_rul = recalculate_rul(modified, historical_readings)

        if not stressed_rul:
            return jsonify({"error": "Failed to recalculate RUL"}), 500

        # Calculate change
        baseline_hours = baseline_rul.get("rul_hours", 0)
        stressed_hours = stressed_rul.get("rul_hours", 0)
        rul_change_hours = stressed_hours - baseline_hours
        rul_change_percent = (rul_change_hours / baseline_hours * 100) if baseline_hours > 0 else 0

        # Update tracker with new RUL prediction
        tracker.rul_prediction = stressed_rul
        tracker.current_reading = modified
        tracker.last_update = datetime.utcnow()

        logger.info(f"✅ Stress applied: {stress_type} +{magnitude}% | RUL: {baseline_hours:.1f}h → {stressed_hours:.1f}h (Δ {rul_change_hours:+.1f}h, {rul_change_percent:+.2f}%)")

        message = f"{stress_type.capitalize()} increased by {magnitude:.1f}%"

        return jsonify({
            "status": "stressed",
            "stress_type": stress_type,
            "magnitude": magnitude,
            "message": message,
            "baseline_rul": baseline_rul,
            "stressed_rul": stressed_rul,
            "rul_change": {
                "hours": round(rul_change_hours, 2),
                "percent": round(rul_change_percent, 2),
                "direction": "decreased" if rul_change_hours < 0 else "increased"
            },
            "modified_sensors": {k: v for k, v in modified.items() if k.startswith("sensor_")},
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 200

    except Exception as e:
        logger.error(f"❌ Failed to simulate stress: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route('/api/live-component/summary', methods=['GET'])
def get_component_summary():
    """
    Get a complete summary of the live component system.

    Returns:
    {
        "component_id": "LIVE_COMPONENT_01",
        "location": { ... },
        "historical_data": {
            "total_readings": 840,
            "days_of_data": 35,
            "initial_rul": 8400,
            "final_rul": 0
        },
        "current_state": {
            "timestamp": "...",
            "rul_hours": 150,
            "risk_zone": "yellow"
        }
    }
    """
    try:
        if not is_initialized():
            return jsonify({"error": "Component not initialized"}), 400

        sim = get_degradation_sim()
        tracker = get_live_tracker()
        summary = sim.get_degradation_summary()
        state = tracker.get_state()
        df = sim.get_historical_df()

        return jsonify({
            "component_id": sim.component_id,
            "location": tracker.location,
            "historical_data": {
                "total_readings": len(df),
                "days_of_data": sim.total_days,
                "initial_rul_cycles": summary["initial_rul_cycles"],
                "final_rul_cycles": summary["final_rul_cycles"],
                "rul_range": f"{summary['final_rul_cycles']} to {summary['initial_rul_cycles']} cycles"
            },
            "current_state": {
                "timestamp": state.get("last_update"),
                "rul_hours": state.get("rul_prediction", {}).get("rul_hours"),
                "risk_zone": state.get("rul_prediction", {}).get("risk_zone")
            },
            "api_endpoints": {
                "init": "POST /api/live-component/init",
                "status": "GET /api/live-component/status",
                "history": "GET /api/live-component/history",
                "update_hardware": "POST /api/live-component/update-hardware",
                "simulate_stress": "POST /api/live-component/simulate-stress"
            }
        }), 200

    except Exception as e:
        logger.error(f"❌ Failed to get summary: {e}")
        return jsonify({"error": str(e)}), 500
