const express = require('express');
const cors = require('cors');
const path = require('path');
const { createProxyMiddleware } = require('http-proxy-middleware');
require('dotenv').config();


// Proxy API requests to Python backend
// Core app pages
app.use('/pcp', createProxyMiddleware({
  target: AI_BACKEND_URL,
  changeOrigin: true,
  secure: false, // For ngrok https
}));

app.use('/oncologist', createProxyMiddleware({
  target: AI_BACKEND_URL,
  changeOrigin: true,
  secure: false, // For ngrok https
}));

app.use('/patient', createProxyMiddleware({
  target: AI_BACKEND_URL,
  changeOrigin: true,
  secure: false, // For ngrok https
}));

app.use('/ai-diagnostics', createProxyMiddleware({
  target: AI_BACKEND_URL,
  changeOrigin: true,
  secure: false, // For ngrok https
}));

// AI API endpoints
app.use('/api', createProxyMiddleware({
  target: AI_BACKEND_URL,
  changeOrigin: true,
  secure: false,
}));

// Emergency hospital finder
app.use('/emergency-hospitals', createProxyMiddleware({
  target: AI_BACKEND_URL,
  changeOrigin: true,
  secure: false,
}));

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({
    status: 'OK',
    message: 'Frontend server is running',
    backend: AI_BACKEND_URL
  });
});

// API status endpoint
app.get('/api/status', (req, res) => {
  res.json({
    status: 'Frontend Ready',
    message: 'Proxy server configured',
    backend: AI_BACKEND_URL,
    setup: {
      buildCommand: 'npm install',
      startCommand: 'node server.js',
      runtime: 'Node.js',
      port: 'PORT environment variable or 3000'
    }
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