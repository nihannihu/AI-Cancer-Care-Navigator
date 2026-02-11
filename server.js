// Add error handling for missing dependencies
try {
  require('express');
  require('cors');
  require('http-proxy-middleware');
  require('dotenv').config();
  // Remove axios from dependency check since we're not using it
} catch (error) {
  console.error('❌ Missing dependencies. Please run "npm install" before starting the server.');
  console.error('Error details:', error.message);
  process.exit(1);
}

const express = require('express');
const cors = require('cors');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');

// Load environment variables
const PORT = process.env.PORT || 3001;
const AI_BACKEND_URL = process.env.AI_BACKEND_URL || 'http://localhost:8000';

const app = express();

// Enable CORS for all routes
app.use(cors());

// Parse JSON bodies
app.use(express.json());

// Serve static files from the "static" directory
app.use(express.static(path.join(__dirname, 'static')));

// Serve template files from the "templates" directory
app.use(express.static(path.join(__dirname, 'templates')));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Proxy AI backend requests
app.use('/api', createProxyMiddleware({
  target: AI_BACKEND_URL,
  changeOrigin: true,
  secure: false,
  headers: {
    'ngrok-skip-browser-warning': 'true'
  }
}));

// Add emergency endpoint to proxy to Python backend
app.use('/emergency-hospitals', createProxyMiddleware({
  target: AI_BACKEND_URL,
  changeOrigin: true,
  secure: false,
  headers: {
    'ngrok-skip-browser-warning': 'true'
  }
}));

// Add ambulance endpoint to proxy to Python backend
app.use('/ambulance', createProxyMiddleware({
  target: AI_BACKEND_URL,
  changeOrigin: true,
  secure: false,
  headers: {
    'ngrok-skip-browser-warning': 'true'
  }
}));

// Serve the main page
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'templates', 'base.html'));
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Frontend server running on port ${PORT}`);
  console.log(`Backend API proxied to: ${AI_BACKEND_URL}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
});