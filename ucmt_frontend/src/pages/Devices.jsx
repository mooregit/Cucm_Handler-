// src/pages/Devices.jsx
import React, { useEffect, useState } from 'react';
import { fetchDevices } from '../api/devices';
import DataTable from '../components/DataTable';

export default function Devices() {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        setLoading(true);
        const data = await fetchDevices();
        // data can be an array or an object with devices prop; handle both
        setDevices(Array.isArray(data) ? data : data.devices || []);
      } catch (err) {
        setError(err.message || 'Failed to load devices');
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  return (
    <div>
      <h2>Devices</h2>
      {loading && <p>Loading devices...</p>}
      {error && <p>Error: {error}</p>}
      {!loading && !error && <DataTable data={devices} />}
    </div>
  );
}
