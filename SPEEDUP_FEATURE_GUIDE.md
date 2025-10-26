# ⏩ Speedup Timeline Feature - Complete Guide

## What It Does

The **"Show 30-Day Timeline"** button allows judges to see 30 days of component degradation **in just 3 seconds**.

### Before (Without Speedup)
```
Day 1: RUL = 349h (GREEN)
Wait 30 days...
Day 30: RUL = 1h (RED)
```

### After (With Speedup)
```
Click ⏩ button
↓
Watch: Day 1 → 2 → 3 ... → 30 (3 seconds total)
↓
See: RUL countdown: 349h → 341h → 333h ... → 1h
↓
See: Color change: GREEN → YELLOW → RED (automatically)
↓
Understand: How knob position affects failure timeline
```

---

## How It Works

### 1. User Clicks "Show 30-Day Timeline" Button
- Button is in the Sensor Details Panel (right side)
- Button is cyan/purple gradient with ⏩ emoji

### 2. Frontend Calls Backend
```javascript
POST /api/live-component/accelerate
{
  "days": 30,
  "acceleration_factor": 100
}
```

### 3. Backend Generates 30-Day Degradation Trajectory
```python
# For each simulated day (1-30):
# - Age the component
# - Degrade sensors based on current knob position
# - Call RUL model to predict remaining life
# - Record: {day, rul_prediction, risk_zone}
```

**Key insight**: Higher knob values = faster degradation
- T=45°C (hot) → Fast failure
- T=25°C (cool) → Slow failure

### 4. Frontend Animates Through Timeline
- Shows each day for 100ms (30 days = 3 seconds)
- RUL countdown updates every frame
- Progress bar fills: 0% → 100%
- Shows day number: 1/30 → 2/30 ... → 30/30

### 5. Summary Shows
- Start RUL: 349h (GREEN)
- End RUL: 1h (RED)
- Days to critical: Day 25 (example)
- Degradation rate assessment

---

## What Judges Will See

### Timeline Animation
```
⏩ Show 30-Day Timeline
     ↓ (click)
███░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
Day 15 of 30

Start RUL: 349h [GREEN] → End RUL: 1h [RED]
🔴 Critical at Day 25 - Moderate degradation
```

### RUL Countdown (During Animation)
- Updates every 100ms
- Shows real-time degradation
- Changes color: green → yellow → orange → red
- Proof that model is working

### Examples of Different Scenarios

#### Scenario 1: High Temperature (45°C)
```
Click speedup
↓
Day 10: Already YELLOW (warning)
Day 15: RED (critical)
Day 20: Deep red (failure imminent)
Summary: 🔴 Critical at Day 15 - Very fast degradation!
```

#### Scenario 2: Moderate Temperature (30°C)
```
Click speedup
↓
Day 15: GREEN
Day 20: YELLOW (warning)
Day 25: ORANGE (high risk)
Day 30: RED (critical)
Summary: 🔴 Critical at Day 25 - Moderate degradation
```

#### Scenario 3: Low Temperature (20°C)
```
Click speedup
↓
Day 20: GREEN
Day 25: YELLOW (just warning)
Day 30: Still ORANGE (not critical)
Summary: 🔴 Critical at Day 30+ - Slow degradation
```

---

## Key Features

### 1. Dynamic Based on Knob Position
The timeline changes depending on current sensor values:
- **How to show judges**: Adjust knob, click speedup, see different timeline
- Proof that model is sensitive to input

### 2. Visual Timeline Progress
- Cyan-to-red gradient progress bar
- Clearly shows progress: 0% → 100%
- Day counter: "Day 15 of 30"

### 3. Summary Statistics
- Shows starting and ending RUL values
- Shows color transition: GREEN → RED
- Shows which day becomes critical
- Assessment: "Very fast", "Moderate", or "Slow" degradation

### 4. Real RUL Model Predictions
- Each day uses actual Gradient Boosting model
- Not fake or hardcoded
- Proves model is working over full trajectory

---

## How to Use in Demo

### Setup
1. Click on a sensor point on the map
2. Sensor Details Panel opens (right side)
3. You'll see ⏩ button labeled "Show 30-Day Timeline"

### Demo Flow

**Step 1: Show Normal Operation**
```
"Let me demonstrate how the model predicts failures."
Click sensor → Panel opens
Show current RUL: 349h (GREEN)
```

**Step 2: Adjust Knobs (Optional)**
```
"Let's say we operate at high temperature (45°C)"
Turn temperature knob to 45°C
(Or just use current value)
```

