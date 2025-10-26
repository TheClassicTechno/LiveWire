# Raspberry Pi Integration Guide

**For**: Your teammate with the Raspberry Pi and hardware knobs
**Goal**: Send sensor data to Elasticsearch so the dashboard shows real-time RUL changes

---

## What the Pi Needs to Do

1. **Read sensor values** from your hardware (temperature, vibration, strain, power)
2. **Send to Elasticsearch** in the correct format
3. **That's it!** The backend handles RUL calculation

---

## The Data Format

Your Elasticsearch data should look like this:

```json
{
  "sensor_data": {
    "temperature": 25.5,
    "vibration": 0.12,
    "strain": 105.0
  },
  "@timestamp": "2025-10-26T12:00:34.123Z"
}
```

**Fields explained** (3 knobs = 3 sensors):
- `sensor_data.temperature`: Knob 1 - Current temperature in °C (typical range: 15-45°C)
- `sensor_data.vibration`: Knob 2 - Vibration in g-force (typical range: 0.05-2.0)
- `sensor_data.strain`: Knob 3 - Mechanical strain in microstrain µε (typical range: 50-500)
- `@timestamp`: ISO 8601 timestamp with timezone

---

## Python Code Example

```python
import json
import time
from datetime import datetime
from elasticsearch import Elasticsearch

# Configure Elasticsearch
ES_ENDPOINT = "https://your-elastic-cloud-endpoint.us-west1.gcp.elastic.cloud"
ES_API_KEY = "your-api-key-here"
ES_INDEX = "metrics-livewire.sensors-default"

# Initialize Elasticsearch client
es = Elasticsearch(
    hosts=[ES_ENDPOINT],
    api_key=ES_API_KEY,
    verify_certs=True
)

def read_sensors():
    """
    Read sensor values from your 3 knobs.
    Replace this with actual knob reads from GPIO.
    """
    # TODO: Read from your actual knobs via GPIO
    # For now, return mock data simulating knob positions
    return {
        "temperature": 15 + (time.time() % 30),  # Knob 1: 15-45°C
        "vibration": 0.05 + (time.time() % 1.95) * 0.1,  # Knob 2: 0.05-2.0 g
        "strain": 50 + (time.time() % 450)  # Knob 3: 50-500 µε
    }

def send_to_elasticsearch(sensor_values):
    """
    Send sensor readings to Elasticsearch.
    """
    try:
        doc = {
            "sensor_data": sensor_values,
            "@timestamp": datetime.utcnow().isoformat() + "Z"
        }

        # Index the document
        result = es.index(index=ES_INDEX, body=doc)
        print(f"✅ Sent to Elasticsearch: {doc}")
        return True

    except Exception as e:
        print(f"❌ Error sending to Elasticsearch: {e}")
        return False

def main():
    """
    Main loop: read sensors and send to Elasticsearch every 5 seconds.
    """
    print("Starting Raspberry Pi sensor stream...")
    print(f"Sending to: {ES_INDEX}")

    while True:
        try:
            # Read sensor values
            sensors = read_sensors()

            # Send to Elasticsearch
            send_to_elasticsearch(sensors)

            # Wait before next reading
            time.sleep(5)

        except KeyboardInterrupt:
            print("\nStopping...")
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
```

---

## Setup Steps

### 1. Install Elasticsearch Client

```bash
pip install elasticsearch
```

### 2. Get Elasticsearch Credentials

