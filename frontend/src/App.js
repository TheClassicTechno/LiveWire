import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { CityProvider } from './contexts/CityContext';
import LandingPage from './components/LandingPage';
import Dashboard from './components/Dashboard';
import './App.css';

function App() {
  return (
    <CityProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/dashboard" element={<Dashboard />} />
          </Routes>
        </div>
      </Router>
    </CityProvider>
  );
}

export default App;
