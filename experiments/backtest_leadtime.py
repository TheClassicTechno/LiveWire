import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.grid_risk_model import CCIPipeline, backtest_warning_lead_time
import pandas as pd

pipe = CCIPipeline.load("../artifacts")
df = pd.read_csv("../data/processed/scored_results.csv")
res = backtest_warning_lead_time(pipe, df,
                                 fire_start_ts="2018-11-08T06:33:00Z",
                                 component_id="Cable_002")  # Using actual component from our test
print(res)
