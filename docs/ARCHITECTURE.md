# Architecture Documentation

## System Overview

Aether Constellation Manager is a real-time autonomous satellite collision avoidance system. It monitors a satellite constellation, predicts potential collisions with debris, and automatically plans and executes evasion maneuvers.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND LAYER                                  │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │    Home     │  │   Mission   │  │   Metrics   │  │  Dashboard  │        │
│  │    Page     │  │   Control   │  │    Page     │  │  (3D View)  │        │
│  │             │  │  Dashboard  │  │             │  │             │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │                │
│         └────────────────┴────────────────┴────────────────┘                │
│                                   │                                         │
│                          ┌───────┴───────┐                                 │
│                          │  api.js       │  API Service Layer              │
│                          │  (25+ funcs)  │                                 │
│                          └───────┬───────┘                                 │
└──────────────────────────────────┼──────────────────────────────────────────┘
                                   │ REST/HTTP
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND LAYER                                    │
│                                                                               │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                         API ROUTES (FastAPI)                           │  │
│  │  /simulate    /avoidance    /decisions    /history    /visualization  │  │
│  │  /system      /telemetry                                               │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                   │                                          │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                         SERVICES LAYER                                 │  │
│  │                                                                        │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │  │
│  │  │ SimulationService│  │ AvoidanceService │  │ DecisionService  │    │  │
│  │  │ - step()         │  │ - run_cycle()    │  │ - score_threat() │    │  │
│  │  │ - reset()        │  │ - plan_avoidance │  │ - prioritize()   │    │  │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘    │  │
│  │                                                                        │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │  │
│  │  │ ExecutionService │  │ TelemetryService │  │ EventLogService  │    │  │
│  │  │ - execute_burn() │  │ - store_state()  │  │ - log()          │    │  │
│  │  │ - verify()       │  │ - get_stats()    │  │ - query()        │    │  │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘    │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                   │                                          │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                         CORE ALGORITHMS                                │  │
│  │                                                                        │  │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐    │  │
│  │  │ OrbitPropagator  │  │ConjunctionDetect │  │ ManeuverPlanner  │    │  │
│  │  │ - propagate_sgp4 │  │ - predict()      │  │ - plan_evasion() │    │  │
│  │  │ - propagate_j2   │  │ - find_tca()     │  │ - plan_recovery()│    │  │
│  │  └──────────────────┘  └──────────────────┘  └──────────────────┘    │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
│                                   │                                          │
│  ┌────────────────────────────────────────────────────────────────────────┐  │
│  │                         DATA MODELS                                    │  │
│  │  Satellite | Debris | Conjunction | Maneuver | ThreatScore | Decision │  │
│  └────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### Simulation Step Flow

```
┌───────────┐     POST /simulate/step      ┌────────────────┐
│  Frontend │ ───────────────────────────► │ SimulationSvc  │
│   (5s)    │                              │                │
└───────────┘                              └───────┬────────┘
                                                   │
                    ┌──────────────────────────────┘
                    ▼
            ┌───────────────┐
            │ 1. Propagate  │  Advance all satellite/debris
            │    All Orbits │  positions by dt seconds
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │ 2. Predict    │  Scan for close approaches
            │  Conjunctions │  in next 24 hours
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │ 3. Score &    │  Prioritize by miss distance,
            │   Prioritize  │  urgency, and velocity
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │ 4. Make       │  Check fuel, mode, capacity
            │   Decisions   │  → schedule, skip, or defer
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │ 5. Plan       │  Compute evasion + recovery
            │   Maneuvers   │  burn parameters
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │ 6. Execute    │  Apply delta-v, update state,
            │   Burns       │  deplete fuel
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
            │ 7. Verify     │  Check if miss distance improved
            │   & Cleanup   │  Re-plan if needed
            └───────┬───────┘
                    │
                    ▼
            ┌───────────────┐
          ◄─│ Return Status │
            └───────────────┘
```

---

## Core Algorithms

### 1. Conjunction Detection

The system uses a 3-phase algorithm optimized for large debris populations:

