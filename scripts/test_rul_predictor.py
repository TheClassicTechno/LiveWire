"""
Comprehensive Test Suite for RUL Predictor
===========================================

Trains on each CMaps dataset and evaluates on corresponding test set.
Provides insights into model performance across different operating conditions.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
import numpy as np
from utils.rul_data_loader import CMapsDataLoader, explore_dataset
from models.rul_predictor import RULPredictor


def test_dataset(dataset: str = "FD001", verbose: bool = True):
    """
    Test RUL predictor on a single CMaps dataset.

    Args:
        dataset: One of "FD001", "FD002", "FD003", "FD004"
        verbose: Print detailed output

    Returns:
        Dictionary with results
    """
    print(f"\n{'='*70}")
    print(f"Testing on {dataset}")
    print(f"{'='*70}")

    # Load data
    loader = CMapsDataLoader()
    train_df = loader.load_training_data(dataset)
    test_df = loader.load_test_data(dataset)

    if verbose:
        explore_dataset(train_df, f"{dataset} Training Data")
        explore_dataset(test_df, f"{dataset} Test Data")

    # Train model
    print(f"\n{'='*70}")
    print("TRAINING")
    print(f"{'='*70}")
    model = RULPredictor(max_depth=6, n_estimators=100, learning_rate=0.1)
    model.train(train_df)

    # Make predictions on test data
    print(f"\n{'='*70}")
    print("INFERENCE")
    print(f"{'='*70}")
    results = model.predict(test_df)

    # Get true RUL values
    true_rul = test_df.groupby('unit_id')['RUL'].first().values
    pred_rul = results['predictions']

    print(f"\nPredicted {len(results['unit_ids'])} engines")
    print(f"Prediction range: {pred_rul.min():.0f} to {pred_rul.max():.0f} cycles")
    print(f"True RUL range: {true_rul.min():.0f} to {true_rul.max():.0f} cycles")

    # Evaluate
    print(f"\n{'='*70}")
    print("EVALUATION METRICS")
    print(f"{'='*70}")
    metrics = model.evaluate(true_rul, pred_rul)

    for metric, value in metrics.items():
        if metric in ['MAE', 'RMSE', 'Scoring_Error']:
            print(f"  {metric:25s}: {value:10.2f} cycles")
        else:
            print(f"  {metric:25s}: {value:10.4f}")

    # Feature importance
    print(f"\n{'='*70}")
    print("TOP 10 IMPORTANT FEATURES")
    print(f"{'='*70}")
    importances = model.get_feature_importance(top_n=10)
    for i, (feat, imp) in enumerate(importances.items(), 1):
        print(f"  {i:2d}. {feat:35s}: {imp:8.4f}")

    # Prediction error analysis
    errors = np.abs(true_rul - pred_rul)
    print(f"\n{'='*70}")
    print("PREDICTION ERROR ANALYSIS")
    print(f"{'='*70}")
    print(f"  Mean Absolute Error: {errors.mean():.2f} cycles")
    print(f"  Median Absolute Error: {np.median(errors):.2f} cycles")
    print(f"  Std Dev of Errors: {errors.std():.2f} cycles")
    print(f"  Max Error: {errors.max():.2f} cycles")
    print(f"  % within ±25 cycles: {(errors <= 25).sum() / len(errors) * 100:.1f}%")
    print(f"  % within ±50 cycles: {(errors <= 50).sum() / len(errors) * 100:.1f}%")

    return {
        'dataset': dataset,
        'model': model,
        'metrics': metrics,
        'errors': errors,
        'true_rul': true_rul,
        'pred_rul': pred_rul,
        'unit_ids': results['unit_ids']
    }


def compare_all_datasets():
    """Train and test on all 4 CMaps datasets, compare results"""
    print("\n" + "="*70)
    print("RUL PREDICTOR - MULTI-DATASET EVALUATION")
    print("="*70)

    results_all = {}
    for dataset in ["FD001", "FD002", "FD003", "FD004"]:
        try:
            results = test_dataset(dataset, verbose=False)
            results_all[dataset] = results
        except Exception as e:
            print(f"\n❌ Error testing {dataset}: {e}")
            continue

    # Summary comparison
    print("\n" + "="*70)
    print("SUMMARY ACROSS ALL DATASETS")
    print("="*70)
    print(f"\n{'Dataset':<10} {'MAE':<12} {'RMSE':<12} {'R2':<12} {'% within 50cy':<15}")
    print("-" * 60)

    for dataset, results in results_all.items():
        mae = results['metrics']['MAE']
        rmse = results['metrics']['RMSE']
        r2 = results['metrics']['R2']
        pct_within_50 = (results['errors'] <= 50).sum() / len(results['errors']) * 100

        print(f"{dataset:<10} {mae:<12.2f} {rmse:<12.2f} {r2:<12.4f} {pct_within_50:<14.1f}%")

    return results_all


def cross_dataset_evaluation():
    """Train on one dataset, test on another (transfer learning potential)"""
    print("\n" + "="*70)
    print("CROSS-DATASET EVALUATION (Transfer Learning Test)")
    print("="*70)

    loader = CMapsDataLoader()
    datasets = ["FD001", "FD002", "FD003", "FD004"]

    for train_dataset in datasets:
        print(f"\n{'='*70}")
        print(f"Training on {train_dataset}, testing on other datasets")
        print(f"{'='*70}")

        # Train on this dataset
        train_df = loader.load_training_data(train_dataset)
        model = RULPredictor()
        model.train(train_df)

        # Test on all others
        for test_dataset in datasets:
            if test_dataset == train_dataset:
                continue

            test_df = loader.load_test_data(test_dataset)
            results = model.predict(test_df)
            true_rul = test_df.groupby('unit_id')['RUL'].first().values
            metrics = model.evaluate(true_rul, results['predictions'])

            mae = metrics['MAE']
            r2 = metrics['R2']
            print(f"  Test on {test_dataset}: MAE={mae:6.2f} cycles, R²={r2:7.4f}")


if __name__ == "__main__":
    # Run comprehensive tests
    compare_all_datasets()

    # Optional: Test cross-dataset transfer
    print("\n" + "="*70)
    print("Run cross-dataset evaluation? (Uncomment to enable)")
    print("="*70)
    # cross_dataset_evaluation()

    print("\n✅ Testing complete!")
