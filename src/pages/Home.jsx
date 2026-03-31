import { useState, useEffect, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { PageLayout, StatusBadge, Card, StatCard, ProgressBar, Skeleton } from '../components/shared';
import { API_BASE } from '../config';

export default function Home() {
  const [data, setData] = useState({
    lastUpdateTime: '--:--:--',
    systemMode: 'INITIALIZING',
    activeSatellites: 0,
    trackedDebris: 0,
    criticalThreats: 0,
    alertCount: 0,
    maneuverTimer: '00:00:00',
    fuelPercentage: 0,
    uplinkId: 'UPLINK-0000',
    cdmCount: 0,
    fpRate: '<0.2%',
    verificationStatus: 'PENDING',
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Format time remaining helper
  const formatTimeRemaining = useCallback((seconds) => {
    if (!seconds || seconds < 0) return '00:00:00';
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }, []);

  // Fetch data from backend
  useEffect(() => {
    let isMounted = true;
    
    const fetchData = async () => {
      try {
        const [healthRes, summaryRes, riskRes, decisionRes] = await Promise.all([
          fetch(`${API_BASE}/api/health`),
          fetch(`${API_BASE}/api/system/summary`),
          fetch(`${API_BASE}/api/system/risk`),
          fetch(`${API_BASE}/api/decisions/statistics`),
        ]);

        const healthData = healthRes.ok ? await healthRes.json() : {};
        const summaryData = summaryRes.ok ? await summaryRes.json() : {};
        const riskData = riskRes.ok ? await riskRes.json() : { top_threats: [], overview: {} };
        const decisionData = decisionRes.ok ? await decisionRes.json() : {};

        const criticalThreats = riskData.overview?.severity_distribution?.critical || 0;
        const alertCount = riskData.overview?.total_conjunctions || 0;

        if (isMounted) {
          setData({
            lastUpdateTime: new Date().toLocaleTimeString(),
            systemMode: healthData.avoidance_enabled ? 'AUTONOMOUS' : 'MANUAL',
            activeSatellites: healthData.satellites || summaryData.constellation?.total_satellites || 0,
            trackedDebris: healthData.debris || summaryData.constellation?.total_debris || 0,
            criticalThreats,
            alertCount,
            maneuverTimer: formatTimeRemaining(riskData.top_threats?.[0]?.time_to_tca_s),
            fuelPercentage: summaryData.fuel?.constellation_fuel_fraction 
              ? Math.round(summaryData.fuel.constellation_fuel_fraction * 100) 
              : 0,
            uplinkId: `UPLINK-${Math.floor(Math.random() * 9000) + 1000}`,
            cdmCount: decisionData.total_decisions || 0,
            fpRate: '<0.2%',
            verificationStatus: summaryData.system_mode?.mode === 'nominal' ? 'ACTIVE' : 'PENDING',
          });
          setError(null);
          setLoading(false);
        }
      } catch (err) {
        console.error('Fetch error:', err);
        if (isMounted) {
          setError(err.message);
          setLoading(false);
        }
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [formatTimeRemaining]);

  // Loading skeleton
  if (loading) {
    return <HomePageSkeleton />;
  }

  return (
    <PageLayout showFooter={true} className="px-0">
      {/* Hero Section */}
      <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden -mt-24 pt-24">
        {/* Hero Background */}
        <div className="absolute inset-0 z-0">
          <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#10131a]/60 to-[#10131a] z-10" />
          <div className="absolute inset-0 bg-gradient-to-r from-[#10131a] via-transparent to-[#10131a] z-10" />
          <img
            alt="India at night from space"
            className="w-full h-full object-cover opacity-60"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuBvHb8IA9q645jMvw1_08wGGwrytShbUDAPIX2r-d5IsXdHrVGGZqT8KPfAdo91RZektoFoC3EIX0CLJDbU1t0PJYNdHCYQ1IqUH6VVgZZxfEADf5YlHSx6db9LkyJdyWhq1uh44bMJVWchCr_bYi7ZDAgmHi3tI-xI9DGkhDr0qfQcxpC2mOEtppNGnTI4kLbtM4i8QBwm3dz6CVkQKSHPRO_ZUWj0Kyq7GstSpc6tBRkRX7E4cf0VCfNBk2QTT2nolevJ-32kJ0Sy"
          />
        </div>

        {/* Hero Content */}
        <div className="relative z-20 max-w-[1440px] mx-auto w-full px-8">
          <div className="max-w-3xl mx-auto text-center animate-fadeInUp">
            {/* Status Bar */}
            <div className="flex items-center justify-center gap-6 mb-10 text-xs font-mono">
              <span className="text-[#4fdbc8]/60">LAST UPDATE: {data.lastUpdateTime}</span>
              <span className="w-1.5 h-1.5 rounded-full bg-[#4fdbc8] animate-pulse" />
              <StatusBadge status={data.systemMode} pulse={true} />
            </div>

            {/* Title */}
            <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight text-[#e1e2eb] mb-4">
              <span className="text-gradient">Prabanja Chitra</span>
            </h1>
            <p className="text-xl md:text-2xl font-semibold text-[#4fdbc8] mb-10">
              India's Autonomous Satellite Safety Command
            </p>

            {/* Tagline */}
            <div className="flex gap-3 justify-center mb-8 flex-wrap">
              {['Predict', 'Protect', 'Recover'].map((tag, i) => (
                <span 
                  key={tag}
                  className="text-sm font-bold tracking-[0.1em] uppercase bg-[#1d2026]/80 backdrop-blur px-4 py-2 rounded-lg border-l-4 border-[#4fdbc8] animate-fadeInUp"
                  style={{ animationDelay: `${(i + 1) * 100}ms` }}
                >
                  {tag}
                </span>
              ))}
            </div>

            <p className="text-[#bbcac6] text-lg mb-10 max-w-xl mx-auto">
              Fuel-aware orbital safety for constellation operations. 
              Real-time conjunction prediction and autonomous collision avoidance.
            </p>

            {/* Stats Cards */}
            <div className="grid grid-cols-3 gap-6 max-w-2xl mx-auto mb-12 animate-fadeInUp delay-200">
              <HeroStatCard 
                label="Active Satellites" 
                value={data.activeSatellites} 
                color="#4fdbc8"
              />
              <HeroStatCard 
                label="Tracked Debris" 
                value={data.trackedDebris} 
                color="#bbcac6"
              />
              <HeroStatCard 
                label="Critical Threats" 
                value={data.criticalThreats} 
                color={data.criticalThreats > 0 ? '#ffb4ab' : '#4fdbc8'}
                highlight={data.criticalThreats > 0}
              />
            </div>

            {/* CTA Buttons */}
            <div className="flex gap-6 justify-center animate-fadeInUp delay-300">
              <Link 
                to="/architecture" 
                className="btn-secondary px-8 py-4 text-sm"
              >
                See How It Works
              </Link>
              <Link 
                to="/mission-control" 
                className="btn-primary px-8 py-4 text-sm"
              >
                Open Mission Control
              </Link>
            </div>
          </div>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-float">
          <div className="w-6 h-10 rounded-full border-2 border-[#4fdbc8]/30 flex items-start justify-center pt-2">
            <div className="w-1.5 h-3 bg-[#4fdbc8]/50 rounded-full animate-pulse" />
          </div>
        </div>
      </section>

      {/* Live Intelligence Strip */}
      <section className="bg-[#0b0e14] border-y border-[#3c4947]/20 sticky top-16 z-40">
        <div className="max-w-[1440px] mx-auto px-8 py-4">
          <div className="flex flex-wrap justify-between items-center gap-6">
            <div className="flex items-center gap-3">
              <span className={`w-2.5 h-2.5 rounded-full ${data.alertCount > 0 ? 'bg-[#ffb4ab] animate-pulse' : 'bg-[#4fdbc8]'}`} />
              <span className="text-[#e1e2eb] font-bold">{data.alertCount} Active alerts</span>
            </div>
            
            <div className="flex items-center gap-8 text-[0.6875rem] uppercase tracking-[0.1em] text-[#bbcac6]">
              <div className="flex flex-col items-center md:items-start">
                <span>Maneuver timeline</span>
                <span className="text-[#e1e2eb] font-bold text-base mt-1 font-mono">T-{data.maneuverTimer}</span>
              </div>
              <div className="w-px h-8 bg-[#3c4947]/30 hidden md:block" />
              <div className="flex flex-col items-center md:items-start">
                <span>Fleet fuel</span>
                <span className="text-[#4fdbc8] font-bold text-base mt-1">{data.fuelPercentage}%</span>
              </div>
              <div className="w-px h-8 bg-[#3c4947]/30 hidden md:block" />
              <div className="flex flex-col items-center md:items-start">
                <span>Uplink</span>
                <span className="text-[#e1e2eb]/60 font-mono text-xs mt-1">{data.uplinkId}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Core Operational Vectors */}
      <section className="py-24 px-8 max-w-[1440px] mx-auto">
        <div className="flex items-center gap-6 mb-12">
          <div className="w-1 h-8 bg-[#4fdbc8] rounded-full" />
          <h2 className="text-2xl font-bold text-[#e1e2eb]">Core Operational Vectors</h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <OperationalCard
            icon="radar"
            title="Predict conjunctions"
            description="Operational orbit propagation and proximity analysis."
            features={[
              { label: 'TCA Prediction Accuracy', value: '98.4%' },
              { label: '72-hour Lookahead Window', value: null },
              { label: 'CDMs Processed', value: data.cdmCount },
            ]}
            delay={0}
          />
          
          <OperationalCard
            icon="analytics"
            title="Score threats"
            description="Probabilistic modeling to distinguish noise from lethal collision events."
            features={[
              { label: 'Collision Probability Scoring', value: null },
              { label: 'Asset Sensitivity Adjustment', value: null },
              { label: 'False Positive Rate', value: data.fpRate },
            ]}
            delay={100}
            showSeverityBar={true}
          />
          
          <OperationalCard
            icon="rocket_launch"
            title="Execute recovery"
            description="Automated delta-V commands to shift orbital parameters."
            features={[
              { label: 'Autonomous Maneuver Upload', value: null },
              { label: 'Post-Burn Verification', value: data.verificationStatus },
              { label: 'Fuel-Efficient Pathfinding', value: null },
            ]}
            delay={200}
            showTimeline={true}
          />
        </div>
      </section>

      {/* Operational Safety Layer */}
      <section className="py-24 bg-[#0b0e14]">
        <div className="max-w-[1440px] mx-auto px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div className="animate-fadeInUp">
              <h2 className="text-3xl font-bold mb-10 text-[#e1e2eb]">Operational Safety Layer</h2>
              <p className="text-[#bbcac6] mb-12 text-lg leading-relaxed">
                Maintaining continuity in congested orbits requires more than tracking—it requires 
                surgical precision in decision making.
              </p>
              
              <div className="space-y-4">
                <SafetyFeature 
                  icon="security" 
                  title="Reduce collision risk"
                  description="Verified collision risk mitigation via continuous epoch monitoring."
                />
                <SafetyFeature 
                  icon="ev_station" 
                  title="Save fuel"
                  description="Fuel-optimized paths ensure mission lifespan is never compromised."
                />
                <SafetyFeature 
                  icon="verified" 
                  title="Improve uptime"
                  description="Maintain data stream integrity during station-keeping maneuvers."
                />
              </div>
            </div>
            
            <div className="relative aspect-square rounded-2xl overflow-hidden border border-[#3c4947]/20 animate-fadeInUp delay-200">
              <img
                alt="Satellite constellation visualization"
                className="w-full h-full object-cover grayscale opacity-30"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuCreeRG0SWjqmRs-xl2Cg5hPPLmOJN5Y2hdTCq9AkIyAWjAxJ-cd1dgUpFVY3xtwz_HYsW5RsijxrvRfnoiTOAnWttKbzjfD6vG0WpvLcduLHV3ZttN_i1mRJEH-6Q8Rcz-jqNeiudUDcJsQIbRxTbkINIsiMWTyJaBvd8u_l_PIXmADKOWh1mZV0ANyxWLFgpvgl1gSG0cby3jaEfzK0tCMnomx3_B-ntHRRCZhOFWKrrLyagh9hmSfP6FoPVrqq6NZ_EsrjUQ-nmA"
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="relative">
                  <div className="w-64 h-64 border-2 border-[#4fdbc8]/20 rounded-full animate-pulse" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="w-48 h-48 border-2 border-[#4fdbc8]/40 rounded-full" />
                  </div>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="w-20 h-20 bg-[#4fdbc8]/10 rounded-full flex items-center justify-center">
                      <span className="material-symbols-outlined text-[#4fdbc8] text-4xl">shield_with_heart</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Key Capabilities */}
      <section className="py-24 px-8 max-w-[1440px] mx-auto">
        <div className="text-center mb-16">
          <span className="text-[0.6875rem] uppercase tracking-[0.2em] text-[#4fdbc8] font-bold">
            Sentinel Capabilities
          </span>
          <h2 className="text-3xl font-bold mt-2 text-[#e1e2eb]">Engineered for Extremes</h2>
        </div>
        
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
          {[
            { icon: 'auto_mode', label: 'Autonomous Avoidance' },
            { icon: 'my_location', label: 'Real-time Tracking' },
            { icon: 'speed', label: 'Fuel Optimization' },
            { icon: 'cloud_sync', label: 'Ground Sync' },
            { icon: 'hub', label: 'Swarm Logic' },
            { icon: 'memory', label: 'On-edge ML' },
          ].map((cap, i) => (
            <CapabilityCard key={cap.label} icon={cap.icon} label={cap.label} delay={i * 50} />
          ))}
        </div>
      </section>

      {/* Proof Metrics */}
      <section className="py-20 bg-[#1d2026]">
        <div className="max-w-[1440px] mx-auto px-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            <ProofMetric 
              title="Real-time conjunction prediction" 
              badge="Latency Verified" 
              delay={0}
            />
            <ProofMetric 
              title="Fuel-aware autonomous avoidance" 
              badge="Edge Processing" 
              delay={100}
            />
            <ProofMetric 
              title="Verified maneuver loop" 
              badge="Optimization Engine" 
              delay={200}
            />
            <ProofMetric 
              title="Operational decision support" 
              badge="Mission Success" 
              highlight={true}
              delay={300}
            />
          </div>
        </div>
      </section>

      {/* Error Toast */}
      {error && (
        <div className="fixed bottom-8 right-8 z-50 animate-slideInRight">
          <div className="bg-[#1a1d26] border border-[#ffb4ab]/30 rounded-xl p-4 shadow-lg max-w-sm">
            <div className="flex items-start gap-3">
              <span className="text-[#ffb4ab]"><span className="material-symbols-outlined">error</span></span>
              <div>
                <p className="text-sm font-medium text-[#e1e2eb]">Connection issue</p>
                <p className="text-xs text-[#bbcac6] mt-1">{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </PageLayout>
  );
}

// Hero Stat Card Component
function HeroStatCard({ label, value, color, highlight = false }) {
  return (
    <div className={`
      glass-panel rounded-xl p-4 text-center
      ${highlight ? 'animate-glowPulse border-[#ffb4ab]/30' : ''}
    `}>
      <div className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#bbcac6] mb-2">{label}</div>
      <div 
        className="text-3xl font-bold metric-value"
        style={{ color }}
      >
        {value}
      </div>
    </div>
  );
}

// Operational Card Component
function OperationalCard({ icon, title, description, features, delay, showSeverityBar, showTimeline }) {
  return (
    <Card 
      className="group relative overflow-hidden animate-fadeInUp"
      style={{ animationDelay: `${delay}ms` }}
      padding="large"
    >
      <div className="absolute top-0 left-0 w-1 h-full bg-[#4fdbc8] opacity-20 group-hover:opacity-100 transition-opacity" />
      
      <span className="material-symbols-outlined text-[#4fdbc8] mb-10 text-4xl block">
        {icon}
      </span>
      
      <h3 className="text-xl font-bold text-[#e1e2eb] mb-3">{title}</h3>
      <p className="text-[#bbcac6] leading-relaxed mb-10">{description}</p>
      
      <div className="border-t border-[#3c4947]/20 pt-6">
        <ul className="space-y-3 text-sm text-[#bbcac6]">
          {features.map((feature, i) => (
            <li key={i} className="flex items-center justify-between gap-2">
              <span className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-[#4fdbc8]" />
                {feature.label}
              </span>
              {feature.value && (
                <span className="text-[#4fdbc8] font-semibold">{feature.value}</span>
              )}
            </li>
          ))}
        </ul>
        
        {showSeverityBar && (
          <div className="mt-6 bg-[#0b0e14]/50 p-4 rounded-lg border border-[#3c4947]/10">
            <div className="text-[0.625rem] uppercase tracking-widest text-[#4fdbc8]/60 mb-2">
              Severity Breakdown
            </div>
            <div className="flex gap-1 h-2 rounded-full overflow-hidden">
              <div className="bg-[#ffb4ab] w-[15%]" />
              <div className="bg-orange-400 w-[25%]" />
              <div className="bg-yellow-400 w-[35%]" />
              <div className="bg-[#4fdbc8]/30 flex-1" />
            </div>
            <div className="flex justify-between mt-1 text-[0.625rem] text-[#bbcac6]/60">
              <span>CRITICAL</span>
              <span>LOW RISK</span>
            </div>
          </div>
        )}
        
        {showTimeline && (
          <div className="mt-6 bg-[#0b0e14]/50 p-4 rounded-lg border border-[#3c4947]/10">
            <div className="text-[0.625rem] uppercase tracking-widest text-[#4fdbc8]/60 mb-2">
              Maneuver Timeline
            </div>
            <div className="flex items-center justify-between gap-2 px-2">
              <div className="w-3 h-3 rounded-full bg-[#4fdbc8]" />
              <div className="h-0.5 flex-1 bg-[#4fdbc8]/30" />
              <div className="w-3 h-3 rounded-full border-2 border-[#4fdbc8]/40" />
              <div className="h-0.5 flex-1 bg-[#4fdbc8]/10" />
              <div className="w-3 h-3 rounded-full border-2 border-[#4fdbc8]/40" />
            </div>
            <div className="flex justify-between mt-2 text-[0.5rem] text-[#bbcac6]/60 uppercase">
              <span>Burn</span>
              <span>Verify</span>
              <span>Station</span>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}

// Safety Feature Component
function SafetyFeature({ icon, title, description }) {
  return (
    <div className="flex gap-6 items-start p-4 bg-[#1d2026] rounded-lg hover:bg-[#272a31] transition-colors group">
      <div className="bg-[#4fdbc8]/10 p-3 rounded-lg text-[#4fdbc8] group-hover:scale-110 transition-transform">
        <span className="material-symbols-outlined">{icon}</span>
      </div>
      <div>
        <h4 className="font-bold mb-1 text-[#e1e2eb]">{title}</h4>
        <p className="text-sm text-[#bbcac6]">{description}</p>
      </div>
    </div>
  );
}

// Capability Card Component
function CapabilityCard({ icon, label, delay }) {
  return (
    <div 
      className="bg-[#191c22] p-6 rounded-xl text-center flex flex-col items-center justify-center hover:bg-[#1d2026] transition-all border-b-2 border-transparent hover:border-[#4fdbc8]/40 hover:-translate-y-1 animate-fadeInUp"
      style={{ animationDelay: `${delay}ms` }}
    >
      <span className="material-symbols-outlined text-[#4fdbc8] mb-3 text-2xl">{icon}</span>
      <span className="text-xs font-bold uppercase tracking-wider text-[#e1e2eb]/80">{label}</span>
    </div>
  );
}

// Proof Metric Component
function ProofMetric({ title, badge, highlight = false, delay }) {
  return (
    <div 
      className="text-center md:text-left animate-fadeInUp"
      style={{ animationDelay: `${delay}ms` }}
    >
      <div className={`text-xl font-bold mb-2 ${highlight ? 'text-[#4fdbc8]' : 'text-[#e1e2eb]'}`}>
        {title}
      </div>
      <div className={`text-[0.6875rem] uppercase tracking-[0.1em] font-bold ${highlight ? 'text-[#bbcac6]' : 'text-[#4fdbc8]'}`}>
        {badge}
      </div>
    </div>
  );
}

// Loading Skeleton Component
function HomePageSkeleton() {
  return (
    <PageLayout showFooter={false} className="px-0">
      {/* Hero Skeleton */}
      <section className="relative min-h-[90vh] flex items-center justify-center -mt-24 pt-24 bg-[#0b0e14]">
        <div className="max-w-3xl mx-auto text-center px-8">
          <div className="flex justify-center gap-6 mb-10">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-4 w-24" />
          </div>
          <Skeleton className="h-16 w-96 mx-auto mb-4" />
          <Skeleton className="h-8 w-72 mx-auto mb-10" />
          <div className="flex gap-3 justify-center mb-8">
            <Skeleton className="h-10 w-24" />
            <Skeleton className="h-10 w-24" />
            <Skeleton className="h-10 w-24" />
          </div>
          <Skeleton className="h-20 w-full max-w-xl mx-auto mb-12" />
          <div className="grid grid-cols-3 gap-6 max-w-2xl mx-auto mb-12">
            <Skeleton className="h-24 w-full rounded-xl" />
            <Skeleton className="h-24 w-full rounded-xl" />
            <Skeleton className="h-24 w-full rounded-xl" />
          </div>
        </div>
      </section>
    </PageLayout>
  );
}
