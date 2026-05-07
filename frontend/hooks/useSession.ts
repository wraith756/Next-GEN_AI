import { useState, useEffect, useCallback } from 'react'

export type Session = { id: number; title: string }

export function useSession() {
  const [sessions, setSessions] = useState<Session[]>([])
  const [activeId, setActiveId] = useState<number | null>(null)

  const load = useCallback(async () => {
    try {
      const res = await fetch('/api/sessions')
      const data: Session[] = await res.json()
      setSessions(data)
      if (data.length > 0 && !activeId) setActiveId(data[0].id)
    } catch {}
  }, [activeId])

  useEffect(() => { load() }, [])

  const createSession = useCallback(async () => {
    const title = `Chat #${sessions.length + 1}`
    const res = await fetch('/api/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    })
    const sess: Session = await res.json()
    setSessions((prev) => [...prev, sess])
    setActiveId(sess.id)
    return sess
  }, [sessions.length])

  const renameSession = useCallback(async (id: number, title: string) => {
    await fetch(`/api/sessions/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    })
    setSessions((prev) => prev.map((s) => (s.id === id ? { ...s, title } : s)))
  }, [])

  const deleteSession = useCallback(async (id: number) => {
    await fetch(`/api/sessions/${id}`, { method: 'DELETE' })
    setSessions((prev) => {
      const next = prev.filter((s) => s.id !== id)
      if (activeId === id) setActiveId(next[0]?.id ?? null)
      return next
    })
  }, [activeId])

  return { sessions, activeId, setActiveId, createSession, renameSession, deleteSession, reload: load }
}
