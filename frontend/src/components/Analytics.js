import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Thermometer, 
  Zap, 
  Activity, 
  AlertTriangle, 
  CheckCircle,
  TrendingDown
} from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import './Analytics.css';

const Analytics = () => {
  const [selectedParameter, setSelectedParameter] = useState('temperature');
  const [timeRange, setTimeRange] = useState('24h');

  // Mock data for demonstration
  const generateMockData = (parameter, hours = 24) => {
    const data = [];
    const now = new Date();
    
    for (let i = hours; i >= 0; i--) {
      const time = new Date(now.getTime() - i * 60 * 60 * 1000);
      let value;
      
      switch (parameter) {
        case 'temperature':
          value = 25 + Math.sin(i / 4) * 10 + Math.random() * 5;
          break;
        case 'vibration':
          value = 1.5 + Math.sin(i / 3) * 0.8 + Math.random() * 0.3;
          break;
        case 'strain':
          value = 0.5 + Math.sin(i / 5) * 0.3 + Math.random() * 0.1;
          break;
        default:
          value = 50 + Math.random() * 20;
      }
      
      data.push({
        time: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        value: Math.round(value * 100) / 100,
        healthy: parameter === 'temperature' ? value < 40 : 
                 parameter === 'vibration' ? value < 2.5 : 
                 parameter === 'strain' ? value < 0.8 : true
      });
    }
    
    return data;
  };

  const [chartData, setChartData] = useState(generateMockData('temperature'));

  useEffect(() => {
    setChartData(generateMockData(selectedParameter, timeRange === '24h' ? 24 : 168));
  }, [selectedParameter, timeRange]);

  const parameters = [
    {
      id: 'temperature',
      name: 'Temperature',
      unit: '°C',
      icon: Thermometer,
      healthyRange: { min: 20, max: 40 },
      unhealthyRange: { min: 40, max: 80 },
      description: 'Cable temperature indicating potential overheating or degradation',
      color: 'var(--electric-orange)',
      healthyColor: 'var(--electric-green)',
      unhealthyColor: 'var(--electric-orange)'
    },
    {
      id: 'vibration',
      name: 'Vibration',
      unit: 'm/s²',
      icon: Activity,
      healthyRange: { min: 0, max: 2.5 },
      unhealthyRange: { min: 2.5, max: 5 },
      description: 'Vibration levels detecting mechanical stress or external impact',
      color: 'var(--electric-purple)',
      healthyColor: 'var(--electric-green)',
      unhealthyColor: 'var(--electric-purple)'
    },
    {
      id: 'strain',
      name: 'Strain',
      unit: 'mm/m',
      icon: Zap,
      healthyRange: { min: 0, max: 0.8 },
      unhealthyRange: { min: 0.8, max: 2 },
      description: 'Strain measurements detecting elongation or deformation under stress',
      color: 'var(--electric-blue)',
      healthyColor: 'var(--electric-green)',
      unhealthyColor: 'var(--electric-blue)'
    }
  ];

  const currentParam = parameters.find(p => p.id === selectedParameter);
  const currentValue = chartData[chartData.length - 1]?.value || 0;
  const isHealthy = currentValue <= currentParam.healthyRange.max;

  const cableStates = [
    { state: 'Normal', count: 847, percentage: 96.8, color: 'var(--electric-green)', icon: CheckCircle },
    { state: 'Degradation', count: 23, percentage: 2.6, color: 'var(--electric-yellow)', icon: AlertTriangle },
    { state: 'Fault', count: 5, percentage: 0.6, color: 'var(--electric-orange)', icon: TrendingDown }
  ];

  return (
    <div className="analytics">
      {/* Parameter Selection */}
      <div className="parameter-selector">
        <h2 className="section-title">Cable Health Parameters</h2>
        <div className="parameter-tabs">
          {parameters.map((param) => {
            const Icon = param.icon;
            return (
              <motion.button
                key={param.id}
                className={`param-tab ${selectedParameter === param.id ? 'active' : ''}`}
                onClick={() => setSelectedParameter(param.id)}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Icon className="param-icon" style={{ color: param.color }} />
                <span className="param-name">{param.name}</span>
                <span className="param-unit">{param.unit}</span>
              </motion.button>
            );
          })}
        </div>
      </div>

      {/* Current Status */}
      <div className="current-status">
        <div className="status-card card-electric">
          <div className="status-header">
            <div className="status-icon" style={{ color: currentParam.color }}>
              <currentParam.icon />
            </div>
            <div className="status-info">
              <h3 className="status-title">{currentParam.name}</h3>
              <p className="status-description">{currentParam.description}</p>
            </div>
          </div>
          <div className="status-value">
            <span className="value-number" style={{ color: isHealthy ? currentParam.healthyColor : currentParam.unhealthyColor }}>
              {currentValue}
            </span>
            <span className="value-unit">{currentParam.unit}</span>
            <div className={`status-indicator ${isHealthy ? 'healthy' : 'unhealthy'}`}>
              {isHealthy ? <CheckCircle /> : <AlertTriangle />}
              <span>{isHealthy ? 'Healthy' : 'Warning'}</span>
            </div>
          </div>
        </div>

        {/* Health Range */}
        <div className="health-range card-electric">
          <h4 className="range-title">Health Range</h4>
          <div className="range-bar">
            <div className="range-segment healthy" style={{ backgroundColor: currentParam.healthyColor }}>
              <span>Healthy: {currentParam.healthyRange.min} - {currentParam.healthyRange.max} {currentParam.unit}</span>
            </div>
            <div className="range-segment unhealthy" style={{ backgroundColor: currentParam.unhealthyColor }}>
              <span>Warning: {currentParam.unhealthyRange.min} - {currentParam.unhealthyRange.max} {currentParam.unit}</span>
            </div>
          </div>
          <div className="current-marker" style={{ 
            left: `${Math.min(100, Math.max(0, ((currentValue - currentParam.healthyRange.min) / (currentParam.unhealthyRange.max - currentParam.healthyRange.min)) * 100))}%`,
            backgroundColor: isHealthy ? currentParam.healthyColor : currentParam.unhealthyColor
          }}>
            <span>{currentValue}</span>
          </div>
        </div>
      </div>

      {/* Time Range Selector */}
      <div className="time-range-selector">
        <div className="time-tabs">
          {['24h', '7d'].map((range) => (
            <button
              key={range}
              className={`time-tab ${timeRange === range ? 'active' : ''}`}
              onClick={() => setTimeRange(range)}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {/* Chart */}
      <div className="chart-container card-electric">
        <h3 className="chart-title">{currentParam.name} Trend</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
            <XAxis 
              dataKey="time" 
              stroke="var(--text-secondary)"
              fontSize={12}
            />
            <YAxis 
              stroke="var(--text-secondary)"
              fontSize={12}
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: 'var(--dark-surface)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                color: 'var(--text-primary)'
              }}
            />
            <Line 
              type="monotone" 
              dataKey="value" 
              stroke={currentParam.color}
              strokeWidth={3}
              dot={{ fill: currentParam.color, strokeWidth: 2, r: 4 }}
              activeDot={{ r: 6, stroke: currentParam.color, strokeWidth: 2 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Cable State Distribution */}
      <div className="cable-states">
        <h3 className="section-title">Cable State Distribution</h3>
        <div className="states-grid">
          {cableStates.map((state) => {
            const Icon = state.icon;
            return (
              <motion.div 
                key={state.state}
                className="state-card card-electric"
                whileHover={{ scale: 1.02 }}
                transition={{ duration: 0.2 }}
              >
                <div className="state-header">
                  <Icon className="state-icon" style={{ color: state.color }} />
                  <span className="state-name">{state.state}</span>
                </div>
                <div className="state-stats">
                  <div className="state-count" style={{ color: state.color }}>
                    {state.count}
                  </div>
                  <div className="state-percentage">
                    {state.percentage}%
                  </div>
                </div>
                <div className="state-bar">
                  <div 
                    className="state-progress" 
                    style={{ 
                      width: `${state.percentage}%`,
                      backgroundColor: state.color
                    }}
                  />
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Comparison Chart */}
      <div className="comparison-chart card-electric">
        <h3 className="chart-title">Parameter Comparison</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={parameters.map(p => ({
            name: p.name,
            healthy: p.healthyRange.max,
            current: chartData[chartData.length - 1]?.value || 0
          }))}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
            <XAxis 
              dataKey="name" 
              stroke="var(--text-secondary)"
              fontSize={12}
            />
            <YAxis 
              stroke="var(--text-secondary)"
              fontSize={12}
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: 'var(--dark-surface)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                color: 'var(--text-primary)'
              }}
            />
            <Bar dataKey="healthy" fill="var(--electric-green)" opacity={0.7} />
            <Bar dataKey="current" fill="var(--electric-blue)" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default Analytics;
