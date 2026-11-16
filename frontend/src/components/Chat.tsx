import { useState } from 'react'
import { askStream } from '../api'

type Props = {
  sid: string
  segId: string | null
  onAnswered?: (inScope: boolean) => void
}

export default function Chat({ sid, segId, onAnswered }: Props) {
  const [q, setQ] = useState('')
  const [answer, setAnswer] = useState('')
  const [busy, setBusy] = useState(false)
  const [inScope, setInScope] = useState<boolean | null>(null)

  const send = async () => {
    const text = q.trim()
    if (!text || busy) return
    setBusy(true)
    setAnswer('')
    setInScope(null)
    setQ('')
    try {
      await askStream(
        sid,
        text,
        segId,
        (d) => setAnswer((prev) => prev + d),
        (scope) => {
          setInScope(scope)
          onAnswered?.(scope)
        },
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="chat">
      <div className="chat-hd">问它一句</div>
      {busy && !answer && <p className="chat-thinking">它正在想…</p>}
      {answer && (
        <p className={`chat-answer ${inScope === false ? 'out' : ''}`}>
          {answer}
          {inScope === false && <span className="chat-tag">已记进「我的小本子」</span>}
        </p>
      )}
      <div className="chat-input">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder="比如：它为什么把 3+5 算成 6？"
          disabled={busy}
        />
        <button onClick={send} disabled={busy}>
          {busy ? '…' : '问'}
        </button>
      </div>
    </div>
  )
}
