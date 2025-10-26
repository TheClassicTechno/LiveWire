"""
RUL Sensor Watcher
==================

Monitors Elasticsearch for new sensor data and automatically triggers RUL scoring.

This can be:
1. Run as a background daemon polling Elasticsearch
2. Triggered by Elasticsearch watchers/alerting
3. Called by Logstash/Filebeat ingest pipelines

The watcher ensures that whenever sensor data is stored, RUL predictions
are automatically computed and stored.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import requests
import time
from threading import Thread

logger = logging.getLogger(__name__)

try:
    from elasticsearch import Elasticsearch
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False


class RULSensorWatcher:
    """Watches Elasticsearch sensor data and triggers RUL predictions"""

    def __init__(self, backend_url: str = "http://localhost:5000", poll_interval: int = 30):
        """
        Initialize the watcher.

        Args:
            backend_url: Flask backend URL
            poll_interval: Poll Elasticsearch every N seconds
        """
        self.backend_url = backend_url.rstrip('/')
        self.poll_interval = poll_interval
        self.sensor_index = "metrics-livewire.sensors-default"
        self.last_check = datetime.utcnow() - timedelta(minutes=5)  # Start from 5 min ago
        self.es = None
        self.running = False

    def connect(self):
        """Connect to Elasticsearch"""
        if not ELASTICSEARCH_AVAILABLE:
            raise Exception("Elasticsearch client not available")

        endpoint = os.getenv('ELASTIC_ENDPOINT')
        api_key = os.getenv('ELASTIC_API_KEY')

        if not endpoint or not api_key:
            raise Exception("Missing ELASTIC_ENDPOINT or ELASTIC_API_KEY")

        try:
            self.es = Elasticsearch(
                hosts=[endpoint],
                api_key=api_key,
                verify_certs=True,
                request_timeout=10
            )
            self.es.info()
            logger.info("✅ Connected to Elasticsearch for sensor watching")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Elasticsearch: {e}")
            return False

    def fetch_latest_sensor_data(self) -> Dict[str, Dict]:
        """
        Fetch latest sensor data for all components from Elasticsearch.

        Returns:
            Dict mapping component_id to latest sensor reading
        """
        try:
            if not self.es:
                return {}

            # Get latest reading per component
            query = {
                "aggs": {
                    "by_component": {
                        "terms": {
                            "field": "component_id.keyword",
                            "size": 1000
                        },
                        "aggs": {
                            "latest": {
                                "top_hits": {
                                    "size": 1,
                                    "sort": [{"@timestamp": {"order": "desc"}}]
                                }
                            }
                        }
                    }
                },
                "size": 0
            }

            result = self.es.search(index=self.sensor_index, body=query)
            buckets = result.get("aggregations", {}).get("by_component", {}).get("buckets", [])

            sensor_data = {}
            for bucket in buckets:
                component_id = bucket.get("key")
                hits = bucket.get("latest", {}).get("hits", {}).get("hits", [])

                if hits:
                    sensor_data[component_id] = hits[0].get("_source", {})

            return sensor_data

        except Exception as e:
            logger.error(f"❌ Failed to fetch sensor data: {e}")
            return {}

    def convert_to_rul_input(self, sensor_reading: Dict) -> Optional[Dict]:
        """
        Convert Elasticsearch sensor reading to RUL prediction input format.

        Args:
            sensor_reading: Raw sensor document from Elasticsearch

        Returns:
            Dict ready for /api/rul/predict or None if invalid
        """
        try:
            # Extract 21 sensors
            sensors = {}
            for i in range(1, 22):
                key = f"sensor_{i}"
                sensors[key] = sensor_reading.get(key, 0)

            # Extract operational settings
            sensors["op_setting_1"] = sensor_reading.get("op_setting_1", 0)
            sensors["op_setting_2"] = sensor_reading.get("op_setting_2", 0)
            sensors["op_setting_3"] = sensor_reading.get("op_setting_3", 0)

            # Time in operation (cycles)
            sensors["time_cycles"] = sensor_reading.get("time_cycles", 0)
            sensors["max_cycles"] = sensor_reading.get("max_cycles", 361)

            return sensors

        except Exception as e:
            logger.error(f"❌ Failed to convert sensor data: {e}")
            return None

    def trigger_rul_prediction(self, component_id: str, sensor_data: Dict) -> bool:
        """
        Call the backend RUL prediction API.

        Args:
            component_id: Component identifier
            sensor_data: Sensor readings dict

        Returns:
            True if prediction was triggered
        """
        try:
            payload = {
                "component_id": component_id,
                "sensors": sensor_data
            }

            response = requests.post(
                f"{self.backend_url}/api/rul/predict",
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                prediction = response.json()
                logger.info(f"✅ RUL prediction triggered: {component_id} → {prediction['rul_hours']}h")

                # Also store to Elasticsearch
                self.store_prediction(prediction)
                return True
            else:
                logger.warning(f"⚠️ RUL prediction failed: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Failed to trigger RUL prediction: {e}")
            return False

    def store_prediction(self, prediction: Dict) -> bool:
        """
        Store RUL prediction to Elasticsearch.

        Args:
            prediction: Prediction result from /api/rul/predict

        Returns:
            True if stored
        """
        try:
            response = requests.post(
                f"{self.backend_url}/api/rul-predictions",
                json=prediction,
                timeout=10
            )

            return response.status_code in [200, 201]

        except Exception as e:
            logger.error(f"❌ Failed to store prediction: {e}")
            return False

    def check_and_predict(self):
        """Check for new sensor data and trigger RUL predictions"""
        try:
            logger.info("🔍 Checking for sensor data...")

            # Fetch latest sensor data
            sensor_data = self.fetch_latest_sensor_data()

            if not sensor_data:
                logger.info("   No sensor data found")
                return

            logger.info(f"   Found {len(sensor_data)} components with sensor data")

            # Trigger RUL predictions
            success_count = 0
            for component_id, reading in sensor_data.items():
                rul_input = self.convert_to_rul_input(reading)

                if rul_input:
                    if self.trigger_rul_prediction(component_id, rul_input):
                        success_count += 1

            logger.info(f"✅ Triggered {success_count}/{len(sensor_data)} RUL predictions")

        except Exception as e:
            logger.error(f"❌ Check and predict failed: {e}")

    def start_watching(self, daemon: bool = False):
        """
        Start the watcher daemon.

        Args:
            daemon: If True, run in background thread
        """
        if self.running:
            logger.warning("Watcher already running")
            return

        if not self.connect():
            logger.error("Failed to connect - not starting watcher")
            return

        self.running = True

        if daemon:
            thread = Thread(target=self._watch_loop, daemon=True)
            thread.start()
            logger.info(f"🚀 RUL watcher started (daemon mode, polling every {self.poll_interval}s)")
        else:
            self._watch_loop()

    def _watch_loop(self):
        """Main watch loop"""
        logger.info("🔄 RUL Sensor Watcher - Main loop started")

        while self.running:
            try:
                self.check_and_predict()
                time.sleep(self.poll_interval)
            except KeyboardInterrupt:
                logger.info("Stopping watcher...")
                self.running = False
            except Exception as e:
                logger.error(f"❌ Watch loop error: {e}")
                time.sleep(self.poll_interval)

    def stop_watching(self):
        """Stop the watcher"""
        self.running = False
        logger.info("✋ RUL watcher stopped")


# Global watcher instance
watcher = RULSensorWatcher()
