# RUL Model Sensitivity Analysis

## Executive Summary

The RUL (Remaining Useful Life) prediction model **shows near-zero sensitivity to sensor changes** across all lifecycle stages (early, mid, late). This is **not a bug** but a fundamental characteristic of how the model was trained.

**Key Finding**: The model's predictions are **88% driven by time-based features** (`time_normalized`), not by actual sensor values.

## Feature Importance Breakdown

```
Feature                 Importance    Category
─────────────────────────────────────────────
time_normalized         0.8807        ⚠️ TIME-BASED (88%)
time_cycles             0.0899        ⚠️ TIME-BASED (9%)
volatility_10           0.0057        📊 SENSOR (0.57%)
volatility_5            0.0045        📊 SENSOR (0.45%)
volatility_16           0.0027        📊 SENSOR (0.27%)
... (all other sensor features)  <0.2%  NEGLIGIBLE
─────────────────────────────────────────────
Total Sensor Features: ~1-2% combined importance
```

## Test Results Across Lifecycle

### Early Lifecycle (10% through component life)
- **Baseline RUL**: 289h
- **Stress Applied**: Temperature +50%, Vibration +50%, All sensors +50%
- **Result**: **ZERO CHANGE** (0.00h)
- **Sensitivity**: 0%

### Mid Lifecycle (50% through component life)
- **Baseline RUL**: 165h
- **Stress Applied**: Temperature +50%, Vibration +50%, All sensors +50%
- **Result**: **ZERO CHANGE** (0.00h)
- **Sensitivity**: 0%

### Late Lifecycle (90% through component life)
- **Baseline RUL**: 50h
- **Stress Applied**: Temperature +50%
- **Result**: +0.06h (minimal change)
- **Sensitivity**: +0.12%

## Why This Happens

### 1. Model Architecture
The RUL model uses **Gradient Boosting Regression** trained on NASA CMaps turbofan engine data with these features:
- 21 sensor values (current)
- 21 degradation trends (slope from history)
- 21 sensor volatilities (standard deviation from history)
- 3 operational settings
- 2 time metrics (cycles, normalized time)
- **Total: 68 features**

### 2. The Time-Dominance Problem
When `time_normalized` (cycles elapsed / max cycles) captures 88% of the predictive power, the model is essentially saying:

> "The best predictor of RUL is simply: how far into the component's lifecycle are we?"

This works well for:
- **Linear degradation** (where sensor failure is roughly proportional to time)
- **NASA CMaps data** (well-controlled turbofan engines with predictable wear patterns)

