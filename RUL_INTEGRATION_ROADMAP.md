# RUL Integration Roadmap
## From Model to Real-Time Map Visualization

### Current Status
✅ **RUL Model Complete**: Gradient Boosting model trained on NASA CMaps data (68.76 MAE)
✅ **Elasticsearch Infrastructure**: Backend proxy endpoints working, data flowing from alerts index
⏳ **Frontend Integration**: LiveElasticsearchDashboard updated with API polling
❌ **RUL Pipeline Integration**: NOT YET CONNECTED - need to link RUL model to hardware → Elasticsearch → frontend

---

## Roadmap: 6 Phases to Production

### Phase 1: Backend RUL API Endpoint
**Goal**: Expose RUL predictor as HTTP API endpoint

**Current State**:
- RUL model exists at `models/rul_predictor.py`
- Can predict individual component RUL from sensor readings
- NO backend API exists yet

**What Needs to Happen**:
1. Create Flask endpoint in `backend/rul_api.py`:
   ```
   POST /api/rul/predict
   Input: { component_id, sensor_readings }
   Output: { component_id, rul_hours, confidence, prediction_timestamp }
   ```

2. Load pre-trained RUL model on startup:
   - Train once on NASA CMaps data
   - Save model artifact to `models/artifacts/`
   - Load at boot for fast inference

3. Implement batch prediction endpoint:
   ```
   POST /api/rul/batch-predict
   Input: { components: [ { component_id, sensor_readings } ] }
   Output: { predictions: [ { component_id, rul_hours } ] }
   ```

**Success Criteria**:
- Can POST sensor data → get RUL prediction back (< 100ms latency)
- Model loads from disk on startup
- Error handling for bad input data

---

### Phase 2: RUL ↔ Elasticsearch Integration
**Goal**: Store RUL predictions in Elasticsearch for historical tracking and visualization

**Current State**:
- Elasticsearch has `metrics-livewire.sensors-default` (sensor readings)
- Elasticsearch has `logs-livewire.alerts-default` (alerts)
- No RUL predictions index exists

**What Needs to Happen**:
1. Create RUL predictions index in Elasticsearch:
   ```
   Index: metrics-livewire.rul-predictions-default

   Schema:
   {
     "@timestamp": "2025-10-26T11:00:00Z",
     "component_id": "CABLE_A1_MAIN",
     "component_location": { "lat": 34.0522, "lon": -118.2437 },
     "rul_hours": 48.5,
     "rul_days": 2.02,
     "confidence": 0.87,
     "last_sensor_reading": {
       "temperature": 45.3,
       "vibration": 0.82,
       "strain": 185.2,
       "power": 720.5
     },
     "risk_zone": "yellow",
     "risk_score": 0.72
   }
   ```

2. Modify backend proxy (`backend/elasticsearch_proxy.py`):
   - Add `/api/rul-predictions` endpoint
   - Add `/api/rul-by-component/<component_id>` endpoint for specific components
   - Return aggregated RUL data (latest, trends over 24h)

3. Create RUL scoring pipeline:
   - When new sensor data arrives in Elasticsearch
   - Trigger RUL prediction
   - Store prediction in `metrics-livewire.rul-predictions-default` index

**Success Criteria**:
- RUL predictions automatically written to Elasticsearch when sensors update
- Can query `/api/rul-predictions` and get all components' RUL values
- Historical RUL data available for trend analysis

---

### Phase 3: Map Component with RUL Display
**Goal**: Show RUL predictions on the Los Angeles map, with color coding by risk

**Current State**:
- `frontend/src/components/LosAngelesMap.js` exists
- Shows map with static component locations
- NO RUL data displayed

**What Needs to Happen**:
1. Update LosAngelesMap component:
   ```javascript
   // Fetch RUL predictions
   useEffect(() => {
     fetch('/api/rul-predictions')
       .then(r => r.json())
       .then(data => {
         // data = { predictions: [ { component_id, rul_hours, risk_zone, location } ] }
         setComponentsRUL(data.predictions);
       });
   }, []); // Fetch once on load, or poll every 10s for real-time

   // Render markers on map
   // Color code: Green (>72h) → Yellow (24-72h) → Red (<24h)
   // Tooltip shows: "CABLE_A1: 48.5 hours remaining"
   // Click marker → show detailed RUL trend chart
   ```

