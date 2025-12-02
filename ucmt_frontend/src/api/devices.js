// src/api/devices.js
import { apiGet } from './client';

export async function fetchDevices() {
  // adjust path here if your router prefix is different (e.g. '/api/devices')
  return apiGet('/devices');
}
