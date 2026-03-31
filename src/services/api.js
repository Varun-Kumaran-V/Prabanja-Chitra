/**
 * API Service Layer
 * Centralized API calls to the Aether Constellation Manager backend
 */

import { API_BASE } from '../config';

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;

  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}

// ============================================
// SYSTEM ENDPOINTS
// ============================================

/**
 * Get system health status
 */
export async function fetchSystemHealth() {
  return fetchAPI('/api/health');
}

/**
 * Get system summary (constellation overview)
 */
export async function fetchSystemSummary() {
  return fetchAPI('/api/system/summary');
}

/**
 * Get system risk assessment
 */
export async function fetchSystemRisk() {
  return fetchAPI('/api/system/risk');
}

/**
 * Get system metrics
 */
export async function fetchSystemMetrics() {
  return fetchAPI('/api/system/metrics');
}

// ============================================
// AVOIDANCE / THREAT ENDPOINTS
// ============================================

/**
 * Get avoidance status
 */
export async function fetchAvoidanceStatus() {
  return fetchAPI('/api/avoidance/status');
}

/**
 * Get active conjunctions (close approaches)
 */
export async function fetchConjunctions() {
  return fetchAPI('/api/avoidance/conjunctions');
}

/**
 * Get pending maneuvers
 */
export async function fetchPendingManeuvers() {
  return fetchAPI('/api/avoidance/maneuvers/pending');
}

/**
 * Get threat scores
 */
export async function fetchThreatScores() {
  return fetchAPI('/api/decisions/threats/scores');
}

/**
 * Get critical threats
 */
export async function fetchCriticalThreats() {
  return fetchAPI('/api/decisions/threats/critical');
}

// ============================================
// DECISION ENDPOINTS
// ============================================

/**
 * Get all decisions
 */
export async function fetchDecisions() {
  return fetchAPI('/api/decisions');
}

/**
 * Get decision statistics
 */
export async function fetchDecisionStats() {
  return fetchAPI('/api/decisions/statistics');
}

/**
 * Get decision summary
 */
export async function fetchDecisionSummary() {
  return fetchAPI('/api/decisions/summary');
}

// ============================================
// HISTORY ENDPOINTS
// ============================================

/**
 * Get event history log
 */
export async function fetchEventHistory(limit = 50) {
  return fetchAPI(`/api/history/events?limit=${limit}`);
}

/**
 * Get historical statistics
 */
export async function fetchHistoricalStats() {
  return fetchAPI('/api/history/statistics');
}

/**
 * Get maneuver history
 */
export async function fetchManeuverHistory() {
  return fetchAPI('/api/history/maneuvers');
}

// ============================================
// VISUALIZATION ENDPOINTS
// ============================================

/**
 * Get current visualization snapshot (satellite/debris positions)
 */
export async function fetchVisualizationSnapshot() {
  return fetchAPI('/api/visualization/snapshot');
}

/**
 * Get full visualization snapshot
 */
export async function fetchVisualizationFull() {
  return fetchAPI('/api/visualization/snapshot/full');
}

/**
 * Get ground stations
 */
export async function fetchGroundStations() {
  return fetchAPI('/api/visualization/ground-stations');
}

// ============================================
// SIMULATION ENDPOINTS
// ============================================

/**
 * Run a simulation step
 */
export async function runSimulationStep(stepSeconds = 60) {
  return fetchAPI('/api/simulate/step', {
    method: 'POST',
    body: JSON.stringify({ dt_seconds: stepSeconds }),
  });
}

/**
 * Get simulation status
 */
export async function fetchSimulationStatus() {
  return fetchAPI('/api/simulate/status');
}

/**
 * Reset simulation
 */
export async function resetSimulation() {
  return fetchAPI('/api/simulate/reset', { method: 'POST' });
}

// ============================================
// FUEL ENDPOINTS
// ============================================

/**
 * Get fuel status for constellation
 * Transforms satellites object to array if needed
 */
export async function fetchFuelStatus() {
  const result = await fetchAPI('/api/decisions/fuel/status');
  // Backend may return satellites as object keyed by sat_id - transform to array
  if (result.satellites && !Array.isArray(result.satellites)) {
    result.satellites = Object.entries(result.satellites).map(([id, data]) => ({
      satellite_id: id,
      ...data,
    }));
  }
  return result;
}

