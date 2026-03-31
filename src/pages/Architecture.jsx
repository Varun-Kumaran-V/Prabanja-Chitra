import { Link } from 'react-router-dom';
import { useMemo } from 'react';
import { PageLayout, Card } from '../components/shared';

export default function Architecture() {
  const components = useMemo(() => ({
    frontend: {
      title: 'Frontend UI',
      subtitle: 'React Dashboard',
      description: 'Real-time visualization and mission control interface',
      icon: 'monitor'
    },
    api: {
      title: 'API Layer',
      subtitle: 'FastAPI Backend',
      description: 'REST endpoints for telemetry, decisions, and system control',
      icon: 'api'
    },
    core: [
      { name: 'Telemetry Ingestion', description: 'TLE parsing and satellite state updates', icon: 'satellite_alt' },
      { name: 'Orbit Propagation', description: 'SGP4 propagator for position prediction', icon: 'public' },
      { name: 'Conjunction Detection', description: 'KD-tree spatial filtering + TCA calculation', icon: 'radar' },
      { name: 'Decision Engine', description: 'Threat scoring and maneuver approval logic', icon: 'psychology' },
      { name: 'Maneuver Planner', description: 'Delta-V optimization for collision avoidance', icon: 'rocket_launch' },
      { name: 'Fuel Management', description: 'Tsiolkovsky equation and fuel tracking', icon: 'local_gas_station' }
    ],
    simulation: {
      title: 'Simulation Engine',
      subtitle: 'Orbital Dynamics',
      description: 'Physics simulation for testing and validation',
      icon: 'science'
    }
  }), []);

  const dataFlowSteps = useMemo(() => [
    { step: 1, title: 'Telemetry In → TLE data ingested from NORAD/SpaceTrack', detail: 'Satellite positions and orbital elements updated continuously' },
    { step: 2, title: 'Propagation → SGP4 predicts future positions', detail: '72-hour lookahead window for conjunction analysis' },
    { step: 3, title: 'Detection → KD-tree spatial filtering finds close approaches', detail: 'TCA (Time of Closest Approach) calculated with Newton-Raphson refinement' },
    { step: 4, title: 'Scoring → Composite threat score determines action', detail: 'Weighted by miss distance, urgency, and relative velocity' },
    { step: 5, title: 'Planning → Delta-V maneuver optimized for fuel efficiency', detail: 'Evasion + recovery burn sequence calculated' },
    { step: 6, title: 'Execution → Autonomous upload and post-burn verification', detail: 'Maneuver executed, new orbit verified, system returns to monitoring' }
  ], []);

  const techStack = useMemo(() => [
    { label: 'Frontend', value: 'React + Three.js' },
    { label: 'Backend', value: 'FastAPI + Python' },
    { label: 'Propagation', value: 'SGP4 (skyfield)' },
    { label: 'Spatial Index', value: 'KD-tree (scipy)' }
  ], []);

  return (
    <PageLayout className="px-8 md:px-12 pb-24">
      {/* Header */}
      <div className="text-center mb-16 animate-fadeInUp">
        <span className="text-[0.6875rem] uppercase tracking-[0.2em] text-[#4fdbc8] font-bold">System Design</span>
        <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight mt-4 mb-10">
          System Architecture
        </h1>
        <p className="text-xl text-[#bbcac6] max-w-3xl mx-auto leading-relaxed">
          End-to-end autonomous collision avoidance built on modular, scalable components.
        </p>
      </div>

      {/* Architecture Diagram */}
      <div className="max-w-5xl mx-auto">
        {/* Layer 1: Frontend */}
        <div className="flex justify-center mb-16 animate-fadeInUp delay-100">
          <div className="relative arch-arrow-down">
            <Card variant="elevated" padding="large" className="w-80 border-2 border-[#4fdbc8]/40 glow-accent">
              <span className="material-symbols-outlined text-[#4fdbc8] text-5xl mb-4 block">{components.frontend.icon}</span>
              <h2 className="text-2xl font-bold mb-2">{components.frontend.title}</h2>
              <p className="text-sm text-[#4fdbc8] font-bold uppercase tracking-wider mb-3">{components.frontend.subtitle}</p>
              <p className="text-[#bbcac6] text-sm">{components.frontend.description}</p>
            </Card>
          </div>
        </div>

        {/* Layer 2: API */}
        <div className="flex justify-center mb-16 animate-fadeInUp delay-200">
          <div className="relative arch-arrow-down">
            <Card variant="elevated" padding="large" className="w-80 border-2 border-[#4fdbc8]/40 glow-accent">
              <span className="material-symbols-outlined text-[#4fdbc8] text-5xl mb-4 block">{components.api.icon}</span>
              <h2 className="text-2xl font-bold mb-2">{components.api.title}</h2>
              <p className="text-sm text-[#4fdbc8] font-bold uppercase tracking-wider mb-3">{components.api.subtitle}</p>
              <p className="text-[#bbcac6] text-sm">{components.api.description}</p>
            </Card>
          </div>
        </div>

        {/* Layer 3: Core Engine Modules */}
        <div className="mb-16 animate-fadeInUp delay-300">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-2">Core Engine</h2>
            <p className="text-[#bbcac6]">Autonomous decision-making pipeline</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {components.core.map((module, idx) => (
              <Card
                key={module.name}
                padding="medium"
                className="card-interactive animate-fadeInUp"
                style={{ animationDelay: `${(idx + 4) * 100}ms` }}
              >
                <div className="flex items-center gap-3 mb-3">
                  <span className="material-symbols-outlined text-[#4fdbc8] text-3xl">{module.icon}</span>
                  <h3 className="font-bold text-lg">{module.name}</h3>
                </div>
                <p className="text-[#bbcac6] text-sm leading-relaxed">{module.description}</p>
              </Card>
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
        <div className="flex justify-center mb-16 animate-fadeInUp delay-600">
          <Card variant="elevated" padding="large" className="w-80 border-2 border-[#4fdbc8]/40 glow-accent">
            <span className="material-symbols-outlined text-[#4fdbc8] text-5xl mb-4 block">{components.simulation.icon}</span>
            <h2 className="text-2xl font-bold mb-2">{components.simulation.title}</h2>
            <p className="text-sm text-[#4fdbc8] font-bold uppercase tracking-wider mb-3">{components.simulation.subtitle}</p>
            <p className="text-[#bbcac6] text-sm">{components.simulation.description}</p>
          </Card>
        </div>

        {/* Data Flow Summary */}
        <Card padding="large" className="mb-12 animate-fadeInUp delay-700">
          <h3 className="text-2xl font-bold mb-10 flex items-center gap-3">
            <span className="material-symbols-outlined text-[#4fdbc8] text-4xl">swap_vert</span>
            Data Flow
          </h3>
          <div className="space-y-4">
            {dataFlowSteps.map((flow) => (
              <div key={flow.step} className="flex items-start gap-6 group">
                <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#4fdbc8]/10 flex items-center justify-center text-[#4fdbc8] font-bold text-sm group-hover:bg-[#4fdbc8]/20 transition-colors">
                  {flow.step}
                </div>
                <div>
                  <p className="font-bold mb-1">{flow.title}</p>
                  <p className="text-[#bbcac6] text-sm">{flow.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Tech Stack */}
        <Card padding="large" className="border-l-4 border-[#4fdbc8] bg-gradient-to-r from-[#4fdbc8]/5 to-transparent animate-fadeInUp delay-800">
          <h3 className="text-xl font-bold mb-10 flex items-center gap-2">
            <span className="material-symbols-outlined text-[#4fdbc8]">code</span>
            Technology Stack
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            {techStack.map((tech) => (
              <div key={tech.label}>
                <p className="text-xs uppercase tracking-wider text-[#4fdbc8] mb-2 font-bold">{tech.label}</p>
                <p className="text-sm text-[#bbcac6]">{tech.value}</p>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* CTA */}
      <div className="mt-16 text-center">
        <h2 className="text-3xl font-bold mb-4">Explore The System</h2>
        <p className="text-[#bbcac6] mb-8 text-lg">
          See how these components work together in real-time
        </p>
        <div className="flex gap-6 justify-center">
          <Link to="/comparison" className="btn-secondary px-8 py-4">
            View Comparison
          </Link>
          <Link to="/mission-control" className="btn-primary px-8 py-4">
            Launch Mission Control
          </Link>
        </div>
      </div>
    </PageLayout>
  );
}
