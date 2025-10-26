"""
Diagnose RUL Model Sensitivity Across Component Lifecycle
=========================================================

Tests the model's responsiveness to sensor changes at different stages:
- Early lifecycle (healthy component, high RUL)
- Mid lifecycle (degraded, moderate RUL)
- Late lifecycle (heavily degraded, low RUL)

Investigates why sensor changes show low sensitivity.
"""

import sys
import os

# Set up path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)
os.chdir(project_root)

import numpy as np
import pandas as pd
from backend.synthetic_degradation import SyntheticComponentSimulator
from backend import rul_api
import joblib

# Load model
rul_api.load_rul_artifacts()

if not rul_api.rul_model:
    print("❌ Failed to load RUL model")
    print(f"   Current dir: {os.getcwd()}")
    print(f"   Artifact dir: {os.path.join(project_root, 'models', 'artifacts')}")
    sys.exit(1)

print("="*70)
print("RUL MODEL SENSITIVITY DIAGNOSTIC")
print("="*70)

# Generate synthetic 35-day component data
print("\n🔄 Generating 35-day synthetic degradation data...")
sim = SyntheticComponentSimulator("TEST_COMPONENT", total_days=35)
df = sim.generate_readings(readings_per_day=12)

print(f"✅ Generated {len(df)} readings")
print(f"   RUL range: {df['rul_true'].min():.0f} to {df['rul_true'].max():.0f} cycles")

# Test at 3 lifecycle stages
stages = {
    "EARLY": int(len(df) * 0.1),      # 10% through lifecycle (healthy)
    "MID": int(len(df) * 0.5),        # 50% through lifecycle (degraded)
    "LATE": int(len(df) * 0.9),       # 90% through lifecycle (very degraded)
}

for stage_name, idx in stages.items():
    print(f"\n" + "="*70)
    print(f"LIFECYCLE STAGE: {stage_name} (Reading {idx}/{len(df)})")
    print("="*70)

    # Get reading at this stage
    current_row = df.iloc[idx]
    true_rul = current_row['rul_true']

    # Get history up to this point (for trend calculation)
    history_df = df.iloc[max(0, idx-20):idx+1]
    previous_readings = history_df.to_dict('records')

    # Extract sensor data
    sensor_data = {col: current_row[col] for col in df.columns if col.startswith('sensor_')}
    sensor_data.update({
        'op_setting_1': current_row['op_setting_1'],
        'op_setting_2': current_row['op_setting_2'],
        'op_setting_3': current_row['op_setting_3'],
        'time_cycles': current_row['time_cycles'],
        'max_cycles': current_row['max_cycles'],
    })

    # BASELINE: Predict RUL with unmodified sensors
    print(f"\n📊 BASELINE (Unmodified Sensors)")
    print(f"   True RUL: {true_rul:.1f} cycles")
    print(f"   Component health: {1 - (idx / len(df)):.1%}")

    X_baseline = rul_api.engineer_features(sensor_data, previous_readings)
    X_baseline_scaled = rul_api.rul_scaler.transform(X_baseline.reshape(1, -1))
    rul_baseline = float(rul_api.rul_model.predict(X_baseline_scaled)[0])

    print(f"   Predicted RUL: {rul_baseline:.2f}h")

    # Show sensor values
    print(f"\n   Sample sensor values:")
    for i in [1, 2, 3, 4, 5]:
        col = f'sensor_{i}'
        val = sensor_data.get(col, 0)
        print(f"      {col}: {val:.1f}")

    # TEST 1: Increase temperature sensors by 10%, 25%, 50%, 100%
    print(f"\n🌡️  TEMPERATURE STRESS (sensor_2, sensor_3)")
    stress_magnitudes = [10, 25, 50, 100]

    for magnitude in stress_magnitudes:
        sensor_data_stressed = sensor_data.copy()
        sensor_data_stressed['sensor_2'] *= (1 + magnitude / 100)
        sensor_data_stressed['sensor_3'] *= (1 + magnitude / 100)

        X_stressed = rul_api.engineer_features(sensor_data_stressed, previous_readings)
        X_stressed_scaled = rul_api.rul_scaler.transform(X_stressed.reshape(1, -1))
        rul_stressed = float(rul_api.rul_model.predict(X_stressed_scaled)[0])

        delta_rul = rul_stressed - rul_baseline
        delta_percent = (delta_rul / rul_baseline * 100) if rul_baseline != 0 else 0

        direction = "↓" if delta_rul < 0 else "↑"
        print(f"   +{magnitude:>3}%: {rul_stressed:>7.2f}h  |  Δ {direction} {abs(delta_rul):>6.2f}h ({delta_percent:>+6.2f}%)")

    # TEST 2: Increase vibration sensors by 10%, 25%, 50%, 100%
    print(f"\n📈 VIBRATION STRESS (sensor_1, sensor_4, sensor_5)")

    for magnitude in stress_magnitudes:
        sensor_data_stressed = sensor_data.copy()
        sensor_data_stressed['sensor_1'] *= (1 + magnitude / 100)
        sensor_data_stressed['sensor_4'] *= (1 + magnitude / 100)
        sensor_data_stressed['sensor_5'] *= (1 + magnitude / 100)

        X_stressed = rul_api.engineer_features(sensor_data_stressed, previous_readings)
        X_stressed_scaled = rul_api.rul_scaler.transform(X_stressed.reshape(1, -1))
        rul_stressed = float(rul_api.rul_model.predict(X_stressed_scaled)[0])

        delta_rul = rul_stressed - rul_baseline
        delta_percent = (delta_rul / rul_baseline * 100) if rul_baseline != 0 else 0

        direction = "↓" if delta_rul < 0 else "↑"
        print(f"   +{magnitude:>3}%: {rul_stressed:>7.2f}h  |  Δ {direction} {abs(delta_rul):>6.2f}h ({delta_percent:>+6.2f}%)")

    # TEST 3: Increase all sensors simultaneously
    print(f"\n⚡ ALL SENSORS STRESS (+50% to all)")

    sensor_data_stressed = sensor_data.copy()
    for key in sensor_data_stressed:
        if key.startswith('sensor_'):
            sensor_data_stressed[key] *= 1.5

    X_stressed = rul_api.engineer_features(sensor_data_stressed, previous_readings)
    X_stressed_scaled = rul_api.rul_scaler.transform(X_stressed.reshape(1, -1))
    rul_stressed = float(rul_api.rul_model.predict(X_stressed_scaled)[0])

    delta_rul = rul_stressed - rul_baseline
    delta_percent = (delta_rul / rul_baseline * 100) if rul_baseline != 0 else 0

    print(f"   Baseline: {rul_baseline:.2f}h")
    print(f"   Stressed: {rul_stressed:.2f}h")
    print(f"   Δ {delta_rul:+.2f}h ({delta_percent:+.2f}%)")

    # TEST 4: Modify operational settings
    print(f"\n⚙️  OPERATIONAL SETTINGS STRESS")

    sensor_data_stressed = sensor_data.copy()
    sensor_data_stressed['op_setting_1'] *= 1.2  # Increase temperature setpoint

    X_stressed = rul_api.engineer_features(sensor_data_stressed, previous_readings)
    X_stressed_scaled = rul_api.rul_scaler.transform(X_stressed.reshape(1, -1))
    rul_stressed = float(rul_api.rul_model.predict(X_stressed_scaled)[0])

    delta_rul = rul_stressed - rul_baseline
    delta_percent = (delta_rul / rul_baseline * 100) if rul_baseline != 0 else 0

    print(f"   Baseline: {rul_baseline:.2f}h")
    print(f"   Op_setting_1 +20%: {rul_stressed:.2f}h (Δ {delta_rul:+.2f}h, {delta_percent:+.2f}%)")

