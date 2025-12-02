// src/api/health.js
import { apiGet } from './client';

export async function fetchHealth() {
  // adjust path to your actual health endpoint
  return apiGet('/health');
}
