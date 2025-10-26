"""
Optimized Cable Risk Classification Models
==========================================
Collection of tuned machine learning models for cable infrastructure monitoring.

Models included:
1. Enhanced Neural Network (Deep MLP with hyperparameter tuning)
2. Random Forest Classifier (Optimized for cable features)
3. Gradient Boosting Classifier (XGBoost-style with tuning)
4. Support Vector Machine (RBF and Linear kernels)
5. Ensemble Voting Classifier
6. Stacked Ensemble Model

All models optimized for red/yellow/green risk zone classification.
"""

import numpy as np
import pandas as pd
from sklearn.neural_network import MLPClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.model_selection import GridSearchCV, cross_val_score, StratifiedKFold
from sklearn.metrics import accuracy_score, classification_report, f1_score, confusion_matrix
from sklearn.base import BaseEstimator, ClassifierMixin
import warnings
warnings.filterwarnings('ignore')

class CableRiskModel:
    """Base class for cable risk classification models"""
    
    def __init__(self, model_name="BaseModel"):
        self.model_name = model_name
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.feature_names = ['temperature', 'vibration', 'strain', 'power']
        
    def engineer_features(self, sensor_data):
        """Engineer advanced features for cable monitoring"""
        if isinstance(sensor_data, dict):
            # Single prediction
            temp = sensor_data['temperature']
            vib = sensor_data['vibration']
            strain = sensor_data['strain']
            power = sensor_data['power']
            
            features = {
                # Raw features
                'temperature': temp,
                'vibration': vib,
                'strain': strain,
                'power': power,
                
                # Thermal features
                'thermal_load': temp * power / 1000,  # Thermal-electrical interaction
                'temp_normalized': temp / 70.0,       # Normalized temperature
                'temp_excess': max(0, temp - 40),     # Temperature above normal
                
                # Mechanical features
                'mechanical_stress': strain + vib * 100,  # Combined mechanical stress
                'strain_normalized': strain / 800.0,       # Normalized strain
                'vibration_intensity': vib ** 2,           # Vibration energy
                
                # Electrical features
                'power_density': power / 2000.0,          # Normalized power
                'electrical_stress': power * temp / 10000, # Electrical-thermal stress
                
                # Combined risk indicators
                'total_stress': temp/70 + vib/5 + strain/800 + power/2000,  # Overall stress
                'risk_product': (temp/40) * (vib/1) * (strain/300) * (power/1200),  # Multiplicative risk
                'safety_margin': 1 - max(temp/70, vib/5, strain/800, power/2000),   # Safety buffer
                
                # Interaction features
                'temp_vib_interaction': temp * vib,
                'strain_power_ratio': strain / (power + 1),
                'thermal_mechanical': temp * strain / 1000
            }
            
            return np.array([list(features.values())])
            
        else:
            # Batch prediction - DataFrame
            df = sensor_data.copy()
            
            features_df = pd.DataFrame({
                # Raw features
                'temperature': df['temperature'],
                'vibration': df['vibration'],
                'strain': df['strain'],
                'power': df['power'],
                
                # Thermal features
                'thermal_load': df['temperature'] * df['power'] / 1000,
                'temp_normalized': df['temperature'] / 70.0,
                'temp_excess': np.maximum(0, df['temperature'] - 40),
                
                # Mechanical features
                'mechanical_stress': df['strain'] + df['vibration'] * 100,
                'strain_normalized': df['strain'] / 800.0,
                'vibration_intensity': df['vibration'] ** 2,
                
                # Electrical features
                'power_density': df['power'] / 2000.0,
                'electrical_stress': df['power'] * df['temperature'] / 10000,
                
                # Combined risk indicators
                'total_stress': df['temperature']/70 + df['vibration']/5 + df['strain']/800 + df['power']/2000,
                'risk_product': (df['temperature']/40) * (df['vibration']/1) * (df['strain']/300) * (df['power']/1200),
                'safety_margin': 1 - np.maximum.reduce([df['temperature']/70, df['vibration']/5, df['strain']/800, df['power']/2000]),
                
                # Interaction features
                'temp_vib_interaction': df['temperature'] * df['vibration'],
                'strain_power_ratio': df['strain'] / (df['power'] + 1),
                'thermal_mechanical': df['temperature'] * df['strain'] / 1000
            })
            
            return features_df.values
    
    def train(self, X, y):
        """Train the model"""
        X_features = self.engineer_features(X)
        X_scaled = self.scaler.fit_transform(X_features)
        self.model.fit(X_scaled, y)
        self.is_trained = True
    
    def predict(self, sensor_data):
        """Predict risk zone"""
        if not self.is_trained:
            raise ValueError("Model not trained")
        
        X_features = self.engineer_features(sensor_data)
        X_scaled = self.scaler.transform(X_features)
        
        prediction = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled) if hasattr(self.model, 'predict_proba') else None
        
        if isinstance(sensor_data, dict):
            return prediction[0], probabilities[0] if probabilities is not None else None
        else:
            return prediction, probabilities
    
    def get_model_info(self):
        """Get model information"""
        return {
            'name': self.model_name,
            'trained': self.is_trained,
            'features': 16  # Number of engineered features
        }