# Feature importance analysis
print(f"\n" + "="*70)
print("FEATURE IMPORTANCE ANALYSIS")
print("="*70)

if hasattr(rul_api.rul_model, 'feature_importances_'):
    importances = rul_api.rul_model.feature_importances_
    feature_names = ["sensor_" + str(i) for i in range(1, 22)]
    feature_names += ["trend_" + str(i) for i in range(1, 22)]
    feature_names += ["volatility_" + str(i) for i in range(1, 22)]
    feature_names += ["op_setting_1", "op_setting_2", "op_setting_3", "time_cycles", "time_normalized"]

    # Sort by importance
    sorted_idx = np.argsort(importances)[::-1]

    print(f"\n📊 Top 10 Most Important Features:")
    for rank, idx in enumerate(sorted_idx[:10], 1):
        if idx < len(feature_names):
            print(f"   {rank:2}. {feature_names[idx]:20} → {importances[idx]:.4f}")

print(f"\n" + "="*70)
print("SUMMARY")
print("="*70)
print("""
🔍 Low sensitivity findings:

1. **Without Historical Context**: When we apply single-point stress without
   providing updated historical data, the model can't compute proper trend and
   volatility features. These are held constant while sensors change.

2. **Feature Engineering Limitation**: The model uses:
   - Current sensor values (directly impacts prediction)
   - Degradation trends (from history - STAYS CONSTANT if history unchanged)
   - Sensor volatility (from history - STAYS CONSTANT if history unchanged)

   So a single-point sensor change is dampened by constant trend/volatility features.

3. **Recommended Fix**: To properly test sensitivity:
   - Provide historical data that ALREADY shows the degraded trend
   - Or simulate multiple readings in sequence to build new trends
   - Current testing methodology is flawed because it doesn't update trends

✅ Next Step: Test with properly constructed historical data showing
   degradation trends to see if sensitivity improves.
""")
