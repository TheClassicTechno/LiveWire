"""
Elasticsearch Proxy Endpoints
=============================

Backend proxy to safely query Elasticsearch and bypass CORS/CSP restrictions.
Provides aggregated real-time sensor data for the React frontend.

Usage:
  - GET /api/sensor-data → Returns aggregated metrics (power, temp, vibration, strain)
  - GET /api/alerts → Returns recent alerts from last 24h
  - GET /api/component-health → Returns per-component health status
  - GET /api/health → Health check connection
"""

import os
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import logging

# Try to import elasticsearch, gracefully handle if not installed
try:
    from elasticsearch import Elasticsearch
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False
    print("⚠️ elasticsearch package not installed. Install with: pip install elasticsearch")

bp = Blueprint('elasticsearch', __name__)
logger = logging.getLogger(__name__)

# Initialize Elasticsearch client (will be setup on first request if not available)
es_client = None


def get_es_client():
    """Initialize Elasticsearch client"""
    global es_client

    if es_client is not None:
        return es_client

    if not ELASTICSEARCH_AVAILABLE:
        raise Exception("Elasticsearch client not available. Install with: pip install elasticsearch")

    endpoint = os.getenv('ELASTIC_ENDPOINT')
    api_key = os.getenv('ELASTIC_API_KEY')

    if not endpoint or not api_key:
        raise Exception("Missing ELASTIC_ENDPOINT or ELASTIC_API_KEY in environment")

    try:
        es_client = Elasticsearch(
            hosts=[endpoint],
            api_key=api_key,
            verify_certs=True,
            request_timeout=10
        )
        # Test connection
        es_client.info()
        logger.info("✅ Connected to Elasticsearch")
        return es_client
    except Exception as e:
        logger.error(f"❌ Failed to connect to Elasticsearch: {e}")
        raise


@bp.route('/api/sensor-data', methods=['GET'])
def get_sensor_data():
    """
    Get aggregated sensor data for the last hour.

    Returns:
    {
        "avgPower": 691.237,
        "avgTemp": 32.532,
        "avgVibration": 0.828,
        "avgStrain": 168.637,
        "maxPower": 1300,
        "maxTemp": 65,
        "sampleCount": 3500,
        "lastUpdated": "2025-10-26T10:30:00Z",
        "status": "success"
    }
    """
    try:
        es = get_es_client()

        # Query aggregated metrics from last hour
        query = {
            "aggs": {
                "metrics": {
                    "date_histogram": {
                        "field": "@timestamp",
                        "fixed_interval": "1h"
                    },
                    "aggs": {
                        "avg_power": {"avg": {"field": "power"}},
                        "avg_temp": {"avg": {"field": "temperature"}},
                        "avg_vibration": {"avg": {"field": "vibration"}},
                        "avg_strain": {"avg": {"field": "strain"}},
                        "max_power": {"max": {"field": "power"}},
                        "max_temp": {"max": {"field": "temperature"}},
                    }
                }
            },
            "size": 0
        }

        result = es.search(index="metrics-livewire.sensors-default", body=query)

        # Extract aggregated values
        buckets = result.get("aggregations", {}).get("metrics", {}).get("buckets", [])

        if buckets:
            latest = buckets[-1]  # Get most recent bucket
            aggs = latest.get("avg_power", {})

            response = {
                "avgPower": aggs.get("value", 0) if isinstance(aggs, dict) else 0,
                "avgTemp": latest.get("avg_temp", {}).get("value", 0),
                "avgVibration": latest.get("avg_vibration", {}).get("value", 0),
                "avgStrain": latest.get("avg_strain", {}).get("value", 0),
                "maxPower": latest.get("max_power", {}).get("value", 0),
                "maxTemp": latest.get("max_temp", {}).get("value", 0),
                "sampleCount": latest.get("doc_count", 0),
                "riskZones": {},
                "lastUpdated": datetime.utcnow().isoformat() + "Z",
                "status": "success"
            }
        else:
            response = {
                "avgPower": 0,
                "avgTemp": 0,
                "avgVibration": 0,
                "avgStrain": 0,
                "maxPower": 0,
                "maxTemp": 0,
                "sampleCount": 0,
                "riskZones": {},
                "lastUpdated": datetime.utcnow().isoformat() + "Z",
                "status": "success"
            }

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"❌ Sensor data query failed: {e}")
        return jsonify({
            "error": str(e),
            "status": "error",
            "avgPower": 0,
            "avgTemp": 0,
            "avgVibration": 0,
            "avgStrain": 0,
            "maxPower": 0,
            "maxTemp": 0,
            "sampleCount": 0,
            "riskZones": {}
        }), 500