**Step 3: Click Speedup Button**
```
"Now let me compress 30 days of operation into 3 seconds"
Click ⏩ "Show 30-Day Timeline"
```

**Step 4: Watch Animation**
```
Watch timeline animate
Notice: RUL counts down
Notice: Color changes green → yellow → red
Notice: Progress bar fills
```

**Step 5: Read Summary**
```
"See how it reaches critical at Day 25?"
"That's when the component would need maintenance"
"All based on the Gradient Boosting model predictions"
```

**Step 6: Show Sensitivity (Optional Second Run)**
```
"Let me show what happens at low temperature"
Click speedup again with different knob value
"Notice it takes longer to reach critical"
"Proof the model responds to sensor changes"
```

---

## Technical Implementation

### Backend: `/api/live-component/accelerate`

**Request:**
```json
{
  "days": 30,
  "acceleration_factor": 100
}
```

**Response:**
```json
{
  "status": "success",
  "trajectory": [
    {
      "day": 1,
      "time_cycles": 1,
      "rul_hours": 349,
      "risk_zone": "green",
      "reading": {...}
    },
    {
      "day": 2,
      "time_cycles": 2,
      "rul_hours": 348,
      "risk_zone": "green",
      "reading": {...}
    },
    // ... 28 more days
  ],
  "summary": {
    "start_rul": 349,
    "end_rul": 1,
    "start_zone": "green",
    "end_zone": "red",
    "days_to_critical": 25
  }
}
```

### Frontend: Animation Loop

```javascript
// For each day in trajectory:
for (let i = 0; i < trajectory.length; i++) {
  // Update display with day's data
  setSensorStatus({...trajectory[i]});

  // Update progress bar
  setSpeedupProgress(((i + 1) / trajectory.length) * 100);

  // Update day counter
  setSpeedupDays(trajectory[i].day);

  // Wait 100ms before next frame
  await sleep(100);  // 30 days * 100ms = 3 seconds
}
```

---

## Customization

### Change Animation Speed
In `SensorDetailsPanel.js`, line ~237:
```javascript
await new Promise(resolve => setTimeout(resolve, 100));  // Change 100 to different value
// 50ms = 1.5 second animation
// 100ms = 3 second animation (default)
// 200ms = 6 second animation
```

### Change Degradation Days
In `SensorDetailsPanel.js`, line ~198:
```javascript
body: JSON.stringify({
  days: 30,  // Change to 7, 14, 60, etc.
  acceleration_factor: 100
})
```

### Change Degradation Rate Formula
In `backend/live_component_api.py`, line ~837:
```python
degradation_rate = 0.3 + avg_degradation_factor * 2.0  # Adjust coefficients
# Higher = faster degradation
# Lower = slower degradation
```

---

## Troubleshooting

### Button Doesn't Work
**Check**: Backend is running and `/api/live-component/status` works
```bash
curl http://localhost:5000/api/live-component/status
# Should return sensor data
```

### Animation is Too Fast/Slow
Adjust the `setTimeout` value (default 100ms per day)

### RUL Doesn't Change During Animation
**Check**: Backend is generating proper trajectory
```bash
curl -X POST http://localhost:5000/api/live-component/accelerate \
  -H "Content-Type: application/json" \
  -d '{"days": 30}'
# Should return 30 trajectory points
```

### Progress Bar Stuck
Browser cache issue - hard refresh (Cmd+Shift+R or Ctrl+Shift+R)

---

## Judge FAQ

**Q: Is this real?**
A: The RUL predictions are real - generated by your Gradient Boosting model. The timeline is accelerated (30 days in 3 seconds), but each prediction is what the model would actually predict.

**Q: Why does RUL decrease faster when temperature is high?**
A: Because your model learned from NASA turbofan data that higher temperature = faster degradation. The model is applying that physics to your simulation.

**Q: Can this predict real failures?**
A: In production, yes. Right now we're using synthetic baseline data, but the system is designed to accumulate real degradation data over time. Once deployed on actual grid sensors, it would make real predictions.

**Q: How long would 30 real days take?**
A: In real time, 30 days = 720 hours of operation. With 2-second polls, that's 1.3 million data points. The speedup button compresses that to 30 key decision points, showing the trajectory in 3 seconds.

---

## Summary

The speedup button is your **killer demo feature** because it:

✅ Shows the model working over a full component lifecycle
✅ Proves sensitivity to sensor inputs (knob position matters)
✅ Visualizes the failure progression in real-time
✅ Gives judges a visceral understanding of RUL countdown
✅ Completes in under 5 seconds (fits any demo slot)
✅ Works with any knob position (dynamic based on current state)

---

**Ready to amaze judges! 🚀**
