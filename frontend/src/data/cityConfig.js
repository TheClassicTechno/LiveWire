/**
 * City Configuration
 * Real California transmission grids from OpenStreetMap
 */

export const CITY_CONFIG = {
  'los-angeles': {
    key: 'los-angeles',
    name: 'Los Angeles Transmission Grid',
    center: [-118.2437, 34.0522],
    zoom: 16,
    pitch: 60,
    bearing: 0,
    description: 'Real transmission lines - Southern California',
    region: 'LOS_ANGELES'
  },
  'san-francisco': {
    key: 'san-francisco',
    name: 'San Francisco Transmission Grid',
    center: [-122.4194, 37.7749],
    zoom: 16,
    pitch: 60,
    bearing: 0,
    description: 'Real transmission lines - Northern California',
    region: 'SAN_FRANCISCO'
  },
  'paradise-city': {
    key: 'paradise-city',
    name: 'Paradise Transmission Grid',
    center: [-121.5795, 39.7596],
    zoom: 14,
    pitch: 60,
    bearing: 0,
    description: 'Real transmission lines - Camp Fire location (2018)',
    region: 'PARADISE'
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
