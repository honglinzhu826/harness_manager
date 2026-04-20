import { useEffect, useMemo, useState } from 'react'

import { createSession, getAgents, pollSession, sendInput } from '../services/api'

function appendAssistantChunk(messages, chunk) {
  if (!chunk) return messages
  const next = [...messages]
  const last = next[next.length - 1]
  if (last && last.role === 'assistant') {
    last.content += chunk
    return next
  }
  next.push({ id: crypto.randomUUID(), role: 'assistant', content: chunk })
  return next
}

export function App() {
  const [agents, setAgents] = useState([])
  const [selectedAgent, setSelectedAgent] = useState('codex')
  const [selectedModel, setSelectedModel] = useState('')
  const [cwd, setCwd] = useState('.')
  const [draft, setDraft] = useState('')
  const [messages, setMessages] = useState([])
  const [sessionId, setSessionId] = useState(null)
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    void getAgents().then((items) => {
      setAgents(items)
      if (items.length > 0) {
        const firstInstalled = items.find((it) => it.installed) ?? items[0]
        setSelectedAgent(firstInstalled.id)
        setSelectedModel(firstInstalled.supported_models?.[0] ?? '')
      }
    })
  }, [])

  const activeAgent = useMemo(
    () => agents.find((agent) => agent.id === selectedAgent),
    [agents, selectedAgent],
  )

  useEffect(() => {
    if (!activeAgent) return
    if (!activeAgent.supported_models?.includes(selectedModel)) {
      setSelectedModel(activeAgent.supported_models?.[0] ?? '')
    }
  }, [activeAgent, selectedModel])

  useEffect(() => {
    if (!sessionId) return
    const timer = setInterval(async () => {
      const data = await pollSession(sessionId)
      if (data.chunks.length === 0) return
      setMessages((prev) => data.chunks.reduce((acc, chunk) => appendAssistantChunk(acc, chunk), prev))
    }, 350)
    return () => clearInterval(timer)
  }, [sessionId])

  const ensureSession = async () => {
    if (sessionId) return sessionId
    setCreating(true)
    try {
      const session = await createSession({
        agent_id: selectedAgent,
        model: selectedModel || null,
        cwd,
      })
      setSessionId(session.session_id)
      return session.session_id
    } finally {
      setCreating(false)
    }
  }

  const onSend = async () => {
    const text = draft.trim()
    if (!text || !activeAgent?.installed) return
    setDraft('')
    setMessages((prev) => [...prev, { id: crypto.randomUUID(), role: 'user', content: text }])
    const id = await ensureSession()
    await sendInput(id, `${text}\n`)
  }

  const onNewChat = () => {
    setMessages([])
    setSessionId(null)
  }

  return (
    <div className="chat-layout">
      <header className="topbar">
        <div>
          <h1>Harness Manager</h1>
          <p>Unified chat UI over PTY-backed code agents</p>
        </div>
        <button onClick={onNewChat}>New Chat</button>
      </header>

      <main className="chat-main">
        <section className="messages">
          {messages.length === 0 ? (
            <div className="empty">Send your first message to create a background PTY session.</div>
          ) : (
            messages.map((msg) => (
              <div key={msg.id} className={`bubble ${msg.role}`}>
                <div className="role">{msg.role === 'user' ? 'You' : 'Assistant'}</div>
                <pre>{msg.content}</pre>
              </div>
            ))
          )}
        </section>

        <section className="composer">
          <div className="selectors">
            <label>
              Agent
              <select value={selectedAgent} onChange={(e) => setSelectedAgent(e.target.value)}>
                {agents.map((agent) => (
                  <option key={agent.id} value={agent.id} disabled={!agent.installed}>
                    {agent.display_name} {!agent.installed ? '(not installed)' : ''}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Model
              <select value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)}>
                {(activeAgent?.supported_models ?? []).map((model) => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </label>
            <label>
              CWD
              <input value={cwd} onChange={(e) => setCwd(e.target.value)} />
            </label>
          </div>

          <div className="input-row">
            <textarea
              value={draft}
              placeholder="Type a request..."
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  void onSend()
                }
              }}
            />
            <button onClick={onSend} disabled={creating || !activeAgent?.installed}>
              {creating ? 'Starting Session...' : 'Send'}
            </button>
          </div>
        </section>
      </main>
    </div>
  )
}
