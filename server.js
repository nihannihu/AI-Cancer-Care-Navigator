const express = require('express');
const cors = require('cors');
const path = require('path');
const { createProxyMiddleware } = require('http-proxy-middleware');
const axios = require('axios');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;
const AI_BACKEND_URL = process.env.AI_BACKEND_URL || 'http://localhost:8000';

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Serve static files
app.use('/static', express.static(path.join(__dirname, 'static'), {
  maxAge: '1d',
  etag: false
}));

// Proxy uploaded images to Python backend
app.use('/static/uploads', createProxyMiddleware({
  target: AI_BACKEND_URL,
  changeOrigin: true,
  secure: false,
  headers: {
    'ngrok-skip-browser-warning': 'true'
  }
}));

// Proxy API requests to Python backend
app.use('/pcp', createProxyMiddleware({
  target: AI_BACKEND_URL,
  changeOrigin: true,
  secure: false,
  headers: {
    'ngrok-skip-browser-warning': 'true'
  }
}));

app.use('/oncologist', createProxyMiddleware({
  target: AI_BACKEND_URL,
  changeOrigin: true,
  secure: false,
  headers: {
    'ngrok-skip-browser-warning': 'true'
  }
}));

app.use('/patient', createProxyMiddleware({
  target: AI_BACKEND_URL,
  changeOrigin: true,
  secure: false,
  headers: {
    'ngrok-skip-browser-warning': 'true'
  }
}));

app.use('/ai-diagnostics', createProxyMiddleware({
  target: AI_BACKEND_URL,
  changeOrigin: true,
  secure: false,
  headers: {
    'ngrok-skip-browser-warning': 'true'
  }
}));

// AI API endpoints
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

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'OK',
    message: 'Frontend server is running',
    backend: AI_BACKEND_URL
  });
});

// Serve the main index.html for root route
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'static', 'index.html'));
});

// Fallback to serve index.html for any other routes (SPA behavior)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'static', 'index.html'));
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Frontend server running on port ${PORT}`);
  console.log(`Backend API proxied to: ${AI_BACKEND_URL}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
});