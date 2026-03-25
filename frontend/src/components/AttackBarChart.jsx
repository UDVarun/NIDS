import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

const AttackBarChart = ({ breakdown }) => {
  const data = Object.entries(breakdown).map(([name, value]) => ({ name, value }));
  const COLORS = ['#00f3ff', '#ff00ff', '#f3ff00', '#ff4646', '#00ff9d'];

  return (
    <div className="cyber-card" style={{ height: '300px', flex: 1 }}>
      <h3 style={{ fontSize: '0.9rem', marginBottom: '1.5rem' }}>// ATTACK_TYPE_DISTRIBUTION</h3>
      <ResponsiveContainer width="100%" height="80%">
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
          <XAxis 
            dataKey="name" 
            stroke="var(--text-secondary)" 
            fontSize={10} 
            tick={{ fill: 'var(--text-secondary)' }} 
          />
          <YAxis 
            stroke="var(--text-secondary)" 
            fontSize={10} 
            tick={{ fill: 'var(--text-secondary)' }} 
          />
          <Tooltip 
            contentStyle={{ backgroundColor: 'var(--bg-secondary)', borderColor: 'var(--accent-cyan)' }}
            itemStyle={{ color: 'var(--accent-cyan)' }}
          />
          <Bar dataKey="value" minPointSize={10}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default AttackBarChart;
