# Phase 3: Elasticsearch Integration with Live Component RUL

**Date**: October 26, 2025
**Status**: ✅ COMPLETE
**What Changed**: Live component dashboard now reads real sensor data from Elasticsearch and recalculates RUL in real-time while maintaining 35-day historical baseline context.

---

## The Problem Solved

Previously, the live component dashboard was using **synthetic stress simulation** - when you clicked stress buttons, it modified sensor values locally but didn't connect to actual hardware.

Now the system works like this:

```
Raspberry Pi with Knobs
        ↓
        ├─ Reads sensor values (temperature, vibration, strain, power)
        ├─ Sends to Elasticsearch
        │
        └─→ Dashboard polls for latest sensor data
            ├─ Merges with 35-day synthetic baseline
            ├─ Recalculates RUL using merged data
            └─ Shows real-time RUL changes as hardware values change
```

---

## Architecture

### Data Flow

```
┌─────────────────────────────────────────┐
│  Raspberry Pi Hardware                  │
│  ├─ Temperature sensor (15-45°C)        │
│  ├─ Vibration sensor (0.05-2.0 g)       │
│  ├─ Strain sensor (50-500 µε)           │
│  └─ Power sensor (800-1500 W)           │
└────────────┬──────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Elasticsearch (metrics-livewire.      │
│   sensors-default)                      │
│  ├─ temperature                         │
│  ├─ vibration                           │
│  ├─ strain                              │
│  ├─ power                               │
│  └─ @timestamp                          │
└────────────┬──────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  /api/live-component/status endpoint    │
│  (live_component_api.py)                │
│                                         │
│  1. Fetch latest from Elastic           │
│  2. Merge with baseline structure       │
│  3. Get 35-day history for context      │
│  4. Engineer RUL features               │
│  5. Predict with RUL model              │
│  6. Return updated RUL                  │
└────────────┬──────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  React Dashboard                        │
│  (/live-component route)                │
│                                         │
│  ✅ Shows data_source = "elastic"       │
│  ✅ Displays real-time RUL             │
│  ✅ Updates every 10 seconds            │
│  ✅ Shows green pulsing badge           │
└─────────────────────────────────────────┘
```

### Key Insight: Historical Baseline Context

The RUL model **requires** historical context to calculate trends and volatility features. We maintain:

- **35-day synthetic degradation** (stored in module-level state)
- **Latest real sensor data** (from Elasticsearch, queried at request time)

This combination means:
- RUL prediction uses proper feature engineering (trends, rate of change, etc.)
- Real hardware changes immediately affect the RUL
- Smooth fallback to synthetic data if Elasticsearch is unavailable

---

## What Changed in the Code

### 1. Backend: `backend/live_component_api.py`

#### Added Elasticsearch Support
```python
try:
    from elasticsearch import Elasticsearch
    HAS_ELASTICSEARCH = True
except ImportError:
    HAS_ELASTICSEARCH = False
```

#### New Helper Functions

**`get_elasticsearch_client()`**
- Initializes Elasticsearch client from environment variables
- `ELASTIC_ENDPOINT` and `ELASTIC_API_KEY`
- Returns None if unavailable (graceful degradation)

**`fetch_latest_sensor_data_from_elastic()`**
- Queries `metrics-livewire.sensors-default` index
- Looks for data from last 5 minutes
- Returns dict with: temperature, vibration, strain, power
- Returns None if no data found or Elastic unavailable

**`build_sensor_reading_from_elastic(elastic_data, baseline_reading)`**
- Merges Elastic real-time data with 21-sensor baseline structure
- Maps Elastic sensor ranges to our internal sensor format:
  - Temperature: 15-45°C → sensor_2 (350-500 range)
  - Vibration: 0.05-2.0 g → sensor_1 (100-150 range)
  - Strain: 50-500 µε → sensor_3 (50-500 range)
  - Power: 800-1500 W → op_setting_3 (0-1 normalized)
- Preserves all other sensors from baseline (steady-state values)

#### Modified Endpoint: `/api/live-component/status`

**Before**: Returned fixed synthetic data from module state

**After**:
1. Check if initialized
2. Try to fetch latest sensor data from Elasticsearch
3. If data found:
   - Merge with baseline sensor structure
   - Get 35-day historical readings
   - Recalculate RUL with merged data + history
   - Update tracker with new RUL
   - Set `data_source = "elastic"`
