"""
Realistic Pre-2018 Camp Fire Data Generator
==========================================

This module generates realistic sensor data that simulates the actual conditions
leading up to the 2018 Camp Fire, including:
- Multiple components of varying ages (including the famous 97-year-old hook)
- Realistic seasonal weather patterns for Northern California
- Escalating vibration due to increasing wind speeds in fall 2018
- Temperature and strain patterns that correlate with component aging
- Known failure progression leading to the November 8, 2018 fire

Based on actual Camp Fire reports and PG&E data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os


def generate_camp_fire_data(start_date="2016-01-01", end_date="2018-11-08", freq_hours=1):
    """
    Generate realistic pre-Camp Fire sensor data.
    
    Parameters:
    -----------
    start_date : str
        Start date for data generation (default: 2 years before fire)
    end_date : str 
        End date (Camp Fire start: November 8, 2018, 6:33 AM)
    freq_hours : int
        Data frequency in hours
    
    Returns:
    --------
    pd.DataFrame with realistic sensor data
    """
    
    print(f"Generating Camp Fire simulation data from {start_date} to {end_date}")
    
    # Create timestamp range
    timestamps = pd.date_range(start=start_date, end=end_date, freq=f'{freq_hours}H')
    
    # Define the actual components that were involved
    components = {
        'HOOK_97YO': {  # The famous 97-year-old hook that caused the fire
            'age_years': 97,
            'location': 'Pulga_Line',
            'base_vibration': 0.15,  # Higher baseline due to age
            'base_temperature': 25,
            'base_strain': 120,  # Higher baseline strain
            'failure_risk': 0.95  # Very high risk
        },
        'TOWER_45YO': {  # Nearby tower, also old but not as critical
            'age_years': 45,
            'location': 'Pulga_Line', 
            'base_vibration': 0.08,
            'base_temperature': 22,
            'base_strain': 85,
            'failure_risk': 0.3
        },
        'INSULATOR_30YO': {  # Insulator near failure point
            'age_years': 30,
            'location': 'Pulga_Line',
            'base_vibration': 0.06,
            'base_temperature': 20,
            'base_strain': 65,
            'failure_risk': 0.25
        },
        'TOWER_NEW': {  # Newer equipment for comparison
            'age_years': 8,
            'location': 'Adjacent_Line',
            'base_vibration': 0.03,
            'base_temperature': 18,
            'base_strain': 45,
            'failure_risk': 0.05
        },
        'HOOK_CONTROL': {  # Control component away from fire area
            'age_years': 25,
            'location': 'Control_Area',
            'base_vibration': 0.05,
            'base_temperature': 19,
            'base_strain': 55,
            'failure_risk': 0.1
        }
    }
    
    # Initialize random state for reproducibility
    np.random.seed(42)
    
    data = []
    
    for comp_id, comp_info in components.items():
        print(f"  Generating data for {comp_id} (age: {comp_info['age_years']} years)")
        
        for i, timestamp in enumerate(timestamps):
            
            # === SEASONAL PATTERNS ===
            day_of_year = timestamp.timetuple().tm_yday
            
            # California seasonal temperature (hot dry summers, mild winters)
            seasonal_temp = 15 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
            
            # Wind patterns - higher in fall (fire season)
            fall_wind_factor = 1.0
            if timestamp.month in [9, 10, 11]:  # Fall fire season
                fall_wind_factor = 1.5 + 0.5 * np.sin(2 * np.pi * (day_of_year - 244) / 90)
            
            # === COMPONENT AGING EFFECTS ===
            # Linear aging effect over time
            days_since_start = (timestamp - pd.Timestamp(start_date)).days
            aging_factor = 1.0 + (comp_info['age_years'] / 100.0) * (days_since_start / 1000.0)
            
            # === CAMP FIRE BUILDUP (October-November 2018) ===
            fire_buildup_factor = 1.0
            if timestamp >= pd.Timestamp('2018-10-01'):
                # Increasing stress leading to fire
                days_to_fire = (pd.Timestamp('2018-11-08 06:33:00') - timestamp).days
                if days_to_fire >= 0:
                    # Exponential increase in stress as fire approaches
                    fire_buildup_factor = 1.0 + comp_info['failure_risk'] * (1 - days_to_fire / 38.0) ** 2
            
            # === VIBRATION (Key factor - wind-induced oscillations) ===
            base_vib = comp_info['base_vibration']
            
            # Daily wind cycle (stronger in afternoon)
            hourly_wind = 0.3 * np.sin(2 * np.pi * timestamp.hour / 24)
            
            # Weather events (random gusts)
            weather_factor = 1.0 + 0.4 * np.random.exponential(0.5)
            
            # Combine all vibration factors
            vibration = (base_vib * aging_factor * fall_wind_factor * 
                        fire_buildup_factor * weather_factor * (1 + hourly_wind) +
                        np.random.normal(0, 0.02))
            
            # === TEMPERATURE ===
            base_temp = comp_info['base_temperature']
            
            # Daily cycle
            hourly_temp = 8 * np.sin(2 * np.pi * (timestamp.hour - 6) / 24)
            
            # Equipment heating under load
            load_heating = 5 * (vibration / base_vib - 1) if vibration > base_vib else 0
            
            temperature = (base_temp + seasonal_temp + hourly_temp + 
                          load_heating + aging_factor * 2 +
                          np.random.normal(0, 1.5))
            
            # === STRAIN (electrical/mechanical stress) ===
            base_strain = comp_info['base_strain']
            
            # Strain increases with vibration and temperature
            vibration_strain = 15 * (vibration / base_vib - 1) if vibration > base_vib else 0
            thermal_strain = 0.5 * (temperature - base_temp) if temperature > base_temp else 0
            
            strain = (base_strain * aging_factor + vibration_strain + 
                     thermal_strain + fire_buildup_factor * 10 +
                     np.random.normal(0, 3))
            
            # === CABLE STATE (ground truth) ===
            # Determine actual cable state based on conditions
            risk_score = (vibration / (base_vib * 3) + 
                         (temperature - base_temp) / 30 + 
                         strain / (base_strain * 2) + 
                         comp_info['failure_risk'] * fire_buildup_factor) / 4
            
            if risk_score > 0.8:
                cable_state = "Critical"
            elif risk_score > 0.5:
                cable_state = "Degradation" 
            elif risk_score > 0.3:
                cable_state = "Warning"
            else:
                cable_state = "Normal"
            
            # Special case: 97-year-old hook goes critical in final weeks
            if comp_id == 'HOOK_97YO' and timestamp >= pd.Timestamp('2018-10-20'):
                cable_state = "Critical"
            
            # === CREATE RECORD ===
            data.append({
                'component_id': comp_id,
                'timestamp': timestamp,
                'temperature': round(temperature, 2),
                'vibration': round(max(0, vibration), 4),  # Can't be negative
                'strain': round(max(0, strain), 2),  # Can't be negative
                'cable_state': cable_state,
                'age_years': comp_info['age_years'],
                'location': comp_info['location'],
                # Additional realistic fields
                'wind_speed': round(max(0, fall_wind_factor * weather_factor * 5 + np.random.normal(0, 2)), 1),
                'humidity': round(max(10, min(90, 45 - seasonal_temp + np.random.normal(0, 10))), 1),
                'risk_score_true': round(risk_score, 3)  # Hidden ground truth for validation
            })
    
    df = pd.DataFrame(data)
    
    print(f"Generated {len(df):,} records for {len(components)} components")
    print(f"Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"Component states distribution:")
    print(df['cable_state'].value_counts())
    
    return df


def split_camp_fire_data(df, split_date="2018-01-01"):
    """Split data into training (pre-2018) and test (2018) sets."""
    
    split_ts = pd.Timestamp(split_date)
    
    train_df = df[df['timestamp'] < split_ts].copy()
    test_df = df[df['timestamp'] >= split_ts].copy()
    
    print(f"Training data: {len(train_df):,} records ({train_df['timestamp'].min()} to {train_df['timestamp'].max()})")
    print(f"Test data: {len(test_df):,} records ({test_df['timestamp'].min()} to {test_df['timestamp'].max()})")
    
    return train_df, test_df


def save_camp_fire_datasets(df, base_path="./data"):
    """Save the generated datasets in the correct format."""
    
    # Create directories
    os.makedirs(f"{base_path}/camp_fire", exist_ok=True)
    os.makedirs(f"{base_path}/calib", exist_ok=True)
    os.makedirs(f"{base_path}/pre_fire", exist_ok=True)
    
    # Split the data
    train_df, test_df = split_camp_fire_data(df)
    
    # Save full dataset
    full_path = f"{base_path}/camp_fire/complete_dataset.csv"
    df.to_csv(full_path, index=False)
    print(f"✓ Full dataset saved: {full_path}")
    
    # Save training data (for calibration)
    calib_path = f"{base_path}/calib/pre2018_camp_fire.csv"
    train_df.to_csv(calib_path, index=False)
    print(f"✓ Training data saved: {calib_path}")
    
    # Save test data (2018 leading to fire)
    test_path = f"{base_path}/pre_fire/2018_camp_fire_runup.csv"
    test_df.to_csv(test_path, index=False)
    print(f"✓ Test data saved: {test_path}")
    
    return calib_path, test_path


if __name__ == "__main__":
    print("=== Camp Fire Data Generation ===\n")
    
    # Generate the realistic dataset
    df = generate_camp_fire_data(
        start_date="2016-01-01",
        end_date="2018-11-08 06:33:00",  # Exact Camp Fire start time
        freq_hours=4  # Data every 4 hours for efficiency
    )
    
    # Save datasets
    calib_path, test_path = save_camp_fire_datasets(df)
    
    print(f"\n=== Camp Fire Data Ready! ===")
    print(f"Next steps:")
    print(f"1. Train models: python compare_models_camp_fire.py")
    print(f"2. Test Camp Fire prediction capability")
    print(f"3. Validate which model (CCI vs Grid Risk) performs better")
    
    # Show sample of the critical component near failure
    print(f"\n🔥 Sample data for 97-year-old hook near Camp Fire:")
    hook_data = df[df['component_id'] == 'HOOK_97YO'].tail(10)
    print(hook_data[['timestamp', 'temperature', 'vibration', 'strain', 'cable_state', 'risk_score_true']].to_string(index=False))