/**
 * SimulatorPanel.jsx
 * ==================
 * Built-in attack simulator for demo and testing purposes.
 * Launches real attack simulations (nmap, hping3, SSH brute force)
 * against localhost directly from the dashboard UI.
 *
 * IMPORTANT: This panel is clearly labeled as a LAB TOOL.
 * It only targets localhost — never external IPs.
 */

import { useState, useEffect, useRef } from 'react'
import { Zap, Search, Lock, Trash2, StopCircle } from 'lucide-react'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:5000'

// Button configurations — each maps to a backend simulation command
const BUTTONS = [
  {
    id:      'port_scan',
    label:   'PORT SCAN',
    sub:     'nmap -sT localhost',
    icon:    Search,
    color:   '#00d4ff',
    bgColor: 'rgba(0,212,255,0.08)',
    border:  'rgba(0,212,255,0.3)',
  },
  {
    id:      'syn_flood',
    label:   'SYN FLOOD',
    sub:     'hping3 -S localhost',
    icon:    Zap,
    color:   '#ff2d55',
    bgColor: 'rgba(255,45,85,0.08)',
    border:  'rgba(255,45,85,0.3)',
  },
  {
    id:      'brute_force',
    label:   'BRUTE FORCE',
    sub:     'ssh x@localhost ×60',
    icon:    Lock,
    color:   '#ffb800',
    bgColor: 'rgba(255,184,0,0.08)',
    border:  'rgba(255,184,0,0.3)',
  },
]

export function SimulatorPanel() {
  const [simStatus, setSimStatus]   = useState({ running: false })
  const [loading, setLoading]       = useState(null)   // which button is loading
  const pollRef                     = useRef(null)

  // Poll simulation status every 2 seconds
  useEffect(() => {
    const poll = async () => {
      try {
        const res  = await fetch(`${API_BASE}/api/simulate/status`)
        const data = await res.json()
        setSimStatus(data)
        if (!data.running) setLoading(null)
      } catch (_) {}
    }
    poll()
    pollRef.current = setInterval(poll, 2000)
    return () => clearInterval(pollRef.current)
  }, [])

  const launchSim = async (attackType) => {
    setLoading(attackType)
    try {
      await fetch(`${API_BASE}/api/simulate/${attackType}`, { method: 'POST' })
    } catch (e) {
      console.error('Simulation launch failed:', e)
      setLoading(null)
    }
  }

  const stopSim = async () => {
    try {
      await fetch(`${API_BASE}/api/simulate/stop`, { method: 'POST' })
      setSimStatus({ running: false })
      setLoading(null)
    } catch (_) {}
  }

  const clearAlerts = async () => {
    try {
      await fetch(`${API_BASE}/api/alerts/clear`, { method: 'POST' })
    } catch (_) {}
  }

  return (
    <div className="card" style={{
      border: '1px solid rgba(255,184,0,0.2)',
      borderTop: '2px solid #ffb800',
      padding: '14px 16px',
    }}>
      {/* Header row */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 12,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{
            fontFamily: "'Orbitron', monospace",
            fontSize: 11,
            color: '#ffb800',
            letterSpacing: 2,
          }}>// ATTACK_SIMULATOR</span>
          <span style={{
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 9,
            color: '#4a5568',
            background: 'rgba(255,184,0,0.06)',
            border: '1px solid rgba(255,184,0,0.15)',
            borderRadius: 3,
            padding: '2px 6px',
          }}>LAB USE ONLY · LOCALHOST TARGET</span>
        </div>

        {/* SIMULATION ACTIVE badge */}
        {simStatus.running && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            fontFamily: "'JetBrains Mono', monospace",
            fontSize: 10,
            color: '#ff2d55',
          }}>
            <span style={{
              width: 6, height: 6, borderRadius: '50%',
              background: '#ff2d55',
            }} />
            SIMULATION ACTIVE — {simStatus.elapsed_s}s
          </div>
        )}
      </div>

      {/* Buttons row */}
      <div style={{ display: 'flex', gap: 10, alignItems: 'stretch' }}>
        {BUTTONS.map(btn => {
          const Icon       = btn.icon
          const isActive   = simStatus.running && simStatus.attack_type === btn.id
          const isDisabled = simStatus.running && !isActive
          const isLoading  = loading === btn.id

          return (
            <button
              key={btn.id}
              onClick={() => isActive ? stopSim() : launchSim(btn.id)}
              disabled={isDisabled}
              style={{
                flex: 1,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 6,
                padding: '10px 8px',
                background: isActive ? btn.bgColor : 'transparent',
                border: `1px solid ${isActive ? btn.color : btn.border}`,
                borderRadius: 6,
                cursor: isDisabled ? 'not-allowed' : 'pointer',
                opacity: isDisabled ? 0.35 : 1,
                transition: 'all 0.2s',
              }}
            >
              <Icon
                size={16}
                color={isActive ? btn.color : '#8892a4'}
              />
              <span style={{
                fontFamily: "'Orbitron', monospace",
                fontSize: 9,
                color: isActive ? btn.color : '#8892a4',
                letterSpacing: 1,
              }}>{btn.label}</span>
              <span style={{
                fontFamily: "'JetBrains Mono', monospace",
                fontSize: 9,
                color: '#4a5568',
              }}>{isLoading ? 'launching...' : isActive ? 'running...' : btn.sub}</span>
            </button>
          )
        })}

        {/* Divider */}
        <div style={{
          width: 1,
          background: '#1a2744',
          margin: '0 4px',
        }} />

        {/* Stop button */}
        {simStatus.running && (
          <button
            onClick={stopSim}
            style={{
              display: 'flex', flexDirection: 'column',
              alignItems: 'center', gap: 6,
              padding: '10px 12px',
              background: 'rgba(255,45,85,0.08)',
              border: '1px solid rgba(255,45,85,0.3)',
              borderRadius: 6, cursor: 'pointer',
            }}
          >
            <StopCircle size={16} color="#ff2d55" />
            <span style={{
              fontFamily: "'Orbitron', monospace",
              fontSize: 9, color: '#ff2d55', letterSpacing: 1,
            }}>STOP</span>
          </button>
        )}

        {/* Clear alerts button */}
        <button
          onClick={clearAlerts}
          style={{
            display: 'flex', flexDirection: 'column',
            alignItems: 'center', gap: 6,
            padding: '10px 12px',
            background: 'transparent',
            border: '1px solid rgba(136,146,164,0.2)',
            borderRadius: 6, cursor: 'pointer',
          }}
        >
          <Trash2 size={16} color="#4a5568" />
          <span style={{
            fontFamily: "'Orbitron', monospace",
            fontSize: 9, color: '#4a5568', letterSpacing: 1,
          }}>CLEAR</span>
        </button>
      </div>
    </div>
  )
}
