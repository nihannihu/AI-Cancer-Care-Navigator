# Deployment Instructions

## Node.js Frontend (Render)

### Build Configuration
```
Build Command: npm install
Start Command: node server.js
Runtime: Node.js
```

### Environment Variables
Set these in Render's environment variables section:
```
PORT=3000
AI_BACKEND_URL=https://your-ngrok-url.ngrok.io
NODE_ENV=production
```

## Python AI Backend (ngrok)

### Local Setup
1. Run the Python backend locally:
   ```bash
   python app_main.py
   ```

2. Expose with ngrok:
   ```bash
   ngrok http 8000
   ```

3. Update the AI_BACKEND_URL in your Node.js environment variables with the ngrok URL.

## Directory Structure
```
project/
├── package.json          # Node.js dependencies
├── server.js            # Node.js server
├── .env                 # Node.js environment variables
├── .env.python          # Python environment variables (rename to .env when running Python)
├── app_main.py          # Python FastAPI application
├── requirements.txt     # Python dependencies
├── templates/           # HTML templates
├── static/              # CSS, JS, images
└── ml/                  # Machine learning models
```

## Deployment Steps

1. Deploy Node.js frontend to Render
2. Run Python backend locally
3. Expose Python backend with ngrok
4. Update Node.js environment with ngrok URL