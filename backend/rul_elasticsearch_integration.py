"""
RUL ↔ Elasticsearch Integration
================================

Handles storing and querying RUL predictions in Elasticsearch.
Enables automatic RUL scoring when sensor data arrives.

Features:
- Store RUL predictions with full metadata
- Query historical RUL trends per component
- Auto-trigger RUL scoring from sensor events
- Aggregate RUL statistics across components
"""

import os
import json
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
import logging
from typing import Dict, List, Optional

try:
    from elasticsearch import Elasticsearch
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False

bp = Blueprint('rul_elasticsearch', __name__)
logger = logging.getLogger(__name__)

# Global ES client
es_client = None


def get_es_client():
    """Get or initialize Elasticsearch client"""
    global es_client

    if es_client is not None:
        return es_client

    if not ELASTICSEARCH_AVAILABLE:
        raise Exception("Elasticsearch client not available")

    endpoint = os.getenv('ELASTIC_ENDPOINT')
    api_key = os.getenv('ELASTIC_API_KEY')

    if not endpoint or not api_key:
        raise Exception("Missing ELASTIC_ENDPOINT or ELASTIC_API_KEY")

    try:
        es_client = Elasticsearch(
            hosts=[endpoint],
            api_key=api_key,
            verify_certs=True,
            request_timeout=10
        )
        es_client.info()
        logger.info("✅ Connected to Elasticsearch for RUL integration")
        return es_client
    except Exception as e:
        logger.error(f"❌ Failed to connect to Elasticsearch: {e}")
        raise


