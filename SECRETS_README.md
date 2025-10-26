# API Keys and Secrets Management

## 🔐 Secret Files Location

Your API keys are stored in the following files (all ignored by git):

### Root Directory
- **`.env`** - Main environment variables
- **`secrets.json`** - JSON format API keys

### Frontend Directory  
- **`frontend/.env`** - React environment variables

## 🔑 Available API Keys

### Claude AI API
- **Key**: `sk-ant-api03-***[HIDDEN]***`
- **Usage**: AI model interactions, chat features
- **Location**: `.env`, `secrets.json`, `frontend/.env`

### Mapbox API
- **Key**: `pk.***[HIDDEN]***`
- **Usage**: Map rendering, geolocation features
- **Location**: `.env`, `secrets.json`, `frontend/.env`

### Vercel Project
- **ID**: `***[HIDDEN]***`
- **Usage**: Deployment configuration
- **Location**: `.env`, `secrets.json`, `frontend/.env`

## 🛡️ Security Features

✅ **Git Protection**: All secret files are in `.gitignore`
✅ **Multiple Formats**: Environment vars, JSON, React env
✅ **Frontend Ready**: React apps can access `REACT_APP_*` variables
✅ **Backend Ready**: Python can load from `.env` or `secrets.json`

## 📝 Usage Examples

### Python Backend
```python
import json
import os
from dotenv import load_dotenv

# Method 1: Load from .env
load_dotenv()
claude_key = os.getenv('ANTHROPIC_API_KEY')
mapbox_key = os.getenv('MAPBOX_TOKEN')

# Method 2: Load from secrets.json
with open('secrets.json', 'r') as f:
    secrets = json.load(f)
    claude_key = secrets['claude_api_key']
    mapbox_key = secrets['mapbox_api_key']
```

### React Frontend
```javascript
// Access environment variables in React
const mapboxToken = process.env.REACT_APP_MAPBOX_TOKEN;
const claudeKey = process.env.REACT_APP_ANTHROPIC_API_KEY;
const vercelId = process.env.REACT_APP_VERCEL_TOKEN;
```

## ⚠️ Security Reminders

1. **Never commit secret files** - They're gitignored
2. **Don't share API keys** in chat/email
3. **Rotate keys** if compromised
4. **Use environment variables** in production
5. **Keep backups** of your keys securely

## 🔄 Git Status Check

To verify secrets are ignored:
```bash
git check-ignore .env secrets.json frontend/.env
# Should return all three files
```