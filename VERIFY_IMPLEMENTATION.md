# How to Verify the Live RUL Monitoring Implementation

**Date**: October 26, 2025

---

## What You Have

A complete, working system that:
1. ✅ Fetches real sensor data from Elasticsearch (or uses synthetic baseline)
2. ✅ Recalculates RUL in real-time with live sensor values
3. ✅ Displays live RUL updates every 2 seconds (Elasticsearch) or 10 seconds (baseline)
4. ✅ Shows which sensors are stressed (temperature, vibration, strain)
5. ✅ Tracks RUL changes from baseline
6. ✅ Visualizes 5-minute RUL trend in real-time
7. ✅ Indicates data source (LIVE vs BASELINE)

---

## Step-by-Step Verification

### Step 1: Start the Backend

```bash
# From project root
python web_dashboard.py
```

**Expected Output**:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
 * WARNING: This is a development server...
```

If you see Flask errors, there's a Python issue. Check logs.

### Step 2: Start the Frontend

```bash
# In another terminal
cd frontend
npm start
```

**Expected Output**:
```
Compiled successfully!

You can now view livewire in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000

Note that the development build is not optimized...
```

If you see npm errors, check that dependencies are installed: `npm install`

### Step 3: Open the Dashboard

```
http://localhost:3000
```

**Expected**: Map shows with transmission lines and a green sensor dot in San Francisco.

### Step 4: Click the Sensor Point

- Look for the **green dot** on the transmission line (far west of SF map)
- Click it
- A panel should slide in from the right

**Expected Panel Content**:
- Header: "Sensor #1 - Live Monitor"
- Data source badge (green color, says "📊 Simulated baseline data" OR "📡 LIVE DATA")
- Live Status section with:
  - Large RUL countdown (e.g., "39.2h")
  - Status badge (color coded)
  - Risk Score and Confidence
  - Current Readings grid (Temperature, Vibration, Strain, Last Update)

### Step 5: Verify Backend Response

**Open DevTools** (F12 or Cmd+Option+I):
- Network tab
- Filter: "XHR" or "Fetch"
- Close and reopen the sensor panel
- You should see requests to:
  - `/api/live-component/init` (POST) - Initialize
  - `/api/live-component/status` (GET) - Get status
  - `/api/live-component/history` (GET) - Get historical data
  - `/api/live-component/summary` (GET) - Get summary

Click on `/api/live-component/status` and check the **Response** tab:

**Expected JSON** (simplified):
```json
{
  "component_id": "LIVE_COMPONENT_01",
  "current_reading": {
    "sensor_1": 125.4,
    "sensor_2": 450.2,
    "sensor_3": 520.1,
    ...
  },
  "rul_prediction": {
    "rul_hours": 39.23,
    "risk_zone": "green",
    "risk_score": 0.12,
    "confidence": 0.087
  },
  "data_source": "synthetic",
  "elastic_available": false,
  "rul_change_from_baseline": {
    "hours": 0.0,
    "percent": 0.0,
    "direction": "stable"
  },
  "stress_indicators": {
    "temperature": {
      "status": "normal",
      "delta": 0,
      "delta_percent": 0
    },
    "vibration": {...},
    "frequency": {...}
  },
  ...
}
```

### Step 6: Check Polling Frequency

**In DevTools Network tab**:
- Watch requests to `/api/live-component/status`
- Should see requests coming in at regular intervals
- Interval: **10 seconds** if showing "Simulated baseline data"
- Interval: **2 seconds** if showing "LIVE DATA"

Since we don't have real Pi data, you should see ~10 second intervals.

### Step 7: Verify Data Display

**In the panel**, check each section:

1. **Data Source Badge** ✅
   - Should say: "📊 Simulated baseline data"
   - No pulsing dot (would appear if LIVE DATA)
   - Background color: orange tint

2. **RUL Display** ✅
   - Shows: "39.2h" or similar
   - Red border with status "Healthy"
   - Risk Score: ~0-20%
   - Confidence: ~8-9%

3. **Current Readings** ✅
   - Temperature: ~450°C (varies)
   - Vibration: ~125g (varies)
   - Strain: ~520με (varies)
   - Last Update: Current time
   - All readings show "🟢 normal" status

4. **Live RUL Trend Chart** ✅ (after ~30 seconds)
   - Should appear after chart has 5+ data points
   - Shows RUL over time
   - Line should be relatively flat (no real degradation)

5. **35-Day Degradation Baseline** ✅
   - Shows historical synthetic data
   - RUL line declining from ~8400 to ~20
   - Temperature line showing degradation pattern

6. **Statistics** ✅
   - Data Points: 420
   - Time Period: 35 days
   - Initial RUL: ~8400h
   - Final RUL: ~20h

---

## Testing with Real Elasticsearch Data (Optional)

If you have Elasticsearch running with Pi sensor data:

### 1. Verify Elasticsearch Connection

```bash
# Check if env vars are set
echo $ELASTIC_ENDPOINT
echo $ELASTIC_API_KEY

# If empty, set them:
export ELASTIC_ENDPOINT="https://your-endpoint.es.aws.com:9200"
export ELASTIC_API_KEY="your_key_here"

