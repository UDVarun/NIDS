import React from 'react';
import { AlertCircle, ChevronRight, Activity } from 'lucide-react';

const AlertFeed = ({ alerts }) => {
  return (
    <div className="cyber-card" style={{ flex: 1.5, maxHeight: '600px', overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
      <h3 style={{ fontSize: '0.9rem', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Activity size={16} /> 
        // INTRUSION_LOG_STREAM
      </h3>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {alerts.length === 0 ? (
          <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)', border: '1px dashed var(--border-cyan)' }}>
            NO INTRUSIONS DETECTED — SYSTEM SECURE
          </div>
        ) : (
          alerts.map((alert, idx) => (
            <div 
              key={idx} 
              className={`cyber-card ${alert.is_attack ? 'attack-alert' : ''}`}
              style={{ 
                padding: '0.75rem', 
                fontSize: '0.85rem', 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                backgroundColor: alert.is_attack ? 'rgba(255, 70, 70, 0.05)' : 'var(--glass-bg)'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{ color: alert.is_attack ? '#ff4646' : '#00ff9d' }}>
                  {alert.is_attack ? <AlertCircle size={18} /> : <div style={{ width: 18, height: 18, borderRadius: '50%', border: '2px solid #00ff9d' }} />}
                </div>
                
                <div>
                  <div style={{ fontWeight: 'bold' }}>
                    {alert.src_ip} <ChevronRight size={12} style={{ verticalAlign: 'middle' }} /> {alert.dst_ip}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                    {new Date(alert.timestamp * 1000).toLocaleTimeString()} | {alert.protocol} | {alert.prediction}
                  </div>
                </div>
              </div>

              {alert.is_attack && (
                <div style={{ textAlign: 'right' }}>
                  <div style={{ color: '#ff4646', fontWeight: 'bold', fontSize: '0.75rem' }}>
                    {alert.attack_type || 'ANOMALY'}
                  </div>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                    CONF: {(alert.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default AlertFeed;
