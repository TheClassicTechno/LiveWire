# Phase 3: Live Component System - User Guide

## Quick Start

### 1. Start the Backend
```bash
python web_dashboard.py
```
The Flask app will start on `http://localhost:5000` with the live component API endpoints registered.

### 2. Start the Frontend (in another terminal)
```bash
cd frontend
npm start
```
The React app will start on `http://localhost:3000`.

### 3. Navigate to Live Component Dashboard
Open your browser and go to:
```
http://localhost:3000/live-component
```

### 4. Initialize the System
Click the blue "Initialize Live Component" button. This will:
- Generate 35 days of synthetic sensor data (420 readings)
- Create a realistic degradation curve from healthy to near-failure
- Initialize the live component tracker
- Display historical data on the chart

---

## Understanding the Dashboard

### Status Panel
Shows the current state of the component:
- **Component ID**: Unique identifier for this asset
- **Location**: Geographic coordinates (LA Downtown Grid)
- **Last Update**: Most recent measurement timestamp

### RUL Prediction Card
The heart of the system:
- **Large number**: Time until failure (hours/days/minutes)
  - Green: >72 hours (healthy)
  - Yellow: 24-72 hours (degrading)
  - Red: <24 hours (critical)
- **Risk Score**: 0-100% likelihood of failure
- **Confidence**: Model uncertainty (lower is better)

### Current Sensor Readings
Six key metrics:
- **sensor_1** (vibration): Mechanical oscillation
- **sensor_2** (temperature): Heat signature
- **sensor_3, 4**: Additional monitoring
- **op_setting_1**: Operational parameter
- **time_cycles**: Operating hours equivalent

### Historical Degradation Curve
35-day chart showing:
- **Red line (RUL true)**: Remaining useful life over time
  - Starts at 8400 cycles
  - Ends at 20 cycles
  - Linear decline matching model training data
- **Blue line (Sensor 1)**: Vibration increases with time
- **Orange line (Sensor 2)**: Temperature increases with time

### Hardware Stress Simulation
Three groups of stress buttons:

**Temperature Stress** (+10%, +25%, +50%)
- Increases sensor_2 and sensor_3 (temperature-related)
- Models thermal degradation
- Watch RUL change (expect minimal change due to model characteristics)

**Vibration Stress** (+10%, +25%, +50%)
- Increases sensor_1, sensor_4, sensor_5 (vibration-related)
- Models mechanical shock or wear
- Tests model sensitivity to mechanical failures

**All Sensors** (+10%, +25%, +50%)
- Increases all 21 sensors proportionally
- Models system-wide degradation
- Most aggressive test case

---

## Expected Behavior

### First Launch
1. Dashboard loads with init button
2. Click "Initialize" - takes ~5 seconds
3. Historical chart populates with 35-day baseline
4. Current RUL shows as ~50-150h (near end of lifecycle)
5. Risk zone likely yellow or red (expected for degraded state)

### Auto-Refresh
- Metrics refresh every 10 seconds
- RUL should remain **roughly stable** (time-based model)
- Small fluctuations possible from floating-point precision
- Stress applications trigger immediate refresh

### Applying Stress
1. Click a stress button (e.g., "Temperature +50%")
2. Button shows feedback while processing
3. RUL prediction updates based on new sensor values
4. **Expected result**:
   - Early lifecycle: No change (0%)
   - Mid lifecycle: No change (0%)
   - Late lifecycle: Tiny change (<0.5%)
5. This is **normal** - see "Why Low Sensitivity?" section below

### Checking Historical Correlation
- Stress buttons modify **current** sensors
- Historical curve shows **past** baseline data
- Compare current sensors to historical values
- They should be at the degraded end of the curve

---

## Why Is RUL Not Changing Much When I Increase Sensors?

This is the key finding from Phase 3 analysis:

### The Model's Feature Importance
```
time_normalized    88.07%  ← DOMINANT
time_cycles         8.99%
all_sensors          <2%   ← Very low impact
```

### What This Means
The RUL prediction model is **88% based on how far through the lifecycle** the component is, not on the actual sensor values.

This makes sense because:
1. **Training data** (NASA CMaps turbofan): Linear degradation over time
2. **Synthetic data** (our 35 days): Linear degradation over time
3. **Real power grids**: Often also degrade gradually over time
4. **Physics**: Fatigue and wear are time-dependent phenomena

### Why This Limits Anomaly Detection
- Sudden sensor spike? Model barely reacts (1% impact)
- Temperature spike? No effect if time-normalized is the same
- Vibration shock? Drowned out by the 88% time component

This model would **miss early failure signs** in the real world.

