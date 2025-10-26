import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.grid_risk_model import CCIPipeline, CCIPipelineConfig
import pandas as pd

# Create data directories if they don't exist
os.makedirs("../data/calib", exist_ok=True)
os.makedirs("../artifacts", exist_ok=True)

calib_df = pd.read_csv("../data/calib/pre2018.csv")
pipe = CCIPipeline(CCIPipelineConfig())
pipe.fit(calib_df)
pipe.save("../artifacts")
