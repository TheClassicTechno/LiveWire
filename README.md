# LiveWire: AI-Powered Smart City Cable Monitoring

**An electrocardiogram for the power grid** - AI that monitors and predicts infrastructure disasters before they happen.

## 🏆 Project Overview

LiveWire is a comprehensive AI-powered platform that combines:
- **Backend AI Models**: Python-based machine learning for power grid failure prediction
- **Frontend Dashboard**: React-based interactive visualization and monitoring system

## 🧠 Backend AI Models (Python)

### Production-Ready Models

| Model                       | Specialization        | Performance     | Use Case                 |
| --------------------------- | --------------------- | --------------- | ------------------------ |
| **Grid Risk Model**         | Component degradation | 308-day warning | Infrastructure disasters |
| **Enhanced Neural Network** | Network cascades      | 70% accuracy    | Blackout prevention      |
| **Hybrid Ensemble**         | Multi-algorithm       | 65.7% accuracy  | Robustness & resilience  |

### Key Achievements
- **🔥 Camp Fire 2018**: 308 days advance warning
- **🌊 Cascade Failures**: 70% detection accuracy
- **📊 Multiple Models**: 4+ architectures validated

## 🎨 Frontend Dashboard (React)

### Interactive Features
- **🌍 Global Cable Network**: Rotating world map with real-time cable visualization
- **🏙️ City Monitoring**: 4 cities (LA, SF, Paradise City, NYC) with detailed cable networks
- **⚡ Real-time Alerts**: AI-powered risk assessment with Anthropic Claude integration
- **📊 Analytics Dashboard**: Comprehensive cable health monitoring
- **💰 Economic Assessment**: Cost analysis and impact assessment

### Technologies Used
- **React.js**: Modern frontend framework
- **Mapbox GL JS**: Interactive 3D city maps and world visualization
- **Framer Motion**: Smooth animations and transitions
- **Anthropic Claude API**: AI-powered natural language risk assessment
- **React Router**: Client-side navigation
- **CSS3**: Advanced styling with glassmorphism effects

## 🚀 Quick Start

### Backend Setup (AI Models)
```bash
# Create environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run tests
python scripts/test_camp_fire.py
python scripts/test_enhanced_neural_network_cascade_models.py
```

### Frontend Setup (React Dashboard)
```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Start development server
npm start
```

## 🔑 Required API Keys

### Mapbox API Key
- **Purpose**: 3D city maps and world visualization
- **Get it from**: https://account.mapbox.com/access-tokens/
- **Required scopes**: `styles:read`, `fonts:read`, `datasets:read`

### Anthropic Claude API Key
- **Purpose**: AI-powered cable risk assessment
- **Get it from**: https://console.anthropic.com/
- **Required**: Valid Anthropic account with API access

## 📁 Project Structure

```
LiveWire/
├── 📊 Backend AI Models (Python)
│   ├── models/                    # Core AI Models
│   │   ├── grid_risk_model.py    # 🏆 Grid Risk CCI Pipeline
│   │   ├── hybrid_cascade_model.py # Advanced ensemble
│   │   └── ccimodel.py
│   ├── scripts/                   # Testing & Validation
│   │   ├── test_camp_fire.py      # 308-day validation
│   │   ├── test_enhanced_neural_network_cascade_models.py
│   │   └── [8 more comprehensive tests]
│   ├── utils/                     # Data Pipeline
│   │   ├── cascade_failures_loader.py
│   │   ├── generate_camp_fire_data.py
│   │   └── data_loader.py
│   └── data/                      # Processed datasets
│
├── 🎨 Frontend Dashboard (React)
│   ├── src/
│   │   ├── components/            # React components
│   │   │   ├── LandingPage.js     # Landing page with world map
│   │   │   ├── Dashboard.js       # Main dashboard
│   │   │   ├── LosAngelesMap.js   # City maps (4 cities)
│   │   │   └── EconomicAssessment.js
│   │   ├── contexts/              # State management
│   │   │   └── CityContext.js     # City switching logic
│   │   └── App.js                 # Main app component
│   ├── public/                    # Static assets
│   ├── package.json               # Dependencies
│   ├── .env.example              # Environment template
│   └── SETUP.md                  # Frontend setup guide
│
└── 📖 Documentation
    ├── README.md                  # This file
    ├── CAL_HACKS_GUIDE.md         # Competition guide
    └── frontend/README-FRONTEND.md # Frontend details
```

## 🎯 Use Cases

| Problem                     | Backend Solution | Frontend Display | Result             |
| --------------------------- | ---------------- | ---------------- | ------------------ |
| **Aged equipment failures** | Grid Risk Model  | Real-time alerts | 308-day warning    |
| **Cascade blackouts**       | Neural Network   | Interactive maps | 70% detection      |
| **Network resilience**      | Ensemble models  | Analytics dashboard | Robust predictions |
| **Real-time monitoring**   | Stream pipeline  | Live visualization | Instant alerts     |

## 🔮 What's Next

### Backend Enhancements
- Real-time IoT sensor integration
- Cloud deployment framework
- Production alert system
- Domain-specific model adaptation

### Frontend Enhancements
- Voice agent notifications
- Advanced analytics visualizations
- Mobile app development
- Real-time data streaming

## 📊 Project Stats

### Backend (AI Models)
- **2,395** lines of core model code
- **850+** lines of data integration
- **11** comprehensive test scripts
- **3** validated failure scenarios
- **4+** model architectures

### Frontend (React Dashboard)
- **4** interactive city visualizations
- **Real-time** cable monitoring
- **AI-powered** risk assessment
- **Responsive** design for all devices
- **Modern** UI with glassmorphism effects

## 🏆 Competition Ready

This project is designed to win:
- **CalHacks**: Innovative AI + Frontend integration
- **YCombinator Track**: Production-ready MVP with real impact
- **Hackathon Success**: Complete full-stack solution

## 📞 Key Insight

> "Real data is dramatically better than synthetic. We proved this across 3 datasets: real disaster data (excellent), real topology (very good), fully synthetic (poor).
> 
> **This validates the core ask: deploy IoT sensors. With real data, accuracy will skyrocket.**"

## ⚡ One-Liner

**LiveWire is an agentic electrocardiogram for power grids—predicting catastrophic failures before they happen with AI, visualized through an interactive React dashboard.**

---

_Saving lives with better infrastructure resilience._

## Contributors

- **Backend AI**: @lavirox, @TheClassicTechno, @claude
- **Frontend Dashboard**: @marianaisaw
- **Full-Stack Integration**: Complete AI + React solution

## License

This project is part of the LiveWire initiative to prevent infrastructure disasters through AI-powered monitoring and prediction.