# Restart backend
python web_dashboard.py
```

### 2. Send Test Data to Elasticsearch

```bash
# Send a test sensor reading
curl -X POST ${ELASTIC_ENDPOINT}/metrics-livewire.sensors-default/_doc \
  -H "Authorization: ApiKey ${ELASTIC_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "@timestamp": "2025-10-26T12:00:00Z",
    "sensor_data": {
      "temperature": 35.5,
      "vibration": 0.5,
      "strain": 150.0
    }
  }'
```

### 3. Reload Sensor Panel

- Close the panel (X button)
- Click sensor point again
- Check the data source badge

**Expected**:
- Badge now says: "📡 LIVE DATA - Live from Raspberry Pi → Elasticsearch"
- Green pulsing dot appears
- Polling interval changes to 2 seconds
- RUL might change slightly (sensor values affect calculation)

### 4. Monitor Console Logs

In backend terminal, look for:
```
✅ RUL updated from Elastic: 39.12h (green)
```

In frontend console (DevTools), look for successful fetch logs.

---

## Common Issues & Solutions

### Issue: Panel shows "Simulated baseline data" instead of "LIVE DATA"

**This is EXPECTED** if:
- Elasticsearch isn't configured
- Pi isn't sending data to Elasticsearch
- Env vars aren't set

**To fix**:
1. Set `ELASTIC_ENDPOINT` and `ELASTIC_API_KEY`
2. Ensure Pi is sending data to correct index
3. Restart backend
4. Reload panel

### Issue: "Failed to initialize component" error

**This means** the backend `/api/live-component/init` endpoint is failing.

**To debug**:
1. Open DevTools Console
2. Check error message (now shows details)
3. Check backend logs for Python errors
4. Common causes:
   - RUL model not loaded
   - Synthetic data generation failed
   - Database/file permission issues

**To fix**:
1. Restart backend: `python web_dashboard.py`
2. Check logs for specific errors
3. Verify Python environment has all dependencies

### Issue: RUL not changing even with Elasticsearch data

**This is EXPECTED** because:
- RUL model is 88% time-based
- Sensor changes have small effect
- Even with new data, RUL change might be < 0.1%

**This is correct behavior** (see SENSITIVITY_ANALYSIS.md)

### Issue: Console shows "ParseError" or JSON errors

**This means** backend is returning invalid JSON.

**To fix**:
1. Check backend logs
2. Test endpoint directly: `curl http://localhost:5000/api/live-component/status`
3. Look for Python exceptions

---

## What Each File Does

### Backend
- **`live_component_api.py`**
  - `/api/live-component/init` → Initialize with 35-day synthetic data
  - `/api/live-component/status` → Get current RUL + stress indicators
  - `/api/live-component/history` → Get historical 35-day data
  - `/api/live-component/summary` → Get summary statistics

### Frontend
- **`SensorDetailsPanel.js`**
  - Polls status every 2-10 seconds
  - Displays live RUL with change badge
  - Shows 5-minute RUL trend
  - Displays stress indicators
  - Auto-detects data source

- **`SensorDetailsPanel.css`**
  - Styling for LIVE DATA badge
  - Color-coded stress indicators
  - RUL change animation
  - Pulsing indicator animation

- **`SensorPointLayer.js`**
  - Renders sensor point on map
  - Can change color based on RUL zone (optional integration)

---

## Performance Expectations

| Metric | Value | Note |
|--------|-------|------|
| Status endpoint response | <100ms | Python local calculation |
| Poll interval (Elastic) | 2 seconds | Fast for live data |
| Poll interval (Synthetic) | 10 seconds | Slower since no live data |
| Network request size | ~2KB | Small JSON responses |
| UI update latency | <50ms | React re-renders quickly |
| Chart update | <200ms | Recharts library rendering |

---

## Success Criteria Checklist

- [ ] Backend starts without errors
- [ ] Frontend compiles successfully
- [ ] Map loads with SF transmission lines
- [ ] Sensor point visible (green dot)
- [ ] Clicking sensor opens panel
- [ ] Panel shows "Simulated baseline data" badge
- [ ] RUL countdown displays (e.g., "39.2h")
- [ ] Current readings show values (Temp, Vib, Strain)
- [ ] Status colors match values (green for normal)
- [ ] DevTools shows polling requests every 10 seconds
- [ ] Live RUL Trend chart appears and updates
- [ ] 35-Day Degradation chart displays historical data
- [ ] Statistics show correct values (420 readings, 35 days)
- [ ] No console errors when opening panel
- [ ] Panel closes cleanly with X button

---

## Next Steps After Verification

1. **If everything works**: Ready to demo or test with real Pi data
2. **If something fails**: Check error messages, review code, check dependencies
3. **To integrate real data**:
   - Ensure Pi sends to Elasticsearch with correct format
   - Set env vars: `ELASTIC_ENDPOINT`, `ELASTIC_API_KEY`
   - Restart backend
   - Panel will auto-detect and switch to 2-second polling

---

## Getting Help

**If you see errors**, check:
1. Browser DevTools Console (frontend errors)
2. Backend terminal logs (Python errors)
3. Network tab (API response errors)
4. Error messages shown in the panel

**Common error patterns**:
- `TypeError: Cannot read property...` → Missing data field
- `Failed to initialize component` → Backend init failed
- `ParseError` → Invalid JSON from backend
- `Failed to fetch from Elastic` → Elasticsearch connection issue (expected if not configured)

---

**You now have a fully working live RUL monitoring system!**

Ready to: Demo, test with real Pi data, or integrate further.
