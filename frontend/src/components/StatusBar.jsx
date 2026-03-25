import React from 'react';
import { Activity, Shield, Terminal, Clock } from 'lucide-react';

const StatusBar = ({ isConnected, totalPackets, uptime }) => {
  const formatUptime = (sec) => {
    const hrs = Math.floor(sec / 3600);
    const mins = Math.floor((sec % 3600) / 60);
    const secs = sec % 60;
    return `${hrs}h ${mins}m ${secs}s`;
  };

  return (
    <div className="cyber-card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '0.75rem 1.5rem', marginBottom: '1rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <Shield size={32} color="#00f3ff" />
        <div>
          <h2 style={{ margin: 0, fontSize: '1.2rem' }}>NIDS <span className="glitch-text">SENTINEL</span></h2>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>AI-POWERED INTRUSION DETECTION</div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Activity size={16} color={isConnected ? '#00ff9d' : '#ff4646'} />
          <span style={{ fontSize: '0.8rem', color: isConnected ? '#00ff9d' : '#ff4646' }}>
            {isConnected ? 'LIVE' : 'DISCONNECTED'}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Terminal size={16} color="var(--accent-cyan)" />
          <span style={{ fontSize: '0.8rem' }}>{(totalPackets || 0).toLocaleString()} PACKETS</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <Clock size={16} color="var(--accent-cyan)" />
          <span style={{ fontSize: '0.8rem' }}>UPTIME: {formatUptime(uptime)}</span>
        </div>
      </div>
    </div>
  );
};

export default StatusBar;