/**
 * Get critical fuel satellites
 */
export async function fetchCriticalFuelSatellites() {
  return fetchAPI('/api/decisions/fuel/critical');
}

/**
 * Get unprotected satellites
 * Maps backend 'satellites' field to 'unprotected_satellites' for frontend consistency
 */
export async function fetchUnprotectedSatellites() {
  const result = await fetchAPI('/api/avoidance/unprotected');
  // Backend returns { satellites: [...] }, frontend expects { unprotected_satellites: [...] }
  if (result.satellites && !result.unprotected_satellites) {
    result.unprotected_satellites = result.satellites;
  }
  return result;
}

/**
 * Get decision explanation for a specific decision ID
 */
export async function fetchDecisionExplanation(decisionId) {
  return fetchAPI(`/api/decisions/explain/${decisionId}`);
}

/**
 * Get avoidance sequences
 */
export async function fetchAvoidanceSequences() {
  return fetchAPI('/api/avoidance/sequences');
}

// ============================================
// AGGREGATED DATA FETCHERS (for specific pages)
// ============================================

/**
 * Fetch all data needed for the Home page
 */
export async function fetchHomePageData() {
  const [health, summary, risk, decisions] = await Promise.all([
    fetchSystemHealth().catch(() => ({})),
    fetchSystemSummary().catch(() => ({})),
    fetchSystemRisk().catch(() => ({ top_threats: [] })),
    fetchDecisionStats().catch(() => ({})),
  ]);

  return {
    health,
    summary,
    risk,
    decisions,
  };
}

/**
 * Fetch all data needed for Mission Control page
 */
export async function fetchMissionControlData() {
  const [
    avoidanceStatus,
    summary,
    conjunctions,
    maneuvers,
    sequences,
    events,
    fuelStatus,
    unprotected
  ] = await Promise.all([
    fetchAvoidanceStatus().catch(() => ({ enabled: false, active_conjunctions: 0 })),
    fetchSystemSummary().catch(() => ({})),
    fetchConjunctions().catch(() => ({ conjunctions: [] })),
    fetchPendingManeuvers().catch(() => ({ maneuvers: [] })),
    fetchAvoidanceSequences().catch(() => ({ sequences: [] })),
    fetchEventHistory(20).catch(() => ({ events: [] })),
    fetchFuelStatus().catch(() => ({ satellites: [] })),
    fetchUnprotectedSatellites().catch(() => ({ unprotected_satellites: [] })),
  ]);

  return {
    avoidanceStatus,
    summary,
    conjunctions,
    maneuvers,
    sequences,
    events,
    fuelStatus,
    unprotected,
  };
}

/**
 * Fetch all data needed for Metrics page
 */
export async function fetchMetricsPageData() {
  const [health, metrics, decisions, stats] = await Promise.all([
    fetchSystemHealth().catch(() => ({})),
    fetchSystemMetrics().catch(() => ({})),
    fetchDecisionStats().catch(() => ({})),
    fetchHistoricalStats().catch(() => ({})),
  ]);

  return {
    health,
    metrics,
    decisions,
    stats,
  };
}

export default {
  fetchSystemHealth,
  fetchSystemSummary,
  fetchSystemRisk,
  fetchSystemMetrics,
  fetchAvoidanceStatus,
  fetchConjunctions,
  fetchPendingManeuvers,
  fetchThreatScores,
  fetchCriticalThreats,
  fetchDecisions,
  fetchDecisionStats,
  fetchDecisionSummary,
  fetchEventHistory,
  fetchHistoricalStats,
  fetchManeuverHistory,
  fetchVisualizationSnapshot,
  fetchVisualizationFull,
  fetchGroundStations,
  runSimulationStep,
  fetchSimulationStatus,
  resetSimulation,
  fetchFuelStatus,
  fetchCriticalFuelSatellites,
  fetchUnprotectedSatellites,
  fetchDecisionExplanation,
  fetchAvoidanceSequences,
  fetchHomePageData,
  fetchMissionControlData,
  fetchMetricsPageData,
};
