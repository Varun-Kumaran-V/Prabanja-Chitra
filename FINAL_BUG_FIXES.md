# Final Bug Fixes - Mission Control

## Issues Fixed

### Issue 1: time_to_tca Fallback ✅

**Problem:** Previously showed `0` when data missing, which displays as "0 min"

**Fix Applied (lines 369-372, 398):**
```javascript
// Fallback value
const timeToTCA = threat.time_to_tca_seconds != null
  ? Math.round(threat.time_to_tca_seconds / 60)
  : '--';  // Changed from 0 to '--'

// UI display
Time to TCA: {timeToTCA === '--' ? '--' : `${timeToTCA} min`}
```

**Result:** When time_to_tca_seconds is null/undefined, displays `--` instead of `0 min`

---

### Issue 2: Auto-Selection Logic ✅

**Problem:** `hasAutoSelectedRef` only allowed auto-selection once, preventing selection of new conjunctions when old ones disappeared

**Fix Applied (lines 10-57):**

**REMOVED:**
```javascript
const hasAutoSelectedRef = useRef(false);

// Old broken logic
if (!hasAutoSelectedRef.current && result.conjunctions?.conjunctions?.length > 0) {
  loadDecisionExplanation(firstConjunction.id);
  hasAutoSelectedRef.current = true;  // Never resets
}
```

**ADDED:**
```javascript
const selectedDecisionRef = useRef(null);

async function loadData() {
  const result = await fetchMissionControlData();
  setData(result);
  setLoading(false);

  const conjunctionIds = result.conjunctions?.conjunctions?.map(c => c.id) || [];

  // Clear selection if selected conjunction no longer exists
  if (selectedDecisionRef.current !== null && !conjunctionIds.includes(selectedDecisionRef.current)) {
    selectedDecisionRef.current = null;
    setSelectedDecision(null);
    setDecisionExplanation(null);
  }

  // Auto-select first conjunction if nothing is currently selected
  if (selectedDecisionRef.current === null && result.conjunctions?.conjunctions?.length > 0) {
    const firstConjunction = result.conjunctions.conjunctions[0];
    loadDecisionExplanation(firstConjunction.id);
  }
}

async function loadDecisionExplanation(conjunctionId) {
  // ... existing code ...
  selectedDecisionRef.current = conjunctionId;  // Track selection in ref
}
```

**Behavior:**
1. ✅ If NO selection AND conjunctions exist → auto-selects first
2. ✅ If user selected something → does NOT override
3. ✅ If selected conjunction disappears → clears selection and auto-selects new first
4. ✅ No flicker or unnecessary re-triggers

**Example Flow:**
- Initial load: No selection → auto-selects Conjunction A
- Poll #1 (5s): Conjunction A still selected → no change
- Poll #2 (10s): Conjunction A resolved → clears selection, auto-selects Conjunction B
- User clicks Conjunction C → manually selects C
- Poll #3 (15s): Conjunction C still exists → keeps user's selection
- Poll #4 (20s): Conjunction C resolved → clears selection, auto-selects first available

---

## Files Modified

- `src/pages/MissionControl.jsx` (lines 10-57, 369-372, 398)

## Testing Checklist

- [ ] Load Mission Control → first threat auto-selected
- [ ] Wait 5 seconds (poll) → selection unchanged (no flicker)
- [ ] Click different threat → switches to clicked threat
- [ ] Wait 5 seconds → manual selection preserved
- [ ] Missing time_to_tca displays as `--` not `0 min`
- [ ] When selected threat resolves → auto-selects new threat
