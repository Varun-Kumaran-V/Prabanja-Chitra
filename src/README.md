# Aether Constellation Manager - Frontend

**React-based mission control dashboard for autonomous satellite collision avoidance**

Real-time visualization and monitoring interface for the Aether autonomous constellation management system.

---

## Tech Stack

- **Framework:** React 18 with Hooks
- **Routing:** React Router 7
- **3D Visualization:** Three.js + React Three Fiber
- **Styling:** Tailwind CSS 4
- **Build Tool:** Vite 5

---

## Quick Start

```bash
# From project root
npm install
npm run dev
```

Open http://localhost:3000

---

## Project Structure

```
src/
├── main.jsx              # Application entry point
├── App.jsx               # Router configuration
├── config.js             # API base URL configuration
├── index.css             # Global styles + Tailwind
│
├── components/           # Reusable components
│   ├── Dashboard.jsx     # 3D visualization with polling
│   └── OrbitViewer.jsx   # Three.js orbit renderer
│
├── pages/                # Page components
│   ├── Home.jsx          # Landing page
│   ├── MissionControl.jsx# Main dashboard
│   ├── Metrics.jsx       # Analytics dashboard
│   ├── Comparison.jsx    # Manual vs Autonomous
│   └── Architecture.jsx  # System architecture
│
└── services/
    └── api.js            # API client (25+ endpoints)
```

---

## Pages

### Home (`/home`)
Landing page showcasing system capabilities:
- Hero section with live status
- Core operational vectors (Predict/Score/Execute)
- Key capabilities grid
- Proof metrics

### Mission Control (`/mission-control`) ⭐ Main Dashboard
Real-time mission operations:
- **Status Strip:** Active satellites, debris, threats, fuel
- **Threat List:** Active conjunctions with severity colors
- **Maneuver Timeline:** Planned evasion + recovery burns
- **Fuel Status:** Per-satellite fuel bars
- **Decision Log:** AI decisions with explanations
- **Event Log:** System event history

### Metrics (`/metrics`)
Performance analytics:
- System overview (satellites, debris, fuel)
- Decision statistics (scheduled/deferred/skipped)
- Historical summary

### Comparison (`/comparison`)
Manual vs Autonomous comparison:
- 6 comparison metrics
- Side-by-side analysis
- "The Verdict" summary

### Architecture (`/architecture`)
System architecture visualization:
- Frontend/Backend/Core layers
- Data flow diagram
- Tech stack

### Dashboard (`/dashboard`)
3D orbit visualization:
- Three.js rendered scene
- Interactive orbit controls
- Real-time satellite/debris positions

---

## Components

### Dashboard.jsx
3D visualization with real-time updates:
- Uses `@react-three/fiber` for React-Three.js integration
- Polls `/api/visualization/snapshot` every 2 seconds
- Runs simulation step on each update

### OrbitViewer.jsx
Standalone Three.js scene component:
- Earth sphere with blue material
- Satellites as green points
- Debris as gray points
- Interactive orbit controls
- Stats overlay

---

## API Service (api.js)

Centralized API client with 25+ endpoint functions:

### System Endpoints
```javascript
fetchSystemHealth()     // GET /api/health
fetchSystemSummary()    // GET /api/system/summary
fetchSystemRisk()       // GET /api/system/risk
```

### Avoidance Endpoints
```javascript
fetchAvoidanceStatus()      // GET /api/avoidance/status
fetchConjunctions()         // GET /api/avoidance/conjunctions
fetchPendingManeuvers()     // GET /api/avoidance/maneuvers/pending
fetchAvoidanceSequences()   // GET /api/avoidance/sequences
fetchUnprotectedSatellites()// GET /api/avoidance/unprotected
```

### Decision Endpoints
```javascript
fetchDecisions()            // GET /api/decisions
fetchDecisionStats()        // GET /api/decisions/statistics
fetchDecisionExplanation(id)// GET /api/decisions/explain/{id}
fetchFuelStatus()           // GET /api/decisions/fuel/status
```

### Simulation Endpoints
```javascript
runSimulationStep(dt)       // POST /api/simulate/step
fetchSimulationStatus()     // GET /api/simulate/status
resetSimulation()           // POST /api/simulate/reset
```

### Aggregated Fetchers
```javascript
fetchMissionControlData()   // Fetches 8 endpoints in parallel
fetchMetricsPageData()      // Fetches 4 endpoints in parallel
fetchHomePageData()         // Fetches 4 endpoints in parallel
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────┐
│                     Page Component                       │
│                                                          │
│  ┌─────────────────┐    ┌─────────────────────────────┐ │
│  │  useState()     │    │  useEffect()                │ │
│  │  - data         │◄───│  - Initial fetch            │ │
│  │  - loading      │    │  - setInterval (5-10s)      │ │
│  │  - error        │    │  - cleanup on unmount       │ │
│  └─────────────────┘    └─────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│                    api.js Service                        │
│                                                          │
│  fetchXxxData() ──► fetchAPI(endpoint) ──► fetch()      │
│                           │                              │
│                           ▼                              │
│                   Backend Response                       │
└─────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────┐
│                Backend (localhost:8000)                  │
└─────────────────────────────────────────────────────────┘
```

---

## Styling

### Theme Colors
Defined in `index.css`:

```css
--color-stitch-dark: #10131a    /* Dark background */
--color-stitch-accent: #4fdbc8  /* Cyan accent */
--color-stitch-text: #e1e2eb    /* Light text */
--color-stitch-muted: #6c7086   /* Muted gray */
--color-stitch-error: #ffb4ab   /* Error/critical red */
```

### Severity Colors
Used consistently across pages:

| Severity | Color | Hex |
|----------|-------|-----|
| CRITICAL | Coral Red | `#ffb4ab` |
| HIGH | Orange | `#f38764` |
| MEDIUM | Peach | `#ffb59e` |
| LOW | Teal | `#a0d0c6` |
| WATCH | Sage | `#bbcac6` |

---

## Configuration

### API Base URL (config.js)

```javascript
// Default: localhost:8000
export const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";
```

Override with environment variable:
```bash
VITE_API_BASE=https://api.yourserver.com npm run dev
```

Or create `.env` file:
```
VITE_API_BASE=https://api.yourserver.com
```

---

## Development

### Available Scripts

```bash
npm run dev      # Start dev server (hot reload)
npm run build    # Production build
npm run preview  # Preview production build
```

### Hot Reload

Vite provides instant hot module replacement. Changes to `.jsx` or `.css` files update immediately in the browser.

### Adding a New Page

1. Create page in `src/pages/NewPage.jsx`
2. Add route in `src/App.jsx`:
   ```jsx
   <Route path="/new-page" element={<NewPage />} />
   ```
3. Add API functions to `src/services/api.js` if needed

### Adding a New API Endpoint

In `src/services/api.js`:

```javascript
export async function fetchNewEndpoint() {
  return fetchAPI('/api/new/endpoint');
}
```

---

## Performance Notes

- **Polling intervals**: Pages poll every 5-10 seconds for updates
- **Parallel fetching**: Aggregated fetchers use `Promise.all` for parallel requests
- **3D rendering**: `frameloop="demand"` minimizes GPU usage when scene is static
- **Graceful failures**: API errors return empty defaults, preventing crashes
