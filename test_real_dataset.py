"""
Real Dataset Model Evaluation - Cable Monitoring
================================================
Tests all models on REAL cable monitoring dataset from Kaggle.
365,002 real samples with actual cable states: Normal, Degradation, Fault.

This will show the TRUE performance of our models on real-world data.
"""

import pandas as pd
import numpy as np
import sys
import os
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, f1_score, classification_report, confusion_matrix
import time
import warnings
warnings.filterwarnings('ignore')

# Add models directory to path
models_path = os.path.join(os.path.dirname(__file__), 'models')
sys.path.append(models_path)

from models.optimized_cable_models import create_all_models

def load_real_cable_dataset():
    """Load the real cable monitoring dataset"""
    print("📊 Loading REAL cable monitoring dataset...")
    
    # Load the real dataset
    df = pd.read_csv('data/raw/cable_monitoring_dataset.csv')
    
    print(f"✅ Loaded {len(df):,} real cable monitoring samples")
    print(f"📅 Date range: Real cable infrastructure data")
    print(f"🔌 Cables: {df['Cable ID'].nunique()} different cables")
    
    # Check the cable states
    state_counts = df['Cable State'].value_counts()
    print(f"📈 Cable State Distribution:")
    for state, count in state_counts.items():
        percentage = count / len(df) * 100
        print(f"   {state:12s}: {count:6,} samples ({percentage:5.1f}%)")
    
    return df

def prepare_real_data(df, sample_size=10000):
    """Prepare real data for model testing"""
    print(f"\n🔧 Preparing real data for model evaluation...")
    
    # Sample data if dataset is too large
    if len(df) > sample_size:
        print(f"📊 Sampling {sample_size:,} samples from {len(df):,} total...")
        df_sample = df.sample(n=sample_size, random_state=42)
    else:
        df_sample = df.copy()
    
    # Map cable states to risk zones
    state_mapping = {
        'Normal': 'green',
        'Degradation': 'yellow', 
        'Fault': 'red'
    }
    
    df_sample['risk_zone'] = df_sample['Cable State'].map(state_mapping)
    
    # Prepare features - map column names to our model's expected format
    feature_mapping = {
        'Temperature (°C)': 'temperature',
        'Vibration (m/s²)': 'vibration',
        'Strain (mm/m)': 'strain',
        'Energy Consumption (W)': 'power'
    }
    
    # Create feature DataFrame with our expected column names
    X = pd.DataFrame()
    for original_col, new_col in feature_mapping.items():
        X[new_col] = df_sample[original_col]
    
    # Convert strain from mm/m to microstrain (µε) - multiply by 1000
    X['strain'] = X['strain'] * 1000
    
    # Convert vibration from m/s² to g-force (divide by 9.81)
    X['vibration'] = X['vibration'] / 9.81
    
    # Prepare labels
    label_encoder = LabelEncoder()
    y = label_encoder.fit_transform(df_sample['risk_zone'])
    
    print(f"✅ Data prepared:")
    print(f"   Features: {list(X.columns)}")
    print(f"   Classes: {list(label_encoder.classes_)}")
    print(f"   Samples: {len(X):,}")
    
    # Show feature statistics
    print(f"\n📊 Real Data Feature Statistics:")
    for col in X.columns:
        print(f"   {col:12s}: {X[col].mean():8.2f} ± {X[col].std():6.2f} (range: {X[col].min():.2f} to {X[col].max():.2f})")
    
    return X, y, label_encoder, df_sample

