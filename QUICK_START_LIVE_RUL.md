# Quick Start: Live RUL Monitoring Demo

**Last Updated**: October 26, 2025
**Status**: ✅ Ready to Deploy

---

## TL;DR - What Was Built

A **real-time RUL monitoring system** that shows your Raspberry Pi sensor data impacting the remaining useful life calculation in real-time.

### The Demo Story
1. Click sensor on map
2. Panel opens showing "📡 LIVE DATA" badge
3. Watch RUL countdown update every 2 seconds
4. See live 5-minute trend chart
5. **Temperature goes up → RUL goes down** (live!)
6. Stress indicators show which sensors are elevated
7. Map sensor point color changes (green → yellow → red)

---

## What Changed

### Backend: 3 New Response Fields

Your `/api/live-component/status` now returns:

```json
{
  "data_source": "elastic",          // "elastic" or "synthetic"
  "elastic_available": true,         // Is Pi data available?
  "rul_change_from_baseline": {      // How much RUL changed
    "hours": -0.5,
    "percent": -2.1,
    "direction": "decreasing"
  },
  "stress_indicators": {             // Which sensors are stressed?
    "temperature": {
      "status": "elevated",          // "normal" | "elevated" | "critical"
      "delta": 50.5,                 // Changed by 50.5 units
      "delta_percent": 11.9          // Changed by 11.9%
    },
    "vibration": { ... },
    "frequency": { ... }
  },
  "sensor_deltas": {                 // All sensor changes
    "sensor_1": { "delta": 5.2, ... },
    ...
  }
  // ... rest of response
}
```

### Frontend: 5 New Features

1. **Data Source Badge** - Shows "LIVE" or "BASELINE"
2. **RUL Change Badge** - Shows delta from baseline with ↓↑ indicator
3. **Stress Indicators** - Color-coded sensor status (🟢🟡🔴)
4. **Live RUL Trend** - 5-minute rolling chart of RUL changes
5. **Adaptive Polling** - 2-second refresh for Elasticsearch, 10-second for synthetic

### Map: Dynamic Sensor Coloring

Sensor point on map changes color based on RUL:
- 🟢 **Green**: >72 hours remaining
- 🟡 **Yellow**: 24-72 hours remaining
- 🟠 **Orange**: 14-24 hours remaining
- 🔴 **Red**: <14 hours remaining

---

## How to Test It

### Setup

```bash
# 1. Start backend
python web_dashboard.py
# → Backend running on http://localhost:5000

# 2. Start frontend
cd frontend
npm start
# → Frontend running on http://localhost:3000
```

### Test Without Real Hardware

```bash
# 1. Open http://localhost:3000
# 2. Navigate to San Francisco map
# 3. Click the sensor point (green dot on transmission line)
# 4. Panel opens with "Simulated baseline data"
# 5. RUL stays constant (no Pi data)
# 6. Updates every 10 seconds
```

### Test With Real Pi Data (If Available)

```bash
# 1. Ensure Pi is sending to Elasticsearch:
#    - Temperature, Vibration, Strain in sensor_data
#    - Correct index: metrics-livewire.sensors-default

# 2. Check env vars are set:
export ELASTIC_ENDPOINT="https://..."
export ELASTIC_API_KEY="..."

# 3. Restart backend to pick up env vars
python web_dashboard.py

# 4. Open panel again
# 5. Should see "LIVE DATA" badge
# 6. Updates every 2 seconds
# 7. RUL changes as sensor data changes
```

---

## Demo Script (5 Minutes)

### Act 1: Show Live Data Source (1 min)
```
1. Open map, click sensor
2. "Notice the green LIVE DATA badge at the top"
3. "This means the system found real sensor data from the Pi"
4. "We're polling Elasticsearch every 2 seconds"
```

### Act 2: Show Live RUL Countdown (1.5 min)
```
1. Point to large RUL number (e.g., "39.2h")
2. "This is how much time this component has left"
3. "It updates every 2 seconds with live data"
4. Point to change badge "↓ 2.1%"
5. "This shows how much RUL changed from baseline"
6. Open DevTools Network tab, watch status requests come in
```

### Act 3: Show Real-Time Trend (1.5 min)
```
1. Point to "Live RUL Trend (5 Minutes)" chart
2. "This shows the last 5 minutes of RUL history"
3. "Watch it update in real-time"
4. Close/reopen panel to see new trend data
5. Mention: "If temperature keeps increasing, RUL keeps dropping"
```

### Act 4: Show Stress Indicators (1 min)
```
1. Point to Current Readings section
2. Show Temperature "🟡 +11.9%"
3. "This sensor is elevated compared to baseline"
4. Show color-coded indicators
5. "If it gets critical, you'd see 🔴"
```

---

## Key Metrics

| Metric | Value | Meaning |
|--------|-------|---------|
| Polling Interval | 2-10 seconds | Faster for live, slower for baseline |
| Trend Window | 5 minutes | Rolling window of recent RUL |
| Backend Calc | <100ms | Quick RUL recalculation |
| Model Sensitivity | ~0.5-2% per 10°C | Expected behavior (see docs) |
| Data Source Detection | Automatic | System auto-detects Pi data |

---

## Troubleshooting

### I see "Simulated baseline data" but want "LIVE DATA"

**Check Pi is sending data:**
```bash
# If using Elasticsearch locally:
curl http://localhost:9200/metrics-livewire.sensors-default/_search | jq '.hits.hits | .[0]._source'
```

**Check env vars:**
```bash
echo $ELASTIC_ENDPOINT
echo $ELASTIC_API_KEY
# Both should be set
```

**Check backend logs:**
```bash
# Look for "✅ RUL updated from Elastic:" or "Failed to fetch from Elastic"
```

### RUL not changing when I change sensors

**This is expected!** The RUL model is 88% driven by time, not sensors.
- See: `/Users/Vanya/dev/LiveWire/SENSITIVITY_ANALYSIS.md`
- A 10°C temperature increase = ~0.5-2% RUL change
- This is correct for power grid components

### Chart shows wrong data

**Try:**
1. Hard refresh: Cmd+Shift+R (Mac) or Ctrl+Shift+R (Windows)
2. Close panel with X button
3. Click sensor again

---

## Files Modified

| File | Change | Impact |
|------|--------|--------|
| `backend/live_component_api.py` | Added RUL change tracking | Status endpoint now richer |
| `frontend/SensorDetailsPanel.js` | Complete rewrite | Live data display |
| `frontend/SensorDetailsPanel.css` | Major enhancement | New UI for live features |
| `frontend/SensorPointLayer.js` | Enhanced coloring | Map sensor responds to RUL |

---

## Next Steps

1. **Test with real Pi data** if you have it
2. **Show to stakeholders** as proof of concept
3. **Integrate alerting** (optional enhancement)
4. **Add data export** (optional enhancement)

---

## Documentation

- **Full details**: `/Users/Vanya/dev/LiveWire/PHASE_4_LIVE_RUL_MONITORING.md`
- **Implementation plan**: `/Users/Vanya/dev/LiveWire/IMPLEMENTATION_PLAN.md`
- **Phase 3 reference**: `/Users/Vanya/dev/LiveWire/PHASE_3_IMPLEMENTATION_SUMMARY.md`
- **Model details**: `/Users/Vanya/dev/LiveWire/PREDICTIVE_MODELS_OVERVIEW.md`

---

**Status**: ✅ Ready for Demo
**Deployed**: October 26, 2025
