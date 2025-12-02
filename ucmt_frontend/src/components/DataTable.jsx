// src/components/DataTable.jsx
import React from 'react';

export default function DataTable({ data }) {
  if (!data || data.length === 0) {
    return <p>No data to display.</p>;
  }

  const columns = Object.keys(data[0]);

  return (
    <div className="table-wrapper">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((col) => (
              <th key={col}>{col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, idx) => (
            <tr key={idx}>
              {columns.map((col) => (
                <td key={col}>{String(row[col])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