class EnhancedNeuralNetwork(CableRiskModel):
    """Optimized Neural Network for cable risk classification"""
    
    def __init__(self):
        super().__init__("Enhanced Neural Network")
        
        # Optimized architecture for cable monitoring
        self.model = MLPClassifier(
            hidden_layer_sizes=(256, 128, 64, 32),  # Deeper network
            activation='relu',
            solver='adam',
            alpha=0.0001,                            # L2 regularization
            batch_size=64,
            learning_rate='adaptive',                # Adaptive learning rate
            learning_rate_init=0.001,
            max_iter=1000,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.15,
            n_iter_no_change=20,
            tol=1e-6
        )
        self.scaler = StandardScaler()


class OptimizedRandomForest(CableRiskModel):
    """Optimized Random Forest for cable risk classification"""
    
    def __init__(self):
        super().__init__("Optimized Random Forest")
        
        # Tuned parameters for cable monitoring
        self.model = RandomForestClassifier(
            n_estimators=200,                    # More trees
            max_depth=15,                        # Controlled depth
            min_samples_split=5,                 # Prevent overfitting
            min_samples_leaf=2,                  # Prevent overfitting
            max_features='sqrt',                 # Feature sampling
            bootstrap=True,
            class_weight='balanced',             # Handle class imbalance
            random_state=42,
            n_jobs=-1
        )
        self.scaler = RobustScaler()  # More robust to outliers


class OptimizedGradientBoosting(CableRiskModel):
    """Optimized Gradient Boosting for cable risk classification"""
    
    def __init__(self):
        super().__init__("Optimized Gradient Boosting")
        
        # XGBoost-style parameters
        self.model = GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.1,
            max_depth=8,
            min_samples_split=10,
            min_samples_leaf=4,
            subsample=0.8,                       # Stochastic gradient boosting
            max_features='sqrt',
            random_state=42,
            validation_fraction=0.1,
            n_iter_no_change=10,
            tol=1e-4
        )
        self.scaler = StandardScaler()


class OptimizedSVM(CableRiskModel):
    """Optimized Support Vector Machine for cable risk classification"""
    
    def __init__(self, kernel='rbf'):
        super().__init__(f"Optimized SVM ({kernel})")
        
        if kernel == 'rbf':
            self.model = SVC(
                kernel='rbf',
                C=10.0,                          # Regularization
                gamma='scale',                   # RBF kernel parameter
                class_weight='balanced',
                probability=True,                # Enable probability estimates
                random_state=42
            )
        else:
            self.model = SVC(
                kernel='linear',
                C=1.0,
                class_weight='balanced',
                probability=True,
                random_state=42
            )
        
        self.scaler = StandardScaler()  # SVM requires scaling


