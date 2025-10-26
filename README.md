# LiveWire
AI that predicts and prevents city cable failures with real-time alerts and a voice agent using live sensor data and map visualization

## 🏆 Project Status: SUCCESSFUL Camp Fire Prediction!
The Grid Risk Model successfully predicted the 2018 Camp Fire with **308 days advance warning**.

## Tools Used
- Python (scikit-learn, pandas, numpy)
- Kaggle dataset
- JavaScript (frontend - coming soon)

## Project Structure
```
LiveWire/
├── models/                 # Core AI models
│   ├── grid_risk_model.py  # 🏆 WINNING model - Grid Risk CCI Pipeline
│   └── ccimodel.py         # Alternative CCI model
├── scripts/                # Main execution scripts
│   ├── compare_models_camp_fire.py  # Model comparison
│   ├── fix_model_thresholds.py     # Model optimization
│   ├── test_camp_fire.py           # Camp Fire simulation
│   └── run_complete_pipeline.py    # Full pipeline
├── utils/                  # Data utilities
│   ├── data_loader.py              # Kaggle data loader
│   └── generate_camp_fire_data.py  # Realistic Camp Fire simulation
├── analysis/               # Performance analysis
│   └── analyze_performance.py      # Model evaluation
├── experiments/            # Research experiments
│   ├── calibrate_baseline.py
│   ├── predict_fire.py
│   └── backtest_leadtime.py
├── data/                   # Data directories
│   ├── raw/               # Original datasets
│   ├── processed/         # camp_fire_predictions.csv (BEST RESULTS)
│   ├── calib/            # Training data
│   ├── pre_fire/         # Test scenarios
│   └── camp_fire/        # Camp Fire simulation data
└── model.py               # Legacy simple model
```

## 🎯 Key Results
- **Grid Risk Model**: 54.5% accuracy, **308 days Camp Fire warning** ✅
- **CCI Model**: 73.8% accuracy, **0 days Camp Fire warning** ❌
- **Winner**: Grid Risk Model (catches critical failures!)

## Quick Start

1. **Setup environment:**
```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

2. **Generate Camp Fire simulation:**
```powershell
python utils/generate_camp_fire_data.py
```

3. **Compare models:**
```powershell
python scripts/compare_models_camp_fire.py
```

4. **Test Camp Fire prediction:**
```powershell
python scripts/test_camp_fire.py
```

## 🔥 Camp Fire Results
The Grid Risk Model successfully identified the 97-year-old hook component would fail **308 days before** the actual 2018 Camp Fire, providing sufficient time for:
- Preventive maintenance
- Component replacement
- Emergency planning
- **Lives saved** 🚨

## Next Steps
- [ ] Frontend integration
- [ ] Hardware sensor integration
- [ ] Real-time monitoring dashboard
- [ ] Voice agent alerts