You need:
- `ELASTIC_ENDPOINT`: The Elasticsearch URL (e.g., https://your-cloud-id.us-west1.gcp.elastic.cloud)
- `ELASTIC_API_KEY`: API key for authentication

If you don't have these, ask whoever set up the Elasticsearch instance.

### 3. Test Connection

```python
from elasticsearch import Elasticsearch

es = Elasticsearch(
    hosts=["your-endpoint"],
    api_key="your-key"
)

try:
    info = es.info()
    print("✅ Connected to Elasticsearch!")
except Exception as e:
    print(f"❌ Connection failed: {e}")
```

### 4. Send Test Data

```python
es.index(
    index="metrics-livewire.sensors-default",
    body={
        "sensor_data": {
            "temperature": 25.0,  # Knob 1
            "vibration": 0.1,     # Knob 2
            "strain": 100.0       # Knob 3
        },
        "@timestamp": "2025-10-26T12:00:00Z"
    }
)
print("✅ Test data sent!")
```

### 5. Check the Dashboard

Go to `http://localhost:3000/live-component` (or your deployment URL):
- Initialize the component
- Look for the badge under "Live Component Monitoring System"
- If sending data, should see: **"Data from Elasticsearch (Live Hardware)"** with a green pulsing dot
- RUL should change as your sensor values change

---

## Mapping Your 3 Knobs to Sensor Values

Your Raspberry Pi has 3 knobs. Here's how to map them:

### Knob 1 → Temperature
```python
# Read knob 1 from GPIO ADC (0-1023 or 0-4095 depending on ADC)
knob_1_raw = read_adc_channel(0)  # 0 to max_adc_value
knob_1_normalized = knob_1_raw / max_adc_value  # 0 to 1

# Map to temperature range: 15-45°C
temperature = 15 + (knob_1_normalized * 30)
sensor_data["temperature"] = temperature
```

### Knob 2 → Vibration
```python
# Read knob 2 from GPIO ADC
knob_2_raw = read_adc_channel(1)
knob_2_normalized = knob_2_raw / max_adc_value

# Map to vibration range: 0.05-2.0 g-force
vibration = 0.05 + (knob_2_normalized * 1.95)
sensor_data["vibration"] = vibration
```

### Knob 3 → Strain
```python
# Read knob 3 from GPIO ADC
knob_3_raw = read_adc_channel(2)
knob_3_normalized = knob_3_raw / max_adc_value

# Map to strain range: 50-500 µε (microstrain)
strain = 50 + (knob_3_normalized * 450)
sensor_data["strain"] = strain
```

**Complete example**:
```python
def read_sensors_from_knobs():
    """Read 3 knob values and convert to sensor ranges"""
    max_adc = 4095  # For ADS1115 or similar; adjust for your ADC

    knob_1 = read_adc_channel(0) / max_adc
    knob_2 = read_adc_channel(1) / max_adc
    knob_3 = read_adc_channel(2) / max_adc

    return {
        "temperature": 15 + (knob_1 * 30),    # 15-45°C
        "vibration": 0.05 + (knob_2 * 1.95),  # 0.05-2.0
        "strain": 50 + (knob_3 * 450)         # 50-500
    }
```

---

## Troubleshooting

### "Connection refused"
- Check Elasticsearch endpoint is correct
- Check API key is valid
- Check firewall/network access to Elasticsearch

### "Index does not exist"
- The index `metrics-livewire.sensors-default` needs to exist
- Ask your DevOps team to create it, or Elasticsearch will auto-create on first write

### "Data not appearing on dashboard"
1. Check data was sent: `es.search(index="metrics-livewire.sensors-default", size=1)`
2. Check timestamp is recent (within 5 minutes for dashboard to pick it up)
3. Check dashboard is running: `http://localhost:3000/live-component`
4. Check browser console for errors (F12)

### "RUL not changing when I change sensors"
- This is **normal** and expected!
- The RUL model is 88% time-based (learned from NASA turbofan data)
- Sensor changes have small impact compared to elapsed time
- But the system IS working - you can verify by checking the API response

---

## Complete Main Loop Example

When you have physical knobs set up:

```python
import RPi.GPIO as GPIO
import time
from datetime import datetime
from elasticsearch import Elasticsearch

# Elasticsearch setup
es = Elasticsearch(
    hosts=["your-endpoint"],
    api_key="your-key"
)

def read_knobs():
    """Read your 3 physical knobs and convert to sensor values"""
    # Adjust these based on your ADC setup (ADS1115, MCP3008, etc.)
    max_adc = 4095

    knob_1 = read_adc_channel(0) / max_adc  # Temperature knob
    knob_2 = read_adc_channel(1) / max_adc  # Vibration knob
    knob_3 = read_adc_channel(2) / max_adc  # Strain knob

    return {
        "temperature": 15 + (knob_1 * 30),    # 15-45°C
        "vibration": 0.05 + (knob_2 * 1.95),  # 0.05-2.0 g
        "strain": 50 + (knob_3 * 450)         # 50-500 µε
    }

def send_to_elasticsearch(sensor_values):
    """Send sensor data to Elasticsearch"""
    try:
        doc = {
            "sensor_data": sensor_values,
            "@timestamp": datetime.utcnow().isoformat() + "Z"
        }
        es.index(index="metrics-livewire.sensors-default", body=doc)
        print(f"✅ Sent: temp={sensor_values['temperature']:.1f}°C, "
              f"vib={sensor_values['vibration']:.2f}g, "
              f"strain={sensor_values['strain']:.0f}µε")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main loop: read knobs and send to Elasticsearch every 1 second"""
    print("Starting sensor stream from 3 knobs...")

    while True:
        try:
            sensors = read_knobs()
            send_to_elasticsearch(sensors)
            time.sleep(1)  # Send every second for smooth real-time updates
        except KeyboardInterrupt:
            print("\nStopping...")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
```

**Key points**:
- Send every 1 second for responsive real-time updates
- 3 knobs = 3 sensor values only
- Dashboard auto-refreshes every 10 seconds to pick up changes
- When you turn a knob, the RUL will update within 10 seconds

---

## Performance Tips

1. **Send data every 1-5 seconds** - More frequent is better for real-time feel
2. **Use local variable fallbacks** if Elasticsearch is temporarily down
3. **Log every Nth send** to avoid log spam
4. **Monitor Elasticsearch index size** - It will grow continuously

---

## What NOT to Do

❌ **Don't send RUL/confidence to Elasticsearch**
- The backend calculates this from your sensor data
- You only send: temperature, vibration, strain (3 fields)

❌ **Don't normalize sensor values to 0-1 range**
- Send actual physical units (°C, g-force, µε)
- Send values in the ranges: temp 15-45, vib 0.05-2.0, strain 50-500
- Backend handles mapping to internal sensor format

❌ **Don't send extra fields**
- Stick to: temperature, vibration, strain
- No power, no RUL, no confidence - only what the knobs control

✅ **DO send every 1 second**
- 1 Hz frequency is good for real-time feel
- Dashboard polls every 10 seconds anyway

---

## Next Steps

1. Get Elasticsearch endpoint and API key
2. Run the example code above
3. Verify data appears on dashboard
4. Map physical knob values to sensor ranges
5. Integrate with your actual hardware

---

**Questions?** Check the main README and dashboard logs for errors.