4. If Elastic unavailable or no data:
   - Return cached synthetic data
   - Set `data_source = "synthetic"`
5. Return response with `data_source` field

**Response includes**:
```json
{
  "component_id": "LIVE_COMPONENT_01",
  "current_reading": { ... },
  "rul_prediction": { ... },
  "data_source": "elastic",  // or "synthetic"
  "timestamp": "2025-10-26T12:00:00Z"
}
```

---

### 2. Frontend: `frontend/src/components/LiveComponentDashboard.js`

#### Added Data Source Badge

In the header, now displays:

```jsx
{currentStatus?.data_source === 'elastic' && (
  <div className="data-source-badge elastic">
    <span className="pulse"></span>
    Data from Elasticsearch (Live Hardware)
  </div>
)}
{currentStatus?.data_source === 'synthetic' && (
  <div className="data-source-badge synthetic">
    Data from Synthetic Baseline
  </div>
)}
```

Shows users immediately whether they're viewing real hardware data or synthetic baseline.

---

### 3. Frontend: `frontend/src/components/LiveComponentDashboard.css`

#### New Styles

**.data-source-badge**
- Inline-flex display with green (elastic) or gray (synthetic) styling
- Shows border and background for clear visual distinction
- Font size: 12px, positioned under description

**.data-source-badge.elastic**
- Green (#86efac) text on dark green background
- 1px border with semi-transparent green

**.data-source-badge.synthetic**
- Gray (#cbd5e1) text on dark gray background
- 1px border with semi-transparent gray

**.data-source-badge .pulse**
- 6px green circle
- Pulsing animation (scale 1 → 1.1 → 1, 2 second cycle)
- Only visible when data_source = "elastic"

---

## How It Works End-to-End

### Scenario: Raspberry Pi Knob Changes Temperature

1. **Hardware**: Pi reads knob position → increases temperature sensor from 25°C to 35°C
2. **Pi Software**: Sends to Elasticsearch:
   ```json
   {
     "temperature": 35.0,
     "vibration": 0.15,
     "strain": 120.0,
     "power": 1100.0,
     "@timestamp": "2025-10-26T12:00:00Z"
   }
   ```
3. **Dashboard**: Every 10 seconds calls `GET /api/live-component/status`
4. **Backend Processing**:
   - Fetches latest from Elasticsearch ✅ Found data
   - Merges with baseline: Temperature 35°C → sensor_2 = 400 (scaled)
   - Gets last 35 days of synthetic history
   - Engineers 68 RUL features from merged data + history
   - Runs through GradientBoosting model
   - **RUL changes** (usually slight change, since model is 88% time-based)
5. **Frontend Display**:
   - Shows "Data from Elasticsearch (Live Hardware)" badge with pulsing dot
   - Updates RUL countdown to new value
   - Shows data_source: "elastic" in response

### Scenario: Elasticsearch Unavailable

1. Dashboard calls `/api/live-component/status`
2. Backend tries to fetch from Elastic → fails
3. Returns last cached RUL prediction from tracker
4. Shows "Data from Synthetic Baseline" badge
5. System continues working with synthetic data
6. Next time Elastic is available, automatically switches back to real data

---

## Requirements & Configuration

### Environment Variables

Add to your `.env` file:

```bash
ELASTIC_ENDPOINT=https://your-elastic-cloud-id.us-west1.gcp.elastic.cloud
ELASTIC_API_KEY=your-api-key-here
```

Or set in your deployment environment.

### Python Dependencies

```bash
pip install elasticsearch
```

(Already in requirements.txt if you've been using Elasticsearch for other components)

### Elasticsearch Index

Expected index: `metrics-livewire.sensors-default`

Expected fields:
- `@timestamp` (datetime) - When the reading was taken
- `temperature` (float) - °C
- `vibration` (float) - g-force
- `strain` (float) - microstrain
- `power` (float) - Watts
- `component_id` (optional keyword) - Component identifier

---

## Testing

### Quick Test: Check Elastic Integration

```bash
# Start backend
python web_dashboard.py

# In browser console (after initializing component)
fetch('/api/live-component/status')
  .then(r => r.json())
  .then(data => console.log('Data source:', data.data_source))
```

Should see:
- `"data_source": "elastic"` if Elastic is connected and has recent data
- `"data_source": "synthetic"` if Elastic is unavailable or no recent data

### Full Test: Send Fake Data to Elastic

```bash
# If you have elasticsearch-py installed locally
python -c "
from elasticsearch import Elasticsearch
import json
from datetime import datetime

es = Elasticsearch(['http://localhost:9200'])
doc = {
    '@timestamp': datetime.utcnow().isoformat() + 'Z',
    'temperature': 30.0,
    'vibration': 0.5,
    'strain': 150.0,
    'power': 1000.0,
    'component_id': 'LIVE_COMPONENT_01'
}
es.index(index='metrics-livewire.sensors-default', body=doc)
print('✅ Test data sent to Elastic')
"
```

Then refresh the dashboard - RUL should update!

---

## Why This Design

### 1. Historical Context is Critical
RUL models need trends to make predictions. The 35-day baseline provides:
- Rate of change features
- Volatility measurements
- Time-based features (cycle count)
- Reference degradation pattern

Without it, a single sensor reading can't be properly interpreted.

### 2. Graceful Degradation
If Elasticsearch is unavailable:
- System doesn't crash
- Falls back to synthetic data
- Automatically resumes when Elastic comes back online
- Users are always informed via badge

### 3. Sensor Mapping is Flexible
The `build_sensor_reading_from_elastic()` function is intentionally simple and can be customized:
- Map to different sensor fields
- Adjust scaling ranges
- Add more sensors
- Integrate with other data sources

### 4. No Breaking Changes
- Existing synthetic data path still works
- Stress simulation buttons still work (modify synthetic sensors)
- Historical chart uses 35-day baseline regardless
- Pure additive change

---

## Deployment Checklist

- [ ] Add `ELASTIC_ENDPOINT` and `ELASTIC_API_KEY` to environment variables
- [ ] Verify `elasticsearch` package is in requirements.txt
- [ ] Verify Elasticsearch index `metrics-livewire.sensors-default` exists
- [ ] Verify Raspberry Pi is sending data to Elasticsearch with correct field names
- [ ] Test dashboard initialization and status endpoint
- [ ] Verify data_source badge appears in dashboard header
- [ ] Test with Elastic connected and with Elastic disconnected
- [ ] Check logs for "RUL updated from Elastic" messages

---

## Files Modified

| File | Changes |
|------|---------|
| `backend/live_component_api.py` | Added Elasticsearch integration functions, modified `/api/live-component/status` endpoint |
| `frontend/src/components/LiveComponentDashboard.js` | Added data_source badge display in header |
| `frontend/src/components/LiveComponentDashboard.css` | Added styles for data_source badge and pulse animation |

---

## Next Steps

### Integration with Raspberry Pi
Your teammate should:
1. Read sensor values from hardware
2. Send to Elasticsearch endpoint configured in environment
3. Use fields: temperature, vibration, strain, power, @timestamp
4. Dashboard will automatically pick up the data

### Customization
To adjust sensor mapping:
1. Edit `build_sensor_reading_from_elastic()` function
2. Change scaling ranges to match your hardware
3. Add new sensor fields as needed
4. Test with `fetch('/api/live-component/status')`

### Production Deployment
1. Store Elasticsearch credentials securely (not in source code)
2. Use environment variables or secrets manager
3. Set appropriate data retention policies in Elasticsearch
4. Monitor Elasticsearch cluster health
5. Add alerting if Elasticsearch becomes unavailable

---

## How to Verify It's Working

### Check 1: Visual Indicator
- Initialize live component
- Look at header under "Live Component Monitoring System"
- If Elastic has data: See "Data from Elasticsearch (Live Hardware)" with pulsing green dot
- If Elastic unavailable: See "Data from Synthetic Baseline" in gray

### Check 2: Data Source in API
```bash
curl http://localhost:5000/api/live-component/status | jq '.data_source'
# Returns: "elastic" or "synthetic"
```

### Check 3: RUL Changes in Real-Time
1. Send test data to Elasticsearch
2. Refresh dashboard (or wait 10 seconds for auto-refresh)
3. RUL should update based on new sensor values
4. Check browser console: `console.log(currentStatus.data_source)`

---

**Summary**: The live component dashboard now reads real hardware sensor data from Elasticsearch while maintaining the 35-day synthetic baseline for proper RUL model feature engineering. The system gracefully falls back to synthetic data if Elasticsearch is unavailable, and users always know which data source they're viewing.

🚀 **Ready for real hardware integration!**
