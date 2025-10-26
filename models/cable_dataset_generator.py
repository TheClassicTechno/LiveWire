"""
Cable Risk Dataset Generator
============================
Generates realistic cable monitoring sensor data with proper risk classification.

Cable Infrastructure Monitoring Parameters:
- Temperature: Infrastructure thermal stress (15-70°C)
- Vibration: Structural oscillations (0.05-5.0g)
- Strain: Mechanical stress (50-800µε)
- Power: Electrical load (200-2000W)

Risk Zone Classification:
- Green (Normal): Safe operating conditions
- Yellow (Warning): Elevated risk requiring monitoring
- Red (Critical): Immediate intervention required
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random

class CableDatasetGenerator:
    """Generate realistic cable monitoring datasets with proper risk classification"""
    
    def __init__(self, random_seed=42):
        """Initialize the cable dataset generator"""
        np.random.seed(random_seed)
        random.seed(random_seed)
        
        # Cable operating thresholds based on industry standards
        self.thresholds = {
            # Temperature thresholds (°C)
            'temp_green_max': 40,    # Normal operation
            'temp_yellow_max': 55,   # Warning zone
            'temp_red_min': 55,      # Critical zone
            
            # Vibration thresholds (g-force)
            'vib_green_max': 1.0,    # Normal vibration
            'vib_yellow_max': 2.5,   # Elevated vibration
            'vib_red_min': 2.5,      # Dangerous vibration
            
            # Strain thresholds (µε - microstrain)
            'strain_green_max': 300, # Normal mechanical stress
            'strain_yellow_max': 500,# Warning level stress
            'strain_red_min': 500,   # Critical stress
            
            # Power thresholds (W)
            'power_green_max': 1200, # Normal load
            'power_yellow_max': 1600,# High load
            'power_red_min': 1600    # Overload
        }
        
        # Base operating points
        self.base_values = {
            'temperature': 25.0,  # °C
            'vibration': 0.2,     # g
            'strain': 150.0,      # µε
            'power': 800.0        # W
        }
        
    def generate_sensor_reading(self, risk_zone='green', time_of_day=12, weather_factor=1.0):
        """
        Generate a single sensor reading for specified risk zone
        
        Args:
            risk_zone: 'green', 'yellow', or 'red'
            time_of_day: Hour (0-23) for diurnal effects
            weather_factor: Weather severity multiplier (0.5-2.0)
        
        Returns:
            dict: Sensor readings
        """
        # Diurnal temperature variation
        temp_diurnal = 5 * np.sin(2 * np.pi * (time_of_day - 6) / 24)
        
        if risk_zone == 'green':
            # Normal operation with small variations
            temperature = self.base_values['temperature'] + temp_diurnal + np.random.normal(0, 3)
            vibration = self.base_values['vibration'] + abs(np.random.normal(0, 0.1)) * weather_factor
            strain = self.base_values['strain'] + np.random.normal(0, 30)
            power = self.base_values['power'] + np.random.normal(0, 100)
            
            # Ensure values stay in green zone
            temperature = np.clip(temperature, 15, self.thresholds['temp_green_max'])
            vibration = np.clip(vibration, 0.05, self.thresholds['vib_green_max'])
            strain = np.clip(strain, 50, self.thresholds['strain_green_max'])
            power = np.clip(power, 200, self.thresholds['power_green_max'])
            
        elif risk_zone == 'yellow':
            # Warning zone - elevated but not critical
            temperature = np.random.uniform(self.thresholds['temp_green_max'], 
                                          self.thresholds['temp_yellow_max']) + temp_diurnal
            vibration = np.random.uniform(self.thresholds['vib_green_max'],
                                        self.thresholds['vib_yellow_max']) * weather_factor
            strain = np.random.uniform(self.thresholds['strain_green_max'],
                                     self.thresholds['strain_yellow_max'])
            power = np.random.uniform(self.thresholds['power_green_max'],
                                    self.thresholds['power_yellow_max'])
            
        else:  # red zone
            # Critical zone - dangerous conditions
            temperature = self.thresholds['temp_red_min'] + abs(np.random.normal(0, 8)) + temp_diurnal
            vibration = self.thresholds['vib_red_min'] + abs(np.random.normal(0, 1.0)) * weather_factor
            strain = self.thresholds['strain_red_min'] + abs(np.random.normal(0, 100))
            power = self.thresholds['power_red_min'] + abs(np.random.normal(0, 200))
            
            # Cap extreme values
            temperature = min(temperature, 70)
            vibration = min(vibration, 5.0)
            strain = min(strain, 800)
            power = min(power, 2000)
        
        return {
            'temperature': round(temperature, 2),
            'vibration': round(vibration, 3),
            'strain': round(strain, 1),
            'power': round(power, 1)
        }
    
    def classify_risk_zone(self, sensor_data):
        """
        Classify risk zone based on sensor thresholds
        
        Args:
            sensor_data: Dict with sensor readings
            
        Returns:
            str: 'green', 'yellow', or 'red'
        """
        temp = sensor_data['temperature']
        vib = sensor_data['vibration']
        strain = sensor_data['strain']
        power = sensor_data['power']
        
        # Count critical conditions
        critical_count = 0
        if temp >= self.thresholds['temp_red_min']: critical_count += 1
        if vib >= self.thresholds['vib_red_min']: critical_count += 1
        if strain >= self.thresholds['strain_red_min']: critical_count += 1
        if power >= self.thresholds['power_red_min']: critical_count += 1
        
        # Count warning conditions
        warning_count = 0
        if temp >= self.thresholds['temp_green_max']: warning_count += 1
        if vib >= self.thresholds['vib_green_max']: warning_count += 1
        if strain >= self.thresholds['strain_green_max']: warning_count += 1
        if power >= self.thresholds['power_green_max']: warning_count += 1
        
        # Classification logic
        if critical_count >= 2:  # 2+ critical conditions = red
            return 'red'
        elif critical_count >= 1 or warning_count >= 3:  # 1 critical or 3+ warnings = yellow
            return 'yellow'
        else:
            return 'green'
    
    def generate_balanced_dataset(self, n_samples=5000, green_ratio=0.6, yellow_ratio=0.25, red_ratio=0.15):
        """
        Generate a balanced dataset with specified distribution
        
        Args:
            n_samples: Total number of samples
            green_ratio: Proportion of green samples
            yellow_ratio: Proportion of yellow samples
            red_ratio: Proportion of red samples
            
        Returns:
            pd.DataFrame: Generated dataset
        """
        print(f"🔧 Generating {n_samples} cable monitoring samples...")
        print(f"📊 Distribution: {green_ratio*100:.1f}% green, {yellow_ratio*100:.1f}% yellow, {red_ratio*100:.1f}% red")
        
        data = []
        labels = []
        
        # Calculate sample counts
        n_green = int(n_samples * green_ratio)
        n_yellow = int(n_samples * yellow_ratio)
        n_red = n_samples - n_green - n_yellow
        
        # Generate samples for each zone
        zones = ['green'] * n_green + ['yellow'] * n_yellow + ['red'] * n_red
        random.shuffle(zones)
        
        for i, target_zone in enumerate(zones):
            # Vary time of day and weather
            time_of_day = random.randint(0, 23)
            weather_factor = random.uniform(0.7, 1.5)
            
            # Generate sensor reading
            sensor_data = self.generate_sensor_reading(target_zone, time_of_day, weather_factor)
            
            # Verify classification (sometimes adjust to match target)
            actual_zone = self.classify_risk_zone(sensor_data)
            
            # If mismatch, regenerate with more extreme values
            if actual_zone != target_zone:
                sensor_data = self.generate_sensor_reading(target_zone, time_of_day, weather_factor * 1.2)
                actual_zone = self.classify_risk_zone(sensor_data)
            
            data.append(sensor_data)
            labels.append(actual_zone)
            
            if (i + 1) % 1000 == 0:
                print(f"✓ Generated {i + 1}/{n_samples} samples")
        
        # Create DataFrame
        df = pd.DataFrame(data)
        df['risk_zone'] = labels
        df['sample_id'] = range(len(df))
        
        # Add timestamp
        base_time = datetime.now() - timedelta(days=30)
        df['timestamp'] = [base_time + timedelta(minutes=i*5) for i in range(len(df))]
        
        # Verify distribution
        zone_counts = df['risk_zone'].value_counts()
        print(f"\n📈 Final distribution:")
        for zone in ['green', 'yellow', 'red']:
            count = zone_counts.get(zone, 0)
            percentage = count / len(df) * 100
            print(f"   {zone.upper():6s}: {count:4d} samples ({percentage:5.1f}%)")
        
        return df
    
    def generate_time_series_dataset(self, n_components=10, days=7, samples_per_hour=12):
        """
        Generate time series dataset for multiple cable components
        
        Args:
            n_components: Number of cable components to simulate
            days: Number of days to simulate
            samples_per_hour: Sampling frequency
            
        Returns:
            pd.DataFrame: Time series dataset
        """
        print(f"🕒 Generating time series for {n_components} components over {days} days")
        
        all_data = []
        start_time = datetime.now() - timedelta(days=days)
        
        for comp_id in range(1, n_components + 1):
            component_name = f"CABLE_{comp_id:03d}"
            
            # Each component has different degradation pattern
            degradation_rate = random.uniform(0.0001, 0.001)  # Per hour
            base_risk = random.uniform(0.1, 0.3)
            
            current_time = start_time
            end_time = start_time + timedelta(days=days)
            
            while current_time < end_time:
                hours_elapsed = (current_time - start_time).total_seconds() / 3600
                
                # Progressive degradation
                degradation_factor = 1 + degradation_rate * hours_elapsed
                
                # Time-based risk (higher at peak hours)
                hour = current_time.hour
                time_risk = 0.3 * np.sin(2 * np.pi * (hour - 6) / 24) + 0.5
                
                # Combined risk
                total_risk = (base_risk + time_risk) * degradation_factor
                
                # Determine risk zone
                if total_risk > 0.8:
                    target_zone = 'red'
                elif total_risk > 0.5:
                    target_zone = 'yellow'
                else:
                    target_zone = 'green'
                
                # Generate sensor data
                weather_factor = random.uniform(0.8, 1.4)
                sensor_data = self.generate_sensor_reading(target_zone, hour, weather_factor)
                
                # Add to dataset
                row = sensor_data.copy()
                row['component_id'] = component_name
                row['timestamp'] = current_time
                row['risk_zone'] = self.classify_risk_zone(sensor_data)
                row['hours_elapsed'] = hours_elapsed
                
                all_data.append(row)
                
                # Next sample
                current_time += timedelta(minutes=60//samples_per_hour)
        
        df = pd.DataFrame(all_data)
        print(f"✅ Generated {len(df)} time series samples")
        
        return df


# Test the generator
if __name__ == "__main__":
    generator = CableDatasetGenerator()
    
    # Generate test dataset
    df = generator.generate_balanced_dataset(n_samples=1000)
    
    print(f"\n📊 Dataset shape: {df.shape}")
    print(f"📋 Columns: {list(df.columns)}")
    print(f"\n🔍 Sample data:")
    print(df.head())
    
    print(f"\n📈 Risk zone statistics:")
    for zone in ['green', 'yellow', 'red']:
        zone_data = df[df['risk_zone'] == zone]
        if len(zone_data) > 0:
            print(f"\n{zone.upper()} Zone:")
            print(f"  Temperature: {zone_data['temperature'].mean():.1f}°C ± {zone_data['temperature'].std():.1f}")
            print(f"  Vibration:   {zone_data['vibration'].mean():.2f}g ± {zone_data['vibration'].std():.2f}")
            print(f"  Strain:      {zone_data['strain'].mean():.0f}µε ± {zone_data['strain'].std():.0f}")
            print(f"  Power:       {zone_data['power'].mean():.0f}W ± {zone_data['power'].std():.0f}")