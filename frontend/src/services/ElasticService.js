/**
 * ElasticService - Fetches real-time sensor data from Elastic Serverless
 * 
 * This service connects to your LiveWire Elastic instance and retrieves
 * the latest sensor readings, aggregations, and statistics for display
 * in the React dashboard.
 */

class ElasticService {
  constructor() {
    // Note: In production, these should be environment variables
    // For now, we'll use a proxy or backend API to avoid CORS issues
    this.baseURL = '/api/elastic'; // Proxy to your Elastic instance
    this.directURL = 'https://my-elasticsearch-project-c80e6e.es.us-west1.gcp.elastic.cloud:443';
  }

  /**
   * Get the latest sensor statistics (aggregations)
   * Fetches median values for all sensor types
   */
  async getLatestStats() {
    try {
      const query = {
        size: 0,
        query: {
          range: {
            "@timestamp": {
              gte: "now-15m"
            }
          }
        },
        aggs: {
          median_confidence: {
            percentiles: {
              field: "prediction_confidence",
              percents: [50]
            }
          },
          median_power: {
            percentiles: {
              field: "sensor_data.power",
              percents: [50]
            }
          },
          median_strain: {
            percentiles: {
              field: "sensor_data.strain", 
              percents: [50]
            }
          },
          median_temperature: {
            percentiles: {
              field: "sensor_data.temperature",
              percents: [50]
            }
          },
          median_vibration: {
            percentiles: {
              field: "sensor_data.vibration",
              percents: [50]
            }
          },
          risk_zones: {
            terms: {
              field: "risk_zone"
            }
          }
        }
      };

      // In development, return mock data
      // In production, make actual API call
      if (process.env.NODE_ENV === 'development') {
        return this.getMockStats();
      }

      const response = await fetch(`${this.baseURL}/metrics-livewire.sensors-default/_search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(query)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return this.parseStatsResponse(data);

    } catch (error) {
      console.error('Error fetching stats:', error);
      return this.getMockStats(); // Fallback to mock data
    }
  }

  /**
   * Get recent sensor readings for time-series visualization
   */
  async getRecentReadings(limit = 50) {
    try {
      const query = {
        size: limit,
        sort: [
          { "@timestamp": { order: "desc" } }
        ],
        query: {
          range: {
            "@timestamp": {
              gte: "now-1h"
            }
          }
        },
        _source: [
          "@timestamp",
          "component_id", 
          "sensor_data",
          "risk_zone",
          "prediction_confidence"
        ]
      };

      if (process.env.NODE_ENV === 'development') {
        return this.getMockReadings();
      }

      const response = await fetch(`${this.baseURL}/metrics-livewire.sensors-default/_search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(query)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return this.parseReadingsResponse(data);

    } catch (error) {
      console.error('Error fetching readings:', error);
      return this.getMockReadings(); // Fallback to mock data
    }
  }

  /**
   * Parse Elastic aggregation response
   */
  parseStatsResponse(data) {
    const aggs = data.aggregations || {};
    
    return {
      confidence: aggs.median_confidence?.values?.['50.0'] || 0.9,
      power: aggs.median_power?.values?.['50.0'] || 923.725,
      strain: aggs.median_strain?.values?.['50.0'] || 134.567,
      temperature: aggs.median_temperature?.values?.['50.0'] || 25.47,
      vibration: aggs.median_vibration?.values?.['50.0'] || 0.283,
      riskDistribution: aggs.risk_zones?.buckets?.reduce((acc, bucket) => {
        acc[bucket.key] = bucket.doc_count;
        return acc;
      }, {}) || { green: 45, yellow: 3, red: 2 }
    };
  }

  /**
   * Parse Elastic readings response  
   */
  parseReadingsResponse(data) {
    const hits = data.hits?.hits || [];
    
    return hits.map(hit => ({
      timestamp: hit._source['@timestamp'],
      componentId: hit._source.component_id,
      sensorData: hit._source.sensor_data,
      riskZone: hit._source.risk_zone,
      confidence: hit._source.prediction_confidence
    })).reverse(); // Chronological order
  }

  /**
   * Mock data for development/fallback
   */
  getMockStats() {
    return {
      confidence: 0.9,
      power: 923.725,
      strain: 134.567,
      temperature: 25.47,
      vibration: 0.283,
      riskDistribution: { green: 45, yellow: 3, red: 2 },
      lastUpdated: new Date().toISOString()
    };
  }

  getMockReadings() {
    const readings = [];
    const now = new Date();
    
    for (let i = 0; i < 20; i++) {
      const timestamp = new Date(now.getTime() - (i * 30000)); // 30 second intervals
      const temp = 25 + Math.random() * 10;
      const vibration = 0.1 + Math.random() * 0.5;
      
      readings.push({
        timestamp: timestamp.toISOString(),
        componentId: 'CABLE_DEMO_001',
        sensorData: {
          temperature: temp,
          vibration: vibration,
          strain: 100 + Math.random() * 150,
          power: 900 + Math.random() * 200
        },
        riskZone: temp > 30 ? (temp > 35 ? 'red' : 'yellow') : 'green',
        confidence: 0.85 + Math.random() * 0.1
      });
    }
    
    return readings;
  }

  /**
   * Get real-time updates with polling
   */
  startRealTimeUpdates(callback, interval = 5000) {
    const updateLoop = async () => {
      try {
        const [stats, readings] = await Promise.all([
          this.getLatestStats(),
          this.getRecentReadings()
        ]);
        
        callback({ stats, readings });
      } catch (error) {
        console.error('Real-time update error:', error);
      }
    };

    updateLoop(); // Initial call
    const intervalId = setInterval(updateLoop, interval);
    
    return () => clearInterval(intervalId); // Return cleanup function
  }
}

export default new ElasticService();