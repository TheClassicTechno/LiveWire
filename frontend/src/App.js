import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { CityProvider } from './contexts/CityContext';
import LandingPage from './components/LandingPage';
import Dashboard from './components/Dashboard';
import ParadiseDemoMap from './components/ParadiseDemoMap';
import LiveElasticsearchDashboard from './components/LiveElasticsearchDashboard';
<<<<<<< HEAD
=======
import LiveComponentDashboard from './components/LiveComponentDashboard';
>>>>>>> 05e9e369937a6de6abceedcebd5f1a45da0cd095
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
<<<<<<< HEAD
=======
            <Route path="/live-component" element={<LiveComponentDashboard />} />
>>>>>>> 05e9e369937a6de6abceedcebd5f1a45da0cd095
          </Routes>
        </div>
      </Router>
    </CityProvider>
  );
}

export default App;
