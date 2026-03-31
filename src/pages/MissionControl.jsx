import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import {
  fetchMissionControlData,
  fetchDecisionExplanation,
  runSimulationStep,
  fetchDecisions,
  fetchDecisionStats,
} from '../services/api';

export default function MissionControl() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedDecision, setSelectedDecision] = useState(null);
  const [decisionExplanation, setDecisionExplanation] = useState(null);
  const selectedDecisionRef = useRef(null);
  const [decisions, setDecisions] = useState([]);
  const [decisionStats, setDecisionStats] = useState(null);

  // Load initial data
  useEffect(() => {
    loadData();
  }, []);

  // Poll for updates every 5 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      loadData();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  async function loadData() {
    try {
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

      // Fetch decisions and decision stats
      const [decisionsData, statsData] = await Promise.all([
        fetchDecisions().catch(() => ({ decisions: [] })),
        fetchDecisionStats().catch(() => ({})),
      ]);
      setDecisions(decisionsData.decisions || []);
      setDecisionStats(statsData);
    } catch (error) {
      console.error('Failed to load mission control data:', error);
      setLoading(false);
    }
  }

  async function loadDecisionExplanation(conjunctionId) {
    try {
      const explanation = await fetchDecisionExplanation(conjunctionId);
      setDecisionExplanation(explanation);
      setSelectedDecision(conjunctionId);
      selectedDecisionRef.current = conjunctionId;
    } catch (error) {
      console.error('Failed to load decision explanation:', error);
      setDecisionExplanation(null);
    }
  }

  async function handleSimulationStep() {
    try {
      await runSimulationStep(60);
      await loadData();
    } catch (error) {
      console.error('Failed to run simulation step:', error);
    }
  }

  if (loading || !data) {
    return (
      <div className="min-h-screen bg-[#10131a] flex items-center justify-center">
        <div className="text-[#4fdbc8] text-xl">Loading Mission Control...</div>
      </div>
    );
  }

  const {
    avoidanceStatus = {},
    summary = {},
    conjunctions = { conjunctions: [] },
    maneuvers = { maneuvers: [] },
    sequences = { sequences: [] },
    events = { events: [] },
    fuelStatus = { satellites: [] },
    unprotected = { unprotected_satellites: [] },
  } = data;

  // Extract data for display
  const systemMode = avoidanceStatus?.enabled ? 'AUTONOMOUS' : 'MANUAL';
  const satelliteCount = summary?.constellation?.total_satellites || 0;
  const debrisCount = summary?.constellation?.total_debris || 0;
  const criticalThreats = conjunctions?.conjunctions?.filter(c => c?.severity === 'CRITICAL').length || 0;
  const maneuverCount = maneuvers?.maneuvers?.length || 0;
  const fuelPct = summary?.fuel?.constellation_fuel_fraction
    ? Math.round(summary.fuel.constellation_fuel_fraction * 100)
    : 0;

  // Get top threats sorted by severity
  const sortedThreats = Array.isArray(conjunctions?.conjunctions) 
    ? [...conjunctions.conjunctions].sort((a, b) => {
        const severityOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3, WATCH: 4 };
        return (severityOrder[a?.severity] || 99) - (severityOrder[b?.severity] || 99);
      })
    : [];

  const topThreat = sortedThreats[0] || null;
  const secondThreat = sortedThreats[1] || null;

  return (
    <div className="min-h-screen bg-[#10131a] text-[#e1e2eb]">
       <div className="max-w-7xl mx-auto px-6 py-6 space-y-6">
      {/* Top Nav Bar */}
      <nav className="fixed top-0 w-full z-50 bg-[#1d2026]/80 backdrop-blur-xl border-b border-[#4fdbc8]/15 shadow-[0_24px_48px_rgba(0,0,0,0.4)]">
        <div className="flex justify-between items-center h-16 px-8 max-w-[1440px] mx-auto font-['Inter'] antialiased tracking-tight">
          <div className="text-xl font-semibold tracking-[-0.02em] text-[#e1e2eb]">
            Prabanja Chitra
          </div>
          <div className="hidden md:flex gap-8 items-center h-full">
            <Link
              to="/home"
              className="text-[#e1e2eb]/70 hover:text-[#e1e2eb] transition-colors"
            >
              Home
            </Link>
            <Link
              to="/mission-control"
              className="text-[#4fdbc8] border-b-2 border-[#4fdbc8] pb-1 font-bold"
            >
              Mission Control
            </Link>
            <Link
              to="/metrics"
              className="text-[#e1e2eb]/70 hover:text-[#e1e2eb] transition-colors"
            >
              Metrics
            </Link>
            <Link
              to="/architecture"
              className="text-[#e1e2eb]/70 hover:text-[#e1e2eb] transition-colors"
            >
              Architecture
            </Link>
          </div>
          <Link
            to="/dashboard"
            className="bg-[#4fdbc8] text-[#003731] px-5 py-2 rounded-lg font-semibold hover:bg-[#32353c] hover:text-[#4fdbc8] transition-all duration-200 active:scale-95"
          >
            Launch Dashboard
          </Link>
        </div>
      </nav>

      <main className="pt-24 pb-12 px-8 max-w-[1440px] mx-auto min-h-screen">
        {/* Compact Status Strip */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4 mb-8">
          <div className="bg-[#1a1d26] border-l-4 border-[#4fdbc8] p-3 rounded-lg flex flex-col justify-center shadow-lg hover:shadow-xl transition-shadow">
            <span className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#6c7086] font-bold">
              System Mode
            </span>
            <span className="text-[#4fdbc8] font-bold mt-1">{systemMode}</span>
          </div>
          <div className="bg-[#1a1d26] p-3 rounded-lg flex flex-col justify-center border border-[#2a2f3a] shadow-lg hover:shadow-xl hover:border-[#3a3f4a] transition-all">
            <span className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#6c7086]">
              Satellites
            </span>
            <span className="text-[#e1e2eb] text-xl font-bold mt-1">{satelliteCount}</span>
          </div>
          <div className="bg-[#1a1d26] p-3 rounded-lg flex flex-col justify-center border border-[#2a2f3a] shadow-lg hover:shadow-xl hover:border-[#3a3f4a] transition-all">
            <span className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#6c7086]">
              Debris Tracking
            </span>
            <span className="text-[#e1e2eb] text-xl font-bold mt-1">{debrisCount}</span>
          </div>
          <div className="bg-[#1a1d26] border-l-4 border-[#ffb4ab] p-3 rounded-lg flex flex-col justify-center shadow-lg hover:shadow-xl transition-shadow">
            <span className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#ffb4ab] font-bold">
              Critical Threats
            </span>
            <span className="text-[#ffb4ab] text-xl font-bold mt-1">{criticalThreats}</span>
          </div>
          <div className="bg-[#1a1d26] p-3 rounded-lg flex flex-col justify-center border border-[#2a2f3a] shadow-lg hover:shadow-xl hover:border-[#3a3f4a] transition-all">
            <span className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#6c7086]">
              Maneuvers
            </span>
            <span className="text-[#e1e2eb] text-xl font-bold mt-1">{maneuverCount}</span>
          </div>
          <div className="bg-[#1a1d26] p-3 rounded-lg flex flex-col justify-center border border-[#2a2f3a] shadow-lg hover:shadow-xl hover:border-[#3a3f4a] transition-all">
            <span className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#6c7086]">
              Total Fuel
            </span>
            <span className="text-[#a0d0c6] text-xl font-bold mt-1">{fuelPct}%</span>
          </div>
        </div>

        {/* Operational Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* LEFT COLUMN: Threats */}
          <aside className="lg:col-span-3 flex flex-col gap-6">
            {/* Active Threats */}
            <section className="bg-[#1a1d26] p-5 rounded-xl border border-[#2a2f3a] shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-[0.6875rem] uppercase tracking-[0.05em] font-bold text-[#e1e2eb] flex items-center gap-2">
                  <span className="text-sm text-[#ffb4ab]">⚠</span>
                  Active Threats
                </h2>
                <span className="text-[0.6rem] text-[#bbcac6]">{sortedThreats.length} TOTAL</span>
              </div>
              <div className="flex flex-col gap-3 max-h-[400px] overflow-y-auto pr-2">
                {sortedThreats.length > 0 ? (
                  sortedThreats.map((threat, idx) => (
                    <ThreatCard
                      key={threat.id}
                      threat={threat}
                      onClick={() => loadDecisionExplanation(threat.id)}
                      selected={selectedDecision === threat.id}
                      opacity={idx > 2 ? 0.7 : 1}
                    />
                  ))
                ) : (
                  <div className="bg-[#272a31] p-4 rounded-xl text-center text-[#bbcac6] text-sm">
                    No active threats detected
                  </div>
                )}
              </div>
            </section>

            {/* Unprotected Satellites */}
            <section className="bg-[#1a1d26] p-5 rounded-xl border border-[#2a2f3a] shadow-lg">
              <h2 className="text-[0.6875rem] uppercase tracking-[0.05em] font-bold text-[#e1e2eb] mb-4">
                Unprotected Assets
              </h2>
              <div className="space-y-3">
                {unprotected.unprotected_satellites?.length > 0 ? (
                  unprotected.unprotected_satellites.map((sat, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between text-[0.6875rem]"
                    >
                      <span className="text-[#bbcac6]">{sat.satellite_id}</span>
                      <span className="text-[#ffb4ab]">{sat.reason || 'NO COVERAGE'}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-[0.6875rem] text-[#bbcac6]/50 text-center">
                    All satellites protected
                  </div>
                )}
              </div>
            </section>
          </aside>

          {/* CENTER COLUMN: Visualization */}
          <main className="lg:col-span-6 flex flex-col gap-6">
            {/* Main Visualization Canvas */}
            <div className="bg-[#0b0e14] rounded-xl min-h-[480px] relative border border-[#2a2f3a] shadow-xl flex items-center justify-center overflow-hidden">
              <div className="absolute inset-0 opacity-40 bg-[radial-gradient(circle_at_center,rgba(79,219,200,0.15)_0%,transparent_70%)]"></div>
              <img
                alt="Satellite orbital tracks"
                className="absolute inset-0 w-full h-full object-cover opacity-60"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuBNw4Yvfp6ak1huvv6WCJjs9-3mrt-arB5YcVSszvbSvYsV1NvBRGR4QvY6Tjb-HkUGZUJ5rxmQ5hXvYlcUGpABjDQin8lRgfH6oAo_k6nYTSPP4RiZ6iKpDpHVxpN5yJ9pjplfL_kBVOwl7fFHaoIV0DHibd00DzQQ1N8PA8TFuFlVCkT2IlpuQRDa2xrrVLVdU5fEUca3hIW9adimrM5jpiIJeazDFKJJq6X98aESMMdOPLqVaCHxVvl0RiH77jFbJJ_6CZq0GIpM"
              />

              {/* HUD Overlays */}
              <div className="absolute top-6 left-6 flex flex-col gap-1 z-10">
                <span className="text-[0.6rem] text-[#4fdbc8]/70 uppercase tracking-widest">
                  Conjunction Monitor
                </span>
                <span className="text-lg font-bold text-[#e1e2eb]">
                  TRACKING {conjunctions?.conjunctions?.length || 0} APPROACHES
                </span>
              </div>

              {/* Miss Distance Bullseye */}
              {topThreat && (
                <div className="absolute bottom-6 right-6 w-32 h-32 border border-[#4fdbc8]/20 rounded-full flex items-center justify-center">
                  <div className="w-20 h-20 border border-[#4fdbc8]/40 rounded-full"></div>
                  <div className="w-8 h-8 border border-[#4fdbc8]/60 rounded-full flex items-center justify-center">
                    <div className="w-1 h-1 bg-[#ffb4ab] rounded-full"></div>
                  </div>
                  <span className="absolute -top-4 text-[0.6rem] text-[#bbcac6]">
                    {Math.round(topThreat?.predicted_miss_distance_m ?? 0)}m
                  </span>
                </div>
              )}

              {/* Decision Explanation Bubble */}
              {decisionExplanation && (
                <div className="absolute bottom-10 left-10 max-w-xs bg-[rgba(29,32,38,0.8)] backdrop-blur-[20px] p-4 rounded-xl border border-[#4fdbc8]/20 z-10">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm text-[#4fdbc8]">🧠</span>
                    <span className="text-[0.6875rem] font-bold text-[#4fdbc8] uppercase">
                      Autonomous Decision
                    </span>
                  </div>
                  <p className="text-[0.6875rem] leading-relaxed text-[#bbcac6]">
                    {decisionExplanation?.reasoning || decisionExplanation?.explanation ||
                     'Analyzing threat geometry and planning optimal evasion trajectory...'}
                  </p>
                </div>
              )}
            </div>

            {/* Live Maneuver Timeline */}
            <ManeuverTimeline maneuvers={maneuvers?.maneuvers || []} sequences={sequences?.sequences || []} />

            {/* Simulation Control */}
            <div className="bg-[#1a1d26] p-5 rounded-xl border border-[#2a2f3a] shadow-lg">
              <button
                onClick={handleSimulationStep}
                className="w-full bg-[#4fdbc8] text-[#003731] py-3 rounded-lg font-semibold hover:bg-[#3cc9b5] hover:shadow-lg hover:shadow-[#4fdbc8]/30 transition-all duration-200 active:scale-95"
              >
                Step Simulation (+60s)
              </button>
            </div>
          </main>

          {/* RIGHT COLUMN: Metrics & Logs */}
          <aside className="lg:col-span-3 flex flex-col gap-6">
            {/* Fuel Status */}
            <section className="bg-[#1a1d26] p-5 rounded-xl border border-[#2a2f3a] shadow-lg">
              <div className="flex justify-between items-center mb-3">
                <span className="text-[0.6875rem] uppercase font-bold text-[#6c7086]">
                  Fleet Fuel Status
                </span>
                <span className="text-[#4fdbc8] text-lg">⛽</span>
              </div>
              <div className="flex items-end gap-2 mb-3">
                <span className="text-3xl font-bold text-[#e1e2eb]">{fuelPct}%</span>
                <span className="text-[#a0d0c6] text-xs pb-1 font-semibold">NOMINAL</span>
              </div>
              <div className="w-full bg-[#0b0e14] h-2 rounded-full shadow-inner">
                <div
                  className="bg-gradient-to-r from-[#4fdbc8] to-[#a0d0c6] h-full rounded-full transition-all duration-500"
                  style={{ width: `${fuelPct}%` }}
                ></div>
              </div>
            </section>

            {/* Per-Satellite Fuel Bars */}
            <FuelStatusPanel satellites={fuelStatus?.satellites || []} />

            {/* Decision Log Panel */}
            <DecisionLogPanel decisions={decisions} decisionStats={decisionStats} />

            {/* Event Log */}
            <EventLog events={events?.events || []} />
          </aside>
        </div>
      </main>
    </div>
    </div>
  );
}

// Threat Card Component
function ThreatCard({ threat, onClick, selected, opacity = 1 }) {
  if (!threat) return null;

  const severityColors = {
    CRITICAL: { border: '#ffb4ab', bg: 'rgba(255, 180, 171, 0.2)', text: '#ffb4ab' },
    HIGH: { border: '#f38764', bg: 'rgba(243, 135, 100, 0.2)', text: '#f38764' },
    MEDIUM: { border: '#ffb59e', bg: 'rgba(255, 181, 158, 0.2)', text: '#ffb59e' },
    LOW: { border: '#a0d0c6', bg: 'rgba(160, 208, 198, 0.2)', text: '#a0d0c6' },
    WATCH: { border: '#bbcac6', bg: 'rgba(187, 202, 198, 0.2)', text: '#bbcac6' },
  };

  const colors = severityColors[threat?.severity] || severityColors.WATCH;
  const timeToTCA =
    threat?.time_to_tca != null
      ? Math.round(threat.time_to_tca / 60)
      : '--';

  return (
    <div
      onClick={onClick}
      style={{ opacity }}
      className={`bg-[#1a1d26] p-4 rounded-xl border relative overflow-hidden cursor-pointer hover:bg-[#242830] hover:shadow-lg transition-all duration-200 ${
        selected ? 'border-[#4fdbc8] shadow-lg shadow-[#4fdbc8]/20' : 'border-[#2a2f3a] hover:border-[#3a3f4a]'
      }`}
    >
      <div className="absolute top-0 left-0 w-1 h-full" style={{ background: colors.border }}></div>
      <div className="flex justify-between items-start mb-2">
        <span className="text-xs font-bold text-[#e1e2eb]">
          {threat?.satellite_id || 'Unknown'} ↔ {threat?.secondary_id || 'Unknown'}
        </span>
        <span
          className="px-2 py-0.5 rounded-sm text-[0.6rem] font-bold uppercase"
          style={{ background: colors.bg, color: colors.text }}
        >
          {threat?.severity || 'UNKNOWN'}
        </span>
      </div>
      <div className="text-[0.6875rem] text-[#bbcac6] mb-1">
        Miss Distance: {Math.round(threat?.predicted_miss_distance_m ?? 0)}m
      </div>
      <div className="text-[0.6875rem] text-[#bbcac6]">
        Time to TCA: {timeToTCA === '--' ? '--' : `${timeToTCA} min`}
      </div>
    </div>
  );
}

// Maneuver Timeline Component
function ManeuverTimeline({ maneuvers = [], sequences = [] }) {
  const safeManeuvers = Array.isArray(maneuvers) ? maneuvers : [];
  const safeSequences = Array.isArray(sequences) ? sequences : [];
  
  const allManeuvers = [...safeManeuvers];

  // Add maneuvers from sequences
  safeSequences.forEach(seq => {
    if (seq?.evasion_maneuver) allManeuvers.push(seq.evasion_maneuver);
    if (seq?.recovery_maneuver) allManeuvers.push(seq.recovery_maneuver);
  });

  const sortedManeuvers = allManeuvers
    .filter(m => m?.scheduled_time != null)
    .sort((a, b) => new Date(a.scheduled_time) - new Date(b.scheduled_time))
    .slice(0, 8);

  return (
    <div className="bg-[#1a1d26] p-5 rounded-xl border border-[#2a2f3a] shadow-lg">
      <h3 className="text-[0.6875rem] uppercase tracking-[0.05em] font-bold mb-4 text-[#e1e2eb] flex items-center justify-between">
        <span>Planned Maneuvers</span>
        <span className="text-[#4fdbc8]">{allManeuvers.length} total</span>
      </h3>
      {sortedManeuvers.length > 0 ? (
        <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2">
          {sortedManeuvers.map((m, idx) => {
            const typeColors = {
              EVASION: { bg: '#ffb4ab', text: '#1a1d26' },
              RECOVERY: { bg: '#a0d0c6', text: '#1a1d26' },
              STATION_KEEPING: { bg: '#bbcac6', text: '#1a1d26' },
              EMERGENCY: { bg: '#ff6b6b', text: '#ffffff' },
            };
            const colors = typeColors[m?.type] || { bg: '#bbcac6', text: '#1a1d26' };

            return (
              <div
                key={idx}
                className="bg-[#0b0e14] p-3 rounded-lg border-l-2"
                style={{ borderColor: colors.bg }}
              >
                <div className="flex items-center justify-between mb-2">
                  <span
                    className="px-2 py-1 rounded text-[0.6rem] font-bold uppercase"
                    style={{ background: colors.bg, color: colors.text }}
                  >
                    {m?.type || 'UNKNOWN'}
                  </span>
                  <span className="text-[0.6rem] text-[#bbcac6]">{m?.state || 'PENDING'}</span>
                </div>
                <div className="text-[0.6875rem] text-[#e1e2eb] mb-1">
                  {m?.satellite_id || 'Unknown SAT'}
                </div>
                <div className="flex items-center justify-between text-[0.6rem] text-[#bbcac6]">
                  <span>ΔV: {m?.delta_v?.toFixed(2) ?? 'N/A'} m/s</span>
                  {m?.estimated_fuel_kg != null && (
                    <span>Fuel: {m.estimated_fuel_kg.toFixed(3)} kg</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="text-center text-[#bbcac6] text-sm py-8">
          No maneuvers scheduled
        </div>
      )}
    </div>
  );
}

// Fuel Status Panel Component
function FuelStatusPanel({ satellites = [] }) {
  const safeSatellites = Array.isArray(satellites) ? satellites : [];
  const topSatellites = safeSatellites.slice(0, 5);

  return (
    <section className="bg-[#1a1d26] p-5 rounded-xl border border-[#2a2f3a] shadow-lg">
      <h3 className="text-[0.6875rem] uppercase tracking-[0.05em] font-bold mb-4 text-[#e1e2eb]">
        Per-Satellite Fuel
      </h3>
      <div className="space-y-4">
        {topSatellites.length > 0 ? (
          topSatellites.map((sat, idx) => {
            const fuelPct = (sat?.total_fuel_capacity_kg || 0) > 0
              ? Math.round(((sat?.fuel_kg || 0) / sat.total_fuel_capacity_kg) * 100)
              : 0;
            const statusColor =
              sat?.fuel_status === 'CRITICAL'
                ? '#ffb4ab'
                : sat?.fuel_status === 'LOW'
                ? '#ffb59e'
                : '#4fdbc8';

            return (
              <div key={idx} className="flex items-center gap-3">
                <div
                  className="w-2 h-2 rounded-full"
                  style={{
                    background: statusColor,
                    boxShadow: `0 0 8px ${statusColor}66`,
                  }}
                ></div>
                <div className="flex-1">
                  <div className="flex justify-between text-[0.6875rem] mb-1">
                    <span>{sat?.satellite_id || 'Unknown'}</span>
                    <span>{fuelPct}%</span>
                  </div>
                  <div className="w-full h-1 bg-[#32353c] rounded-full overflow-hidden">
                    <div
                      className="h-full transition-all duration-500"
                      style={{ width: `${fuelPct}%`, background: statusColor }}
                    ></div>
                  </div>
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-[0.6875rem] text-[#bbcac6]/50 text-center">
            No satellite data available
          </div>
        )}
      </div>
    </section>
  );
}

// Event Log Component
function EventLog({ events = [] }) {
  const safeEvents = Array.isArray(events) ? events : [];
  const recentEvents = safeEvents.slice(0, 15);

  return (
    <section className="bg-[#0b0e14] border border-[#3c4947]/15 p-5 rounded-xl flex-1 flex flex-col">
      <h3 className="text-[0.6875rem] uppercase tracking-[0.05em] font-bold mb-4 text-[#e1e2eb]">
        Event History ({safeEvents.length} events)
      </h3>
      <div className="space-y-2 overflow-y-auto max-h-[400px] pr-2">
        {recentEvents.length > 0 ? (
          recentEvents.map((event, idx) => (
            <div key={event?.id || idx} className="py-2">
              <div className="text-[0.75rem] font-semibold text-[#4fdbc8] mb-1">
                Event: {event?.event_type || 'unknown'}
              </div>
              <div className="text-[0.6875rem] text-[#e1e2eb] leading-relaxed">
                {event?.message || 'No message'}
              </div>
            </div>
          ))
        ) : (
          <div className="text-[0.6875rem] text-[#bbcac6]/50 text-center py-8">
            No events yet
          </div>
        )}
      </div>
    </section>
  );
}

// Decision Log Panel Component
function DecisionLogPanel({ decisions = [], decisionStats = {} }) {
  const safeDecisions = Array.isArray(decisions) ? decisions : [];
  const recentDecisions = safeDecisions.slice(0, 8);

  const decisionTypeColors = {
    maneuver_scheduled: { bg: '#4fdbc8', text: '#003731', icon: '✓' },
    deferred: { bg: '#ffb59e', text: '#1a1d26', icon: '⏸' },
    skipped: { bg: '#bbcac6', text: '#1a1d26', icon: '⊘' },
  };

  const totalDecisions = decisionStats?.total_decisions || 0;
  const maneuverScheduled = decisionStats?.maneuvers_scheduled || 0;
  const deferred = decisionStats?.decisions_deferred || 0;
  const skipped = decisionStats?.threats_skipped || 0;

  return (
    <section className="bg-[#1a1d26] p-5 rounded-xl border border-[#2a2f3a] shadow-lg">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-[0.6875rem] uppercase tracking-[0.05em] font-bold text-[#e1e2eb]">
          Decision Intelligence
        </h3>
        <span className="text-[#4fdbc8] text-lg">🧠</span>
      </div>

      {/* Decision Statistics */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="bg-[#0b0e14] p-2 rounded text-center">
          <div className="text-xs text-[#bbcac6]">Scheduled</div>
          <div className="text-lg font-bold text-[#4fdbc8]">{maneuverScheduled}</div>
        </div>
        <div className="bg-[#0b0e14] p-2 rounded text-center">
          <div className="text-xs text-[#bbcac6]">Deferred</div>
          <div className="text-lg font-bold text-[#ffb59e]">{deferred}</div>
        </div>
        <div className="bg-[#0b0e14] p-2 rounded text-center">
          <div className="text-xs text-[#bbcac6]">Skipped</div>
          <div className="text-lg font-bold text-[#bbcac6]">{skipped}</div>
        </div>
      </div>

      {/* Recent Decisions List */}
      <div className="space-y-2 max-h-[250px] overflow-y-auto pr-2">
        {recentDecisions.length > 0 ? (
          recentDecisions.map((decision, idx) => {
            const decisionType = decision?.maneuver_planned ? 'maneuver_scheduled' : 
                                decision?.deferred_reason ? 'deferred' : 'skipped';
            const colors = decisionTypeColors[decisionType] || decisionTypeColors.skipped;
            const timestamp = decision?.sim_time ? 
              `T+${Math.round(decision.sim_time)}s` : 
              decision?.timestamp ? new Date(decision.timestamp).toLocaleTimeString() : '--';

            return (
              <div
                key={decision?.decision_id || idx}
                className="bg-[#0b0e14] p-3 rounded-lg border-l-2"
                style={{ borderColor: colors.bg }}
              >
                <div className="flex items-start justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span
                      className="px-2 py-0.5 rounded text-[0.6rem] font-bold"
                      style={{ background: colors.bg, color: colors.text }}
                    >
                      {colors.icon}
                    </span>
                    <span className="text-[0.6875rem] text-[#e1e2eb] font-semibold">
                      {decision?.satellite_id || 'Unknown'}
                    </span>
                  </div>
                  <span className="text-[0.6rem] text-[#bbcac6]">{timestamp}</span>
                </div>
                {decision?.maneuver_planned && (
                  <div className="text-[0.6rem] text-[#4fdbc8] mt-1">
                    ΔV: {decision?.delta_v_ms?.toFixed(2) || 'N/A'} m/s • 
                    Fuel: {decision?.fuel_cost_kg?.toFixed(3) || 'N/A'} kg
                  </div>
                )}
                {decision?.deferred_reason && (
                  <div className="text-[0.6rem] text-[#ffb59e] mt-1">
                    Reason: {decision.deferred_reason}
                  </div>
                )}
                {decision?.skip_reason && (
                  <div className="text-[0.6rem] text-[#bbcac6] mt-1">
                    Reason: {decision.skip_reason}
                  </div>
                )}
              </div>
            );
          })
        ) : (
          <div className="text-[0.6875rem] text-[#bbcac6]/50 text-center py-4">
            No decisions made yet
          </div>
        )}
      </div>

      {/* Total Decision Count */}
      {totalDecisions > 0 && (
        <div className="mt-3 pt-3 border-t border-[#3c4947]/10 text-center">
          <span className="text-[0.6rem] text-[#bbcac6]">
            Total Decisions: <span className="font-bold text-[#e1e2eb]">{totalDecisions}</span>
          </span>
        </div>
      )}
    </section>
  );
}
