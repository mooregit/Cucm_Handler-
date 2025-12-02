// src/api/client.js
const BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function apiGet(path) {
  const url = `${BASE_URL}${path}`;
  const resp = await fetch(url);

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(
      `Request failed: ${resp.status} ${resp.statusText} - ${text}`
    );
  }

  return resp.json();
}

export { apiGet, BASE_URL };
