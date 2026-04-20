import { useEffect, useState } from 'react'

import { TerminalPanel } from '../components/TerminalPanel'
import { createSession, getAgents } from '../services/api'
import { useSessionStore } from '../stores/sessionStore'

export function App() {
  const [agents, setAgents] = useState([])
  const [selected, setSelected] = useState('codex')
  const [cwd, setCwd] = useState('.')
  const { activeSession, setActiveSession } = useSessionStore()

  useEffect(() => {
    void getAgents().then(setAgents)
  }, [])

  const onCreateSession = async () => {
    const session = await createSession({ agent_id: selected, cwd })
    setActiveSession(session)
  }

  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>Harness Manager</h1>
        <p>Pure TUI orchestration over PTY sessions.</p>
        <label>Agent</label>
        <select value={selected} onChange={(e) => setSelected(e.target.value)}>
          {agents.map((agent) => (
            <option key={agent.id} value={agent.id} disabled={!agent.installed}>
              {agent.display_name} {!agent.installed ? '(not installed)' : ''}
            </option>
          ))}
        </select>
        <label>Working Directory</label>
        <input value={cwd} onChange={(e) => setCwd(e.target.value)} />
        <button onClick={onCreateSession}>Start TUI Session</button>
      </aside>

      <main className="workspace">
        {activeSession ? (
          <TerminalPanel session={activeSession} />
        ) : (
          <div className="empty">Start a session to view terminal output.</div>
        )}
      </main>
    </div>
  )
}
