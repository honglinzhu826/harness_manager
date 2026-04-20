import { create } from 'zustand'

export const useSessionStore = create((set) => ({
  activeSession: null,
  sessions: [],
  setActiveSession: (session) =>
    set((state) => ({
      activeSession: session,
      sessions: state.sessions.some((s) => s.session_id === session.session_id)
        ? state.sessions
        : [...state.sessions, session],
    })),
}))