```
Phase 1: Spatial Filtering (KD-Tree)
─────────────────────────────────────
For each satellite:
  • Query KD-tree of debris positions
  • Radius = 50 km (SPATIAL_SCREENING_THRESHOLD)
  • Returns candidate pairs in O(log N)

Phase 2: Temporal Filtering (Coarse Scan)
─────────────────────────────────────────
For each candidate pair:
  • Propagate forward in 5-minute steps
  • Detect local distance minima
  • Filter pairs with minimum > 25 km

Phase 3: TCA Refinement (Newton-Raphson)
────────────────────────────────────────
For pairs passing temporal filter:
  • Newton iteration to find exact TCA
  • Convergence: Δt < 0.1 seconds
  • Computes: tca, miss_distance, relative_velocity
  
  Algorithm:
  ┌─────────────────────────────────────────────────────┐
  │ t_guess = coarse_minimum_time                       │
  │ for iter in 1..20:                                  │
  │   sat_pos, sat_vel = propagate(satellite, t_guess) │
  │   deb_pos, deb_vel = propagate(debris, t_guess)    │
  │   rel_pos = sat_pos - deb_pos                      │
  │   rel_vel = sat_vel - deb_vel                      │
  │   range_rate = (rel_pos · rel_vel) / |rel_pos|     │
  │                                                     │
  │   if |range_rate| < 1e-9: break  # Converged       │
  │                                                     │
  │   # Numerical derivative                            │
  │   range_rate_h = compute(t_guess + 1s)             │
  │   f_prime = (range_rate_h - range_rate) / 1.0      │
  │                                                     │
  │   delta_t = -range_rate / f_prime                  │
  │   t_guess = clamp(t_guess + delta_t, bounds)       │
  └─────────────────────────────────────────────────────┘
```

### 2. Threat Scoring

Multi-factor composite scoring prioritizes threats for handling:

```
┌─────────────────────────────────────────────────────────┐
│                    THREAT SCORING                       │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Miss Distance Score (50% weight)                       │
│  ─────────────────────────────────                      │
│  < 100m  → 90-100 (exponential scale)                  │
│  < 500m  → 60-80                                        │
│  < 1km   → 40-60                                        │
│  < 10km  → 10-40                                        │
│  > 10km  → 0-10                                         │
│                                                         │
│  Time Urgency Score (35% weight)                        │
│  ──────────────────────────────                         │
│  < 30min → 90-100                                       │
│  < 2hr   → 60-80                                        │
│  < 6hr   → 40-60                                        │
│  < 24hr  → 10-40                                        │
│  > 24hr  → 0-10                                         │
│                                                         │
│  Velocity Score (15% weight)                            │
│  ─────────────────────────────                          │
│  < 1km/s  → 0-30  (slow approach)                      │
│  1-5km/s  → 30-60                                       │
│  5-10km/s → 60-85 (typical)                            │
│  > 10km/s → 85-100 (hypervelocity)                     │
│                                                         │
│  ═══════════════════════════════════════════           │
│  Composite = 0.50×miss + 0.35×urgency + 0.15×velocity  │
│                                                         │
│  Severity Classification:                               │
│  • CRITICAL: composite ≥ 80                            │
│  • HIGH:     composite ≥ 60                            │
│  • MEDIUM:   composite ≥ 40                            │
│  • LOW:      composite < 40                            │
└─────────────────────────────────────────────────────────┘
```

### 3. Maneuver Planning

Evasion maneuvers use RTN (Radial-Transverse-Normal) frame burns:

```
┌─────────────────────────────────────────────────────────┐
│               EVASION BURN CALCULATION                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Compute required miss distance increase:            │
│     Δd = target_miss (500m) - current_miss             │
│                                                         │
│  2. Calculate delta-v magnitude:                        │
│     Δv = Δd / (effectiveness × time_to_tca)            │
│         × safety_margin (1.2)                           │
│     Δv = clamp(Δv, 0, MAX_DELTA_V)                     │
│                                                         │
│  3. Determine burn direction:                           │
│     ┌────────────────────────────────────┐             │
│     │ Compute RTN frame at satellite:    │             │
│     │   R = radial (outward)             │             │
│     │   T = transverse (prograde)        │             │
│     │   N = normal (out of plane)        │             │
│     │                                    │             │
│     │ Project threat direction:          │             │
│     │   threat = (debris - sat) / dist   │             │
│     │                                    │             │
│     │ if |threat · N| > 0.5:             │             │
│     │   → NORMAL burn (most effective)   │             │
│     │ else if debris ahead:              │             │
│     │   → RETROGRADE (slow down)         │             │
│     │ else:                              │             │
│     │   → PROGRADE (speed up)            │             │
│     └────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│               RECOVERY BURN CALCULATION                 │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. Compute orbit deviation from nominal:               │
│     Δa = semi-major axis error                         │
│     Δv_RTN = velocity error components                 │
│                                                         │
│  2. Correct largest deviation:                          │
│     if |Δv_transverse| largest:                        │
│       Δv_transverse > 0 → RETROGRADE                   │
│       Δv_transverse < 0 → PROGRADE                     │
│                                                         │
│  3. Schedule 1 hour after TCA                           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 4. Fuel Management

Uses Tsiolkovsky rocket equation for accurate fuel depletion:

```
Fuel consumption for delta-v burn:

  Δm = m₀ × (1 - e^(-Δv/vₑ))

