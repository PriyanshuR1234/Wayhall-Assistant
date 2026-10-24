/**
 * Wayhall Municipal Assistant API Client
 * Centralized interface for the FastAPI backend.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) throw new Error(`Health check returned status ${res.status}`);
    return await res.json();
  } catch (err) {
    return { status: 'unreachable', db: 'unreachable', gemini: 'unknown', chunks_indexed: 0 };
  }
}

export async function fetchDocuments() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/documents`);
    if (!res.ok) throw new Error(`Failed to fetch documents: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('Fetch documents error:', err);
    return [];
  }
}

export async function fetchDocumentChunks(docLabel) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/documents/${encodeURIComponent(docLabel)}/chunks?limit=30`);
    if (!res.ok) throw new Error(`Failed to fetch chunks: ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('Fetch chunks error:', err);
    return [];
  }
}

export async function createSession() {
  const res = await fetch(`${API_BASE_URL}/api/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) throw new Error(`Failed to create session: ${res.status}`);
  return await res.json();
}

export async function fetchSessionHistory(sessionId) {
  const res = await fetch(`${API_BASE_URL}/api/sessions/${encodeURIComponent(sessionId)}`);
  if (!res.ok) throw new Error(`Failed to load history: ${res.status}`);
  return await res.json();
}

export async function sendChatMessage(message, sessionId = null) {
  const res = await fetch(`${API_BASE_URL}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      session_id: sessionId || null,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error: ${res.status}`);
  }

  return await res.json();
}

export async function submitFeedback({ sessionId, rating, helpful, comments = '' }) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        rating: rating || (helpful ? 5 : 1),
        helpful: Boolean(helpful),
        comments,
      }),
    });
    return await res.json();
  } catch (err) {
    console.warn('Feedback submit error:', err);
    return null;
  }
}
