"""
Paradise Demo API - Simple Flask server for Camp Fire time-slider demo

This serves scored CCI predictions for Tower 27/222 to the React frontend.

Usage:
    python src/api/paradise_api.py

Then from frontend, fetch:
    GET /api/snapshot/2018-05-21  → returns component data for that date
    GET /api/components           → returns list of all components

How to prepare data:
1. Generate 2016-2018 Camp Fire data:
   python utils/generate_camp_fire_data.py

2. Score it with the model:
   python scripts/test_camp_fire.py

   This creates scored predictions CSV

3. Run this API:
   python src/api/paradise_api.py

   The API will load the scored data and serve it on port 5000

4. Frontend can now fetch real data instead of using simulated values

See DEMO_DATA_SETUP.md for full instructions.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Configuration
DATA_PATH = 'data/processed/paradise_10year_daily.csv'
TOWER_27_222 = {
    'component_id': 'TOWER_27_222',
    'name': 'Tower 27/222 - C-Hook',
    'lat': 39.8039,
    'lon': -121.4487,
    'location': 'Pulga, Feather River Canyon',
    'built_year': 1919,
}

# Global data cache
scored_data = None


def load_data():
    """Load and cache scored data"""
    global scored_data
    if scored_data is None:
        if not os.path.exists(DATA_PATH):
            print(f"Warning: {DATA_PATH} not found")
            print("Using simulated data until scored data is available")
            return None

        scored_data = pd.read_csv(DATA_PATH)
        scored_data['timestamp'] = pd.to_datetime(scored_data['timestamp'])
        print(f"✓ Loaded scored data: {len(scored_data)} records")
    return scored_data


@app.route('/api/snapshot/<date_str>', methods=['GET'])
def get_snapshot(date_str):
    """
    Get component data for a specific date.

    Args:
        date_str: ISO format date (YYYY-MM-DD)

    Returns:
        List of component data for that date
    """
    try:
        target_date = pd.to_datetime(date_str)
    except:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    # Try to load real data
    data = load_data()
    if data is not None:
        filtered = data[data['timestamp'].dt.date == target_date.date()]
        if len(filtered) > 0:
            return jsonify(filtered.to_dict('records'))

    # Fallback: return simulated data
    print(f"No real data for {date_str}, returning simulated snapshot")
    return jsonify(generate_simulated_snapshot(target_date))


@app.route('/api/components', methods=['GET'])
def get_components():
    """Get list of all components with locations"""
    return jsonify([TOWER_27_222])


@app.route('/api/time-series/<component_id>', methods=['GET'])
def get_time_series(component_id):
    """
    Get full time-series for a component.

    Optional query params:
        - start_date: Start date (YYYY-MM-DD)
        - end_date: End date (YYYY-MM-DD)
    """
    data = load_data()
    if data is None:
        return jsonify({'error': 'Data not loaded'}), 500

    # Filter by component
    component_data = data[data['component_id'] == component_id]
    if len(component_data) == 0:
        return jsonify({'error': f'Component {component_id} not found'}), 404

    # Optional date filtering
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if start_date:
        component_data = component_data[component_data['timestamp'] >= pd.to_datetime(start_date)]
    if end_date:
        component_data = component_data[component_data['timestamp'] <= pd.to_datetime(end_date)]

    return jsonify({
        'component_id': component_id,
        'data': component_data.to_dict('records')
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall stats"""
    data = load_data()

    stats = {
        'fire_date': '2018-11-08T06:33:00',
        'critical_alert_date': '2018-05-21',
        'days_advance_warning': 308,
        'tower_built': 1919,
        'tower_age_at_fire': 99,
        'components': 1,
    }

    if data is not None:
        stats.update({
            'total_records': len(data),
            'date_range': {
                'start': str(data['timestamp'].min()),
                'end': str(data['timestamp'].max())
            }
        })

    return jsonify(stats)


@app.route('/api/health', methods=['GET'])
def health():
    """Health check"""
    data = load_data()
    return jsonify({
        'status': 'ok',
        'data_available': data is not None,
        'api_version': '1.0'
    })


def generate_simulated_snapshot(date):
    """
    Generate a simulated component snapshot for a date.
    Used when real data is not available.
    """
    fire_date = pd.Timestamp(2018, 11, 8)
    critical_alert_date = pd.Timestamp(2018, 5, 21)

    days_until_fire = (fire_date - date).days

    # Determine zone based on date
    zone = 'green'
    cci = 0.3

    if date >= critical_alert_date:
        days_since_critical = (date - critical_alert_date).days
        progress = min(days_since_critical / 308, 1)

        if progress < 0.3:
            zone = 'yellow'
            cci = 0.6 + progress * 0.2
        elif progress < 0.7:
            zone = 'orange'
            cci = 0.8 + progress * 0.15
        else:
            zone = 'red'
            cci = 0.95

    # Generate realistic sensor values
    import numpy as np
    np.random.seed(int(date.timestamp()))

    return [{
        'component_id': TOWER_27_222['component_id'],
        'name': TOWER_27_222['name'],
        'timestamp': date.isoformat(),
        'lat': TOWER_27_222['lat'],
        'lon': TOWER_27_222['lon'],
        'location': TOWER_27_222['location'],
        'built_year': TOWER_27_222['built_year'],
        'age_years': date.year - TOWER_27_222['built_year'],
        'zone': zone,
        'cci': round(cci, 3),
        'temperature': round(65 + np.random.normal(0, 5) + (cci * 10), 1),
        'vibration': round(0.15 + (cci * 0.5), 4),
        'strain': round(120 + (cci * 200), 1),
        'wind_speed': round(15 + (max(0, (308 - days_until_fire) / 308) * 40), 1),
        'days_until_fire': days_until_fire,
    }]


@app.route('/', methods=['GET'])
def index():
    """API documentation"""
    return jsonify({
        'name': 'Paradise Demo API',
        'version': '1.0',
        'description': 'Serves Camp Fire prediction data for Tower 27/222',
        'endpoints': {
            'GET /api/snapshot/<date>': 'Get component data for a date (YYYY-MM-DD)',
            'GET /api/components': 'Get list of all components',
            'GET /api/time-series/<component_id>': 'Get full time-series (optional: ?start_date=&end_date=)',
            'GET /api/stats': 'Get overall stats',
            'GET /api/health': 'Health check'
        },
        'example_requests': {
            'snapshot': '/api/snapshot/2018-05-21',
            'components': '/api/components',
            'time_series': '/api/time-series/TOWER_27_222?start_date=2016-01-01&end_date=2018-11-08'
        }
    })


if __name__ == '__main__':
    print("=" * 50)
    print("Paradise Demo API Server")
    print("=" * 50)
    print(f"Tower: {TOWER_27_222['name']}")
    print(f"Location: {TOWER_27_222['location']}")
    print(f"Coordinates: {TOWER_27_222['lat']}, {TOWER_27_222['lon']}")
    print()

    # Try to load data at startup
    print("Attempting to load scored data...")
    data = load_data()

    if data is None:
        print("⚠️  No scored data found. Using simulated data.")
        print("    To enable real data, run:")
        print("    $ python scripts/score_paradise_data.py")
        print()

    print("Starting server on http://localhost:5000")
    print("API docs at http://localhost:5000/")
    print("=" * 50)
    print()

    app.run(debug=True, port=5000)
