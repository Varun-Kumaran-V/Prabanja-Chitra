# Setup Guide

Complete installation and setup instructions for Aether Constellation Manager.

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Node.js | 18+ | Frontend runtime |
| npm | 9+ | Package manager |
| Python | 3.10+ | Backend runtime |
| pip | 21+ | Python packages |

### Verify Installation

```bash
# Check Node.js
node --version  # Should show v18.x.x or higher

# Check npm
npm --version   # Should show 9.x.x or higher

# Check Python
python --version  # Should show Python 3.10.x or higher

# Check pip
pip --version
```

---

## Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/aether-constellation-manager.git
cd aether-constellation-manager
```

### Step 2: Install Frontend Dependencies

```bash
npm install
```

This installs:
- React 18
- React Router 7
- Three.js + React Three Fiber
- Tailwind CSS 4
- Vite 5

### Step 3: Install Backend Dependencies

```bash
cd backend
pip install -r requirements.txt
cd ..
```

This installs:
- FastAPI
- Uvicorn
- SGP4
- SciPy
- Pydantic

### Step 4: Verify TLE Data

Ensure data files exist in `backend/data/`:

```bash
ls backend/data/
# Should show:
# active.txt
# debris_cosmos.txt
# debris_fengyun.txt
# debris_iridium.txt
```

---

## Running the Application

### Start Backend Server

**Windows:**
```bash
start-backend.bat
```

**Unix/Mac:**
```bash
chmod +x start-backend.sh
./start-backend.sh
```

**Manual (any platform):**
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
============================================================
AETHER CONSTELLATION MANAGER
Autonomous Collision Avoidance System
============================================================
Loading satellite TLE dataset from: .../backend/data/active.txt
✓ Loaded 800 satellites
Loading debris TLE datasets from 3 file(s)...
✓ Total: 1550 debris objects loaded
============================================================
Server ready on 0.0.0.0:8000
============================================================
```

### Start Frontend Development Server

```bash
npm run dev
```

Expected output:
```
VITE v5.0.0  ready in 500 ms

➜  Local:   http://localhost:3000/
➜  Network: http://192.168.x.x:3000/
```

### Access the Application

| URL | Description |
|-----|-------------|
| http://localhost:3000 | Frontend application |
| http://localhost:8000 | Backend API |
| http://localhost:8000/docs | API documentation (Swagger) |

---

## Environment Configuration

### Backend Configuration

Create `backend/.env` to override defaults:

```bash
# Data directory (relative to backend/ or absolute)
DATA_DIR=./data

# TLE file names
SATELLITE_TLE_FILE=active.txt
DEBRIS_TLE_FILES=debris_iridium.txt,debris_cosmos.txt,debris_fengyun.txt

# Server settings
HOST=0.0.0.0
PORT=8000

# Avoidance parameters (optional)
PREDICTION_HORIZON_SECONDS=86400
MISS_DISTANCE_ALERT_THRESHOLD_M=100
MAX_DELTA_V_MS=15
```

### Frontend Configuration

Create `.env` in project root:

```bash
# Backend API URL
VITE_API_BASE=http://localhost:8000
```

For production:
```bash
VITE_API_BASE=https://api.yourserver.com
```

---

## Building for Production

### Build Frontend

```bash
npm run build
```

Output goes to `dist/` folder.

### Preview Production Build

```bash
npm run preview
```

### Run Backend in Production

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## Using Virtual Environment (Recommended)

### Create Virtual Environment

```bash
# Create venv
python -m venv .venv

# Activate - Windows
.venv\Scripts\activate

# Activate - Unix/Mac
source .venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt
```

### Deactivate

```bash
deactivate
```

---

## Troubleshooting

### Common Issues

#### Backend won't start - "Module not found"

```bash
# Ensure you're in backend directory
cd backend

# Reinstall dependencies
pip install -r requirements.txt
```

#### Frontend shows "API Error" or blank data

1. Ensure backend is running on port 8000
2. Check frontend config:
   ```javascript
   // src/config.js should have:
   export const API_BASE = "http://127.0.0.1:8000";
   ```
3. Check browser console for CORS errors

#### "TLE file not found" warnings

Ensure data files are in `backend/data/`:
```bash
# From project root
ls backend/data/
```

If missing, the TLE files may not have been committed. Check git status.

#### Port already in use

```bash
# Find process using port
# Windows
netstat -ano | findstr :8000

# Unix/Mac
lsof -i :8000

# Kill process
# Windows
taskkill /PID <pid> /F

# Unix/Mac
kill -9 <pid>
```

#### Slow conjunction detection

This is expected for large debris populations. First run may take 5-10 seconds. Subsequent runs use caching (~3-4 seconds).

---

## Development Tips

### Hot Reload

Both frontend (Vite) and backend (Uvicorn) support hot reload:
- Frontend: Edit any `.jsx`/`.css` file and browser updates automatically
- Backend: Edit any `.py` file and server restarts automatically

### API Testing

Use the Swagger docs at http://localhost:8000/docs to:
- Test individual endpoints
- See request/response schemas
- Try the simulation step

### Useful Commands

```bash
# Run linter (if configured)
npm run lint

# Format code (if prettier configured)
npm run format

# Run tests (if configured)
npm test
```

---

## Docker Setup (Optional)

### Using Docker Compose

```yaml
# docker-compose.yml
version: '3.8'
services:
  frontend:
    build: .
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - VITE_API_BASE=http://backend:8000

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/data:/app/data
```

```bash
docker-compose up --build
```

---

## Next Steps

After setup:

1. **Explore Mission Control** - Main dashboard at `/mission-control`
2. **Run Simulation** - Click "Run Simulation Step" to see avoidance in action
3. **View Metrics** - Check `/metrics` for system analytics
4. **Read Architecture** - See `docs/ARCHITECTURE.md` for technical details
