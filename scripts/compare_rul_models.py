"""
Compare RUL Prediction Models: Gradient Boosting vs LSTM
========================================================

Tests both approaches on CMaps datasets with stratified sampling.
Shows accuracy improvements and trade-offs.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import pandas as pd
import time
from utils.rul_data_loader import CMapsDataLoader
from models.rul_predictor import RULPredictor
from models.rul_predictor_lstm import RULPredictorLSTM


def test_gradient_boosting(dataset: str = "FD001", stratified: bool = True) -> dict:
    """Test Gradient Boosting RUL predictor"""
    print(f"\n{'='*70}")
    print(f"Gradient Boosting - {dataset} (stratified={stratified})")
    print(f"{'='*70}")

    # Load data
    loader = CMapsDataLoader()
    train_df = loader.load_training_data(dataset)
    test_df = loader.load_test_data(dataset)

    # Train
    print("\n🔧 Training Gradient Boosting...")
    start_time = time.time()
    model = RULPredictor(
        max_depth=6,
        n_estimators=100,
        learning_rate=0.1,
        stratified_sampling=stratified,
        samples_per_lifecycle=20 if stratified else 50
    )
    model.train(train_df)
    train_time = time.time() - start_time

    # Predict
    print("🎯 Making predictions...")
    start_time = time.time()
    results = model.predict(test_df)
    pred_time = time.time() - start_time

    # Evaluate
    y_true = test_df.groupby('unit_id')['RUL'].first().values
    metrics = model.evaluate(y_true, results['predictions'])

    print(f"\n📊 Results:")
    print(f"  MAE: {metrics['MAE']:.2f} cycles")
    print(f"  RMSE: {metrics['RMSE']:.2f} cycles")
    print(f"  R²: {metrics['R2']:.4f}")
    print(f"  Training time: {train_time:.2f}s")
    print(f"  Inference time: {pred_time:.4f}s")

    return {
        'model_type': 'Gradient Boosting',
        'dataset': dataset,
        'stratified': stratified,
        'metrics': metrics,
        'errors': np.abs(y_true - results['predictions']),
        'train_time': train_time,
        'pred_time': pred_time,
        'predictions': results['predictions'],
        'true_rul': y_true
    }


def test_lstm(dataset: str = "FD001") -> dict:
    """Test LSTM RUL predictor"""
    print(f"\n{'='*70}")
    print(f"LSTM - {dataset}")
    print(f"{'='*70}")

    # Load data
    loader = CMapsDataLoader()
    train_df = loader.load_training_data(dataset)
    test_df = loader.load_test_data(dataset)

    # Train
    print("\n🔧 Training LSTM...")
    start_time = time.time()
    model = RULPredictorLSTM(
        sequence_length=50,
        lstm_units=64,
        dropout=0.2,
        learning_rate=0.001,
        epochs=50,
        batch_size=32
    )
    model.train(train_df)
    train_time = time.time() - start_time

    # Predict
    print("🎯 Making predictions...")
    start_time = time.time()
    results = model.predict(test_df)
    pred_time = time.time() - start_time

    # Evaluate
    y_true = test_df.groupby('unit_id')['RUL'].first().values
    metrics = model.evaluate(y_true, results['predictions'])

    print(f"\n📊 Results:")
    print(f"  MAE: {metrics['MAE']:.2f} cycles")
    print(f"  RMSE: {metrics['RMSE']:.2f} cycles")
    print(f"  R²: {metrics['R2']:.4f}")
    print(f"  Training time: {train_time:.2f}s")
    print(f"  Inference time: {pred_time:.4f}s")

    return {
        'model_type': 'LSTM',
        'dataset': dataset,
        'stratified': 'N/A',
        'metrics': metrics,
        'errors': np.abs(y_true - results['predictions']),
        'train_time': train_time,
        'pred_time': pred_time,
        'predictions': results['predictions'],
        'true_rul': y_true
    }


def compare_results(all_results: list):
    """Compare results across all models and datasets"""
    print("\n" + "="*90)
    print("SUMMARY COMPARISON - ALL MODELS")
    print("="*90)

    # Create comparison table
    print(f"\n{'Model':<25} {'Dataset':<12} {'MAE':<12} {'RMSE':<12} {'R²':<12} {'Train(s)':<10}")
    print("-" * 90)

    for result in all_results:
        model_name = result['model_type']
        if result['stratified'] is not None and result['stratified'] != 'N/A':
            model_name += f" (strat={result['stratified']})"

        mae = result['metrics']['MAE']
        rmse = result['metrics']['RMSE']
        r2 = result['metrics']['R2']
        train_time = result['train_time']

        print(f"{model_name:<25} {result['dataset']:<12} {mae:<12.2f} {rmse:<12.2f} {r2:<12.4f} {train_time:<10.2f}")

    # Best model
    print("\n" + "="*90)
    print("BEST PERFORMERS")
    print("="*90)

    best_mae = min(all_results, key=lambda x: x['metrics']['MAE'])
    best_r2 = max(all_results, key=lambda x: x['metrics']['R2'])
    best_speed = min(all_results, key=lambda x: x['train_time'])

    print(f"\n🏆 Lowest MAE: {best_mae['model_type']} on {best_mae['dataset']}")
    print(f"   MAE: {best_mae['metrics']['MAE']:.2f}, R²: {best_mae['metrics']['R2']:.4f}")

    print(f"\n📈 Highest R²: {best_r2['model_type']} on {best_r2['dataset']}")
    print(f"   R²: {best_r2['metrics']['R2']:.4f}, MAE: {best_r2['metrics']['MAE']:.2f}")

    print(f"\n⚡ Fastest: {best_speed['model_type']}")
    print(f"   Training time: {best_speed['train_time']:.2f}s")

    # Error distribution analysis
    print("\n" + "="*90)
    print("ERROR DISTRIBUTION ANALYSIS")
    print("="*90)

    for result in all_results:
        errors = result['errors']
        model_name = f"{result['model_type']} - {result['dataset']}"
        if result['stratified'] is not None and result['stratified'] != 'N/A':
            model_name += f" (strat={result['stratified']})"

        print(f"\n{model_name}:")
        print(f"  Mean error: {errors.mean():.2f} cycles")
        print(f"  Median error: {np.median(errors):.2f} cycles")
        print(f"  Std dev: {errors.std():.2f} cycles")
        print(f"  Within ±25 cycles: {(errors <= 25).sum() / len(errors) * 100:.1f}%")
        print(f"  Within ±50 cycles: {(errors <= 50).sum() / len(errors) * 100:.1f}%")


if __name__ == "__main__":
    print("\n" + "="*90)
    print("RUL PREDICTOR COMPARISON: GRADIENT BOOSTING vs LSTM")
    print("="*90)

    all_results = []

    # Test Gradient Boosting without stratification (baseline)
    try:
        result = test_gradient_boosting("FD001", stratified=False)
        all_results.append(result)
    except Exception as e:
        print(f"❌ Gradient Boosting (no strat) failed: {e}")

    # Test Gradient Boosting with stratification (improved)
    try:
        result = test_gradient_boosting("FD001", stratified=True)
        all_results.append(result)
    except Exception as e:
        print(f"❌ Gradient Boosting (stratified) failed: {e}")

    # Test LSTM
    try:
        result = test_lstm("FD001")
        all_results.append(result)
    except Exception as e:
        print(f"❌ LSTM failed: {e}")

    # Show comparison
    if all_results:
        compare_results(all_results)
        print("\n✅ Comparison complete!")
    else:
        print("\n❌ No successful results to compare")
