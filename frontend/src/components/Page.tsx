import { useState } from 'react'
import type { Segment } from '../api'
import LevelRenderer from './levels'

type Props = {
  seg: Segment
  sid: string
  banner?: string | null
  onPrev?: () => void
  onBubble?: (question: string, goalTag?: string) => void
}

const IMG_BASE = '/images'

export default function Page({ seg, sid, banner, onPrev, onBubble }: Props) {
  const body = seg.body || {}
  const lines: string[] = body.lines || []
  const note: string = body.note || ''
  const bubbles: { q: string; a: string }[] = body.bubbles || []
  const variant = seg.variant || 'story'

  const [opened, setOpened] = useState<number | null>(null)

  return (
    <article
      className={`page ${seg.image_url ? 'has-art' : ''} ${variant === 'plain' ? 'plain' : ''} ${
        variant === 'naming' ? 'naming-page' : ''
      }`}
    >
      {seg.image_url && <img className="bg" src={`${IMG_BASE}/${seg.image_url.split('/').pop()}`} alt="" />}

      {banner && <div className="page-banner">{banner}</div>}

      {body.kicker && <p className="kicker">{body.kicker}</p>}

      {variant === 'ledger' && (
        <div className="sheet">
          <div className="ledger">
            {(body.ledger || []).map((t: string, i: number) => (
              <span key={i} style={{ animationDelay: `${i * 90}ms` }}>
                {t}
              </span>
            ))}
          </div>
        </div>
      )}

      {variant === 'level' && <LevelRenderer seg={seg} sid={sid} />}

      {variant === 'naming' && (
        <div className="naming">
          <div className="naming-lines">
            {lines.map((t, i) => (
              <p key={i} className="line" style={{ animationDelay: `${300 + i * 620}ms` }}>
                {t}
              </p>
            ))}
          </div>

          <div className="naming-card" style={{ animationDelay: `${300 + lines.length * 620}ms` }}>
            <span className="naming-pinyin">{body.term_pinyin}</span>
            <span className="naming-term">{body.term}</span>
            <span className="naming-def">
              {(body.definition || '').split('\n').map((l: string, i: number) => (
                <span key={i}>
                  {l}
                  <br />
                </span>
              ))}
            </span>
          </div>

          <p className="naming-foot" style={{ animationDelay: `${900 + lines.length * 620}ms` }}>
            {(body.footnote || '').split('\n').map((l: string, i: number) => (
              <span key={i}>
                {l}
                <br />
              </span>
            ))}
          </p>

          {body.takeaway && (
            <div className="takeaway" style={{ animationDelay: `${1300 + lines.length * 620}ms` }}>
              <span className="takeaway-hd">这本书想让你带走的一句</span>
              <span className="takeaway-text">{body.takeaway}</span>
            </div>
          )}
        </div>
      )}

      {variant !== 'naming' && (
        <div className={`caption ${seg.image_url ? 'on-art' : ''}`}>
          {lines.map((t, i) => (
            <p key={i} className="line" style={{ animationDelay: `${300 + i * 520}ms` }}>
              {t}
            </p>
          ))}
        </div>
      )}

      {note && (
        <p className="note" style={{ animationDelay: `${500 + lines.length * 520}ms` }}>
          {note.split('\n').map((l, i) => (
            <span key={i}>
              {l}
              <br />
            </span>
          ))}
        </p>
      )}

      {bubbles.length > 0 && (
        <div className="bubbles" style={{ animationDelay: `${900 + lines.length * 520}ms` }}>
          {bubbles.map((b, i) => (
            <div key={i} className="bubble-wrap">
              <button
                className="bubble"
                onClick={() => {
                  setOpened(opened === i ? null : i)
                  onBubble?.(b.q, seg.goal_tag || undefined)
                }}
              >
                {b.q}
              </button>
              {opened === i && <p className="bubble-answer">{b.a}</p>}
            </div>
          ))}
        </div>
      )}

      {onPrev && (
        <button className="back-inline" onClick={onPrev} aria-label="上一页">
          ←
        </button>
      )}
    </article>
  )
}
