import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './components/Dashboard';
import Home from './pages/Home';
import MissionControl from './pages/MissionControl';
import Metrics from './pages/Metrics';
import Comparison from './pages/Comparison';
import Architecture from './pages/Architecture';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/mission-control" replace />} />
        <Route path="/home" element={<Home />} />
        <Route path="/mission-control" element={<MissionControl />} />
        <Route path="/metrics" element={<Metrics />} />
        <Route path="/comparison" element={<Comparison />} />
        <Route path="/architecture" element={<Architecture />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </Router>
  );
}

export default App;