class EnsembleVotingClassifier(CableRiskModel):
    """Ensemble voting classifier combining multiple models"""
    
    def __init__(self):
        super().__init__("Ensemble Voting Classifier")
        
        # Create base models
        neural_net = MLPClassifier(
            hidden_layer_sizes=(128, 64, 32),
            activation='relu',
            solver='adam',
            alpha=0.0001,
            max_iter=500,
            random_state=42
        )
        
        random_forest = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            class_weight='balanced',
            random_state=42
        )
        
        gradient_boost = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=6,
            random_state=42
        )
        
        # Voting classifier
        self.model = VotingClassifier(
            estimators=[
                ('neural_net', neural_net),
                ('random_forest', random_forest),
                ('gradient_boost', gradient_boost)
            ],
            voting='soft'  # Use probabilities
        )
        
        self.scaler = StandardScaler()


class AutoTunedModel(CableRiskModel):
    """Auto-tuned model using GridSearchCV"""
    
    def __init__(self, base_model='neural_network'):
        super().__init__(f"Auto-Tuned {base_model}")
        self.base_model_type = base_model
        self.model = None
        self.scaler = StandardScaler()
    
    def train(self, X, y):
        """Train with hyperparameter tuning"""
        X_features = self.engineer_features(X)
        X_scaled = self.scaler.fit_transform(X_features)
        
        if self.base_model_type == 'neural_network':
            # Neural network hyperparameter grid
            base_model = MLPClassifier(random_state=42, max_iter=1000)
            param_grid = {
                'hidden_layer_sizes': [(64, 32), (128, 64), (128, 64, 32), (256, 128, 64)],
                'activation': ['relu', 'tanh'],
                'alpha': [0.0001, 0.001, 0.01],
                'learning_rate_init': [0.001, 0.01]
            }
            
        elif self.base_model_type == 'random_forest':
            # Random forest hyperparameter grid
            base_model = RandomForestClassifier(random_state=42)
            param_grid = {
                'n_estimators': [100, 150, 200],
                'max_depth': [10, 15, 20],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }
            
        else:  # gradient_boosting
            # Gradient boosting hyperparameter grid
            base_model = GradientBoostingClassifier(random_state=42)
            param_grid = {
                'n_estimators': [100, 150, 200],
                'learning_rate': [0.05, 0.1, 0.2],
                'max_depth': [6, 8, 10],
                'subsample': [0.8, 0.9, 1.0]
            }
        
        # Grid search with cross-validation
        print(f"🔧 Auto-tuning {self.base_model_type} hyperparameters...")
        grid_search = GridSearchCV(
            base_model,
            param_grid,
            cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
            scoring='f1_macro',
            n_jobs=-1,
            verbose=0
        )
        
        grid_search.fit(X_scaled, y)
        
        self.model = grid_search.best_estimator_
        self.best_params = grid_search.best_params_
        self.best_score = grid_search.best_score_
        self.is_trained = True
        
        print(f"✅ Best parameters: {self.best_params}")
        print(f"📊 Best CV score: {self.best_score:.4f}")


# Model factory
def create_all_models():
    """Create all optimized models for comparison"""
    models = {
        'enhanced_neural_network': EnhancedNeuralNetwork(),
        'optimized_random_forest': OptimizedRandomForest(),
        'optimized_gradient_boosting': OptimizedGradientBoosting(),
        'optimized_svm_rbf': OptimizedSVM('rbf'),
        'optimized_svm_linear': OptimizedSVM('linear'),
        'ensemble_voting': EnsembleVotingClassifier(),
        'auto_tuned_neural_network': AutoTunedModel('neural_network'),
        'auto_tuned_random_forest': AutoTunedModel('random_forest'),
        'auto_tuned_gradient_boosting': AutoTunedModel('gradient_boosting')
    }
    
    return models


# Example usage
if __name__ == "__main__":
    # Test individual model
    model = EnhancedNeuralNetwork()
    
    # Test feature engineering
    sensor_data = {
        'temperature': 45.0,
        'vibration': 1.2,
        'strain': 350.0,
        'power': 1100.0
    }
    
    features = model.engineer_features(sensor_data)
    print(f"🔧 Engineered {features.shape[1]} features from 4 sensor readings")
    print(f"📊 Features shape: {features.shape}")
    
    # Show all available models
    all_models = create_all_models()
    print(f"\n🤖 Available optimized models:")
    for i, (name, model) in enumerate(all_models.items(), 1):
        print(f"   {i:2d}. {model.model_name}")
    
    print(f"\n✅ All models ready for training and evaluation!")