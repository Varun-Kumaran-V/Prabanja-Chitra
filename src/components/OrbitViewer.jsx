import { useRef, useEffect, useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Stars } from '@react-three/drei';
import * as THREE from 'three';
import { API_BASE } from '../config';

const MAX_SATELLITES = 500;
const MAX_DEBRIS = 200;

// Simple Earth sphere
function Earth() {
  return (
    <mesh>
      <sphereGeometry args={[1, 32, 32]} />
      <meshPhongMaterial
        color="#1a4d7c"
        emissive="#0a1929"
        emissiveIntensity={0.1}
      />
    </mesh>
  );
}

// Static space objects - no animation
function SpaceObjects({ objects, type }) {
  if (!objects || objects.length === 0) return null;

  const color = type === 'satellite' ? '#00ff00' : '#888888';
  const size = type === 'satellite' ? 0.025 : 0.018;

  return (
    <group>
      {objects.map((obj, i) => {
        const id = obj.id || obj.norad_id || `${type}-${i}`;
        return (
          <mesh key={id} position={[obj.x, obj.y, obj.z]}>
            <sphereGeometry args={[size, 8, 8]} />
            <meshBasicMaterial color={color} />
          </mesh>
        );
      })}
    </group>
  );
}

// Static scene - no animation
function Scene({ satellites, debris }) {
  return (
    <>
      <ambientLight intensity={0.3} />
      <pointLight position={[50, 30, 50]} intensity={1.5} />
      <Stars radius={200} depth={100} count={3000} factor={6} saturation={0} />

      <Earth />

      <SpaceObjects objects={satellites} type="satellite" />
      <SpaceObjects objects={debris} type="debris" />

      <OrbitControls
        enablePan={true}
        enableZoom={true}
        enableRotate={true}
        minDistance={2}
        maxDistance={50}
      />
    </>
  );
}

// Stats overlay
function StatsOverlay({ satellites, debris, error }) {
  return (
    <div style={{
      position: 'absolute',
      top: 16,
      right: 16,
      zIndex: 10,
      fontFamily: "'SF Mono', 'Consolas', monospace",
      fontSize: 12,
    }}>
      {error && (
        <div style={{
          background: 'rgba(255, 50, 50, 0.9)',
          color: '#fff',
          padding: '8px 12px',
          borderRadius: 6,
          marginBottom: 8,
        }}>
          {error}
        </div>
      )}

      <div style={{
        background: 'rgba(0, 0, 0, 0.75)',
        borderRadius: 8,
        padding: 12,
        border: '1px solid rgba(255, 255, 255, 0.1)',
        minWidth: 160,
      }}>
        <div style={{ color: '#888', marginBottom: 8, fontSize: 10 }}>
          ORBITAL OBJECTS
        </div>

        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 6 }}>
          <div style={{
            width: 8, height: 8, borderRadius: '50%',
            background: '#00ff00', marginRight: 8,
          }} />
          <span style={{ color: '#ccc', flex: 1 }}>Satellites</span>
          <span style={{ color: '#00ff00', fontWeight: 600 }}>
            {satellites}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 6 }}>
          <div style={{
            width: 8, height: 8, borderRadius: '50%',
            background: '#888', marginRight: 8,
          }} />
          <span style={{ color: '#ccc', flex: 1 }}>Debris</span>
          <span style={{ color: '#888', fontWeight: 600 }}>
            {debris}
          </span>
        </div>
      </div>
    </div>
  );
}

export default function OrbitViewer({
  apiEndpoint = `${API_BASE}/api/visualization/snapshot`,
}) {
  const [satellites, setSatellites] = useState([]);
  const [debris, setDebris] = useState([]);
  const [error, setError] = useState(null);
  const hasLoadedRef = useRef(false);

  useEffect(() => {
    // Fetch ONCE only
    if (hasLoadedRef.current) return;
    hasLoadedRef.current = true;

    const fetchSnapshot = async () => {
      try {
        console.log("Fetching snapshot once from:", apiEndpoint);
        const res = await fetch(apiEndpoint);

        if (!res.ok) {
          throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }

        const data = await res.json();

        // Extract and validate objects
        const allSatellites = data?.satellites || data?.objects?.filter(o => o.type === 'satellite') || [];
        const allDebris = data?.debris || data?.objects?.filter(o => o.type === 'debris') || [];

        // Validate coordinates
        const validateObject = (obj) => {
          if (!obj || typeof obj !== 'object') return false;
          const { x, y, z } = obj;
          return isFinite(x) && isFinite(y) && isFinite(z);
        };

        const validSatellites = allSatellites.filter(validateObject).slice(0, MAX_SATELLITES);
        const validDebris = allDebris.filter(validateObject).slice(0, MAX_DEBRIS);

        console.log("Rendering subset:", validSatellites.length + validDebris.length);
        console.log("Satellites:", validSatellites.length);
        console.log("Debris:", validDebris.length);

        // Set state ONCE - no further updates
        setSatellites(validSatellites);
        setDebris(validDebris);
        setError(null);
      } catch (err) {
        console.error("Fetch error:", err);
        setError(err.message);
      }
    };

    fetchSnapshot();
  }, [apiEndpoint]);

  return (
    <div style={{
      width: '100%',
      height: '100%',
      background: 'radial-gradient(ellipse at center, #0a0a1a 0%, #000000 100%)',
      position: 'relative',
      overflow: 'hidden',
    }}>
      <StatsOverlay
        satellites={satellites.length}
        debris={debris.length}
        error={error}
      />

      <Canvas
        camera={{ position: [0, 3, 8], fov: 55 }}
        gl={{
          antialias: false,
          powerPreference: 'high-performance',
        }}
        frameloop="demand"
      >
        <Scene satellites={satellites} debris={debris} />
      </Canvas>
    </div>
  );
}
