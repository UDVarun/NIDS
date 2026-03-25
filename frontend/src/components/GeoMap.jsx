/**
 * GeoMap.jsx
 * ==========
 * Real-time world map showing geographic origin of attacks.
 * Uses D3.js Natural Earth projection + TopoJSON world topology.
 */

import { useEffect, useRef, useState } from 'react'
import * as d3 from 'd3'
import * as topojson from 'topojson-client'

const WORLD_TOPO_URL = 'https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json'
const MAP_W = 580
const MAP_H = 300

export function GeoMap({ alerts = [], topCountries = {} }) {
  const svgRef = useRef(null)
  const projectionRef = useRef(null)
  const [markers, setMarkers] = useState([])
  const [loaded, setLoaded] = useState(false)
  const markerIdRef = useRef(0)

  useEffect(() => {
    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()
    const projection = d3.geoNaturalEarth1().scale(93).translate([MAP_W / 2, MAP_H / 2])
    projectionRef.current = projection
    const path = d3.geoPath().projection(projection)

    d3.json(WORLD_TOPO_URL).then(world => {
      const countries = topojson.feature(world, world.objects.countries)
      const borders = topojson.mesh(world, world.objects.countries, (a, b) => a !== b)
      svg.append('g').selectAll('path').data(countries.features).join('path').attr('d', path).attr('fill', '#0d1829')
      svg.append('path').datum(borders).attr('d', path).attr('fill', 'none').attr('stroke', 'rgba(0,212,255,0.12)').attr('stroke-width', 0.4)
      setLoaded(true)
    })
  }, [])

  useEffect(() => {
    if (!projectionRef.current || alerts.length === 0) return
    const latest = alerts[0]
    if (!latest?.is_attack || !latest?.geo?.lat || !latest?.geo?.lon || latest.geo.private) return

    const [x, y] = projectionRef.current([latest.geo.lon, latest.geo.lat]) || [null, null]
    if (!x || !y) return

    const id = ++markerIdRef.current
    setMarkers(prev => [...prev.slice(-29), { id, x, y, created: Date.now() }])
    setTimeout(() => setMarkers(prev => prev.filter(m => m.id !== id)), 10000)
  }, [alerts])

  const topList = Object.entries(topCountries).filter(([c]) => c !== 'Local Network').sort((a, b) => b[1] - a[1]).slice(0, 5)

  return (
    <div className="card" style={{ border: '1px solid rgba(255,45,85,0.2)', borderTop: '2px solid #ff2d55', padding: '16px' }}>
      <div style={{ fontFamily: "'Orbitron', monospace", fontSize: 11, color: '#ff2d55', letterSpacing: 2, marginBottom: 12 }}>// ATTACKER_GEOMAP</div>
      <div style={{ display: 'flex', gap: 16 }}>
        <div style={{ flex: 1, position: 'relative' }}>
          <svg ref={svgRef} width="100%" viewBox={`0 0 ${MAP_W} ${MAP_H}`} style={{ background: '#06090f', borderRadius: 4, border: '1px solid #1a2744' }}>
            {markers.map(m => (
              <g key={m.id}>
                <circle cx={m.x} cy={m.y} r={5} fill="#ff2d55" style={{ filter: 'drop-shadow(0 0 4px #ff2d55)' }} />
              </g>
            ))}
          </svg>
        </div>
        <div style={{ width: 160 }}>
          <div style={{ fontSize: 10, color: '#4a5568', marginBottom: 8 }}>TOP SOURCES</div>
          {topList.map(([c, count]) => (
            <div key={c} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: '#8892a4', marginBottom: 4 }}>
              <span>{c}</span><span>{count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
