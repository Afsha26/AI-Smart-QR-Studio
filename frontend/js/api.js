// api.js — reusable functions for communicating with the FastAPI backend
// Provides: generateAITheme, generateAIContent, validateURL, analyzeQR, downloadQR
// Uses async/await and central request helper with timeout and error handling

const DEFAULT_TIMEOUT = 15000; // ms
const API_BASE = 'http://127.0.0.1:8000';

// Helper: central fetch wrapper with JSON handling, timeout, and errors
async function request(path, { method = 'GET', body = null, headers = {}, timeout = DEFAULT_TIMEOUT, expectBlob = false } = {}) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);

  const opts = { method, headers: { ...headers }, signal: controller.signal };
  if (body != null) {
    if (body instanceof FormData) {
      opts.body = body; // browser sets correct headers
    } else if (typeof body === 'string' || body instanceof Blob) {
      opts.body = body;
    } else {
      opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(body);
    }
  }

  try {
    const res = await fetch(path, opts);
    clearTimeout(id);
    if (!res.ok) {
      // Try to parse JSON error message when available
      let errText = `${res.status} ${res.statusText}`;
      try { const json = await res.json(); if (json && json.error) errText = json.error; } catch (_) {}
      const err = new Error(`Request failed: ${errText}`);
      err.status = res.status;
      throw err;
    }

    if (expectBlob) return await res.blob();

    // default: parse JSON, but fall back to text
    const ctype = res.headers.get('content-type') || '';
    if (ctype.includes('application/json')) return await res.json();
    return await res.text();
  } catch (err) {
    // Normalize AbortError to a clearer message
    if (err.name === 'AbortError') throw new Error('Request timed out');
    throw err;
  }
}

// generateAITheme: ask backend for a theme suggestion based on a prompt
// POST /ai/theme { prompt }
export async function generateAITheme(prompt) {
  if (!prompt) throw new Error('generateAITheme requires a prompt');
  try {
    const res = await request(`${API_BASE}/ai/theme`, { method: 'POST', body: { prompt } });
    return res; // expected: { theme: {...} } or similar
  } catch (err) {
    console.error('generateAITheme error', err);
    throw err;
  }
}

// generateAIContent: ask backend to create content (title/tagline/CTA) for a QR
// POST /ai/content { prompt, type }
export async function generateAIContent(prompt, type = 'default') {
  if (!prompt) throw new Error('generateAIContent requires a prompt');
  try {
    const res = await request(`${API_BASE}/ai/content`, { method: 'POST', body: { prompt, type } });
    return res; // expected: { title, tagline, cta, content }
  } catch (err) {
    console.error('generateAIContent error', err);
    throw err;
  }
}

// validateInput: validate a QR payload using the backend dispatcher
// POST /validator { type, value }
export async function validateInput(type, value) {
  if (!type) throw new Error('validateInput requires a qr type');
  if (value == null) throw new Error('validateInput requires a value');
  try {
    const res = await request(`${API_BASE}/validator`, { method: 'POST', body: { type, value } });
    return res; // expected: { valid, normalized, issues }
  } catch (err) {
    console.error('Unable to validate input.', err);
    throw err;
  }
}

// validateURL: validate and sanitize a URL using backend rules
export async function validateURL(url) {
  return validateInput('url', url);
}

// analyzeQR: send QR payload and design options to backend to evaluate scan quality
// POST /analysis/quality { payload, options }
export async function analyzeQR(payload, options = {}) {
  if (payload == null) throw new Error('analyzeQR requires a payload');
  try {
    const res = await request(`${API_BASE}/analysis/quality`, { method: 'POST', body: { payload, options } });
    return res; // expected: { contrast, moduleSize, logoImpact, score }
  } catch (err) {
    console.error('analyzeQR error', err);
    throw err;
  }
}

// downloadQR: request the backend to render and return a downloadable QR (svg/png)
// POST /download with { payload, format, options } and returns a Blob
export async function downloadQR(payload, format = 'png', options = {}) {
  if (payload == null) throw new Error('downloadQR requires a payload');
  const supported = ['png', 'svg'];
  if (!supported.includes(format)) throw new Error(`Unsupported format ${format}`);
  try {
    // expect a binary response
    const blob = await request(`${API_BASE}/download`, { method: 'POST', body: { payload, format, options }, expectBlob: true, headers: { Accept: '*/*' } });
    return blob; // caller can save via URL.createObjectURL or other means
  } catch (err) {
    console.error('downloadQR error', err);
    throw err;
  }
}

// Convenience: save a blob to disk by triggering a download
export function saveBlob(blob, filename = 'aiqr.png') {
  if (!(blob instanceof Blob)) throw new Error('saveBlob requires a Blob');
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.style.display = 'none';
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 60000);
}

// Default export with all helpers
export default {
  generateAITheme,
  generateAIContent,
  validateURL,
  analyzeQR,
  downloadQR,
  saveBlob,
};