2. Color scheme:
   - **Green (safe)**: RUL > 72 hours
   - **Yellow (warning)**: RUL 24-72 hours
   - **Red (critical)**: RUL < 24 hours

3. Interactive features:
   - Click component marker → Show RUL history chart (last 7 days)
   - Hover → Show component name + RUL hours
   - Filter by risk level (show only Red/Yellow)

**Success Criteria**:
- All power grid components visible on map
- Color-coded by RUL risk level
- Clicking a component shows RUL trend over time
- Real-time updates every 5-10 seconds

---

### Phase 4: Real-Time Frontend Updates
**Goal**: Keep RUL predictions flowing to frontend with minimal latency

**Current State**:
- LiveElasticsearchDashboard has `useEffect` polling `/api/sensor-data` every 5s
- NO RUL data polling

**What Needs to Happen**:
1. Add RUL polling to Dashboard component:
   ```javascript
   useEffect(() => {
     const fetchRUL = async () => {
       const response = await fetch('/api/rul-predictions');
       const data = await response.json();
       setRULData(data.predictions);
     };

     fetchRUL();
     const interval = setInterval(fetchRUL, 10000); // Poll every 10 seconds
     return () => clearInterval(interval);
   }, []);
   ```

2. Display RUL stats in dashboard:
   - "Components at Risk": Count of components with RUL < 24h
   - "Average RUL": Mean RUL across all components
   - "Most Critical": Component with lowest RUL (show countdown)

3. Real-time alerts:
   - If any component RUL < 24h → Show prominent red alert
   - If RUL decreasing rapidly → Yellow warning
   - Sound/notification option

4. Optional: WebSocket upgrade for lower latency
   - Current: HTTP polling (1-2 second latency)
   - Future: WebSocket streaming (< 100ms latency)

**Success Criteria**:
- Dashboard shows live RUL metrics
- Map updates in real-time as RUL changes
- Alerts fire when critical threshold crossed
- < 5 second round-trip from sensor → prediction → frontend

---

### Phase 5: Hardware Integration
**Goal**: Ensure Raspberry Pi sensor stream flows → RUL predictions → Elasticsearch

**Current State**:
- Raspberry Pi sending sensor data (assumed, based on project description)
- Data should be in Elasticsearch `metrics-livewire.sensors-default` index
- RUL predictions NOT yet computed from incoming data

**What Needs to Happen**:
1. Create Elasticsearch watcher/rule to trigger RUL scoring:
   - When new documents arrive in `metrics-livewire.sensors-default`
   - Group by component_id + time window (e.g., last 100 readings)
   - Extract [temp, vibration, strain, power]
   - Call `/api/rul/predict` endpoint
   - Write result to `metrics-livewire.rul-predictions-default`

2. Alternative: Streaming lambda function:
   - Elasticsearch Ingest pipeline processes incoming sensor data
   - Calls backend RUL endpoint
   - Stores predictions alongside sensor readings

3. Verify data quality:
   - Check that sensors are reporting all required fields
   - Validate ranges (temp: 0-100°C, vibration: 0-5g, etc.)
   - Log missing/bad data for debugging

**Success Criteria**:
- Sensor data from Pi flows to Elasticsearch (verify in Kibana)
- RUL predictions auto-computed and stored
- New sensor reading → RUL prediction within 1-2 seconds
- No manual steps required (fully automated pipeline)

---

### Phase 6: End-to-End Testing & Deployment
**Goal**: Verify full pipeline and deploy to production

**Test Checklist**:
- [ ] Start Flask backend: `python web_dashboard.py`
- [ ] Verify RUL endpoint: `curl http://localhost:5000/api/rul/predict -X POST -d '...'`
- [ ] Check Elasticsearch: RUL predictions index has documents
- [ ] Start React frontend: `npm start` in `frontend/`
- [ ] View LA map: Navigate to `/map` or home page
- [ ] See colored markers for each component
- [ ] Click a marker: Should show RUL trend chart
- [ ] Watch real-time updates: Map colors change as RUL updates
- [ ] Trigger critical alert: Manually lower a component's RUL, verify alert fires

**Load Testing**:
- Simulate 100+ sensors sending data (use synthetic Elasticsearch ingest)
- Verify backend can handle 10+ RUL predictions/second
- Check frontend doesn't lag with live updates
- Monitor Elasticsearch storage growth

