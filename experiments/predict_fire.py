import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from models.grid_risk_model import CCIPipeline
import pandas as pd

# Create data directories if they don't exist
os.makedirs("../data/pre_fire", exist_ok=True)
os.makedirs("../data/processed", exist_ok=True)

pipe = CCIPipeline.load("../artifacts")
pre_fire_df = pd.read_csv("../data/pre_fire/2018_runup.csv")
scored = pipe.score(pre_fire_df)
scored.to_csv("../data/processed/scored_2018.csv", index=False)
