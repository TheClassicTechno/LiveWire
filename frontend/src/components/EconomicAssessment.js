import React from 'react';
import { motion } from 'framer-motion';
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  Calculator, 
  Target,
  Zap
} from 'lucide-react';
import { PieChart as RechartsPieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import './EconomicAssessment.css';

const EconomicAssessment = () => {
  // Mock data for economic analysis
  const costSavings = [
    { category: 'Preventive Maintenance', amount: 450000, percentage: 35 },
    { category: 'Emergency Repairs', amount: 320000, percentage: 25 },
    { category: 'Energy Efficiency', amount: 280000, percentage: 22 },
    { category: 'Downtime Reduction', amount: 230000, percentage: 18 }
  ];

  const monthlyTrends = [
    { month: 'Jan', savings: 85000, costs: 12000 },
    { month: 'Feb', savings: 92000, costs: 15000 },
    { month: 'Mar', savings: 78000, costs: 18000 },
    { month: 'Apr', savings: 105000, costs: 14000 },
    { month: 'May', savings: 115000, costs: 16000 },
    { month: 'Jun', savings: 98000, costs: 13000 }
  ];

  const roiData = [
    { name: 'Year 1', roi: 150 },
    { name: 'Year 2', roi: 280 },
    { name: 'Year 3', roi: 420 },
    { name: 'Year 4', roi: 580 },
    { name: 'Year 5', roi: 750 }
  ];

  const pieData = costSavings.map(item => ({
    name: item.category,
    value: item.amount,
    color: item.category === 'Preventive Maintenance' ? 'var(--electric-green)' :
           item.category === 'Emergency Repairs' ? 'var(--electric-blue)' :
           item.category === 'Energy Efficiency' ? 'var(--electric-purple)' :
           'var(--electric-orange)'
  }));

  return (
    <div className="economic-assessment">
      <div className="assessment-header">
        <h2 className="section-title">Economic Impact Analysis</h2>
        <p className="section-subtitle">
          Comprehensive cost-benefit analysis and ROI projections for LifeWire implementation
        </p>
      </div>

      {/* Key Metrics */}
      <div className="key-metrics">
        <div className="metric-card card-electric">
          <div className="metric-icon">
            <DollarSign />
          </div>
          <div className="metric-content">
            <div className="metric-value text-electric">$1.28M</div>
            <div className="metric-label">Annual Savings</div>
            <div className="metric-change positive">
              <TrendingUp />
              <span>+23% vs last year</span>
            </div>
          </div>
        </div>

        <div className="metric-card card-electric">
          <div className="metric-icon">
            <Target />
          </div>
          <div className="metric-content">
            <div className="metric-value text-electric">450%</div>
            <div className="metric-label">ROI (5 years)</div>
            <div className="metric-change positive">
              <TrendingUp />
              <span>+15% vs target</span>
            </div>
          </div>
        </div>

        <div className="metric-card card-electric">
          <div className="metric-icon">
            <Calculator />
          </div>
          <div className="metric-content">
            <div className="metric-value text-electric">$2.1M</div>
            <div className="metric-label">Total Investment</div>
            <div className="metric-change neutral">
              <span>One-time cost</span>
            </div>
          </div>
        </div>

        <div className="metric-card card-electric">
          <div className="metric-icon">
            <Zap />
          </div>
          <div className="metric-content">
            <div className="metric-value text-electric">18</div>
            <div className="metric-label">Months Payback</div>
            <div className="metric-change positive">
              <TrendingDown />
              <span>-3 months vs estimate</span>
            </div>
          </div>
        </div>
      </div>

      {/* Cost Breakdown */}
      <div className="cost-breakdown">
        <h3 className="subsection-title">Cost Savings Breakdown</h3>
        <div className="breakdown-content">
          <div className="pie-chart-container card-electric">
            <h4 className="chart-title">Savings Distribution</h4>
            <ResponsiveContainer width="100%" height={300}>
              <RechartsPieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={120}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{
                    backgroundColor: 'var(--dark-surface)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '8px',
                    color: 'var(--text-primary)'
                  }}
                />
              </RechartsPieChart>
            </ResponsiveContainer>
          </div>

          <div className="savings-list">
            {costSavings.map((item, index) => (
              <motion.div
                key={item.category}
                className="savings-item"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                <div className="savings-header">
                  <span className="savings-category">{item.category}</span>
                  <span className="savings-percentage">{item.percentage}%</span>
                </div>
                <div className="savings-amount">
                  ${item.amount.toLocaleString()}
                </div>
                <div className="savings-bar">
                  <div 
                    className="savings-progress"
                    style={{ 
                      width: `${item.percentage}%`,
                      backgroundColor: pieData[index].color
                    }}
                  />
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Monthly Trends */}
      <div className="monthly-trends card-electric">
        <h3 className="chart-title">Monthly Savings vs Costs</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={monthlyTrends}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
            <XAxis 
              dataKey="month" 
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
            <Bar dataKey="savings" fill="var(--electric-green)" opacity={0.8} />
            <Bar dataKey="costs" fill="var(--electric-orange)" opacity={0.8} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* ROI Projection */}
      <div className="roi-projection card-electric">
        <h3 className="chart-title">5-Year ROI Projection</h3>
        <div className="roi-content">
          <div className="roi-chart">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={roiData}>
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
                <Bar dataKey="roi" fill="var(--electric-blue)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="roi-summary">
            <div className="roi-item">
              <span className="roi-label">Break-even Point</span>
              <span className="roi-value">18 months</span>
            </div>
            <div className="roi-item">
              <span className="roi-label">NPV (5 years)</span>
              <span className="roi-value">$3.2M</span>
            </div>
            <div className="roi-item">
              <span className="roi-label">IRR</span>
              <span className="roi-value">67%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Implementation Timeline */}
      <div className="implementation-timeline card-electric">
        <h3 className="chart-title">Implementation Timeline & Costs</h3>
        <div className="timeline-content">
          <div className="timeline-phases">
            {[
              { phase: 'Phase 1: Planning & Setup', duration: '3 months', cost: '$400K', status: 'completed' },
              { phase: 'Phase 2: Sensor Installation', duration: '6 months', cost: '$800K', status: 'in-progress' },
              { phase: 'Phase 3: AI Integration', duration: '4 months', cost: '$600K', status: 'pending' },
              { phase: 'Phase 4: Optimization', duration: '3 months', cost: '$300K', status: 'pending' }
            ].map((phase, index) => (
              <motion.div
                key={phase.phase}
                className={`timeline-item ${phase.status}`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
              >
                <div className="timeline-marker"></div>
                <div className="timeline-content">
                  <div className="timeline-phase">{phase.phase}</div>
                  <div className="timeline-details">
                    <span className="timeline-duration">{phase.duration}</span>
                    <span className="timeline-cost">{phase.cost}</span>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EconomicAssessment;
