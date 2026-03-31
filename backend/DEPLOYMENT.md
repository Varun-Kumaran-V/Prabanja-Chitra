# AETHER Constellation Manager - Deployment Guide

## Quick Start (Docker)

### 1. Prepare TLE Data

Place your TLE files in the `data/` directory:
```bash
mkdir -p data
cp /path/to/active.txt data/
cp /path/to/debris_*.txt data/
```

### 2. Build the Docker Image

```bash
cd backend
docker build -t aether-backend .
```

### 3. Run the Container

```bash
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  --name aether-backend \
  aether-backend
```

**For Windows PowerShell:**
```powershell
docker run -d `
  -p 8000:8000 `
  -v ${PWD}/data:/app/data `
  --name aether-backend `
  aether-backend
```

### 4. Verify Health

```bash
curl http://localhost:8000/api/health
```

## Configuration

All configuration is managed through environment variables. See `.env.example` for available options.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |
| `DATA_DIR` | `./data` | Directory containing TLE files |
| `SATELLITE_TLE_FILE` | `active.txt` | Satellite TLE file name |
| `DEBRIS_TLE_FILES` | `debris_iridium.txt,...` | Comma-separated debris TLE files |
| `PREDICTION_HORIZON_SECONDS` | `86400.0` | Conjunction prediction window (24h) |
| `MISS_DISTANCE_ALERT_THRESHOLD_M` | `100.0` | Alert threshold in meters |
| `MAX_DELTA_V_MS` | `15.0` | Maximum delta-v per burn (m/s) |
| `COOLDOWN_SECONDS` | `600.0` | Cooldown between burns (seconds) |
| `CACHE_PROPAGATION_RESULTS` | `true` | Enable result caching |
| `MAX_DEBRIS_IN_SNAPSHOT` | `10000` | Max debris in visualization |

### Using Custom Configuration

Create a `.env` file:
```bash
cp .env.example .env
# Edit .env with your values
```

Then run with docker:
```bash
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  --name aether-backend \
  aether-backend
```

## Local Development

### Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### Run

```bash
# Ensure TLE files are accessible
export DATA_DIR=../  # or set to your data location
export SATELLITE_TLE_FILE=active.txt
export DEBRIS_TLE_FILES=debris_iridium.txt,debris_cosmos.txt,debris_fengyun.txt

python -m app.main
```

The API will be available at `http://localhost:8000`.
Interactive docs: `http://localhost:8000/docs`

## Docker Compose

For easier multi-container setups:

```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATA_DIR=/app/data
      - SATELLITE_TLE_FILE=active.txt
      - DEBRIS_TLE_FILES=debris_iridium.txt,debris_cosmos.txt,debris_fengyun.txt
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d
```

## Production Deployment

### System Requirements

- **OS**: Ubuntu 22.04 LTS or compatible
- **Python**: 3.11+
- **Memory**: 2GB+ (depends on debris count)
- **CPU**: 2+ cores recommended for large constellations

### Performance Tuning

For large debris populations (10,000+ objects):

1. **Enable caching**:
   ```bash
   CACHE_PROPAGATION_RESULTS=true
   CACHE_TTL_SECONDS=60.0
   ```

2. **Limit visualization payload**:
   ```bash
   MAX_DEBRIS_IN_SNAPSHOT=5000
   ```

3. **Adjust prediction granularity** (trade accuracy for speed):
   ```bash
   COARSE_PROPAGATION_STEP_SECONDS=600.0  # 10 min instead of 5
   ```

### Monitoring

Logs are output to stdout in structured format:
```
2026-03-26 12:00:00 | INFO     | app.main             | Server ready on 0.0.0.0:8000
2026-03-26 12:01:00 | WARNING  | avoidance_service    | CONJUNCTION_DETECTED | sat=SAT-12345 | miss=85.2m
```

Monitor critical events:
- `CONJUNCTION_DETECTED` - New conjunction found
- `AVOIDANCE_PLANNED` - Maneuver sequence created
- `MANEUVER_EXECUTED` - Burn executed
- `VERIFICATION_SUCCESS/FAILED` - Post-maneuver check result

### Health Checks

Kubernetes/Docker health probe:
```yaml
livenessProbe:
  httpGet:
    path: /api/health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
```

## API Endpoints

### Core Operations

- `POST /api/simulate/step/auto` - Advance simulation with avoidance
- `GET /api/visualization/snapshot/full` - Full constellation state
- `GET /api/avoidance/status` - Avoidance system status
- `GET /api/avoidance/conjunctions` - Predicted conjunctions
- `GET /api/avoidance/unprotected` - Critical unprotected satellites

### Documentation

Interactive API docs: `http://localhost:8000/docs`
OpenAPI schema: `http://localhost:8000/openapi.json`

## Troubleshooting

### No satellites loaded

**Symptom**: Health check shows 0 satellites
**Solution**: Ensure TLE files are in the correct location and `DATA_DIR` is set properly

Check logs:
```bash
docker logs aether-backend | grep "Loading satellite"
```

### Container exits immediately

**Symptom**: Container stops right after starting
**Solution**: Check for missing TLE files or invalid configuration

```bash
docker logs aether-backend
```

### High memory usage

**Symptom**: Container uses excessive RAM
**Solution**: Reduce debris count or enable sampling

```bash
MAX_DEBRIS_IN_SNAPSHOT=5000
```

## Support

For issues and questions, see the project repository.
