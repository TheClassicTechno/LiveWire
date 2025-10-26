"""
Train Models on Power Grid Cascade Failure Dataset
==================================================

This dataset represents power grid nodes with:
- Spatial coordinates (x, y)
- Demand and capacity
- Node status (active/damaged)
- Network connectivity (neighbors)

This is much more realistic for power grid fault prediction!
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
import sys
import os
import ast
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

warnings.filterwarnings('ignore')

# Import both models
from models.grid_risk_model import CCIPipeline, CCIPipelineConfig
from models.legacy_model import CCIModel, timeseries_to_feature_matrix

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, precision_score, recall_score, f1_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import networkx as nx


def load_cascade_failure_data():
    """Load and analyze the cascade failure dataset"""
    print("Loading cascade failure dataset...")
    
    df = pd.read_csv("data/power_grid_dataset_with_cascade_failures.csv")
    print(f"✓ Loaded {len(df)} grid nodes")
    
    # Parse neighbors list
    df['neighbors'] = df['neighbors'].apply(ast.literal_eval)
    df['neighbor_count'] = df['neighbors'].apply(len)
    
    # Status distribution
    status_dist = df['status'].value_counts()
    print(f"✓ Node status distribution: {dict(status_dist)}")
    
    return df


def engineer_cascade_features(df):
    """Engineer features specific to cascade failures"""
    print("🔧 Engineering cascade failure features...")
    
    # Basic grid health indicators
    df['demand_capacity_ratio'] = df['demand'] / df['capacity']
    df['capacity_utilization'] = np.clip(df['demand_capacity_ratio'], 0, 1)
    df['overload_risk'] = np.where(df['demand'] > df['capacity'], 1, 0)
    
    # Network topology features
    df['degree_centrality'] = df['neighbor_count']
    
    # Create network graph for advanced features
    G = nx.Graph()
    for idx, row in df.iterrows():
        G.add_node(row['node_id'], **row.to_dict())
        for neighbor in row['neighbors']:
            if neighbor <= len(df):  # Only add if neighbor exists
                G.add_edge(row['node_id'], neighbor)
    
    print(f"✓ Created network graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges")
    
    # Calculate advanced network metrics
    betweenness = nx.betweenness_centrality(G)
    closeness = nx.closeness_centrality(G)
    clustering = nx.clustering(G)
    
    # Add network metrics to dataframe
    df['betweenness_centrality'] = df['node_id'].map(betweenness)
    df['closeness_centrality'] = df['node_id'].map(closeness)
    df['clustering_coefficient'] = df['node_id'].map(clustering)
    
    # Spatial features
    df['distance_from_center'] = np.sqrt((df['x_coordinate'] - 50)**2 + (df['y_coordinate'] - 50)**2)
    
    # Vulnerability indicators
    df['vulnerability_score'] = (
        df['demand_capacity_ratio'] * 0.4 +
        df['betweenness_centrality'] * 0.3 +
        (1 - df['clustering_coefficient']) * 0.3
    )
    
    # Cascade risk features
    damaged_nodes = set(df[df['status'] == 'damaged']['node_id'])
    
    def calculate_neighbor_damage_ratio(neighbors):
        if not neighbors:
            return 0
        damaged_neighbors = sum(1 for n in neighbors if n in damaged_nodes)
        return damaged_neighbors / len(neighbors)
    
    df['neighbor_damage_ratio'] = df['neighbors'].apply(calculate_neighbor_damage_ratio)
    
    # Cascade propagation risk
    df['cascade_risk'] = (
        df['vulnerability_score'] * 0.5 +
        df['neighbor_damage_ratio'] * 0.3 +
        df['overload_risk'] * 0.2
    )
    
    print(f"✓ Engineered {len([col for col in df.columns if col not in ['node_id', 'neighbors', 'status']])} features")
    
    return df


def prepare_cascade_grid_risk_data(df):
    """Prepare cascade data for Grid Risk Model"""
    print("⚡ Preparing cascade data for Grid Risk Model...")
    
    # Convert network data to time-series format for Grid Risk Model
    # We'll simulate temporal evolution of the grid
    
    time_series_data = []
    
    # Create multiple time snapshots showing cascade evolution
    for time_step in range(10):  # 10 time steps
        for idx, row in df.iterrows():
            record = {
                'component_id': f"NODE_{row['node_id']:03d}",
                'timestamp': pd.Timestamp('2024-01-01') + pd.Timedelta(hours=time_step),
                
                # Map grid features to sensor readings
                'vibration': row['vulnerability_score'],  # Vulnerability as vibration
                'temperature': row['demand_capacity_ratio'],  # Load stress as temperature
                'strain': row['cascade_risk'],  # Cascade risk as strain
                'cascade_risk': row['cascade_risk'],  # Keep cascade_risk for later use
                
                # Synthetic features
                'energy': 1.0 - row['capacity_utilization'],
                'processing_speed': row['closeness_centrality'],
                'age_years': 20 + time_step,  # Aging over time
                
                # Map damage status to cable state
                'cable_state': 'Critical' if row['status'] == 'damaged' else 'Normal'
            }
            time_series_data.append(record)
    
    grid_df = pd.DataFrame(time_series_data)
    
    # Add some degradation states for nodes at risk
    high_risk_mask = (grid_df['cascade_risk'] > 0.7) & (grid_df['cable_state'] == 'Normal')
    grid_df.loc[high_risk_mask, 'cable_state'] = 'Warning'
    
    medium_risk_mask = (grid_df['cascade_risk'] > 0.4) & (grid_df['cable_state'] == 'Normal')
    grid_df.loc[medium_risk_mask, 'cable_state'] = 'Degradation'
    
    # Sort by component and timestamp
    grid_df = grid_df.sort_values(['component_id', 'timestamp']).reset_index(drop=True)
    
    print(f"✓ Created {len(grid_df)} time-series records for Grid Risk Model")
    state_dist = grid_df['cable_state'].value_counts()
    print(f"✓ Cable state distribution: {dict(state_dist)}")
    
    return grid_df


def prepare_cascade_cci_data(df, sequence_length=8):
    """Prepare cascade data for CCI Model"""
    print(f"⚡ Preparing cascade data for CCI Model (sequence_length={sequence_length})...")
    
    # Create feature sequences for each node
    feature_cols = ['vulnerability_score', 'demand_capacity_ratio', 'cascade_risk', 
                   'neighbor_damage_ratio', 'betweenness_centrality']
    
    # Normalize features
    scaler = StandardScaler()
    feature_data = scaler.fit_transform(df[feature_cols])
    feature_df = pd.DataFrame(feature_data, columns=feature_cols)
    
    # Create sequences by simulating temporal evolution
    sequences = []
    labels = []
    
    # For each node, create a sequence showing evolution toward current state
    for idx, row in df.iterrows():
        # Create synthetic time evolution leading to current state
        base_features = feature_df.iloc[idx].values
        
        # Generate sequence showing progression
        sequence = []
        for t in range(sequence_length):
            # Add noise and trend toward final state
            progress = t / (sequence_length - 1)
            noise = np.random.normal(0, 0.1, len(base_features))
            step_features = base_features * progress + noise
            sequence.append(step_features)
        
        sequences.append(np.array(sequence))
        
        # Label based on final status
        if row['status'] == 'damaged':
            if row['cascade_risk'] > 0.8:
                labels.append('red')    # High cascade risk damage
            else:
                labels.append('yellow') # Moderate damage
        else:
            if row['cascade_risk'] > 0.6:
                labels.append('yellow') # At risk
            else:
                labels.append('green')  # Safe
    
    X = np.array(sequences)
    y = np.array(labels)
    
    print(f"✓ Created {len(X)} cascade sequences, shape: {X.shape}")
    print(f"✓ Label distribution: {dict(pd.Series(y).value_counts())}")
    
    return X, y


def create_cascade_grid_config():
    """Create optimized configuration for cascade failures"""
    config = CCIPipelineConfig()
    
    # Faster response for cascade events
    config.short_win = 3
    config.mid_win = 6
    config.long_win = 9
    
    # Balanced weights for cascade detection
    config.w_vibration = 0.5    # Vulnerability
    config.w_temperature = 0.3  # Load stress
    config.w_strain = 0.2       # Cascade risk
    
    # Sensitive thresholds for early warning
    config.yellow_q = 0.4
    config.red_q = 0.7
    
    return config


def test_cascade_models(df):
    """Test both models on cascade failure data"""
    print("\n⚡ === TESTING CASCADE FAILURE MODELS ===")
    
    # Split data - use random split since this is network data, not time series
    train_indices, test_indices = train_test_split(
        range(len(df)), test_size=0.3, random_state=42, 
        stratify=df['status']
    )
    
    train_df = df.iloc[train_indices].reset_index(drop=True)
    test_df = df.iloc[test_indices].reset_index(drop=True)
    
    print(f"Train nodes: {len(train_df)} ({train_df['status'].value_counts().to_dict()})")
    print(f"Test nodes: {len(test_df)} ({test_df['status'].value_counts().to_dict()})")
    
    # Test Grid Risk Model
    print("\n🔧 Testing Cascade Grid Risk Model...")
    
    train_df_grid = prepare_cascade_grid_risk_data(train_df)
    test_df_grid = prepare_cascade_grid_risk_data(test_df)
    
    config = create_cascade_grid_config()
    grid_model = CCIPipeline(config)
    
    start_time = datetime.now()
    grid_model.fit(train_df_grid)
    grid_train_time = (datetime.now() - start_time).total_seconds()
    
    # Score test data
    start_time = datetime.now()
    grid_predictions = grid_model.score(test_df_grid)
    grid_pred_time = (datetime.now() - start_time).total_seconds()
    
    # Evaluate Grid Risk Model (use last prediction for each node)
    test_node_predictions = grid_predictions.groupby('component_id').last()
    y_true_grid = test_df_grid.groupby('component_id')['cable_state'].last().values
    y_pred_grid = test_node_predictions['zone'].values
    
    # Map states to zones
    state_to_zone = {'Normal': 'green', 'Degradation': 'yellow', 'Warning': 'yellow', 'Critical': 'red'}
    y_true_grid_zones = [state_to_zone.get(state, 'green') for state in y_true_grid]
    grid_accuracy = accuracy_score(y_true_grid_zones, y_pred_grid)
    
    print(f"✓ Cascade Grid Risk Model Accuracy: {grid_accuracy:.3f} ({grid_accuracy*100:.1f}%)")
    
    # Test CCI Model
    print("\n🔧 Testing Cascade CCI Model...")
    
    X_train, y_train = prepare_cascade_cci_data(train_df)
    X_test, y_test = prepare_cascade_cci_data(test_df)
    
    # Use enhanced features for cascade prediction
    X_train_features = timeseries_to_feature_matrix(X_train)
    X_test_features = timeseries_to_feature_matrix(X_test)
    
    # Use ensemble classifier for better cascade prediction
    from sklearn.ensemble import VotingClassifier
    
    rf_clf = RandomForestClassifier(
        n_estimators=150, max_depth=12, min_samples_split=5,
        class_weight='balanced', random_state=42
    )
    
    gb_clf = GradientBoostingClassifier(
        n_estimators=100, learning_rate=0.1, max_depth=8,
        random_state=42
    )
    
    ensemble_clf = VotingClassifier([
        ('rf', rf_clf),
        ('gb', gb_clf)
    ], voting='soft')
    
    start_time = datetime.now()
    ensemble_clf.fit(X_train_features, y_train)
    cci_train_time = (datetime.now() - start_time).total_seconds()
    
    start_time = datetime.now()
    y_pred_cci = ensemble_clf.predict(X_test_features)
    cci_pred_time = (datetime.now() - start_time).total_seconds()
    
    cci_accuracy = accuracy_score(y_test, y_pred_cci)
    
    print(f"✓ Cascade CCI Model Accuracy: {cci_accuracy:.3f} ({cci_accuracy*100:.1f}%)")
    
    # Detailed metrics
    print(f"\n📊 Cascade Grid Risk Model Metrics:")
    grid_report = classification_report(y_true_grid_zones, y_pred_grid, output_dict=True, zero_division=0)
    print(f"   Precision: {grid_report['weighted avg']['precision']:.3f}")
    print(f"   Recall: {grid_report['weighted avg']['recall']:.3f}")
    print(f"   F1-Score: {grid_report['weighted avg']['f1-score']:.3f}")
    
    print(f"\n📊 Cascade CCI Model Metrics:")
    cci_report = classification_report(y_test, y_pred_cci, output_dict=True, zero_division=0)
    print(f"   Precision: {cci_report['weighted avg']['precision']:.3f}")
    print(f"   Recall: {cci_report['weighted avg']['recall']:.3f}")
    print(f"   F1-Score: {cci_report['weighted avg']['f1-score']:.3f}")
    
    # Cascade-specific metrics
    print(f"\n🔥 Cascade Failure Detection:")
    
    # Grid Risk Model damage detection
    grid_damage_true = [1 if zone == 'red' else 0 for zone in y_true_grid_zones]
    grid_damage_pred = [1 if zone == 'red' else 0 for zone in y_pred_grid]
    
    if sum(grid_damage_true) > 0:
        grid_damage_precision = precision_score(grid_damage_true, grid_damage_pred, zero_division=0)
        grid_damage_recall = recall_score(grid_damage_true, grid_damage_pred, zero_division=0)
        print(f"   Grid Risk Damage Detection - Precision: {grid_damage_precision:.3f}, Recall: {grid_damage_recall:.3f}")
    
    # CCI Model damage detection
    cci_damage_true = [1 if zone == 'red' else 0 for zone in y_test]
    cci_damage_pred = [1 if zone == 'red' else 0 for zone in y_pred_cci]
    
    if sum(cci_damage_true) > 0:
        cci_damage_precision = precision_score(cci_damage_true, cci_damage_pred, zero_division=0)
        cci_damage_recall = recall_score(cci_damage_true, cci_damage_pred, zero_division=0)
        print(f"   CCI Damage Detection - Precision: {cci_damage_precision:.3f}, Recall: {cci_damage_recall:.3f}")
    
    return {
        'grid_risk': {
            'accuracy': grid_accuracy,
            'train_time': grid_train_time,
            'pred_time': grid_pred_time,
            'predictions': y_pred_grid,
            'report': grid_report
        },
        'cci_model': {
            'accuracy': cci_accuracy,
            'train_time': cci_train_time,
            'pred_time': cci_pred_time,
            'predictions': y_pred_cci,
            'report': cci_report
        }
    }


def main():
    """Main function for cascade failure testing"""
    print("🔥 === CASCADE FAILURE POWER GRID TESTING ===\n")
    
    # Load cascade failure data
    df = load_cascade_failure_data()
    
    # Engineer cascade-specific features
    df = engineer_cascade_features(df)
    
    # Test models on cascade failures
    results = test_cascade_models(df)
    
    # Results comparison
    print("\n" + "="*70)
    print("🔥 CASCADE FAILURE RESULTS")
    print("="*70)
    
    grid_acc = results['grid_risk']['accuracy']
    cci_acc = results['cci_model']['accuracy']
    
    print(f"\nCascade Grid Risk Model:")
    print(f"  ✅ Accuracy: {grid_acc*100:.1f}%")
    print(f"  ⏱️  Training time: {results['grid_risk']['train_time']:.1f}s")
    print(f"  ⚡ Prediction time: {results['grid_risk']['pred_time']:.1f}s")
    print(f"  🎯 F1-Score: {results['grid_risk']['report']['weighted avg']['f1-score']:.3f}")
    
    print(f"\nCascade CCI Model:")
    print(f"  ✅ Accuracy: {cci_acc*100:.1f}%")
    print(f"  ⏱️  Training time: {results['cci_model']['train_time']:.1f}s")
    print(f"  ⚡ Prediction time: {results['cci_model']['pred_time']:.1f}s")
    print(f"  🎯 F1-Score: {results['cci_model']['report']['weighted avg']['f1-score']:.3f}")
    
    # Performance ratings
    def get_rating(accuracy):
        if accuracy > 0.85:
            return "🟢 EXCELLENT"
        elif accuracy > 0.70:
            return "🟡 GOOD"
        elif accuracy > 0.55:
            return "🟠 MODERATE"
        else:
            return "🔴 POOR"
    
    print(f"\n🏅 Performance Ratings:")
    print(f"   Cascade Grid Risk Model: {get_rating(grid_acc)}")
    print(f"   Cascade CCI Model: {get_rating(cci_acc)}")
    
    # Winner
    if grid_acc > cci_acc:
        winner = "Cascade Grid Risk Model"
        margin = (grid_acc - cci_acc) * 100
    else:
        winner = "Cascade CCI Model"
        margin = (cci_acc - grid_acc) * 100
    
    print(f"\n🏆 WINNER: {winner} (by {margin:.1f}%)")
    
    # Save results
    results_df = pd.DataFrame([
        {
            'dataset': 'cascade_failures',
            'model': 'Cascade Grid Risk Model',
            'accuracy': grid_acc,
            'f1_score': results['grid_risk']['report']['weighted avg']['f1-score'],
            'training_time': results['grid_risk']['train_time'],
            'prediction_time': results['grid_risk']['pred_time']
        },
        {
            'dataset': 'cascade_failures',
            'model': 'Cascade CCI Model',
            'accuracy': cci_acc,
            'f1_score': results['cci_model']['report']['weighted avg']['f1-score'],
            'training_time': results['cci_model']['train_time'],
            'prediction_time': results['cci_model']['pred_time']
        }
    ])
    
    results_df.to_csv("data/processed/cascade_failure_results.csv", index=False)
    print(f"\n✅ Results saved to: data/processed/cascade_failure_results.csv")
    
    # Comparison with previous results
    print(f"\n📈 COMPARISON WITH PREVIOUS POWER GRID RESULTS:")
    print(f"   Cascade Grid Risk: {grid_acc*100:.1f}% (vs 44.5% baseline)")
    print(f"   Cascade CCI: {cci_acc*100:.1f}% (vs 51.7% baseline)")
    
    if grid_acc > 0.7 or cci_acc > 0.7:
        print(f"\n🎉 EXCELLENT: Cascade dataset provides much better learning signal!")
    elif grid_acc > 0.6 or cci_acc > 0.6:
        print(f"\n✅ GOOD: Cascade failures are more predictable than general faults!")
    else:
        print(f"\n⚠️  Still challenging, but cascade patterns may be more learnable!")


if __name__ == "__main__":
    main()