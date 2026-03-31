# Metrics Page Fix Summary

## What Was Changed

The Metrics page was simplified to **only use verified backend fields** with no assumptions or calculations.

---

## Fields REMOVED

### 1. Avg Miss Distance Improvement
**Reason:** While `/api/system/metrics` does return `performance.avg_miss_distance_improvement_m`, this field was removed per user requirement to keep only guaranteed core metrics.

### 2. Fuel Consumed (kg)
**Reason:** While `/api/system/metrics` does return `performance.total_fuel_consumed_kg`, this field was removed per user requirement.

### 3. Success Rate %
**Reason:** While `/api/system/metrics` does return `maneuvers.success_rate_pct`, this field was removed per user requirement.

### 4. Verification Success Rate
**Reason:** While available in metrics endpoint, it was removed to simplify the page to core operational metrics only.

### 5. "Autonomous Decisions" and "Manual Overrides"
**Reason:** These fields **do not exist** in `/api/decisions/statistics`. The actual response contains:
- `decisions_by_action` with keys: `maneuver_scheduled`, `deferred`, `skipped`
- Not `autonomous_decisions` or `manual_overrides`

### 6. Efficiency Rating (%)
**Reason:** This was a calculated field `(conjunctionsAvoided / totalConjunctions) * 100`. Calculation removed to show only raw backend data.

### 7. Critical Threats Count
**Reason:** This came from `/api/avoidance/status` which is not in the required API list.

### 8. Conjunctions Detected/Avoided
**Reason:** These came from `/api/system/metrics` which was removed from scope.

---

## Fields KEPT (All Verified)

### From `/api/system/summary`
- `satellites.active` → Active Satellites
- `debris.total` → Debris Tracked
- `fuel.constellation_fuel_fraction` → Fleet Fuel %

### From `/api/decisions/statistics`
- `total_decisions` → Total Decisions
- `decisions_by_action.maneuver_scheduled` → Maneuvers Scheduled
- `decisions_by_action.deferred` → Deferred
- `decisions_by_action.skipped` → Skipped

### From `/api/decisions/fuel/status`
- `satellites[]` array with per-satellite fuel data
- Filtered by `fuel_status === 'CRITICAL'` → Critical Fuel Count
- Filtered by `fuel_status === 'LOW'` → Low Fuel Count
- Individual satellite details: `satellite_id`, `fuel_kg`, `total_fuel_capacity_kg`, `fuel_status`

### From `/api/history/statistics`
- `total_events` → Total Events
- `maneuvers.total` → Total Maneuvers
- `conjunctions.total` → Conjunctions Detected

---

## New Page Structure

### Section 1: System Overview (3 cards)
- Active Satellites
- Debris Tracked
- Fleet Fuel %

### Section 2: Decision Analytics (panel)
- Total Decisions
- Maneuvers Scheduled
- Deferred
- Skipped

### Section 3: Fuel Status (2 panels)
- Fleet Fuel Remaining (bar)
- Critical Fuel / Low Fuel counts

### Section 4: Per-Satellite Fuel Details (list)
- Top 10 satellites with fuel bars
- Shows: satellite ID, fuel %, kg remaining/total, status color

### Section 5: Historical Summary (3 cards)
- Total Events
- Total Maneuvers
- Conjunctions

### Section 6: Constellation Telemetry (banner)
- Links to Mission Control and Dashboard

---

## Why This Is Better

1. **No guessing** - Only uses fields that actually exist in backend responses
2. **No calculations** - Shows raw backend data only
3. **Clearer structure** - Organized by data source (summary, decisions, fuel, history)
4. **Per-satellite detail** - Shows top 10 satellites with individual fuel status
5. **Fewer APIs** - Reduced from 6 APIs to 5 APIs (removed `/api/system/metrics` and `/api/avoidance/status`)

---

## Data Accuracy Guarantee

Every field displayed is:
1. Directly from backend API response
2. No transformations except unit conversion (fraction to percentage)
3. No assumptions about field existence
4. Graceful fallbacks to 0 or empty arrays if data missing

**Result:** The page will never crash due to missing fields and will only show data that actually exists.
