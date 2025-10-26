"""
Synthetic Component Degradation Generator
==========================================

Generates realistic 30+ day sensor degradation curves for a single component.
The component starts healthy and gradually degrades until failure.

This simulated data:
1. Shows realistic failure progression (green → yellow → red)
2. Feeds through the RUL model to establish baseline trajectory
3. Provides context for live hardware measurements
4. Demonstrates model sensitivity to degradation patterns
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json


class SyntheticComponentSimulator:
    """Generates realistic multi-day sensor degradation"""

    def __init__(self, component_id: str = "LIVE_COMPONENT_01", total_days: int = 35):
        """
        Initialize the simulator.

        Args:
            component_id: Component identifier
            total_days: How many days to simulate (typically 30-40)
        """
        self.component_id = component_id
        self.total_days = total_days
        self.total_hours = total_days * 24
        self.readings = []

        # Component parameters (these define degradation rate)
        self.initial_health = 0.95  # Starts 95% healthy
        self.failure_threshold = 0.05  # Fails at 5% health
        self.degradation_rate = (self.initial_health - self.failure_threshold) / self.total_hours

    def generate_sensor_value(self, time_hours: float, sensor_id: int, base_degradation: float) -> float:
        """
        Generate a single sensor reading with realistic degradation.

        Args:
            time_hours: Hours elapsed
            sensor_id: Which sensor (1-21)
            base_degradation: Overall component health (0-1)

        Returns:
            Sensor value with noise
        """
        # Different sensors have different baseline ranges
        sensor_ranges = {
            # Critical sensors (first 5) - more sensitive to degradation
            1: (100, 150),  # Vibration amplitude
            2: (350, 500),  # Temperature-related
            3: (450, 600),  # Frequency response
            4: (50, 150),   # Phase shift
            5: (30, 100),   # Harmonic content
            # Mid-range sensors (6-15)
            6: (50, 100),
            7: (10, 50),
            8: (20, 60),
            9: (10, 40),
            10: (30, 80),
            11: (100, 200),
            12: (150, 300),
            13: (80, 150),
            14: (100, 200),
            15: (50, 120),
            # Lower priority sensors (16-21)
            16: (50, 120),
            17: (30, 80),
            18: (40, 100),
            19: (25, 60),
            20: (35, 90),
            21: (25, 70),
        }

        min_val, max_val = sensor_ranges.get(sensor_id, (50, 100))
        baseline = (min_val + max_val) / 2

        # Degradation effect: sensors worsen as health decreases
        degradation_impact = (1 - base_degradation) * (max_val - baseline) * 0.8
        value = baseline + degradation_impact

        # Add realistic noise (sensors are noisy)
        noise = np.random.normal(0, (max_val - min_val) * 0.05)
        value = value + noise

        # Clamp to reasonable range
        value = np.clip(value, min_val, max_val * 1.2)

        return float(value)

    def generate_readings(self, readings_per_day: int = 12) -> pd.DataFrame:
        """
        Generate a full 30+ day degradation curve.

        Args:
            readings_per_day: How many sensor readings per day (12 = every 2 hours)

        Returns:
            DataFrame with columns: timestamp, component_id, sensor_1...21, op_setting_1-3, time_cycles, rul_true
        """
        self.readings = []
        total_readings = self.total_days * readings_per_day

        print(f"🔄 Generating {total_readings} readings over {self.total_days} days...")

        # Cycle through time
        start_time = datetime.utcnow() - timedelta(days=self.total_days)

        for i in range(total_readings):
            time_hours = i * (24 / readings_per_day)  # Hours elapsed
            current_time = start_time + timedelta(hours=time_hours)

            # Component health decreases linearly (realistic for run-to-failure data)
            health = self.initial_health - (self.degradation_rate * time_hours)
            health = np.clip(health, self.failure_threshold, self.initial_health)

            # Generate operational settings (relatively stable)
            op_setting_1 = 42.0 + np.random.normal(0, 2)  # Temperature setpoint
            op_setting_2 = 0.84 + np.random.normal(0, 0.05)  # Speed ratio
            op_setting_3 = 100.0 + np.random.normal(0, 5)  # Load

            # Generate all 21 sensor readings
            reading = {
                "timestamp": current_time.isoformat() + "Z",
                "component_id": self.component_id,
                "time_cycles": int(time_hours * 10),  # Convert to "cycles"
                "max_cycles": int(self.total_hours * 10),  # Will fail at this point
                "op_setting_1": float(op_setting_1),
                "op_setting_2": float(op_setting_2),
                "op_setting_3": float(op_setting_3),
            }

            # Generate 21 sensors
            for sensor_id in range(1, 22):
                value = self.generate_sensor_value(time_hours, sensor_id, health)
                reading[f"sensor_{sensor_id}"] = value

            # Calculate true RUL (cycles remaining until failure)
            cycles_elapsed = reading["time_cycles"]
            max_cycles = reading["max_cycles"]
            rul_true = max(0, max_cycles - cycles_elapsed)
            reading["rul_true"] = rul_true

            self.readings.append(reading)

        df = pd.DataFrame(self.readings)
        print(f"✅ Generated {len(df)} readings")
        print(f"   Time range: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
        print(f"   RUL range: {df['rul_true'].min():.0f} to {df['rul_true'].max():.0f} cycles")

        return df

    def get_latest_reading(self) -> dict:
        """Get the most recent sensor reading (current component state)"""
        if not self.readings:
            return None
        return self.readings[-1].copy()

    def get_historical_df(self) -> pd.DataFrame:
        """Get all historical readings as DataFrame"""
        return pd.DataFrame(self.readings)

    def export_to_json(self, filepath: str):
        """Export all readings to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.readings, f, indent=2)
        print(f"✅ Exported {len(self.readings)} readings to {filepath}")

    def get_degradation_summary(self) -> dict:
        """Get summary of degradation trajectory"""
        df = pd.DataFrame(self.readings)

        # Average sensor values over time
        first_third = df.iloc[:len(df)//3]
        last_third = df.iloc[-len(df)//3:]

        # Calculate average degradation per sensor
        sensor_degradation = {}
        for i in range(1, 22):
            col = f"sensor_{i}"
            if col in first_third.columns:
                early_avg = first_third[col].mean()
                late_avg = last_third[col].mean()
                degradation = ((late_avg - early_avg) / early_avg * 100) if early_avg != 0 else 0
                sensor_degradation[col] = {
                    "early_avg": float(early_avg),
                    "late_avg": float(late_avg),
                    "percent_change": float(degradation)
                }

        return {
            "component_id": self.component_id,
            "total_days": self.total_days,
            "total_readings": len(df),
            "initial_rul_cycles": int(df['rul_true'].iloc[0]),
            "final_rul_cycles": int(df['rul_true'].iloc[-1]),
            "sensor_degradation": sensor_degradation
        }


class LiveComponentTracker:
    """Tracks the current state of the live component"""

    def __init__(self, component_id: str, location: dict = None):
        """
        Initialize tracker.

        Args:
            component_id: Component identifier
            location: Dict with lat/lon (optional)
        """
        self.component_id = component_id
        self.location = location or {"lat": 34.0522, "lon": -118.2437}
        self.current_reading = None
        self.rul_prediction = None
        self.last_update = None

    def update_from_hardware(self, sensor_dict: dict, rul_prediction: dict):
        """
        Update the component state from hardware reading + RUL prediction.

        Args:
            sensor_dict: Dict with sensor_1...21, op_setting_1-3, time_cycles
            rul_prediction: Dict with rul_hours, rul_cycles, risk_zone, etc.
        """
        self.current_reading = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "component_id": self.component_id,
            **sensor_dict
        }
        self.rul_prediction = rul_prediction
        self.last_update = datetime.utcnow()

    def get_state(self) -> dict:
        """Get current component state"""
        return {
            "component_id": self.component_id,
            "location": self.location,
            "current_reading": self.current_reading,
            "rul_prediction": self.rul_prediction,
            "last_update": self.last_update.isoformat() if self.last_update else None
        }

    def to_dict(self) -> dict:
        """Export state as dict"""
        return self.get_state()


# Global instances
degradation_sim = None
live_tracker = None


# Module-level state (persists across Flask requests)
_component_state = {
    "degradation_sim": None,
    "live_tracker": None,
    "initialized": False
}


def initialize_live_component(component_id: str = "LIVE_COMPONENT_01", total_days: int = 35):
    """Initialize the live component system"""
    global _component_state

    print(f"\n🔧 Initializing Live Component System")
    print(f"   Component: {component_id}")
    print(f"   Simulation period: {total_days} days")

    # Create simulator
    sim = SyntheticComponentSimulator(component_id, total_days)
    historical_df = sim.generate_readings()

    # Create tracker with LA grid location
    tracker = LiveComponentTracker(
        component_id,
        location={"lat": 34.0522, "lon": -118.2437, "name": "LA Downtown Grid"}
    )

    # Store in module-level state
    _component_state["degradation_sim"] = sim
    _component_state["live_tracker"] = tracker
    _component_state["initialized"] = True

    # Initialize from the last historical reading
    last_reading = sim.get_latest_reading()
    if last_reading:
        # Use historical data as starting point for hardware
        print(f"\n✅ Live component initialized from historical data:")
        print(f"   Last reading timestamp: {last_reading['timestamp']}")
        print(f"   Starting RUL (true): {last_reading['rul_true']:.0f} cycles")

    return sim, tracker


def get_component_state():
    """Get the current component state"""
    return _component_state