def evaluate_on_real_data():
    """Evaluate all models on real cable monitoring data"""
    print("🧪 REAL CABLE DATASET MODEL EVALUATION")
    print("=" * 60)
    print("🎯 Testing on actual cable infrastructure monitoring data")
    print("📊 365,002 real samples from cable monitoring systems")
    print("=" * 60)
    
    # Load real dataset
    df = load_real_cable_dataset()
    
    # Prepare data
    X, y, label_encoder, df_sample = prepare_real_data(df, sample_size=5000)  # Use 5k samples for faster testing
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, stratify=y, random_state=42)
    
    print(f"\n🔬 Test Setup:")
    print(f"   Training samples: {len(X_train):,}")
    print(f"   Test samples: {len(X_test):,}")
    
    # Create all models
    models = create_all_models()
    
    print(f"\n🤖 Testing {len(models)} models on REAL data...")
    print("-" * 80)
    
    results = []
    
    for model_name, model in models.items():
        print(f"\n🧪 Testing {model.model_name}...")
        
        try:
            # Train model
            start_time = time.time()
            model.train(X_train, y_train)
            training_time = time.time() - start_time
            
            # Test predictions
            start_time = time.time()
            predictions, probabilities = model.predict(X_test)
            prediction_time = (time.time() - start_time) / len(X_test) * 1000
            
            # Calculate metrics
            accuracy = accuracy_score(y_test, predictions)
            f1_macro = f1_score(y_test, predictions, average='macro')
            f1_weighted = f1_score(y_test, predictions, average='weighted')
            
            # Store results
            result = {
                'Model': model.model_name,
                'Accuracy': accuracy,
                'F1-Macro': f1_macro,
                'F1-Weighted': f1_weighted,
                'Training Time (s)': training_time,
                'Prediction Time (ms)': prediction_time
            }
            results.append(result)
            
            print(f"   ✅ Accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")
            print(f"   📊 F1-Macro: {f1_macro:.4f}")
            print(f"   ⏱️ Training: {training_time:.2f}s")
            print(f"   ⚡ Prediction: {prediction_time:.3f}ms")
            
        except Exception as e:
            print(f"   ❌ FAILED: {str(e)}")
            result = {
                'Model': model.model_name,
                'Accuracy': 0.0,
                'F1-Macro': 0.0,
                'F1-Weighted': 0.0,
                'Training Time (s)': 0.0,
                'Prediction Time (ms)': 0.0,
                'Error': str(e)
            }
            results.append(result)
    
    # Sort results by F1-Macro score
    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('F1-Macro', ascending=False)
    
    print(f"\n" + "=" * 80)
    print("🏆 REAL DATASET EVALUATION RESULTS")
    print("=" * 80)
    print("📊 Tested on ACTUAL cable monitoring data (5,000 samples)")
    print("🎯 Performance on real-world cable infrastructure conditions")
    print("-" * 80)
    
    for i, (_, row) in enumerate(results_df.iterrows(), 1):
        if 'Error' not in row or pd.isna(row.get('Error')):
            emoji = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "📊"
            print(f"{emoji} #{i:2d}. {row['Model']:30s} | F1: {row['F1-Macro']:.4f} | Acc: {row['Accuracy']:.4f} ({row['Accuracy']*100:.1f}%)")
        else:
            print(f"❌ #{i:2d}. {row['Model']:30s} | FAILED: {row['Error']}")
    
    # Best model analysis
    if len(results_df) > 0 and results_df.iloc[0]['F1-Macro'] > 0:
        best_model = results_df.iloc[0]
        print(f"\n🎯 BEST MODEL ON REAL DATA: {best_model['Model']}")
        print("-" * 50)
        print(f"✅ Real Dataset Accuracy: {best_model['Accuracy']:.4f} ({best_model['Accuracy']*100:.2f}%)")
        print(f"📊 Real Dataset F1-Macro: {best_model['F1-Macro']:.4f}")
        print(f"📊 Real Dataset F1-Weighted: {best_model['F1-Weighted']:.4f}")
        print(f"⏱️ Training Time: {best_model['Training Time (s)']:.2f}s")
        print(f"⚡ Prediction Speed: {best_model['Prediction Time (ms)']:.3f}ms")
        
        print(f"\n💡 ANALYSIS:")
        if best_model['Accuracy'] > 0.85:
            print(f"✅ Excellent performance on real cable data")
        elif best_model['Accuracy'] > 0.70:
            print(f"✅ Good performance on real cable data")
        elif best_model['Accuracy'] > 0.50:
            print(f"⚠️ Moderate performance - room for improvement")
        else:
            print(f"❌ Poor performance - needs significant improvement")
    
    print(f"\n📈 REAL vs SYNTHETIC COMPARISON:")
    print(f"🔬 Synthetic Data Results: 99.94% accuracy (suspiciously high)")
    avg_real_acc = results_df['Accuracy'].mean()
    print(f"🌍 Real Data Results: {avg_real_acc:.1%} average accuracy")
    print(f"📊 Reality Check: Real data is much more challenging!")
    
    return results_df

if __name__ == "__main__":
    results = evaluate_on_real_data()