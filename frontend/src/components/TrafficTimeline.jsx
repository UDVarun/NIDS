/**
 * TrafficTimeline.jsx
 * ===================
 * Real-time 60-second rolling traffic chart.
 * Shows normal vs attack packets per second as two filled area lines.
 * Self-contained: polls /api/timeline every 1000ms internally.
 *
 * Props: none (fetches its own data)
 */

import { useState, useEffect, useRef } from 'react'
import {
  AreaChart, Area, XAxis, YAxis, Tooltip,
  ResponsiveContainer, CartesianGrid, ReferenceLine
} from 'recharts'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000'

// Format x-axis tick: convert unix timestamp to relative "Xs ago" label
function formatTick(ts) {
  const now    = Math.floor(Date.now() / 1000)
  const delta  = now - ts
  if (delta <= 0)  return 'now'
  if (delta <= 10) return `${delta}s`
  if (delta % 10 === 0) return `${delta}s`
  return ''   // hide intermediate ticks for cleaner look
}

// Custom tooltip shown on hover
function TimelineTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const normal = payload.find(p => p.dataKey === 'normal')?.value ?? 0
  const attack = payload.find(p => p.dataKey === 'attack')?.value ?? 0
  return (
    <div style={{
      background: '#0a0f1e',
      border: '1px solid #1a2744',
      borderRadius: 4,
      padding: '8px 12px',
      fontFamily: "'JetBrains Mono', monospace",
      fontSize: 11,
    }}>
      <div style={{ color: '#00ff88', marginBottom: 2 }}>
        Normal: {normal} pkt/s
      </div>
      <div style={{ color: '#ff2d55' }}>
        Attack: {attack} pkt/s
      </div>
    </div>
  )
}

export function TrafficTimeline() {
  const [data, setData]         = useState([])
  const [peakAttack, setPeak]   = useState(0)
  const intervalRef             = useRef(null)

  useEffect(() => {
    // Fetch timeline data from backend
    const fetchTimeline = async () => {
      try {
        const res    = await fetch(`${API_BASE}/api/timeline`)
        const buckets = await res.json()

        // Add a 'time' label for the x-axis
        const formatted = buckets.map((b, i) => ({
          ...b,
          label:    formatTick(b.t),
          idx:      i,
          isAttack: b.attack > 0,
        }))

        setData(formatted)
        setPeak(Math.max(...buckets.map(b => b.attack), 0))
      } catch (e) {
        // Silently ignore fetch errors — chart just stops updating
      }
    }

    fetchTimeline()  // Immediate first fetch
    intervalRef.current = setInterval(fetchTimeline, 1000)

    return () => clearInterval(intervalRef.current)
  }, [])

  const maxY = Math.max(peakAttack, 10, ...data.map(d => d.normal)) * 1.3

  return (
    <div className="card" style={{ padding: '16px 16px 8px', border: '1px solid rgba(0,212,255,0.2)', borderTop: '2px solid #00d4ff' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 12,
      }}>
        <span style={{
          fontFamily: "'Orbitron', monospace",
          fontSize: 11,
          color: '#00d4ff',
          letterSpacing: 2,
        }}>// TRAFFIC_TIMELINE</span>

        <div style={{ display: 'flex', gap: 16 }}>
          {/* Legend */}
          <span style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 10,
            color: '#00ff88',
            display: 'flex',
            alignItems: 'center',
            gap: 5,
          }}>
            <span style={{
              display: 'inline-block', width: 20, height: 2,
              background: '#00ff88',
            }} />
            NORMAL
          </span>
          <span style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 10,
            color: '#ff2d55',
            display: 'flex',
            alignItems: 'center',
            gap: 5,
          }}>
            <span style={{
              display: 'inline-block', width: 20, height: 2,
              background: '#ff2d55',
            }} />
            ATTACK
          </span>
        </div>
      </div>

      {/* Chart */}
      <ResponsiveContainer width="100%" height={140}>
        <AreaChart
          data={data}
          margin={{ top: 4, right: 8, left: 0, bottom: 0 }}
        >
          <defs>
            {/* Green gradient fill for normal traffic area */}
            <linearGradient id="gradNormal" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"   stopColor="#00ff88" stopOpacity={0.25} />
              <stop offset="100%" stopColor="#00ff88" stopOpacity={0.02} />
            </linearGradient>
            {/* Red gradient fill for attack traffic area */}
            <linearGradient id="gradAttack" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%"   stopColor="#ff2d55" stopOpacity={0.4} />
              <stop offset="100%" stopColor="#ff2d55" stopOpacity={0.02} />
            </linearGradient>
          </defs>

          <CartesianGrid
            strokeDasharray="2 4"
            stroke="rgba(255,255,255,0.04)"
            vertical={false}
          />

          <XAxis
            dataKey="label"
            tick={{ fontFamily: "'JetBrains Mono', monospace",
                    fontSize: 9, fill: '#4a5568' }}
            axisLine={false}
            tickLine={false}
            interval={9}   // Show tick every 10 seconds
          />

          <YAxis
            domain={[0, maxY]}
            tick={{ fontFamily: "'JetBrains Mono', monospace",
                    fontSize: 9, fill: '#4a5568' }}
            axisLine={false}
            tickLine={false}
            width={28}
          />

          <Tooltip content={<TimelineTooltip />} />

          {/* Normal traffic — green area */}
          <Area
            type="monotone"
            dataKey="normal"
            stroke="#00ff88"
            strokeWidth={1.5}
            fill="url(#gradNormal)"
            dot={false}
            activeDot={{ r: 3, fill: '#00ff88' }}
            animationDuration={200}
          />

          {/* Attack traffic — red area, drawn on top of normal */}
          <Area
            type="monotone"
            dataKey="attack"
            stroke="#ff2d55"
            strokeWidth={2}
            fill="url(#gradAttack)"
            dot={false}
            activeDot={{ r: 3, fill: '#ff2d55' }}
            animationDuration={200}
            style={{ filter: peakAttack > 0
              ? 'drop-shadow(0 0 4px rgba(255,45,85,0.6))'
              : 'none' }}
          />

          {/* Threshold reference line at 10 pkt/s */}
          <ReferenceLine
            y={10}
            stroke="rgba(255,184,0,0.3)"
            strokeDasharray="3 3"
            label={{
              value: 'threshold',
              position: 'insideTopRight',
              fontSize: 9,
              fill: 'rgba(255,184,0,0.5)',
              fontFamily: "'JetBrains Mono', monospace",
            }}
          />
        </AreaChart>
      </ResponsiveContainer>

      {/* Live stats below chart */}
      <div style={{
        display: 'flex',
        gap: 20,
        marginTop: 6,
        paddingTop: 6,
        borderTop: '1px solid #1a2744',
      }}>
        <span style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 10,
          color: '#4a5568',
        }}>
          PEAK ATTACK RATE:&nbsp;
          <span style={{ color: '#ff2d55' }}>{peakAttack} pkt/s</span>
        </span>
        <span style={{
          fontFamily: "'JetBrains Mono', monospace",
          fontSize: 10,
          color: '#4a5568',
        }}>
          WINDOW: 60s rolling
        </span>
      </div>
    </div>
  )
}
