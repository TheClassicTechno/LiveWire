import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.grid_risk_model import CCIPipeline, backtest_warning_lead_time
import pandas as pd

# Use absolute paths to avoid confusion
base_dir = os.path.dirname(os.path.dirname(__file__))  # Go up two levels from experiments/
artifacts_path = os.path.join(base_dir, "artifacts")
data_path = os.path.join(base_dir, "data", "processed", "scored_results.csv")

pipe = CCIPipeline.load(artifacts_path)
df = pd.read_csv(data_path)
res = backtest_warning_lead_time(pipe, df,
                                 fire_start_ts="2018-11-08T06:33:00Z",
                                 component_id="Cable_002")  # Using actual component from our test
print(res)
