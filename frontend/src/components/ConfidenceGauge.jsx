import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

const ConfidenceGauge = ({ value }) => {
  const data = [
    { value: value },
    { value: 1.0 - value }
  ];
  
  const COLORS = [value > 0.8 ? '#00ff9d' : '#ffaa00', 'rgba(255,255,255,0.05)'];

  return (
    <div className="cyber-card" style={{ height: '300px', flex: 0.5 }}>
      <h3 style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>// ML_CONFIDENCE</h3>
      <div style={{ height: '200px', width: '100%', position: 'relative' }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              startAngle={180}
              endAngle={0}
              innerRadius={70}
              outerRadius={90}
              dataKey="value"
              stroke="none"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index]} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
        <div style={{
          position: 'absolute',
          bottom: '20%',
          left: '50%',
          transform: 'translateX(-50%)',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: COLORS[0] }}>
            {(value * 100).toFixed(0)}%
          </div>
          <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)' }}>THRESHOLD: 46%</div>
        </div>
      </div>
    </div>
  );
};

export default ConfidenceGauge;