class RULElasticsearchManager:
    """Manages RUL predictions in Elasticsearch"""

    def __init__(self):
        self.index = "metrics-livewire.rul-predictions-default"
        self.es = None

    def connect(self):
        """Initialize Elasticsearch connection"""
        self.es = get_es_client()

    def store_rul_prediction(self, prediction: Dict) -> bool:
        """
        Store a single RUL prediction in Elasticsearch.

        Args:
            prediction: Dict with keys:
                - component_id
                - rul_cycles, rul_hours, rul_days
                - confidence
                - risk_zone, risk_score
                - timestamp
                - (optional) sensors, location, etc.

        Returns:
            True if stored successfully
        """
        try:
            if not self.es:
                self.connect()

            # Prepare document
            doc = {
                "@timestamp": prediction.get("timestamp", datetime.utcnow().isoformat() + "Z"),
                "component_id": prediction.get("component_id"),
                "rul_cycles": prediction.get("rul_cycles"),
                "rul_hours": prediction.get("rul_hours"),
                "rul_days": prediction.get("rul_days"),
                "confidence": prediction.get("confidence"),
                "risk_zone": prediction.get("risk_zone"),
                "risk_score": prediction.get("risk_score"),
            }

            # Add optional fields if present
            if "sensors" in prediction:
                doc["sensors"] = prediction["sensors"]
            if "component_location" in prediction:
                doc["component_location"] = prediction["component_location"]
            if "last_sensor_reading" in prediction:
                doc["last_sensor_reading"] = prediction["last_sensor_reading"]

            # Index the document
            result = self.es.index(index=self.index, document=doc)
            logger.info(f"✅ Stored RUL prediction for {prediction['component_id']}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to store RUL prediction: {e}")
            return False

    def store_batch_rul_predictions(self, predictions: List[Dict]) -> int:
        """
        Store multiple RUL predictions using bulk indexing.

        Args:
            predictions: List of prediction dicts

        Returns:
            Number of predictions stored
        """
        try:
            if not self.es:
                self.connect()

            # Prepare bulk request
            bulk_data = []
            for pred in predictions:
                # Index action
                bulk_data.append({"index": {"_index": self.index}})

                # Document
                doc = {
                    "@timestamp": pred.get("timestamp", datetime.utcnow().isoformat() + "Z"),
                    "component_id": pred.get("component_id"),
                    "rul_cycles": pred.get("rul_cycles"),
                    "rul_hours": pred.get("rul_hours"),
                    "rul_days": pred.get("rul_days"),
                    "confidence": pred.get("confidence"),
                    "risk_zone": pred.get("risk_zone"),
                    "risk_score": pred.get("risk_score"),
                }

                if "sensors" in pred:
                    doc["sensors"] = pred["sensors"]
                if "component_location" in pred:
                    doc["component_location"] = pred["component_location"]

                bulk_data.append(doc)

            # Execute bulk request
            result = self.es.bulk(body=bulk_data, refresh=True)

            count = len(predictions)
            logger.info(f"✅ Stored {count} RUL predictions in batch")
            return count

        except Exception as e:
            logger.error(f"❌ Batch RUL storage failed: {e}")
            return 0

    def get_latest_rul(self, component_id: str) -> Optional[Dict]:
        """
        Get latest RUL prediction for a component.

        Args:
            component_id: Component identifier

        Returns:
            Latest RUL prediction or None
        """
        try:
            if not self.es:
                self.connect()

            query = {
                "query": {
                    "match": {"component_id": component_id}
                },
                "sort": [{"@timestamp": {"order": "desc"}}],
                "size": 1
            }

            result = self.es.search(index=self.index, body=query)
            hits = result.get("hits", {}).get("hits", [])

            if hits:
                return hits[0].get("_source")
            return None

        except Exception as e:
            logger.error(f"❌ Failed to get latest RUL: {e}")
            return None

    def get_rul_history(self, component_id: str, days: int = 7) -> List[Dict]:
        """
        Get RUL history for a component over the past N days.

        Args:
            component_id: Component identifier
            days: Number of days to look back

        Returns:
            List of RUL predictions sorted by timestamp
        """
        try:
            if not self.es:
                self.connect()

            start_time = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"

            query = {
                "query": {
                    "bool": {
                        "must": [
                            {"match": {"component_id": component_id}},
                            {"range": {"@timestamp": {"gte": start_time}}}
                        ]
                    }
                },
                "sort": [{"@timestamp": {"order": "asc"}}],
                "size": 1000
            }

            result = self.es.search(index=self.index, body=query)
            hits = result.get("hits", {}).get("hits", [])

            return [hit.get("_source") for hit in hits]

        except Exception as e:
            logger.error(f"❌ Failed to get RUL history: {e}")
            return []

    def get_all_latest_rul(self) -> Dict[str, Dict]:
        """
        Get latest RUL for all components.

        Returns:
            Dict mapping component_id to latest RUL prediction
        """
        try:
            if not self.es:
                self.connect()

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

            result = self.es.search(index=self.index, body=query)
            buckets = result.get("aggregations", {}).get("by_component", {}).get("buckets", [])

            latest_rul = {}
            for bucket in buckets:
                component_id = bucket.get("key")
                hits = bucket.get("latest", {}).get("hits", {}).get("hits", [])

                if hits:
                    latest_rul[component_id] = hits[0].get("_source")

            return latest_rul

        except Exception as e:
            logger.error(f"❌ Failed to get all latest RUL: {e}")
            return {}

    def get_rul_stats(self) -> Dict:
        """
        Get aggregated RUL statistics.

        Returns:
            Dict with:
            - avg_rul_hours
            - min_rul_hours (most critical)
            - max_rul_hours (most safe)
            - critical_count (rul < 24h)
            - warning_count (24h <= rul < 72h)
            - safe_count (rul >= 72h)
            - total_components
        """
        try:
            if not self.es:
                self.connect()

            # Get latest RUL for all components
            all_latest = self.get_all_latest_rul()

            if not all_latest:
                return {
                    "avg_rul_hours": 0,
                    "min_rul_hours": 0,
                    "max_rul_hours": 0,
                    "critical_count": 0,
                    "warning_count": 0,
                    "safe_count": 0,
                    "total_components": 0
                }

            rul_values = [pred.get("rul_hours", 0) for pred in all_latest.values()]

            critical = sum(1 for v in rul_values if v < 24)
            warning = sum(1 for v in rul_values if 24 <= v < 72)
            safe = sum(1 for v in rul_values if v >= 72)

            return {
                "avg_rul_hours": round(sum(rul_values) / len(rul_values), 2) if rul_values else 0,
                "min_rul_hours": round(min(rul_values), 2) if rul_values else 0,
                "max_rul_hours": round(max(rul_values), 2) if rul_values else 0,
                "critical_count": critical,
                "warning_count": warning,
                "safe_count": safe,
                "total_components": len(all_latest)
            }

        except Exception as e:
            logger.error(f"❌ Failed to get RUL stats: {e}")
            return {}


# Initialize manager
rul_manager = RULElasticsearchManager()


# ============================================================================
# Flask Endpoints
# ============================================================================

