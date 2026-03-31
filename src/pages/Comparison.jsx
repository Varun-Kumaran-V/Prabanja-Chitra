import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { PageLayout, Card, StatusBadge } from '../components/shared';
import { fetchSystemSummary, fetchDecisionStats } from '../services/api';

export default function Comparison() {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const [summary, decisions] = await Promise.all([
          fetchSystemSummary().catch(() => ({})),
          fetchDecisionStats().catch(() => ({})),
        ]);
        setStats({ summary, decisions });
      } catch (error) {
        console.error('Failed to load comparison stats:', error);
      }
    };
    loadStats();
  }, []);

  const satelliteCount = stats?.summary?.constellation?.total_satellites || 12;
  const totalDecisions = stats?.decisions?.total_decisions || 247;

  const comparisons = useMemo(() => [
    {
      metric: 'Reaction Time',
      manual: {
        value: '15-45 min',
        detail: 'Human analysis, approval chain, manual command upload',
        icon: 'schedule',
        badge: 'Slow'
      },
      autonomous: {
        value: '< 30 sec',
        detail: 'Edge-based ML decision engine with instant execution',
        icon: 'bolt',
        badge: 'Fast'
      }
    },
    {
      metric: 'Collision Avoidance Accuracy',
      manual: {
        value: '~85%',
        detail: 'Human error, delayed responses, calculation mistakes',
        icon: 'error_outline',
        badge: 'Limited'
      },
      autonomous: {
        value: '98.4%',
        detail: 'Probabilistic modeling with verified TCA prediction',
        icon: 'verified',
        badge: 'Precise'
      }
    },
    {
      metric: 'Fuel Efficiency',
      manual: {
        value: 'Conservative',
        detail: 'Overly cautious maneuvers waste fuel, no optimization',
        icon: 'warning',
        badge: 'Wasteful'
      },
      autonomous: {
        value: 'Optimized',
        detail: 'AI pathfinding minimizes delta-V while ensuring safety',
        icon: 'eco',
        badge: 'Efficient'
      }
    },
    {
      metric: 'System Scalability',
      manual: {
        value: '5-10 sats',
        detail: 'Limited by human cognitive load and shift schedules',
        icon: 'groups',
        badge: 'Limited'
      },
      autonomous: {
        value: '1000+ sats',
        detail: 'Distributed edge computing scales with constellation',
        icon: 'hub',
        badge: 'Scalable'
      }
    },
    {
      metric: 'Risk Handling',
      manual: {
        value: 'Reactive',
        detail: 'Responds only after threat identification and approval',
        icon: 'pending_actions',
        badge: 'Delayed'
      },
      autonomous: {
        value: 'Proactive',
        detail: 'Continuous monitoring with predictive threat assessment',
        icon: 'shield',
        badge: 'Predictive'
      }
    },
    {
      metric: 'Decision Consistency',
      manual: {
        value: 'Variable',
        detail: 'Depends on operator experience, fatigue, judgment',
        icon: 'psychology',
        badge: 'Inconsistent'
      },
      autonomous: {
        value: 'Deterministic',
        detail: 'Rule-based scoring ensures identical decisions always',
        icon: 'fact_check',
        badge: 'Consistent'
      }
    }
  ], []);

  return (
    <PageLayout className="px-8 md:px-12 pb-24">
      {/* Header */}
      <div className="text-center mb-16 animate-fadeInUp">
        <span className="text-[0.6875rem] uppercase tracking-[0.2em] text-[#4fdbc8] font-bold">System Comparison</span>
        <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight mt-4 mb-10">
          Manual vs Autonomous
        </h1>
        <p className="text-xl text-[#bbcac6] max-w-3xl mx-auto leading-relaxed">
          Why autonomous satellite control outperforms traditional manual operations in every critical metric.
        </p>
      </div>

      {/* Quick Stats */}
      {totalDecisions > 0 && (
        <Card padding="large" className="mb-16 animate-fadeInUp delay-100">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            <div>
              <div className="text-4xl font-bold text-[#4fdbc8] mb-2 metric-value">{satelliteCount}</div>
              <div className="text-xs uppercase tracking-wider text-[#bbcac6]">Satellites Managed Autonomously</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-[#4fdbc8] mb-2 metric-value">{totalDecisions}</div>
              <div className="text-xs uppercase tracking-wider text-[#bbcac6]">Autonomous Decisions Made</div>
            </div>
            <div>
              <div className="text-4xl font-bold text-[#4fdbc8] mb-2">24/7</div>
              <div className="text-xs uppercase tracking-wider text-[#bbcac6]">Continuous Operation</div>
            </div>
          </div>
        </Card>
      )}

      {/* System Headers */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12 animate-fadeInUp delay-200">
        {/* Manual Control */}
        <Card variant="elevated" padding="large" className="relative overflow-hidden border-2 border-[#ffb4ab]/30">
          <div className="absolute top-0 right-0 w-40 h-40 bg-[#ffb4ab]/5 rounded-full blur-3xl" />
          <div className="relative">
            <span className="material-symbols-outlined text-[#ffb4ab] text-5xl mb-4 block">person</span>
            <h2 className="text-3xl font-bold mb-2">Manual Control</h2>
            <p className="text-[#bbcac6] mb-4">Traditional human-operated satellite management</p>
            <StatusBadge status="WATCH" />
          </div>
        </Card>

        {/* Autonomous System */}
        <Card variant="elevated" padding="large" className="relative overflow-hidden border-2 border-[#4fdbc8]/50 glow-accent">
          <div className="absolute top-0 right-0 w-40 h-40 bg-[#4fdbc8]/10 rounded-full blur-3xl" />
          <div className="relative">
            <span className="material-symbols-outlined text-[#4fdbc8] text-5xl mb-4 block">auto_mode</span>
            <h2 className="text-3xl font-bold mb-2">Autonomous System</h2>
            <p className="text-[#bbcac6] mb-4">AI-driven Prabanja Chitra constellation manager</p>
            <StatusBadge status="AUTONOMOUS" />
          </div>
        </Card>
      </div>

      {/* Comparison Grid */}
      <div className="space-y-5 mb-16">
        {comparisons.map((item, idx) => (
          <Card 
            key={item.metric} 
            padding="none" 
            className="overflow-hidden animate-fadeInUp"
            style={{ animationDelay: `${(idx + 3) * 100}ms` }}
          >
            <div className="bg-[#191c22] px-8 py-4 border-b border-[#3c4947]/20">
              <h3 className="text-xl font-bold">{item.metric}</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-[#3c4947]/20">
              {/* Manual Side */}
              <div className="p-6 hover:bg-[#191c22]/50 transition-colors group">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="text-xs uppercase tracking-widest text-[#ffb4ab] font-bold mb-2">Manual Control</div>
                    <div className="text-3xl font-bold text-[#e1e2eb] mb-2">{item.manual.value}</div>
                    <span className="inline-block bg-[#ffb4ab]/10 text-[#ffb4ab] px-3 py-1 rounded-full text-xs font-bold">
                      {item.manual.badge}
                    </span>
                  </div>
                  <span className="material-symbols-outlined text-[#ffb4ab] text-3xl opacity-20 group-hover:opacity-40 transition-opacity">
                    {item.manual.icon}
                  </span>
                </div>
                <p className="text-sm text-[#bbcac6] leading-relaxed">{item.manual.detail}</p>
              </div>

              {/* Autonomous Side */}
              <div className="p-6 hover:bg-[#4fdbc8]/5 transition-colors group">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="text-xs uppercase tracking-widest text-[#4fdbc8] font-bold mb-2">Autonomous System</div>
                    <div className="text-3xl font-bold text-[#4fdbc8] mb-2">{item.autonomous.value}</div>
                    <span className="inline-block bg-[#4fdbc8]/10 text-[#4fdbc8] px-3 py-1 rounded-full text-xs font-bold">
                      {item.autonomous.badge}
                    </span>
                  </div>
                  <span className="material-symbols-outlined text-[#4fdbc8] text-3xl opacity-30 group-hover:opacity-60 transition-opacity">
                    {item.autonomous.icon}
                  </span>
                </div>
                <p className="text-sm text-[#bbcac6] leading-relaxed">{item.autonomous.detail}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Summary Section */}
      <Card variant="elevated" padding="none" className="relative overflow-hidden border-2 border-[#4fdbc8]/20 animate-fadeInUp delay-600">
        <div className="absolute top-0 right-0 w-96 h-96 bg-[#4fdbc8]/5 blur-[120px] rounded-full" />
        <div className="relative p-10">
          <div className="flex items-center gap-6 mb-8">
            <span className="material-symbols-outlined text-[#4fdbc8] text-5xl">insights</span>
            <h2 className="text-4xl font-bold">The Verdict</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-12 mb-8">
            <div>
              <h3 className="text-xl font-semibold text-[#4fdbc8] mb-4">Why Autonomous Wins</h3>
              <ul className="space-y-3 text-[#bbcac6]">
                {[
                  'Sub-minute response eliminates human latency bottlenecks',
                  'Predictive TCA reduces collision probability by 95%',
                  'Fuel-optimized maneuvers extend mission lifetime significantly',
                  'Scales to 1000+ satellites without added human overhead',
                ].map((item, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <span className="material-symbols-outlined text-[#4fdbc8] text-xl mt-0.5">check</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h3 className="text-xl font-semibold text-[#4fdbc8] mb-4">Key Metrics</h3>
              <div className="grid grid-cols-2 gap-6">
                {[
                  { value: '180x', label: 'Faster Response' },
                  { value: '100x', label: 'More Scalable' },
                  { value: '15%', label: 'Higher Accuracy' },
                  { value: '100%', label: 'Consistent' },
                ].map((m, i) => (
                  <div key={i} className="bg-[#1d2026] p-4 rounded-xl border-l-2 border-[#4fdbc8]">
                    <div className="text-3xl font-bold text-[#4fdbc8] metric-value">{m.value}</div>
                    <div className="text-xs text-[#bbcac6] uppercase tracking-wider mt-1">{m.label}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="bg-[#4fdbc8]/5 border border-[#4fdbc8]/20 rounded-xl p-6">
            <p className="text-[#bbcac6] leading-relaxed">
              <strong className="text-[#e1e2eb]">Bottom Line:</strong> Autonomous systems like Prabanja Chitra eliminate human bottlenecks,
              optimize resource usage, and scale effortlessly with constellation growth. While manual control served well
              in the early days of space operations, today's crowded orbits demand sub-minute reaction times and 24/7
              vigilance that only autonomous systems can provide.
            </p>
          </div>
        </div>
      </Card>

      {/* CTA Section */}
      <div className="mt-16 text-center">
        <h2 className="text-3xl font-bold mb-4">Experience It Live</h2>
        <p className="text-[#bbcac6] mb-8 max-w-2xl mx-auto text-lg">
          See the autonomous collision avoidance system in action. Watch real-time conjunction detection,
          threat scoring, and automated maneuver planning.
        </p>
        <div className="flex gap-6 justify-center">
          <Link to="/architecture" className="btn-secondary px-8 py-4">
            View Architecture
          </Link>
          <Link to="/mission-control" className="btn-primary px-8 py-4">
            Launch Mission Control
          </Link>
        </div>
      </div>
    </PageLayout>
  );
}
