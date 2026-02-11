# Docker Setup Instructions

This project includes Docker configuration files to easily replicate the environment on any machine.

## Files Included

1. `Dockerfile.python` - Docker configuration for the Python backend
2. `Dockerfile.node` - Docker configuration for the Node.js frontend
3. `docker-compose.yml` - Configuration to run both services together

## Prerequisites

- Docker installed on your system
- Docker Compose installed (usually included with Docker Desktop)

## Setup Instructions

1. **Prepare Environment Variables:**
   - Copy `.env.example` to `.env`:
     ```
     cp .env.example .env
     ```
   - Edit `.env` and add your actual API keys and configuration

2. **Build and Run with Docker Compose (Recommended):**
   ```bash
   docker-compose up --build
   ```

3. **Access the Applications:**
   - Node.js Frontend: http://localhost:3001
   - Python Backend API: http://localhost:8000

## Alternative: Build and Run Individually

### Python Backend:
```bash
# Build the Python Docker image
docker build -t onco-navigator-python -f Dockerfile.python .

# Run the Python container
docker run -p 8000:8000 --env-file .env onco-navigator-python
```

### Node.js Frontend:
```bash
# Build the Node Docker image
docker build -t onco-navigator-node -f Dockerfile.node .

# Run the Node container
docker run -p 3001:3001 -e AI_BACKEND_URL=http://host.docker.internal:8000 onco-navigator-node
```

## Stopping the Services

If you used docker-compose:
```bash
docker-compose down
```

If you ran containers individually:
```bash
docker ps  # Find container IDs
docker stop [container-id]
```

## Notes

- The docker-compose setup automatically links the services so the frontend can communicate with the backend
- When running individually, you may need to adjust the AI_BACKEND_URL to match your Docker host IP
- All dependencies are locked to specific versions ensuring consistency across environments