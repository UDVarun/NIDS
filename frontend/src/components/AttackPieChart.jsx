import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

const AttackPieChart = ({ stats }) => {
  const data = [
    { name: 'Normal', value: stats.normal_count },
    { name: 'Attacks', value: stats.total_attacks }
  ];
  const COLORS = ['#00ff9d', '#ff4646'];

  return (
    <div className="cyber-card" style={{ height: '300px', flex: 1, position: 'relative' }}>
      <h3 style={{ fontSize: '0.9rem', marginBottom: '1rem' }}>// THREAT_LANDSCAPE</h3>
      <ResponsiveContainer width="100%" height="85%">
        <PieChart>
          <Pie
            data={data}
            innerRadius={60}
            outerRadius={80}
            paddingAngle={5}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip 
            contentStyle={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--accent-cyan)' }}
          />
        </PieChart>
      </ResponsiveContainer>
      <div style={{
        position: 'absolute',
        top: '55%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '1.5rem', fontWeight: 'bold', color: 'var(--accent-cyan)' }}>
          {stats.total_attacks}
        </div>
        <div style={{ fontSize: '0.6rem', color: 'var(--text-secondary)' }}>THREATS</div>
      </div>
    </div>
  );
};

export default AttackPieChart;