where:
  m₀ = total mass (dry + fuel)
  vₑ = exhaust velocity = Isp × g₀
  g₀ = 9.80665 m/s²

Default parameters:
  Isp = 300 seconds (hydrazine)
  vₑ = 2942 m/s
  Initial fuel = 50 kg
  Dry mass = 500 kg
```

---

## Operating Modes

The system automatically adjusts behavior based on load:

```
┌─────────────────────────────────────────────────────────┐
│                    OPERATING MODES                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  NOMINAL MODE (< 10 pending maneuvers)                 │
│  ─────────────────────────────────────                  │
│  • Process all threat severities                        │
│  • Full capability                                      │
│                                                         │
│  DEGRADED MODE (10-20 pending maneuvers)               │
│  ─────────────────────────────────────                  │
│  • Skip LOW severity threats                           │
│  • Skip LOW/MEDIUM if fuel is LOW                      │
│  • Log mode transition                                  │
│                                                         │
│  EMERGENCY MODE (> 20 pending maneuvers)               │
│  ─────────────────────────────────────                  │
│  • Process only CRITICAL threats                       │
│  • Maximum conservation mode                            │
│  • Alert operators                                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## API Reference

### Simulation Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/simulate/step` | Advance simulation with avoidance cycle |
| GET | `/api/simulate/status` | Current simulation state |
| POST | `/api/simulate/reset` | Reset to initial state |

### Avoidance Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/avoidance/status` | Avoidance system status |
| GET | `/api/avoidance/conjunctions` | Active predicted conjunctions |
| GET | `/api/avoidance/maneuvers/pending` | Pending maneuver queue |
| GET | `/api/avoidance/sequences` | Planned evasion+recovery sequences |
| GET | `/api/avoidance/unprotected` | Satellites without LOS for critical threats |

### Decision Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/decisions` | Recent decision records |
| GET | `/api/decisions/statistics` | Decision statistics |
| GET | `/api/decisions/threats/scores` | Threat scores for all conjunctions |
| GET | `/api/decisions/fuel/status` | Fleet fuel status |
| GET | `/api/decisions/explain/{id}` | Explanation for specific decision |

### History Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/history/events` | Query event log |
| GET | `/api/history/statistics` | Summary statistics |
| GET | `/api/history/maneuvers` | Executed maneuver history |

### System Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/system/summary` | High-level system status |
| GET | `/api/system/risk` | Risk overview with top threats |
| GET | `/api/health` | Service health check |

---

## Frontend Components

### Page Structure

```
App.jsx (Router)
├── Home.jsx
│   └── Landing page with system overview
│
├── MissionControl.jsx
│   ├── StatusStrip - Key metrics
│   ├── ThreatList - Active conjunctions
│   ├── ManeuverTimeline - Planned burns
│   ├── FuelStatusPanel - Fleet fuel
│   ├── DecisionLogPanel - AI decisions
│   └── EventLog - System events
│
├── Metrics.jsx
│   ├── System overview cards
│   ├── Decision analytics
│   └── Historical summary
│
├── Comparison.jsx
│   └── Manual vs Autonomous comparison
│
├── Architecture.jsx
│   └── System architecture diagram
│
└── Dashboard.jsx
    └── 3D orbit visualization (Three.js)
```

### Data Flow

```
Component Mount
      │
      ▼
  useEffect()
      │
      ▼
fetchXxxData() ───► api.js ───► Backend
      │                           │
      │    ◄──────────────────────┘
      ▼
 setData(response)
      │
      ▼
  Render UI
      │
      ▼
setInterval() ──► Poll every 5-10 seconds
```

---

## Configuration Reference

### Backend Configuration (config.py)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `PREDICTION_HORIZON_SECONDS` | 86400 | Lookahead window (24h) |
| `MISS_DISTANCE_ALERT_THRESHOLD_M` | 100 | Avoidance trigger |
| `SPATIAL_SCREENING_THRESHOLD_KM` | 50 | KD-tree radius |
| `MAX_DELTA_V_MS` | 15 | Max burn per maneuver |
| `COOLDOWN_SECONDS` | 600 | Min time between burns |
| `FUEL_CRITICAL_THRESHOLD` | 0.10 | Critical fuel (10%) |
| `FUEL_LOW_THRESHOLD` | 0.30 | Low fuel (30%) |
| `MAX_CONCURRENT_MANEUVERS` | 5 | Parallel maneuver limit |

### Frontend Configuration (config.js)

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE` | `http://127.0.0.1:8000` | Backend URL |

Set via environment: `VITE_API_BASE=https://api.example.com`
