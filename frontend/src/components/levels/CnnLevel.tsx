import { useState } from 'react'
import { runLevel } from '../../api'
import type { LevelProps } from './types'

/** 它不看整幅画，它一格一格看，最后拼起来。第 7 章的机器。
 *
 * 这一关的重点是「看多少格」——翻得少时票数被个别格子带偏
 * （两个条纹格就猜斑马），全翻开才拼出正确答案。
 */
export function CnnLevel({ seg, sid, spec }: LevelProps) {
  const tiles: any[] = spec.tiles || []
  const options: string[] = spec.options || []
  const answer: string = spec.answer || ''

  const [opened, setOpened] = useState<string[]>([])
  const [m, setM] = useState<any>(null)

  const flip = async (id: string) => {
    if (opened.includes(id)) return
    const next = [...opened, id]
    setOpened(next)
    const r = await runLevel(sid, seg.id, '', { revealed: next })
    setM(r.machine)
  }

  const reset = async () => {
    setOpened([])
    setM(null)
  }

  return (
    <div className="stage cnn-stage">
      {spec.prompt && <p className="lv-prompt">{spec.prompt}</p>}

      <div className="cnn-grid">
        {tiles.map((t) => {
          const on = opened.includes(t.id)
          return (
            <button
              key={t.id}
              className={`cnn-tile ${on ? 'on' : ''}`}
              onClick={() => flip(t.id)}
              aria-label={on ? `已看：${t.see}` : '还没看的格子'}
            >
              {on ? t.see : <span className="cnn-hidden">?</span>}
            </button>
          )
        })}
      </div>

      {m ? (
        <>
          <div className="machine">
            它猜：{m.label}
            <span className="cnn-share">（{m.share}% 把握 · 看了 {m.opened} 格）</span>
          </div>
          <p className="lv-because">
            {Object.entries(m.votes)
              .map(([lb, n]) => `${lb} ${n} 票`)
              .join(' · ')}
          </p>
          {opened.length === tiles.length && m.label !== answer && (
            <p className="lv-because">全看完了还是猜错——格子都对，拼错了。</p>
          )}
          {opened.length === tiles.length && m.label === answer && (
            <p className="lv-because">全翻开，才拼出「{answer}」。看太少会猜错。</p>
          )}
        </>
      ) : (
        <p className="lv-hint">翻一个格子，它才看一眼。</p>
      )}

      {options.length > 0 && (
        <p className="cnn-options">
          它只在里头挑：{options.join(' / ')}
        </p>
      )}

      {opened.length > 0 && (
        <button className="cnn-reset" onClick={reset}>
          重新看
        </button>
      )}
    </div>
  )
}
