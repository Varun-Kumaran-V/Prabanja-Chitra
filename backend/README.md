# Aether Constellation Manager - Backend

**Autonomous satellite collision avoidance system backend**

FastAPI-based service providing orbit propagation, conjunction detection, maneuver planning, and decision intelligence for autonomous satellite constellation management.

---

## Tech Stack

- **Framework:** FastAPI (async Python web framework)
- **Runtime:** Python 3.10+
- **Orbital Mechanics:** SGP4 (TLE propagation)
- **Spatial Indexing:** SciPy KD-Tree
- **Validation:** Pydantic

---

## Quick Start

```bash
cd backend

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Start server
python -m uvicorn app.main:app --reload --port 8000
```

API available at: http://localhost:8000
Interactive docs: http://localhost:8000/docs

---

## Project Structure

```
backend/
├── run.py                # Development server entry
├── requirements.txt      # Python dependencies
├── data/                 # TLE orbital data files
│   ├── active.txt        # Satellite catalog (~800)
│   ├── debris_cosmos.txt # Cosmos-2251 debris
│   ├── debris_fengyun.txt# Fengyun-1C debris
│   └── debris_iridium.txt# Iridium-33 debris
│
└── app/
    ├── main.py           # FastAPI application setup
    ├── config.py         # Configuration (Pydantic settings)
    │
    ├── api/              # Route handlers
    │   ├── simulation.py # POST /simulate/step
    │   ├── avoidance.py  # GET /avoidance/...
    │   ├── decisions.py  # GET /decisions/...
    │   ├── history.py    # GET /history/...
    │   ├── system.py     # GET /system/...
    │   ├── telemetry.py  # POST /telemetry
    │   └── visualization.py
    │
    ├── core/             # Core algorithms
    │   ├── orbit_propagator.py    # SGP4 + J2 propagation
    │   ├── conjunction_detector.py # KD-tree + Newton TCA
    │   ├── maneuver_planner.py    # Evasion + recovery burns
    │   ├── maneuver_executor.py   # Burn execution
    │   └── ground_station.py      # LOS calculations
    │
    ├── services/         # Business logic
    │   ├── simulation_service.py  # Main simulation loop
    │   ├── avoidance_service.py   # Closed-loop avoidance
    │   ├── decision_service.py    # Threat scoring
    │   ├── execution_service.py   # Maneuver execution
    │   ├── orbit_service.py       # TLE loading
    │   ├── telemetry_service.py   # State management
    │   └── event_log_service.py   # Audit logging
    │
    ├── models/           # Data models
    │   ├── satellite.py
    │   ├── debris.py
    │   ├── conjunction.py
    │   ├── maneuver.py
    │   ├── decision.py
    │   └── event_log.py
    │
    └── utils/
        └── tle_parser.py # TLE file parsing
```

---

## Core Algorithms

### Orbit Propagation

**File:** `app/core/orbit_propagator.py`

Uses SGP4 (Simplified General Perturbations 4) for TLE-based propagation:

```python
# Propagate satellite forward by dt seconds
orbit_propagator.propagate_sgp4(tle_line1, tle_line2, dt_seconds)
```

Includes J2 perturbation (Earth oblateness) and atmospheric drag effects. Typical accuracy: ±2km in LEO after 24 hours.

### Conjunction Detection

**File:** `app/core/conjunction_detector.py`

Three-phase algorithm:

1. **Spatial Filtering (KD-Tree)**
   - Build KD-tree of debris positions
   - Query satellites with 50km radius
   - Complexity: O(log N)

2. **Temporal Filtering**
   - Propagate candidates in 5-minute steps
   - Detect local distance minima
   - Filter pairs > 25km

3. **TCA Refinement (Newton-Raphson)**
   - Find exact time where range_rate = 0
   - Convergence: Δt < 0.1 seconds
   - Returns: (tca, miss_distance, relative_velocity)

### Decision Intelligence

**File:** `app/services/decision_service.py`

Threat scoring formula:
```
composite = 0.50 × miss_distance_score
          + 0.35 × time_urgency_score
          + 0.15 × velocity_score
```

Severity classification:
- CRITICAL: ≥ 80
- HIGH: ≥ 60
- MEDIUM: ≥ 40
- LOW: < 40

### Maneuver Planning

**File:** `app/core/maneuver_planner.py`

Computes RTN (Radial-Transverse-Normal) frame burns:

1. **Evasion burn:** Increase miss distance to 500m safety margin
2. **Recovery burn:** Return to nominal orbit 1 hour after TCA

Direction selection based on threat geometry:
- Normal burn (out-of-plane) if threat is in-plane
- Prograde/Retrograde if threat is ahead/behind

---

## Simulation Flow

Each `POST /api/simulate/step` triggers:

```
1. Propagate all orbits (satellites + debris)
2. Handle verification failures (re-planning)
3. Predict conjunctions (24-hour lookahead)
4. Score and prioritize threats
5. Make fuel-aware decisions
6. Plan avoidance sequences
7. Execute pending maneuvers
8. Verify maneuver effectiveness
9. Clear passed conjunctions
10. Return status
```

---

## API Endpoints

### Simulation

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/simulate/step` | POST | Advance simulation with avoidance |
| `/api/simulate/status` | GET | Current simulation state |
| `/api/simulate/reset` | POST | Reset to initial state |

### Avoidance

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/avoidance/status` | GET | Avoidance system status |
| `/api/avoidance/conjunctions` | GET | Active conjunctions |
| `/api/avoidance/maneuvers/pending` | GET | Pending maneuver queue |
| `/api/avoidance/sequences` | GET | Planned maneuver sequences |
| `/api/avoidance/unprotected` | GET | Satellites without LOS |

### Decisions

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/decisions` | GET | Recent decisions |
| `/api/decisions/statistics` | GET | Decision statistics |
| `/api/decisions/fuel/status` | GET | Fleet fuel status |
| `/api/decisions/explain/{id}` | GET | Decision explanation |

### History

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/history/events` | GET | Event log |
| `/api/history/statistics` | GET | Summary statistics |

---

## Configuration

Key parameters in `app/config.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `PREDICTION_HORIZON_SECONDS` | 86400 | Lookahead (24h) |
| `MISS_DISTANCE_ALERT_THRESHOLD_M` | 100 | Avoidance trigger |
| `MAX_DELTA_V_MS` | 15 | Max burn Δv |
| `COOLDOWN_SECONDS` | 600 | Min between burns |
| `FUEL_CRITICAL_THRESHOLD` | 0.10 | Critical fuel % |
| `MAX_CONCURRENT_MANEUVERS` | 5 | Parallel limit |

Override via environment variables or `.env` file.

---

## Data Files

TLE (Two-Line Element) orbital data in `data/`:

| File | Objects | Source |
|------|---------|--------|
| `active.txt` | ~800 satellites | Space-Track |
| `debris_fengyun.txt` | ~1,300 debris | Fengyun-1C ASAT (2007) |
| `debris_cosmos.txt` | ~200 debris | Cosmos-Iridium (2009) |
| `debris_iridium.txt` | ~50 debris | Iridium 33 |

---

## Docker

```bash
# Build
docker build -t aether-backend .

# Run
docker run -p 8000:8000 -v $(pwd)/data:/app/data aether-backend
```

---

## Testing

```bash
# Run tests (if pytest configured)
pytest

# Test health endpoint
curl http://localhost:8000/api/health
```
