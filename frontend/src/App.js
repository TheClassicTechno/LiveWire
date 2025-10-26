import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { CityProvider } from './contexts/CityContext';
import LandingPage from './components/LandingPage';
import Dashboard from './components/Dashboard';
import ParadiseDemoMap from './components/ParadiseDemoMap';
import LiveElasticsearchDashboard from './components/LiveElasticsearchDashboard';
import LiveComponentDashboard from './components/LiveComponentDashboard';
import './App.css';

function App() {
  return (
    <CityProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/camp-fire-demo" element={<ParadiseDemoMap />} />
            <Route path="/elasticsearch" element={<LiveElasticsearchDashboard />} />
            <Route path="/live-component" element={<LiveComponentDashboard />} />
          </Routes>
        </div>
      </Router>
    </CityProvider>
  );
}

export default App;