@bp.route('/api/rul-predictions', methods=['GET'])
def get_rul_predictions():
    """
    Get latest RUL predictions for all components.

    Query params:
      - limit: Max number of components (default: all)

    Returns:
    {
        "predictions": {
            "CABLE_A1_MAIN": { rul_cycles, rul_hours, rul_days, risk_zone, ... },
            "CABLE_A2_BACKUP": { ... }
        },
        "stats": {
            "avg_rul_hours": 150.5,
            "critical_count": 2,
            "warning_count": 5,
            "safe_count": 18
        }
    }
    """
    try:
        if not rul_manager.es:
            rul_manager.connect()

        predictions = rul_manager.get_all_latest_rul()
        stats = rul_manager.get_rul_stats()

        return jsonify({
            "predictions": predictions,
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 200

    except Exception as e:
        logger.error(f"❌ Failed to get RUL predictions: {e}")
        return jsonify({"error": str(e), "predictions": {}, "stats": {}}), 500


@bp.route('/api/rul-predictions/<component_id>', methods=['GET'])
def get_component_rul(component_id):
    """
    Get RUL prediction for a specific component.

    Query params:
      - days: Historical days to include (default: 0 for latest only)

    Returns:
    {
        "component_id": "CABLE_A1_MAIN",
        "latest": { rul_cycles, rul_hours, rul_days, ... },
        "history": [ { ... }, { ... } ]  (if days > 0)
    }
    """
    try:
        if not rul_manager.es:
            rul_manager.connect()

        days = int(request.args.get('days', 0))
        latest = rul_manager.get_latest_rul(component_id)

        response = {
            "component_id": component_id,
            "latest": latest,
        }

        if days > 0:
            response["history"] = rul_manager.get_rul_history(component_id, days)

        if latest:
            return jsonify(response), 200
        else:
            return jsonify({**response, "error": "No predictions found"}), 404

    except Exception as e:
        logger.error(f"❌ Failed to get component RUL: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route('/api/rul-predictions', methods=['POST'])
def store_rul_prediction():
    """
    Store a RUL prediction (called after model prediction).

    Request JSON:
    {
        "component_id": "CABLE_A1_MAIN",
        "rul_cycles": 199.71,
        "rul_hours": 199.71,
        "rul_days": 8.32,
        "confidence": 0.087,
        "risk_zone": "green",
        "risk_score": 0.26,
        "sensors": { ... },
        "component_location": { "lat": 34.0522, "lon": -118.2437 }
    }

    Returns:
    {
        "status": "stored",
        "component_id": "CABLE_A1_MAIN",
        "timestamp": "2025-10-26T11:00:00Z"
    }
    """
    try:
        if not rul_manager.es:
            rul_manager.connect()

        data = request.get_json()

        if 'component_id' not in data:
            return jsonify({"error": "Missing 'component_id'"}), 400

        success = rul_manager.store_rul_prediction(data)

        if success:
            return jsonify({
                "status": "stored",
                "component_id": data.get("component_id"),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 201
        else:
            return jsonify({"error": "Failed to store prediction"}), 500

    except Exception as e:
        logger.error(f"❌ Failed to store RUL prediction: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route('/api/rul-predictions/batch', methods=['POST'])
def store_batch_rul_predictions():
    """
    Store multiple RUL predictions in one request.

    Request JSON:
    {
        "predictions": [
            { component_id, rul_hours, ... },
            { component_id, rul_hours, ... }
        ]
    }

    Returns:
    {
        "status": "stored",
        "count": 3,
        "timestamp": "2025-10-26T11:00:00Z"
    }
    """
    try:
        if not rul_manager.es:
            rul_manager.connect()

        data = request.get_json()

        if 'predictions' not in data:
            return jsonify({"error": "Missing 'predictions' array"}), 400

        count = rul_manager.store_batch_rul_predictions(data['predictions'])

        return jsonify({
            "status": "stored",
            "count": count,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 201

    except Exception as e:
        logger.error(f"❌ Batch storage failed: {e}")
        return jsonify({"error": str(e)}), 500


@bp.route('/api/rul-stats', methods=['GET'])
def get_rul_stats():
    """
    Get aggregated RUL statistics across all components.

    Returns:
    {
        "avg_rul_hours": 150.5,
        "min_rul_hours": 9.78,
        "max_rul_hours": 250.0,
        "critical_count": 2,
        "warning_count": 5,
        "safe_count": 18,
        "total_components": 25
    }
    """
    try:
        if not rul_manager.es:
            rul_manager.connect()

        stats = rul_manager.get_rul_stats()
        return jsonify({**stats, "timestamp": datetime.utcnow().isoformat() + "Z"}), 200

    except Exception as e:
        logger.error(f"❌ Failed to get RUL stats: {e}")
        return jsonify({"error": str(e)}), 500
