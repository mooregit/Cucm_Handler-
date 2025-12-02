// src/pages/Dashboard.jsx
import React, { useEffect, useState } from 'react';
import { fetchHealth } from '../api/health';
import StatusBadge from '../components/StatusBadge';

export default function Dashboard() {
  const [health, setHealth] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const data = await fetchHealth();
        setHealth(data);
      } catch (err) {
        setError(err.message || 'Failed to load health');
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  if (loading) return <p>Loading dashboard...</p>;
  if (error) return <p>Error: {error}</p>;

  // Expecting something like { overall: "ok", cucm: {...}, db: {...}, ... }
  const overallStatus = health?.overall || health?.status || 'unknown';

  return (
    <div>
      <h2>Dashboard</h2>
      <div className="card-row">
        <div className="card">
          <h3>Overall System Status</h3>
          <StatusBadge status={overallStatus} />
        </div>
      </div>

      <div className="card">
        <h3>Raw Health Payload</h3>
        <pre>{JSON.stringify(health, null, 2)}</pre>
      </div>
    </div>
  );
}
