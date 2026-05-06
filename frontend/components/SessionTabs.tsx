import { Session } from '../hooks/useSession'

interface Props {
  sessions: Session[]
  activeId: number | null
  onSelect: (id: number) => void
  onNew: () => void
  onRename: (id: number, title: string) => void
  onDelete: (id: number) => void
}

export default function SessionTabs({ sessions, activeId, onSelect, onNew, onRename, onDelete }: Props) {
  function handleDoubleClick(id: number, currentTitle: string) {
    const newTitle = prompt('Rename session:', currentTitle)
    if (newTitle?.trim()) onRename(id, newTitle.trim())
  }

  function handleClose(e: React.MouseEvent, id: number) {
    e.stopPropagation()
    if (sessions.length > 1) onDelete(id)
  }

  return (
    <div className="session-tabs">
      {sessions.map((s) => (
        <div
          key={s.id}
          className={`session-tab${s.id === activeId ? ' active' : ''}`}
          onClick={() => onSelect(s.id)}
          onDoubleClick={() => handleDoubleClick(s.id, s.title)}
        >
          {s.title}
          <span className="session-tab-close" onClick={(e) => handleClose(e, s.id)}>×</span>
        </div>
      ))}
      <button className="session-tab-new" onClick={onNew} title="New session">+</button>
    </div>
  )
}