@bp.route('/api/alerts', methods=['GET'])
def get_recent_alerts():
    """
    Get recent alerts from the last 24 hours.

    Query params:
      - alert_level: Filter by 'critical', 'warning', or 'info'
      - limit: Maximum number of alerts to return (default 50)

    Returns:
    {
        "alerts": [
            {
                "timestamp": "2025-10-26T09:55:33.116Z",
                "component_id": "CABLE_B2_BACKUP",
                "risk_zone": "yellow",
                "alert_level": "warning",
                "confidence": 0.7,
                "message": "Component showing yellow risk...",
            },
            ...
        ]
    }
    """
    try:
        es = get_es_client()

        alert_level = request.args.get('alert_level')
        limit = int(request.args.get('limit', 50))

        # Build query for alerts in last 24 hours
        query = {
            "query": {
                "range": {
                    "@timestamp": {
                        "gte": "now-24h"
                    }
                }
            },
            "sort": [{"@timestamp": {"order": "desc"}}],
            "size": limit
        }

        result = es.search(index="logs-livewire.alerts-default", body=query)

        alerts = []
        for hit in result.get("hits", {}).get("hits", []):
            source = hit.get("_source", {})

            # Filter by alert level if specified
            if alert_level and source.get("alert_level") != alert_level:
                continue

            alerts.append({
                "timestamp": source.get("@timestamp", datetime.utcnow().isoformat() + "Z"),
                "component_id": source.get("component_id", "unknown"),
                "risk_zone": source.get("risk_zone", "unknown"),
                "alert_level": source.get("alert_level", "info"),
                "confidence": source.get("confidence", 0),
                "message": source.get("message", "No message"),
            })

        return jsonify({"alerts": alerts}), 200

    except Exception as e:
        logger.error(f"❌ Alert query failed: {e}")
        return jsonify({"alerts": [], "error": str(e)}), 500


@bp.route('/api/component-health', methods=['GET'])
def get_component_health():
    """
    Get current health status for all components.

    Returns:
    {
        "components": {
            "CABLE_A1_MAIN": {
                "status": "yellow",
                "confidence": 0.85,
                "last_reading": "2025-10-26T11:00:00Z",
                "temperature": 45.3,
                "vibration": 0.82,
                "strain": 185.2
            },
            ...
        }
    }
    """
    try:
        es = get_es_client()

        # Get latest reading per component
        query = {
            "aggs": {
                "by_component": {
                    "terms": {
                        "field": "component_id.keyword",
                        "size": 100
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

        result = es.search(index="metrics-livewire.sensors-default", body=query)

        components = {}
        for bucket in result.get("aggregations", {}).get("by_component", {}).get("buckets", []):
            component_id = bucket.get("key")
            hits = bucket.get("latest", {}).get("hits", {}).get("hits", [])

            if hits:
                source = hits[0].get("_source", {})
                components[component_id] = {
                    "status": source.get("risk_zone", "unknown"),
                    "confidence": source.get("confidence", 0),
                    "last_reading": source.get("@timestamp", datetime.utcnow().isoformat() + "Z"),
                    "temperature": source.get("temperature", 0),
                    "vibration": source.get("vibration", 0),
                    "strain": source.get("strain", 0),
                }

        return jsonify({"components": components}), 200

    except Exception as e:
        logger.error(f"❌ Component health query failed: {e}")
        return jsonify({"components": {}, "error": str(e)}), 500


@bp.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check - verify backend can connect to Elasticsearch.

    Returns:
    {
        "status": "healthy",
        "elasticsearch": {
            "connected": true,
            "version": "8.11.0"
        }
    }
    """
    try:
        es = get_es_client()
        info = es.info()
        version = info.get("version", {}).get("number", "unknown")

        return jsonify({
            "status": "healthy",
            "elasticsearch": {
                "connected": True,
                "version": version
            }
        }), 200
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "elasticsearch": {
                "connected": False
            },
            "error": str(e)
        }), 500
