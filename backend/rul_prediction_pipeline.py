"""
RUL Prediction Pipeline
=======================

End-to-end pipeline that:
1. Takes sensor data
2. Calls RUL prediction API
3. Stores predictions in Elasticsearch
4. Returns results to frontend

This is the glue that connects sensor data → RUL model → Elasticsearch storage.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
import requests

logger = logging.getLogger(__name__)


class RULPredictionPipeline:
    """Complete pipeline from sensor data to Elasticsearch storage"""

    def __init__(self, backend_url: str = "http://localhost:5000"):
        """
        Initialize the pipeline.

        Args:
            backend_url: Base URL of the Flask backend (e.g., http://localhost:5000)
        """
        self.backend_url = backend_url.rstrip('/')
        self.predict_endpoint = f"{self.backend_url}/api/rul/predict"
        self.batch_predict_endpoint = f"{self.backend_url}/api/rul/batch-predict"
        self.store_endpoint = f"{self.backend_url}/api/rul-predictions"
        self.batch_store_endpoint = f"{self.backend_url}/api/rul-predictions/batch"

    def predict_and_store(self, component_id: str, sensor_data: Dict) -> Optional[Dict]:
        """
        Predict RUL for a component and store in Elasticsearch.

        Args:
            component_id: Component identifier
            sensor_data: Dict with sensor readings (21 sensors, op_settings, time_cycles)

        Returns:
            Prediction result or None if failed
        """
        try:
            # Step 1: Call RUL prediction API
            predict_payload = {
                "component_id": component_id,
                "sensors": sensor_data
            }

            logger.info(f"🔮 Predicting RUL for {component_id}...")
            predict_response = requests.post(
                self.predict_endpoint,
                json=predict_payload,
                timeout=10
            )

            if predict_response.status_code != 200:
                logger.error(f"❌ Prediction failed: {predict_response.text}")
                return None

            prediction = predict_response.json()
            logger.info(f"✅ RUL prediction: {component_id} → {prediction['rul_hours']}h ({prediction['risk_zone']})")

            # Step 2: Store in Elasticsearch
            store_payload = {
                **prediction,
                "sensors": sensor_data
            }

            logger.info(f"💾 Storing prediction in Elasticsearch...")
            store_response = requests.post(
                self.store_endpoint,
                json=store_payload,
                timeout=10
            )

            if store_response.status_code not in [200, 201]:
                logger.warning(f"⚠️ Storage failed: {store_response.text}")
                # Still return prediction even if storage failed
                return prediction

            logger.info(f"✅ Prediction stored in Elasticsearch")
            return prediction

        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            return None

    def batch_predict_and_store(self, components: List[Dict]) -> Optional[Dict]:
        """
        Predict RUL for multiple components and store all in Elasticsearch.

        Args:
            components: List of dicts with:
                - component_id
                - sensors (dict with 21 sensor values, op_settings, time_cycles)

        Returns:
            Batch prediction result or None if failed
        """
        try:
            # Step 1: Call batch RUL prediction API
            predict_payload = {"predictions": components}

            logger.info(f"🔮 Batch predicting RUL for {len(components)} components...")
            predict_response = requests.post(
                self.batch_predict_endpoint,
                json=predict_payload,
                timeout=30
            )

            if predict_response.status_code != 200:
                logger.error(f"❌ Batch prediction failed: {predict_response.text}")
                return None

            batch_result = predict_response.json()
            predictions = batch_result.get("predictions", [])
            logger.info(f"✅ Batch prediction complete: {len(predictions)} components")

            # Step 2: Store all in Elasticsearch in one batch
            store_payload = {"predictions": predictions}

            logger.info(f"💾 Storing {len(predictions)} predictions in Elasticsearch...")
            store_response = requests.post(
                self.batch_store_endpoint,
                json=store_payload,
                timeout=30
            )

            if store_response.status_code not in [200, 201]:
                logger.warning(f"⚠️ Batch storage failed: {store_response.text}")
                # Still return predictions even if storage failed
                return batch_result

            logger.info(f"✅ All predictions stored in Elasticsearch")
            return batch_result

        except Exception as e:
            logger.error(f"❌ Batch pipeline failed: {e}")
            return None

    def predict_from_elasticsearch_sensor_data(self, component_id: str) -> Optional[Dict]:
        """
        Fetch sensor data from Elasticsearch and predict RUL.

        This would be called by an Elasticsearch watcher or Logstash pipeline.

        Args:
            component_id: Component identifier

        Returns:
            Prediction result or None if failed
        """
        try:
            # TODO: Fetch latest sensor readings from Elasticsearch for component_id
            # Then call predict_and_store()
            # This requires Elasticsearch data access which is handled by elasticsearch_proxy
            logger.info(f"📊 Would fetch sensor data for {component_id} from Elasticsearch")
            logger.info(f"   Then call predict_and_store()")
            return None

        except Exception as e:
            logger.error(f"❌ Failed to predict from ES data: {e}")
            return None


# Global pipeline instance
pipeline = RULPredictionPipeline()
