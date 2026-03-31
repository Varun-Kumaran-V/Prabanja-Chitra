import { useState, useEffect, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  PageLayout,
  Card,
  StatCard,
  SectionHeader,
  StatusBadge,
  ProgressBar,
  Skeleton,
} from '../components/shared';
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

  const loadData = useCallback(async () => {
    try {
      const [summary, decisionStats, historyStats, fuelStatus, avoidanceStatus] = await Promise.all([
        fetchSystemSummary().catch(() => ({})),
        fetchDecisionStats().catch(() => ({})),
        fetchHistoricalStats().catch(() => ({})),
        fetchFuelStatus().catch(() => ({ satellites: [] })),
        fetchAvoidanceStatus().catch(() => ({ enabled: false })),
      ]);

      setData({ summary, decisionStats, historyStats, fuelStatus, avoidanceStatus });
      setLoading(false);
    } catch (error) {
      console.error('Failed to load metrics data:', error);
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [loadData]);

  if (loading || !data) {
    return <MetricsSkeleton />;
  }

  // Computed metrics
  const metrics = useMemo(() => {
    const { summary = {}, decisionStats = {}, historyStats = {}, fuelStatus = { satellites: [] }, avoidanceStatus = {} } = data;

    return {
      systemMode: avoidanceStatus?.enabled ? 'AUTONOMOUS' : 'MANUAL',
      satelliteCount: summary?.constellation?.total_satellites || 0,
      debrisCount: summary?.constellation?.total_debris || 0,
      fuelRemaining: summary?.fuel?.constellation_fuel_fraction || 0,
      totalDecisions: decisionStats?.total_decisions || 0,
      maneuversScheduled: decisionStats?.decisions_by_action?.maneuver_scheduled || 0,
      deferred: decisionStats?.decisions_by_action?.deferred || 0,
      skipped: decisionStats?.decisions_by_action?.skipped || 0,
      satellites: Array.isArray(fuelStatus?.satellites) ? fuelStatus.satellites : [],
      totalEvents: historyStats?.total_events || 0,
      eventsByType: historyStats?.events_by_type || {},
    };
  }, [data]);

  const criticalFuelCount = metrics.satellites.filter(s => s?.fuel_status === 'CRITICAL').length;
  const lowFuelCount = metrics.satellites.filter(s => s?.fuel_status === 'LOW').length;
  const totalManeuvers = (metrics.eventsByType?.maneuver_executed || 0) + (metrics.eventsByType?.maneuver_failed || 0);
  const totalConjunctions = metrics.eventsByType?.conjunction_detected || 0;

  return (
    <PageLayout className="px-8 md:px-8 pb-20 space-y-8">
      {/* Page Header */}
      <SectionHeader
        label="Live Operations"
        title="Orbital Performance Metrics"
        action={
          <StatusBadge status={metrics.systemMode} pulse={true} />
        }
        className="animate-fadeInUp"
      />

      {/* System Overview */}
      <section className="animate-fadeInUp delay-100">
        <h2 className="text-sm font-bold uppercase tracking-widest text-[#bbcac6] mb-4">System Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatCard
            title="Active Satellites"
            value={metrics.satelliteCount}
            subtitle="Operational constellation"
            icon={<span className="material-symbols-outlined text-4xl">satellite</span>}
            accentColor="#4fdbc8"
          />
          <StatCard
            title="Debris Tracked"
            value={metrics.debrisCount}
            subtitle="Active monitoring"
            icon="🌌"
            accentColor="#4fdbc8"
          />
          <StatCard
            title="Fleet Fuel"
            value={`${Math.round(metrics.fuelRemaining * 100)}%`}
            subtitle="Constellation remaining"
            icon={<span className="material-symbols-outlined text-4xl">local_gas_station</span>}
            accentColor="#a0d0c6"
          />
        </div>
      </section>

      {/* Decision Analytics */}
      <section className="animate-fadeInUp delay-200">
        <h2 className="text-sm font-bold uppercase tracking-widest text-[#bbcac6] mb-4">Decision Analytics</h2>
        <Card padding="large" className="overflow-hidden">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <MetricNumber label="Total Decisions" value={metrics.totalDecisions} />
            <MetricNumber label="Maneuvers Scheduled" value={metrics.maneuversScheduled} color="#4fdbc8" />
            <MetricNumber label="Deferred" value={metrics.deferred} color="#ffb59e" />
            <MetricNumber label="Skipped" value={metrics.skipped} color="#bbcac6" />
          </div>
        </Card>
      </section>

      {/* Fuel Status */}
      <section className="animate-fadeInUp delay-300">
        <h2 className="text-sm font-bold uppercase tracking-widest text-[#bbcac6] mb-4">Fuel Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card padding="large" hover>
            <div className="flex justify-between items-end mb-4">
              <span className="text-xs text-[#bbcac6] uppercase tracking-wider">Fleet Fuel Remaining</span>
              <span className="text-3xl font-bold text-[#e1e2eb] metric-value">
                {Math.round(metrics.fuelRemaining * 100)}%
              </span>
            </div>
            <ProgressBar 
              value={metrics.fuelRemaining * 100} 
              max={100} 
              color="#4fdbc8" 
              height="large"
            />
          </Card>
          <Card padding="large" hover>
            <div className="grid grid-cols-2 gap-6">
              <div>
                <span className="block text-xs text-[#859490] uppercase tracking-wider mb-2">Critical Fuel</span>
                <span className="text-3xl font-bold text-[#ffb4ab] metric-value">{criticalFuelCount}</span>
                <span className="block text-xs text-[#bbcac6] mt-1">satellites</span>
              </div>
              <div>
                <span className="block text-xs text-[#859490] uppercase tracking-wider mb-2">Low Fuel</span>
                <span className="text-3xl font-bold text-[#ffb59e] metric-value">{lowFuelCount}</span>
                <span className="block text-xs text-[#bbcac6] mt-1">satellites</span>
              </div>
            </div>
          </Card>
        </div>
      </section>

      {/* Per-Satellite Fuel Details */}
      <section className="animate-fadeInUp delay-400">
        <h2 className="text-sm font-bold uppercase tracking-widest text-[#bbcac6] mb-4">Per-Satellite Fuel Status</h2>
        <Card padding="large">
          <div className="space-y-4">
            {metrics.satellites.length > 0 ? (
              metrics.satellites.slice(0, 10).map((sat, idx) => {
                const fuelKg = sat?.fuel_kg || 0;
                const totalCapacity = sat?.total_fuel_capacity_kg || 1;
                const fuelPct = totalCapacity > 0 ? Math.round((fuelKg / totalCapacity) * 100) : 0;
                const statusColor = sat?.fuel_status === 'CRITICAL' ? '#ffb4ab' :
                                   sat?.fuel_status === 'LOW' ? '#ffb59e' : '#4fdbc8';

                return (
                  <div key={idx} className="flex items-center gap-6 p-3 rounded-lg bg-[#10131a]/50 hover:bg-[#10131a] transition-colors">
                    <div
                      className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                      style={{ background: statusColor, boxShadow: `0 0 10px ${statusColor}88` }}
                    />
                    <div className="flex-1">
                      <div className="flex justify-between text-sm mb-2">
                        <span className="font-semibold text-[#e1e2eb]">{sat?.satellite_id || 'Unknown'}</span>
                        <span className="text-[#bbcac6] font-mono text-xs">
                          {fuelPct}% ({fuelKg.toFixed(1)} / {totalCapacity.toFixed(1)} kg)
                        </span>
                      </div>
                      <ProgressBar value={fuelPct} max={100} color={statusColor} height="small" />
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="text-center text-[#bbcac6] py-8">No satellite data available</div>
            )}
          </div>
        </Card>
      </section>

      {/* Historical Summary */}
      <section className="animate-fadeInUp delay-500">
        <h2 className="text-sm font-bold uppercase tracking-widest text-[#bbcac6] mb-4">Historical Summary</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StatCard
            title="Total Events"
            value={metrics.totalEvents}
            subtitle="Mission log entries"
            icon={<span className="material-symbols-outlined text-4xl">list_alt</span>}
            accentColor="#4fdbc8"
          />
          <StatCard
            title="Total Maneuvers"
            value={totalManeuvers}
            subtitle="Executed burns"
            icon={<span className="material-symbols-outlined inline-block align-middle">rocket_launch</span>}
            accentColor="#4fdbc8"
          />
          <StatCard
            title="Conjunctions"
            value={totalConjunctions}
            subtitle="Detected approaches"
            icon={<span className="material-symbols-outlined text-4xl">error</span>}
            accentColor="#ffb59e"
          />
        </div>
      </section>

      {/* Constellation Operations Banner */}
      <section className="w-full rounded-xl h-64 relative overflow-hidden bg-gradient-to-br from-[#1a1d26] to-[#0b0e14] border border-[#2a2f3a] shadow-xl animate-fadeInUp delay-600">
        <div className="absolute inset-0 gradient-radial-accent opacity-30" />
        <div className="absolute inset-0 flex flex-col items-center justify-center p-8">
          <h3 className="text-2xl font-bold text-[#e1e2eb] mb-2">Constellation Operations</h3>
          <p className="text-[#bbcac6] text-sm mb-10 max-w-xl text-center leading-relaxed">
            Managing {metrics.satelliteCount} active satellites with real-time tracking of {metrics.debrisCount} debris objects.
            Autonomous collision avoidance system operational.
          </p>
          <div className="flex gap-6">
            <Link to="/mission-control" className="btn-secondary px-8 py-2.5 text-xs font-bold uppercase tracking-widest">
              View Operations
            </Link>
            <Link to="/dashboard" className="btn-primary px-8 py-2.5 text-xs font-bold uppercase tracking-widest">
              Launch Dashboard
            </Link>
          </div>
        </div>
      </section>
    </PageLayout>
  );
}

// Metric Number Component
function MetricNumber({ label, value, color = '#e1e2eb' }) {
  return (
    <div>
      <span className="block text-xs text-[#859490] uppercase tracking-wider mb-2">{label}</span>
      <span className="text-4xl font-bold metric-value" style={{ color }}>{value}</span>
    </div>
  );
}

// Metrics Skeleton Component
function MetricsSkeleton() {
  return (
    <PageLayout className="px-8 md:px-8 pb-20 space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <Skeleton className="h-4 w-24 mb-2" />
          <Skeleton className="h-10 w-64" />
        </div>
        <Skeleton className="h-8 w-32" />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {[1, 2, 3].map(i => (
          <Card key={i} padding="large">
            <Skeleton className="h-4 w-32 mb-4" />
            <Skeleton className="h-10 w-20 mb-2" />
            <Skeleton className="h-3 w-40" />
          </Card>
        ))}
      </div>
      <Card padding="large">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {[1, 2, 3, 4].map(i => (
            <div key={i}>
              <Skeleton className="h-3 w-24 mb-2" />
              <Skeleton className="h-10 w-16" />
            </div>
          ))}
        </div>
      </Card>
    </PageLayout>
  );
}
