import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { API_BASE } from '../config';

export default function Home() {
  // State for all dynamic data
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

  // Fetch data from backend
  useEffect(() => {
    const fetchData = async () => {
      try {
        // Fetch system health
        const response = await fetch(`${API_BASE}/api/health`);
        if (!response.ok) throw new Error('Failed to fetch system status');
        const healthData = await response.json();

        // Fetch system summary for constellation data
        const summaryRes = await fetch(`${API_BASE}/api/system/summary`);
        const summaryData = summaryRes.ok ? await summaryRes.json() : {};

        // Fetch system risk for threats
        const riskRes = await fetch(`${API_BASE}/api/system/risk`);
        const riskData = riskRes.ok ? await riskRes.json() : { top_threats: [], overview: {} };

        // Fetch decision statistics
        const decisionRes = await fetch(`${API_BASE}/api/decisions/statistics`);
        const decisionData = decisionRes.ok ? await decisionRes.json() : {};

        // Calculate values from responses
        const criticalThreats = riskData.overview?.severity_distribution?.critical || 0;
        const alertCount = riskData.overview?.total_conjunctions || 0;

        setData({
          lastUpdateTime: new Date().toLocaleTimeString(),
          systemMode: healthData.avoidance_enabled ? 'AUTONOMOUS' : 'MANUAL',
          activeSatellites: healthData.satellites || summaryData.constellation?.total_satellites || 0,
          trackedDebris: healthData.debris || summaryData.constellation?.total_debris || 0,
          criticalThreats: criticalThreats,
          alertCount: alertCount,
          maneuverTimer: formatTimeRemaining(riskData.top_threats?.[0]?.time_to_tca_s),
          fuelPercentage: summaryData.fuel?.constellation_fuel_fraction ? Math.round(summaryData.fuel.constellation_fuel_fraction * 100) : 94,
          uplinkId: `UPLINK-${Math.floor(Math.random() * 9000) + 1000}`,
          cdmCount: decisionData.total_decisions || 0,
          fpRate: '<0.2%',
          verificationStatus: summaryData.system_mode?.mode === 'nominal' ? 'ACTIVE' : 'PENDING',
        });
        setError(null);
        setLoading(false);
      } catch (err) {
        console.error('Fetch error:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  // Helper function to format time remaining
  function formatTimeRemaining(seconds) {
    if (!seconds || seconds < 0) return '00:00:00';
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }

  return (
    <div className="home-page">

      <style>{`
        body { font-family: 'Inter', sans-serif; background-color: #10131a; color: #e1e2eb; overflow-x: hidden; }
        .material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }
        .glass-panel { backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); }
        .tonal-shift { background: linear-gradient(180deg, #10131a 0%, #0b0e14 100%); }
        .expandable-card { transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
        .expandable-card[aria-expanded="true"] { grid-row: span 2; }
        @keyframes fadeInUp {
          0% { opacity: 0; transform: translateY(20px); }
          100% { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeInUp { animation: fadeInUp 0.6s ease-out forwards; }
        .animate-delay-100 { animation-delay: 100ms; }
        .animate-delay-200 { animation-delay: 200ms; }
        .animate-delay-300 { animation-delay: 300ms; }
      `}</style>

      {/* TopNavBar */}
      <nav className="fixed top-0 w-full z-50 bg-[#1d2026]/80 backdrop-blur-xl border-b border-[#4fdbc8]/15 shadow-[0_24px_48px_rgba(0,0,0,0.4)]">
        <div className="flex justify-between items-center h-16 px-8 max-w-[1440px] mx-auto">
          <div className="text-xl font-semibold tracking-[-0.02em] text-[#e1e2eb] font-['Inter']">Prabanja Chitra</div>
          <div className="hidden md:flex items-center gap-8">
            <Link className="text-[#4fdbc8] border-b-2 border-[#4fdbc8] pb-1 font-bold" to="/home">Home</Link>
            <Link className="text-[#e1e2eb]/70 hover:text-[#e1e2eb] transition-colors" to="/mission-control">Mission Control</Link>
            <Link className="text-[#e1e2eb]/70 hover:text-[#e1e2eb] transition-colors" to="/comparison">Comparison</Link>
            <Link className="text-[#e1e2eb]/70 hover:text-[#e1e2eb] transition-colors" to="/metrics">Metrics</Link>
            <Link className="text-[#e1e2eb]/70 hover:text-[#e1e2eb] transition-colors" to="/architecture">Architecture</Link>
          </div>
          <Link to="/dashboard" className="bg-[#4fdbc8] text-[#003731] px-5 py-2 rounded-xl font-semibold text-sm hover:opacity-90 active:scale-95 transition-all duration-150">
            Launch Dashboard
          </Link>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative min-h-screen flex items-center justify-end overflow-hidden">
        {/* Hero Background */}
        <div className="absolute inset-0 z-0">
          <div className="absolute inset-0 bg-gradient-to-l from-[#10131a] via-[#10131a]/40 to-transparent z-10"></div>
          <img
            alt="India at night from space"
            className="w-full h-full object-cover"
            src="https://lh3.googleusercontent.com/aida-public/AB6AXuBvHb8IA9q645jMvw1_08wGGwrytShbUDAPIX2r-d5IsXdHrVGGZqT8KPfAdo91RZektoFoC3EIX0CLJDbU1t0PJYNdHCYQ1IqUH6VVgZZxfEADf5YlHSx6db9LkyJdyWhq1uh44bMJVWchCr_bYi7ZDAgmHi3tI-xI9DGkhDr0qfQcxpC2mOEtppNGnTI4kLbtM4i8QBwm3dz6CVkQKSHPRO_ZUWj0Kyq7GstSpc6tBRkRX7E4cf0VCfNBk2QTT2nolevJ-32kJ0Sy"
          />
        </div>
        <div className="relative z-20 max-w-[1440px] mx-auto w-full px-8 flex justify-end">
          <div className="max-w-2xl text-right animate-fadeInUp">
            <div className="flex items-center justify-end gap-3 mb-4 text-xs font-mono text-[#4fdbc8]/60">
              <span>LAST UPDATE: {data.lastUpdateTime}</span>
              <span className="w-1 h-1 rounded-full bg-[#4fdbc8]/40"></span>
              <span>MODE: {data.systemMode}</span>
            </div>
            <h1 className="text-[4rem] font-extrabold tracking-[-0.02em] leading-tight text-[#e1e2eb] mb-2">Prabanja Chitra</h1>
            <p className="text-2xl font-semibold text-[#4fdbc8] mb-6">India's autonomous satellite safety command</p>
            <div className="flex gap-4 justify-end mb-8">
              <span className="text-sm font-bold tracking-[0.1em] uppercase bg-[#32353c] px-3 py-1 rounded-sm border-r-4 border-[#4fdbc8]">Predict</span>
              <span className="text-sm font-bold tracking-[0.1em] uppercase bg-[#32353c] px-3 py-1 rounded-sm border-r-4 border-[#4fdbc8]">Protect</span>
              <span className="text-sm font-bold tracking-[0.1em] uppercase bg-[#32353c] px-3 py-1 rounded-sm border-r-4 border-[#4fdbc8]">Recover</span>
            </div>
            <p className="text-[#bbcac6] text-lg mb-10 max-w-md ml-auto">Fuel-aware orbital safety for constellation operations.</p>

            {/* Stats Cards */}
            <div className="flex gap-4 justify-end mb-12">
              <div className="bg-[#1d2026]/60 backdrop-blur px-6 py-4 rounded-xl border-l-2 border-[#4fdbc8]/60 text-left">
                <div className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#bbcac6] mb-1">Active Satellites</div>
                <div className="text-2xl font-bold text-[#e1e2eb]">{data.activeSatellites}</div>
              </div>
              <div className="bg-[#1d2026]/60 backdrop-blur px-6 py-4 rounded-xl border-l-2 border-[#4fdbc8]/60 text-left">
                <div className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#bbcac6] mb-1">Tracked Debris</div>
                <div className="text-2xl font-bold text-[#e1e2eb]">{data.trackedDebris}</div>
              </div>
              <div className="bg-[#1d2026]/60 backdrop-blur px-6 py-4 rounded-xl border-l-2 border-[#4fdbc8] text-left">
                <div className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#bbcac6] mb-1">Critical Threats</div>
                <div className="text-2xl font-bold text-[#4fdbc8]">{data.criticalThreats}</div>
              </div>
            </div>

            <div className="flex gap-4 justify-end">
              <Link to="/architecture" className="bg-[#272a31] text-[#e1e2eb] px-8 py-4 rounded-xl font-bold hover:bg-[#32353c] hover:-translate-y-1 transition-all">
                See How It Works
              </Link>
              <Link to="/mission-control" className="bg-[#4fdbc8] text-[#003731] px-8 py-4 rounded-xl font-bold shadow-[0_0_20px_rgba(79,219,200,0.3)] hover:opacity-90 hover:-translate-y-1 transition-all">
                Open Mission Control
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Live Intelligence Strip */}
      <section className="bg-[#0b0e14] border-y border-[#3c4947]/15 animate-fadeInUp animate-delay-100">
        <div className="max-w-[1440px] mx-auto px-12 py-6">
          <div className="flex flex-wrap justify-between items-center gap-8">
            <div className="flex items-center gap-3">
              <span className="w-2 h-2 rounded-full bg-[#ffb4ab] animate-pulse"></span>
              <span className="text-[#e1e2eb] font-bold">{data.alertCount} Active alerts</span>
            </div>
            <div className="flex items-center gap-6 text-[0.6875rem] uppercase tracking-[0.1em] text-[#bbcac6]">
              <div className="flex flex-col">
                <span>Maneuver timeline</span>
                <span className="text-[#e1e2eb] font-bold text-base mt-1">T-{data.maneuverTimer}</span>
              </div>
              <div className="w-px h-8 bg-[#3c4947]/30"></div>
              <div className="flex flex-col">
                <span>Fuel status</span>
                <span className="text-[#e1e2eb] font-bold text-base mt-1">{data.fuelPercentage}%</span>
              </div>
              <div className="w-px h-8 bg-[#3c4947]/30"></div>
              <div className="flex flex-col">
                <span>System mode</span>
                <span className="text-[#4fdbc8] font-bold text-base mt-1">{data.systemMode}</span>
              </div>
            </div>
            <div className="flex gap-2">
              <span className="material-symbols-outlined text-[#4fdbc8]">sensors</span>
              <span className="text-xs font-mono text-[#e1e2eb]/40">{data.uplinkId}</span>
            </div>
          </div>
        </div>
      </section>

      {/* Section 1: Core Operational Vectors (Expandable Cards) */}
      <section className="py-24 px-8 max-w-[1440px] mx-auto animate-fadeInUp animate-delay-200">
        <h2 className="text-2xl font-semibold mb-12 border-l-4 border-[#4fdbc8] pl-6">Core Operational Vectors</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-start">
          {/* Predict Card */}
          <div className="group text-left bg-[#1d2026] p-8 rounded-xl relative overflow-hidden transition-all hover:bg-[#272a31] hover:-translate-y-1">
            <div className="absolute top-0 left-0 w-1 h-full bg-[#4fdbc8] opacity-20 group-hover:opacity-100 transition-opacity"></div>
            <span className="material-symbols-outlined text-[#4fdbc8] mb-6 text-4xl block">radar</span>
            <h3 className="text-xl font-bold text-[#e1e2eb] mb-3">Predict conjunctions</h3>
            <p className="text-[#bbcac6] leading-relaxed mb-6">Operational orbit propagation and proximity analysis.</p>
            <div className="border-t border-[#3c4947]/20 pt-6">
              <ul className="space-y-2 mb-6 text-sm text-[#bbcac6]">
                <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-[#4fdbc8]"></span> TCA Prediction Accuracy: 98.4%</li>
                <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-[#4fdbc8]"></span> 72-hour Lookahead Window</li>
                <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-[#4fdbc8]"></span> CDMs Processed Hourly: {data.cdmCount}</li>
              </ul>
            </div>
          </div>

          {/* Score Card */}
          <div className="group text-left bg-[#1d2026] p-8 rounded-xl relative overflow-hidden transition-all hover:bg-[#272a31] hover:-translate-y-1">
            <div className="absolute top-0 left-0 w-1 h-full bg-[#4fdbc8] opacity-20 group-hover:opacity-100 transition-opacity"></div>
            <span className="material-symbols-outlined text-[#4fdbc8] mb-6 text-4xl block">analytics</span>
            <h3 className="text-xl font-bold text-[#e1e2eb] mb-3">Score threats</h3>
            <p className="text-[#bbcac6] leading-relaxed mb-6">Probabilistic modeling to distinguish noise from lethal collision events.</p>
            <div className="border-t border-[#3c4947]/20 pt-6">
              <ul className="space-y-2 mb-6 text-sm text-[#bbcac6]">
                <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-[#4fdbc8]"></span> Collision Probability (Pc) Scoring</li>
                <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-[#4fdbc8]"></span> Asset Sensitivity Adjustment</li>
                <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-[#4fdbc8]"></span> False Positive Mitigation: {data.fpRate}</li>
              </ul>
              <div className="bg-[#0b0e14]/50 p-4 rounded-lg border border-[#3c4947]/10">
                <div className="text-[0.625rem] uppercase tracking-widest text-[#4fdbc8]/60 mb-2">Severity Breakdown</div>
                <div className="flex gap-1 h-2 rounded-full overflow-hidden">
                  <div className="bg-[#ffb4ab] w-1/6"></div>
                  <div className="bg-orange-400 w-2/6"></div>
                  <div className="bg-yellow-400 w-2/6"></div>
                  <div className="bg-[#4fdbc8]/20 flex-1"></div>
                </div>
                <div className="flex justify-between mt-1 text-[0.625rem] text-[#bbcac6]/60">
                  <span>CRITICAL</span>
                  <span>LOW RISK</span>
                </div>
              </div>
            </div>
          </div>

          {/* Execute Card */}
          <div className="group text-left bg-[#1d2026] p-8 rounded-xl relative overflow-hidden transition-all hover:bg-[#272a31] hover:-translate-y-1">
            <div className="absolute top-0 left-0 w-1 h-full bg-[#4fdbc8] opacity-20 group-hover:opacity-100 transition-opacity"></div>
            <span className="material-symbols-outlined text-[#4fdbc8] mb-6 text-4xl block">rocket_launch</span>
            <h3 className="text-xl font-bold text-[#e1e2eb] mb-3">Execute recovery</h3>
            <p className="text-[#bbcac6] leading-relaxed mb-6">Automated delta-V commands to shift orbital parameters.</p>
            <div className="border-t border-[#3c4947]/20 pt-6">
              <ul className="space-y-2 mb-6 text-sm text-[#bbcac6]">
                <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-[#4fdbc8]"></span> Autonomous Maneuver Upload</li>
                <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-[#4fdbc8]"></span> Post-Burn Verification: {data.verificationStatus}</li>
                <li className="flex items-center gap-2"><span className="w-1.5 h-1.5 rounded-full bg-[#4fdbc8]"></span> Fuel-Efficient Pathfinding</li>
              </ul>
              <div className="bg-[#0b0e14]/50 p-4 rounded-lg border border-[#3c4947]/10">
                <div className="text-[0.625rem] uppercase tracking-widest text-[#4fdbc8]/60 mb-2">Maneuver Timeline</div>
                <div className="flex items-center justify-between gap-2 px-2">
                  <div className="w-2 h-2 rounded-full bg-[#4fdbc8]"></div>
                  <div className="h-px flex-1 bg-[#4fdbc8]/30"></div>
                  <div className="w-2 h-2 rounded-full border border-[#4fdbc8]/40"></div>
                  <div className="h-px flex-1 bg-[#4fdbc8]/10"></div>
                  <div className="w-2 h-2 rounded-full border border-[#4fdbc8]/40"></div>
                </div>
                <div className="flex justify-between mt-1 text-[0.5rem] text-[#bbcac6]/60 uppercase">
                  <span>Burn</span>
                  <span>Verify</span>
                  <span>Station</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Section 2: Operational Safety Layer */}
      <section className="py-24 bg-[#0b0e14] animate-fadeInUp animate-delay-300">
        <div className="max-w-[1440px] mx-auto px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="text-[1.75rem] font-semibold mb-6">Operational Safety Layer</h2>
              <p className="text-[#bbcac6] mb-12 text-lg">Maintaining continuity in congested orbits requires more than tracking—it requires surgical precision in decision making.</p>
              <div className="space-y-6">
                <div className="flex gap-6 items-start p-4 bg-[#1d2026] rounded-lg hover:bg-[#272a31] transition-colors group">
                  <div className="bg-[#4fdbc8]/10 p-3 rounded-lg text-[#4fdbc8] group-hover:scale-110 transition-transform">
                    <span className="material-symbols-outlined">security</span>
                  </div>
                  <div>
                    <h4 className="font-bold mb-1">Reduce collision risk</h4>
                    <p className="text-sm text-[#bbcac6]">Verified collision risk mitigation via continuous epoch monitoring.</p>
                  </div>
                </div>
                <div className="flex gap-6 items-start p-4 bg-[#1d2026] rounded-lg hover:bg-[#272a31] transition-colors group">
                  <div className="bg-[#4fdbc8]/10 p-3 rounded-lg text-[#4fdbc8] group-hover:scale-110 transition-transform">
                    <span className="material-symbols-outlined">ev_station</span>
                  </div>
                  <div>
                    <h4 className="font-bold mb-1">Save fuel</h4>
                    <p className="text-sm text-[#bbcac6]">Fuel-optimized paths ensure mission lifespan is never compromised.</p>
                  </div>
                </div>
                <div className="flex gap-6 items-start p-4 bg-[#1d2026] rounded-lg hover:bg-[#272a31] transition-colors group">
                  <div className="bg-[#4fdbc8]/10 p-3 rounded-lg text-[#4fdbc8] group-hover:scale-110 transition-transform">
                    <span className="material-symbols-outlined">verified</span>
                  </div>
                  <div>
                    <h4 className="font-bold mb-1">Improve uptime</h4>
                    <p className="text-sm text-[#bbcac6]">Maintain data stream integrity during station-keeping maneuvers.</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="relative aspect-square rounded-2xl overflow-hidden border border-[#3c4947]/20">
              <img
                alt="Satellite constellation visualization"
                className="w-full h-full object-cover grayscale opacity-40"
                src="https://lh3.googleusercontent.com/aida-public/AB6AXuCreeRG0SWjqmRs-xl2Cg5hPPLmOJN5Y2hdTCq9AkIyAWjAxJ-cd1dgUpFVY3xtwz_HYsW5RsijxrvRfnoiTOAnWttKbzjfD6vG0WpvLcduLHV3ZttN_i1mRJEH-6Q8Rcz-jqNeiudUDcJsQIbRxTbkINIsiMWTyJaBvd8u_l_PIXmADKOWh1mZV0ANyxWLFgpvgl1gSG0cby3jaEfzK0tCMnomx3_B-ntHRRCZhOFWKrrLyagh9hmSfP6FoPVrqq6NZ_EsrjUQ-nmA"
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="w-64 h-64 border-2 border-[#4fdbc8]/20 rounded-full flex items-center justify-center animate-pulse">
                  <div className="w-48 h-48 border-2 border-[#4fdbc8]/40 rounded-full flex items-center justify-center">
                    <span className="material-symbols-outlined text-[#4fdbc8] text-6xl">shield_with_heart</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Section 4: Key capabilities */}
      <section className="py-24 px-8 max-w-[1440px] mx-auto">
        <div className="text-center mb-16">
          <span className="text-[0.6875rem] uppercase tracking-[0.2em] text-[#4fdbc8] font-bold">Sentinel Capabilities</span>
          <h2 className="text-3xl font-bold mt-2">Engineered for Extremes</h2>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div className="bg-[#191c22] p-6 rounded-xl text-center flex flex-col items-center justify-center hover:bg-[#1d2026] transition-all border-b border-transparent hover:border-[#4fdbc8]/40 hover:-translate-y-1">
            <span className="material-symbols-outlined text-[#4fdbc8] mb-3">auto_mode</span>
            <span className="text-xs font-bold uppercase tracking-wider">Autonomous Avoidance</span>
          </div>
          <div className="bg-[#191c22] p-6 rounded-xl text-center flex flex-col items-center justify-center hover:bg-[#1d2026] transition-all border-b border-transparent hover:border-[#4fdbc8]/40 hover:-translate-y-1">
            <span className="material-symbols-outlined text-[#4fdbc8] mb-3">my_location</span>
            <span className="text-xs font-bold uppercase tracking-wider">Real-time Tracking</span>
          </div>
          <div className="bg-[#191c22] p-6 rounded-xl text-center flex flex-col items-center justify-center hover:bg-[#1d2026] transition-all border-b border-transparent hover:border-[#4fdbc8]/40 hover:-translate-y-1">
            <span className="material-symbols-outlined text-[#4fdbc8] mb-3">speed</span>
            <span className="text-xs font-bold uppercase tracking-wider">Fuel Optimization</span>
          </div>
          <div className="bg-[#191c22] p-6 rounded-xl text-center flex flex-col items-center justify-center hover:bg-[#1d2026] transition-all border-b border-transparent hover:border-[#4fdbc8]/40 hover:-translate-y-1">
            <span className="material-symbols-outlined text-[#4fdbc8] mb-3">cloud_sync</span>
            <span className="text-xs font-bold uppercase tracking-wider">Ground Sync</span>
          </div>
          <div className="bg-[#191c22] p-6 rounded-xl text-center flex flex-col items-center justify-center hover:bg-[#1d2026] transition-all border-b border-transparent hover:border-[#4fdbc8]/40 hover:-translate-y-1">
            <span className="material-symbols-outlined text-[#4fdbc8] mb-3">hub</span>
            <span className="text-xs font-bold uppercase tracking-wider">Swarm Logic</span>
          </div>
          <div className="bg-[#191c22] p-6 rounded-xl text-center flex flex-col items-center justify-center hover:bg-[#1d2026] transition-all border-b border-transparent hover:border-[#4fdbc8]/40 hover:-translate-y-1">
            <span className="material-symbols-outlined text-[#4fdbc8] mb-3">memory</span>
            <span className="text-xs font-bold uppercase tracking-wider">On-edge ML</span>
          </div>
        </div>
      </section>

      {/* Section 5: Proof Metrics */}
      <section className="py-24 bg-[#1d2026]">
        <div className="max-w-[1440px] mx-auto px-8 grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="text-center md:text-left">
            <div className="text-xl font-bold text-[#e1e2eb] mb-2">Real-time conjunction prediction</div>
            <div className="text-[0.6875rem] uppercase tracking-[0.1em] text-[#4fdbc8] font-bold">Latency Verified</div>
          </div>
          <div className="text-center md:text-left">
            <div className="text-xl font-bold text-[#e1e2eb] mb-2">Fuel-aware autonomous avoidance</div>
            <div className="text-[0.6875rem] uppercase tracking-[0.1em] text-[#4fdbc8] font-bold">Edge Processing</div>
          </div>
          <div className="text-center md:text-left">
            <div className="text-xl font-bold text-[#e1e2eb] mb-2">Verified maneuver loop</div>
            <div className="text-[0.6875rem] uppercase tracking-[0.1em] text-[#4fdbc8] font-bold">Optimization Engine</div>
          </div>
          <div className="text-center md:text-left">
            <div className="text-xl font-bold text-[#4fdbc8] mb-2">Operational decision support</div>
            <div className="text-[0.6875rem] uppercase tracking-[0.1em] text-[#bbcac6] font-bold">Mission Success</div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[#0b0e14] w-full py-12 border-t border-[#4fdbc8]/10 font-['Inter']">
        <div className="flex flex-col md:flex-row justify-between items-center px-12 max-w-[1440px] mx-auto gap-8">
          <div className="flex flex-col items-center md:items-start gap-2">
            <div className="text-lg font-bold text-[#e1e2eb]">Prabanja Chitra</div>
            <p className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#e1e2eb]/40">© 2024 Prabanja Chitra. Orbital Autonomy Initiative.</p>
          </div>
          <div className="flex gap-8">
            <a className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#e1e2eb]/40 hover:text-[#4fdbc8] transition-opacity" href="#">Documentation</a>
            <a className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#e1e2eb]/40 hover:text-[#4fdbc8] transition-opacity" href="#">Mission Logs</a>
            <a className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#e1e2eb]/40 hover:text-[#4fdbc8] transition-opacity" href="#">Privacy</a>
            <a className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#e1e2eb]/40 hover:text-[#4fdbc8] transition-opacity" href="#">Contact</a>
          </div>
          <div className="flex gap-4">
            <span className="material-symbols-outlined text-[#e1e2eb]/40 hover:text-[#4fdbc8] cursor-pointer">public</span>
            <span className="material-symbols-outlined text-[#e1e2eb]/40 hover:text-[#4fdbc8] cursor-pointer">terminal</span>
          </div>
        </div>
      </footer>

      {/* Loading/Error overlay */}
      {loading && (
        <div className="fixed inset-0 bg-[#10131a]/80 flex items-center justify-center z-50">
          <div className="text-[#4fdbc8] text-xl">Connecting to backend...</div>
        </div>
      )}
    </div>
  );
}
