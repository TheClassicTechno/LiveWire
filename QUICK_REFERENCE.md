# Phase 3: Quick Reference Guide

**For when you need to quickly understand Phase 3 implementation**

---

## THE GOAL
Demonstrate that RUL predictions respond to real-time hardware changes with a complete feedback loop.

## THE SOLUTION
- 35-day historical baseline showing realistic degradation
- Live component tracking starting from degraded state
- Hardware stress simulation that recalculates RUL in real-time
- Beautiful dashboard showing all of it together

---

## CRITICAL FILES YOU NEED TO KNOW

### If You Need to Understand Data Generation
**File**: `backend/synthetic_degradation.py`

**Key Classes**:
- `SyntheticComponentSimulator` - Generates 420 readings (35 days)
- `LiveComponentTracker` - Tracks current hardware state
- Function: `initialize_live_component()` - Entry point

**What It Does**:
```python
# Generate 35 days of degradation
sim = SyntheticComponentSimulator()
df = sim.generate_readings()  # 420 readings

# Create tracker for live state
tracker = LiveComponentTracker()

# Store in persistent module state
_component_state["degradation_sim"] = sim
_component_state["live_tracker"] = tracker
```

---

### If You Need to Understand API Endpoints
**File**: `backend/live_component_api.py`

**5 Key Endpoints**:
1. `POST /api/live-component/init` - Initialize system
2. `GET /api/live-component/status` - Get current RUL
3. `GET /api/live-component/history` - Get 35-day history
4. `POST /api/live-component/simulate-stress` - Apply stress & recalculate RUL
5. `GET /api/live-component/summary` - Overview

**The Feedback Loop** (THE CRITICAL PART):
```python
# In simulate-stress endpoint:
1. Get baseline RUL
2. Modify sensors (temperature +50%)
3. Recalculate RUL with modified sensors  ← THIS WAS THE FIX
4. Compute RUL change
5. Update tracker with new RUL
6. Return baseline, stressed, and change to frontend
```

**Key Function**:
```python
recalculate_rul(sensor_readings, historical_readings)
# Takes modified sensors
# Uses 35-day history for context
# Feeds through RUL model
# Returns new RUL prediction
```

---

### If You Need to Understand the Frontend
**File**: `frontend/src/components/LiveComponentDashboard.js`

**8 UI Sections**:
1. Initialization button
2. Header with title
3. Status cards (component ID, location, time)
4. RUL countdown (large display)
5. Stress control buttons (3 groups × 3 buttons)
6. Historical chart (Recharts)
7. Summary statistics
8. Help text

**Key Function**:
```javascript
applyStress(stressType, magnitude)
// Calls POST /api/live-component/simulate-stress
// Logs RUL change to console
// Fetches updated status
// Displays new RUL
```

---

### If You Need to Understand State Management
**File**: `backend/synthetic_degradation.py` - Module level

**Why Module-Level State?**
```python
# Flask creates new instances per request
# Module-level variables persist across requests
# This is how 35-day history survives API calls

_component_state = {
    "degradation_sim": SyntheticComponentSimulator(...),
    "live_tracker": LiveComponentTracker(...),
    "initialized": True
}

def get_component_state():
    return _component_state  # Returns SAME instance every time
```

---

## THE FIX THAT MADE IT WORK

**Problem**: Stress buttons modified sensors but RUL didn't change
**Root Cause**: Stress endpoint didn't recalculate RUL
**Solution**: Added `recalculate_rul()` call in stress endpoint

**Before**:
```python
# Only modified sensors
modified["sensor_2"] *= 1.5
return {"modified_sensors": {...}}  # No RUL change shown
```

**After**:
```python
# Modified sensors AND recalculate
modified["sensor_2"] *= 1.5
stressed_rul = recalculate_rul(modified, historical_readings)  # NEW
rul_change = stressed_rul["rul_hours"] - baseline_rul["rul_hours"]
return {
    "baseline_rul": baseline_rul,
    "stressed_rul": stressed_rul,
    "rul_change": {"hours": rul_change, "percent": ...}  # NOW shows change
}
```

---

## TEST EVERYTHING

### Quick Test (5 minutes)
```bash
python scripts/test_stress_feedback_loop.py
```
Shows RUL recalculation working across 6 stress scenarios.

### Live Test (10 minutes)
```bash
# Terminal 1
python web_dashboard.py

# Terminal 2
cd frontend && npm start

# Browser
http://localhost:3000/live-component
# Click stress button, open console (F12)
```

