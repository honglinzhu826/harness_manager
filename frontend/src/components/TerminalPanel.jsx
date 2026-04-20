import { useEffect, useRef } from 'react'
import { FitAddon } from '@xterm/addon-fit'
import { Terminal } from '@xterm/xterm'
import '@xterm/xterm/css/xterm.css'

import { pollSession, sendInput } from '../services/api'

export function TerminalPanel({ session }) {
  const terminalRef = useRef(null)
  const xtermRef = useRef(null)

  useEffect(() => {
    if (!session || !terminalRef.current) return

    const term = new Terminal({
      cursorBlink: true,
      fontSize: 13,
      convertEol: true,
      theme: { background: '#111827' },
    })
    const fitAddon = new FitAddon()
    term.loadAddon(fitAddon)
    term.open(terminalRef.current)
    fitAddon.fit()

    term.onData((data) => {
      void sendInput(session.session_id, data)
    })

    xtermRef.current = term

    const timer = setInterval(async () => {
      const data = await pollSession(session.session_id)
      data.chunks.forEach((chunk) => term.write(chunk))
    }, 300)

    return () => {
      clearInterval(timer)
      term.dispose()
    }
  }, [session])

  return <div className="terminal" ref={terminalRef} />
}
