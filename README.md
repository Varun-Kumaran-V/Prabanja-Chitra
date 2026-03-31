# Aether Constellation Manager

**Autonomous Satellite Collision Avoidance System**

A real-time mission control platform for managing satellite constellations with AI-powered collision avoidance. The system predicts orbital conjunctions, scores threats, plans evasion maneuvers, and executes autonomous collision avoidance—all while optimizing fuel consumption across the fleet.

![Tech Stack](https://img.shields.io/badge/React-18.2-61DAFB?logo=react)
![Tech Stack](https://img.shields.io/badge/FastAPI-Python-009688?logo=fastapi)
![Tech Stack](https://img.shields.io/badge/Three.js-3D-black?logo=three.js)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🚀 Features

### Mission Control Dashboard
- **Real-time threat monitoring** - Active conjunctions with severity classification
- **Autonomous decision intelligence** - AI-scored threats with fuel-aware scheduling
- **Maneuver timeline** - Planned evasion and recovery burns
- **Fleet fuel status** - Per-satellite fuel monitoring with critical alerts
- **Event log** - Complete audit trail of all system actions

### Autonomous Collision Avoidance
- **24-hour conjunction prediction** using SGP4 orbital propagation
- **Multi-factor threat scoring** (50% miss distance + 35% urgency + 15% velocity)
- **Fuel-aware decision making** - Skip low-priority threats when fuel is critical
- **Evasion + Recovery burn sequences** - Return satellite to nominal orbit after avoidance
- **Ground station LOS constraint** - Maneuvers require uplink visibility
- **Graceful degradation** - Automatic mode switching under high load

### 3D Visualization
- **Interactive orbit viewer** - Three.js-powered constellation display
- **Real-time position updates** - See satellites and debris move in orbit
- **Conjunction highlighting** - Visualize close approaches

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React 18)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │   Home   │ │ Mission  │ │ Metrics  │ │Comparison│ │   3D     │ │
│  │   Page   │ │ Control  │ │   Page   │ │   Page   │ │ Viewer   │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ │
│       └────────────┴────────────┴────────────┴────────────┘       │
│                              │ API Service Layer                   │
└──────────────────────────────┼─────────────────────────────────────┘
                               │ HTTP/REST
┌──────────────────────────────┼─────────────────────────────────────┐
│                        BACKEND (FastAPI)                           │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                      API Routes (40+)                        │ │
│  │  /simulate  /avoidance  /decisions  /history  /visualization │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    Services Layer                            │ │
│  │ SimulationService  AvoidanceService  DecisionService  etc.   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    Core Algorithms                           │ │
│  │  OrbitPropagator   ConjunctionDetector   ManeuverPlanner    │ │
│  │  (SGP4 + J2)       (KD-tree + Newton)    (RTN burns)        │ │
│  └──────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

### Frontend
- **React 18** - UI framework with hooks
- **React Router 7** - Page navigation
- **Three.js** + React Three Fiber - 3D orbital visualization
- **Tailwind CSS 4** - Utility-first styling
- **Vite 5** - Build tool

### Backend
- **FastAPI** - High-performance async API
- **Python 3.10+** - Core language
- **SGP4** - Orbital propagation from TLE data
- **SciPy** - KD-tree spatial indexing
- **Pydantic** - Data validation

---

## 📁 Project Structure

```
aether-constellation-manager/
├── README.md                 # This file
├── package.json              # Frontend dependencies
├── vite.config.js            # Frontend build config
├── index.html                # App entry point
├── start-backend.sh          # Unix backend launcher
├── start-backend.bat         # Windows backend launcher
│
├── docs/
│   ├── ARCHITECTURE.md       # Detailed system design
│   └── SETUP.md              # Installation guide
│
├── src/                      # Frontend source
│   ├── App.jsx               # Router configuration
│   ├── config.js             # API configuration
│   ├── components/           # Reusable components
│   │   ├── Dashboard.jsx     # 3D visualization dashboard
│   │   └── OrbitViewer.jsx   # Three.js orbit renderer
│   ├── pages/                # Page components
│   │   ├── Home.jsx          # Landing page
│   │   ├── MissionControl.jsx # Main dashboard
│   │   ├── Metrics.jsx       # Analytics page
│   │   ├── Comparison.jsx    # Manual vs Autonomous
│   │   └── Architecture.jsx  # System architecture
│   └── services/
│       └── api.js            # API client (25+ endpoints)
│
└── backend/                  # Backend source
    ├── README.md             # Backend documentation
    ├── requirements.txt      # Python dependencies
    ├── run.py                # Server entry point
    ├── data/                 # TLE orbital data
    │   ├── active.txt        # Satellite catalog
    │   └── debris_*.txt      # Debris catalogs
    └── app/
        ├── main.py           # FastAPI app setup
        ├── config.py         # Configuration
        ├── api/              # Route handlers
        ├── core/             # Core algorithms
        ├── models/           # Data models
        ├── services/         # Business logic
        └── utils/            # Utilities
```

---

## ⚡ Quick Start

### Prerequisites
- **Node.js 18+** and npm
- **Python 3.10+** and pip

### 1. Clone & Install

```bash
# Clone repository
git clone https://github.com/yourusername/aether-constellation-manager.git
cd aether-constellation-manager

# Install frontend dependencies
npm install

# Install backend dependencies
cd backend
pip install -r requirements.txt
cd ..
```

### 2. Start Backend

**Windows:**
```bash
start-backend.bat
```

**Unix/Mac:**
```bash
./start-backend.sh
```

Or manually:
```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Start Frontend

```bash
npm run dev
```

### 4. Open Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## 🔌 API Overview

| Endpoint Group | Description |
|----------------|-------------|
| `POST /api/simulate/step` | Advance simulation with avoidance |
| `GET /api/avoidance/status` | Current avoidance system state |
| `GET /api/avoidance/conjunctions` | Active predicted conjunctions |
| `GET /api/decisions` | Decision records with explanations |
| `GET /api/decisions/fuel/status` | Fleet fuel status |
| `GET /api/history/events` | Event audit log |
| `GET /api/visualization/snapshot` | 3D visualization data |
| `GET /api/system/summary` | System overview |

See `/docs/ARCHITECTURE.md` for complete API documentation.

---

## 🧠 Core Algorithms

### Conjunction Detection
1. **Spatial Filtering** - KD-tree queries find debris within 50km of each satellite
2. **Temporal Filtering** - 5-minute propagation steps find local minima
3. **TCA Refinement** - Newton-Raphson iteration finds exact closest approach

### Threat Scoring
```
Composite Score = 0.50 × miss_distance_score
                + 0.35 × time_urgency_score  
                + 0.15 × velocity_score

Severity: CRITICAL (≥80), HIGH (≥60), MEDIUM (≥40), LOW (<40)
```

### Decision Intelligence
- **Fuel-aware**: Skip low-priority threats when fuel is critical
- **Mode-aware**: Graceful degradation under high load
- **Verification**: Post-maneuver validation with re-planning

---

## 📊 Data Sources

The system uses real Two-Line Element (TLE) data:

| File | Objects | Source |
|------|---------|--------|
| `active.txt` | ~800 satellites | Space-Track catalog |
| `debris_fengyun.txt` | ~1,300 debris | Fengyun-1C ASAT test (2007) |
| `debris_cosmos.txt` | ~200 debris | Cosmos-Iridium collision (2009) |
| `debris_iridium.txt` | ~50 debris | Iridium 33 debris |

---

## 🔧 Configuration

### Frontend (src/config.js)
```javascript
// Set via environment variable or .env file
VITE_API_BASE=http://localhost:8000
```

### Backend (backend/.env)
```bash
DATA_DIR=./data
SATELLITE_TLE_FILE=active.txt
DEBRIS_TLE_FILES=debris_iridium.txt,debris_cosmos.txt,debris_fengyun.txt
```

---

## 📄 License

MIT License - See [LICENSE](LICENSE) for details.

---

## 👨‍💻 Author

**Varun Kumaran** - 2026

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request