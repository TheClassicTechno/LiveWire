import React, { createContext, useContext, useState } from 'react';

const CityContext = createContext();

export const useCity = () => {
  const context = useContext(CityContext);
  if (!context) {
    throw new Error('useCity must be used within a CityProvider');
  }
  return context;
};

export const CityProvider = ({ children }) => {
  const [currentCity, setCurrentCity] = useState('los-angeles');

  const cityStats = {
    'los-angeles': {
      cables: 36,
      capacity: "12.6GW",
      operational: "100%"
    },
    'san-francisco': {
      cables: 28,
      capacity: "9.8GW",
      operational: "98%"
    },
    'paradise-city': {
      cables: 42,
      capacity: "15.2GW",
      operational: "99%"
    },
    'new-york': {
      cables: 58,
      capacity: "22.4GW",
      operational: "97%"
    }
  };

  const getCurrentCityStats = () => {
    return cityStats[currentCity];
  };

  const value = {
    currentCity,
    setCurrentCity,
    getCurrentCityStats
  };

  return (
    <CityContext.Provider value={value}>
      {children}
    </CityContext.Provider>
  );
};
