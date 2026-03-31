import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { 
  PageLayout, 
  Card, 
  StatusBadge, 
  ProgressBar, 
  EmptyState,
  MissionControlSkeleton,
} from '../components/shared';
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
  const [simulating, setSimulating] = useState(false);

  // Load data with cleanup
  const loadData = useCallback(async () => {
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
  }, []);

  // Initial load
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Poll for updates every 5 seconds
  useEffect(() => {
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [loadData]);

  const loadDecisionExplanation = async (conjunctionId) => {
    try {
      const explanation = await fetchDecisionExplanation(conjunctionId);
      setDecisionExplanation(explanation);
      setSelectedDecision(conjunctionId);
      selectedDecisionRef.current = conjunctionId;
    } catch (error) {
      console.error('Failed to load decision explanation:', error);
      setDecisionExplanation(null);
    }
  };

  const handleSimulationStep = async () => {
    setSimulating(true);
    try {
      await runSimulationStep(60);
      await loadData();
    } catch (error) {
      console.error('Failed to run simulation step:', error);
    } finally {
      setSimulating(false);
    }
  };

  // Memoized computed values
  const computedData = useMemo(() => {
    if (!data) return null;

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

    const systemMode = avoidanceStatus?.enabled ? 'AUTONOMOUS' : 'MANUAL';
    const satelliteCount = summary?.constellation?.total_satellites || 0;
    const debrisCount = summary?.constellation?.total_debris || 0;
    const criticalThreats = conjunctions?.conjunctions?.filter(c => c?.severity === 'CRITICAL').length || 0;
    const maneuverCount = maneuvers?.maneuvers?.length || 0;
    const fuelPct = summary?.fuel?.constellation_fuel_fraction
      ? Math.round(summary.fuel.constellation_fuel_fraction * 100)
      : 0;

    const sortedThreats = Array.isArray(conjunctions?.conjunctions) 
      ? [...conjunctions.conjunctions].sort((a, b) => {
          const severityOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3, WATCH: 4 };
          return (severityOrder[a?.severity] || 99) - (severityOrder[b?.severity] || 99);
        })
      : [];

    return {
      systemMode,
      satelliteCount,
      debrisCount,
      criticalThreats,
      maneuverCount,
      fuelPct,
      sortedThreats,
      maneuvers: maneuvers?.maneuvers || [],
      sequences: sequences?.sequences || [],
      events: events?.events || [],
      satellites: fuelStatus?.satellites || [],
      unprotectedSatellites: unprotected?.unprotected_satellites || [],
      totalConjunctions: conjunctions?.conjunctions?.length || 0,
    };
  }, [data]);

  if (loading || !computedData) {
    return <MissionControlSkeleton />;
  }

  return (
    <PageLayout showFooter={false} className="px-6 md:px-8">
      {/* Compact Status Strip */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3 mb-6 animate-fadeInUp">
        <StatusCard 
          label="System Mode" 
          value={computedData.systemMode} 
          accent={computedData.systemMode === 'AUTONOMOUS'}
        />
        <StatusCard label="Satellites" value={computedData.satelliteCount} />
        <StatusCard label="Debris Tracking" value={computedData.debrisCount} />
        <StatusCard 
          label="Critical Threats" 
          value={computedData.criticalThreats} 
          critical={computedData.criticalThreats > 0}
        />
        <StatusCard label="Maneuvers" value={computedData.maneuverCount} />
        <StatusCard label="Fleet Fuel" value={`${computedData.fuelPct}%`} fuel />
      </div>

      {/* Main Operational Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* LEFT COLUMN: Threats */}
        <aside className="lg:col-span-3 flex flex-col gap-5 animate-slideInLeft">
          {/* Active Threats */}
          <Card padding="normal" className="flex flex-col">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xs uppercase tracking-[0.05em] font-bold text-[#e1e2eb] flex items-center gap-2">
                <span className="text-[#ffb4ab]">⚠</span>
                Active Threats
              </h2>
              <span className="text-[0.65rem] text-[#bbcac6] font-mono">
                {computedData.sortedThreats.length} TOTAL
              </span>
            </div>
            <div className="flex flex-col gap-2 max-h-[380px] overflow-y-auto pr-1 -mr-1">
              {computedData.sortedThreats.length > 0 ? (
                computedData.sortedThreats.map((threat, idx) => (
                  <ThreatCard
                    key={threat.id}
                    threat={threat}
                    onClick={() => loadDecisionExplanation(threat.id)}
                    selected={selectedDecision === threat.id}
                    dimmed={idx > 3}
                  />
                ))
              ) : (
                <EmptyState 
                  icon="✓" 
                  title="All Clear" 
                  description="No active threats detected"
                />
              )}
            </div>
          </Card>

          {/* Unprotected Satellites */}
          <Card padding="normal">
            <h2 className="text-xs uppercase tracking-[0.05em] font-bold text-[#e1e2eb] mb-4">
              Unprotected Assets
            </h2>
            <div className="space-y-2">
              {computedData.unprotectedSatellites.length > 0 ? (
                computedData.unprotectedSatellites.map((sat, idx) => (
                  <div key={idx} className="flex items-center justify-between text-[0.6875rem] py-1">
                    <span className="text-[#bbcac6]">{sat.satellite_id}</span>
                    <span className="text-[#ffb4ab] font-medium">{sat.reason || 'NO COVERAGE'}</span>
                  </div>
                ))
              ) : (
                <div className="text-[0.6875rem] text-[#4fdbc8] text-center py-3">
                  ✓ All satellites protected
                </div>
              )}
            </div>
          </Card>
        </aside>

        {/* CENTER COLUMN: Visualization */}
        <main className="lg:col-span-6 flex flex-col gap-5 animate-fadeInUp delay-100">
          {/* Main Visualization Canvas */}
          <div className="bg-[#0b0e14] rounded-xl min-h-[420px] relative border border-[#2a2f3a] shadow-xl overflow-hidden">
            <div className="absolute inset-0 gradient-radial-accent opacity-60" />
            <img
              alt="Satellite orbital tracks"
              className="absolute inset-0 w-full h-full object-cover opacity-50"
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuBNw4Yvfp6ak1huvv6WCJjs9-3mrt-arB5YcVSszvbSvYsV1NvBRGR4QvY6Tjb-HkUGZUJ5rxmQ5hXvYlcUGpABjDQin8lRgfH6oAo_k6nYTSPP4RiZ6iKpDpHVxpN5yJ9pjplfL_kBVOwl7fFHaoIV0DHibd00DzQQ1N8PA8TFuFlVCkT2IlpuQRDa2xrrVLVdU5fEUca3hIW9adimrM5jpiIJeazDFKJJq6X98aESMMdOPLqVaCHxVvl0RiH77jFbJJ_6CZq0GIpM"
            />

            {/* HUD Overlays */}
            <div className="absolute top-5 left-5 z-10">
              <span className="text-[0.65rem] text-[#4fdbc8]/70 uppercase tracking-widest">
                Conjunction Monitor
              </span>
              <div className="text-lg font-bold text-[#e1e2eb] mt-1">
                TRACKING {computedData.totalConjunctions} APPROACHES
              </div>
            </div>

            {/* Top Threat Bullseye */}
            {computedData.sortedThreats[0] && (
              <div className="absolute bottom-5 right-5 z-10">
                <div className="relative w-28 h-28">
                  <div className="absolute inset-0 border border-[#4fdbc8]/20 rounded-full" />
                  <div className="absolute inset-4 border border-[#4fdbc8]/40 rounded-full" />
                  <div className="absolute inset-8 border border-[#4fdbc8]/60 rounded-full flex items-center justify-center">
                    <div className="w-2 h-2 bg-[#ffb4ab] rounded-full shadow-[0_0_10px_#ffb4ab]" />
                  </div>
                  <span className="absolute -top-6 left-1/2 -translate-x-1/2 text-[0.65rem] text-[#bbcac6] font-mono">
                    {Math.round(computedData.sortedThreats[0]?.predicted_miss_distance_m ?? 0)}m
                  </span>
                </div>
              </div>
            )}

            {/* Decision Explanation Bubble */}
            {decisionExplanation && (
              <div className="absolute bottom-5 left-5 max-w-xs glass-panel p-4 rounded-xl z-10 animate-scaleIn">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-[#4fdbc8]">🧠</span>
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

            {/* 3D Dashboard Link */}
            <Link 
              to="/dashboard"
              className="absolute top-5 right-5 z-10 bg-[#1a1d26]/80 backdrop-blur px-4 py-2 rounded-lg text-xs font-semibold text-[#4fdbc8] hover:bg-[#272a31] transition-all flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-sm">3d_rotation</span>
              3D View
            </Link>
          </div>

          {/* Live Maneuver Timeline */}
          <ManeuverTimeline 
            maneuvers={computedData.maneuvers} 
            sequences={computedData.sequences} 
          />

          {/* Simulation Control */}
          <button
            onClick={handleSimulationStep}
            disabled={simulating}
            className={`
              w-full py-4 rounded-xl font-semibold text-sm transition-all duration-200
              ${simulating 
                ? 'bg-[#272a31] text-[#6c7086] cursor-wait' 
                : 'btn-primary'
              }
            `}
          >
            {simulating ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-4 h-4 border-2 border-[#6c7086] border-t-transparent rounded-full animate-spin" />
                Simulating...
              </span>
            ) : (
              'Step Simulation (+60s)'
            )}
          </button>
        </main>

        {/* RIGHT COLUMN: Metrics & Logs */}
        <aside className="lg:col-span-3 flex flex-col gap-5 animate-slideInRight">
          {/* Fuel Status */}
          <Card padding="normal">
            <div className="flex justify-between items-center mb-3">
              <span className="text-xs uppercase font-bold text-[#6c7086]">Fleet Fuel Status</span>
              <span className="text-[#4fdbc8] text-lg">⛽</span>
            </div>
            <div className="flex items-end gap-2 mb-3">
              <span className="text-3xl font-bold text-[#e1e2eb] metric-value">{computedData.fuelPct}%</span>
              <span className="text-[#a0d0c6] text-xs pb-1 font-semibold">NOMINAL</span>
            </div>
            <ProgressBar 
              value={computedData.fuelPct} 
              max={100} 
              color="#4fdbc8" 
              height="normal"
            />
          </Card>

          {/* Per-Satellite Fuel Bars */}
          <FuelStatusPanel satellites={computedData.satellites} />

          {/* Decision Log Panel */}
          <DecisionLogPanel decisions={decisions} decisionStats={decisionStats} />

          {/* Event Log */}
          <EventLog events={computedData.events} />
        </aside>
      </div>
    </PageLayout>
  );
}

// Status Card Component
function StatusCard({ label, value, accent = false, critical = false, fuel = false }) {
  let colorClass = 'text-[#e1e2eb]';
  let borderClass = 'border-[#2a2f3a]';
  
  if (accent) {
    colorClass = 'text-[#4fdbc8]';
    borderClass = 'border-l-4 border-l-[#4fdbc8] border-[#2a2f3a]';
  } else if (critical) {
    colorClass = 'text-[#ffb4ab]';
    borderClass = 'border-l-4 border-l-[#ffb4ab] border-[#2a2f3a]';
  } else if (fuel) {
    colorClass = 'text-[#a0d0c6]';
  }

  return (
    <div className={`bg-[#1a1d26] p-3 rounded-lg border ${borderClass} shadow-md hover:shadow-lg transition-shadow`}>
      <span className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#6c7086] block mb-1">
        {label}
      </span>
      <span className={`text-xl font-bold ${colorClass} metric-value`}>{value}</span>
    </div>
  );
}

// Threat Card Component
function ThreatCard({ threat, onClick, selected, dimmed = false }) {
  if (!threat) return null;

  const severityColors = {
    CRITICAL: { border: '#ffb4ab', bg: 'rgba(255, 180, 171, 0.15)', text: '#ffb4ab' },
    HIGH: { border: '#f38764', bg: 'rgba(243, 135, 100, 0.15)', text: '#f38764' },
    MEDIUM: { border: '#ffb59e', bg: 'rgba(255, 181, 158, 0.15)', text: '#ffb59e' },
    LOW: { border: '#a0d0c6', bg: 'rgba(160, 208, 198, 0.15)', text: '#a0d0c6' },
    WATCH: { border: '#bbcac6', bg: 'rgba(187, 202, 198, 0.15)', text: '#bbcac6' },
  };

  const colors = severityColors[threat?.severity] || severityColors.WATCH;
  const timeToTCA = threat?.time_to_tca != null ? Math.round(threat.time_to_tca / 60) : '--';

  return (
    <div
      onClick={onClick}
      className={`
        bg-[#1a1d26] p-3 rounded-lg border relative overflow-hidden cursor-pointer 
        transition-all duration-200 card-interactive
        ${selected ? 'border-[#4fdbc8] shadow-lg shadow-[#4fdbc8]/10' : 'border-[#2a2f3a]'}
        ${dimmed ? 'opacity-60' : ''}
      `}
    >
      <div className="absolute top-0 left-0 w-1 h-full" style={{ background: colors.border }} />
      
      <div className="flex justify-between items-start mb-2 pl-2">
        <span className="text-xs font-bold text-[#e1e2eb] truncate">
          {threat?.satellite_id || 'Unknown'} ↔ {threat?.secondary_id || 'Unknown'}
        </span>
        <StatusBadge status={threat?.severity || 'UNKNOWN'} size="small" />
      </div>
      
      <div className="pl-2 space-y-0.5">
        <div className="text-[0.6875rem] text-[#bbcac6]">
          Miss: <span className="text-[#e1e2eb] font-mono">{Math.round(threat?.predicted_miss_distance_m ?? 0)}m</span>
        </div>
        <div className="text-[0.6875rem] text-[#bbcac6]">
          TCA: <span className="text-[#e1e2eb] font-mono">{timeToTCA === '--' ? '--' : `${timeToTCA}min`}</span>
        </div>
      </div>
    </div>
  );
}

// Maneuver Timeline Component
function ManeuverTimeline({ maneuvers = [], sequences = [] }) {
  const allManeuvers = useMemo(() => {
    const combined = [...(Array.isArray(maneuvers) ? maneuvers : [])];
    
    (Array.isArray(sequences) ? sequences : []).forEach(seq => {
      if (seq?.evasion_maneuver) combined.push(seq.evasion_maneuver);
      if (seq?.recovery_maneuver) combined.push(seq.recovery_maneuver);
    });

    return combined
      .filter(m => m?.scheduled_time != null)
      .sort((a, b) => new Date(a.scheduled_time) - new Date(b.scheduled_time))
      .slice(0, 6);
  }, [maneuvers, sequences]);

  const totalCount = maneuvers.length + sequences.reduce((acc, s) => 
    acc + (s?.evasion_maneuver ? 1 : 0) + (s?.recovery_maneuver ? 1 : 0), 0);

  return (
    <Card padding="normal">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-xs uppercase tracking-[0.05em] font-bold text-[#e1e2eb]">
          Planned Maneuvers
        </h3>
        <span className="text-[#4fdbc8] text-xs font-semibold">{totalCount} total</span>
      </div>
      
      {allManeuvers.length > 0 ? (
        <div className="space-y-2 max-h-[200px] overflow-y-auto pr-1 -mr-1">
          {allManeuvers.map((m, idx) => {
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
                className="bg-[#0b0e14] p-3 rounded-lg border-l-2 transition-colors hover:bg-[#0f1218]"
                style={{ borderColor: colors.bg }}
              >
                <div className="flex items-center justify-between mb-1">
                  <span
                    className="px-2 py-0.5 rounded text-[0.6rem] font-bold uppercase"
                    style={{ background: colors.bg, color: colors.text }}
                  >
                    {m?.type || 'UNKNOWN'}
                  </span>
                  <span className="text-[0.6rem] text-[#bbcac6]">{m?.state || 'PENDING'}</span>
                </div>
                <div className="text-[0.6875rem] text-[#e1e2eb] font-medium mb-1">
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
        <EmptyState 
          icon="📅" 
          title="No maneuvers scheduled" 
          description="The system will plan maneuvers as needed"
        />
      )}
    </Card>
  );
}

// Fuel Status Panel Component
function FuelStatusPanel({ satellites = [] }) {
  const topSatellites = useMemo(() => 
    (Array.isArray(satellites) ? satellites : []).slice(0, 5), 
  [satellites]);

  return (
    <Card padding="normal">
      <h3 className="text-xs uppercase tracking-[0.05em] font-bold text-[#e1e2eb] mb-4">
        Per-Satellite Fuel
      </h3>
      <div className="space-y-3">
        {topSatellites.length > 0 ? (
          topSatellites.map((sat, idx) => {
            const fuelPct = (sat?.total_fuel_capacity_kg || 0) > 0
              ? Math.round(((sat?.fuel_kg || 0) / sat.total_fuel_capacity_kg) * 100)
              : 0;
            const statusColor =
              sat?.fuel_status === 'CRITICAL' ? '#ffb4ab' :
              sat?.fuel_status === 'LOW' ? '#ffb59e' : '#4fdbc8';

            return (
              <div key={idx} className="flex items-center gap-3">
                <div
                  className="w-2 h-2 rounded-full flex-shrink-0"
                  style={{ background: statusColor, boxShadow: `0 0 8px ${statusColor}66` }}
                />
                <div className="flex-1 min-w-0">
                  <div className="flex justify-between text-[0.6875rem] mb-1">
                    <span className="text-[#e1e2eb] truncate">{sat?.satellite_id || 'Unknown'}</span>
                    <span className="text-[#bbcac6] font-mono ml-2">{fuelPct}%</span>
                  </div>
                  <ProgressBar value={fuelPct} max={100} color={statusColor} height="small" />
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-[0.6875rem] text-[#bbcac6]/50 text-center py-4">
            No satellite data available
          </div>
        )}
      </div>
    </Card>
  );
}

// Event Log Component
function EventLog({ events = [] }) {
  const recentEvents = useMemo(() => 
    (Array.isArray(events) ? events : []).slice(0, 12), 
  [events]);

  return (
    <Card variant="dark" padding="normal" className="flex-1 flex flex-col">
      <h3 className="text-xs uppercase tracking-[0.05em] font-bold text-[#e1e2eb] mb-4">
        Event History <span className="text-[#bbcac6] font-normal">({events.length})</span>
      </h3>
      <div className="space-y-1 overflow-y-auto max-h-[300px] pr-1 -mr-1 flex-1">
        {recentEvents.length > 0 ? (
          recentEvents.map((event, idx) => (
            <div 
              key={event?.id || idx} 
              className="py-2 border-b border-[#3c4947]/10 last:border-0"
            >
              <div className="text-[0.7rem] font-semibold text-[#4fdbc8] mb-0.5">
                {event?.event_type || 'unknown'}
              </div>
              <div className="text-[0.65rem] text-[#bbcac6] leading-relaxed line-clamp-2">
                {event?.message || 'No message'}
              </div>
            </div>
          ))
        ) : (
          <EmptyState icon="📋" title="No events yet" />
        )}
      </div>
    </Card>
  );
}

// Decision Log Panel Component
function DecisionLogPanel({ decisions = [], decisionStats = {} }) {
  const recentDecisions = useMemo(() => 
    (Array.isArray(decisions) ? decisions : []).slice(0, 6), 
  [decisions]);

  const totalDecisions = decisionStats?.total_decisions || 0;
  const maneuverScheduled = decisionStats?.maneuvers_scheduled || 0;
  const deferred = decisionStats?.decisions_deferred || 0;
  const skipped = decisionStats?.threats_skipped || 0;

  const decisionTypeColors = {
    maneuver_scheduled: { bg: '#4fdbc8', text: '#003731', icon: '✓' },
    deferred: { bg: '#ffb59e', text: '#1a1d26', icon: '⏸' },
    skipped: { bg: '#bbcac6', text: '#1a1d26', icon: '⊘' },
  };

  return (
    <Card padding="normal">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xs uppercase tracking-[0.05em] font-bold text-[#e1e2eb]">
          Decision Intelligence
        </h3>
        <span className="text-[#4fdbc8] text-lg">🧠</span>
      </div>

      {/* Decision Statistics */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="bg-[#0b0e14] p-2 rounded text-center">
          <div className="text-[0.6rem] text-[#bbcac6]">Scheduled</div>
          <div className="text-base font-bold text-[#4fdbc8] metric-value">{maneuverScheduled}</div>
        </div>
        <div className="bg-[#0b0e14] p-2 rounded text-center">
          <div className="text-[0.6rem] text-[#bbcac6]">Deferred</div>
          <div className="text-base font-bold text-[#ffb59e] metric-value">{deferred}</div>
        </div>
        <div className="bg-[#0b0e14] p-2 rounded text-center">
          <div className="text-[0.6rem] text-[#bbcac6]">Skipped</div>
          <div className="text-base font-bold text-[#bbcac6] metric-value">{skipped}</div>
        </div>
      </div>

      {/* Recent Decisions List */}
      <div className="space-y-2 max-h-[180px] overflow-y-auto pr-1 -mr-1">
        {recentDecisions.length > 0 ? (
          recentDecisions.map((decision, idx) => {
            const decisionType = decision?.maneuver_planned ? 'maneuver_scheduled' : 
                                decision?.deferred_reason ? 'deferred' : 'skipped';
            const colors = decisionTypeColors[decisionType] || decisionTypeColors.skipped;
            const timestamp = decision?.sim_time ? 
              `T+${Math.round(decision.sim_time)}s` : '--';

            return (
              <div
                key={decision?.decision_id || idx}
                className="bg-[#0b0e14] p-2 rounded-lg border-l-2"
                style={{ borderColor: colors.bg }}
              >
                <div className="flex items-start justify-between mb-1">
                  <div className="flex items-center gap-2">
                    <span
                      className="px-1.5 py-0.5 rounded text-[0.55rem] font-bold"
                      style={{ background: colors.bg, color: colors.text }}
                    >
                      {colors.icon}
                    </span>
                    <span className="text-[0.65rem] text-[#e1e2eb] font-medium">
                      {decision?.satellite_id || 'Unknown'}
                    </span>
                  </div>
                  <span className="text-[0.55rem] text-[#bbcac6] font-mono">{timestamp}</span>
                </div>
                {decision?.maneuver_planned && (
                  <div className="text-[0.55rem] text-[#4fdbc8] mt-1">
                    ΔV: {decision?.delta_v_ms?.toFixed(2) || 'N/A'} m/s
                  </div>
                )}
                {decision?.deferred_reason && (
                  <div className="text-[0.55rem] text-[#ffb59e] mt-1 truncate">
                    {decision.deferred_reason}
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
            Total: <span className="font-bold text-[#e1e2eb]">{totalDecisions}</span>
          </span>
        </div>
      )}
    </Card>
  );
}
