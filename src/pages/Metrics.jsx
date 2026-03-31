import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  fetchSystemSummary,
  fetchDecisionStats,
  fetchHistoricalStats,
  fetchFuelStatus,
  fetchAvoidanceStatus,
} from '../services/api';

export default function Metrics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  // Load initial data
  useEffect(() => {
    loadData();
  }, []);

  // Poll for updates every 10 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      loadData();
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  async function loadData() {
    try {
      const [summary, decisionStats, historyStats, fuelStatus, avoidanceStatus] = await Promise.all([
        fetchSystemSummary().catch(() => ({})),
        fetchDecisionStats().catch(() => ({})),
        fetchHistoricalStats().catch(() => ({})),
        fetchFuelStatus().catch(() => ({ satellites: [] })),
        fetchAvoidanceStatus().catch(() => ({ enabled: false })),
      ]);

      setData({
        summary,
        decisionStats,
        historyStats,
        fuelStatus,
        avoidanceStatus,
      });
      setLoading(false);
    } catch (error) {
      console.error('Failed to load metrics data:', error);
      setLoading(false);
    }
  }

  if (loading || !data) {
    return (
      <div className="min-h-screen bg-[#10131a] flex items-center justify-center">
        <div className="text-[#4fdbc8] text-xl">Loading Metrics...</div>
      </div>
    );
  }

  const {
    summary = {},
    decisionStats = {},
    historyStats = {},
    fuelStatus = { satellites: [] },
    avoidanceStatus = {},
  } = data;

  // Extract verified metrics only
  const systemMode = avoidanceStatus?.enabled ? 'AUTONOMOUS' : 'MANUAL';
  const satelliteCount = summary?.constellation?.total_satellites || 0;
  const debrisCount = summary?.constellation?.total_debris || 0;
  const fuelRemaining = summary?.fuel?.constellation_fuel_fraction || 0;

  // Decision statistics
  const totalDecisions = decisionStats?.total_decisions || 0;
  const decisionsByAction = decisionStats?.decisions_by_action || {};
  const maneuversScheduled = decisionsByAction?.maneuver_scheduled || 0;
  const deferred = decisionsByAction?.deferred || 0;
  const skipped = decisionsByAction?.skipped || 0;

  // Fuel analysis
  const satellites = Array.isArray(fuelStatus?.satellites) ? fuelStatus.satellites : [];
  const criticalFuelSatellites = satellites.filter(s => s?.fuel_status === 'CRITICAL').length;
  const lowFuelSatellites = satellites.filter(s => s?.fuel_status === 'LOW').length;

  // History stats (from events_by_type)
  const totalEvents = historyStats?.total_events || 0;
  const eventsByType = historyStats?.events_by_type || {};
  const totalManeuvers = (eventsByType?.maneuver_executed || 0) + (eventsByType?.maneuver_failed || 0);
  const totalConjunctions = eventsByType?.conjunction_detected || 0;

  return (
    <div className="min-h-screen bg-[#10131a] text-[#e1e2eb] antialiased selection:bg-[#4fdbc8] selection:text-[#003731]">
      {/* Top Nav Bar */}
      <nav className="fixed top-0 w-full z-50 bg-[#1d2026]/80 backdrop-blur-xl border-b border-[#4fdbc8]/15 shadow-[0_24px_48px_rgba(0,0,0,0.4)]">
        <div className="flex justify-between items-center h-16 px-8 max-w-[1440px] mx-auto font-['Inter'] antialiased tracking-tight">
          <div className="text-xl font-semibold tracking-[-0.02em] text-[#e1e2eb]">
            Prabanja Chitra
          </div>
          <div className="hidden md:flex items-center gap-8">
            <Link to="/home" className="text-[#e1e2eb]/70 hover:text-[#e1e2eb] transition-colors">
              Home
            </Link>
            <Link to="/mission-control" className="text-[#e1e2eb]/70 hover:text-[#e1e2eb] transition-colors">
              Mission Control
            </Link>
            <Link to="/metrics" className="text-[#4fdbc8] border-b-2 border-[#4fdbc8] pb-1 font-bold">
              Metrics
            </Link>
            <Link to="/architecture" className="text-[#e1e2eb]/70 hover:text-[#e1e2eb] transition-colors">
              Architecture
            </Link>
          </div>
          <Link
            to="/dashboard"
            className="bg-[#4fdbc8] text-[#003731] px-5 py-2 rounded-xl text-sm font-semibold hover:bg-[#14b8a6] transition-all active:scale-95 duration-150 shadow-[0_0_15px_rgba(79,219,200,0.3)]"
          >
            Launch Dashboard
          </Link>
        </div>
      </nav>

      <main className="pt-24 pb-20 px-8 max-w-[1440px] mx-auto min-h-screen space-y-8">
        {/* Page Header */}
        <header className="flex flex-col md:flex-row md:items-end justify-between gap-4">
          <div>
            <label className="text-[0.6875rem] uppercase tracking-[0.05em] font-bold text-[#4fdbc8] mb-1 block">
              Live Operations
            </label>
            <h1 className="text-3xl font-extrabold tracking-tight text-[#e1e2eb]">
              Orbital Performance Metrics
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <span className="flex items-center gap-2 bg-[#272a31] px-3 py-1.5 rounded-lg text-[0.6875rem] font-bold uppercase tracking-wider text-[#bbcac6]">
              <span className="w-2 h-2 rounded-full bg-[#4fdbc8] animate-pulse"></span>
              {systemMode}
            </span>
            <span className="text-[#859490] text-xs">Real-time telemetry</span>
          </div>
        </header>

        {/* System Overview */}
        <section>
          <h2 className="text-sm font-bold uppercase tracking-widest text-[#bbcac6] mb-4">System Overview</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <MetricCard
              title="Active Satellites"
              value={satelliteCount}
              subtitle="Operational constellation"
              icon="🛰️"
              borderColor="#4fdbc8"
            />
            <MetricCard
              title="Debris Tracked"
              value={debrisCount}
              subtitle="Active monitoring"
              icon="🌌"
              borderColor="#4fdbc8"
            />
            <MetricCard
              title="Fleet Fuel"
              value={`${Math.round(fuelRemaining * 100)}%`}
              subtitle="Constellation remaining"
              icon="⛽"
              borderColor="#a0d0c6"
            />
          </div>
        </section>

        {/* Decision Analytics */}
        <section>
          <h2 className="text-sm font-bold uppercase tracking-widest text-[#bbcac6] mb-4">Decision Analytics</h2>
          <div className="bg-[#1a1d26] rounded-xl p-8 border border-[#2a2f3a] shadow-lg">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
              <div>
                <span className="block text-[0.6875rem] text-[#859490] uppercase tracking-wider mb-2">
                  Total Decisions
                </span>
                <span className="text-4xl font-bold text-[#e1e2eb]">{totalDecisions}</span>
              </div>
              <div>
                <span className="block text-[0.6875rem] text-[#859490] uppercase tracking-wider mb-2">
                  Maneuvers Scheduled
                </span>
                <span className="text-4xl font-bold text-[#4fdbc8]">{maneuversScheduled}</span>
              </div>
              <div>
                <span className="block text-[0.6875rem] text-[#859490] uppercase tracking-wider mb-2">
                  Deferred
                </span>
                <span className="text-4xl font-bold text-[#ffb59e]">{deferred}</span>
              </div>
              <div>
                <span className="block text-[0.6875rem] text-[#859490] uppercase tracking-wider mb-2">
                  Skipped
                </span>
                <span className="text-4xl font-bold text-[#bbcac6]">{skipped}</span>
              </div>
            </div>
          </div>
        </section>

        {/* Fuel Status */}
        <section>
          <h2 className="text-sm font-bold uppercase tracking-widest text-[#bbcac6] mb-4">Fuel Status</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-[#1a1d26] rounded-xl p-8 border border-[#2a2f3a] shadow-lg hover:shadow-xl hover:border-[#3a3f4a] transition-all">
              <div className="flex justify-between items-end mb-4">
                <span className="text-[0.6875rem] text-[#bbcac6] uppercase tracking-wider">
                  Fleet Fuel Remaining
                </span>
                <span className="text-3xl font-bold text-[#e1e2eb]">
                  {Math.round(fuelRemaining * 100)}%
                </span>
              </div>
              <div className="w-full h-4 bg-[#0b0e14] rounded-full overflow-hidden">
                <div
                  className="bg-gradient-to-r from-[#4fdbc8] to-[#a0d0c6] h-full rounded-full transition-all duration-500"
                  style={{ width: `${fuelRemaining * 100}%` }}
                ></div>
              </div>
            </div>
            <div className="bg-[#1a1d26] rounded-xl p-8 border border-[#2a2f3a] shadow-lg hover:shadow-xl hover:border-[#3a3f4a] transition-all">
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <span className="block text-[0.6875rem] text-[#859490] uppercase tracking-wider mb-2">
                    Critical Fuel
                  </span>
                  <span className="text-3xl font-bold text-[#ffb4ab]">{criticalFuelSatellites}</span>
                  <span className="block text-xs text-[#bbcac6] mt-1">satellites</span>
                </div>
                <div>
                  <span className="block text-[0.6875rem] text-[#859490] uppercase tracking-wider mb-2">
                    Low Fuel
                  </span>
                  <span className="text-3xl font-bold text-[#ffb59e]">{lowFuelSatellites}</span>
                  <span className="block text-xs text-[#bbcac6] mt-1">satellites</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Per-Satellite Fuel Details */}
        <section>
          <h2 className="text-sm font-bold uppercase tracking-widest text-[#bbcac6] mb-4">
            Per-Satellite Fuel Status
          </h2>
          <div className="bg-[#1a1d26] rounded-xl p-8 border border-[#2a2f3a] shadow-lg">
            <div className="space-y-5">
              {Array.isArray(satellites) && satellites.length > 0 ? (
                satellites.slice(0, 10).map((sat, idx) => {
                  const fuelKg = sat?.fuel_kg || 0;
                  const totalCapacity = sat?.total_fuel_capacity_kg || 1;
                  const fuelPct = totalCapacity > 0
                    ? Math.round((fuelKg / totalCapacity) * 100)
                    : 0;
                  const statusColor =
                    sat?.fuel_status === 'CRITICAL'
                      ? '#ffb4ab'
                      : sat?.fuel_status === 'LOW'
                      ? '#ffb59e'
                      : '#4fdbc8';

                  return (
                    <div key={idx} className="flex items-center gap-4 p-3 rounded-lg bg-[#10131a]/50 hover:bg-[#10131a] transition-colors">
                      <div
                        className="w-2 h-2 rounded-full flex-shrink-0"
                        style={{
                          background: statusColor,
                          boxShadow: `0 0 10px ${statusColor}88`,
                        }}
                      ></div>
                      <div className="flex-1">
                        <div className="flex justify-between text-sm mb-2">
                          <span className="font-semibold text-[#e1e2eb]">{sat?.satellite_id || 'Unknown'}</span>
                          <span className="text-[#bbcac6] font-mono text-xs">
                            {fuelPct}% ({fuelKg.toFixed(1)} / {totalCapacity.toFixed(1)} kg)
                          </span>
                        </div>
                        <div className="w-full h-2 bg-[#0b0e14] rounded-full overflow-hidden shadow-inner">
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
                <div className="text-center text-[#bbcac6] py-4">No satellite data available</div>
              )}
            </div>
          </div>
        </section>

        {/* Historical Summary */}
        <section>
          <h2 className="text-sm font-bold uppercase tracking-widest text-[#bbcac6] mb-4">Historical Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <MetricCard
              title="Total Events"
              value={totalEvents}
              subtitle="Mission log entries"
              icon="📋"
              borderColor="#4fdbc8"
            />
            <MetricCard
              title="Total Maneuvers"
              value={totalManeuvers}
              subtitle="Executed burns"
              icon="🚀"
              borderColor="#4fdbc8"
            />
            <MetricCard
              title="Conjunctions"
              value={totalConjunctions}
              subtitle="Detected approaches"
              icon="⚠️"
              borderColor="#ffb59e"
            />
          </div>
        </section>

        {/* Constellation Telemetry Banner */}
        <section className="w-full rounded-xl h-64 relative overflow-hidden bg-[#1a1d26] border border-[#2a2f3a] shadow-xl">
          <img
            alt="Orbital Visualization Background"
            className="w-full h-full object-cover mix-blend-overlay opacity-30"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuAXyt7cr5eVMYFKRopPUPbAC8Sc9q0UESeB_HN3tmEdCXNtucIz0syOh6BilyJZnqTi7AhuRz2QVX_uMsa3C4OktuqXij4uZtpf-QxL3jfjk87afjrwsFKUFprQPWBJMzCCcdznMNNiNWTUFiPc7vV-UReGKb75k5-LH8xPC9i1xytl1fINfMLnPY42l7-p1iJGjJQCIiTOg-g8zpDOi9JsgnDcbBQi_UFoW_EnyPMxRdHop5n26zakKI0LOyY3WBB5x6h8GhqfowZL"
          />
          <div className="absolute inset-0 flex flex-col items-center justify-center p-8 bg-gradient-to-t from-[#10131a] via-[#10131a]/70 to-transparent">
            <h3 className="text-2xl font-bold text-[#e1e2eb] mb-2">Constellation Operations</h3>
            <p className="text-[#bbcac6] text-sm mb-6 max-w-xl text-center leading-relaxed">
              Managing {satelliteCount} active satellites with real-time tracking of {debrisCount} debris objects.
              Autonomous collision avoidance system operational.
            </p>
            <div className="flex gap-4">
              <Link
                to="/mission-control"
                className="bg-[#272a31] text-[#e1e2eb] px-6 py-2.5 rounded-lg text-xs font-bold uppercase tracking-widest hover:bg-[#32353c] hover:shadow-lg transition-all border border-[#3a3f4a]"
              >
                View Operations
              </Link>
              <Link
                to="/dashboard"
                className="bg-[#4fdbc8] text-[#003731] px-6 py-2.5 rounded-lg text-xs font-bold uppercase tracking-widest hover:opacity-90 hover:shadow-lg hover:shadow-[#4fdbc8]/30 transition-all"
              >
                Launch Dashboard
              </Link>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-[#0b0e14] w-full py-12 border-t border-[#4fdbc8]/10">
        <div className="flex flex-col md:flex-row justify-between items-center px-12 max-w-[1440px] mx-auto gap-8 font-['Inter']">
          <div className="flex flex-col items-center md:items-start">
            <div className="text-lg font-bold text-[#e1e2eb] mb-2">Prabanja Chitra</div>
            <div className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#e1e2eb]/40">
              © 2024 Prabanja Chitra. Orbital Autonomy Initiative.
            </div>
          </div>
          <div className="flex gap-8">
            <a className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#e1e2eb]/40 hover:text-[#4fdbc8] transition-colors" href="#">
              Documentation
            </a>
            <a className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#e1e2eb]/40 hover:text-[#4fdbc8] transition-colors" href="#">
              Mission Logs
            </a>
            <a className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#e1e2eb]/40 hover:text-[#4fdbc8] transition-colors" href="#">
              Privacy
            </a>
            <a className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#e1e2eb]/40 hover:text-[#4fdbc8] transition-colors" href="#">
              Contact
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}

// Metric Card Component
function MetricCard({
  title,
  value,
  subtitle,
  icon,
  borderColor = '#4fdbc8',
  valueColor = '#e1e2eb',
}) {
  return (
    <div
      className="bg-[#1a1d26] rounded-xl p-6 relative overflow-hidden group border border-[#2a2f3a] shadow-lg hover:shadow-xl hover:border-[#3a3f4a] transition-all duration-300"
      style={{ borderLeft: `4px solid ${borderColor}` }}
    >
      <div className="flex justify-between items-start mb-4">
        <span className="text-[0.6875rem] font-bold uppercase tracking-widest text-[#6c7086] group-hover:text-[#bbcac6] transition-colors">
          {title}
        </span>
        <span className="text-2xl opacity-60 group-hover:opacity-100 transition-opacity">{icon}</span>
      </div>
      <div className="text-4xl font-extrabold tracking-tight mb-2" style={{ color: valueColor }}>
        {value}
      </div>
      <div className="flex items-center gap-1 text-xs text-[#6c7086] italic">
        <span>{subtitle}</span>
      </div>
    </div>
  );
}
