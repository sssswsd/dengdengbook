import type { Note } from '../api'

type Props = {
  notes: Note[]
  onClose: () => void
}

export default function Notebook({ notes, onClose }: Props) {
  return (
    <div className="notebook-mask" onClick={onClose}>
      <div className="notebook" onClick={(e) => e.stopPropagation()}>
        <div className="notebook-hd">
          <span>我的小本子</span>
          <button className="notebook-x" onClick={onClose} aria-label="合上">
            ✕
          </button>
        </div>

        {notes.length === 0 ? (
          <p className="notebook-empty">
            还是空的。
            <br />
            你问它答不上来的问题，会被记在这里。
          </p>
        ) : (
          <ul className="notebook-list">
            {notes.map((n) => (
              <li key={n.id}>{n.question}</li>
            ))}
          </ul>
        )}

        <p className="notebook-foot">这些它现在还答不上来。下次我们一起看。</p>
      </div>
    </div>
  )
}
