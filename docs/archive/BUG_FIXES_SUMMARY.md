# Mission Control Bug Fixes - Summary

## Files Modified

1. `src/services/api.js`
2. `src/pages/MissionControl.jsx`

---

## Fixes Applied

### 1. ✅ Simulation API Payload (api.js:187-192)

**Issue:** Payload used `dt_seconds` but should use `step_seconds`

**Fix:**
```javascript
// BEFORE
body: JSON.stringify({ dt_seconds: dtSeconds })

// AFTER
body: JSON.stringify({ step_seconds: stepSeconds })
```

**Why:** Backend expects `step_seconds` parameter for simulation stepping.

---

### 2. ✅ Stale State Bug in Auto-Selection (MissionControl.jsx:14, 35-40)

**Issue:** `selectedDecision` was captured in closure, causing repeated auto-selection on every poll cycle

**Fix:**
```javascript
// Added ref to track if auto-selection already happened
const hasAutoSelectedRef = useRef(false);

// Modified loadData to only auto-select once
if (!hasAutoSelectedRef.current && result.conjunctions?.conjunctions?.length > 0) {
  const firstConjunction = result.conjunctions.conjunctions[0];
  loadDecisionExplanation(firstConjunction.id);
  hasAutoSelectedRef.current = true;
}
```

**Why:** Using a ref prevents the auto-selection from running on every 5-second poll, eliminating flicker and unnecessary API calls.

---

### 3. ✅ Invalid Inline Color Values (ThreatCard:352-356)

**Issue:** CSS doesn't support Tailwind-style `#ffb4ab/20` syntax in inline styles

**Fix:**
```javascript
// BEFORE
CRITICAL: { border: '#ffb4ab', bg: '#ffb4ab/20', text: '#ffb4ab' }

// AFTER
CRITICAL: { border: '#ffb4ab', bg: 'rgba(255, 180, 171, 0.2)', text: '#ffb4ab' }
```

**Applied to all severity levels:**
- CRITICAL: `rgba(255, 180, 171, 0.2)`
- HIGH: `rgba(243, 135, 100, 0.2)`
- MEDIUM: `rgba(255, 181, 158, 0.2)`
- LOW: `rgba(160, 208, 198, 0.2)`
- WATCH: `rgba(187, 202, 198, 0.2)`

**Why:** Browsers require valid CSS color values in style attributes.

---

### 4. ✅ Sorting Crash Risk (ManeuverTimeline:400-402)

**Issue:** Sorting by `scheduled_time` crashes if field is null/undefined

**Fix:**
```javascript
// BEFORE
const sortedManeuvers = allManeuvers
  .sort((a, b) => new Date(a.scheduled_time) - new Date(b.scheduled_time))

// AFTER
const sortedManeuvers = allManeuvers
  .filter(m => m.scheduled_time != null)
  .sort((a, b) => new Date(a.scheduled_time) - new Date(b.scheduled_time))
```

**Why:** Filter out maneuvers without scheduled times before sorting to prevent `Invalid Date` errors.

---

### 5. ✅ Division by Zero Risk (FuelStatusPanel:457-459)

**Issue:** Dividing by `total_fuel_capacity_kg` when it's zero causes NaN or Infinity

**Fix:**
```javascript
// BEFORE
const fuelPct = Math.round((sat.fuel_kg / sat.total_fuel_capacity_kg) * 100);

// AFTER
const fuelPct = sat.total_fuel_capacity_kg > 0
  ? Math.round((sat.fuel_kg / sat.total_fuel_capacity_kg) * 100)
  : 0;
```

**Why:** Guard against division by zero with defensive check and sensible fallback.

---

### 6. ✅ Missing time_to_tca_seconds Handling (ThreatCard:358-360, MissionControl.jsx:277)

**Issue:** `time_to_tca_seconds` could be null/undefined causing calculation errors

**Fix:**
```javascript
// ThreatCard
const timeToTCA = threat.time_to_tca_seconds != null
  ? Math.round(threat.time_to_tca_seconds / 60)
  : 0;

// Miss distance display
{Math.round(topThreat.miss_distance_m || 0)}m
```

**Why:** Gracefully handle missing data with null checks and fallback values.

---

### 7. ✅ Polling Optimization (MissionControl.jsx:14, 35-40)

**Issue:** Every 5-second poll caused full reload flicker and repeated auto-selection

**Fix:**
Same as Fix #2 - using `hasAutoSelectedRef` prevents re-triggering auto-selection logic on every poll.

**Impact:**
- Eliminates unnecessary API calls to `/api/decisions/explain/{id}`
- Prevents UI flicker from repeated state updates
- Maintains smooth user experience during polling

**Why:** Auto-selection should happen once on mount, not on every data refresh.

---

## Testing Checklist

- [ ] Simulation step button works without console errors
- [ ] First threat auto-selects on page load
- [ ] Polling doesn't repeatedly change selected threat
- [ ] Severity badges display correct colors
- [ ] Fuel percentages display correctly even with edge cases
- [ ] Maneuver timeline doesn't crash with missing data
- [ ] Time to TCA displays "0 min" instead of "NaN min" for missing data
- [ ] Miss distance displays "0m" instead of "NaNm" for missing data

---

## Code Quality Improvements

All fixes were minimal and defensive:
- Added null checks where data might be missing
- Used ternary operators for simple conditionals
- Converted invalid CSS to valid rgba() format
- Used useRef for one-time initialization logic
- Filtered data before operations that require valid values

No redesigns. No new features. Only safety and correctness.
