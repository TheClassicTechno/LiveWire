/**
 * City Configuration
 * Centralized configuration for all cities with map view settings
 */

export const CITY_CONFIG = {
  'los-angeles': {
    name: 'Los Angeles Cable Network',
    center: [-118.2500, 34.0500],
    zoom: 17,
    pitch: 60,
    bearing: 0,
    description: 'Downtown LA Financial District cables'
  },
  'san-francisco': {
    name: 'San Francisco Cable Network',
    center: [-122.4000, 37.7900],
    zoom: 17,
    pitch: 60,
    bearing: 0,
    description: 'SF Financial District cables'
  },
  'paradise-city': {
    name: 'Paradise Cable Network',
    center: [-121.5795, 39.7596],
    zoom: 14,
    pitch: 60,
    bearing: 0,
    description: 'Actual Paradise, CA (2018 Camp Fire location)'
  },
  'new-york': {
    name: 'New York City Cable Network',
    center: [-74.0060, 40.7128],
    zoom: 17,
    pitch: 60,
    bearing: 0,
    description: 'NYC Financial District cables'
  }
};

/**
 * Get city configuration by ID
 */
export const getCityConfig = (cityId) => CITY_CONFIG[cityId];

/**
 * Get next city in rotation
 */
export const getNextCity = (currentCity) => {
  const cities = Object.keys(CITY_CONFIG);
  const currentIndex = cities.indexOf(currentCity);
  const nextIndex = (currentIndex + 1) % cities.length;
  return cities[nextIndex];
};

/**
 * Get all available cities
 */
export const getAllCities = () => Object.keys(CITY_CONFIG);
