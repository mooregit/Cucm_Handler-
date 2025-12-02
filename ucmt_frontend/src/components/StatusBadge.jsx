// src/components/StatusBadge.jsx
import React from 'react';

export default function StatusBadge({ status }) {
  const normalized = (status || '').toString().toLowerCase();

  let className = 'badge';
  if (normalized === 'ok' || normalized === 'up' || normalized === 'registered') {
    className += ' badge-ok';
  } else if (normalized === 'warning' || normalized === 'degraded') {
    className += ' badge-warning';
  } else if (normalized === 'down' || normalized === 'error') {
    className += ' badge-error';
  }

  return <span className={className}>{status}</span>;
}
