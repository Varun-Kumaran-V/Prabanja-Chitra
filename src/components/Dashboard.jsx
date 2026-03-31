import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import OrbitViewer from './OrbitViewer';
import { API_BASE } from '../config';

const SNAPSHOT_URL = `${API_BASE}/api/visualization/snapshot`;
const SIMULATE_URL = `${API_BASE}/api/simulate/step`;

export default function Dashboard() {
  const [data, setData] = useState({ satellites: [], debris: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;

    async function simulateAndFetch() {
      try {
        // Run simulation step
        const simRes = await fetch(SIMULATE_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ dt_seconds: 60 })
        });

        if (!simRes.ok) {
          console.warn('Simulation step failed:', simRes.status);
        }

        // Fetch updated snapshot
        const res = await fetch(SNAPSHOT_URL);
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }

        const result = await res.json();

        if (isMounted) {
          setData({
            satellites: result.satellites || [],
            debris: result.debris || []
          });
          setError(null);
          setLoading(false);
        }
      } catch (err) {
        console.error("Fetch error:", err);
        if (isMounted) {
          setError(err.message);
          setLoading(false);
        }
      }
    }

    simulateAndFetch();
    const interval = setInterval(simulateAndFetch, 2000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="flex flex-col h-screen bg-[#10131a]">
      {/* Header */}
      <header className="flex justify-between items-center px-6 py-3 bg-[#1a1d26] border-b border-[#2a2f3a]">
        <div className="flex items-center gap-4">
          <Link 
            to="/mission-control" 
            className="text-[#bbcac6] hover:text-[#4fdbc8] transition-colors flex items-center gap-1"
          >
            <span className="material-symbols-outlined text-lg">arrow_back</span>
            <span className="text-sm">Back</span>
          </Link>
          <div className="w-px h-6 bg-[#3c4947]/30" />
          <h1 className="text-xl font-semibold text-[#e1e2eb]">Prabanja Chitra</h1>
          <span className="text-xs text-[#4fdbc8]/60 uppercase tracking-widest">3D Orbital View</span>
        </div>
        
        <div className="flex gap-4">
          <div className="flex items-center gap-2 bg-[#0b0e14] border border-[#2a2f3a] rounded-lg px-4 py-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#4fdbc8] animate-pulse" />
            <span className="text-sm text-[#e1e2eb]">
              Satellites: <span className="font-bold text-[#4fdbc8] metric-value">{data.satellites.length}</span>
            </span>
          </div>
          <div className="flex items-center gap-2 bg-[#0b0e14] border border-[#2a2f3a] rounded-lg px-4 py-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#ffb4ab]" />
            <span className="text-sm text-[#e1e2eb]">
              Debris: <span className="font-bold text-[#ffb4ab] metric-value">{data.debris.length}</span>
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center z-20 bg-[#10131a]/80 backdrop-blur-sm">
            <div className="glass-panel rounded-2xl p-8 text-center animate-scaleIn">
              <div className="w-12 h-12 border-3 border-[#4fdbc8] border-t-transparent rounded-full animate-spin mx-auto mb-4" />
              <div className="text-lg font-medium text-[#4fdbc8] mb-1">Initializing Orbital View</div>
              <div className="text-sm text-[#6c7086]">Loading constellation data...</div>
            </div>
          </div>
        )}
        
        {error && (
          <div className="absolute inset-0 flex items-center justify-center z-20 bg-[#10131a]/80 backdrop-blur-sm">
            <div className="glass-panel rounded-2xl p-8 max-w-md text-center border border-[#ffb4ab]/30 animate-scaleIn">
              <div className="w-12 h-12 rounded-full bg-[#ffb4ab]/10 flex items-center justify-center mx-auto mb-4">
                <span className="material-symbols-outlined text-[#ffb4ab] text-2xl">error_outline</span>
              </div>
              <div className="text-xl font-semibold text-[#ffb4ab] mb-3">Connection Failed</div>
              <div className="text-sm text-[#e1e2eb] mb-4">{error}</div>
              <div className="text-xs text-[#6c7086] mb-6">
                Make sure backend is running at {API_BASE}
              </div>
              <button 
                onClick={() => window.location.reload()}
                className="btn-secondary px-6 py-2 text-sm"
              >
                Retry Connection
              </button>
            </div>
          </div>
        )}
        
        <OrbitViewer satellites={data.satellites} debris={data.debris} />

        {/* Controls Overlay */}
        <div className="absolute bottom-6 left-6 glass-panel rounded-xl p-4 text-xs text-[#bbcac6]">
          <div className="font-semibold text-[#e1e2eb] mb-2">Controls</div>
          <div className="space-y-1">
            <div>🖱️ Drag to rotate</div>
            <div>⚲ Scroll to zoom</div>
            <div>⌨️ Shift+drag to pan</div>
          </div>
        </div>
      </main>
    </div>
  );
}
