import { Link } from 'react-router-dom';

export default function Architecture() {
  // Architecture components
  const components = {
    frontend: {
      title: 'Frontend UI',
      subtitle: 'React Dashboard',
      description: 'Real-time visualization and mission control interface',
      icon: 'monitor',
      color: '#4fdbc8'
    },
    api: {
      title: 'API Layer',
      subtitle: 'FastAPI Backend',
      description: 'REST endpoints for telemetry, decisions, and system control',
      icon: 'api',
      color: '#4fdbc8'
    },
    core: [
      {
        name: 'Telemetry Ingestion',
        description: 'TLE parsing and satellite state updates',
        icon: 'satellite_alt'
      },
      {
        name: 'Orbit Propagation',
        description: 'SGP4 propagator for position prediction',
        icon: 'public'
      },
      {
        name: 'Conjunction Detection',
        description: 'KD-tree spatial filtering + TCA calculation',
        icon: 'radar'
      },
      {
        name: 'Decision Engine',
        description: 'Threat scoring and maneuver approval logic',
        icon: 'psychology'
      },
      {
        name: 'Maneuver Planner',
        description: 'Delta-V optimization for collision avoidance',
        icon: 'rocket_launch'
      },
      {
        name: 'Fuel Management',
        description: 'Tsiolkovsky equation and fuel tracking',
        icon: 'local_gas_station'
      }
    ],
    simulation: {
      title: 'Simulation Engine',
      subtitle: 'Orbital Dynamics',
      description: 'Physics simulation for testing and validation',
      icon: 'science',
      color: '#4fdbc8'
    }
  };

  return (
    <div className="min-h-screen bg-[#10131a] text-[#e1e2eb] font-['Inter']">

      <style>{`
        .material-symbols-outlined { font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24; }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fadeIn { animation: fadeIn 0.6s ease-out forwards; }
        .delay-1 { animation-delay: 100ms; }
        .delay-2 { animation-delay: 200ms; }
        .delay-3 { animation-delay: 300ms; }
        .delay-4 { animation-delay: 400ms; }

        /* Arrow styling */
        .arrow-down::after {
          content: '';
          position: absolute;
          left: 50%;
          bottom: -24px;
          transform: translateX(-50%);
          width: 2px;
          height: 16px;
          background: linear-gradient(to bottom, #4fdbc8, #4fdbc8 50%, transparent);
        }
        .arrow-down::before {
          content: '';
          position: absolute;
          left: 50%;
          bottom: -24px;
          transform: translateX(-50%);
          width: 0;
          height: 0;
          border-left: 6px solid transparent;
          border-right: 6px solid transparent;
          border-top: 8px solid #4fdbc8;
        }

        .arrow-right::after {
          content: '';
          position: absolute;
          right: -24px;
          top: 50%;
          transform: translateY(-50%);
          width: 16px;
          height: 2px;
          background: linear-gradient(to right, #4fdbc8, #4fdbc8 50%, transparent);
        }
        .arrow-right::before {
          content: '';
          position: absolute;
          right: -24px;
          top: 50%;
          transform: translateY(-50%);
          width: 0;
          height: 0;
          border-top: 6px solid transparent;
          border-bottom: 6px solid transparent;
          border-left: 8px solid #4fdbc8;
        }

        .bidirectional-arrow::after {
          content: '';
          position: absolute;
          left: 50%;
          bottom: -32px;
          transform: translateX(-50%);
          width: 2px;
          height: 24px;
          background: #4fdbc8;
        }
        .bidirectional-arrow::before {
          content: '';
          position: absolute;
          left: 50%;
          bottom: -32px;
          transform: translateX(-50%) rotate(180deg);
          width: 0;
          height: 0;
          border-left: 6px solid transparent;
          border-right: 6px solid transparent;
          border-top: 8px solid #4fdbc8;
        }
      `}</style>

      {/* Top Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-[#1d2026]/80 backdrop-blur-xl border-b border-[#4fdbc8]/15 shadow-[0_24px_48px_rgba(0,0,0,0.4)]">
        <div className="flex justify-between items-center h-16 px-8 max-w-[1440px] mx-auto">
          <div className="text-xl font-semibold tracking-[-0.02em] text-[#e1e2eb]">Prabanja Chitra</div>
          <div className="hidden md:flex items-center gap-8">
            <Link className="text-[#e1e2eb]/70 hover:text-[#e1e2eb] transition-colors" to="/home">Home</Link>
            <Link className="text-[#e1e2eb]/70 hover:text-[#e1e2eb] transition-colors" to="/mission-control">Mission Control</Link>
            <Link className="text-[#e1e2eb]/70 hover:text-[#e1e2eb] transition-colors" to="/comparison">Comparison</Link>
            <Link className="text-[#e1e2eb]/70 hover:text-[#e1e2eb] transition-colors" to="/metrics">Metrics</Link>
            <Link className="text-[#4fdbc8] border-b-2 border-[#4fdbc8] pb-1 font-bold" to="/architecture">Architecture</Link>
          </div>
          <Link to="/dashboard" className="bg-[#4fdbc8] text-[#003731] px-5 py-2 rounded-xl font-semibold text-sm hover:opacity-90 transition-all">
            Launch Dashboard
          </Link>
        </div>
      </nav>

      {/* Main Content */}
      <main className="pt-32 pb-24 px-6 md:px-12 max-w-[1440px] mx-auto">
        {/* Header */}
        <div className="text-center mb-16 animate-fadeIn">
          <span className="text-[0.6875rem] uppercase tracking-[0.2em] text-[#4fdbc8] font-bold">System Design</span>
          <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight mt-4 mb-6">
            System Architecture
          </h1>
          <p className="text-xl text-[#bbcac6] max-w-3xl mx-auto leading-relaxed">
            End-to-end autonomous collision avoidance built on modular, scalable components.
          </p>
        </div>

        {/* Architecture Diagram */}
        <div className="max-w-5xl mx-auto">
          {/* Layer 1: Frontend */}
          <div className="flex justify-center mb-16 animate-fadeIn delay-1">
            <div className="relative">
              <div className="bg-gradient-to-br from-[#1d2026] to-[#191c22] p-8 rounded-2xl border-2 border-[#4fdbc8]/40 shadow-xl shadow-[#4fdbc8]/10 w-80 relative arrow-down">
                <span className="material-symbols-outlined text-[#4fdbc8] text-5xl mb-4 block">{components.frontend.icon}</span>
                <h2 className="text-2xl font-bold mb-2">{components.frontend.title}</h2>
                <p className="text-sm text-[#4fdbc8] font-bold uppercase tracking-wider mb-3">{components.frontend.subtitle}</p>
                <p className="text-[#bbcac6] text-sm">{components.frontend.description}</p>
              </div>
            </div>
          </div>

          {/* Layer 2: API */}
          <div className="flex justify-center mb-16 animate-fadeIn delay-2">
            <div className="relative">
              <div className="bg-gradient-to-br from-[#1d2026] to-[#191c22] p-8 rounded-2xl border-2 border-[#4fdbc8]/40 shadow-xl shadow-[#4fdbc8]/10 w-80 relative arrow-down">
                <span className="material-symbols-outlined text-[#4fdbc8] text-5xl mb-4 block">{components.api.icon}</span>
                <h2 className="text-2xl font-bold mb-2">{components.api.title}</h2>
                <p className="text-sm text-[#4fdbc8] font-bold uppercase tracking-wider mb-3">{components.api.subtitle}</p>
                <p className="text-[#bbcac6] text-sm">{components.api.description}</p>
              </div>
            </div>
          </div>

          {/* Layer 3: Core Engine Modules */}
          <div className="mb-16 animate-fadeIn delay-3">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold mb-2">Core Engine</h2>
              <p className="text-[#bbcac6]">Autonomous decision-making pipeline</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {components.core.map((module, idx) => (
                <div
                  key={module.name}
                  className="bg-[#1d2026] p-6 rounded-xl border border-[#4fdbc8]/20 hover:border-[#4fdbc8]/50 transition-all hover:-translate-y-1"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <span className="material-symbols-outlined text-[#4fdbc8] text-3xl">{module.icon}</span>
                    <h3 className="font-bold text-lg">{module.name}</h3>
                  </div>
                  <p className="text-[#bbcac6] text-sm leading-relaxed">{module.description}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Arrow between Core and Simulation */}
          <div className="flex justify-center mb-8">
            <div className="flex flex-col items-center">
              <div className="w-0.5 h-8 bg-[#4fdbc8]"></div>
              <div className="w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-t-[8px] border-t-[#4fdbc8]"></div>
            </div>
          </div>

          {/* Layer 4: Simulation Engine */}
          <div className="flex justify-center mb-16 animate-fadeIn delay-4">
            <div className="bg-gradient-to-br from-[#1d2026] to-[#191c22] p-8 rounded-2xl border-2 border-[#4fdbc8]/40 shadow-xl shadow-[#4fdbc8]/10 w-80">
              <span className="material-symbols-outlined text-[#4fdbc8] text-5xl mb-4 block">{components.simulation.icon}</span>
              <h2 className="text-2xl font-bold mb-2">{components.simulation.title}</h2>
              <p className="text-sm text-[#4fdbc8] font-bold uppercase tracking-wider mb-3">{components.simulation.subtitle}</p>
              <p className="text-[#bbcac6] text-sm">{components.simulation.description}</p>
            </div>
          </div>

          {/* Data Flow Summary */}
          <div className="bg-[#1d2026] rounded-2xl p-8 border border-[#4fdbc8]/20">
            <h3 className="text-2xl font-bold mb-6 flex items-center gap-3">
              <span className="material-symbols-outlined text-[#4fdbc8] text-4xl">swap_vert</span>
              Data Flow
            </h3>
            <div className="space-y-4">
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#4fdbc8]/10 flex items-center justify-center text-[#4fdbc8] font-bold text-sm">1</div>
                <div>
                  <p className="font-bold mb-1">Telemetry In → TLE data ingested from NORAD/SpaceTrack</p>
                  <p className="text-[#bbcac6] text-sm">Satellite positions and orbital elements updated continuously</p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#4fdbc8]/10 flex items-center justify-center text-[#4fdbc8] font-bold text-sm">2</div>
                <div>
                  <p className="font-bold mb-1">Propagation → SGP4 predicts future positions</p>
                  <p className="text-[#bbcac6] text-sm">72-hour lookahead window for conjunction analysis</p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#4fdbc8]/10 flex items-center justify-center text-[#4fdbc8] font-bold text-sm">3</div>
                <div>
                  <p className="font-bold mb-1">Detection → KD-tree spatial filtering finds close approaches</p>
                  <p className="text-[#bbcac6] text-sm">TCA (Time of Closest Approach) calculated with Newton-Raphson refinement</p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#4fdbc8]/10 flex items-center justify-center text-[#4fdbc8] font-bold text-sm">4</div>
                <div>
                  <p className="font-bold mb-1">Scoring → Composite threat score determines action</p>
                  <p className="text-[#bbcac6] text-sm">Weighted by miss distance, urgency, and relative velocity</p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#4fdbc8]/10 flex items-center justify-center text-[#4fdbc8] font-bold text-sm">5</div>
                <div>
                  <p className="font-bold mb-1">Planning → Delta-V maneuver optimized for fuel efficiency</p>
                  <p className="text-[#bbcac6] text-sm">Evasion + recovery burn sequence calculated</p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#4fdbc8]/10 flex items-center justify-center text-[#4fdbc8] font-bold text-sm">6</div>
                <div>
                  <p className="font-bold mb-1">Execution → Autonomous upload and post-burn verification</p>
                  <p className="text-[#bbcac6] text-sm">Maneuver executed, new orbit verified, system returns to monitoring</p>
                </div>
              </div>
            </div>
          </div>

          {/* Tech Stack */}
          <div className="mt-12 bg-gradient-to-r from-[#4fdbc8]/5 to-transparent border-l-4 border-[#4fdbc8] rounded-xl p-8">
            <h3 className="text-xl font-bold mb-6 flex items-center gap-2">
              <span className="material-symbols-outlined text-[#4fdbc8]">code</span>
              Technology Stack
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div>
                <p className="text-xs uppercase tracking-wider text-[#4fdbc8] mb-2 font-bold">Frontend</p>
                <p className="text-sm text-[#bbcac6]">React + Three.js</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wider text-[#4fdbc8] mb-2 font-bold">Backend</p>
                <p className="text-sm text-[#bbcac6]">FastAPI + Python</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wider text-[#4fdbc8] mb-2 font-bold">Propagation</p>
                <p className="text-sm text-[#bbcac6]">SGP4 (skyfield)</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-wider text-[#4fdbc8] mb-2 font-bold">Spatial Index</p>
                <p className="text-sm text-[#bbcac6]">KD-tree (scipy)</p>
              </div>
            </div>
          </div>
        </div>

        {/* CTA */}
        <div className="mt-16 text-center">
          <h2 className="text-3xl font-bold mb-4">Explore The System</h2>
          <p className="text-[#bbcac6] mb-8 text-lg">
            See how these components work together in real-time
          </p>
          <div className="flex gap-4 justify-center">
            <Link to="/comparison" className="bg-[#272a31] text-[#e1e2eb] px-8 py-4 rounded-xl font-bold hover:bg-[#32353c] hover:-translate-y-1 transition-all">
              View Comparison
            </Link>
            <Link to="/mission-control" className="bg-[#4fdbc8] text-[#003731] px-8 py-4 rounded-xl font-bold shadow-[0_0_20px_rgba(79,219,200,0.3)] hover:opacity-90 hover:-translate-y-1 transition-all">
              Launch Mission Control
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-[#0b0e14] w-full py-12 border-t border-[#4fdbc8]/10">
        <div className="flex flex-col md:flex-row justify-between items-center px-12 max-w-[1440px] mx-auto gap-8">
          <div className="flex flex-col items-center md:items-start gap-2">
            <div className="text-lg font-bold text-[#e1e2eb]">Prabanja Chitra</div>
            <p className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#e1e2eb]/40">
              © 2024 Prabanja Chitra. Orbital Autonomy Initiative.
            </p>
          </div>
          <div className="flex gap-8">
            <a className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#e1e2eb]/40 hover:text-[#4fdbc8] transition-colors" href="#">Documentation</a>
            <a className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#e1e2eb]/40 hover:text-[#4fdbc8] transition-colors" href="#">Mission Logs</a>
            <a className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#e1e2eb]/40 hover:text-[#4fdbc8] transition-colors" href="#">Privacy</a>
            <a className="text-[0.6875rem] uppercase tracking-[0.05em] text-[#e1e2eb]/40 hover:text-[#4fdbc8] transition-colors" href="#">Contact</a>
          </div>
          <div className="flex gap-4">
            <span className="material-symbols-outlined text-[#e1e2eb]/40 hover:text-[#4fdbc8] cursor-pointer">public</span>
            <span className="material-symbols-outlined text-[#e1e2eb]/40 hover:text-[#4fdbc8] cursor-pointer">terminal</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