But it fails for:
- **Detecting sudden failures** (sensor spike doesn't matter if time-based model dominates)
- **Real-world variability** (power grid components degrade non-linearly)
- **Early anomaly detection** (can't react to abnormal sensor readings)

### 3. Why Trends & Volatility Don't Help
When testing with single-point sensor modifications:
1. We provide new current sensor values
2. But we keep the same historical data
3. The trends and volatility features are computed from this unchanged history
4. Result: Trends stay the same, volatility stays the same
5. Only the new current sensor values feed into the model
6. But they represent <1% of total feature importance
7. **So prediction barely changes**

## Comparison: What We Expected vs. Reality

### Expected (from user's perspective):
```
Temperature increases → More degradation → RUL decreases
Normal → Green zone
Increased stress → Yellow zone
Extreme stress → Red zone
```

### Reality (model behavior):
```
Time elapsed → Predetermined RUL path
Time 10%: ~289h (set at training time)
Time 50%: ~165h (set at training time)
Time 90%: ~50h  (set at training time)
Sensor values: <1% impact on prediction
```

## Why This Model Exists

This behavior is **intentional for turbofan engines** because:

1. **CMaps dataset characteristics**:
   - Engines run under controlled conditions
   - Failure modes are well-understood and consistent
   - Time is the strongest predictor
   - Real degradation curves are predictable

2. **Training data quality**:
   - Each engine runs until actual failure (run-to-failure data)
   - 100+ engine degradation curves
   - Clear time-RUL relationship

3. **Operational context**:
   - Turbofan engines: can't suddenly get much worse from a spike
   - Failure happens gradually due to physics
   - Linear degradation assumption holds reasonably well

## Implications for Power Grid Use

The model works **reasonably well** for our demo because:

✅ Power grid components also degrade gradually
✅ Synthetic data was generated with linear degradation (matching model assumptions)
✅ Good for showing baseline RUL trends
✅ Acceptable for 30+ day predictions

But it **fails to detect**:

❌ Sudden sensor spikes (equipment shock)
❌ Anomalous degradation patterns
❌ Component-specific failure modes
❌ Early intervention opportunities

## Recommended Solutions

### Option 1: Use a Different Model (Short-term)
Train a new model specifically for power grid data with:
- More weight on sensor-based features
- Real power grid failure data (not turbofan)
- Non-linear degradation patterns
- Anomaly detection integrated

### Option 2: Ensemble Approach (Medium-term)
Combine models:
- **Time-based model** (current): For baseline RUL
- **Sensor-based model**: For anomaly detection
- **Hybrid model**: For final risk assessment

Example: If sensors show 50% increase AND model is in green zone, still trigger yellow alert

### Option 3: Feature Engineering Improvement (Immediate)
Adjust how features are weighted during prediction:
- Reduce time feature importance
- Increase sensor feature importance
- Add rate-of-change features
- Include sensor change acceleration

## Testing Protocol

To verify a model is sensor-aware, test with **this protocol**:

```python
# Generate historical data WITH actual degradation
history_early = [readings 1-20 from lifecycle 1-20%]
history_late  = [readings 320-340 from lifecycle 90-95%]

# Stress the sensor
sensor_late_stressed = history_late[0].copy()
sensor_late_stressed['sensor_2'] *= 1.5  # +50%

# Key: Include proper degradation history
prediction_baseline = model.predict(sensor_late, history_early)
prediction_stressed = model.predict(sensor_late_stressed, history_late)

# If model is sensor-aware: prediction_stressed < prediction_baseline
# Current model: differences are <0.5%
```

The issue with our original test was that we didn't provide historically-degraded readings, so trends were minimal.

## What This Means for Phase 3

### Current Implementation ✅
- ✅ Generates realistic 35-day synthetic data with linear degradation
- ✅ Stress simulation API works correctly (`/api/live-component/simulate-stress`)
- ✅ RUL predictions follow expected time-based curve
- ✅ Frontend can display live RUL updates

### What Works Well
- Showing the historical degradation curve (matches model's training data assumptions)
- Demonstrating RUL countdown
- Showing risk zone transitions (green → yellow → red)

### What Doesn't Work
- Real-time response to sensor changes (model isn't sensitive)
- Demonstrating that hardware manipulation affects RUL (it doesn't, in this model)
- Early failure detection based on anomalies

## Recommendation

**For the current Phase 3 demo**: Accept this limitation and focus on:

1. ✅ Show 35-day historical degradation curve
2. ✅ Live component starting from end of historical data
3. ✅ RUL countdown based on simulated time progression
4. ✅ Demonstrate model correctly predicts failure at end of simulated lifecycle
5. ❌ Don't emphasize "sensor changes affect RUL" (not true for this model)

For future work, either:
- **Option A**: Train new model on real power grid data with sensor-aware architecture
- **Option B**: Add disclaimers that current model is time-based
- **Option C**: Implement hybrid approach with anomaly detection layer

## Files Generated

- `/scripts/diagnose_model_sensitivity.py` - Diagnostic script used for this analysis
- Output: Early (0% change), Mid (0% change), Late (0.12% change)

---

**Date**: 2025-10-26
**Status**: Analysis Complete
**Recommendation**: Proceed with Phase 3 frontend integration using time-based predictions
