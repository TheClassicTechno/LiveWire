"""
Enhanced Cascade Failure Model Training
=======================================

Specialized approach for cascade failure prediction using:
- Graph neural network concepts
- Network topology analysis
- Cascade propagation modeling
- Risk spreading simulation
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

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.neural_network import MLPClassifier
import networkx as nx


def load_and_analyze_cascade_data():
    """Load cascade failure data with enhanced analysis"""
    print("📊 Loading and analyzing cascade failure dataset...")
    
    df = pd.read_csv("data/power_grid_dataset_with_cascade_failures.csv")
    print(f"✓ Loaded {len(df)} grid nodes")
    
    # Parse neighbors list
    df['neighbors'] = df['neighbors'].apply(ast.literal_eval)
    df['neighbor_count'] = df['neighbors'].apply(len)
    
    # Status distribution
    status_dist = df['status'].value_counts()
    print(f"✓ Node status: {dict(status_dist)}")
    print(f"✓ Damage rate: {status_dist['damaged'] / len(df) * 100:.1f}%")
    
    return df


def engineer_advanced_cascade_features(df):
    """Engineer advanced features for cascade failure prediction"""
    print("🔧 Engineering advanced cascade features...")
    
    # Basic load and capacity features
    df['demand_capacity_ratio'] = df['demand'] / df['capacity']
    df['capacity_margin'] = df['capacity'] - df['demand']
    df['capacity_utilization'] = np.clip(df['demand_capacity_ratio'], 0, 1)
    df['overload_risk'] = np.where(df['demand'] > df['capacity'], 1, 0)
    df['load_stress'] = np.maximum(0, df['demand'] - df['capacity']) / df['capacity']
    
    # Create network graph for topology analysis
    G = nx.Graph()
    for idx, row in df.iterrows():
        G.add_node(row['node_id'], **row.to_dict())
        for neighbor in row['neighbors']:
            if neighbor <= len(df):  # Only add if neighbor exists
                G.add_edge(row['node_id'], neighbor)
    
    print(f"✓ Network: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # Advanced network centrality measures
    degree_centrality = nx.degree_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G)
    closeness_centrality = nx.closeness_centrality(G)
    eigenvector_centrality = nx.eigenvector_centrality(G, max_iter=1000)
    pagerank = nx.pagerank(G)
    
    # Local clustering
    clustering = nx.clustering(G)
    
    # Calculate local efficiency for each node
    local_efficiency = {}
    for node in G.nodes():
        neighbors = list(G.neighbors(node))
        if len(neighbors) < 2:
            local_efficiency[node] = 0.0
        else:
            subgraph = G.subgraph(neighbors)
            if len(subgraph.edges()) == 0:
                local_efficiency[node] = 0.0
            else:
                # Simple local efficiency approximation
                possible_edges = len(neighbors) * (len(neighbors) - 1) / 2
                actual_edges = len(subgraph.edges())
                local_efficiency[node] = actual_edges / possible_edges if possible_edges > 0 else 0.0
    
    # Add network metrics to dataframe
    df['degree_centrality'] = df['node_id'].map(degree_centrality)
    df['betweenness_centrality'] = df['node_id'].map(betweenness_centrality)
    df['closeness_centrality'] = df['node_id'].map(closeness_centrality)
    df['eigenvector_centrality'] = df['node_id'].map(eigenvector_centrality)
    df['pagerank'] = df['node_id'].map(pagerank)
    df['clustering_coefficient'] = df['node_id'].map(clustering)
    df['local_efficiency'] = df['node_id'].map(local_efficiency)
    
    # Spatial features
    df['distance_from_center'] = np.sqrt((df['x_coordinate'] - 50)**2 + (df['y_coordinate'] - 50)**2)
    df['grid_edge_distance'] = np.minimum(
        np.minimum(df['x_coordinate'], 100 - df['x_coordinate']),
        np.minimum(df['y_coordinate'], 100 - df['y_coordinate'])
    )
    
    # Identify damaged nodes for cascade analysis
    damaged_nodes = set(df[df['status'] == 'damaged']['node_id'])
    
    # Cascade propagation features
    def calculate_cascade_metrics(row):
        neighbors = row['neighbors']
        if not neighbors:
            return {
                'neighbor_damage_ratio': 0,
                'neighbor_avg_load': 0,
                'neighbor_max_load': 0,
                'cascade_exposure': 0,
                'network_isolation': 1
            }
        
        # Neighbor damage analysis
        damaged_neighbors = sum(1 for n in neighbors if n in damaged_nodes)
        neighbor_damage_ratio = damaged_neighbors / len(neighbors)
        
        # Neighbor load analysis
        neighbor_loads = []
        for n in neighbors:
            if n <= len(df):
                neighbor_row = df[df['node_id'] == n]
                if not neighbor_row.empty:
                    neighbor_loads.append(neighbor_row.iloc[0]['demand_capacity_ratio'])
        
        if neighbor_loads:
            neighbor_avg_load = np.mean(neighbor_loads)
            neighbor_max_load = np.max(neighbor_loads)
        else:
            neighbor_avg_load = 0
            neighbor_max_load = 0
        
        # Cascade exposure (weighted by neighbor importance)
        cascade_exposure = 0
        for n in neighbors:
            if n in damaged_nodes:
                neighbor_importance = degree_centrality.get(n, 0)
                cascade_exposure += neighbor_importance
        
        # Network isolation risk
        network_isolation = 1 / (len(neighbors) + 1)
        
        return {
            'neighbor_damage_ratio': neighbor_damage_ratio,
            'neighbor_avg_load': neighbor_avg_load,
            'neighbor_max_load': neighbor_max_load,
            'cascade_exposure': cascade_exposure,
            'network_isolation': network_isolation
        }
    
    # Apply cascade metrics
    cascade_metrics = df.apply(calculate_cascade_metrics, axis=1, result_type='expand')
    df = pd.concat([df, cascade_metrics], axis=1)
    
    # Composite vulnerability scores
    df['structural_vulnerability'] = (
        df['betweenness_centrality'] * 0.3 +
        df['degree_centrality'] * 0.3 +
        df['eigenvector_centrality'] * 0.2 +
        df['pagerank'] * 0.2
    )
    
    df['load_vulnerability'] = (
        df['demand_capacity_ratio'] * 0.4 +
        df['load_stress'] * 0.3 +
        df['neighbor_max_load'] * 0.3
    )
    
    df['cascade_vulnerability'] = (
        df['neighbor_damage_ratio'] * 0.4 +
        df['cascade_exposure'] * 0.3 +
        df['network_isolation'] * 0.3
    )
    
    df['overall_vulnerability'] = (
        df['structural_vulnerability'] * 0.35 +
        df['load_vulnerability'] * 0.35 +
        df['cascade_vulnerability'] * 0.30
    )
    
    # Risk spreading simulation
    df['cascade_risk_spread'] = df['overall_vulnerability'] * df['neighbor_damage_ratio']
    
    print(f"✓ Engineered {len([col for col in df.columns if col not in ['node_id', 'neighbors', 'status']])} features")
    
    return df


def create_cascade_failure_models():
    """Create specialized models for cascade failure prediction"""
    
    # Model 1: Enhanced Random Forest with cascade-specific tuning
    rf_model = RandomForestClassifier(
        n_estimators=200,
        max_depth=15,
        min_samples_split=3,
        min_samples_leaf=2,
        max_features='sqrt',
        class_weight='balanced',
        random_state=42
    )
    
    # Model 2: Gradient Boosting for cascade patterns
    gb_model = GradientBoostingClassifier(
        n_estimators=150,
        learning_rate=0.15,
        max_depth=10,
        min_samples_split=4,
        min_samples_leaf=2,
        subsample=0.8,
        random_state=42
    )
    
    # Model 3: Neural Network for complex cascade interactions
    nn_model = MLPClassifier(
        hidden_layer_sizes=(64, 32, 16),
        activation='relu',
        solver='adam',
        alpha=0.001,
        learning_rate='adaptive',
        max_iter=500,
        random_state=42
    )
    
    return {
        'Random Forest': rf_model,
        'Gradient Boosting': gb_model,
        'Neural Network': nn_model
    }


def select_cascade_features(df):
    """Select most relevant features for cascade failure prediction"""
    
    # Core cascade features
    cascade_features = [
        # Load and capacity
        'demand_capacity_ratio', 'capacity_utilization', 'load_stress',
        'overload_risk', 'capacity_margin',
        
        # Network topology
        'degree_centrality', 'betweenness_centrality', 'closeness_centrality',
        'eigenvector_centrality', 'pagerank', 'clustering_coefficient',
        
        # Spatial
        'distance_from_center', 'grid_edge_distance',
        
        # Cascade propagation
        'neighbor_damage_ratio', 'neighbor_avg_load', 'neighbor_max_load',
        'cascade_exposure', 'network_isolation',
        
        # Composite vulnerabilities
        'structural_vulnerability', 'load_vulnerability', 'cascade_vulnerability',
        'overall_vulnerability', 'cascade_risk_spread'
    ]
    
    return cascade_features


def test_enhanced_cascade_models(df):
    """Test enhanced models on cascade failure data"""
    print("\n🔥 === ENHANCED CASCADE FAILURE TESTING ===")
    
    # Feature selection
    feature_cols = select_cascade_features(df)
    print(f"✓ Using {len(feature_cols)} cascade-specific features")
    
    # Prepare features and labels
    X = df[feature_cols].fillna(0)
    y = df['status']  # 'active' or 'damaged'
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.3, random_state=42, stratify=y
    )
    
    print(f"Train: {len(X_train)} samples, Test: {len(X_test)} samples")
    print(f"Train distribution: {pd.Series(y_train).value_counts().to_dict()}")
    print(f"Test distribution: {pd.Series(y_test).value_counts().to_dict()}")
    
    # Get models
    models = create_cascade_failure_models()
    results = {}
    
    # Test each model
    for name, model in models.items():
        print(f"\n🔧 Testing {name}...")
        
        start_time = datetime.now()
        model.fit(X_train, y_train)
        train_time = (datetime.now() - start_time).total_seconds()
        
        start_time = datetime.now()
        y_pred = model.predict(X_test)
        pred_time = (datetime.now() - start_time).total_seconds()
        
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        
        results[name] = {
            'accuracy': accuracy,
            'train_time': train_time,
            'pred_time': pred_time,
            'predictions': y_pred,
            'report': report,
            'model': model
        }
        
        print(f"   ✅ {name} Accuracy: {accuracy:.3f} ({accuracy*100:.1f}%)")
        print(f"   ⏱️  Training time: {train_time:.1f}s")
        print(f"   🎯 F1-Score: {report['weighted avg']['f1-score']:.3f}")
        
        # Detailed damage detection metrics
        damage_precision = report.get('damaged', {}).get('precision', 0)
        damage_recall = report.get('damaged', {}).get('recall', 0)
        damage_f1 = report.get('damaged', {}).get('f1-score', 0)
        
        print(f"   🔥 Damage Detection - P: {damage_precision:.3f}, R: {damage_recall:.3f}, F1: {damage_f1:.3f}")
    
    return results, feature_cols, scaler


def analyze_feature_importance(results, feature_cols):
    """Analyze feature importance for cascade failure prediction"""
    print("\n📊 === FEATURE IMPORTANCE ANALYSIS ===")
    
    # Get feature importance from Random Forest
    rf_model = results['Random Forest']['model']
    feature_importance = rf_model.feature_importances_
    
    # Create importance dataframe
    importance_df = pd.DataFrame({
        'feature': feature_cols,
        'importance': feature_importance
    }).sort_values('importance', ascending=False)
    
    print("🔝 Top 10 Most Important Features:")
    for i, row in importance_df.head(10).iterrows():
        print(f"   {row['feature']:<30} {row['importance']:.4f}")
    
    # Save feature importance
    importance_df.to_csv("data/processed/cascade_feature_importance.csv", index=False)
    print(f"✅ Feature importance saved to: data/processed/cascade_feature_importance.csv")
    
    return importance_df


def save_enhanced_results(results):
    """Save enhanced cascade failure results"""
    
    results_data = []
    for name, result in results.items():
        results_data.append({
            'model': f'Enhanced {name}',
            'dataset': 'cascade_failures_enhanced',
            'accuracy': result['accuracy'],
            'f1_score': result['report']['weighted avg']['f1-score'],
            'damage_precision': result['report'].get('damaged', {}).get('precision', 0),
            'damage_recall': result['report'].get('damaged', {}).get('recall', 0),
            'damage_f1': result['report'].get('damaged', {}).get('f1-score', 0),
            'training_time': result['train_time'],
            'prediction_time': result['pred_time']
        })
    
    results_df = pd.DataFrame(results_data)
    results_df.to_csv("data/processed/enhanced_cascade_results.csv", index=False)
    print(f"✅ Enhanced results saved to: data/processed/enhanced_cascade_results.csv")
    
    return results_df


def main():
    """Main function for enhanced cascade failure testing"""
    print("🔥 === ENHANCED CASCADE FAILURE PREDICTION ===\n")
    
    # Load and analyze data
    df = load_and_analyze_cascade_data()
    
    # Engineer advanced features
    df = engineer_advanced_cascade_features(df)
    
    # Test enhanced models
    results, feature_cols, scaler = test_enhanced_cascade_models(df)
    
    # Analyze feature importance
    importance_df = analyze_feature_importance(results, feature_cols)
    
    # Save results
    results_df = save_enhanced_results(results)
    
    # Results summary
    print("\n" + "="*70)
    print("🔥 ENHANCED CASCADE FAILURE RESULTS")
    print("="*70)
    
    best_model = None
    best_accuracy = 0
    
    for name, result in results.items():
        accuracy = result['accuracy']
        f1_score = result['report']['weighted avg']['f1-score']
        damage_f1 = result['report'].get('damaged', {}).get('f1-score', 0)
        
        print(f"\n{name}:")
        print(f"  ✅ Accuracy: {accuracy*100:.1f}%")
        print(f"  🎯 Overall F1-Score: {f1_score:.3f}")
        print(f"  🔥 Damage Detection F1: {damage_f1:.3f}")
        print(f"  ⏱️  Training: {result['train_time']:.1f}s")
        
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_model = name
    
    # Performance ratings
    def get_rating(accuracy):
        if accuracy > 0.85:
            return "🟢 EXCELLENT"
        elif accuracy > 0.70:
            return "🟡 GOOD"
        elif accuracy > 0.60:
            return "🟠 MODERATE"
        else:
            return "🔴 POOR"
    
    print(f"\n🏆 BEST MODEL: {best_model} ({best_accuracy*100:.1f}%)")
    print(f"🏅 Performance: {get_rating(best_accuracy)}")
    
    # Comparison with previous results
    print(f"\n📈 IMPROVEMENT ANALYSIS:")
    print(f"   Best Enhanced Model: {best_accuracy*100:.1f}%")
    print(f"   Previous Cascade Models: ~56.7%")
    print(f"   Previous Power Grid Models: ~51.7%")
    print(f"   Improvement: +{(best_accuracy - 0.567)*100:.1f}% over cascade baseline")
    
    if best_accuracy > 0.75:
        print(f"\n🎉 EXCELLENT: Enhanced features provide significant improvement!")
    elif best_accuracy > 0.65:
        print(f"\n✅ GOOD: Enhanced approach shows meaningful gains!")
    else:
        print(f"\n⚠️  Moderate improvement - cascade failures remain challenging!")
    
    # Top features summary
    print(f"\n🔍 TOP CASCADE PREDICTORS:")
    for i, row in importance_df.head(5).iterrows():
        print(f"   {i+1}. {row['feature']}")


if __name__ == "__main__":
    main()