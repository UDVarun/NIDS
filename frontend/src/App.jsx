import React from 'react';
import './styles/cyberpunk.css';
import { useAlerts } from './hooks/useAlerts';
import StatusBar from './components/StatusBar';
import StatsPanel from './components/StatsPanel';
import { TrafficTimeline } from './components/TrafficTimeline';
import { SimulatorPanel } from './components/SimulatorPanel';
import { GeoMap } from './components/GeoMap';
import AttackBarChart from './components/AttackBarChart';
import AttackPieChart from './components/AttackPieChart';
import ConfidenceGauge from './components/ConfidenceGauge';
import AlertFeed from './components/AlertFeed';

function App() {
  const { alerts, stats, isConnected } = useAlerts();

  return (
    <div className="app-container" style={{ display: 'flex', flexDirection: 'column', gap: '1rem', padding: '1rem' }}>
      <StatusBar 
        isConnected={isConnected} 
        totalPackets={stats.total_packets} 
        uptime={stats.uptime_seconds} 
      />

      <StatsPanel stats={stats} />

      <TrafficTimeline />
      <SimulatorPanel />

      <div style={{ display: 'flex', gap: '1rem', flex: 1, minHeight: 0 }}>
        {/* Left Column: Alerts */}
        <div style={{ flex: 1.5, display: 'flex', flexDirection: 'column' }}>
          <AlertFeed alerts={alerts} />
        </div>

        {/* Right Column: Visualizations */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <GeoMap alerts={alerts} topCountries={stats.top_countries || {}} />
          <div style={{ display: 'flex', gap: '1rem' }}>
            <AttackPieChart stats={stats} />
            <ConfidenceGauge value={stats.avg_confidence} />
          </div>
          <AttackBarChart breakdown={stats.attack_breakdown} />
        </div>
      </div>
    </div>
  );
}

export default App;
