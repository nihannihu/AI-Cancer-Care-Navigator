const express = require('express');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('static'));

// Serve HTML templates
app.use('/templates', express.static(path.join(__dirname, 'templates')));

// Root route - serve the index.html from templates
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'templates', 'index.html'));
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'OK', message: 'Frontend server is running' });
});

// Proxy endpoint for AI backend (to be configured with your ngrok URL)
app.get('/api/status', (req, res) => {
  res.json({ 
    status: 'Frontend Ready', 
    message: 'Configure AI_BACKEND_URL environment variable with your ngrok URL',
    setup: {
      buildCommand: 'npm install',
      startCommand: 'node server.js',
      runtime: 'Node.js',
      port: 'PORT environment variable or 3000'
    }
  });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Frontend server running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
});