---

## FEATURE IMPORTANCE (Why Changes Are Small)

```
time_normalized:    88.07%  ← Controls RUL
time_cycles:         8.99%
sensor_features:     <2%    ← Why stress impact is small

This is CORRECT for the NASA CMaps model:
- Turbofans degrade linearly over time
- Model learned: "Age is the best predictor"
- Stress shows RUL change but it's small
```

---

## WHEN INTEGRATING WITH REAL HARDWARE

**Update This Endpoint**:
```python
# backend/live_component_api.py
@bp.route('/api/live-component/simulate-stress', methods=['POST'])

# Replace stress simulation logic with:
# 1. Read actual hardware sensor values
# 2. Feed to recalculate_rul()
# 3. Return RUL change
# 4. Update tracker
```

**Keep These Unchanged**:
- `recalculate_rul()` function (it's flexible)
- `/api/live-component/init` (historical data for context)
- `/api/live-component/status` (returns current RUL)
- Frontend (works with any RUL data)

---

## FOLDER STRUCTURE FOR THIS PHASE

```
LiveWire/
├── backend/
│   ├── synthetic_degradation.py      ← Phase 3A (data gen)
│   ├── live_component_api.py         ← Phase 3C (API) + 3D (fix)
│   └── rul_api.py                    ← Existing (unchanged)
│
├── frontend/src/components/
│   ├── LiveComponentDashboard.js     ← Phase 3B (dashboard)
│   └── LiveComponentDashboard.css    ← Phase 3B (styling)
│
├── frontend/src/
│   └── App.js                        ← Phase 3B (routing)
│
├── scripts/
│   ├── test_stress_feedback_loop.py  ← Phase 3E (test)
│   └── diagnose_model_sensitivity.py ← Phase 3E (diagnostic)
│
├── web_dashboard.py                  ← Phase 3C (blueprint registration)
│
└── Documentation/
    ├── PHASE_3_IMPLEMENTATION_SUMMARY.md  ← YOU ARE HERE
    ├── PHASE_3_README.md                  ← User guide
    ├── PHASE_3_COMPLETION_SUMMARY.md      ← Technical details
    ├── PHASE_3_FEEDBACK_LOOP_FIX.md       ← The fix explained
    └── ... (6 more docs)
```

---

## ENDPOINTS AT A GLANCE

```
Method  Endpoint                              What It Does
────────────────────────────────────────────────────────────────
POST    /api/live-component/init              Create 35-day baseline
GET     /api/live-component/status            Get current RUL
GET     /api/live-component/history           Get historical data
POST    /api/live-component/simulate-stress   Apply stress, recalculate
GET     /api/live-component/summary           Overview
```

---

## UNDERSTANDING THE SYSTEM IN 30 SECONDS

1. **Initialization**: Generate 35 days of degradation data (healthy → failure)
2. **Live Component**: Start hardware from end of 35-day data (degraded state)
3. **Stress Simulation**: Apply temperature increase → modify sensors
4. **RUL Recalculation**: Feed modified sensors through RUL model
5. **Display**: Show baseline RUL vs stressed RUL with change
6. **Proof**: Stress objectively affects RUL (feedback loop works)

---

## COMMON QUESTIONS

**Q: Why are RUL changes so small?**
A: Model is 88% time-based. This is expected. But stress DOES cause RUL change (proving loop works).

**Q: How do I verify it works?**
A: Run `python scripts/test_stress_feedback_loop.py` - shows RUL recalculation in action.

**Q: Where do I add real hardware?**
A: Replace stress simulation logic in `/api/live-component/simulate-stress` endpoint.

**Q: Can I use different component?**
A: Yes - change "LIVE_COMPONENT_01" to anything, update location coordinates.

**Q: What about Elasticsearch?**
A: Optional enhancement. Current system uses module-level state (good enough for demo).

---

## NEXT STEPS

**To Test**:
```bash
python scripts/test_stress_feedback_loop.py
```

**To Deploy**:
```bash
# Terminal 1: Backend
python web_dashboard.py

# Terminal 2: Frontend
cd frontend && npm start

# Browser: http://localhost:3000/live-component
```

**To Extend**:
- Read `PHASE_3_IMPLEMENTATION_SUMMARY.md` (detailed breakdown)
- Check `PHASE_3_README.md` (user guide)
- Review `PHASE_3_FEEDBACK_LOOP_FIX.md` (how the fix works)

---

**Status**: ✅ COMPLETE & WORKING
**Date**: October 26, 2025
