// src/pages/Health.jsx
import React, { useEffect, useState } from 'react';
import { fetchHealth } from '../api/health';
import StatusBadge from '../components/StatusBadge';

export default function Health() {
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

  if (loading) return <p>Loading health...</p>;
  if (error) return <p>Error: {error}</p>;

  // If health is a dict of subsystems, render as simple list
  const entries = Object.entries(health || {});

  return (
    <div>
      <h2>Health</h2>
      <div className="card">
        <ul className="health-list">
          {entries.map(([key, value]) => {
            const status =
              typeof value === 'object' && value !== null
                ? value.status || value.state || ''
                : '';

            return (
              <li key={key}>
                <strong>{key}</strong>{' '}
                {status && <StatusBadge status={status} />}
              </li>
            );
          })}
        </ul>
      </div>

      <div className="card">
        <h3>Raw Health JSON</h3>
        <pre>{JSON.stringify(health, null, 2)}</pre>
      </div>
    </div>
  );
}
