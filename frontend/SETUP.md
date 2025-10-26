# LiveWire Setup Instructions

## 🔐 Environment Variables Setup

1. **Copy the environment template:**

   ```bash
   cp .env.example .env
   ```

2. **Fill in your API keys in `.env`:**

   ```bash
   # Get your Mapbox token from: https://account.mapbox.com/access-tokens/
   REACT_APP_MAPBOX_TOKEN=your_mapbox_token_here

   # Get your Anthropic API key from: https://console.anthropic.com/
   REACT_APP_ANTHROPIC_API_KEY=your_anthropic_api_key_here
   ```

## 🚀 Installation & Running

1. **Install dependencies:**

   ```bash
   npm install
   ```

2. **Start the development server:**

   ```bash
   npm start
   ```

3. **Open your browser:**
   Navigate to `http://localhost:3000`

## 🔑 Required API Keys

### Mapbox API Key

- **Purpose**: 3D city maps and world visualization
- **Get it from**: https://account.mapbox.com/access-tokens/
- **Required scopes**: `styles:read`, `fonts:read`, `datasets:read`

### Anthropic Claude API Key

- **Purpose**: AI-powered cable risk assessment
- **Get it from**: https://console.anthropic.com/
- **Required**: Valid Anthropic account with API access

## 🛡️ Security Notes

- **Never commit `.env` file** - It's already in `.gitignore`
- **Use `.env.example`** as a template for other developers
- **Rotate API keys** regularly for security
- **Use different keys** for development and production

## 📁 Project Structure

```
src/
├── components/
│   ├── LandingPage.js      # Landing page with world map
│   ├── Dashboard.js        # Main dashboard
│   ├── LosAngelesMap.js    # City maps (LA, SF, Paradise, NYC)
│   └── EconomicAssessment.js
├── contexts/
│   └── CityContext.js      # City state management
└── App.js                  # Main app component
```

## 🌍 Features

- **Interactive World Map**: Rotating globe with global cable network
- **City Visualizations**: 4 cities with detailed cable networks
- **AI Risk Assessment**: Click cables for AI-powered analysis
- **Real-time Monitoring**: Live cable health data
- **Responsive Design**: Works on all devices

## 🚀 Deployment

1. **Build for production:**

   ```bash
   npm run build
   ```

2. **Deploy to your hosting platform** (Vercel, Netlify, etc.)

3. **Set environment variables** in your hosting platform's dashboard

## 🆘 Troubleshooting

- **Map not loading**: Check your Mapbox token
- **AI not working**: Verify Anthropic API key
- **Build errors**: Ensure all environment variables are set
