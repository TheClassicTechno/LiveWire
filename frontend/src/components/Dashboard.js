import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Zap,
  Activity,
  BarChart3,
  DollarSign,
  Menu,
  X,
  AlertTriangle,
  Radio,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useCity } from "../contexts/CityContext";
import Analytics from "./Analytics";
import EconomicAssessment from "./EconomicAssessment";
import LosAngelesMap from "./LosAngelesMap";
import LiveMetrics from "./LiveMetrics";
import "./Dashboard.css";

const Dashboard = () => {
  const navigate = useNavigate();
  const { getCurrentCityStats, setCurrentCity } = useCity();
  const [activeTab, setActiveTab] = useState("health");
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleLogoClick = () => {
    navigate("/");
  };

  const cities = [
    { id: "paradise", label: "Paradise (Camp Fire)", key: "paradise-city" },
    { id: "la", label: "Los Angeles", key: "los-angeles" },
    { id: "sf", label: "San Francisco", key: "san-francisco" },
  ];

  const mainTabs = [
    { id: "live", label: "Live Data", icon: Radio },
    { id: "analytics", label: "Analytics", icon: BarChart3 },
    { id: "economic", label: "Economic Assessment", icon: DollarSign },
  ];

  const [currentCityIndex, setCurrentCityIndex] = useState(0);

  const tabs = mainTabs;
  const currentCity = cities[currentCityIndex];

  // Navigate between cities
  const handlePrevCity = () => {
    const newIndex = (currentCityIndex - 1 + cities.length) % cities.length;
    setCurrentCityIndex(newIndex);
    setCurrentCity(cities[newIndex].key);
  };

  const handleNextCity = () => {
    const newIndex = (currentCityIndex + 1) % cities.length;
    setCurrentCityIndex(newIndex);
    setCurrentCity(cities[newIndex].key);
  };

  // Update city context when tab changes
  const handleTabChange = (tabId) => {
    setActiveTab(tabId);
  };

  const renderContent = () => {
    // Always render the map as the base content, but it's persistent across tabs
    if (activeTab === "analytics") {
      return <Analytics />;
    }
    if (activeTab === "economic") {
      return <EconomicAssessment />;
    }
    if (activeTab === "live") {
      return <LiveMetrics />;
    }
    // For all city tabs (paradise, la, sf), render the same persistent map
    // The map updates internally based on currentCity from CityContext
    return <LosAngelesMap />;
  };

  return (
    <div className="dashboard">
      {/* Sidebar */}
      <motion.aside
        className={`sidebar ${sidebarOpen ? "open" : "closed"}`}
        initial={{ x: -300 }}
        animate={{ x: sidebarOpen ? 0 : -300 }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
      >
        <div className="sidebar-header">
          <div className="logo-container" onClick={handleLogoClick}>
            <Zap className="logo-icon electric-pulse" />
            <span className="logo-text text-electric">LiveWire</span>
          </div>
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
          >
            {sidebarOpen ? <X /> : <Menu />}
          </button>
        </div>

        <nav className="sidebar-nav">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <motion.button
                key={tab.id}
                className={`nav-item ${activeTab === tab.id ? "active" : ""}`}
                onClick={() => handleTabChange(tab.id)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Icon className="nav-icon" />
                <span className="nav-label">{tab.label}</span>
                {activeTab === tab.id && (
                  <motion.div
                    className="nav-indicator"
                    layoutId="nav-indicator"
                    initial={false}
                    transition={{ duration: 0.2 }}
                  />
                )}
              </motion.button>
            );
          })}
        </nav>

        {/* User Session Info */}
        <div className="sidebar-footer">
          <div className="user-session">
            <div className="session-header">
              <div className="user-avatar">
                <span className="avatar-text">U</span>
              </div>
              <div className="user-info">
                <div className="user-name">User</div>
                <div className="user-role">System Administrator</div>
              </div>
            </div>
            <div className="session-stats">
              <div className="session-item">
                <div className="session-label">Status</div>
                <div className="session-status active">Active</div>
              </div>
            </div>
          </div>
        </div>
      </motion.aside>

      {/* Main content */}
      <main className="main-content">
        <header className="content-header">
          <div className="header-info">
            {activeTab !== "analytics" &&
              activeTab !== "economic" &&
              activeTab !== "live" && (
                <div className="city-navigator">
                  <button
                    className="city-nav-btn"
                    onClick={handlePrevCity}
                    aria-label="Previous city"
                  >
                    <ChevronLeft size={20} />
                  </button>
                  <h1 className="page-title">{currentCity.label}</h1>
                  <button
                    className="city-nav-btn"
                    onClick={handleNextCity}
                    aria-label="Next city"
                  >
                    <ChevronRight size={20} />
                  </button>
                </div>
              )}
            {(activeTab === "analytics" ||
              activeTab === "economic" ||
              activeTab === "live") && (
              <h1 className="page-title">
                {tabs.find((tab) => tab.id === activeTab)?.label}
              </h1>
            )}
            <p className="page-subtitle">
              {activeTab === "paradise" &&
                "Real transmission grid - 2018 Camp Fire case study with Tower 27/222"}
              {activeTab === "la" &&
                "Real transmission grid visualization for Los Angeles area"}
              {activeTab === "sf" &&
                "Real transmission grid visualization for San Francisco area"}
              {activeTab === "analytics" &&
                "Detailed analysis of transmission line parameters and risk trends"}
              {activeTab === "economic" &&
                "Cost analysis and economic impact assessment"}
              {activeTab === "live" &&
                "Real-time transmission line data and system metrics"}
            </p>
          </div>

          {/* Network Stats */}
          <div className="network-stats-header">
            <div className="stat-item">
              <div className="stat-number">{getCurrentCityStats().cables}</div>
              <div className="stat-label">Individual Cables</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">
                {getCurrentCityStats().capacity}
              </div>
              <div className="stat-label">Total Capacity</div>
            </div>
            <div className="stat-item">
              <div className="stat-number">
                {getCurrentCityStats().operational}
              </div>
              <div className="stat-label">Operational</div>
            </div>
          </div>

          <div className="header-actions">
            <div className="status-indicator">
              <div className="status-dot healthy"></div>
              <span>System Online</span>
            </div>
            <div className="last-updated">
              Last updated: {new Date().toLocaleTimeString()}
            </div>
          </div>
        </header>

        <div className="content-body">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3 }}
            >
              {renderContent()}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
