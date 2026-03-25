import React from 'react';
import { Activity, AlertTriangle, ShieldCheck, Zap } from 'lucide-react';

const StatCard = ({ title, value, icon: Icon, color }) => (
  <div className="cyber-card" style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '1rem' }}>
    <div style={{ background: `rgba(${color}, 0.1)`, padding: '0.75rem', borderRadius: '4px' }}>
      <Icon size={24} color={`rgb(${color})`} />
    </div>
    <div>
      <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>{title}</div>
      <div style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>{value}</div>
    </div>
  </div>
);

const StatsPanel = ({ stats }) => {
  return (
    <div style={{ display: 'flex', gap: '1rem', width: '100%', marginBottom: '1rem' }}>
      <StatCard 
        title="Total Traffic" 
        value={(stats.total_packets || 0).toLocaleString()} 
        icon={Activity} 
        color="0, 243, 255" 
      />
      <StatCard 
        title="Attacks Blocked" 
        value={(stats.total_attacks || 0).toLocaleString()} 
        icon={AlertTriangle} 
        color="255, 70, 70" 
      />
      <StatCard 
        title="Normal Traffic" 
        value={(stats.normal_count || 0).toLocaleString()} 
        icon={ShieldCheck} 
        color="0, 255, 157" 
      />
      <StatCard 
        title="ML Confidence" 
        value={`${(stats.avg_confidence * 100).toFixed(1)}%`} 
        icon={Zap} 
        color="243, 255, 0" 
      />
    </div>
  );
};

export default StatsPanel;