**Deployment**:
- Set environment variables on production server
- Ensure Elasticsearch Serverless accessible from prod backend
- Run backend with process manager (PM2, systemd)
- Serve React build as static files or separate frontend server
- Set up monitoring/logging for all endpoints

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  Raspberry Pi Hardware                      │
│  (Temperature, Vibration, Strain, Power sensors)           │
└────────────────────────┬────────────────────────────────────┘
                         │ (MQTT or HTTP POST)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│         Elasticsearch Serverless (GCP)                      │
│  - metrics-livewire.sensors-default (incoming sensor data)  │
│  - metrics-livewire.rul-predictions-default (NEW!)          │
│  - logs-livewire.alerts-default                             │
└─────────────────┬────────────────────────────────────────────┘
                  │ (Query + Ingest Pipeline)
                  ▼
┌─────────────────────────────────────────────────────────────┐
│            Flask Backend (Port 5000)                        │
│  ├─ /api/sensor-data (existing)                            │
│  ├─ /api/alerts (existing)                                 │
│  ├─ /api/rul/predict (NEW - Phase 1)                       │
│  ├─ /api/rul/batch-predict (NEW - Phase 1)                 │
│  └─ /api/rul-predictions (NEW - Phase 2)                   │
│                                                              │
│  Loaded Models:                                             │
│  ├─ models/rul_predictor.py (Gradient Boosting)            │
│  └─ models/grid_risk_model.py (CCI - existing)             │
└────────────────────────────┬─────────────────────────────────┘
                             │ (REST API)
                             ▼
┌─────────────────────────────────────────────────────────────┐
│          React Frontend (Port 3000)                         │
│  ├─ LosAngelesMap.js (Phase 3 - show RUL on map)          │
│  ├─ LiveElasticsearchDashboard.js (Phase 4 - RUL stats)    │
│  └─ Other dashboard components                             │
│                                                              │
│  Real-time Polling:                                        │
│  ├─ fetch('/api/sensor-data') every 5s                     │
│  ├─ fetch('/api/rul-predictions') every 10s                │
│  └─ fetch('/api/alerts') every 10s                         │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Order (Recommended)

1. **Start with Phase 1** (Backend RUL API)
   - Quick win: Get RUL model serving predictions
   - Foundation for all other phases
   - Est. 2-3 hours

2. **Then Phase 2** (Elasticsearch Integration)
   - Enable historical RUL tracking
   - Required for map visualization
   - Est. 2-3 hours

3. **Then Phase 3** (Map Component)
   - Make RUL visible to users
   - High impact demo feature
   - Est. 3-4 hours

4. **Then Phase 4** (Real-Time Frontend)
   - Connect dashboard to live RUL data
   - Add critical alerts
   - Est. 2-3 hours

5. **Then Phase 5** (Hardware)
   - Automate RUL scoring from Pi data
   - Fully operational pipeline
   - Est. 3-4 hours (depends on Pi setup)

6. **Finally Phase 6** (Testing & Deploy)
   - Verify everything works together
   - Load testing
   - Production deployment

**Total Estimated Time**: 15-20 hours for full integration

---

## Key Files to Modify/Create

| File | Phase | Action | Status |
|------|-------|--------|--------|
| `backend/rul_api.py` | 1 | **CREATE** | ❌ Not started |
| `models/rul_predictor.py` | 1 | Train + save artifact | ✅ Model ready |
| `backend/elasticsearch_proxy.py` | 2 | Add `/api/rul-predictions` | ⏳ Modify existing |
| `frontend/src/components/LosAngelesMap.js` | 3 | Add RUL markers + polling | ⏳ Enhance existing |
| `frontend/src/components/LiveElasticsearchDashboard.js` | 4 | Add RUL stats panel | ✅ Already polling |
| Elasticsearch ingest pipeline | 5 | Create watcher/rule | ❌ Not started |

---

## Next Immediate Step

**→ Phase 1: Create RUL Backend API Endpoint**

This is the foundation everything else builds on. Once the `/api/rul/predict` endpoint works, we can:
- Test it independently with curl
- Chain it to Elasticsearch
- Display results on the map
- Push live updates to frontend

Would you like me to start building Phase 1?
