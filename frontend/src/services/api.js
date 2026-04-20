const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000/api'

export async function getAgents() {
  const res = await fetch(`${API_BASE}/agents`)
  if (!res.ok) throw new Error('Failed to load agents')
  return res.json()
}

export async function createSession(payload) {
  const res = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error('Failed to create session')
  return res.json()
}

export async function pollSession(sessionId) {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/drain`)
  if (!res.ok) throw new Error('Failed to poll session')
  return res.json()
}

export async function sendInput(sessionId, data) {
  await fetch(`${API_BASE}/sessions/${sessionId}/input`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ data }),
  })
}
