import { useEffect, useRef, useState } from 'react'
import { runLevel } from '../../api'
import type { LevelProps } from './types'

/** 它一句一句往后传，新的进来，旧的滑走。第 8 章的机器。
 *
 * 这一关的重点是「句子越长忘得越多」——孩子把句子一次次加长，
 * 亲眼看见开头几个字一个个溜走。
 */
export function RnnLevel({ seg, sid, spec }: LevelProps) {
  const rounds: any[] = spec.rounds || []
  const [ri, setRi] = useState(0)
  const [m, setM] = useState<any>(null)
  const first = useRef(true)

  const run = async (idx: number) => {
    const r = rounds[idx]
    if (!r) return
    setRi(idx)
    const res = await runLevel(sid, seg.id, '', { round: r.id })
    setM(res.machine)
  }

  useEffect(() => {
    if (!first.current) return
    first.current = false
    run(0)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="stage rnn-stage">
      {spec.prompt && <p className="lv-prompt">{spec.prompt}</p>}

      <div className="rnn-ctl">
        <span className="knn-label">句子长度</span>
        {rounds.map((r, i) => (
          <button key={r.id} className={ri === i ? 'on' : ''} onClick={() => run(i)}>
            {i + 1}
          </button>
        ))}
      </div>

      {m && (
        <>
          <p className="rnn-said">
            <span className="rnn-dropped">{m.dropped}</span>
            <span className="rnn-kept">{m.remembered}</span>
          </p>
          <div className="machine">{m.text}</div>
          {m.forgot > 0 ? (
            <p className="lv-because">有 {m.forgot} 个字被挤掉了——新的进来，旧的滑走。</p>
          ) : (
            <p className="lv-because">句子短，它全记得。</p>
          )}
        </>
      )}
    </div>
  )
}
