import type { Session, Message, Artifact, ChatRequest, ChatResponse, Skill, HealthResponse } from '../types';

const API_BASE = '/api/v1';

async function fetchJson<T>(url: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${url}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Health
  health: () => fetchJson<HealthResponse>('/health'),

  // Sessions
  createSession: (data: { title?: string; user_id?: string; llm_provider?: string; llm_model?: string }) =>
    fetchJson<Session>('/sessions', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  listSessions: (user_id?: string, limit = 20) => {
    const params = new URLSearchParams();
    if (user_id) params.set('user_id', user_id);
    params.set('limit', String(limit));
    return fetchJson<Session[]>(`/sessions?${params.toString()}`);
  },

  getSession: (id: string) =>
    fetchJson<Session & { messages: Message[] }>(`/sessions/${id}`),

  updateSession: (id: string, data: { title?: string }) =>
    fetchJson<Session>(`/sessions/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  deleteSession: async (id: string) => {
    const response = await fetch(`${API_BASE}/sessions/${id}`, { method: 'DELETE' });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
  },

  // Chat
  chat: (request: ChatRequest) =>
    fetchJson<ChatResponse>('/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  // Artifacts
  getArtifacts: (sessionId: string) =>
    fetchJson<Artifact[]>(`/sessions/${sessionId}/artifacts`),

  // Skills
  listSkills: () =>
    fetchJson<Skill[]>('/skills'),
};