import { useState, useEffect, useRef } from 'react';
import axios from 'axios';

export const useAlerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState({
    total_packets: 0,
    total_attacks: 0,
    normal_count: 0,
    attack_breakdown: {},
    uptime_seconds: 0,
    avg_confidence: 0
  });
  const [isConnected, setIsConnected] = useState(false);
  const eventSourceRef = useRef(null);

  const fetchStats = async () => {
    try {
      const resp = await axios.get('/api/stats');
      setStats(resp.data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  const fetchInitialAlerts = async () => {
    try {
      const resp = await axios.get('/api/alerts?limit=20');
      setAlerts(resp.data.alerts);
    } catch (err) {
      console.error('Failed to fetch initial alerts:', err);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchInitialAlerts();
    const statsInterval = setInterval(fetchStats, 5000);

    const connectSSE = () => {
      console.log('Connecting to SSE stream...');
      const es = new EventSource('/api/stream');
      
      es.onopen = () => setIsConnected(true);
      
      es.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'alert') {
          setAlerts(prev => [data, ...prev].slice(0, 100));
          // Proactively update stats on attack to feel responsive
          setStats(prev => ({
            ...prev,
            total_packets: (prev.total_packets || 0) + 1,
            total_attacks: (prev.total_attacks || 0) + 1,
            normal_count: prev.normal_count || 0,
            avg_confidence: data.confidence || 0
          }));
        } else if (data.type === 'stats_update') {
          setStats(data);
        }
      };

      es.onerror = (err) => {
        console.error('SSE Error:', err);
        setIsConnected(false);
        es.close();
        setTimeout(connectSSE, 5000); // Reconnect logic
      };

      eventSourceRef.current = es;
    };

    connectSSE();

    return () => {
      clearInterval(statsInterval);
      if (eventSourceRef.current) eventSourceRef.current.close();
    };
  }, []);

  return { alerts, stats, isConnected };
};
