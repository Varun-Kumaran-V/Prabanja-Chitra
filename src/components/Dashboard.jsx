import { useState, useEffect } from 'react';
import OrbitViewer from './OrbitViewer';
import { API_BASE } from '../config';

const SNAPSHOT_URL = `${API_BASE}/api/visualization/snapshot`;
const SIMULATE_URL = `${API_BASE}/api/simulate/step`;

export default function Dashboard() {
  const [data, setData] = useState({ satellites: [], debris: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function simulateAndFetch() {
      try {
        // Step 1: Run simulation step
        console.log('Running simulation step...');
        console.log("Calling:", API_BASE);

        const simRes = await fetch(SIMULATE_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ dt_seconds: 60 })
        });

        const simText = await simRes.text();
        console.log("RAW SIMULATION RESPONSE:", simText);

        if (!simRes.ok) {
          console.warn('Simulation step failed:', simRes.status);
        } else {
          const simResult = JSON.parse(simText);
          console.log('Simulation step completed:', simResult);
        }

        // Step 2: Fetch updated snapshot
        console.log('Fetching snapshot from:', SNAPSHOT_URL);
        const res = await fetch(SNAPSHOT_URL);
        const text = await res.text();
        console.log("RAW SNAPSHOT RESPONSE:", text);

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }

        const result = JSON.parse(text);
        console.log('Data received:', result);

        setData({
          satellites: result.satellites || [],
          debris: result.debris || []
        });
        setError(null);
        setLoading(false);
      } catch (err) {
        console.error("FULL ERROR:", err);
        setError(err.message);
        setLoading(false);
      }
    }

    // Initial fetch
    simulateAndFetch();

    // Auto-update every 2 seconds
    const interval = setInterval(simulateAndFetch, 2000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="flex flex-col h-screen bg-[#10131a]">
      {/* Header */}
      <header className="flex justify-between items-center px-8 py-4 bg-[#1a1d26] border-b border-[#2a2f3a] shadow-sm">
        <h1 className="text-2xl font-semibold text-[#e1e2eb]">Aether Constellation Manager</h1>
        <div className="flex gap-8">
          <div className="flex items-center gap-2 bg-[#1a1d26] border border-[#2a2f3a] rounded-lg px-4 py-2 shadow-sm">
            <span className="w-2.5 h-2.5 rounded-full bg-[#4fdbc8] animate-pulse" />
            <span className="text-sm text-[#e1e2eb]">
              Satellites: <span className="font-bold text-[#4fdbc8]">{data.satellites.length}</span>
            </span>
          </div>
          <div className="flex items-center gap-2 bg-[#1a1d26] border border-[#2a2f3a] rounded-lg px-4 py-2 shadow-sm">
            <span className="w-2.5 h-2.5 rounded-full bg-[#ffb4ab]" />
            <span className="text-sm text-[#e1e2eb]">
              Debris: <span className="font-bold text-[#ffb4ab]">{data.debris.length}</span>
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 relative">
        {loading && (
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-10 text-center">
            <div className="bg-[#1a1d26] border border-[#2a2f3a] rounded-xl p-8 shadow-lg">
              <div className="text-xl font-medium text-[#4fdbc8] mb-2">Connecting to backend...</div>
              <div className="text-sm text-[#6c7086]">Loading constellation data</div>
            </div>
          </div>
        )}
        {error && (
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-10 text-center">
            <div className="bg-[#1a1d26] border border-[#ffb4ab] rounded-xl p-8 shadow-lg max-w-md">
              <div className="text-xl font-semibold text-[#ffb4ab] mb-3">Connection Failed</div>
              <div className="text-sm text-[#e1e2eb] mb-4">{error}</div>
              <div className="text-xs text-[#6c7086]">
                Make sure backend is running at {API_BASE}
              </div>
            </div>
          </div>
        )}
        <OrbitViewer satellites={data.satellites} debris={data.debris} />
      </main>
    </div>
  );
}
