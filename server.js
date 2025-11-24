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

// Emergency hospital finder - implemented in Node.js with Geoapify
app.post('/emergency-hospitals', async (req, res) => {
  try {
    const { latitude, longitude } = req.body;

    const GEOAPIFY_API_KEY = process.env.GEOAPIFY_API_KEY;

    if (!GEOAPIFY_API_KEY) {
      console.log('No Geoapify API key found');
      return res.status(500).json({ error: 'Geoapify API key not configured' });
    }

    if (!latitude || !longitude) {
      console.log('No location provided');
      return res.status(400).json({ error: 'Location required' });
    }

    console.log(`Searching for hospitals near: ${latitude}, ${longitude}`);

    // Call Geoapify API
    const url = `https://api.geoapify.com/v2/places?categories=healthcare.hospital,healthcare.clinic,healthcare&filter=circle:${longitude},${latitude},10000&limit=10&apiKey=${GEOAPIFY_API_KEY}`;

    const response = await axios.get(url, { timeout: 10000 });

    if (response.data && response.data.features && response.data.features.length > 0) {
      console.log(`Found ${response.data.features.length} hospitals from Geoapify`);
      return res.json({ features: response.data.features });
    } else {
      console.log('No hospitals found from Geoapify');
      return res.status(404).json({ error: 'No hospitals found nearby' });
    }

  } catch (error) {
    console.error('Error finding hospitals:', error.message);
    return res.status(500).json({ error: 'Failed to find hospitals: ' + error.message });
  }
});

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