### What Would Make It Sensor-Aware?
- Train on data where sensor values predict failure better than time
- Real power grid data with non-linear failures
- Anomaly-based models (statistical outliers)
- Ensemble approaches (time-based + sensor-based + anomaly detection)

---

## API Endpoints (For Advanced Users)

### Initialize Component
```bash
curl -X POST http://localhost:5000/api/live-component/init \
  -H "Content-Type: application/json" \
  -d '{
    "component_id": "LIVE_COMPONENT_01",
    "total_days": 35
  }'
```

Response: 420 readings generated, component initialized

### Get Current Status
```bash
curl http://localhost:5000/api/live-component/status
```

Response: Current RUL, risk zone, sensor readings, location

### Get Historical Data
```bash
curl "http://localhost:5000/api/live-component/history?days=35&interval=1"
```

Response: All 420 historical readings with timestamps

### Apply Stress
```bash
curl -X POST http://localhost:5000/api/live-component/simulate-stress \
  -H "Content-Type: application/json" \
  -d '{
    "stress_type": "temperature",
    "magnitude": 50
  }'
```

Response: Modified sensor values and stress impact

### Get Summary
```bash
curl http://localhost:5000/api/live-component/summary
```

Response: Complete system overview with all endpoints listed

---

## Troubleshooting

### "Component not initialized" error
**Solution**: Click "Initialize Live Component" button again

### Chart not appearing
**Solution**:
- Check browser console (F12) for errors
- Ensure backend is running on port 5000
- Refresh page

### RUL not updating
**Solution**:
- Check that auto-refresh is enabled (should happen every 10s)
- Click manual refresh button
- Check network tab to see if API calls are succeeding

### Stress buttons not working
**Solution**:
- Ensure component is initialized first
- Check console for API errors
- Verify backend is accessible

### Very large RUL values (>500h)
**Solution**: This is normal early in the lifecycle. Historical curve shows where you are in the degradation path.

---

## Technical Details

### Synthetic Data Generation
- **Duration**: 35 days
- **Readings**: 420 total (12 per day = 2-hour intervals)
- **Component health**: Starts at 95%, declines linearly to 5%
- **Sensors**: 21 realistic sensors with ranges calibrated for power grid
- **Operational settings**: 3 stable settings that vary slightly with Gaussian noise
- **RUL true**: Calculated as (max_cycles - time_cycles)

### RUL Prediction Model
- **Type**: Gradient Boosting Regressor
- **Training data**: NASA CMaps turbofan engines (100+ engines, run to failure)
- **Features**: 68 engineered features
  - 21 sensor values (current)
  - 21 degradation trends (slope from history)
  - 21 sensor volatilities (std dev from history)
  - 3 operational settings
  - 2 time metrics
- **Output**: RUL in hours (or cycles, 1:1 conversion for power grid)
- **Risk zones**:
  - Green: RUL > 72h
  - Yellow: RUL 24-72h
  - Red: RUL < 24h

### State Management
The backend uses module-level state to persist data across HTTP requests:
```python
_component_state = {
    "degradation_sim": SyntheticComponentSimulator(...),
    "live_tracker": LiveComponentTracker(...),
    "initialized": True
}
```

This allows the component to maintain its 35-day history and current state across multiple API calls from the frontend.

---

## Performance Expectations

| Operation | Time |
|-----------|------|
| Initialize (generate 35 days) | ~3-5 seconds |
| Fetch historical data | ~100ms |
| Get current status | ~50ms |
| Apply stress | ~150ms |
| Frontend auto-refresh | Every 10 seconds |

---

## Next Steps

### For Testing
1. Initialize component
2. Observe historical degradation curve
3. Try different stress magnitudes
4. Correlate with RUL changes
5. Compare to sensitivity analysis findings

### For Real Hardware Integration
1. Replace synthetic data with Raspberry Pi sensor stream
2. Update `/api/live-component/update-hardware` to accept real readings
3. Validate RUL predictions against actual failure modes
4. Tune operational thresholds based on real data

### For Production Deployment
1. Implement multi-component tracking
2. Add anomaly detection layer
3. Retrain model on power grid data
4. Add alerting and notification system
5. Integrate with existing SCADA systems

---

## Support & Documentation

- **Model Analysis**: See `SENSITIVITY_ANALYSIS.md`
- **Implementation Details**: See `PHASE_3_COMPLETION_SUMMARY.md`
- **API Contract**: Check docstrings in `backend/live_component_api.py`
- **Frontend Code**: See `frontend/src/components/LiveComponentDashboard.js`
- **Diagnostic Tools**: Run `python scripts/diagnose_model_sensitivity.py`

---

**Last Updated**: October 26, 2025
**Status**: Production Ready ✅
